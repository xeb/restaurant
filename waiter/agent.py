#!/usr/bin/env python3
"""Waiter agent - uses chef via A2A and orders/menu MCP servers."""

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
    print("[WAITER] Error: Could not import MCP tools", file=sys.stderr)
    McpToolset = None

print("[WAITER] Connecting to chef agent via A2A...")

tools = []

try:
    chef_agent = RemoteA2aAgent(
        name="chef_agent",
        agent_card="http://localhost:8002/.well-known/agent-card.json"
    )

    chef_tool = AgentTool(agent=chef_agent)
    tools.append(chef_tool)

    print("[WAITER] ✅ Connected to chef agent (port 8002)")

except Exception as e:
    print(f"[WAITER] ⚠️  Could not connect to chef agent: {e}")

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
        print(f"[WAITER] ⚠️  Could not find orders_mcp_server.py in any of: {orders_possible_paths}")
    else:
        try:
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
            print(f"[WAITER] ✅ Connected to orders MCP server (using {orders_path})")

        except Exception as e:
            print(f"[WAITER] ⚠️  Could not connect to orders MCP: {e}")

# Add menu MCP tools
if McpToolset:
    # Try to find menu_mcp_server.py in multiple locations
    menu_possible_paths = [
        "menu_mcp_server.py",           # When running from root (webapp)
        "../menu_mcp_server.py",        # When running from waiter/ directory
    ]

    menu_path = None
    for path in menu_possible_paths:
        if os.path.exists(path):
            # Convert to absolute path so it works regardless of current directory
            menu_path = os.path.abspath(path)
            break

    if menu_path is None:
        print(f"[WAITER] ⚠️  Could not find menu_mcp_server.py in any of: {menu_possible_paths}")
    else:
        try:
            menu_connection = StdioConnectionParams(
                server_params=StdioServerParameters(
                    command="uv",
                    args=["run", menu_path]
                )
            )

            menu_toolset = McpToolset(
                connection_params=menu_connection
            )

            tools.append(menu_toolset)
            print(f"[WAITER] ✅ Connected to menu MCP server (using {menu_path})")

        except Exception as e:
            print(f"[WAITER] ⚠️  Could not connect to menu MCP: {e}")

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
- list_menu(category) - List all menu items, optionally filtered by category
- get_menu_item(item_name) - Get detailed description of a specific menu item
- list_categories() - Get all menu categories
- search_menu(query) - Search menu by keyword

HANDLING MENU QUESTIONS:
When customer asks "What do you have on the menu?" or "What can I order?":
1. Use list_menu() to get all menu items
2. Present them in an organized, appealing way by category
3. Highlight a few signature dishes with their artisanal descriptions
4. Offer to provide more details on any item

When customer asks about a specific item:
1. Use get_menu_item(item_name) to get the full description
2. Share the artisanal description, price, and dietary information
3. Mention prep/cook time if they ask

When customer asks about dietary options (vegan, gluten-free, etc.):
1. Use search_menu(query) with the dietary term
2. List matching items with their descriptions

WORKFLOW FOR TAKING AN ORDER:
1. First interaction: ALWAYS ask "Welcome! May I have your name please?"
2. Wait for customer to provide their name
3. Ask: "What would you like to order, [name]?"
4. Customer orders (e.g., "Greek Salad")
5. Send order to chef: chef_agent("Order: Greek Salad")
   - Do NOT include the customer's name in the message to the chef
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
   - THEN notify the chef: chef_agent("Order #[order_id] has been delivered")
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
You: [Use chef_agent("Order: Greek Salad")]
     [Chef responds: "Greek Salad will be ready in 15 minutes (prep: 15min, cook: 0min)"]
     [Use save_order(name="Alice", order_details="Greek Salad", estimated_wait_time="15 minutes") → returns order_id 1]
     [Use set_order_status(1, "COOKING")]
     [Use set_order_status(1, "READY")]
     "Excellent choice! Your Greek Salad will be ready in 15 minutes."

Customer: "Where is my food?"
You: [Use list_orders() → finds order #1 for Alice with status READY]
     [Use set_order_status(1, "SERVED")]
     [Use chef_agent("Order #1 has been delivered")]
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
