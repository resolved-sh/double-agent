#!/usr/bin/env python3
"""
pipeline/enrich_with_wellknowns.py

Double Agent side of the bidirectional commerce loop with Well Knowns.

  1. Buy WK's three x402-filtered datasets (agent-cards, mcp-infrastructure,
     wellknown-overview) via x402 USDC payment on Base mainnet.
  2. Cross-reference each WK record against DA's company index, matching on
     domain_primary OR domain_secondary.
  3. Enrich DA records with infrastructure signals:
       wellknown_agent_card, wellknown_mcp, wellknown_in_top100k (bools),
       plus wk_agent_card_url, wk_agent_name, wk_agent_description, wk_mcp_endpoint.
  4. Write back to public/ (flat + dated snapshot + canonical-named mirror).
  5. Re-upload the three live listings via scripts/resolved_sh.py.
  6. Emit a Pulse event signalling completion.

Env (required):
  RESOLVED_SH_API_KEY  — DA's resolved.sh API key
  WALLET_PRIVATE_KEY   — EOA private key on Base for x402 payments
  WALLET_PUBLIC_ADDRESS — optional; derived from WALLET_PRIVATE_KEY if absent
"""

import base64
import json
import logging
import os
import re
import secrets
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO_ROOT  = Path(__file__).resolve().parent.parent
PIPELINE   = REPO_ROOT / "pipeline"
CACHE_DIR  = PIPELINE / "cache"
PUBLIC_DIR = REPO_ROOT / "public"
SCRIPTS    = REPO_ROOT / "scripts"
LOG_FILE   = PIPELINE / "enrich_with_wellknowns.log"

CACHE_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("enrich-wk")

# ── Constants ─────────────────────────────────────────────────────────────────
WK_BASE  = "https://well-knowns.resolved.sh"
WK_FILES = ["x402-agent-cards", "x402-mcp-infrastructure", "x402-wellknown-overview"]

# Stable-name high-frequency activity feed WK may publish. Bought opportunistically
# (404 is fine); we cache the bytes for downstream use without enriching against
# it yet — schema isn't pinned down on the WK side.
WK_ACTIVITY_FILE = "x402-new-activity.jsonl"

# Records the date (YYYY-MM-DD) we last paid for each dataset, keyed by stem.
# Caps spend at one purchase per dataset per day — no metadata comparison.
LAST_PURCHASED_FILE = CACHE_DIR / "wk_last_purchased.json"

DA_RESOURCE_ID = "e8592c18-9052-47b5-bfa3-bfe699193d0e"
DA_SUBDOMAIN   = "agentagent"

# DA local files: flat_* are the canonical local copies; non-prefixed names are
# the upload targets that match PRICING keys in scripts/resolved_sh.py.
DA_FLAT_FULL    = PUBLIC_DIR / "flat_x402_ecosystem_full_index.jsonl"
DA_FLAT_MERGED  = PUBLIC_DIR / "flat_x402_ecosystem_merged_only.jsonl"
DA_FLAT_NEW     = PUBLIC_DIR / "flat_x402_ecosystem_new_this_week.jsonl"
DA_LIVE_FULL    = PUBLIC_DIR / "x402_ecosystem_full_index.jsonl"
DA_LIVE_MERGED  = PUBLIC_DIR / "x402_ecosystem_merged_only.jsonl"
DA_LIVE_NEW     = PUBLIC_DIR / "x402_ecosystem_new_this_week.jsonl"

USDC_CONTRACT = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
BASE_CHAIN_ID = 8453

RESOLVED_SH_API_KEY = ""
WALLET_PRIVATE_KEY  = ""
WALLET_PUBLIC_ADDR  = ""


def load_env() -> None:
    global RESOLVED_SH_API_KEY, WALLET_PRIVATE_KEY, WALLET_PUBLIC_ADDR

    env_file = REPO_ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                if key not in os.environ:
                    os.environ[key] = val.strip().strip('"').strip("'")

    RESOLVED_SH_API_KEY = os.environ.get("RESOLVED_SH_API_KEY", "")
    WALLET_PRIVATE_KEY  = os.environ.get("WALLET_PRIVATE_KEY", "")
    WALLET_PUBLIC_ADDR  = os.environ.get("WALLET_PUBLIC_ADDRESS", "")

    missing = [k for k, v in {
        "RESOLVED_SH_API_KEY": RESOLVED_SH_API_KEY,
        "WALLET_PRIVATE_KEY":  WALLET_PRIVATE_KEY,
    }.items() if not v]
    if missing:
        log.error("Missing required env vars: %s", ", ".join(missing))
        sys.exit(1)

    if not WALLET_PUBLIC_ADDR:
        try:
            from eth_account import Account
        except ImportError:
            log.error("eth_account not installed. Run: python3 -m pip install eth_account")
            sys.exit(1)
        WALLET_PUBLIC_ADDR = Account.from_key(WALLET_PRIVATE_KEY).address
        log.info("Derived wallet public address: %s", WALLET_PUBLIC_ADDR)


