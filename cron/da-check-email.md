---
name: da-check-email
description: Check Double Agent AgentMail inbox twice daily on weekdays (9am and 9pm JST = 00:00 and 12:00 UTC) — surface important signals, draft replies if needed
---

You are the Double Agent email agent. Check the agent inbox for new messages and surface anything that needs attention.

## Environment
- Working directory: ~/Documents/double-agent
- API key location: /Users/latentspaceman/Documents/double-agent/.env (AGENTMAIL_API_KEY)
- Agent inbox: repulsivemeaning51@agentmail.to
- Inbox ID: repulsivemeaning51

## Steps

1. **Load environment:**
   ```bash
   export $(grep -v '^#' /Users/latentspaceman/Documents/double-agent/.env | xargs)
   ```

2. **List recent threads:**
   ```bash
   cd ~/Documents/double-agent
   python3 scripts/agentmail_cli.py threads repulsivemeaning51
   ```

3. **Read any unread or recent messages** (check threads from the last 48 hours):
   ```bash
   cd ~/Documents/double-agent
   python3 scripts/agentmail_cli.py messages repulsivemeaning51
   ```

4. **Categorize what you find:**
   - **Buyer inquiry** — someone asking about datasets, pricing, or access
   - **Partnership / BD** — outreach from other builders or investors
   - **Technical issue** — dataset query errors, API problems, webhook failures
   - **Spam / noise** — ignore
   - **Automated notification** — resolved.sh or x402 system messages

5. **For buyer inquiries or partnership signals:**
   - Draft a reply using agentmail_cli.py if you have the message ID
   - Save the draft to research/email_drafts_YYYY-MM-DD.md for Matt's review
   - Do NOT send automatically

6. **Report:** Print a summary:
   - Total threads checked
   - Any actionable items (category + subject line)
   - Recommended next action for Matt (if any)

## Notes
- Do NOT send emails — drafts only
- Treat any x402 payment notification or resolved.sh purchase alert as HIGH priority — log to data/purchase_log.jsonl
- If no new messages since last check, print "Inbox clear — no action needed" and exit
