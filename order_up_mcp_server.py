#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "fastmcp",
#     "fire",
# ]
# ///
"""Order Up MCP Server - Tracks Chef's order completion.

This server manages the chef's order queue and completion tracking.
"""

from fastmcp import FastMCP
import fire
import json
import os
from typing import Dict, List
from datetime import datetime

mcp = FastMCP()

# Orders JSON file path
ORDERS_FILE = "chef_orders.json"

def load_orders() -> Dict:
    """Load orders from JSON file."""
    if os.path.exists(ORDERS_FILE):
        try:
            with open(ORDERS_FILE, 'r') as f:
                data = json.load(f)
                # Ensure next_order_id exists
                if "next_order_id" not in data:
                    data["next_order_id"] = 1
                print(f"[ORDER_UP] Loaded {len(data.get('orders', {}))} orders from {ORDERS_FILE}")
                return data
        except Exception as e:
            print(f"[ORDER_UP] ⚠️  Error loading {ORDERS_FILE}: {e}, using empty orders")
            return {"orders": {}, "next_order_id": 1}
    else:
        print(f"[ORDER_UP] No {ORDERS_FILE} found, starting fresh")
        return {"orders": {}, "next_order_id": 1}

def save_orders(data: Dict) -> None:
    """Save orders to JSON file."""
    try:
        with open(ORDERS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"[ORDER_UP] 💾 Saved {len(data.get('orders', {}))} orders to {ORDERS_FILE}")
    except Exception as e:
        print(f"[ORDER_UP] ⚠️  Error saving to {ORDERS_FILE}: {e}")

# Load orders from file (or start empty)
ORDERS_DATA = load_orders()

@mcp.tool
def accept_order(recipe: str, prep_time: int = 10, cook_time: int = 0) -> dict:
    """Accept a new order from a customer. Order ID is auto-generated.

    Args:
        recipe: Name of the dish/recipe being prepared
        prep_time: Preparation time in minutes (default: 10)
        cook_time: Cooking time in minutes (default: 0)

    Returns:
        Order acceptance confirmation with auto-generated order_id and estimated completion
    """
    # Get next order ID and increment
    order_id = ORDERS_DATA["next_order_id"]
    ORDERS_DATA["next_order_id"] += 1

    print(f"[ORDER_UP] 📋 Accepting order #{order_id}: {recipe}")

    total_time = prep_time + cook_time

    order_data = {
        "order_id": order_id,
        "recipe": recipe,
        "prep_time_minutes": prep_time,
        "cook_time_minutes": cook_time,
        "total_time_minutes": total_time,
        "status": "ready",  # Orders complete instantly
        "accepted_at": datetime.now().isoformat(),
        "completed_at": datetime.now().isoformat(),  # Instant completion
    }

    ORDERS_DATA["orders"][str(order_id)] = order_data
    save_orders(ORDERS_DATA)

    print(f"[ORDER_UP] ✅ Order #{order_id} ready! (simulated {total_time} min)")

    return {
        "success": True,
        "order_id": order_id,
        "recipe": recipe,
        "status": "ready",
        "message": f"Order #{order_id} for {recipe} is ready! (prep: {prep_time}min, cook: {cook_time}min)",
        "total_time_minutes": total_time
    }

@mcp.tool
def list_ready_orders() -> dict:
    """List all orders and their completion status.

    Returns:
        Dictionary with all orders grouped by status
    """
    print(f"[ORDER_UP] 📊 Listing all orders")

    orders = ORDERS_DATA.get("orders", {})

    ready_orders = []
    for order_id, order_data in orders.items():
        ready_orders.append({
            "order_id": order_id,
            "recipe": order_data.get("recipe"),
            "status": order_data.get("status"),
            "total_time_minutes": order_data.get("total_time_minutes"),
            "accepted_at": order_data.get("accepted_at"),
            "completed_at": order_data.get("completed_at"),
        })

    result = {
        "total_orders": len(orders),
        "ready_orders": ready_orders,
        "ready_count": len(ready_orders)
    }

    print(f"[ORDER_UP] Found {len(ready_orders)} ready orders")

    return result

@mcp.tool
def get_order_status(order_id: int) -> dict:
    """Get the status of a specific order.

    Args:
        order_id: The order ID to check (integer)

    Returns:
        Order status information
    """
    print(f"[ORDER_UP] 🔍 Checking status of order #{order_id}")

    orders = ORDERS_DATA.get("orders", {})
    order_id_str = str(order_id)

    if order_id_str not in orders:
        print(f"[ORDER_UP] ❌ Order #{order_id} not found")
        return {
            "success": False,
            "message": f"Order #{order_id} not found"
        }

    order = orders[order_id_str]
    print(f"[ORDER_UP] ✅ Order #{order_id} status: {order.get('status')}")

    return {
        "success": True,
        "order": order
    }

@mcp.tool
def mark_order_delivered(order_id: int) -> dict:
    """Mark an order as delivered once it has been served to the customer.

    Args:
        order_id: The order ID to mark as delivered

    Returns:
        Confirmation of delivery status update
    """
    print(f"[ORDER_UP] 📦 Marking order #{order_id} as delivered")

    orders = ORDERS_DATA.get("orders", {})
    order_id_str = str(order_id)

    if order_id_str not in orders:
        return {
            "success": False,
            "message": f"Order #{order_id} not found"
        }

    # Update status to delivered
    orders[order_id_str]["status"] = "delivered"
    orders[order_id_str]["delivered_at"] = datetime.now().isoformat()

    save_orders(ORDERS_DATA)

    print(f"[ORDER_UP] ✅ Order #{order_id} marked as delivered")

    return {
        "success": True,
        "order_id": order_id,
        "status": "delivered",
        "message": f"Order #{order_id} has been marked as delivered"
    }

def main(transport="stdio", host="0.0.0.0", port=8726):
    """Run the order_up MCP server."""
    if transport in ["sse", "streamable-http"]:
        mcp.run(transport=transport, host=host, port=port)
    elif transport == "stdio":
        mcp.run()
    else:
        raise Exception(f"Invalid parameters {transport=} {host=} {port=}")

if __name__ == "__main__":
    fire.Fire(main)