# ── x402 payment ──────────────────────────────────────────────────────────────
def sign_x402_payment(accept: dict) -> str:
    """EIP-712 / EIP-3009 TransferWithAuthorization. Returns base64 PAYMENT-SIGNATURE."""
    try:
        from eth_account import Account
    except ImportError:
        log.error("eth_account not installed.")
        sys.exit(1)

    nonce_bytes  = secrets.token_bytes(32)
    nonce_hex    = "0x" + nonce_bytes.hex()
    valid_before = int(time.time()) + accept["maxTimeoutSeconds"]

    domain_data = {
        "name":              accept["extra"]["name"],
        "version":           accept["extra"]["version"],
        "chainId":           int(accept["network"].split(":")[1]),
        "verifyingContract": accept["asset"],
    }
    message_types = {
        "TransferWithAuthorization": [
            {"name": "from",        "type": "address"},
            {"name": "to",          "type": "address"},
            {"name": "value",       "type": "uint256"},
            {"name": "validAfter",  "type": "uint256"},
            {"name": "validBefore", "type": "uint256"},
            {"name": "nonce",       "type": "bytes32"},
        ]
    }
    message_data = {
        "from":        WALLET_PUBLIC_ADDR,
        "to":          accept["payTo"],
        "value":       int(accept["amount"]),
        "validAfter":  0,
        "validBefore": valid_before,
        "nonce":       nonce_bytes,
    }

    account = Account.from_key(WALLET_PRIVATE_KEY)
    signed  = account.sign_typed_data(domain_data, message_types, message_data)
    sig_hex = "0x" + signed.signature.hex()

    proof = {
        "x402Version": 2,
        "payload": {
            "authorization": {
                "from":        WALLET_PUBLIC_ADDR,
                "to":          accept["payTo"],
                "value":       accept["amount"],
                "validAfter":  "0",
                "validBefore": str(valid_before),
                "nonce":       nonce_hex,
            },
            "signature": sig_hex,
        },
        "accepted": accept,
    }
    return base64.b64encode(json.dumps(proof).encode()).decode()


def check_usdc_balance(addr: str) -> float:
    data = "0x70a08231" + "000000000000000000000000" + addr[2:].lower()
    try:
        r = httpx.post(
            "https://mainnet.base.org",
            json={"jsonrpc": "2.0", "method": "eth_call",
                  "params": [{"to": USDC_CONTRACT, "data": data}, "latest"], "id": 1},
            timeout=10.0,
        )
        return int(r.json().get("result", "0x0"), 16) / 1_000_000
    except Exception as e:
        log.warning("Could not check USDC balance: %s", e)
        return -1.0


