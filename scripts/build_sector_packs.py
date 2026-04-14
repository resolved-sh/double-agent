#!/usr/bin/env python3
"""
T16: Build sector intelligence packs from the full x402 ecosystem index.

Sectors:
  - data:           Data APIs, analytics, search, intelligence feeds
  - infrastructure: Payment rails, SDKs, gateways, orchestration, facilitators
  - ai_agents:      AI agent platforms, LLM tools, MCP servers

Output: public/flat_x402_sector_<name>.jsonl (flat tech_stack, same schema as full_index)
"""
import json
import sys
import warnings
warnings.filterwarnings("ignore")

SOURCE = "public/flat_x402_ecosystem_full_index.jsonl"
OUTPUT_DIR = "public"

SECTOR_KEYWORDS = {
    "data": [
        "data", "dataset", "analytics", "intelligence", "feed", "index",
        "database", "storage", "query", "search", "monitoring", "insights",
        "metrics", "scraping", "crawl", "price feed", "real-time api",
        "financial data", "market data", "sentiment", "news api",
        "research api", "property data", "flight data", "weather api",
    ],
    "infrastructure": [
        "infrastructure", "infra", "gateway", "relay", "protocol", "sdk",
        "framework", "middleware", "facilitator", "orchestrat", "wallet",
        "payment rail", "routing", "proxy", "verifier", "paywall",
        "integration", "connector", "plugin", "library", "client",
    ],
    "ai_agents": [
        "agent", "llm", "language model", "assistant", "automation",
        "mcp server", "mcp tool", "multi-agent", "chatbot", "reasoning",
        "gpt", "claude", "gemini", "inference", "generative", "copilot",
        "prompt", "tool calling", "function calling", "ai tool",
        "ai service", "ai platform", "ai api",
    ],
}


def score_row(row: dict, keywords: list[str]) -> int:
    text = " ".join([
        (row.get("title") or ""),
        (row.get("description") or ""),
        (row.get("scrape_title") or ""),
        (row.get("scrape_desc") or ""),
        (row.get("tech_stack") or ""),
        (row.get("notes") or ""),
    ]).lower()
    return sum(1 for kw in keywords if kw in text)


def classify(row: dict) -> str:
    scores = {
        sector: score_row(row, keywords)
        for sector, keywords in SECTOR_KEYWORDS.items()
    }
    best_score = max(scores.values())
    if best_score == 0:
        return "other"
    return max(scores, key=scores.get)


def main():
    with open(SOURCE) as f:
        rows = [json.loads(line) for line in f if line.strip()]

    print(f"Loaded {len(rows)} rows from {SOURCE}")

    buckets: dict[str, list[dict]] = {"data": [], "infrastructure": [], "ai_agents": []}
    other_count = 0

    for row in rows:
        sector = classify(row)
        if sector in buckets:
            buckets[sector].append(row)
        else:
            other_count += 1

    print(f"\nSector distribution:")
    for sector, sector_rows in buckets.items():
        print(f"  {sector:20s}  {len(sector_rows):3d} rows")
    print(f"  {'other':20s}  {other_count:3d} rows (not included in packs)")

    for sector, sector_rows in buckets.items():
        filename = f"{OUTPUT_DIR}/flat_x402_sector_{sector}.jsonl"
        with open(filename, "w") as f:
            for row in sector_rows:
                f.write(json.dumps(row) + "\n")
        print(f"\nWrote {len(sector_rows)} rows → {filename}")

    # T19: Apply intelligence enrichment to sector packs
    try:
        from enrich_intelligence import enrich_jsonl
        for sector in buckets.keys():
            filename = f"{OUTPUT_DIR}/flat_x402_sector_{sector}.jsonl"
            enrich_jsonl(filename)
        print("\n✓ Intelligence enrichment applied to all sector packs")
    except Exception as e:
        print(f"\nWarning: Intelligence enrichment failed (non-blocking): {e}", file=sys.stderr)

    print("\nDone.")


if __name__ == "__main__":
    main()
