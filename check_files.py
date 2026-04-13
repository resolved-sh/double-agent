import os, requests, json

with open('.env') as f:
    for line in f:
        if line.startswith('RESOLVED_SH_API_KEY='):
            api_key = line.strip().split('=', 1)[1]
            break

r = requests.get(
    'https://resolved.sh/listing/e8592c18-9052-47b5-bfa3-bfe699193d0e/data',
    headers={'Authorization': f'Bearer {api_key}'}
)
print(f'Status: {r.status_code}')
print(json.dumps(r.json(), indent=2))