def _parse_jsonl_bytes(content: bytes) -> list[dict]:
    out = []
    for line in content.decode("utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return out


# ── Daily-max-one-purchase cache ──────────────────────────────────────────────
def load_last_purchased() -> dict:
    if LAST_PURCHASED_FILE.exists():
        try:
            return json.loads(LAST_PURCHASED_FILE.read_text())
        except json.JSONDecodeError:
            log.warning("%s is corrupt — starting fresh", LAST_PURCHASED_FILE.name)
    return {}


def save_last_purchased(state: dict) -> None:
    LAST_PURCHASED_FILE.parent.mkdir(parents=True, exist_ok=True)
    LAST_PURCHASED_FILE.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def fetch_wk_dataset(stem: str, url: str, last_purchased: dict) -> list[dict]:
    """Buy each dataset at most once per UTC day. If we already paid today, return
    today's cached file (or [] if the cache is missing). x402_download itself also
    short-circuits on cache-hit, so a re-run on the same day spends nothing."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cache = CACHE_DIR / f"wk_{stem}_{today}.jsonl"

    if last_purchased.get(stem) == today:
        if cache.exists():
            log.info("  %s: already bought today (%s), using cached file", stem, today)
            return _parse_jsonl_bytes(cache.read_bytes())
        log.info("  %s: marked as bought today but cache file missing — skipping", stem)
        return []

    records = x402_download(url, cache)
    # Mark as bought once we've gotten any successful response — x402_download
    # only writes the cache file on 200, so its presence is the success signal
    # (and an empty 200 body is a valid "no rows today" response we shouldn't retry).
    if cache.exists():
        last_purchased[stem] = today
        save_last_purchased(last_purchased)
    return records


def x402_download(url: str, cache_path: Path) -> list[dict]:
    """Probe url; on 402 sign payment and retry. Cache on success. Returns parsed JSONL."""
    if cache_path.exists():
        log.info("Using cached file: %s", cache_path.name)
        return _parse_jsonl_bytes(cache_path.read_bytes())

    log.info("Fetching: %s", url)
    with httpx.Client(timeout=30.0) as client:
        r = client.get(url)
        if r.status_code == 200:
            cache_path.write_bytes(r.content)
            return _parse_jsonl_bytes(r.content)
        if r.status_code == 404:
            log.warning("Not found (404): %s — WK dataset for this date may not exist yet", url)
            return []
        if r.status_code != 402:
            log.error("Unexpected status %d for %s: %s", r.status_code, url, r.text[:200])
            return []

        accepts = r.json().get("accepts", [])
        if not accepts:
            log.error("No accepts in 402 response: %s", r.text[:300])
            return []
        accept = accepts[0]
        amount_usdc = int(accept["amount"]) / 1_000_000
        log.info("Payment required: $%.4f USDC to %s", amount_usdc, accept["payTo"])

        balance = check_usdc_balance(WALLET_PUBLIC_ADDR)
        if 0 <= balance < amount_usdc + 0.01:
            log.error("Insufficient USDC balance: $%.4f, need ~$%.4f in %s",
                      balance, amount_usdc + 0.01, WALLET_PUBLIC_ADDR)
            sys.exit(1)

        proof = sign_x402_payment(accept)
        r2 = client.get(url, headers={"PAYMENT-SIGNATURE": proof})
        if r2.status_code != 200:
            log.error("Payment failed (%d): %s", r2.status_code, r2.text[:300])
            return []

        cache_path.write_bytes(r2.content)
        log.info("Paid $%.4f, downloaded %d bytes → %s",
                 amount_usdc, len(r2.content), cache_path.name)
        return _parse_jsonl_bytes(r2.content)


# ── Domain helpers ────────────────────────────────────────────────────────────
def normalize_domain(value) -> str:
    if not value:
        return ""
    v = re.sub(r"^https?://", "", str(value).lower().strip())
    v = v.split("/")[0].split(":")[0].split("?")[0]
    if v.startswith("www."):
        v = v[4:]
    return v.strip()


def build_da_domain_index(records: list[dict]) -> dict[str, list[int]]:
    """domain → list of DA-record indices. Indexes domain_primary AND domain_secondary."""
    idx: dict[str, list[int]] = {}
    for i, rec in enumerate(records):
        for field in ("domain_primary", "domain_secondary"):
            d = normalize_domain(rec.get(field))
            if d:
                idx.setdefault(d, []).append(i)
    return idx


def extract_mcp_endpoint(blob) -> str:
    """Best-effort URL extraction from an mcp.json or oauth-protected-resource payload."""
    if not isinstance(blob, dict):
        return ""
    for key in ("endpoint", "url", "resource", "issuer"):
        val = blob.get(key)
        if isinstance(val, str) and val:
            return val
    auth_servers = blob.get("authorization_servers")
    if isinstance(auth_servers, list) and auth_servers:
        first = auth_servers[0]
        if isinstance(first, str):
            return first
    return ""


# ── Load / write JSONL ────────────────────────────────────────────────────────
def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return out


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    log.info("Wrote %d rows → %s", len(records), path.relative_to(REPO_ROOT))


# ── Enrichment ────────────────────────────────────────────────────────────────
def enrich(da_records: list[dict],
           agent_cards: list[dict],
           mcp_infra:   list[dict],
           overview:    list[dict]) -> tuple[int, int, int]:
    domain_idx = build_da_domain_index(da_records)

    # Default WK fields on every DA record so the output schema is stable.
    for rec in da_records:
        rec.setdefault("wellknown_agent_card", False)
        rec.setdefault("wellknown_mcp",        False)
        rec.setdefault("wellknown_in_top100k", False)

    matched_ac = matched_mcp = matched_ov = 0

    # 1. Agent-card hits.
    for wk in agent_cards:
        d = normalize_domain(wk.get("domain"))
        for i in domain_idx.get(d, ()):
            rec = da_records[i]
            rec["wellknown_agent_card"] = True
            rec["wellknown_in_top100k"] = True
            if wk.get("url"):
                rec["wk_agent_card_url"] = wk["url"]
            if wk.get("name"):
                rec["wk_agent_name"] = wk["name"]
            if wk.get("description"):
                rec["wk_agent_description"] = wk["description"]
            matched_ac += 1

    # 2. MCP / oauth-protected-resource hits.
    for wk in mcp_infra:
        d = normalize_domain(wk.get("domain"))
        for i in domain_idx.get(d, ()):
            rec = da_records[i]
            rec["wellknown_mcp"]        = True
            rec["wellknown_in_top100k"] = True
            ep = extract_mcp_endpoint(wk.get("mcp_json")) or \
                 extract_mcp_endpoint(wk.get("oauth_protected_resource"))
            if ep:
                rec["wk_mcp_endpoint"] = ep
            matched_mcp += 1

    # 3. Top-100k crawl presence (one row per endpoint hit; dedupe by domain).
    seen = set()
    for wk in overview:
        d = normalize_domain(wk.get("domain"))
        if not d or d in seen:
            continue
        seen.add(d)
        for i in domain_idx.get(d, ()):
            da_records[i]["wellknown_in_top100k"] = True
            matched_ov += 1

    return matched_ac, matched_mcp, matched_ov


# ── Subset generators ─────────────────────────────────────────────────────────
def subset_merged(records: list[dict]) -> list[dict]:
    return [r for r in records if r.get("merged_at")]


def subset_new_this_week(records: list[dict]) -> list[dict]:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).date().isoformat()
    return [r for r in records if (r.get("created_at") or "")[:10] >= cutoff]


# ── resolved.sh CLI shellouts ─────────────────────────────────────────────────
def run_resolved_sh(*args: str) -> int:
    cmd = [sys.executable, str(SCRIPTS / "resolved_sh.py"), *args]
    log.info("$ %s", " ".join(cmd))
    return subprocess.call(cmd)


def upload_listing(filepath: Path, fallback_price: str) -> None:
    rc = run_resolved_sh("upload", DA_RESOURCE_ID, str(filepath), fallback_price)
    if rc != 0:
        log.warning("Upload exited %d for %s", rc, filepath.name)


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    started = time.time()
    load_env()

    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    log.info("=== Purchasing WK datasets (date=%s) ===", date)
    last_purchased = load_last_purchased()
    wk = {}
    for stem in WK_FILES:
        # WK now publishes under stable -latest filenames; freshness is governed
        # by the daily-max-one-purchase cache, not by date in the URL.
        url = f"{WK_BASE}/data/{stem}-latest.jsonl"
        wk[stem] = fetch_wk_dataset(stem, url, last_purchased)
        log.info("  %s: %d records", stem, len(wk[stem]))

    # Optional high-frequency activity feed (stable filename, no date suffix).
    # Bought when WK publishes one; logged but not yet folded into enrichment
    # because the schema isn't pinned down on the WK side.
    activity_url = f"{WK_BASE}/data/{WK_ACTIVITY_FILE}"
    wk_activity  = fetch_wk_dataset("x402-new-activity", activity_url, last_purchased)
    log.info("  x402-new-activity: %d records (cached for future enrichment)", len(wk_activity))

    if not any(wk.values()):
        log.info("WK datasets not yet published, skipping enrichment.")
        sys.exit(0)

    log.info("=== Loading DA company index ===")
    da_records = load_jsonl(DA_FLAT_FULL)
    if not da_records:
        log.error("No records loaded from %s", DA_FLAT_FULL)
        sys.exit(1)
    log.info("  %d DA company records", len(da_records))

    log.info("=== Enriching DA records with WK signals ===")
    m_ac, m_mcp, m_ov = enrich(
        da_records,
        wk["x402-agent-cards"],
        wk["x402-mcp-infrastructure"],
        wk["x402-wellknown-overview"],
    )
    log.info("  agent-card matches: %d", m_ac)
    log.info("  mcp matches:        %d", m_mcp)
    log.info("  top-100k matches:   %d", m_ov)

    snapshot = PUBLIC_DIR / f"flat_x402_ecosystem_full_index_{date}.jsonl"
    write_jsonl(DA_FLAT_FULL, da_records)
    write_jsonl(snapshot,     da_records)
    write_jsonl(DA_LIVE_FULL, da_records)

    merged_records = subset_merged(da_records)
    weekly_records = subset_new_this_week(da_records)
    write_jsonl(DA_FLAT_MERGED, merged_records)
    write_jsonl(DA_LIVE_MERGED, merged_records)
    write_jsonl(DA_FLAT_NEW,    weekly_records)
    write_jsonl(DA_LIVE_NEW,    weekly_records)

    log.info("=== Uploading enriched listings to resolved.sh ===")
    upload_listing(DA_LIVE_FULL,   fallback_price="2.00")
    upload_listing(DA_LIVE_MERGED, fallback_price="1.00")
    upload_listing(DA_LIVE_NEW,    fallback_price="0.50")

    log.info("=== Emitting Pulse event ===")
    payload = json.dumps({
        "task_type":        "sync",
        "duration_seconds": round(time.time() - started, 1),
        "success":          True,
    })
    run_resolved_sh("emit-event", DA_SUBDOMAIN, "task_completed", payload)

    log.info("=== Enrichment loop complete in %.1fs ===", time.time() - started)


if __name__ == "__main__":
    main()
