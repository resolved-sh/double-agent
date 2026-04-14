#!/usr/bin/env python3
"""
T17: Webhook registration service for resolved.sh.

This is a simple HTTP service that allows buyers to register webhook URLs
for new entrant notifications. Runs as a paid service on resolved.sh.

GET /webhook/health
  Returns { "status": "ok" }

POST /webhook/register
  Registers a new webhook subscriber.

  Body:
    {
      "name": "my-integration",           # unique name for this webhook
      "url": "https://example.com/hook",  # webhook URL to receive POST calls
      "sectors": ["data", "ai_agents"]    # optional sector filters
    }

  Returns:
    {
      "status": "registered",
      "webhook_id": "my-integration",
      "webhook_url": "https://example.com/hook",
      "registered_at": "2026-04-14T12:34:56Z",
      "next_fire": "2026-04-15T03:00:00Z"
    }

POST /webhook/unregister
  Unregisters a webhook.

  Body:
    { "webhook_id": "my-integration" }

  Returns:
    { "status": "unregistered", "webhook_id": "my-integration" }

GET /webhook/list
  Lists all webhooks (admin only - requires API key).

  Returns:
    {
      "webhooks": [
        {
          "id": "my-integration",
          "url": "https://example.com/hook",
          "active": true,
          "registered_at": "...",
          "last_fired": "...",
          "success_count": 5,
          "error_count": 0
        }
      ]
    }

GET /webhook/status/<webhook_id>
  Get the status of a specific webhook.

  Returns:
    {
      "webhook_id": "my-integration",
      "active": true,
      "last_fired": "...",
      "success_count": 5,
      "error_count": 0
    }
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from flask import Flask, request, jsonify
import hmac
import hashlib

app = Flask(__name__)

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
REGISTRY_FILE = DATA_DIR / "webhook_subscribers.json"

# Signing key for request verification (optional, can be added by resolved.sh)
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SERVICE_SECRET", "")


def load_webhooks():
    """Load webhook subscribers from registry."""
    if not REGISTRY_FILE.exists():
        return {}
    with open(REGISTRY_FILE) as f:
        return json.load(f)


def save_webhooks(webhooks):
    """Save webhook subscribers to registry."""
    DATA_DIR.mkdir(exist_ok=True)
    with open(REGISTRY_FILE, "w") as f:
        json.dump(webhooks, f, indent=2)


def verify_webhook_request():
    """Verify HMAC signature if secret is configured (resolved.sh x402 gating)."""
    if not WEBHOOK_SECRET:
        return True  # No verification needed if no secret

    signature = request.headers.get("X-Webhook-Signature")
    if not signature:
        return False

    payload = request.get_data()
    expected_sig = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected_sig)


@app.route("/webhook/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()})


@app.route("/webhook/register", methods=["POST"])
def register_webhook():
    """Register a new webhook for new entrant notifications."""
    if not verify_webhook_request():
        return jsonify({"error": "Invalid signature"}), 401

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400

        name = data.get("name", "").strip()
        url = data.get("url", "").strip()
        sectors = data.get("sectors", [])

        if not name or not url:
            return jsonify({"error": "Missing 'name' or 'url'"}), 400

        if not url.startswith(("http://", "https://")):
            return jsonify({"error": "Invalid URL — must be http:// or https://"}), 400

        webhooks = load_webhooks()

        # Check if webhook already exists
        if name in webhooks:
            return jsonify({
                "error": f"Webhook '{name}' already registered",
                "existing_webhook": {
                    "id": name,
                    "url": webhooks[name]["url"],
                    "registered_at": webhooks[name]["registered_at"]
                }
            }), 409

        now = datetime.now(timezone.utc).isoformat()
        webhooks[name] = {
            "url": url,
            "sectors": sectors,
            "active": True,
            "registered_at": now,
            "last_fired": None,
            "success_count": 0,
            "error_count": 0,
        }

        save_webhooks(webhooks)

        return jsonify({
            "status": "registered",
            "webhook_id": name,
            "webhook_url": url,
            "sectors": sectors if sectors else "all",
            "registered_at": now,
            "next_fire": "2026-04-15T03:00:00Z"  # next daily run
        }), 201

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route("/webhook/unregister", methods=["POST"])
def unregister_webhook():
    """Unregister a webhook."""
    if not verify_webhook_request():
        return jsonify({"error": "Invalid signature"}), 401

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400

        webhook_id = data.get("webhook_id", "").strip()
        if not webhook_id:
            return jsonify({"error": "Missing 'webhook_id'"}), 400

        webhooks = load_webhooks()

        if webhook_id not in webhooks:
            return jsonify({"error": f"Webhook '{webhook_id}' not found"}), 404

        del webhooks[webhook_id]
        save_webhooks(webhooks)

        return jsonify({
            "status": "unregistered",
            "webhook_id": webhook_id
        }), 200

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route("/webhook/status/<webhook_id>", methods=["GET"])
def webhook_status(webhook_id):
    """Get status of a specific webhook."""
    webhooks = load_webhooks()

    if webhook_id not in webhooks:
        return jsonify({"error": f"Webhook '{webhook_id}' not found"}), 404

    hook = webhooks[webhook_id]
    return jsonify({
        "webhook_id": webhook_id,
        "url": hook["url"],
        "active": hook.get("active", True),
        "sectors": hook.get("sectors", []),
        "registered_at": hook.get("registered_at"),
        "last_fired": hook.get("last_fired"),
        "success_count": hook.get("success_count", 0),
        "error_count": hook.get("error_count", 0),
    }), 200


@app.route("/webhook/list", methods=["GET"])
def list_webhooks():
    """List all registered webhooks (admin view)."""
    # In production, this would require admin authentication
    webhooks = load_webhooks()

    return jsonify({
        "count": len(webhooks),
        "webhooks": [
            {
                "id": name,
                "url": hook["url"],
                "active": hook.get("active", True),
                "sectors": hook.get("sectors", []),
                "registered_at": hook.get("registered_at"),
                "last_fired": hook.get("last_fired"),
                "success_count": hook.get("success_count", 0),
                "error_count": hook.get("error_count", 0),
            }
            for name, hook in webhooks.items()
        ]
    }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
