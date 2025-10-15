#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "google-adk[a2a]",
#     "fastmcp",
#     "fire",
# ]
# ///
"""Chef Agent - Prepares dishes based on orders.

This agent:
1. Receives orders from the waiter
2. Looks up recipes in the recipes MCP server
3. Checks pantry for ingredients
4. Takes ingredients from pantry or orders from supplier if needed
5. Estimates cooking time
"""

import io
import sys
import warnings
import logging
from contextlib import redirect_stdout, redirect_stderr

# Suppress warnings from Google ADK and GenAI
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message="Deprecated. Please migrate to the async method.")
warnings.filterwarnings("ignore", message=".*there are non-text parts in the response.*")

# Suppress logger warnings
logging.getLogger('google.genai.types').setLevel(logging.ERROR)
logging.getLogger('google.adk').setLevel(logging.ERROR)
logging.getLogger('google.adk.tools').setLevel(logging.ERROR)
logging.getLogger('google.adk.sessions').setLevel(logging.ERROR)

from google.adk import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.tools.agent_tool import AgentTool

try:
    from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset as McpToolset
    from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams, StdioServerParameters
except ImportError:
    print("Error: Could not import MCP tools", file=sys.stderr)
    McpToolset = None

tools = []

# Determine MCP server paths (works from both root and chef/ directory)
import os

# Add recipes MCP tools
if McpToolset:
    # Try to find recipes_mcp_server.py in multiple locations
    recipes_possible_paths = [
        "chef/recipes_mcp_server.py",     # When running from root (webapp)
        "recipes_mcp_server.py",          # When running from chef/ (a2a_server)
    ]

    recipes_path = None
    for path in recipes_possible_paths:
        if os.path.exists(path):
            # Convert to absolute path so it works regardless of current directory

            recipes_path = os.path.abspath(path)
            break

    if recipes_path is None:
        print(f"[CHEF] ⚠️  Could not find recipes_mcp_server.py in any of: {recipes_possible_paths}")
    else:
        try:
            recipes_connection = StdioConnectionParams(
                    server_params=StdioServerParameters(
                        command="uv",
                        args=["run", recipes_path]
                )
            )

            recipes_toolset = McpToolset(
                    connection_params=recipes_connection
            )

            tools.append(recipes_toolset)
            print(f"[CHEF] ✅ Connected to recipes MCP server (using {recipes_path})")

        except Exception as e:
            print(f"[CHEF] ⚠️  Could not connect to recipes MCP: {e}")

# Add pantry MCP tools
if McpToolset:
    # Try to find pantry_mcp_server.py in multiple locations
    pantry_possible_paths = [
        "pantry_mcp_server.py",           # When running from root (webapp)
        "../pantry_mcp_server.py",        # When running from chef/ (a2a_server)
    ]

    pantry_path = None
    for path in pantry_possible_paths:
        if os.path.exists(path):
            # Convert to absolute path so it works regardless of current directory

            pantry_path = os.path.abspath(path)
            break

    if pantry_path is None:
        print(f"[CHEF] ⚠️  Could not find pantry_mcp_server.py in any of: {pantry_possible_paths}")
    else:
        try:
            pantry_connection = StdioConnectionParams(
                    server_params=StdioServerParameters(
                        command="uv",
                        args=["run", pantry_path]
                )
            )

            pantry_toolset = McpToolset(
                    connection_params=pantry_connection
            )

            tools.append(pantry_toolset)
            print(f"[CHEF] ✅ Connected to pantry MCP server (using {pantry_path})")

        except Exception as e:
            print(f"[CHEF] ⚠️  Could not connect to pantry MCP: {e}")

