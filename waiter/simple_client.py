#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "requests",
# ]
# ///
"""Simple HTTP client to test waiter -> chef -> supplier flow.

This bypasses ADK Runner session management and uses direct JSON-RPC calls.
"""

import requests
import json
import sys
import time

def send_order(dish_name: str) -> dict:
    """Send order to chef via direct JSON-RPC call."""

    print(f"\n[TEST] 🍽️  Ordering: {dish_name}")
    print("[TEST] Sending to chef agent via A2A...")

    # Direct JSON-RPC call to chef
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [
                    {
                        "kind": "text",
                        "text": f"I need to prepare: {dish_name}"
                    }
                ],
                "messageId": f"order-{int(time.time())}"
            }
        }
    }

    try:
        response = requests.post(
            "http://localhost:8002/",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120  # 2 minutes for full order flow
        )

        response.raise_for_status()
        result = response.json()

        if "error" in result:
            print(f"[TEST] ❌ Error from chef: {result['error']}")
            return result

        # Extract response text from task artifacts
        if "result" in result:
            response_data = result["result"]

            # Handle task response with artifacts
            if isinstance(response_data, dict) and response_data.get("kind") == "task":
                print(f"[TEST] ✅ Chef is processing (task status: {response_data.get('status', {}).get('state')})")

                artifacts = response_data.get("artifacts", [])
                if artifacts:
                    print(f"\n[CHEF RESPONSE]")
                    print("=" * 60)
                    for artifact in artifacts:
                        parts = artifact.get("parts", [])
                        for part in parts:
                            if part.get("kind") == "text":
                                print(part.get("text", ""))
                    print("=" * 60)
                else:
                    print("[TEST] ⚠️  No response text from chef yet")

            # Handle direct message response
            elif isinstance(response_data, dict) and response_data.get("kind") == "message":
                print(f"\n[CHEF RESPONSE]")
                print("=" * 60)
                for part in response_data.get("parts", []):
                    if part.get("kind") == "text":
                        print(part.get("text", ""))
                print("=" * 60)

        return result

    except requests.exceptions.Timeout:
        print("[TEST] ❌ Request timed out (chef may be waiting on supplier)")
        return {"error": "timeout"}
    except requests.exceptions.RequestException as e:
        print(f"[TEST] ❌ Connection error: {e}")
        return {"error": str(e)}

def check_chef_connection() -> bool:
    """Verify chef agent is running."""
    try:
        response = requests.get("http://localhost:8002/.well-known/agent-card.json", timeout=5)
        response.raise_for_status()
        card = response.json()
        print(f"[TEST] ✅ Connected to: {card.get('name', 'Unknown Agent')}")
        return True
    except Exception as e:
        print(f"[TEST] ❌ Chef agent not available: {e}")
        print("[TEST] Make sure chef is running: cd chef && uv run a2a_server.py")
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("🍽️  RESTAURANT ORDER TEST (Direct A2A)")
    print("=" * 80)

    # Check chef connection
    if not check_chef_connection():
        sys.exit(1)

    # Test orders
    test_orders = [
        "Greek Salad",
        "Grilled Salmon"
    ]

    for order in test_orders:
        result = send_order(order)
        time.sleep(2)  # Brief pause between orders

        if "error" in result:
            print(f"\n[TEST] ⚠️  Order had errors, but continuing...\n")

    print("\n" + "=" * 80)
    print("✅ Test complete!")
    print("=" * 80)
