#!/usr/bin/env python3
"""
T18: Enhanced agent-card crawl for richer x402 company metadata.

Fetches /.well-known/agent.json from domains with agent cards and extracts:
  - agent_name, agent_description
  - capabilities (list of agent capabilities)
  - skills (list of installed skills)
  - models (LLM models used)
  - tools_count (number of tools/integrations)
  - agent_url (resolved.sh or custom domain)

Adds these fields to the main JSONL dataset for better discovery and filtering.
"""

import json
import requests
import sys
from pathlib import Path
from datetime import datetime
import time

BASE_DIR = Path(__file__).parent.parent
PUBLIC_DIR = BASE_DIR / "public"

# Hardcoded timeout and retry settings
FETCH_TIMEOUT = 5
MAX_RETRIES = 2
RETRY_DELAY = 0.5


def fetch_agent_card(domain):
    """
    Fetch /.well-known/agent.json from a domain.
    Returns the JSON object if successful, None otherwise.
    """
    if not domain:
        return None

    # Ensure domain doesn't include protocol
    domain = domain.replace("https://", "").replace("http://", "").strip("/")

    url = f"https://{domain}/.well-known/agent.json"

    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(url, timeout=FETCH_TIMEOUT, allow_redirects=True)
            if r.status_code == 200:
                return r.json()
        except (requests.RequestException, ValueError, json.JSONDecodeError):
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
    return None


def extract_agent_metadata(agent_card):
    """Extract key metadata from an agent card."""
    if not agent_card or not isinstance(agent_card, dict):
        return {}

    metadata = {}

    # A2A agent card fields (https://github.com/anthropics/agents-schema)
    if "name" in agent_card:
        metadata["agent_name"] = agent_card.get("name", "")

    if "description" in agent_card:
        metadata["agent_description"] = agent_card.get("description", "")[:200]  # truncate

    # Capabilities (what the agent can do)
    if "capabilities" in agent_card:
        caps = agent_card.get("capabilities", [])
        if isinstance(caps, list):
            metadata["agent_capabilities"] = caps[:10]  # limit to 10

    # Skills/tools installed
    if "skills" in agent_card:
        skills = agent_card.get("skills", [])
        if isinstance(skills, list):
            metadata["agent_skills"] = [s if isinstance(s, str) else s.get("name", "") for s in skills][:10]
            metadata["agent_skills_count"] = len(metadata["agent_skills"])

    # Models used
    if "models" in agent_card:
        models = agent_card.get("models", [])
        if isinstance(models, list):
            metadata["agent_models"] = [m if isinstance(m, str) else m.get("id", "") for m in models]

    # URL to agent (if it's a resolved.sh agent)
    if "url" in agent_card:
        metadata["agent_url"] = agent_card.get("url")

    # Tool count (resolved.sh A2A agents)
    if "tools" in agent_card and isinstance(agent_card["tools"], list):
        metadata["agent_tools_count"] = len(agent_card["tools"])

    # Raw agent type
    if "type" in agent_card:
        metadata["agent_type"] = agent_card.get("type")

    return metadata


def enrich_with_agent_cards(jsonl_file):
    """
    Read a JSONL file, fetch agent cards, and add metadata to entries.
    Writes enriched data back to the same file.
    """
    entries = []
    updated_count = 0
    failed_count = 0

    print(f"Loading {jsonl_file}...")
    with open(jsonl_file) as f:
        for i, line in enumerate(f):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                entries.append(entry)
            except json.JSONDecodeError as e:
                print(f"  Skipping line {i+1}: {e}")

    print(f"Loaded {len(entries)} entries. Fetching agent cards...")

    for i, entry in enumerate(entries):
        if i % 50 == 0 and i > 0:
            print(f"  Progress: {i}/{len(entries)} ({updated_count} updated, {failed_count} failed)")

        # Only fetch if we detected an agent card
        if not entry.get("has_agent_card"):
            continue

        domain = entry.get("domain_primary")
        if not domain:
            continue

        # Fetch and extract
        agent_card = fetch_agent_card(domain)
        if agent_card:
            metadata = extract_agent_metadata(agent_card)
            if metadata:
                entry.update(metadata)
                updated_count += 1
            else:
                failed_count += 1
        else:
            failed_count += 1

    print(f"\nFinal: {updated_count} entries enriched with agent cards")
    print(f"       {failed_count} failed fetches")

    # Write back to JSONL
    print(f"Writing {len(entries)} entries to {jsonl_file}...")
    with open(jsonl_file, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")

    print("Done.")


def main():
    if len(sys.argv) < 2:
        print("Usage: enrich_agent_cards.py <jsonl_file>")
        print("\nExample:")
        print("  python scripts/enrich_agent_cards.py public/flat_x402_ecosystem_full_index.jsonl")
        sys.exit(1)

    jsonl_file = Path(sys.argv[1])
    if not jsonl_file.exists():
        print(f"Error: {jsonl_file} not found")
        sys.exit(1)

    enrich_with_agent_cards(jsonl_file)


if __name__ == "__main__":
    main()
