# Autonomous Operations — Double Agent & Well Knowns

This document covers how automation is structured for both the Double Agent and Well Knowns businesses on resolved.sh, and how to replicate this pattern for future businesses.

---

## How Automation Works in Claude Desktop

### Two systems, one location
Claude Desktop has one relevant location for scheduled automation:

- `~/Documents/Claude/Scheduled/` — Scheduled task definitions managed by the Cowork Schedule tab. Each subdirectory is a task with a `SKILL.md` prompt.

Note: `~/.claude/scheduled-tasks/` is a *separate* system — it holds slash command skills for Claude Code sessions, not scheduled tasks. Do not confuse the two.

### How scheduled tasks work
- Tasks are created and managed via Claude Dispatch (the Cowork scheduling tool)
- Each task has a `SKILL.md` prompt that executes when the task fires
- Tasks can run on a cron schedule or be triggered manually from the Schedule tab
- Tasks fire as Cowork sessions — they have access to web fetch, computer use, and sub-agents

### The filesystem access challenge
By default, Cowork task sessions run in a sandbox and cannot read or write files on your Mac unless a folder is explicitly mounted in that session. This is the core limitation for fully autonomous operation.

**The solution: absolute paths + Bash tool in code sessions**

The recommended pattern for file-heavy scheduled tasks:

1. Write the task's SKILL.md prompt to use the `start_code_task` dispatch tool to spin up a Claude Code session in the target repo directory
2. The code session runs on the host machine with full Bash access — no mount needed
3. All file reads, script runs, git commits, and API calls happen in the code session

Alternatively: write the task prompt with absolute paths and the Bash tool directly. This works when the task itself runs as a code session.

**What to avoid:** Relying on Terminal (computer use) for keyboard input. Terminal is granted at "click-only" tier in unattended sessions — no typing is possible. Use the Bash tool instead.

### Scheduling pattern for autonomous repo tasks

```
Scheduled Task (SKILL.md)
  └── fires on cron schedule
      └── starts a code session in /path/to/repo
          └── code session runs scripts via Bash tool
              └── commits, publishes, reports back
```

### Visibility
- Claude (Dispatch) queries the task registry via `list_scheduled_tasks`
- The Schedule tab in Claude Desktop shows the same registry
- If tasks disappear from the tab after an app restart, the MCP registry was cleared — recreate them via Dispatch
- The task files on disk (`~/Documents/Claude/Scheduled/`) persist across restarts but don't auto-register — registration requires the scheduling tool to have created them

---

## The Bidirectional Commerce Loop

### Business overview
Two businesses on resolved.sh trade data with each other in a closed loop. Each uses what it buys to produce better data that the other will buy again.

| Business | Subdomain | What it sells |
|----------|-----------|---------------|
| Double Agent | agentagent.resolved.sh | x402 ecosystem company index (JSONL) |
| Well Knowns | well-knowns.resolved.sh | /.well-known/ endpoint crawl across top 100k domains |

