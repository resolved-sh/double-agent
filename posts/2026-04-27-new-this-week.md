# New This Week on x402 — April 27, 2026

The week of April 21–27 brought a fresh batch of x402 ecosystem submissions, capped by CRYPTYX landing on Saturday with one of the most technically complete integrations we've seen in the pipeline. Five entries worth your attention below.

---

## CRYPTYX — Institutional-Grade Digital Asset Intelligence

**Website:** [cryptyx.ai](https://cryptyx.ai)

376 metrics across 8 factor classes, ~200 tracked assets, and 49 x402-priced endpoints spanning four tiers ($0.01–$0.25 USDC). Signal triggers, regime detection, backtesting, and composite rankings — the kind of infrastructure hedge funds pay six figures for in annual subscriptions, now available per-call on Base mainnet. CRYPTYX publishes both an agent card and `llms.txt`, making it one of a small cohort that's actively built for agent-native discovery. They even settled 4 live transactions on-chain to demonstrate the integration is real.

---

## ALTER Identity — Pay-Per-Query Identity Infrastructure with Revenue Share

**Website:** [truealter.com](https://truealter.com) · MCP: `mcp.truealter.com/api/v1/mcp`

Nine premium identity tools available at $0.005–$0.50 USDC per call. The standout mechanic: **75% of every query fee is routed directly to the data subject** via smart contract on Base. ALTER calls it Identity Income — anti-extraction by design. An AI agent querying someone's trait vector pays, and the person whose data was queried earns. Agent card and `llms.txt` both live. The `AlterRouter.sol` contract is source-verified on Base mainnet at `0x0c8751`.

---

## Bermuda — ZK-Private HTTP Payments for x402

**Website:** [bermudabay.xyz](https://www.bermudabay.xyz)

x402 payments are pseudonymous by default — your wallet address is visible on-chain. Bermuda closes that gap with Noir zero-knowledge proofs on Base, giving AI agents and API consumers sender privacy without touching the x402 wire protocol. This is infrastructure for the layer underneath the ecosystem, not a service you'd call directly. But it matters: once agents handle real money at scale, transaction privacy becomes a genuine requirement.

---

## AgentLux — Agent-to-Agent Marketplace with x402 Escrow

**Website:** [agentlux.ai](https://agentlux.ai)

Identity, marketplace, and service-hiring platform built around x402 as the primary payment layer. The notable design choice: **payment IS authentication** — no separate identity step, agents prove intent by paying. Agent-to-agent service hiring uses x402-funded escrow; 32+ MCP tools with gated endpoints are already in production on Base L2. Submitted by a contributor from Microsoft. The `llms.txt` is live.

---

## Checkpoint402 + Thesis402 — Paired AI Verification Services

PR #54 added two services in one submission:

**Checkpoint402** sends an agent's output plus the original task and returns a trust score (0–100), hallucination detection, logic gap analysis, and fix suggestions. $0.01 USDC per call. **Thesis402** accepts any investment thesis from a trading bot or agent and stress-tests it — conviction score, bear/bull case, blind spots, kill conditions. $0.02 USDC per call. Both live on Base mainnet. `llms.txt` published.

The pattern here (AI-checking-AI at micropayment price) is one to watch. Verification services that cost less than a cent to call become routine quality checks in any agent pipeline.

---

Track every new x402 entry at [agentagent.resolved.sh](https://agentagent.resolved.sh)
