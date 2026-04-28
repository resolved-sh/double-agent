#!/usr/bin/env python3
"""
scripts/publish_delta.py

Upload data/delta_output.jsonl to resolved.sh as a separate "x402 New Activity
Feed" data file under the agentagent listing, then emit a data_upload Pulse
event. Idempotent: PUT is upsert, so re-running on the same content is safe.

Pricing: $0.10 query / $0.50 download.

Stores the uploaded file's UUID in data/delta_listing_id.txt so subsequent
operators can patch / inspect without re-listing every file.

Reads RESOLVED_SH_API_KEY from env (or .env in repo root).
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import requests

REPO_ROOT     = Path(__file__).resolve().parent.parent
DATA_DIR      = REPO_ROOT / "data"
DELTA_FILE    = DATA_DIR / "delta_output.jsonl"
LISTING_ID_FILE = DATA_DIR / "delta_listing_id.txt"

DA_RESOURCE_ID = "e8592c18-9052-47b5-bfa3-bfe699193d0e"
DA_SUBDOMAIN   = "agentagent"
REMOTE_FILENAME = "x402_new_activity_feed.jsonl"
QUERY_PRICE    = "0.10"
DOWNLOAD_PRICE = "0.50"
DESCRIPTION    = ("New x402-ecosystem company additions since last publish — "
                  "delta feed, updated multiple times per week.")

BASE = "https://resolved.sh"


def load_env() -> str:
    env_file = REPO_ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                if key not in os.environ:
                    os.environ[key] = val.strip().strip('"').strip("'")
    api_key = os.environ.get("RESOLVED_SH_API_KEY", "")
    if not api_key:
        print("ERROR: RESOLVED_SH_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    return api_key


def has_data(path: Path) -> bool:
    if not path.exists():
        return False
    with path.open() as f:
        for line in f:
            if line.strip():
                return True
    return False


def count_rows(path: Path) -> int:
    n = 0
    with path.open() as f:
        for line in f:
            if line.strip():
                n += 1
    return n


def upload(api_key: str, filepath: Path) -> dict:
    """PUT the file as a data file under DA's listing. Returns parsed response."""
    body = filepath.read_bytes()
    params = {
        "price_usdc":          DOWNLOAD_PRICE,
        "query_price_usdc":    QUERY_PRICE,
        "download_price_usdc": DOWNLOAD_PRICE,
        "description":         DESCRIPTION,
    }
    r = requests.put(
        f"{BASE}/listing/{DA_RESOURCE_ID}/data/{REMOTE_FILENAME}",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/jsonl"},
        params=params,
        data=body,
    )
    if r.status_code != 201:
        print(f"ERROR: upload expected 201, got {r.status_code}: {r.text[:400]}",
              file=sys.stderr)
        sys.exit(1)
    return r.json()


def emit_data_upload(file_id: str, size_bytes: int, row_count: int) -> None:
    payload = json.dumps({
        "file_id":     file_id,
        "filename":    REMOTE_FILENAME,
        "size_bytes":  size_bytes,
        "price_usdc":  float(DOWNLOAD_PRICE),
        "row_count":   row_count,
    })
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "resolved_sh.py"),
        "emit-event", DA_SUBDOMAIN, "data_upload", payload,
    ]
    rc = subprocess.call(cmd)
    if rc != 0:
        print(f"WARN: emit-event exited {rc}", file=sys.stderr)


def main() -> None:
    if not has_data(DELTA_FILE):
        print("No new data, skipping publish")
        sys.exit(0)

    api_key = load_env()

    rows = count_rows(DELTA_FILE)
    size = DELTA_FILE.stat().st_size

    result = upload(api_key, DELTA_FILE)
    file_id  = result.get("id", "")
    filename = result.get("filename", REMOTE_FILENAME)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LISTING_ID_FILE.write_text(file_id + "\n")

    print(f"Uploaded {filename} ({rows} rows, {size} bytes) → file_id={file_id}")
    print(f"  https://{DA_SUBDOMAIN}.resolved.sh/data/{filename}")

    if file_id:
        emit_data_upload(file_id, size, rows)


if __name__ == "__main__":
    main()
