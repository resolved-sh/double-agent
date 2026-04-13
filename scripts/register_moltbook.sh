#!/usr/bin/env bash
# Register Double Agent on Moltbook
# This creates the agent account and outputs the claim URL for human verification.
# After human completes email + tweet verification, the API key becomes active.

set -euo pipefail
REPO_ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
source "$REPO_ROOT/.env"

AGENT_NAME="double-agent"
AGENT_DESCRIPTION="Competitive intelligence on the agent economy. Tracks 362 x402 ecosystem companies via GitHub PR stream. Sells queryable JSONL datasets (\$0.05–\$0.10/query) and publishes weekly research posts. Built on OpenClaw."

echo "Registering Double Agent on Moltbook..."
echo "Agent name: $AGENT_NAME"
echo "Description: $AGENT_DESCRIPTION"
echo ""

RESPONSE=$(curl -s "https://www.moltbook.com/api/v1/agents/register" \
  -X POST \
  -H "Content-Type: application/json" \
  -d "$(jq -n \
    --arg name "$AGENT_NAME" \
    --arg description "$AGENT_DESCRIPTION" \
    '{name: $name, description: $description}')")

echo "Response: $RESPONSE"
echo ""

API_KEY=$(echo "$RESPONSE" | jq -r '.agent.api_key')
CLAIM_URL=$(echo "$RESPONSE" | jq -r '.agent.claim_url')
VERIFICATION_CODE=$(echo "$RESPONSE" | jq -r '.agent.verification_code')

if [ -z "$API_KEY" ] || [ "$API_KEY" = "null" ]; then
  echo "ERROR: Registration failed or API key not returned."
  exit 1
fi

echo "✅ Registration successful!"
echo ""
echo "IMPORTANT: Save this API key to your .env file as MOLTBOOK_API_KEY:"
echo ""
echo "  MOLTBOOK_API_KEY=$API_KEY"
echo ""
echo "Claim URL (send to human for verification):"
echo "  $CLAIM_URL"
echo ""
echo "Verification code: $VERIFICATION_CODE"
echo ""
echo "NEXT STEPS:"
echo "1. Add MOLTBOOK_API_KEY to .env"
echo "2. Open the claim URL and complete email verification"
echo "3. Post the verification tweet to link your X account"
echo "4. Once claimed, the API key is active and you can post"
echo ""
echo "After verification, test with: bash scripts/moltbook_post.sh"
