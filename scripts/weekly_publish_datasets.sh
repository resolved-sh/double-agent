#!/bin/bash
set -e

# T09: Weekly dataset re-upload to resolved.sh
# Runs after daily scraper on Mondays at 04:00 UTC
# Uploads updated flat JSONL files with correct pricing

cd "$(dirname "$0")/.."

# Load .env to get RESOLVED_SH_API_KEY
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

RESOURCE_ID="e8592c18-9052-47b5-bfa3-bfe699193d0e"

echo "Uploading weekly dataset updates to resolved.sh (resource: $RESOURCE_ID)"

python3 scripts/resolved_sh.py upload "$RESOURCE_ID" public/flat_x402_ecosystem_full_index.jsonl 2.00 --query-price 0.10 --download-price 2.00
python3 scripts/resolved_sh.py upload "$RESOURCE_ID" public/flat_x402_ecosystem_merged_only.jsonl 1.00 --query-price 0.05 --download-price 1.00
python3 scripts/resolved_sh.py upload "$RESOURCE_ID" public/flat_x402_ecosystem_new_this_week.jsonl 0.50 --query-price 0.05 --download-price 0.50

echo "Weekly dataset upload complete."
