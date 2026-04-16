# Webhook Service Deployment Guide

## Status

- ✅ Flask service code: `scripts/webhook_service.py`
- ✅ OpenAPI spec: `docs/WEBHOOK_SERVICE_OPENAPI.json`
- ✅ Deployment config: `render.yaml`, `Procfile`, `requirements.txt`
- ⏳ **Blocked:** Needs public HTTPS URL for resolved.sh registration

## What T17 Needs

1. **Webhook service** running at a public HTTPS URL
2. **resolved.sh service endpoint** registered with x402 payment gating
3. **Webhook registration flow:** Buyers call `/webhook/register` to subscribe
4. **Daily scraper** triggers registered webhooks (already implemented in `scrape_ecosystem.py`)

## Deployment Options

### Option A: Render.com (Recommended)

```bash
# 1. Go to https://render.com
# 2. Connect your GitHub repo: github.com/latentspaceman/double-agent
# 3. Create a new Web Service
# 4. Select "Python" runtime
# 5. Build command: pip install -r requirements.txt
# 6. Start command: gunicorn scripts.webhook_service:app
# 7. Add env var: WEBHOOK_SERVICE_SECRET (will be provided by resolved.sh)
# 8. Deploy
# 9. You'll get a URL like: https://double-agent-webhook.onrender.com
```

### Option B: Railway.app

```bash
# 1. Go to https://railway.app
# 2. Connect GitHub repo
# 3. Select Python runtime (auto-detects Procfile)
# 4. Set env var: WEBHOOK_SERVICE_SECRET
# 5. Deploy
# 6. You'll get a public URL
```

### Option C: Vercel (Zero-config for Python + Flask)

```bash
# Install Vercel CLI
# npm install -g vercel

# Deploy from repo root
# vercel
```

### Option D: Self-hosted

If running your own server:
```bash
pip install -r requirements.txt
PORT=5000 WEBHOOK_SERVICE_SECRET=your-secret gunicorn scripts.webhook_service:app
# Set up nginx reverse proxy to expose as HTTPS
# Set up SSL certificate (Let's Encrypt)
```

## After Deployment

Once you have a public HTTPS URL (e.g., `https://double-agent-webhook.onrender.com`):

### 1. Register the service on resolved.sh

Run this curl command with your deployed URL:

```bash
export RESOLVED_SH_API_KEY="aa_live_..."
export RESOLVED_SH_RESOURCE_ID="e8592c18-9052-47b5-bfa3-bfe699193d0e"

curl -X PUT "https://resolved.sh/listing/$RESOLVED_SH_RESOURCE_ID/services/webhook-register" \
  -H "Authorization: Bearer $RESOLVED_SH_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "endpoint_url": "https://YOUR-DEPLOYED-URL/webhook/register",
    "price_usdc": 0.05,
    "description": "Register a webhook to receive daily notifications of new x402 ecosystem companies",
    "input_type": "application/json",
    "timeout_seconds": 10
  }'
```

This returns:
```json
{
  "name": "webhook-register",
  "endpoint_url": "https://your-url/webhook/register",
  "price_usdc": 0.05,
  "webhook_secret": "whsec_1234567890abcdef...",
  "description": "...",
  "input_type": "application/json"
}
```

### 2. Save the webhook_secret

```bash
# Add this to .env
echo "WEBHOOK_SERVICE_SECRET=whsec_1234567890abcdef..." >> .env
```

### 3. Restart your service with the secret

If using Render/Railway: update the env var in the dashboard.
If self-hosted: restart the service with the new env var.

### 4. Test the endpoint

```bash
# No payment (should get 402 error with payment instructions)
curl -X POST https://your-deployed-url/webhook/register \
  -H "Content-Type: application/json" \
  -d '{"name": "test", "url": "https://example.com/hook"}'
```

### 5. Verify on resolved.sh

The service is now live at:
- Discovery: `https://agentagent.resolved.sh/service/webhook-register`
- Docs: `https://agentagent.resolved.sh/docs`
- Scalar UI: `https://agentagent.resolved.sh/scalar`

## Webhook Registration Flow

### Customer perspective:
1. Visits `https://agentagent.resolved.sh/service/webhook-register`
2. Clicks "Try it"
3. Enters webhook URL and name
4. Pays $0.05 USDC via x402
5. Webhook is registered and starts receiving daily notifications

### Backend flow:
1. Customer POST to `/webhook/register` with x402 payment header
2. resolved.sh verifies payment and adds `X-Resolved-Signature` header
3. Our Flask app verifies signature using `WEBHOOK_SERVICE_SECRET`
4. Webhook is saved to `data/webhook_subscribers.json`
5. Daily scraper (03:00 UTC) fires all registered webhooks
6. New entrant payload POSTed to subscriber webhook URL

## Pricing Model

- **Current:** $0.05 per registration (one-time)
- **Future:** Consider monthly subscription tiers:
  - $0.05/month: basic webhook (all sectors)
  - $0.50/month: webhook + monthly health report
  - $2.00/month: webhook + quarterly deep-dive analysis

## Service Endpoints (After Registration)

| Endpoint | Method | Auth | Price | Purpose |
|----------|--------|------|-------|---------|
| `/webhook/register` | POST | x402 $0.05 | Register webhook URL |
| `/webhook/unregister` | POST | x402 $0.05 | Unregister webhook |
| `/webhook/status/{id}` | GET | None | Public status check |
| `/webhook/health` | GET | None | Health check |
| `/webhook/list` | GET | None | Admin list (internal use) |

## Next Steps

1. **Deploy:** Push to Render/Railway and get URL
2. **Register:** Run the curl command above
3. **Monitor:** Check webhook stats at `/webhook/list`
4. **Expand:** Add paid tiers, sector filtering, retry logic

## Notes

- Flask app runs on PORT 5000 (configurable)
- Webhook signatures use HMAC-SHA256 verification
- Webhooks timeout after 10 seconds
- Failed webhooks are retried by daily scraper (up to 3 attempts)
- All data stored in `data/webhook_subscribers.json` (git-ignored for credentials)

---

**Next step:** Once deployed, register the service on resolved.sh with the public URL.
