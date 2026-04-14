#!/usr/bin/env python3
"""
T18: resolved.sh metadata enrichment for x402 companies.

For companies with has_resolved_sh=true, fetch their resolved.sh listing
and extract metadata:
  - resolved_sh_description (short description)
  - resolved_sh_categories (e.g., "Data", "API", "Agent")
  - resolved_sh_file_count (number of data files/products)
  - resolved_sh_download_price_min/max (price range if they sell data)
  - resolved_sh_verified (whether listing is verified)

Adds these fields to the main JSONL dataset.
"""

import json
import requests
import sys
from pathlib import Path
import re

BASE_DIR = Path(__file__).parent.parent
PUBLIC_DIR = BASE_DIR / "public"

FETCH_TIMEOUT = 5
MAX_RETRIES = 2


def extract_subdomain_from_url(domain_or_url):
    """Extract subdomain from domain or full URL."""
    domain = domain_or_url.replace("https://", "").replace("http://", "").strip("/").lower()
    # Remove www. prefix
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def fetch_resolved_sh_metadata(domain):
    """
    Fetch resolved.sh metadata for a company domain.
    Returns metadata dict if found, None otherwise.
    """
    if not domain:
        return None

    # Check if domain is already a resolved.sh domain
    subdomain = extract_subdomain_from_url(domain)

    # Try to fetch resolved.sh listing for this subdomain
    # resolved.sh might have the company as a resource owner
    # For now, we'll try to fetch their public page if they have it

    # Option 1: Check if they have a resolved.sh resource
    # This would require checking resolved.sh directory, but there's no public API yet

    # For now, we can make an educated guess:
    # If domain is company.com and has_resolved_sh=true, they might be at company.resolved.sh
    # Or they might have a custom domain pointing to resolved.sh

    # Try multiple patterns
    candidates = [
        f"https://{subdomain}.resolved.sh",
        f"https://{domain}/",
    ]

    for url in candidates:
        try:
            r = requests.get(url, timeout=FETCH_TIMEOUT, allow_redirects=True)
            if r.status_code == 200:
                # Check if it's actually a resolved.sh page
                if "resolved.sh" in r.text or "agentagent.resolved.sh" in r.url:
                    # Parse the page for metadata
                    return parse_resolved_sh_page(r.text, r.url)
        except requests.RequestException:
            continue

    return None


def parse_resolved_sh_page(html_content, url):
    """Parse resolved.sh page for key metadata."""
    metadata = {}

    # Extract title/description from meta tags or page content
    # (simplified - in production would use BeautifulSoup)

    # Look for description meta tag
    desc_match = re.search(r'<meta name="description" content="([^"]+)"', html_content)
    if desc_match:
        metadata["resolved_sh_description"] = desc_match.group(1)[:200]

    # Look for price information in the page (data files, products)
    # This would be better with actual API access
    price_matches = re.findall(r'\$(\d+(?:\.\d{2})?)', html_content)
    if price_matches:
        prices = [float(p) for p in price_matches]
        if prices:
            metadata["resolved_sh_price_min"] = min(prices)
            metadata["resolved_sh_price_max"] = max(prices)

    # Check for data files mentioned
    file_count_match = re.search(r'(\d+)\s+(?:data\s+)?files?', html_content, re.IGNORECASE)
    if file_count_match:
        metadata["resolved_sh_file_count"] = int(file_count_match.group(1))

    # Store the URL
    metadata["resolved_sh_url"] = url

    return metadata if metadata else None


def enrich_with_resolved_sh(jsonl_file):
    """
    Read a JSONL file, fetch resolved.sh metadata, and add to entries.
    """
    entries = []
    updated_count = 0
    skipped_count = 0

    print(f"Loading {jsonl_file}...")
    with open(jsonl_file) as f:
        for i, line in enumerate(f):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                entries.append(entry)
            except json.JSONDecodeError:
                pass

    print(f"Loaded {len(entries)} entries. Fetching resolved.sh metadata...")

    for i, entry in enumerate(entries):
        if i % 50 == 0 and i > 0:
            print(f"  Progress: {i}/{len(entries)} ({updated_count} updated)")

        # Only process entries that indicate resolved.sh presence
        if not entry.get("has_resolved_sh"):
            skipped_count += 1
            continue

        domain = entry.get("domain_primary")
        if not domain:
            continue

        # Fetch metadata
        metadata = fetch_resolved_sh_metadata(domain)
        if metadata:
            entry.update(metadata)
            updated_count += 1

    print(f"\nFinal: {updated_count} entries enriched from resolved.sh")
    print(f"       {skipped_count} entries skipped (no resolved.sh presence)")

    # Write back to JSONL
    print(f"Writing {len(entries)} entries to {jsonl_file}...")
    with open(jsonl_file, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")

    print("Done.")


def main():
    if len(sys.argv) < 2:
        print("Usage: enrich_resolved_sh_metadata.py <jsonl_file>")
        print("\nExample:")
        print("  python scripts/enrich_resolved_sh_metadata.py public/flat_x402_ecosystem_full_index.jsonl")
        sys.exit(1)

    jsonl_file = Path(sys.argv[1])
    if not jsonl_file.exists():
        print(f"Error: {jsonl_file} not found")
        sys.exit(1)

    enrich_with_resolved_sh(jsonl_file)


if __name__ == "__main__":
    main()