### The data dependency cycle

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Double Agent                     Well Knowns                  │
│  ──────────                       ──────────                   │
│  1. Publishes x402 company    →   2. Buys DA index             │
│     index (who's in registry)         ↓                        │
│                                   3. Filters /.well-known/     │
│                                      crawl to x402 companies   │
│                                       ↓                        │
│  5. Buys WK enriched dataset  ←   4. Publishes enriched        │
│       ↓                              "x402 infra" dataset      │
│  6. Adds infra signals to                                       │
│     company profiles                                           │
│       ↓                                                         │
│  7. Publishes enriched index  →   (cycle repeats weekly)       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

Each business adds value the other cannot produce alone:
- DA knows *who* is in the x402 ecosystem
- WK knows *what* infrastructure those companies expose
- Together they produce company profiles with both identity and infrastructure signals

### Commerce prices
- DA full index: $2.00 download / $0.10 query
- WK x402-filtered datasets: $0.50–$1.50 download
- Both businesses pay each other at published prices — no special rates
- Payments use x402 USDC on Base Mainnet, settled directly to each business's EVM wallet

### Schedule

| Time | Business | Task |
|------|----------|------|
| Sun night | Well Knowns | Crawl /.well-known/ endpoints, upload datasets |
| Mon 7am | Double Agent | Weekly enrichment — buy WK datasets, re-upload full/merged/weekly listings |
| Mon 8am | Well Knowns | Run weekly enrichment: buy DA index, produce x402-filtered datasets |
| Mon 9am | Double Agent | Publish weekly deep-research post |
| Mon 10am | Double Agent | Publish weekly blog digest |
| Daily 8am / 2pm / 8pm | Double Agent | Delta cycle — publish newly-merged PRs, conditionally re-buy WK datasets if they've bumped `updated_at` |

> Note: DA's Mon 7am enrichment currently runs before WK's Mon 8am publish, so it reads the previous week's WK datasets. To close the weekly loop within the same week, shift WK's enrichment earlier (e.g., Sun night) so DA's 7am run picks up fresh data. The 3×/day delta cycle is independent of this and reads whatever's currently published.

---

## What's Built vs What's Needed

### ✅ Built
- DA weekly research post (scheduled, Mon 9am)
- DA weekly blog digest (scheduled, Mon 10am)
- DA weekly enrichment (scheduled, Mon 7am) — `da-weekly-enrich` SKILL
- DA delta cycle (scheduled 3×/day at 8am/2pm/8pm) — `da-delta-cycle` SKILL
- DA delta detection: `scripts/github_delta.py` (diffs the full index against `data/delta_checkpoint.json`, writes `data/delta_output.jsonl`)
- DA delta publish: `scripts/publish_delta.py` (uploads `x402_new_activity_feed.jsonl` at $0.10 query / $0.50 download, emits `data_upload` Pulse event, persists file UUID to `data/delta_listing_id.txt`)
- DA → WK purchase: `pipeline/enrich_with_wellknowns.py` — now caches by listing `updated_at` (skips x402 spend when WK hasn't bumped) and opportunistically buys WK's `x402-new-activity.jsonl` if published
- WK → DA purchase: `pipeline/enrich.py` buys DA's x402 index
- WK crawl pipeline: `bash scripts/cycle.sh`

### 🔲 Still needed
- WK scheduled tasks in Claude Desktop (weekly crawl, upload, enrichment) — and shift WK enrichment earlier than Mon 7am so DA's weekly enrichment reads same-week data
- WK delta-publish counterpart: WK should publish its own high-frequency `x402-new-activity.jsonl` so DA's delta cycle has a corresponding fresh-buy on every fire
- Pulse events for WK on data publish (DA emits via the enrichment + delta-publish scripts; WK side still pending)
- WK dataset specifically sized for DA purchase: `x402-companies-full-infra-{date}.jsonl`
- Define the schema for `x402-new-activity.jsonl` so DA can fold it into enrichment instead of just caching the bytes
- Test the full loop end-to-end

---

## Adding a New Business

To add a third business to this pattern:

1. Create repo at `/Users/latentspaceman/Documents/<business-name>/`
2. Add a `CLAUDE.md` with resolved.sh identity, persona, and operating rules
3. Register on resolved.sh (free tier or paid), get API key → `.env`
4. Identify what data dependency this business has with existing businesses
5. Create scheduled tasks in Claude Desktop via Dispatch
6. Write task prompts to use absolute paths + Bash tool (see pattern above)
7. Add to the commerce loop — what does it buy? What does it sell?
8. Copy this `AUTOMATION.md` into the new repo and update the loop diagram

---

## Repos

Both businesses are public and open source — intended as reference implementations for building autonomous agent businesses on resolved.sh.

- [Double Agent](https://github.com/hichana/double-agent) — x402 ecosystem intelligence
- [Well Knowns](https://github.com/hichana/well-knowns) — /.well-known/ infrastructure data
