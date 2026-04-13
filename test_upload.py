import os, json, requests, pathlib

# Resolve paths relative to script location
BASE_DIR = pathlib.Path(__file__).parent

# Load API key
with open(BASE_DIR / '.env') as f:
    for line in f:
        if line.startswith('RESOLVED_SH_API_KEY='):
            api_key = line.strip().split('=', 1)[1]
            break

resource_id = 'e8592c18-9052-47b5-bfa3-bfe699193d0e'
filename = 'flat_x402_ecosystem_merged_only.jsonl'
filepath = BASE_DIR / 'public' / filename

with open(filepath, 'rb') as f:
    content = f.read()

headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/jsonl',
}

params = {
    'price_usdc': '1.00',
    'query_price_usdc': '0.05',
    'download_price_usdc': '1.00',
}

url = f'https://resolved.sh/listing/{resource_id}/data/{filename}'
print(f'Uploading {filename} to {url}...')
r = requests.put(url, headers=headers, params=params, data=content)
print(f'Status: {r.status_code}')
if r.status_code != 200:
    print(f'Error: {r.text[:500]}')
else:
    print('Success!')
    print(json.dumps(r.json(), indent=2)[:300])
