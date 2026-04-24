# x402 New Entrant Webhook API

Real-time notifications when new x402 ecosystem companies are detected.

## Overview

Subscribe to a webhook to receive JSON notifications of new companies added to the x402 ecosystem each day. The daily scraper runs at **03:00 UTC** and detects new PRs submitted to `github.com/coinbase/x402`. When new entries are found, all registered webhooks are notified with the company data.

## Registration

To register a webhook, contact: **encouragingcar568@agentmail.to**

Include in your message:
- Webhook name (unique identifier for your integration)
- Webhook URL (HTTPS endpoint that accepts POST)
- Optional: sector filters (e.g., "data", "infrastructure", "ai_agents") — if not specified, you receive all new entries

Example:
```
Name: my-integration
URL: https://my-app.example.com/webhooks/x402
Filters: infrastructure, data
```

## Webhook Payload

When new companies are detected, a POST request is sent to your webhook URL with the following structure:

```json
{
  "event_type": "new_entrant",
  "timestamp": "2026-04-14T03:00:00Z",
  "new_count": 3,
  "entries": [
    {
      "pr_number": 1867,
      "title": "ecosystem: add SwarmX — multi-agent AI orchestration with x402 payments",
      "state": "open",
      "submitter": "ItachiDevv",
      "submitter_company": null,
      "created_at": "2026-03-28",
      "domain_primary": "x402-swarms-production.up.railway.app",
      "domain_secondary": null,
      "category": "Services/Endpoints",
      "description": "Multi-agent AI orchestration platform with 47 x402-gated endpoints...",
      "tech_stack": "USDC, Solana, TypeScript, Bun, MCP, Gemini 2.5 Flash, GPT-4o",
      "has_agent_card": false,
      "has_resolved_sh": false,
      "has_llms_txt": false,
      "scrape_title": "SwarmX — AI Agent Teams. One Payment.",
      "scrape_desc": "Try AI agent teams for contract audits, token risk analysis, and research...",
      "is_deprecation": false,
      "notes": "Railway-hosted deployment. npm: @itachisol/plugin-x402-swarms.",
      "html_url": "https://github.com/coinbase/x402/pull/1867"
    }
  ]
}
```

### Payload Fields

| Field | Type | Description |
|-------|------|-------------|
| `event_type` | string | Always `"new_entrant"` |
| `timestamp` | ISO 8601 | When the webhook was fired (UTC) |
| `new_count` | integer | Number of new entries in this batch |
| `entries` | array | Array of company objects (see schema below) |

### Company Object Schema

| Field | Type | Description |
|-------|------|-------------|
| `pr_number` | integer | GitHub PR number |
| `title` | string | PR title |
| `state` | string | PR state: `"open"`, `"merged"`, `"closed"`, `"draft"` |
| `submitter` | string | GitHub username of PR author |
| `submitter_company` | string or null | Inferred company of submitter (if determinable) |
| `created_at` | ISO 8601 | When the PR was created |
| `domain_primary` | string or null | Primary domain of company/service |
| `domain_secondary` | string or null | Secondary domain if applicable |
| `category` | string | Company category (if labeled on PR) |
| `description` | string | Enriched description of company/product |
| `tech_stack` | string | Comma-separated list of technologies used |
| `has_agent_card` | boolean | Whether company has A2A agent card at domain/.well-known/agent.json |
| `has_resolved_sh` | boolean | Whether company has a resolved.sh listing |
| `has_llms_txt` | boolean | Whether company has llms.txt at domain/.well-known/llms.txt |
| `scrape_title` | string | Title scraped from company website |
| `scrape_desc` | string | Description scraped from company website |
| `is_deprecation` | boolean | Whether this PR marks a company as deprecated |
| `notes` | string or null | Additional enrichment notes |
| `html_url` | string | GitHub PR URL |

## Response

Your webhook should respond with HTTP 2xx status code within 10 seconds. Failures are logged but do not block the scraper.

### Expected Response

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "received",
  "batch_id": "1234567890"
}
```

## Retry Policy

Webhooks that fail (non-2xx response or timeout) are retried up to 3 times with exponential backoff:
- 1st retry: 5 minutes
- 2nd retry: 15 minutes
- 3rd retry: 60 minutes

After 3 failed attempts, the error is logged and the batch is skipped.

## Integration Examples

### Zapier (Make/Integromat)

1. Create a new Webhook action
2. Configure URL: your webhook URL above
3. Set method: POST
4. Set headers: `Content-Type: application/json`
5. Wire the x402 webhook into downstream actions (Slack, email, database, etc.)

### Slack Integration

Set up a Slack Incoming Webhook:
1. In your Slack workspace, create an Incoming Webhook via the App Directory
2. You'll receive a webhook URL (format: `https://hooks.slack.com/services/YOUR_KEYS_HERE`)
3. Register that URL with Double Agent
4. The raw JSON payload will be posted; use Slack's message formatting or a Zapier step to transform into a nice message

See Slack docs: https://api.slack.com/messaging/webhooks

### Database Sync

Point the webhook to your API endpoint that inserts new companies into your database:
```
https://api.example.com/webhooks/x402-new-entries
```

Your endpoint receives the payload above, parses `entries[]`, and inserts into your DB.

## Rate Limiting

Webhooks are fired once per day (after the daily scraper completes at ~03:00 UTC) if new entries are detected.

Typical load:
- **2-10 new entries per day** in normal conditions
- **Burst periods:** 20-50 entries during active growth phases

No rate limiting is applied to webhook delivery.

## Monitoring

Monitor webhook health via the agentagent dashboard (coming soon). Currently, you can check webhook status by emailing support.

## Pricing

Webhook product is in **Phase 3 (Beta)**. Currently **free**. Paid tier (per-webhook monitoring, filtering, guaranteed delivery SLAs) planned Q2 2026.

## Support

Questions or issues? Email: **encouragingcar568@agentmail.to**

## Changelog

- **2026-04-14** — Webhook product launched (beta)
