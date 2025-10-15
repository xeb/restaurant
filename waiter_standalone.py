#!/usr/bin/env python3
"""Standalone waiter agent for webapp - uses chef via A2A and orders MCP."""

import io
import sys
from contextlib import redirect_stdout, redirect_stderr
from google.adk import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.tools.agent_tool import AgentTool

try:
    from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset as McpToolset
    from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams, StdioServerParameters
except ImportError:
    print("[WAITER STANDALONE] Error: Could not import MCP tools", file=sys.stderr)
    McpToolset = None

print("[WAITER STANDALONE] Connecting to chef agent via A2A...")

tools = []

try:
    chef_agent = RemoteA2aAgent(
        name="chef_agent",
        agent_card="http://localhost:8002/.well-known/agent-card.json"
    )

    chef_tool = AgentTool(agent=chef_agent)
    tools.append(chef_tool)

    print("[WAITER STANDALONE] ✅ Connected to chef agent (port 8002)")

except Exception as e:
    print(f"[WAITER STANDALONE] ⚠️  Could not connect to chef agent: {e}")

# Add orders MCP tools
if McpToolset:
    import os

    # Try to find orders_mcp_server.py in multiple locations
    orders_possible_paths = [
        "orders_mcp_server.py",           # When running from root (webapp)
        "../orders_mcp_server.py",        # When running from waiter/ directory
    ]

    orders_path = None
    for path in orders_possible_paths:
        if os.path.exists(path):
            # Convert to absolute path so it works regardless of current directory

            orders_path = os.path.abspath(path)
            break

    if orders_path is None:
        print(f"[WAITER STANDALONE] ⚠️  Could not find orders_mcp_server.py in any of: {orders_possible_paths}")
    else:
        try:
            f_out = io.StringIO()
            f_err = io.StringIO()

            with redirect_stdout(f_out), redirect_stderr(f_err):
                orders_connection = StdioConnectionParams(
                    server_params=StdioServerParameters(
                        command="uv",
                        args=["run", orders_path]
                    )
                )

                orders_toolset = McpToolset(
                    connection_params=orders_connection
                )

                tools.append(orders_toolset)
                print(f"[WAITER STANDALONE] ✅ Connected to orders MCP server (using {orders_path})")

        except Exception as e:
            print(f"[WAITER STANDALONE] ⚠️  Could not connect to orders MCP: {e}")

# Create the waiter agent
root_agent = Agent(
    name="waiter_agent",
    model="gemini-2.5-flash",
    description="Waiter agent that takes customer orders and coordinates with the chef",
    instruction="""You are a friendly waiter in a restaurant. You MUST use the available tools to manage orders.

CRITICAL: ALWAYS ask for the customer's name BEFORE taking their order. Do not take orders without a name.

AVAILABLE TOOLS:
- save_order(name, order_details, estimated_wait_time) - Save a new order, returns order_id
- set_order_status(order_id, status) - Update order status (RECEIVED/COOKING/READY/SERVED)
- get_order_status(order_id) - Check specific order status
- list_orders() - List all outstanding orders
- chef_agent(message) - Send order to the chef

WORKFLOW FOR TAKING AN ORDER:
1. First interaction: ALWAYS ask "Welcome! May I have your name please?"
2. Wait for customer to provide their name
3. Ask: "What would you like to order, [name]?"
4. Customer orders (e.g., "Greek Salad")
5. Send order to chef: chef_agent("Order: Greek Salad for [name]")
6. Chef will respond with time estimate (e.g., "ready in 15 minutes")
7. Save the order: save_order(name="[name]", order_details="Greek Salad", estimated_wait_time="15 minutes")
   - This returns an order_id (keep track of it internally)
8. Update status to COOKING: set_order_status(order_id, "COOKING")
9. Update status to READY: set_order_status(order_id, "READY")
10. Tell customer: "Excellent choice! Your Greek Salad will be ready in 15 minutes."
    - ONLY mention the order ID if the customer specifically asks for it

IF CUSTOMER ASKS "WHERE IS MY FOOD?" or "WHAT'S MY ORDER STATUS?":
1. Use list_orders() to find their order by name
2. Check the status
3. If READY: Say "Your [dish] is ready!" and call set_order_status(order_id, "SERVED")
4. If COOKING: Say "Your order is still being prepared by the chef. It should be ready soon."
5. If RECEIVED: Say "Your order has been received and will be sent to the kitchen shortly."

IF CUSTOMER ASKS "WHAT IS MY ORDER ID?":
1. Use list_orders() to find their order by name
2. Tell them their order_id: "Your order ID is #[order_id]"

IF CUSTOMER ASKS "WHAT ARE THE OUTSTANDING ORDERS?":
1. Use list_orders() to get all non-SERVED orders
2. List them: "We have X outstanding orders: [list details]"

EXAMPLE CONVERSATION:
Customer: "Hi"
You: "Welcome to our restaurant! May I have your name please?"

Customer: "Alice"
You: "Nice to meet you, Alice! What would you like to order today?"

Customer: "Greek Salad"
You: [Use chef_agent("Order: Greek Salad for Alice")]
     [Chef responds: "Greek Salad will be ready in 15 minutes (prep: 15min, cook: 0min)"]
     [Use save_order(name="Alice", order_details="Greek Salad", estimated_wait_time="15 minutes") → returns order_id 1]
     [Use set_order_status(1, "COOKING")]
     [Use set_order_status(1, "READY")]
     "Excellent choice! Your Greek Salad will be ready in 15 minutes."

Customer: "Where is my food?"
You: [Use list_orders() → finds order #1 for Alice with status READY]
     [Use set_order_status(1, "SERVED")]
     "Your Greek Salad is ready! Here you go, Alice. Enjoy your meal!"

Customer: "What is my order ID?"
You: [Use list_orders() → finds order #1 for Alice]
     "Your order ID is #1."

REMEMBER:
- ALWAYS get the customer's name FIRST before taking any order
- ALWAYS use the tools to save and track orders
- Do NOT mention order IDs unless the customer specifically asks
- Be friendly and professional
""",
    tools=tools
)
