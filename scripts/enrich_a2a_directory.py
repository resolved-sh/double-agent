#!/usr/bin/env python3
"""
T18: A2A directory enrichment for x402 companies.

Crawls the A2A (Agent-to-Agent) registry to find x402 companies that have
published agents. Adds:
  - a2a_registered (bool) — is this company in the A2A registry?
  - a2a_agent_name (str) — the agent's name
  - a2a_agent_description (str) — brief description
  - a2a_skills (list) — skills the agent exposes
  - a2a_url (str) — link to agent in registry

The A2A registry is typically at resolved.sh or similar platforms.
"""

import json
import requests
import sys
from pathlib import Path
import re
from urllib.parse import urlparse

BASE_DIR = Path(__file__).parent.parent
PUBLIC_DIR = BASE_DIR / "public"

FETCH_TIMEOUT = 5


def normalize_domain_or_name(domain):
    """Extract base domain name for A2A lookup."""
    domain = domain.lower().strip()
    domain = domain.replace("https://", "").replace("http://", "").strip("/")
    if domain.startswith("www."):
        domain = domain[4:]
    # Get just the domain name (before first dot)
    base_name = domain.split(".")[0]
    return base_name, domain


def check_a2a_registry(domain, submitter=None):
    """
    Check if a company has an agent in the A2A registry.
    Returns metadata if found, None otherwise.
    """
    if not domain:
        return None

    base_name, full_domain = normalize_domain_or_name(domain)

    # Try to find the agent in A2A registry
    # Approach 1: Try resolved.sh agent endpoint
    candidates = [
        f"https://{base_name}.resolved.sh/.well-known/agent.json",
        f"https://{full_domain}/.well-known/agent.json",
    ]

    # If we have submitter info, also try that
    if submitter:
        submitter_name = submitter.lower().replace(" ", "-").replace("_", "-")
        candidates.insert(0, f"https://{submitter_name}.resolved.sh/.well-known/agent.json")

    for url in candidates:
        try:
            r = requests.get(url, timeout=FETCH_TIMEOUT)
            if r.status_code == 200:
                try:
                    card = r.json()
                    return extract_a2a_metadata(card, url)
                except:
                    pass
        except requests.RequestException:
            pass

    return None


def extract_a2a_metadata(card, source_url):
    """Extract A2A-specific metadata from agent card."""
    metadata = {}

    # Mark as registered in A2A
    metadata["a2a_registered"] = True
    metadata["a2a_url"] = source_url

    # Extract agent information
    if "name" in card:
        metadata["a2a_agent_name"] = card.get("name", "")

    if "description" in card:
        desc = card.get("description", "")
        metadata["a2a_agent_description"] = desc[:200] if desc else ""

    # Extract skills
    if "skills" in card:
        skills = card.get("skills", [])
        if isinstance(skills, list):
            skill_names = []
            for skill in skills:
                if isinstance(skill, str):
                    skill_names.append(skill)
                elif isinstance(skill, dict) and "name" in skill:
                    skill_names.append(skill["name"])
            if skill_names:
                metadata["a2a_skills"] = skill_names

    # Extract capabilities
    if "capabilities" in card:
        caps = card.get("capabilities", [])
        if isinstance(caps, list):
            metadata["a2a_capabilities"] = caps[:5]

    # Check if it's a published service
    if "type" in card:
        metadata["a2a_agent_type"] = card.get("type")

    return metadata if metadata else None


def enrich_with_a2a(jsonl_file):
    """
    Read JSONL file and enrich entries with A2A directory data.
    """
    entries = []
    found_count = 0
    checked_count = 0

    print(f"Loading {jsonl_file}...")
    with open(jsonl_file) as f:
        for line in f:
            if line.strip():
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    print(f"Loaded {len(entries)} entries. Checking A2A registry...")

    for i, entry in enumerate(entries):
        if i % 50 == 0 and i > 0:
            print(f"  Progress: {i}/{len(entries)} ({found_count} in A2A registry)")

        # Check if company might have published an agent
        # Companies more likely to have agents: AI agents, infrastructure, data
        category = entry.get("category", "").lower()
        if "ai" not in category and "agent" not in category and "service" not in category:
            entry["a2a_registered"] = False
            continue

        checked_count += 1
        domain = entry.get("domain_primary")
        submitter = entry.get("submitter")

        # Check A2A registry
        a2a_data = check_a2a_registry(domain, submitter)
        if a2a_data:
            entry.update(a2a_data)
            found_count += 1
        else:
            entry["a2a_registered"] = False

    print(f"\nFinal: {found_count} entries found in A2A registry")
    print(f"       {checked_count} entries checked (filtered by category)")

    # Write back
    print(f"Writing {len(entries)} entries to {jsonl_file}...")
    with open(jsonl_file, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")

    print("Done.")


def main():
    if len(sys.argv) < 2:
        print("Usage: enrich_a2a_directory.py <jsonl_file>")
        print("\nExample:")
        print("  python scripts/enrich_a2a_directory.py public/flat_x402_ecosystem_full_index.jsonl")
        sys.exit(1)

    jsonl_file = Path(sys.argv[1])
    if not jsonl_file.exists():
        print(f"Error: {jsonl_file} not found")
        sys.exit(1)

    enrich_with_a2a(jsonl_file)


if __name__ == "__main__":
    main()
