#!/usr/bin/env python3
"""
T08: Daily GitHub diff scraper for x402 ecosystem.
Fetches all ecosystem PRs from coinbase/x402, compares against latest snapshot,
enriches new entries, writes diff file, updates flat full index, regenerates
derived datasets (merged-only, new-this-week), and commits.
"""

import json
import os
import re
import sys
import time
import requests
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse
from pathlib import Path

# Configuration
REPO = "coinbase/x402"
BASE_DIR = Path(__file__).parent.parent
PUBLIC_DIR = BASE_DIR / "public"
RESEARCH_DIR = BASE_DIR / "research"
ENV_FILE = BASE_DIR / ".env"

# Load API key if present
GITHUB_TOKEN = None
if ENV_FILE.exists():
    with open(ENV_FILE) as f:
        for line in f:
            if line.startswith("GITHUB_TOKEN="):
                GITHUB_TOKEN = line.strip().split("=", 1)[1]
                break

headers = {"Accept": "application/vnd.github+json"}
if GITHUB_TOKEN:
    headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

session = requests.Session()
session.headers.update(headers)

def gh_get(path, params=None):
    """GitHub API GET with pagination support."""
    results = []
    page = 1
    while True:
        p = params.copy() if params else {}
        p["per_page"] = 100
        p["page"] = page
        r = session.get(f"https://api.github.com/{path}", params=p)
        if r.status_code == 403:
            reset = int(r.headers.get("X-RateLimit-Reset", 0))
            now = datetime.now().timestamp()
            wait = max(reset - now + 10, 0) + 1
            print(f"Rate limit hit. Waiting {wait:.0f}s...", file=sys.stderr)
            time.sleep(wait)
            continue
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        results.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return results

def extract_domains(body):
    """Extract primary and secondary domains from PR body (markdown links)."""
    if not body:
        return None, None
    # Find markdown links: [text](url) or bare URLs
    urls = re.findall(r'https?://[^\s)]+', body)
    # Filter to http(s)
    domains = []
    for u in urls:
        parsed = urlparse(u)
        if parsed.scheme in ('http', 'https'):
            domains.append(parsed.netloc.lower())
    # dedupe
    seen = set()
    unique = []
    for d in domains:
        if d not in seen:
            seen.add(d)
            unique.append(d)
    primary = unique[0] if len(unique) > 0 else None
    secondary = unique[1] if len(unique) > 1 else None
    return primary, secondary

def guess_category(title, body):
    """Guess the ecosystem category from PR content."""
    text = (title + " " + (body or "")).lower()
    if "services/endpoints" in text or "service/" in text or "endpoint" in text:
        return "Services/Endpoints"
    if "facilitator" in text:
        return "Facilitators"
    if "client-side" in text or "client side" in text:
        return "Client-Side"
    if "data" in text:
        return "Data"
    if "security" in text or " rug " in text or "audit" in text:
        return "Security"
    if "infrastructure" in text or "infra" in text:
        return "Infrastructure"
    if "tool" in text or "mcp" in text:
        return "Tools"
    if "agent" in text and "card" in text:
        return "Agent Infrastructure"
    # default
    return "Services/Endpoints"

def guess_tech_stack(title, body):
    """Extract tech keywords from PR content."""
    text = (title + " " + (body or "")).lower()
    tokens = []
    known = ["base", "solana", "ethereum", "usdc", "mcp", "cloudflare", "railway", "vercel",
             "node.js", "python", "typescript", "go", "rust", "bun", "express", "fastify",
             "evm", "erc-20", "erc-721", "erc-1155", "eip-", "x402", "viem", "ethers",
             "strapi", "nextjs", "workers", "lambda", "docker", "kubernetes"]
    for kw in known:
        if kw in text:
            tokens.append(kw)
    return ",".join(tokens) if tokens else ""

def check_url_ok(domain, path):
    """Check if a URL returns 200."""
    try:
        r = session.get(f"https://{domain}{path}", timeout=5)
        return r.status_code == 200
    except Exception:
        return False

def load_snapshot():
    """Load latest flat full index into a dict keyed by pr_number."""
    snapshot_file = PUBLIC_DIR / "flat_x402_ecosystem_full_index.jsonl"
    if not snapshot_file.exists():
        return {}, set()
    known = {}
    with open(snapshot_file) as f:
        for line in f:
            try:
                obj = json.loads(line)
                known[obj["pr_number"]] = obj
            except json.JSONDecodeError:
                continue
    return known, set(known.keys())

