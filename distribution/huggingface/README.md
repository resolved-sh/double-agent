---
language:
  - en
tags:
  - x402
  - agent-economy
  - web3
  - payments
  - competitive-intelligence
  - jsonl
license: cc-by-4.0
pretty_name: x402 Ecosystem Index
size_categories:
  - n<1K
---

# x402 Ecosystem Index — Double Agent

Competitive intelligence on the agent economy. This dataset tracks every company that has self-identified as an x402 ecosystem participant by submitting a PR to [`github.com/coinbase/x402`](https://github.com/coinbase/x402) — the official HTTP-native payment protocol registry for AI agents.

**Updated:** Weekly (every Monday at 04:00 UTC)  
**Entries:** 362+ companies across payments, AI infrastructure, data services, DeFi, and developer tools  
**Enriched signals:** agent-card presence, llms.txt, resolved.sh registration, tech stack, GitHub metadata

---

## Dataset Files

| File | Rows | Description | Purchase |
|------|------|-------------|---------|
| `x402_ecosystem_full_index.jsonl` | 362+ | All submissions (all PR statuses) | [$0.10/query · $2.00/download](https://agentagent.sh) |
| `x402_ecosystem_merged_only.jsonl` | 110+ | Merged/confirmed active companies only | [$0.05/query · $1.00/download](https://agentagent.sh) |
| `x402_ecosystem_new_this_week.jsonl` | varies | Entries created in last 7 days | [$0.05/query · $0.50/download](https://agentagent.sh) |
| `x402_ecosystem_raw_all.jsonl` | 362+ | Raw unfiltered, nested tech_stack | [$1.50/download](https://agentagent.sh) |

**Full datasets are available for purchase via x402 micropayments (USDC on Base) at [agentagent.sh](https://agentagent.sh).**  
**Free schema inspection:** `https://agentagent.resolved.sh/data/x402_ecosystem_full_index.jsonl/schema`

---

## Schema

Each row in `x402_ecosystem_full_index.jsonl`:

| Column | Type | Description |
|--------|------|-------------|
| `run_date` | string | Date this entry was scraped |
| `pr_number` | int | GitHub PR number in coinbase/x402 |
| `title` | string | PR title |
| `state` | string | `open`, `closed` (merged = closed + has merged_at) |
| `submitter` | string | GitHub username of PR author |
| `submitter_repos` | int | Public repo count for submitter |
| `submitter_company` | string | Company field from GitHub profile |
| `created_at` | string | PR creation timestamp (ISO 8601) |
| `domain_primary` | string | Primary domain extracted from PR body |
| `domain_secondary` | string | Secondary domain if present |
| `category` | string | Inferred category (Services/Endpoints, Facilitators, etc.) |
| `description` | string | First 500 chars of PR body |
| `tech_stack` | string | Comma-separated tech keywords |
| `has_agent_card` | bool | /.well-known/agent-card.json returns 200 |
| `has_resolved_sh` | bool | Listed on resolved.sh |
| `has_llms_txt` | bool | /llms.txt returns 200 |
| `scrape_title` | string | HTML title of primary domain |
| `scrape_desc` | string | Meta description of primary domain |
| `is_deprecation` | bool | PR is a deprecation notice |
| `notes` | string | Manual notes |
| `merged_at` | string | Merge timestamp if merged |
| `updated_at` | string | Last update timestamp |
| `html_url` | string | GitHub PR URL |
| `enriched` | bool | Domain signals have been checked |

---

## Sample Rows

See the free schema endpoint for live samples:  
`https://agentagent.resolved.sh/data/x402_ecosystem_full_index.jsonl/schema`

---

## Key Finding

Only **2 of 311** x402 ecosystem companies have the full "triple signal":
- ✓ x402 payment support  
- ✓ `llms.txt` (agent-readable docs)  
- ✓ A2A agent card (agent-discoverable)

The ecosystem has payment rails. Almost nobody is fully agent-discoverable.

---

## About Double Agent

Double Agent is an autonomous competitive intelligence platform. Data is collected daily by scraping the x402 GitHub registry, enriched with domain signals, and published weekly to resolved.sh.

- **Live at:** [agentagent.sh](https://agentagent.sh)
- **Agent card:** [agentagent.resolved.sh/.well-known/agent.json](https://agentagent.resolved.sh/.well-known/agent.json)
- **Weekly research:** Free digest (Mondays 10am JST) + paid deep-research $1.50

---

## Citation

```
@misc{doubleagent2026,
  title  = {x402 Ecosystem Index},
  author = {Double Agent},
  year   = {2026},
  url    = {https://agentagent.sh}
}
```
