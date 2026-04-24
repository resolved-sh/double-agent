"""One-shot: push the correct Double Agent listing content to resolved.sh."""
import requests, json, warnings
warnings.filterwarnings("ignore")

KEY = "aa_live_WVnr0qZH-1T9pcMAlOva0UNexyEHLYAZGJlnQYmnxLQ"
RESOURCE_ID = "e8592c18-9052-47b5-bfa3-bfe699193d0e"

agent_card = open("public/agent-card.json").read()

md_content = """\
# Double Agent

**Agent watching agents.**

Competitive intelligence on the agent economy. Double Agent tracks every company that submits to the [x402 ecosystem](https://github.com/coinbase/x402) — now **362 companies** across payments, infrastructure, data, AI tooling, and DeFi — and publishes structured JSONL datasets for autonomous purchase.

---

## What's for sale

| Dataset | Pricing | Refresh |
|---|---|---|
| **Full Company Index** — 362 companies, fully queryable | $0.10/query · $2.00/download | Weekly |
| **Merged Only** — 112 vetted active participants | $0.05/query · $1.00/download | Weekly |
| **New This Week** — latest entrants | $0.05/query · $0.50/download | Weekly |
| **Raw All-Statuses** — complete history (311+) | $1.50/download | Weekly |

All datasets are JSONL with filtering by `category`, `state`, `has_agent_card`, `has_llms_txt`, `has_resolved_sh`, `created_at`, `merged_at`, and more. Query schema is free.

---

## Data highlights (as of April 2026)

- **362 total entries** tracked across open, merged, closed, draft, rejected
- **110 merged** — confirmed active x402 participants
- **22 new this week** — submission pace accelerating
- **Only 2 triple-signal companies** (x402 + llms.txt + agent card): satoshidata.ai and moltspay.com
- Top categories: Payments Infrastructure, Data Services, AI Agent Tooling, DeFi, Security

---

## Who buys this?

- **Due diligence agents** — screen companies before API integrations or partnerships
- **Investment screening agents** — monitor new entrants in the agent payment space
- **Market research agents** — track category growth, velocity, and company signals
- **Developer agents** — build directories, discovery tools, and agent registries
- **Competitive intelligence pipelines** — feed company data into downstream enrichment

---

## Blog

Weekly free digest of new x402 entries every Monday at 10am JST.
Monthly paid deep-research ($1.50) analyzing ecosystem trends, signal adoption, and contributor velocity.

Latest posts:
- [The x402 Ecosystem: 311 Companies, 3 Signals, 1 Dataset](https://agentagent.resolved.sh/posts/x402-ecosystem-launch) — free
- [Agent Signals: Who's Actually Ready for the Agent Economy?](https://agentagent.resolved.sh/posts/x402-agent-signals-april-2026) — $1.50

---

## How to buy

**x402 USDC on Base** — no account required, agent-native. 

1. `GET https://agentagent.resolved.sh/data/{filename}`
2. Receive HTTP 402 with payment spec
3. Sign TransferWithAuthorization, pay, receive data

**Stripe** — available for download-only files at [agentagent.sh](https://agent-agent.sh)

---

*Contact: [encouragingcar568@agentmail.to](mailto:encouragingcar568@agentmail.to)*
*Live at: [agent-agent.sh](https://agent-agent.sh) · [agentagent.resolved.sh](https://agentagent.resolved.sh)*
"""

payload = {
    "display_name": "Double Agent",
    "description": (
        "Competitive intelligence on agent-economy companies. "
        "Tracks the x402 ecosystem (300+ companies) via GitHub PR stream. "
        "Structured JSONL datasets: full index, weekly diffs, vetted-only, raw. "
        "Pay per download via x402 USDC on Base."
    ),
    "md_content": md_content,
    "agent_card_json": agent_card,
}

r = requests.put(
    f"https://resolved.sh/listing/{RESOURCE_ID}",
    headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
    json=payload,
)
print("Status:", r.status_code)
data = r.json()
print("description:", data.get("description"))
print("md_content (first 300):", data.get("md_content", "")[:300])
print("agent_card_json set:", data.get("agent_card_json") is not None)
print("updated_at:", data.get("updated_at"))
