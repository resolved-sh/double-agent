#!/usr/bin/env python3
"""
scripts/github_delta.py

Detect newly-merged x402 ecosystem PRs since the last delta run, using DA's
full index as the source of truth.

This script does NOT hit GitHub — DA's daily scrape already populates
public/flat_x402_ecosystem_full_index.jsonl. We just diff that file against
a checkpoint to find what's freshly merged.

Outputs:
  data/delta_output.jsonl       — overwritten each run with newly-merged records
  data/delta_checkpoint.json    — {"last_checked_at": ISO, "last_pr_number": int}

Merge indicator in the schema: a record is "merged" when its `merged_at` field
is a non-null ISO timestamp. (`state` is open|closed; closed-without-merge has
merged_at: null.)
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT  = Path(__file__).resolve().parent.parent
FULL_INDEX = REPO_ROOT / "public" / "flat_x402_ecosystem_full_index.jsonl"
DATA_DIR   = REPO_ROOT / "data"
DELTA_OUT  = DATA_DIR / "delta_output.jsonl"
CHECKPOINT = DATA_DIR / "delta_checkpoint.json"

DA_RESOURCE_ID = "e8592c18-9052-47b5-bfa3-bfe699193d0e"
DA_SUBDOMAIN   = "agentagent"


def load_checkpoint() -> dict:
    if CHECKPOINT.exists():
        try:
            return json.loads(CHECKPOINT.read_text())
        except json.JSONDecodeError:
            print(f"WARN: {CHECKPOINT} is corrupt — using default checkpoint", file=sys.stderr)
    default_since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat().replace("+00:00", "Z")
    return {"last_checked_at": default_since, "last_pr_number": 0}


def save_checkpoint(cp: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CHECKPOINT.write_text(json.dumps(cp, indent=2) + "\n")


def load_full_index() -> list[dict]:
    if not FULL_INDEX.exists():
        print(f"ERROR: {FULL_INDEX} not found", file=sys.stderr)
        sys.exit(1)
    out = []
    with FULL_INDEX.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def load_env_soft() -> bool:
    """Soft-load .env into os.environ. Returns True if RESOLVED_SH_API_KEY ends up set."""
    env_file = REPO_ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                if key not in os.environ:
                    os.environ[key] = val.strip().strip('"').strip("'")
    return bool(os.environ.get("RESOLVED_SH_API_KEY"))


def emit_heartbeat(prs_checked: int, new_records: int) -> None:
    """Fire-and-forget Pulse `monitor` heartbeat. Logs failures, never raises —
    observability must not break the delta cycle."""
    if not load_env_soft():
        print("WARN: RESOLVED_SH_API_KEY not set — skipping heartbeat", file=sys.stderr)
        return
    payload = json.dumps({
        "status":       "healthy",
        "prs_checked":  prs_checked,
        "new_records":  new_records,
    })
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "resolved_sh.py"),
        "emit-event", DA_SUBDOMAIN, "monitor", payload,
    ]
    rc = subprocess.call(cmd)
    if rc != 0:
        print(f"WARN: heartbeat emit-event exited {rc}", file=sys.stderr)


def newly_merged(records: list[dict], since_iso: str) -> list[dict]:
    """Return records whose merged_at is non-null and > since_iso, sorted ascending."""
    new = []
    for rec in records:
        m = rec.get("merged_at")
        if isinstance(m, str) and m and m > since_iso:
            new.append(rec)
    new.sort(key=lambda r: r.get("merged_at") or "")
    return new


def main() -> None:
    cp = load_checkpoint()
    last_checked = cp.get("last_checked_at", "")
    records = load_full_index()

    delta = newly_merged(records, last_checked)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with DELTA_OUT.open("w") as f:
        for rec in delta:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    pr_numbers = [r.get("pr_number") for r in records if isinstance(r.get("pr_number"), int)]
    new_cp = {
        "last_checked_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "last_pr_number":  max(pr_numbers) if pr_numbers else cp.get("last_pr_number", 0),
    }
    save_checkpoint(new_cp)

    print(f"{len(delta)} new records since {last_checked}")
    print(f"Wrote {DELTA_OUT.relative_to(REPO_ROOT)}")
    print(f"Checkpoint advanced: last_checked_at={new_cp['last_checked_at']}, "
          f"last_pr_number={new_cp['last_pr_number']}")

    emit_heartbeat(prs_checked=len(records), new_records=len(delta))


if __name__ == "__main__":
    main()
