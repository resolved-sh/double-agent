---
name: da-daily-scrape
description: Daily x402 ecosystem scraper — fetch new GitHub PRs, enrich, update JSONL datasets, commit
---

You are the Double Agent daily scraper. Run every day at 03:00 UTC.

## Working directory
Auto-detected via `git rev-parse --show-toplevel`, or set `DOUBLE_AGENT_DIR` in the cloud environment to override.

## Steps

1. **Run the scraper:**
   ```bash
   PROJECT_DIR=${DOUBLE_AGENT_DIR:-$(git rev-parse --show-toplevel)}
   cd "$PROJECT_DIR"
   # Load .env only if key vars not already in environment (cloud injects them directly)
   [ -z "$GITHUB_TOKEN" ] && [ -f .env ] && export $(grep -v '^#' .env | xargs)
   python3 scripts/scrape_ecosystem.py
   ```

2. **If the scraper finds new entries (exit 0 with output), commit the results:**
   ```bash
   PROJECT_DIR=${DOUBLE_AGENT_DIR:-$(git rev-parse --show-toplevel)}
   cd "$PROJECT_DIR"
   git add public/flat_x402_ecosystem_full_index.jsonl \
           public/flat_x402_ecosystem_merged_only.jsonl \
           public/flat_x402_ecosystem_new_this_week.jsonl \
           research/
   git commit -m "chore: daily scrape $(date -u +%Y-%m-%d) — add new x402 ecosystem entries

Co-Authored-By: Paperclip <noreply@paperclip.ing>"
   ```

3. **If the scraper exits with "No new entries. Exiting." — that's success, no commit needed.**

4. **Report:** Print the count of new entries found and the updated totals from each dataset.

## Notes
- Do NOT push — Matt pushes manually
- If GitHub rate limit is hit, the script waits automatically
- No GITHUB_TOKEN = 60 req/hr limit; token allows 5000/hr
