#!/usr/bin/env python3
"""
T18: Master orchestrator for expanding data sources.

Runs all three T18 enrichment pipelines in sequence:
  1. enrich_agent_cards.py — fetch /.well-known/agent.json metadata
  2. enrich_resolved_sh_metadata.py — fetch resolved.sh listing metadata
  3. enrich_a2a_directory.py — check A2A registry for published agents

Usage:
  python scripts/enrich_all_sources.py public/flat_x402_ecosystem_full_index.jsonl
  python scripts/enrich_all_sources.py public/flat_x402_sector_data.jsonl
  python scripts/enrich_all_sources.py --all  # runs on all flat_*.jsonl files
"""

import sys
import subprocess
from pathlib import Path
import json

BASE_DIR = Path(__file__).parent.parent
PUBLIC_DIR = BASE_DIR / "public"

ENRICHERS = [
    "enrich_agent_cards.py",
    "enrich_resolved_sh_metadata.py",
    "enrich_a2a_directory.py",
]


def run_enricher(script_name, jsonl_file):
    """Run a single enricher script."""
    script_path = BASE_DIR / "scripts" / script_name
    if not script_path.exists():
        print(f"  ⚠ {script_name} not found")
        return False

    print(f"  Running {script_name}...")
    try:
        result = subprocess.run(
            [sys.executable, str(script_path), str(jsonl_file)],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode == 0:
            print(f"    ✓ {script_name} succeeded")
            return True
        else:
            print(f"    ✗ {script_name} failed: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"    ✗ {script_name} timeout (>600s)")
        return False
    except Exception as e:
        print(f"    ✗ {script_name} error: {e}")
        return False


def enrich_file(jsonl_file):
    """Run all enrichers on a single file."""
    print(f"\nEnriching {jsonl_file.name}...")
    success_count = 0

    for enricher in ENRICHERS:
        if run_enricher(enricher, jsonl_file):
            success_count += 1

    return success_count == len(ENRICHERS)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    if sys.argv[1] == "--all":
        # Run on all flat_*.jsonl files
        files = sorted(PUBLIC_DIR.glob("flat_*.jsonl"))
        if not files:
            print("No flat_*.jsonl files found in public/")
            sys.exit(1)
        print(f"Found {len(files)} files to enrich:")
        for f in files:
            print(f"  - {f.name}")
    else:
        # Run on specified file
        jsonl_file = Path(sys.argv[1])
        if not jsonl_file.exists():
            print(f"Error: {jsonl_file} not found")
            sys.exit(1)
        files = [jsonl_file]

    all_succeeded = True
    for jsonl_file in files:
        if not enrich_file(jsonl_file):
            all_succeeded = False

    print("\n" + "=" * 60)
    if all_succeeded:
        print(f"✓ All enrichers succeeded on {len(files)} file(s)")
    else:
        print(f"✗ Some enrichers failed (check output above)")
        sys.exit(1)


if __name__ == "__main__":
    main()
