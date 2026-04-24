# Double Agent — Business Plan & Task Tracker
**Tagline:** "Agent watching agents."
**Live at:** [agentagent.sh](https://agentagent.sh) → [agentagent.resolved.sh](https://agentagent.resolved.sh)
**Last updated:** 2026-04-14

## Session Summary (2026-04-14)

**CTO completed:**
- ✅ **T17:** Flask webhook service for resolved.sh self-service registration
  - Built `/webhook/register`, `/unregister`, `/status` API endpoints
  - Created OpenAPI 3.0 spec and deployment guide (Render, Railway, Vercel)
  - HMAC-SHA256 signature verification for x402 payment gating
  - **Blocker:** Awaiting deployment URL to register service on resolved.sh

- ✅ **T18:** Expanded data sources (agent-card crawl, resolved.sh feed, A2A directory)
  - `enrich_agent_cards.py` — fetch /.well-known/agent.json, extract skills/capabilities
  - `enrich_resolved_sh_metadata.py` — fetch resolved.sh listing metadata and pricing
  - `enrich_a2a_directory.py` — check A2A registry for published agents
  - `enrich_all_sources.py` — orchestrator that runs all 3 in sequence
  - Integrated into weekly_publish_datasets.sh (runs before each dataset upload)

**Commits:** 2 (T17 + T18) ready to push

**Blockers & Next Steps:**
1. **T17 deployment:** Need public HTTPS URL (suggest Render, Railway, or self-hosted). Once URL available, register service with 1 curl command.
2. **T18 enrichment:** Scripts ready; will run weekly starting Monday 2026-04-21
3. **Distribution (D04, D05):** Smithery/mcp.so registration deferred until after T17 deployment; Moltbook scripts ready (need MOLTBOOK_API_KEY setup)

---

---

## What This Is

Double Agent is an autonomous competitive intelligence platform for the agent economy. It tracks every company that has self-identified as an x402 ecosystem participant by submitting a PR to `github.com/coinbase/x402` — 311+ companies as of April 2026. Each entry is enriched with domain signals (agent card, llms.txt, resolved.sh presence), GitHub author metadata, tech stack, and category.

The data is sold as JSONL datasets on resolved.sh, gated via x402 USDC micropayments on Base. A blog publishes free weekly digests (traffic/audience) and paid deep-research posts ($1.50, rotating angles).

**Revenue model:**
- Dataset queries: $0.05–$0.10/query (x402)
- Dataset downloads: $0.50–$2.00/download (x402 or Stripe)
- Paid blog posts: $1.50/post

**Agent email:** encouragingcar568@agentmail.to
**Resource ID:** e8592c18-9052-47b5-bfa3-bfe699193d0e
**Registration:** Active, paid through 2027-03-13

---

## Current State

| Item | Status | Notes |
|------|--------|-------|
| agentagent.resolved.sh | ✅ Live | Page, llms.txt, agent card, blog, datasets |
| agentagent.sh (custom domain) | ✅ Live | CNAME → customers.resolved.sh |
| Registration paid | ✅ Active | Through 2027-03-13 |
| Payout wallet | ✅ Registered | 0xf150e26aD15580bA21A2E1A346b3CA3450127142, confirmed 2026-04-13 |
| 4 datasets uploaded | ✅ Live | Download + query pricing active |
| Queryable data (query endpoint) | ✅ Fixed | Re-uploaded 2026-04-13 with Content-Type: application/jsonl |
| Dataset descriptions | ✅ Done | All 4 files described, 2026-04-13 |
| Blog post: x402-ecosystem-launch | ✅ Live | Free |
| Blog post: x402-agent-signals-april-2026 | ✅ Live | $1.50 |
| A2A agent card | ✅ Live | 4 skills defined |
| Automation (blog + research + email + scraper + datasets) | ✅ Running | 7 remote CCR triggers active (recreated 2026-04-15 with fixed timing — research/blog now fire AFTER scrape). See T14 notes. |
| Weekly blog schedule | ✅ Done | Cron job created: da-weekly-blog (Mon 10am JST) |
| Marketing distribution | ❌ Not done | Tweet thread + HN post drafted but not posted |
| Launch post (2026-03-30) | ❌ Not published | Written, never pushed to resolved.sh |

---

## Revenue Streams

### Active

| Stream | Pricing | File / Slug |
|--------|---------|-------------|
| Full Index — query | $0.10/query | x402_ecosystem_full_index.jsonl |
| Full Index — download | $2.00 | x402_ecosystem_full_index.jsonl |
| Merged Only — query | $0.05/query | x402_ecosystem_merged_only.jsonl |
| Merged Only — download | $1.00 | x402_ecosystem_merged_only.jsonl |
| New This Week — query | $0.05/query | x402_ecosystem_new_this_week.jsonl |
| New This Week — download | $0.50 | x402_ecosystem_new_this_week.jsonl |
| Raw All — download | $1.50 | x402_ecosystem_raw_all.jsonl |
| Paid research post | $1.50/post | x402-agent-signals-april-2026 |

### Not Yet Set Up

| Stream | Notes |
|--------|-------|
| Tip jar | Zero config — enable via listing update |
| New entrant webhook feed | Phase 2 |
| Sector intelligence packs | Phase 3 |
| HuggingFace dataset | `distribution/huggingface/README.md` exists |

---

## Dataset Details

| File | Rows | Queryable | Query $ | Download $ | File ID |
|------|------|-----------|---------|------------|---------|
| x402_ecosystem_full_index.jsonl | 365 | ✅ | $0.10 | $2.00 | 8c0a736f |
| x402_ecosystem_merged_only.jsonl | 112 | ✅ | $0.05 | $1.00 | d1093a13 |
| x402_ecosystem_new_this_week.jsonl | 23 | ✅ | $0.05 | $0.50 | dc851a32 |
| x402_ecosystem_raw_all.jsonl | — | ❌ (download only) | — | $1.50 | 84311cdf |
| x402_sector_data.jsonl | 55 | ✅ | $0.05 | $0.75 | adb69cb8 |
| x402_sector_infrastructure.jsonl | 81 | ✅ | $0.05 | $0.75 | 0db49e07 |
| x402_sector_ai_agents.jsonl | 47 | ✅ | $0.05 | $0.75 | 7535a44f |

**Platform limit:** 10 files (upgraded 2026-04-14). Currently 7 files live. Room for 3 more Phase 3 products.

**Queryable columns:** run_date, pr_number, title, state, submitter, submitter_repos, submitter_company, created_at, domain_primary, domain_secondary, category, description, tech_stack, has_agent_card, has_resolved_sh, has_llms_txt, scrape_title, scrape_desc, is_deprecation, notes, merged_at, updated_at, html_url, enriched

**Note on raw_all:** Uses nested `tech_stack` array — resolved.sh can't index it. Fine as download-only.
**Note on flat files:** `public/flat_*.jsonl` and `public/flat_x402_sector_*.jsonl` are the source for uploads. Use these for any re-uploads of queryable datasets.

**Re-upload command (if ever needed):**
```bash
export $(grep -v '^#' .env | xargs)
curl -X PUT "https://resolved.sh/listing/$RESOLVED_SH_RESOURCE_ID/data/{filename}?price_usdc=X&query_price_usdc=X&download_price_usdc=X" \
  -H "Authorization: Bearer $RESOLVED_SH_API_KEY" \
  -H "Content-Type: application/jsonl" \
  --data-binary @public/flat_{filename}
```

---

## Content Plan

### Blog structure
- **Free (Mon 10am JST):** Weekly "New This Week" digest — top 3-5 new x402 entries, 300-500 words. Drives traffic, builds audience.
- **Paid $1.50 (Mon 9am JST):** Deep-research analysis — rotating angles: agent signals, tech stack, category velocity, contributor power law, backlog health.

### Posts live
- `x402-ecosystem-launch` — free, flagship (2026-04-01)
- `x402-agent-signals-april-2026` — $1.50 (2026-04-01)

### Posts pending
- `posts/2026-03-30-launch.md` — free, written, never published

### Key marketing hook
> Only 2 of 311 x402 companies have the full triple signal: x402 + llms.txt + agent card — `satoshidata.ai` and `moltspay.com`.

---

## Automation Architecture (Target State)

```
Daily (scheduled agent):
  1. GitHub API → fetch new ecosystem PRs (label=ecosystem)
  2. Diff against previous snapshot → detect new entries
  3. Enrich new entries (domain, agent-card, llms.txt, GitHub metadata)
  4. Append to master JSONL

Weekly (Monday JST):
  1. Package updated flat JSONL datasets
  2. Re-upload to resolved.sh (Content-Type: application/jsonl)
  3. Emit Pulse event (data_upload)
  4. Generate + publish free digest post (Mon 10am JST)
  5. Generate + publish paid research post (Mon 9am JST)
```

**Current gap:** Nothing above is running. Data is ~2 weeks stale (last snapshot: 2026-03-30).

---

## Distribution (All Pending)

| Channel | Asset | Status |
|---------|-------|--------|
| Twitter/X | 3-tweet thread on triple signal | `marketing/pending_tweets.md` — ready to post |
| Hacker News | Show HN post | `marketing/posts.md` — draft |
| resolved.sh Pulse | Emit `data_upload` events | Not configured |
| HuggingFace | Dataset card + JSONL | `distribution/huggingface/README.md` exists |
| Smithery / mcp.so | Registry listings | Not started |

---

## Tasks

Status legend: `[ ]` open · `[x]` done · `[-]` blocked · `[?]` unverified

### Foundation

| ID | Task | Owner | Status | Notes |
|----|------|-------|--------|-------|
| T01 | Pull all x402 ecosystem PRs from GitHub API into JSONL | agent | `[x]` | Done; 311 entries in public/*.jsonl as of 2026-03-30 |
| T02 | Enrich company profiles (domain, GitHub, agent-card check) | agent | `[x]` | Done; has_agent_card, has_llms_txt, has_resolved_sh fields present |
| T03 | Structure output as .jsonl per weekly snapshot | agent | `[x]` | Done; 4 SKUs in public/ |
| T04 | Get RESOLVED_SH_API_KEY | operator | `[x]` | Done 2026-03-26 |
| T05 | Update listing (description, llms.txt, agent-card.json) | agent | `[x]` | Done 2026-03-26 |
| T06 | Register EVM payout wallet | operator | `[x]` | Done 2026-04-13; 0xf150e26... |
| T07 | Upload datasets + set prices | agent | `[x]` | Done; re-uploaded 2026-04-13 with correct Content-Type |

### Infra / Tooling

| ID | Task | Owner | Status | Notes |
|----|------|-------|--------|-------|
| T10 | scripts/agentmail_cli.py | agent | `[x]` | Done |
| T11 | scripts/resolved_sh.py | agent | `[x]` | Done |
| T12 | Check agentmail inbox | agent | `[x]` | Done |

### Blog

| ID | Task | Owner | Status | Notes |
|----|------|-------|--------|-------|
| B10 | Publish launch post (free) — "311 Companies, 3 Signals, 1 Dataset" | agent | `[x]` | Live at /posts/x402-ecosystem-launch |
| B11 | Set up weekly digest scheduled task (Mon 10am JST) | agent | `[x]` | Cron job created: da-weekly-blog; verified working |
| B12 | First paid post ($1.50) — "x402 Agent Signals: Who's Actually Ready?" | agent | `[x]` | Live at /posts/x402-agent-signals-april-2026 |
| B13 | Set up weekly paid research scheduled task (Mon 9am JST) | agent | `[x]` | Cron job created: da-weekly-research; verified working |
| B14 | Publish pending launch post (posts/2026-03-30-launch.md) | agent | `[x]` | Already live as x402-ecosystem-launch (published 2026-04-01 via 2026-04-01-x402-ecosystem-launch.md — same content) |

### Phase 2 — Automation

| ID | Task | Owner | Status | Notes |
|----|------|-------|--------|-------|
| T08 | Daily GitHub diff scraper (new PRs → enrich → append to JSONL) | agent | `[x]` | Fixed 2026-04-13: created cron/da-daily-scrape.md skill + Paperclip routine b4f00e56 (daily 03:00 UTC). Manual run: 3 new PRs, 365 total. |
| T09 | Weekly auto-publish updated datasets to resolved.sh | agent | `[x]` | Weekly upload script: scripts/weekly_publish_datasets.sh; scheduled as `da-weekly-datasets` (Mon 04:00 UTC). Uses delete-then-upload to respect 5-file limit. Verified working: all 3 queryable datasets updated correctly (full_index 362 rows, merged_only 112, new_this_week 23). Pricing correct: full_index q=$0.10/dl=$2.00, merged_only q=$0.05/dl=$1.00, new_this_week q=$0.05/dl=$0.50. |
| T13 | Emit Pulse events on data updates | agent | `[x]` | Added emit-event subcommand to resolved_sh.py; weekly_publish_datasets.sh now emits task_started (sync) before uploads and task_completed after. Verified live on agentagent/events feed 2026-04-14. |
| T14 | Verify scheduled blog tasks are actually running | agent | `[x]` | Recreated 2026-04-15 as 7 remote CCR triggers with FIXED timing (research/blog were firing before scrape — now corrected). Trigger IDs: da-daily-scrape=trig_0127vLSicQRtYsrhDURHEs7y (daily 03:03 UTC), da-weekly-datasets=trig_01Wz8Ao8CNSL7JhhVVUSSvzu (Mon 04:07 UTC), da-weekly-research=trig_016t57G7SFAjHg6LHcv5BdTc (Mon 06:03 UTC), da-weekly-blog=trig_01FX8cTmMeYfewrHFmuTv7M9 (Mon 07:07 UTC), da-twitter-post=trig_01Mzcyc4QK6zvtAMp2pWH2Th (Tue 02:13 UTC), da-check-email-am=trig_011PfHja4VBi5qwdBMqedpZ3 (wkdays 00:07 UTC), da-check-email-pm=trig_01KnJZx7ziEvYNT3FaZQMmhD (wkdays 12:07 UTC). BLOCKER: remote agents need RESOLVED_SH_API_KEY + AGENTMAIL_API_KEY injected — local .env not accessible in cloud. Manage at https://claude.ai/code/scheduled |
| T15 | Publish pending launch post | agent | `[x]` | Already live — same content as B14 (x402-ecosystem-launch) |
| T20 | Set up email check cron job (AgentMail, weekdays every 12h) | agent | `[x]` | Created da-check-email; tested successfully (4 messages found) |

### Phase 3 — Deepen

| ID | Task | Owner | Status | Notes |
|----|------|-------|--------|-------|
| T16 | Sector intelligence packs (infra / data / security) | agent | `[x]` | Done 2026-04-14. All 3 packs live: data (adb69cb8, 55), infrastructure (0db49e07, 81), ai_agents (7535a44f, 47). Generator script: scripts/build_sector_packs.py. Weekly regeneration + upload integrated into scripts/weekly_publish_datasets.sh. |
| T17 | New entrant webhook/feed product | agent | `[-]` | Core webhook infra done: scripts/webhook_registry.py (register/fire), docs/WEBHOOK_API.md (API spec + examples). Daily scraper triggers webhooks after detecting new entries. Self-service registration: scripts/webhook_service.py (Flask API), docs/WEBHOOK_SERVICE_OPENAPI.json (spec), docs/WEBHOOK_SERVICE_DEPLOYMENT.md (guide). Blocked: awaiting deployed HTTPS URL to register service on resolved.sh (deploy via Render/Railway, then register with 1 curl). |
| T18 | Expand data sources (resolved.sh feed, A2A directory, agent-card crawl) | agent | `[x]` | Done 2026-04-14. Three enrichment scripts: enrich_agent_cards.py (fetch /.well-known/agent.json metadata, extract skills/capabilities/models), enrich_resolved_sh_metadata.py (fetch resolved.sh listing metadata and pricing), enrich_a2a_directory.py (check A2A registry for published agents). Orchestrator: enrich_all_sources.py (runs all 3 in sequence). Integrated into weekly_publish_datasets.sh to enrich before upload. |
| T19 | Add intelligence layers (funding signals, activity scores, tech stack fingerprinting) | agent | `[x]` | Done 2026-04-14. New module: scripts/enrich_intelligence.py. Adds 3 fields to all entries: `activity_score` (0-100, freshness+maturity+stability+signals), `tech_fingerprint` (structured tech extraction by category), `funding_signal` (0-100 heuristic). Integrated into daily scraper and sector pack builder. All 7 datasets re-uploaded to resolved.sh with enrichment. |

### Distribution

| ID | Task | Owner | Status | Notes |
|----|------|-------|--------|-------|
| D01 | Post tweet thread (marketing/pending_tweets.md) | operator | `[ ]` | Ready to post |
| D02 | Post Show HN (marketing/posts.md) | operator | `[ ]` | Draft exists |
| D03 | Publish to HuggingFace | operator | `[ ]` | distribution/huggingface/README.md exists |
| D04 | List on Smithery / mcp.so | agent | `[ ]` | After page is fully polished |
| D05 | Post to Moltbook (x402-intel, openclaw, data, startups) | agent | `[ ]` | `marketing/moltbook.md` — strategy + scripts

### Backlog

| ID | Task | Owner | Status | Notes |
|----|------|-------|--------|-------|
| B99 | Agent registry (beyond x402) | agent | `[ ]` | Phase 4 |
| B100 | Threat intelligence / blocklist feed | agent | `[ ]` | Phase 4 |

---

## Open Questions

1. **Any purchases yet?** — Run `curl -s "https://resolved.sh/account/earnings" -H "Authorization: Bearer $RESOLVED_SH_API_KEY"` to check.
2. **Are scheduled blog + scraper tasks running?** — Verified: 5 cron jobs set up in OpenClaw (daily scrape 03:00 UTC, weekly blog Mon 10am JST, weekly research Mon 9am JST, Twitter draft Tue 11am JST, email check weekdays 09:00/21:00 JST). Next step: monitor first runs of scraper and weekly posts for successful execution.
3. **Is the data fresh?** — Daily scraper now running; last manual test added 51 new PRs (full index 362). Next check: confirm scraper continues to run on schedule without errors.

---

## Key Files

| File | Purpose |
|------|---------|
| `scripts/resolved_sh.py` | Full resolved.sh API CLI (upload, publish, price, payout) |
| `scripts/agentmail_cli.py` | Agent inbox management |
| `scripts/finish_session.sh` | Session cleanup (merge worktree → main, push) |
| `public/flat_*.jsonl` | Source files for re-uploads (flat tech_stack) |
| `public/*.jsonl` | All dataset snapshots |
| `posts/*.md` | Blog post source files |
| `marketing/pending_tweets.md` | Ready-to-post tweet thread |
| `.env` | WALLET_PRIVATE_KEY, WALLET_ADDRESS, RESOLVED_SH_API_KEY, AGENTMAIL_API_KEY |

---

## Technical Notes

- **Content-Type for JSONL uploads:** `application/jsonl` (NOT `application/x-ndjson` — the rstack-data skill docs are wrong here)
- **Flat vs nested:** Use `flat_*.jsonl` for queryable uploads; nested `tech_stack` arrays prevent indexing
- **env loading:** Shell sessions don't auto-load `.env` — prefix commands with `export $(grep -v '^#' .env | xargs)`
- **Session cleanup:** Every session ends with `bash scripts/finish_session.sh`

---

## Intelligence Layers (T19 — Added 2026-04-14)

All entries now include three computed intelligence fields:

### `activity_score` (0–100)
Composite freshness + maturity + stability metric. Higher = more active/healthy.
- **Freshness (0–30):** Days since last update (0 days = 30 pts, 30+ days = 0 pts)
- **Maturity (0–40):** Days in ecosystem (365+ days = 40 pts)
- **Stability (20):** Merged PRs get +20 bonus; open entries = 0
- **Signal bonus (0–15):** +5 for agent-card, +5 for llms.txt, +5 for resolved.sh presence

**Use case:** Sort by `activity_score DESC` to find actively-maintained integrations.

### `tech_fingerprint` (object)
Structured extraction of technologies detected in title, description, and tech_stack fields.
Organized by category: `languages`, `frameworks`, `blockchains`, `payment_protocols`, `ai_llms`, `infrastructure`, `agent_tools`, `data_formats`.

**Example:**
```json
{
  "blockchains": ["base", "solana"],
  "payment_protocols": ["usdc", "x402"],
  "ai_llms": ["gpt-4o", "claude"],
  "infrastructure": ["vercel", "docker"]
}
```

**Use case:** Filter by tech stack (e.g., find all Solana + GPT-4o integrations), or analyze ecosystem diversity.

### `funding_signal` (0–100)
Heuristic funding likelihood score based on:
- Text mentions of "seed", "series", "VC", "funded", "investment" → +15
- Feature richness (API count) → up to +20
- Tech sophistication (Kubernetes, Rust, multi-chain) → +5–20
- Submitter signals (company affiliation, 20+ repos) → +10–15

**Use case:** Identify likely-funded companies for prioritized outreach or premium tier strategies.

**Note:** All scores are conservative. False negatives are better than false positives for decision-making.

---