# Add order_up MCP tools
if McpToolset:
    # Try to find order_up_mcp_server.py in multiple locations
    order_up_possible_paths = [
        "order_up_mcp_server.py",           # When running from root (webapp)
        "../order_up_mcp_server.py",        # When running from chef/ (a2a_server)
    ]

    order_up_path = None
    for path in order_up_possible_paths:
        if os.path.exists(path):
            order_up_path = os.path.abspath(path)
            break

    if order_up_path is None:
        print(f"[CHEF] ⚠️  Could not find order_up_mcp_server.py in any of: {order_up_possible_paths}")
    else:
        try:
            order_up_connection = StdioConnectionParams(
                    server_params=StdioServerParameters(
                        command="uv",
                        args=["run", order_up_path]
                )
            )

            order_up_toolset = McpToolset(
                    connection_params=order_up_connection
            )

            tools.append(order_up_toolset)
            print(f"[CHEF] ✅ Connected to order_up MCP server (using {order_up_path})")

        except Exception as e:
            print(f"[CHEF] ⚠️  Could not connect to order_up MCP: {e}")

# Add supplier agent as a tool (A2A)
try:
    print("[CHEF] Connecting to supplier agent via A2A...")

    supplier_agent = RemoteA2aAgent(
        name="supplier_agent",
        agent_card="http://localhost:8003/.well-known/agent-card.json"
    )

    supplier_tool = AgentTool(agent=supplier_agent)
    tools.append(supplier_tool)

    print("[CHEF] ✅ Connected to supplier agent via A2A (port 8003)")

except Exception as e:
    print(f"[CHEF] ⚠️  Could not connect to supplier agent: {e}")

# Create the chef agent
root_agent = Agent(
    model="gemini-2.5-flash",
    name="chef_agent",
    description="Chef agent that prepares dishes based on orders",
    instruction="""You are a professional chef in a restaurant.

Your job is to:
1. Receive dish orders from the waiter (e.g., "Greek Salad", "Grilled Salmon")
2. Look up the recipe using list_recipes and get_recipe tools
3. Check if you have ingredients in the pantry using check_pantry
4. If ingredients are available, take them using take_ingredients
5. If ingredients are missing, order from supplier using the supplier_agent tool
6. Calculate total time needed (prep + cook time from recipe + any supplier wait time)
7. Use accept_order to mark the order as ready with timing details (it returns an auto-generated order ID)
8. Respond with the order ID, time estimate and status

IMPORTANT WORKFLOW:
1. ALWAYS use list_recipes first to find the recipe ID
2. Use get_recipe with the ID to get full recipe details including ingredients
3. Parse ingredients to extract quantities (e.g., "2 cups broccoli" -> {"broccoli": 2})
4. Use check_pantry to verify each ingredient
5. Try take_ingredients - if it fails due to missing items:
   - Extract the missing ingredients from the error response
   - Call supplier_agent to order them (it will wait and restock)
   - Then retry take_ingredients
6. Add up all times (prep + cook + supplier delivery)
7. Call accept_order with recipe name, prep_time, and cook_time (order ID is auto-generated)
8. Respond with clear status including the order ID returned from accept_order

DELIVERY NOTIFICATIONS:
When the waiter notifies you that an order has been served/delivered to the customer:
1. The waiter will send a message like "Order #3 has been delivered" or "Order 3 served"
2. Extract the order_id from the message
3. Use mark_order_delivered(order_id) to update the status from "ready" to "delivered"
4. Respond with confirmation: "Order #3 marked as delivered. Thanks for letting me know!"

Log all actions with [CHEF] prefix.

Example response format:
"Order #3 received for Greek Salad. Checked pantry - all ingredients available.
Prep time: 15 min, Cook time: 0 min. Total time: 15 minutes. Order ready!"

Or if ingredients needed:
"Order #4 received for Grilled Salmon. Missing 2 units of salmon. Ordering from supplier...
[wait for supplier delivery]
Ingredients restocked. Prep time: 10 min, Cook time: 20 min, Supplier wait: 3 min.
Total time: 33 minutes. Order ready!"
""",
    tools=tools
)
