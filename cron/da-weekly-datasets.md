---
name: da-weekly-datasets
description: Weekly dataset re-upload to resolved.sh — runs every Monday at 04:00 UTC, after the daily scrape (03:00 UTC) and before the research post (06:00 UTC)
---

You are the Double Agent dataset automation agent. Your job is to re-upload all 7 datasets to resolved.sh with the freshest data after the Monday scrape completes.

## Environment
- Working directory: ~/Documents/double-agent
- API key location: /Users/latentspaceman/Documents/double-agent/.env (RESOLVED_SH_API_KEY)
- Resource ID: e8592c18-9052-47b5-bfa3-bfe699193d0e

## Steps

1. **Load environment and run the upload script:**
   ```bash
   cd ~/Documents/double-agent
   export $(grep -v '^#' .env | xargs)
   bash scripts/weekly_publish_datasets.sh
   ```

2. **Verify upload success** — the script emits Pulse events and prints a summary of all 7 files with sizes and pricing. Check that all 7 files appear in the final listing.

3. **Check earnings** — append current earnings snapshot to data/earnings_log.jsonl:
   ```bash
   cd ~/Documents/double-agent
   export $(grep -v '^#' .env | xargs)
   python3 -c "
import requests, os, json
from datetime import datetime, timezone
r = requests.get('https://resolved.sh/account/earnings', headers={'Authorization': f\"Bearer {os.environ['RESOLVED_SH_API_KEY']}\"})
data = r.json()
data['logged_at'] = datetime.now(timezone.utc).isoformat()
print(json.dumps(data))
" >> data/earnings_log.jsonl
   ```

4. **Commit earnings log if updated:**
   ```bash
   cd ~/Documents/double-agent
   git add data/earnings_log.jsonl
   git diff --cached --quiet || git commit -m "chore: earnings snapshot $(date -u +%Y-%m-%d)

Co-Authored-By: Paperclip <noreply@paperclip.ing>"
   ```

5. **Report:** Print count of files uploaded, total size, and current earnings balance.

## Notes
- Do NOT push — Matt pushes manually
- If the upload script fails on a file, continue with remaining files (set -e is in the script but individual upload failures are non-fatal)
- The script already handles enrichment (T18) and Pulse events (T13) — no need to run them separately
- data/earnings_log.jsonl tracks revenue over time; create the file if it doesn't exist
