#!/bin/bash
set -e

# T09/T16: Weekly dataset re-upload to resolved.sh
# Replaces existing dataset files with fresh versions from flat_* sources
# Uploads: full_index, merged_only, new_this_week, raw_all, sector_data, sector_infrastructure, sector_ai_agents = 7 files
# Platform limit: 10 files. Room for 3 more Phase 3 products.

cd "$(dirname "$0")/.."

# Load .env
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

RESOURCE_ID="e8592c18-9052-47b5-bfa3-bfe699193d0e"
SUBDOMAIN="agentagent"
API_KEY="$RESOLVED_SH_API_KEY"
UPLOAD_START=$(date +%s)

echo "=== Weekly Dataset Upload ==="
echo "Resource: $RESOURCE_ID"
echo ""

# T13: Emit task_started Pulse event
echo "→ Emitting task_started Pulse event..."
python3 scripts/resolved_sh.py emit-event "$SUBDOMAIN" task_started \
  '{"task_type":"sync","estimated_seconds":120}' || true
echo ""

# T18: Enrich all data sources (agent cards, resolved.sh metadata, A2A directory)
echo "--- Enriching data sources (T18) ---"
python3 scripts/enrich_all_sources.py --all || echo "  ⚠ T18 enrichment had warnings (non-blocking)"
echo ""

# Helper: delete file by filename (looks up UUID first)
delete_file() {
  local filename="$1"
  echo "→ Checking if '$filename' exists on resolved.sh..."
  file_id=$(python3 -c "
import requests, os, sys
api_key = os.environ['RESOLVED_SH_API_KEY']
r = requests.get('https://resolved.sh/listing/${RESOURCE_ID}/data', headers={'Authorization': f'Bearer {api_key}'})
files = r.json().get('files', [])
for f in files:
    if f['filename'] == '${filename}':
        print(f['id'])
        sys.exit(0)
print('NOT_FOUND')
" 2>/dev/null)
  
  if [ "$file_id" = "NOT_FOUND" ]; then
    echo "  Not found — skipping delete"
    return 0
  fi
  
  echo "  Found file ID: $file_id — deleting..."
  python3 -c "
import requests, os
api_key = os.environ['RESOLVED_SH_API_KEY']
r = requests.delete('https://resolved.sh/listing/${RESOURCE_ID}/data/${file_id}', headers={'Authorization': f'Bearer {api_key}'})
print('  Delete status:', r.status_code)
if r.status_code not in (200, 204):
    print('  ERROR:', r.text[:200])
    exit(1)
"
  echo "  Deleted."
}

# Helper: upload flat_ file as target filename
upload_file() {
  local flat_file="$1"   # e.g. flat_x402_ecosystem_merged_only.jsonl
  local target_name="$2" # e.g. x402_ecosystem_merged_only.jsonl
  local query_price="$3"
  local download_price="$4"
  
  echo "→ Uploading $flat_file as $target_name..."
  
  python3 -c "
import requests, os
api_key = os.environ['RESOLVED_SH_API_KEY']
resource = '${RESOURCE_ID}'
with open('public/${flat_file}', 'rb') as f:
    content = f.read()
headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/jsonl'}
params = {
    'price_usdc': '${download_price}',
    'query_price_usdc': '${query_price}',
    'download_price_usdc': '${download_price}'
}
r = requests.put(f'https://resolved.sh/listing/{resource}/data/${target_name}', headers=headers, params=params, data=content)
print(f'  Status: {r.status_code}')
if r.status_code not in (200, 201):
    print('  ERROR:', r.text[:300])
    exit(1)
result = r.json()
print(f'  ✓ Uploaded {result.get(\"filename\")} — {result.get(\"size_bytes\")} bytes, queryable={result.get(\"queryable\")}')
"
}

# Process each dataset
echo "--- Updating full_index ---"
delete_file "x402_ecosystem_full_index.jsonl"
upload_file "flat_x402_ecosystem_full_index.jsonl" "x402_ecosystem_full_index.jsonl" "0.10" "2.00"

echo ""
echo "--- Updating merged_only ---"
delete_file "x402_ecosystem_merged_only.jsonl"
upload_file "flat_x402_ecosystem_merged_only.jsonl" "x402_ecosystem_merged_only.jsonl" "0.05" "1.00"

echo ""
echo "--- Updating new_this_week ---"
delete_file "x402_ecosystem_new_this_week.jsonl"
upload_file "flat_x402_ecosystem_new_this_week.jsonl" "x402_ecosystem_new_this_week.jsonl" "0.05" "0.50"

echo ""
echo "--- Regenerating sector packs from full_index ---"
python3 scripts/build_sector_packs.py

echo ""
echo "--- Updating sector_data ---"
delete_file "x402_sector_data.jsonl"
upload_file "flat_x402_sector_data.jsonl" "x402_sector_data.jsonl" "0.05" "0.75"

echo ""
echo "--- Updating sector_infrastructure ---"
delete_file "x402_sector_infrastructure.jsonl"
upload_file "flat_x402_sector_infrastructure.jsonl" "x402_sector_infrastructure.jsonl" "0.05" "0.75"

echo ""
echo "--- Updating sector_ai_agents ---"
delete_file "x402_sector_ai_agents.jsonl"
upload_file "flat_x402_sector_ai_agents.jsonl" "x402_sector_ai_agents.jsonl" "0.05" "0.75"

echo ""
echo "=== Weekly dataset upload complete ==="

# T13: Emit task_completed Pulse event
UPLOAD_END=$(date +%s)
DURATION=$((UPLOAD_END - UPLOAD_START))
echo ""
echo "→ Emitting task_completed Pulse event (duration: ${DURATION}s)..."
python3 scripts/resolved_sh.py emit-event "$SUBDOMAIN" task_completed \
  "{\"task_type\":\"sync\",\"duration_seconds\":${DURATION},\"success\":true}" || true

echo ""
echo "Current files on resolved.sh:"
python3 -c "
import requests, os
r = requests.get('https://resolved.sh/listing/${RESOURCE_ID}/data', headers={'Authorization': f\"Bearer {os.environ['RESOLVED_SH_API_KEY']}\"})
files = r.json().get('files', [])
for f in files:
    print(f\"  [{f['filename']}] {f['size_bytes']} bytes, queryable={f.get('queryable')}, query=\${f.get('effective_query_price')}, download=\${f.get('effective_download_price')}\")
"