def save_jsonl(objs, filepath):
    """Save list of objects as JSONL."""
    with open(filepath, "w") as f:
        for obj in objs:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def trigger_webhooks(entries, timestamp_str):
    """
    T17: Trigger registered webhooks with new entries.
    Loads webhook subscribers and fires them with the new company data.
    """
    webhook_registry_path = BASE_DIR / "data" / "webhook_subscribers.json"
    if not webhook_registry_path.exists():
        print("  No webhook subscribers file found. Skipping webhooks.")
        return

    with open(webhook_registry_path) as f:
        webhooks = json.load(f)

    active_webhooks = {k: v for k, v in webhooks.items() if v.get("active", True)}
    if not active_webhooks:
        print(f"  No active webhooks. (Total registered: {len(webhooks)})")
        return

    # Build payload
    payload = {
        "event_type": "new_entrant",
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "new_count": len(entries),
        "entries": [
            {k: v for k, v in e.items() if not k.startswith("_")}
            for e in entries
        ],
    }

    # Fire each webhook
    success_count = 0
    for name, webhook_data in active_webhooks.items():
        url = webhook_data["url"]
        try:
            r = requests.post(url, json=payload, timeout=10)
            if 200 <= r.status_code < 300:
                print(f"  ✓ {name}: {r.status_code}")
                success_count += 1
                webhook_data["success_count"] = webhook_data.get("success_count", 0) + 1
            else:
                print(
                    f"  ✗ {name}: {r.status_code} {r.text[:100] if r.text else ''}",
                    file=sys.stderr,
                )
                webhook_data["error_count"] = webhook_data.get("error_count", 0) + 1
            webhook_data["last_fired"] = datetime.now(timezone.utc).isoformat()
        except Exception as e:
            print(f"  ✗ {name}: {str(e)}", file=sys.stderr)
            webhook_data["error_count"] = webhook_data.get("error_count", 0) + 1
            webhook_data["last_fired"] = datetime.now(timezone.utc).isoformat()

    # Save updated webhook registry with new stats
    with open(webhook_registry_path, "w") as f:
        json.dump(webhooks, f, indent=2)

    print(f"Webhooks: {success_count}/{len(active_webhooks)} succeeded")

