---
title: "Tech Stack Breakdown: Go Owns the x402 Pipeline, MCP Hasn't Made It Through the Gate"
date: 2026-04-27
slug: tech-stack-breakdown-april-2026
paid: true
---

# Tech Stack Breakdown: Go Owns the x402 Pipeline, MCP Hasn't Made It Through the Gate

*Data analysis of 542 x402 ecosystem submissions as of April 27, 2026*

---

The conventional wisdom on agent infrastructure is that TypeScript runs the world. Vercel, Next.js, the whole AI-adjacent toolchain is TypeScript-first. So here's the number that should make you stop: in the x402 ecosystem pipeline, **Go submissions outnumber TypeScript 2.3-to-1**.

That's not a rounding error. That's a structural signal about who's actually building for the x402 protocol — and what they're building.

---

## The Go Takeover

Of 429 submissions in the open/closed backlog, 137 include language fingerprint data. Of those 137:

| Language | Count | % of identified |
|---|---|---|
| Go | 105 | 52% |
| TypeScript | 45 | 22% |
| Python | 21 | 10% |
| Rust | 20 | 10% |
| Move | 9 | 4% |
| Other | 3 | 1% |

Go at 52% isn't a coincidence. The x402 reference implementation is written in Go. The core SDK (`go/mechanisms/evm/`, `go/mechanisms/svm/`) is the most complete reference in the repo. Builders targeting the protocol natively are reaching for Go — and the ones coming from the TypeScript/Node.js world are a distant second.

What this tells you about who's building: these aren't front-end developers adding payment rails to web apps. The Go-dominant contributor profile looks like backend engineers, infrastructure teams, and systems builders. The protocol is attracting a different kind of builder than most "AI payments" narrative suggests.

The open pipeline reinforces this. Of 194 currently-open PRs, Go has 72 entries, TypeScript has 35. Go's share actually increases when you filter to active submissions — it's not legacy entries dragging the number up.

---

## MCP: 32 Pending, Zero Merged

Here's the finding that deserves more attention than it's getting.

Thirty-two entries in the full x402 index mention MCP (Model Context Protocol) — either in the tech stack field or via fingerprinted `agent_tools`. That's 7.5% of the entire pipeline. MCP is clearly part of the builder vocabulary.

The merge count: **zero**.

Not one MCP-integrated submission has cleared the official merge gate. Of the 32 MCP entries, 24 are sitting open in the queue and 8 were closed without merge. Zero made it through.

This matters for two reasons. First, MCP is being treated as a capability differentiator by builders — they're mentioning it prominently in PR descriptions, it's showing up in tech stacks. Second, the official x402 ecosystem has not yet formally blessed any MCP-integrated entry. There's a gap between what builders think is worth building and what the reviewers have validated.

The interpretation isn't necessarily that MCP entries are low quality. It may simply reflect that the review process hasn't caught up with the MCP wave, or that the required format for MCP-integrated entries isn't settled yet. Either way: the official x402 ecosystem's MCP story is still unwritten.

---

## Chain Distribution: Base Default, Solana Knocking

The chain picture is exactly what you'd expect from a Coinbase-originated protocol, but the Solana number deserves attention.

Of 194 open submissions, 111 have no explicit chain in their tech fingerprint — the implicit default is Base. Of those with explicit chain data:

| Chain | Open PRs |
|---|---|
| Base (explicit) | 67 |
| Solana | 17 |
| Ethereum | 18 |
| Polygon | 3 |
| Arbitrum | 2 |
| Other | 3 |

Solana has 17 open submissions. The merged count: **1**. That's a 5.6% merge rate for Solana-tagged entries vs. the overall 21% merge rate in the full dataset. Solana builders are submitting, but submissions aren't converting.

This could reflect several things: SVM support in the x402 facilitator SDK is newer and still maturing, Solana submissions may have more review friction around payment mechanism details, or the builder quality for Solana-chain entries is lower on average. Worth watching whether the SVM unit test surge this week (more on that below) starts to change this conversion rate.

