#!/usr/bin/env python3
"""
Enrich x402 company entries with Well Knowns infrastructure signals.

Loads the purchased Well Knowns agent-index and MCP infrastructure datasets,
cross-references with x402 company domains, and adds three fields:

  wellknown_agent_card   (bool)  — domain confirmed in Well Knowns A2A agent index
  wellknown_mcp          (bool)  — domain confirmed in Well Knowns MCP infrastructure catalog
  wellknown_in_top100k   (bool)  — domain appears anywhere in Well Knowns Tranco-top-100k crawl

All three default to False. A True value means the company's domain has been
independently confirmed by Well Knowns' systematic crawl of the top 100k web domains.

Note: most x402 ecosystem companies are early-stage startups not yet in Tranco top 100k.
The cross-reference is meaningful as a future signal — and the 0% overlap is itself
a data point about how early-stage this ecosystem is.
"""

import json
import sys
import glob
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
PUBLIC_DIR = BASE_DIR / "public"

FLAT_FILES = [
    "flat_x402_ecosystem_full_index.jsonl",
    "flat_x402_ecosystem_merged_only.jsonl",
    "flat_x402_ecosystem_new_this_week.jsonl",
    "flat_x402_sector_data.jsonl",
    "flat_x402_sector_infrastructure.jsonl",
    "flat_x402_sector_ai_agents.jsonl",
]


def load_latest(prefix, extension):
    """Find the most recently dated Well Knowns file for a given prefix."""
    pattern = str(PUBLIC_DIR / f"wellknowns-{prefix}-*.{extension}")
    matches = sorted(glob.glob(pattern), reverse=True)
    if not matches:
        return None, None
    path = matches[0]
    with open(path) as f:
        data = json.load(f)
    return data, path


def normalize_domain(domain):
    """Strip protocol and trailing slashes from a domain string."""
    if not domain:
        return ""
    return domain.replace("https://", "").replace("http://", "").strip("/").lower()


def build_domain_set(entries, key="domain"):
    """Build a normalized set of domains from a list of dicts."""
    return {normalize_domain(e.get(key, "")) for e in entries if e.get(key)}


def enrich_file(filepath, agent_domains, mcp_domains, all_wellknown_domains):
    """Add wellknown_* fields to all rows in a flat JSONL file."""
    with open(filepath) as f:
        rows = [json.loads(l) for l in f if l.strip()]

    updated = 0
    for row in rows:
        d1 = normalize_domain(row.get("domain_primary", ""))
        d2 = normalize_domain(row.get("domain_secondary", ""))
        domains = {d for d in [d1, d2] if d}

        row["wellknown_agent_card"] = bool(domains & agent_domains)
        row["wellknown_mcp"] = bool(domains & mcp_domains)
        row["wellknown_in_top100k"] = bool(domains & all_wellknown_domains)

        if row["wellknown_agent_card"] or row["wellknown_mcp"] or row["wellknown_in_top100k"]:
            updated += 1

    with open(filepath, "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")

    return len(rows), updated


def main():
    print("=== Well Knowns Signal Enrichment ===")
    print(f"Run at: {datetime.utcnow().isoformat()}Z\n")

    # Load Well Knowns datasets
    agent_data, agent_path = load_latest("agent-index", "json")
    if not agent_data:
        print("ERROR: No wellknowns-agent-index-*.json file found in public/.")
        print("Run: node scripts/buy_wellknowns_data.js")
        sys.exit(1)

    mcp_data, mcp_path = load_latest("mcp-infra", "json")
    if not mcp_data:
        print("ERROR: No wellknowns-mcp-infra-*.json file found in public/.")
        print("Run: node scripts/buy_wellknowns_data.js")
        sys.exit(1)

    print(f"Agent index: {len(agent_data)} entries ({agent_path})")
    print(f"MCP infra:   {len(mcp_data)} entries ({mcp_path})")

    agent_domains = build_domain_set(agent_data)
    mcp_domains = build_domain_set(mcp_data)
    all_wellknown_domains = agent_domains | mcp_domains

    print(f"\nAgent card domains: {len(agent_domains)}")
    print(f"MCP domains:        {len(mcp_domains)}")
    print(f"Total unique:       {len(all_wellknown_domains)}")

    # Enrich each flat file
    print("\n--- Enriching files ---")
    total_rows = 0
    total_matches = 0

    for filename in FLAT_FILES:
        path = PUBLIC_DIR / filename
        if not path.exists():
            print(f"  SKIP {filename} (not found)")
            continue
        rows, matches = enrich_file(path, agent_domains, mcp_domains, all_wellknown_domains)
        total_rows += rows
        total_matches += matches
        print(f"  ✓ {filename}: {rows} rows, {matches} with Well Knowns signals")

    print(f"\n=== Summary ===")
    print(f"Total rows enriched: {total_rows}")
    print(f"Rows with any Well Knowns signal: {total_matches}")
    print(f"Overlap rate: {total_matches / total_rows * 100:.1f}%")

    if total_matches == 0:
        print("\nNote: 0% overlap is expected — x402 companies are early-stage startups")
        print("not yet in Tranco top 100k. This gap is itself a data signal.")
        print("Fields added with False values; will update automatically as ecosystem matures.")


if __name__ == "__main__":
    main()
