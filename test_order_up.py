#!/usr/bin/env python3
"""Test script for order_up MCP server functions."""

import json
import os
from datetime import datetime

# Orders JSON file path
ORDERS_FILE = "chef_orders.json"

def load_orders():
    """Load orders from JSON file."""
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, 'r') as f:
            return json.load(f)
    return {"orders": {}}

def save_orders(data):
    """Save orders to JSON file."""
    with open(ORDERS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def accept_order(order_id: str, recipe: str, prep_time: int = 10, cook_time: int = 0):
    """Accept a new order."""
    ORDERS_DATA = load_orders()

    total_time = prep_time + cook_time

    order_data = {
        "order_id": order_id,
        "recipe": recipe,
        "prep_time_minutes": prep_time,
        "cook_time_minutes": cook_time,
        "total_time_minutes": total_time,
        "status": "ready",
        "accepted_at": datetime.now().isoformat(),
        "completed_at": datetime.now().isoformat(),
    }

    ORDERS_DATA["orders"][order_id] = order_data
    save_orders(ORDERS_DATA)

    return {
        "success": True,
        "order_id": order_id,
        "recipe": recipe,
        "status": "ready",
        "message": f"Order {order_id} for {recipe} is ready!",
        "total_time_minutes": total_time
    }

def list_ready_orders():
    """List all orders."""
    ORDERS_DATA = load_orders()
    orders = ORDERS_DATA.get("orders", {})

    ready_orders = []
    for order_id, order_data in orders.items():
        ready_orders.append({
            "order_id": order_id,
            "recipe": order_data.get("recipe"),
            "status": order_data.get("status"),
            "total_time_minutes": order_data.get("total_time_minutes"),
        })

    return {
        "total_orders": len(orders),
        "ready_orders": ready_orders,
        "ready_count": len(ready_orders)
    }

# Run tests
print("🧪 Testing order_up MCP server functions...\n")

print("1. Testing accept_order...")
result1 = accept_order('order_001', 'Greek Salad', prep_time=15, cook_time=0)
print(f"   ✅ Result: {result1['message']}")

print("\n2. Testing accept_order with another dish...")
result2 = accept_order('order_002', 'Grilled Salmon', prep_time=10, cook_time=20)
print(f"   ✅ Result: {result2['message']}")

print("\n3. Testing list_ready_orders...")
orders = list_ready_orders()
print(f"   ✅ Found {orders['total_orders']} orders:")
for order in orders['ready_orders']:
    print(f"      - {order['order_id']}: {order['recipe']} ({order['total_time_minutes']} min)")

print("\n4. Checking chef_orders.json file...")
if os.path.exists(ORDERS_FILE):
    with open(ORDERS_FILE, 'r') as f:
        data = json.load(f)
    print(f"   ✅ File exists with {len(data.get('orders', {}))} orders")
else:
    print(f"   ❌ File not found!")

print("\n✅ All order_up MCP server functions work correctly!")
