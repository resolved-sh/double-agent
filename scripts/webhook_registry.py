#!/usr/bin/env python3
"""
T17: Webhook registry for new entrant notifications.

Manages subscriber webhooks and triggers them when new companies are detected.
Stores webhooks in a simple JSON file that can be managed via CLI or committed to repo.
"""
import json
import os
import requests
import sys
from pathlib import Path
from datetime import datetime

REGISTRY_FILE = "data/webhook_subscribers.json"


def load_webhooks():
    """Load webhook subscribers from registry."""
    if not os.path.exists(REGISTRY_FILE):
        return {}
    with open(REGISTRY_FILE) as f:
        return json.load(f)


def save_webhooks(webhooks):
    """Save webhook subscribers to registry."""
    os.makedirs(os.path.dirname(REGISTRY_FILE), exist_ok=True)
    with open(REGISTRY_FILE, "w") as f:
        json.dump(webhooks, f, indent=2)


def add_webhook(name: str, url: str, active=True):
    """Register a new webhook subscriber."""
    webhooks = load_webhooks()
    if name in webhooks:
        print(f"Error: Webhook '{name}' already exists")
        return False
    webhooks[name] = {
        "url": url,
        "active": active,
        "registered_at": datetime.utcnow().isoformat(),
        "last_fired": None,
        "success_count": 0,
        "error_count": 0,
    }
    save_webhooks(webhooks)
    print(f"✓ Registered webhook '{name}' → {url}")
    return True


def remove_webhook(name: str):
    """Unregister a webhook subscriber."""
    webhooks = load_webhooks()
    if name not in webhooks:
        print(f"Error: Webhook '{name}' not found")
        return False
    del webhooks[name]
    save_webhooks(webhooks)
    print(f"✓ Removed webhook '{name}'")
    return True


def list_webhooks():
    """List all registered webhooks."""
    webhooks = load_webhooks()
    if not webhooks:
        print("No webhooks registered.")
        return
    print("Registered webhooks:")
    for name, data in webhooks.items():
        status = "active" if data.get("active") else "inactive"
        print(
            f"  {name:20s} {status:8s}  {data['url']}"
        )
        if data.get("last_fired"):
            print(f"    Last fired: {data['last_fired']} (success={data.get('success_count')}, errors={data.get('error_count')})")


def fire_webhook(name: str, payload: dict):
    """Fire a single webhook with the given payload."""
    webhooks = load_webhooks()
    if name not in webhooks:
        print(f"Error: Webhook '{name}' not found")
        return False

    webhook = webhooks[name]
    if not webhook.get("active"):
        print(f"Webhook '{name}' is inactive")
        return False

    try:
        r = requests.post(webhook["url"], json=payload, timeout=10)
        success = 200 <= r.status_code < 300

        if success:
            webhook["success_count"] = webhook.get("success_count", 0) + 1
            print(f"  ✓ {name}: {r.status_code}")
        else:
            webhook["error_count"] = webhook.get("error_count", 0) + 1
            print(f"  ✗ {name}: {r.status_code} {r.text[:100]}")

        webhook["last_fired"] = datetime.utcnow().isoformat()
        save_webhooks(webhooks)
        return success
    except Exception as e:
        webhook["error_count"] = webhook.get("error_count", 0) + 1
        webhook["last_fired"] = datetime.utcnow().isoformat()
        save_webhooks(webhooks)
        print(f"  ✗ {name}: {str(e)}")
        return False


def fire_all_webhooks(payload: dict):
    """Fire all active webhooks with the given payload."""
    webhooks = load_webhooks()
    active = {k: v for k, v in webhooks.items() if v.get("active")}

    if not active:
        print("No active webhooks")
        return

    print(f"Firing {len(active)} webhook(s)...")
    results = []
    for name in active:
        success = fire_webhook(name, payload)
        results.append(success)

    print(f"\nResults: {sum(results)}/{len(results)} succeeded")


def main():
    if len(sys.argv) < 2:
        print("Usage: webhook_registry.py <command> [args]")
        print("  add <name> <url>           - Register a webhook")
        print("  remove <name>              - Unregister a webhook")
        print("  list                       - List all webhooks")
        print("  fire <name> <json_file>    - Fire a single webhook")
        print("  fire-all <json_file>       - Fire all webhooks")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "add":
        if len(sys.argv) < 4:
            print("Usage: webhook_registry.py add <name> <url>")
            sys.exit(1)
        add_webhook(sys.argv[2], sys.argv[3])

    elif cmd == "remove":
        if len(sys.argv) < 3:
            print("Usage: webhook_registry.py remove <name>")
            sys.exit(1)
        remove_webhook(sys.argv[2])

    elif cmd == "list":
        list_webhooks()

    elif cmd == "fire":
        if len(sys.argv) < 4:
            print("Usage: webhook_registry.py fire <name> <json_file>")
            sys.exit(1)
        with open(sys.argv[3]) as f:
            payload = json.load(f)
        fire_webhook(sys.argv[2], payload)

    elif cmd == "fire-all":
        if len(sys.argv) < 3:
            print("Usage: webhook_registry.py fire-all <json_file>")
            sys.exit(1)
        with open(sys.argv[2]) as f:
            payload = json.load(f)
        fire_all_webhooks(payload)

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
