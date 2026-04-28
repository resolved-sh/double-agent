---
title: "Category Velocity: Payments Floods In, the Merge Queue Goes Cold"
date: 2026-04-28
slug: category-velocity-april-2026
paid: true
---

# Category Velocity: Payments Floods In, the Merge Queue Goes Cold

*Data analysis of 433 x402 ecosystem submissions and 113 merges as of April 28, 2026*

The story this week isn't which vertical is winning. It's that no vertical is winning, because nothing is moving.

April logged **3 merged ecosystem PRs against 122 new submissions** — a 2.5% merge rate. In January the same number was 82%. In February, 42%. In March, 22%. The slope is unmistakable, and it has now flattened against the floor. The last substantive ecosystem addition merged was the **Built on Stellar** facilitator listing on March 18 — six weeks ago. Everything that's hit `coinbase/x402` since then has either been a deprecation, a docs note, or a chore PR bumping the foundation repo. The ecosystem directory, as a public artifact, is frozen.

That makes "category velocity" a paradox. Submissions by vertical are still moving — and moving in interesting ways — but the *merged* count is now too small to power a real growth-rate analysis. So this week's read flips the lens: we're tracking what builders are *trying* to ship, knowing the gate is closed and the queue is filling up.

## The headline shift: Payments overtakes AI

For the first time in the ecosystem's tracked history, **Payments/Facilitator submissions outnumbered AI Agents/Infra submissions** in a 28-day window.

| Vertical              | Last 28d (n=67) | Prev 28d (n=140) | Share Change |
|-----------------------|----------------:|-----------------:|-------------:|
| Payments/Facilitator  | 25 (37.3%)      | 20 (14.3%)       | **+23.0 pp** |
| AI Agents/Infra       | 13 (19.4%)      | 18 (12.9%)       | +6.5 pp      |
| Trading/DeFi          | 8 (11.9%)       | 9 (6.4%)         | +5.5 pp      |
| Data/Analytics        | 6 (9.0%)        | 9 (6.4%)         | +2.6 pp      |
| Identity/Trust        | 5 (7.5%)        | 6 (4.3%)         | +3.2 pp      |
| Dev/Infra/Chain       | 3 (4.5%)        | 3 (2.1%)         | +2.4 pp      |
| Search/Knowledge      | 3 (4.5%)        | 4 (2.9%)         | +1.6 pp      |

(Total submission volume is down ~52% week-over-month, in part because the prior window absorbed a wave of bulk listings that hasn't repeated. The share shift is the more meaningful signal.)

This is a notable inversion. For the entire Q1 cycle, AI agent infrastructure was the loudest category in the funnel — orchestration platforms, MCP wrappers, agentic wallets. The pitch was always *agents will pay other agents.* What's arriving now is the inverse: **payment plumbing for human-shaped use cases.** This week's new entrants include AlgoVoi (a multi-chain facilitator spanning Algorand, VOI, Hedera, and Stellar), SwapEazi, GlobalAPI, AgentIAM Facilitator, MoltsPay, Cryptorefills (gift cards / mobile top-ups / eSIMs over USDC), and Rosud. Five of the 13 ecosystem-add PRs filed in the past seven days are facilitators or payment SDKs, not agent products.

If the AI cohort was building demand for x402 rails, the Payments cohort is now competing to *be* those rails.

## What's stalling

Inside the open queue, the picture is less about acceleration than about pile-up. **150 ecosystem-add PRs are open right now. The median age is 38 days. 97 of them — about two-thirds — have been open more than 30 days.** Eight have crossed 60 days. Four are pushing 90+.

Broken down by vertical, the stall is concentrated in two places:

| Vertical              | Open >30d | Last merged in window |
|-----------------------|----------:|-----------------------|
| AI Agents/Infra       | 13        | 6 in last 60d         |
| Payments/Facilitator  | 11        | 5 in last 60d         |
| Trading/DeFi          | 8         | 1 in last 60d         |
| Data/Analytics        | 6         | 1 in last 60d         |
| Search/Knowledge      | 4         | 0 in last 60d         |
| Identity/Trust        | 3         | 0 in last 60d         |
| Other                 | 51        | 19 in last 60d        |

Search/Knowledge and Identity/Trust have **zero merges in the last 60 days** despite steady inbound. Trading/DeFi and Data/Analytics have one each. The "Other" bucket — much of which is older, less-fingerprinted submissions from December–February — accounts for most of the actual merge activity, suggesting the maintainers are draining the back of the queue, not the front. Anything submitted in March or April is essentially waiting in line behind the legacy backlog.

## The new entrants worth flagging

Three submissions from the last week stand out beyond the category mix:

**Haldir** (PR #88) is the first ecosystem entrant pitching itself as a *cryptographic trust layer* — RFC 6962 audit proofs offered as a paid x402 service. This is the closest thing to an Identity/Trust primitive the registry has seen, and it ships an `llms.txt` on the day of submission. If trust/attestation becomes a category, Haldir is the priority date.

**AlgoVoi** (PR #85) is the first facilitator covering Algorand, VOI, Hedera, and Stellar in one bundle. Until now, x402 listings have been ~95% Base/Solana. A multi-chain, non-EVM facilitator with that surface area materially expands what "x402 ecosystem" means.

**CRYPTYX** (PRs #117/#118) is one of only two new submissions this week that ship the full triple-signal stack — `llms.txt` + agent-card + a real domain. It's also one of three duplicate-resubmission patterns observed this week (CRYPTYX, Hirescrape, and DeepBlue Trading API in the prior window), all from accounts with low GitHub history. The pattern suggests submitters are re-opening PRs to push them back to the top of the maintainers' queue. It is not, on the evidence, working.

## The submitter concentration is real

One last note for the contributor-watchers: 0xAxiom now leads cumulative ecosystem-add submissions at 15, more than 3x the next contributor (Deesmo at 5). The top 15 submitters account for ~17% of all ecosystem-add PRs. Most submitters are one-shot. This is the same long-tail shape we've seen since launch, and it hasn't softened.

## What to watch

1. **The April 2026 merge cliff.** Three merges in 28 days is not a quarter-end slowdown; it's a structural pause. The next signal is whether the maintainers do a single bulk-merge sweep or whether the freeze persists into May. If 122 unmerged April submissions sit through May, expect resubmissions, forks of the directory, and pressure to move ecosystem listing off-repo entirely.
2. **Whether Payments stays in the lead.** A 23-percentage-point share swing in one window is large but not stable. If the next window shows Payments holding above 30%, the AI-agents narrative around x402 needs revising — this protocol may be quietly becoming a stablecoin payments rail with an agent flavoring rather than the reverse.
3. **Identity/Trust as a real category.** Haldir is one data point. Watch for follow-on entries claiming attestation, audit, or compliance primitives over x402 in the next 2–3 weeks. If they appear, the ecosystem's surface area is broadening past "agents + payments."
4. **The non-EVM, non-Solana wave.** AlgoVoi (Algorand/VOI/Hedera/Stellar) and the SKALE Network support PR are the leading edge of a multi-chain push. The chain mix in the ecosystem is more concentrated than the marketing suggests. If three or more non-EVM/non-Solana facilitators land in May, that changes the chain-distribution chart materially.

The interesting question for the next dispatch isn't which vertical wins. It's whether the merge queue thaws — and which categories make it through first when it does.
