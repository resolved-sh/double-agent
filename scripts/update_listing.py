#!/usr/bin/env python3
"""Update Double Agent resolved.sh listing with fresh content."""
import os, sys, requests

# Load API key from .env
with open('.env') as f:
    for line in f:
        if line.startswith('RESOLVED_SH_API_KEY='):
            api_key = line.strip().split('=', 1)[1]
            break

resource_id = 'e8592c18-9052-47b5-bfa3-bfe699193d0e'

# Read agent card
with open('public/agent-card.json') as f:
    agent_card = f.read()

# Read listing md_content
with open('scripts/listing_content.md') as f:
    md_content = f.read()

# Short description for listing card
description = (
    "Competitive intelligence on the agent economy. Tracks 362 x402 ecosystem "
    "companies via GitHub PR stream. Structured JSONL datasets for autonomous "
    "purchase via x402 USDC on Base. Updates weekly."
)

payload = {
    "display_name": "Double Agent",
    "description": description,
    "md_content": md_content,
    "agent_card_json": agent_card,
}

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}

r = requests.put(
    f"https://resolved.sh/listing/{resource_id}",
    headers=headers,
    json=payload,
)

print(f"Status: {r.status_code}")
if r.status_code != 200:
    print(f"Error: {r.text[:500]}")
    sys.exit(1)

data = r.json()
print(f"✓ Listing updated at {data.get('updated_at')}")
print(f"  Display name: {data.get('display_name')}")
print(f"  Subdomain: {data.get('subdomain')}.resolved.sh")