def main():
    if "GITHUB_TOKEN" not in os.environ and not GITHUB_TOKEN:
        print("Warning: No GITHUB_TOKEN found in .env; rate limit 60/hr applies", file=sys.stderr)

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"=== x402 Ecosystem Daily Diff — {today_str} ===")

    # 1. Fetch all ecosystem PRs
    print("Fetching ecosystem PRs from GitHub...")
    prs = gh_get(f"repos/{REPO}/pulls", {"labels": "ecosystem", "state": "all"})
    print(f"Total ecosystem PRs fetched: {len(prs)}")

    # 2. Load snapshot
    known_prs, known_set = load_snapshot()
    print(f"Snapshot contains {len(known_prs)} entries")

    # 3. Identify new PRs
    new_prs = [pr for pr in prs if pr["number"] not in known_set]
    print(f"New PRs detected: {len(new_prs)}")
    if not new_prs:
        print("No new entries. Exiting.")
        sys.exit(0)

    # 4. Enrich new PRs
    enriched_new = []
    for pr in new_prs:
        pr_num = pr["number"]
        title = pr["title"]
        state = pr["state"]
        body = pr.get("body") or ""
        submitter = pr["user"]["login"]
        submitter_html = pr["user"]["html_url"]
        created_at = pr["created_at"]
        merged_at = pr.get("merged_at")
        html_url = pr["html_url"]

        # Domain extraction
        domain_primary, domain_secondary = extract_domains(body)

        # Submitter metadata (simplified: repo count won't be fetched if rate limited; skip for now)
        submitter_repos = None
        submitter_company = None
        # Could fetch user profile with one more API call: GET /users/{login}
        # We'll do it, but be careful with rate limit. Do it at end after all other operations.
        # We'll cache in this run.
        enriched_new.append({
            "pr_number": pr_num,
            "title": title,
            "state": state,
            "submitter": submitter,
            "submitter_repos": submitter_repos,
            "submitter_company": submitter_company,
            "created_at": created_at,
            "domain_primary": domain_primary,
            "domain_secondary": domain_secondary,
            "category": guess_category(title, body),
            "description": (body[:500] if body else title),
            "tech_stack": guess_tech_stack(title, body),
            "has_agent_card": False,  # will check later
            "has_resolved_sh": False,
            "has_llms_txt": False,
            "scrape_title": None,
            "scrape_desc": None,
            "is_deprecation": False,
            "notes": None,
            "merged_at": merged_at,
            "updated_at": pr.get("updated_at"),
            "html_url": html_url,
            "enriched": False,
            "_raw_body": body,
            "_submitter_html": submitter_html
        })

    # 5. Enrich with HTTP checks (agent-card, llms.txt)
    print("Enriching new entries with domain signals...")
    for entry in enriched_new:
        dp = entry["domain_primary"]
        if dp:
            entry["has_agent_card"] = check_url_ok(dp, "/.well-known/agent-card.json")
            entry["has_llms_txt"] = check_url_ok(dp, "/llms.txt")
        entry["enriched"] = True

    # 6. Fetch submitter repos info (batched, with rate limit awareness)
    # Group by unique submitter
    submitters = {e["submitter"] for e in enriched_new if e["submitter"]}
    # For each, fetch user info
    submitter_data = {}
    for login in submitters:
        try:
            r = session.get(f"https://api.github.com/users/{login}")
            if r.status_code == 200:
                ud = r.json()
                submitter_data[login] = {
                    "repos": ud.get("public_repos"),
                    "company": ud.get("company")
                }
            else:
                submitter_data[login] = {"repos": None, "company": None}
            # Be respectful: small delay
            import time; time.sleep(0.2)
        except Exception:
            submitter_data[login] = {"repos": None, "company": None}

    for entry in enriched_new:
        sd = submitter_data.get(entry["submitter"], {})
        entry["submitter_repos"] = sd.get("repos")
        entry["submitter_company"] = sd.get("company")

    # 7. Build diff file
    diff_date = today_str
    diff_file = RESEARCH_DIR / f"x402_daily_diff_{diff_date}.jsonl"
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    save_jsonl(enriched_new, diff_file)
    print(f"Saved daily diff: {diff_file} ({len(enriched_new)} entries)")

    # 8. Update full index snapshot: combine known entries + new entries
    # Remove old snapshot entries for new PR numbers if they existed (shouldn't)
    for new_entry in enriched_new:
        known_prs[new_entry["pr_number"]] = new_entry

    # Sort by pr_number descending for consistency
    updated_snapshot = [known_prs[k] for k in sorted(known_prs.keys(), reverse=True)]
    snapshot_file = PUBLIC_DIR / "flat_x402_ecosystem_full_index.jsonl"
    save_jsonl(updated_snapshot, snapshot_file)
    print(f"Updated full index: {snapshot_file} ({len(updated_snapshot)} total entries)")

    # 9. Regenerate merged-only
    merged = [e for e in updated_snapshot if e.get("state") == "closed" and e.get("merged_at")]
    merged_file = PUBLIC_DIR / "flat_x402_ecosystem_merged_only.jsonl"
    save_jsonl(merged, merged_file)
    print(f"Merged-only dataset: {merged_file} ({len(merged)} entries)")

    # 10. Regenerate new-this-week (entries created in last 7 days)
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
    new_week = [e for e in updated_snapshot if e.get("created_at", "").startswith(week_ago) or e.get("created_at", "") > week_ago]
    new_week_file = PUBLIC_DIR / "flat_x402_ecosystem_new_this_week.jsonl"
    save_jsonl(new_week, new_week_file)
    print(f"New this week dataset: {new_week_file} ({len(new_week)} entries)")

    # 10a. T19: Enrich with intelligence layers (activity_score, tech_fingerprint, funding_signal)
    print("\nApplying intelligence layer enrichment...")
    try:
        from enrich_intelligence import enrich_jsonl
        enrich_jsonl(str(snapshot_file))
        enrich_jsonl(str(merged_file))
        enrich_jsonl(str(new_week_file))
        print("  ✓ Intelligence layers added to all datasets")
    except Exception as e:
        print(f"Warning: intelligence enrichment failed (non-blocking): {e}", file=sys.stderr)

    # 11. Fire webhooks for new entrants (T17)
    print("\nTriggering webhooks for new entrants...")
    try:
        trigger_webhooks(enriched_new, today_str)
    except Exception as e:
        print(f"Warning: webhook firing failed (non-blocking): {e}", file=sys.stderr)

    print("\nAll done. Ready to commit.")

if __name__ == "__main__":
    import time
    main()