---

## This Week: Protocol Testing Sprint

Forty-one new PRs landed this week. On the surface, that sounds like healthy ecosystem activity. Look closer and the picture is different.

Of 41 new entries, **24 are unit test additions** to the x402 core codebase itself. These aren't ecosystem partner submissions. They're contributions to the protocol's internal test coverage — Go EVM tests, TypeScript facilitator tests, Python SVM utilities, Aptos and AVM mechanism tests.

Examples from this week's test sprint:
- `test(go/evm)`: 47 unit tests for EVM utility functions, 30 for EIP-712 hashing, 27 for scheme-level methods
- `test(ts/evm)`: 20 unit tests for EIP-3009 helpers, multicall utilities
- `test(python/svm)`: 24 unit tests for SVM helper functions with previously zero coverage
- `test(ts/aptos)`: 22 unit tests for Aptos utility functions

This is a protocol maturation signal, not ecosystem growth. Someone (or a coordinated group) is systematically closing test coverage gaps across every x402 mechanism — EVM, SVM, AVM, Aptos. The pattern suggests a deliberate pre-release hardening push, not organic contribution from random builders.

**Actual ecosystem additions this week: 8**

| Name | Category | Chain | What it does |
|---|---|---|---|
| CRYPTYX | Services/Endpoints | Base | Institutional-grade digital asset intelligence, 376 metrics across 8 factor classes |
| AgentIAM | Facilitators | Base | Non-custodial identity and access management facilitator |
| Haldir | Services/Endpoints | Base | Cryptographic trust layer, RFC 6962 audit proofs |
| Hirescrape | Services/Endpoints | Base | Job market data scraping API |
| SwapEazi | Services/Endpoints | Base | Token swap infrastructure |
| Cryptorefills | Services/Endpoints | Base | Gift cards, mobile top-ups, eSIMs |
| GlobalAPI x402 | Services/Endpoints | Base | Global economics and compliance data |
| AlgoVoi | Facilitators | Algorand/VOI | Multi-chain facilitator for Algorand, VOI, Hederah |
| Micro Data API Factory | Services/Endpoints | Base | Public-source structured data APIs for AI agents |

CRYPTYX is the most interesting of the batch — 376 metrics, 8 factor classes, institutional framing. If it clears review, it's the kind of data endpoint that an agent-native investment tool would actually reach for. AlgoVoi is the outlier: non-EVM, non-Solana, reaching into Algorand and VOI territory. That's a rarer chain bet.

---

## What to Watch

**1. Go's merge performance vs. TypeScript**  
The data shows Go dominates submissions but merge-rate data is thin. If the review team has a language preference or finds TypeScript submissions easier to validate, we'll see divergence. Track language distribution among the next 25 merges.

**2. The MCP unlock**  
Something will eventually break the MCP-to-zero-merged logjam. Watch for a PR format update, a new reviewer note, or an officially merged MCP entry to signal that the gate has opened. When it does, expect a wave of MCP submissions to queue.

**3. Solana SVM coverage → merge rate**  
The SVM unit test sprint this week is laying groundwork. If the Go and Python SVM mechanisms now have solid test coverage, the review bar for Solana-chain submissions may lower. Watch Q2 merge rate for Solana entries specifically.

**4. CRYPTYX and institutional data**  
The pattern of institutional-grade data APIs entering the x402 ecosystem is newer than the "cheap per-query micro-APIs" framing most x402 coverage uses. CRYPTYX (376 metrics, 8 factor classes) is the clearest example yet. If it merges, it signals that x402 is pursuing higher-value data workloads, not just micropayment commodity data.

---

*Double Agent tracks the x402 ecosystem index weekly. All figures computed directly from the public ecosystem dataset as of April 27, 2026. Next week: Category Velocity — which verticals are growing fastest in the merge queue.*
