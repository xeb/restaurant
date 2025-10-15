#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "fastmcp",
#     "fire",
# ]
# ///
"""Orders MCP Server - Manages customer orders for the restaurant.

This server tracks customer orders, their status, and details.
The waiter agent uses this to manage the order lifecycle.
"""

import json
import os
from typing import Dict, Any, List
from datetime import datetime
from fastmcp import FastMCP
import fire

mcp = FastMCP()

ORDERS_FILE = 'orders.json'

def load_orders() -> Dict[str, Any]:
    if not os.path.exists(ORDERS_FILE):
        print(f"[ORDERS] No existing orders file, starting fresh")
        return {"next_order_id": 1, "orders": {}}
    with open(ORDERS_FILE, 'r') as f:
        try:
            data = json.load(f)
            print(f"[ORDERS] Loaded {len(data.get('orders', {}))} orders from {ORDERS_FILE}")
            return data
        except json.JSONDecodeError:
            print(f"[ORDERS] Error loading orders file, starting fresh")
            return {"next_order_id": 1, "orders": {}}


def save_orders(orders: Dict[str, Any]):
    with open(ORDERS_FILE, 'w') as f:
        json.dump(orders, f, indent=4)

@mcp.tool
def save_order(name: str, order_details: str, estimated_wait_time: str) -> int:
    """Saves a customer's order and returns the new order_id.

    Args:
        name: Customer name
        order_details: Details of what was ordered
        estimated_wait_time: How long the order will take

    Returns:
        The auto-incremented order_id
    """
    orders_data = load_orders()
    order_id = orders_data['next_order_id']
    orders_data['next_order_id'] += 1

    new_order = {
        "order_id": order_id,
        "name": name,
        "order_details": order_details,
        "estimated_wait_time": estimated_wait_time,
        "status": "RECEIVED",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    orders_data['orders'][str(order_id)] = new_order
    save_orders(orders_data)

    print(f"[ORDERS] ✅ Created order #{order_id} for {name} - Status: RECEIVED")
    print(f"[ORDERS]    Details: {order_details}")
    print(f"[ORDERS]    Est. wait: {estimated_wait_time}")

    return order_id

@mcp.tool
def list_orders() -> List[Dict[str, Any]]:
    """Returns a list of all outstanding (not SERVED) orders.

    Returns:
        List of orders that are RECEIVED, COOKING, or READY
    """
    orders_data = load_orders()
    outstanding_orders = [
        order for order in orders_data['orders'].values()
        if order['status'] != 'SERVED'
    ]

    print(f"[ORDERS] Found {len(outstanding_orders)} outstanding orders")
    for order in outstanding_orders:
        print(f"[ORDERS]   #{order['order_id']}: {order['name']} - {order['status']}")

    return outstanding_orders

@mcp.tool
def set_order_status(order_id: int, status: str) -> str:
    """Sets the status for a given order_id. Valid statuses are RECEIVED, COOKING, READY, SERVED.

    Args:
        order_id: The ID of the order to update
        status: New status (RECEIVED, COOKING, READY, SERVED)

    Returns:
        Success message or error message
    """
    orders_data = load_orders()
    order = orders_data['orders'].get(str(order_id))

    if not order:
        print(f"[ORDERS] ❌ Order #{order_id} not found")
        return f"Error: Order with ID {order_id} not found."

    valid_statuses = ["RECEIVED", "COOKING", "READY", "SERVED"]
    if status not in valid_statuses:
        print(f"[ORDERS] ❌ Invalid status '{status}'")
        return f"Error: Invalid status '{status}'. Must be one of {valid_statuses}."

    old_status = order['status']
    order['status'] = status
    order['updated_at'] = datetime.now().isoformat()
    save_orders(orders_data)

    print(f"[ORDERS] ✅ Order #{order_id} ({order['name']}) status: {old_status} → {status}")

    return f"Order {order_id} status updated to {status}"

@mcp.tool
def get_order_status(order_id: int) -> str:
    """Gets the status for a given order_id.

    Args:
        order_id: The ID of the order to check

    Returns:
        The order status or an error message
    """
    orders_data = load_orders()
    order = orders_data['orders'].get(str(order_id))

    if not order:
        print(f"[ORDERS] ❌ Order #{order_id} not found")
        return f"Error: Order with ID {order_id} not found."

    print(f"[ORDERS] Order #{order_id} ({order['name']}): {order['status']}")
    return order['status']

def main(transport="stdio", host="0.0.0.0", port=8004):
    if transport in ["sse", "streamable-http"]:
        mcp.run(transport=transport, host=host, port=port)
    elif transport == "stdio":
        mcp.run()
    else:
        raise Exception(f"Invalid parameters {transport=} {host=} {port=}")


if __name__ == "__main__":
    fire.Fire(main)