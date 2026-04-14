#!/usr/bin/env python3
"""
T19: Intelligence layer enrichment for x402 ecosystem data.
Adds: activity_score, tech_fingerprint, funding_signal to each entry.

This module is called after initial enrichment to layer on advanced signals:
- activity_score: freshness + stability (merged) + maturity
- tech_fingerprint: structured tech stack extraction (frameworks, blockchains, AI/LLMs, infra)
- funding_signal: heuristic scoring from description + tech richness
"""

import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Known technology keywords organized by category
TECH_CATEGORIES = {
    "languages": [
        "python", "typescript", "javascript", "go", "rust", "java", "c#", "c++",
        "solidity", "vyper", "move", "swift", "kotlin", "php", "ruby", "elixir"
    ],
    "frameworks": [
        "nodejs", "node.js", "nextjs", "next.js", "react", "vue", "svelte", "angular",
        "fastapi", "django", "flask", "express", "fastify", "axum", "actix",
        "strapi", "supabase", "firebase"
    ],
    "blockchains": [
        "solana", "ethereum", "eth", "base", "arbitrum", "optimism", "polygon",
        "avalanche", "near", "cosmos", "cardano", "polkadot", "stellar"
    ],
    "payment_protocols": [
        "usdc", "usdt", "dai", "usd", "x402", "erc-20", "spl", "stripe", "razorpay"
    ],
    "ai_llms": [
        "gpt-4", "gpt-4o", "gpt-3.5", "claude", "gemini", "llama", "mistral",
        "openai", "anthropic", "deepseek", "groq", "cohere", "palm"
    ],
    "infrastructure": [
        "docker", "kubernetes", "k8s", "vercel", "railway", "heroku", "aws",
        "gcp", "azure", "cloudflare", "workers", "lambda", "fly.io", "render"
    ],
    "agent_tools": [
        "mcp", "eliza", "langgraph", "crewai", "swarms", "autogen", "agents.ai"
    ],
    "data_formats": [
        "jsonl", "json", "csv", "parquet", "arrow", "protobuf", "avro"
    ]
}

# Flatten for easy lookup
ALL_TECHS = {tech: cat for cat, techs in TECH_CATEGORIES.items() for tech in techs}


def activity_score(entry):
    """
    Calculate activity score (0-100) based on:
    - Freshness: days since last update (0-30 days = higher score)
    - Maturity: days in ecosystem (older = higher)
    - Stability: merged PRs get +20 bonus
    """
    now = datetime.now(timezone.utc)

    # Freshness: last updated
    updated_at_str = entry.get("updated_at", "")
    if updated_at_str:
        try:
            updated_at = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
            days_since_update = (now - updated_at).days
            # 0 days = 30 pts, 30+ days = 0 pts
            freshness = max(0, 30 - days_since_update)
        except:
            freshness = 0
    else:
        freshness = 0

    # Maturity: days in ecosystem (created_at)
    created_at_str = entry.get("created_at", "")
    if created_at_str:
        try:
            created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            days_in_ecosystem = (now - created_at).days
            # 0 days = 0 pts, 365+ days = 40 pts
            maturity = min(40, days_in_ecosystem // 9)
        except:
            maturity = 0
    else:
        maturity = 0

    # Stability: merged PRs get bonus
    stability = 20 if (entry.get("state") == "closed" and entry.get("merged_at")) else 0

    # Bonus for signals
    signal_bonus = 0
    if entry.get("has_agent_card"):
        signal_bonus += 5
    if entry.get("has_llms_txt"):
        signal_bonus += 5
    if entry.get("has_resolved_sh"):
        signal_bonus += 5

    return min(100, freshness + maturity + stability + signal_bonus)


def tech_fingerprint(entry):
    """
    Extract structured tech fingerprint from tech_stack and description.
    Returns dict with breakdown by category.
    """
    tech_stack = entry.get("tech_stack") or ""
    description = entry.get("description") or ""
    title = entry.get("title") or ""
    text = (tech_stack + " " + description + " " + title).lower()

    fingerprint = {cat: [] for cat in TECH_CATEGORIES.keys()}
    fingerprint["other"] = []

    # Extract techs
    found = set()
    for tech in ALL_TECHS.keys():
        if tech in text and tech not in found:
            found.add(tech)
            cat = ALL_TECHS[tech]
            fingerprint[cat].append(tech)

    # Clean up empty categories
    fingerprint = {k: v for k, v in fingerprint.items() if v}

    return fingerprint


def funding_signal(entry):
    """
    Score funding likelihood (0-100) based on:
    - Language hints (mentions of seed, series, VC, funded, investment)
    - Feature richness (number of distinct techs, APIs offered)
    - Tech stack sophistication (mature frameworks, established blockchains)
    - Submitter signals (repo count, company affiliation)
    """
    score = 0
    description_text = (entry.get("description") or "") + " " + (entry.get("title") or "")
    description = description_text.lower()

    # Text signals
    funding_keywords = ["seed", "series", "vc", "venture", "funded", "investment", "backed",
                       "raise", "fundraise", "funding round", "capital", "investors", "incubator"]
    for kw in funding_keywords:
        if kw in description:
            score += 15
            break  # Only count once

    # Feature richness: count distinct API endpoints or services
    feature_signals = re.findall(r'(\d+)\s*(?:api|endpoint|tool|service|pack)', description)
    if feature_signals:
        num_features = max(int(f) for f in feature_signals if f.isdigit())
        score += min(20, num_features // 5)  # Every 5 features = +4 pts

    # Tech sophistication
    tech_stack = entry.get("tech_stack", "").lower()
    sophisticated_techs = ["kubernetes", "terraform", "rust", "golang", "distributed"]
    for tech in sophisticated_techs:
        if tech in tech_stack:
            score += 5

    # Blockchain sophistication (multi-chain = more likely funded)
    blockchains_found = sum(1 for bc in TECH_CATEGORIES["blockchains"]
                           if bc in description)
    if blockchains_found > 1:
        score += 10

    # Submitter signals
    if entry.get("submitter_company"):
        score += 15  # Company-affiliated submitter

    submitter_repos = entry.get("submitter_repos")
    if submitter_repos and submitter_repos > 20:
        score += 10  # Prolific contributor

    return min(100, score)


def enrich_entry(entry):
    """Add intelligence fields to a single entry."""
    entry["activity_score"] = activity_score(entry)
    entry["tech_fingerprint"] = tech_fingerprint(entry)
    entry["funding_signal"] = funding_signal(entry)
    return entry


def enrich_jsonl(input_file, output_file=None):
    """
    Enrich all entries in a JSONL file with intelligence layers.
    If output_file is None, overwrites input file.
    """
    output_file = output_file or input_file
    entries = []

    with open(input_file) as f:
        for line in f:
            try:
                obj = json.loads(line)
                entries.append(enrich_entry(obj))
            except json.JSONDecodeError:
                continue

    with open(output_file, "w") as f:
        for obj in entries:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    return len(entries)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: enrich_intelligence.py <input.jsonl> [output.jsonl]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_file

    count = enrich_jsonl(input_file, output_file)
    print(f"Enriched {count} entries in {output_file}")
