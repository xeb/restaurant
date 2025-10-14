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
from contextlib import redirect_stdout, redirect_stderr
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

# Add recipes MCP tools
if McpToolset:
    try:
        f_out = io.StringIO()
        f_err = io.StringIO()

        with redirect_stdout(f_out), redirect_stderr(f_err):
            recipes_connection = StdioConnectionParams(
                server_params=StdioServerParameters(
                    command="uv",
                    args=["run", "recipes_mcp_server.py"]
                )
            )

            recipes_toolset = McpToolset(
                connection_params=recipes_connection
            )

            tools.append(recipes_toolset)
            print("[CHEF] ✅ Connected to recipes MCP server")

    except Exception as e:
        print(f"[CHEF] ⚠️  Could not connect to recipes MCP: {e}")

# Add pantry MCP tools
if McpToolset:
    try:
        f_out = io.StringIO()
        f_err = io.StringIO()

        with redirect_stdout(f_out), redirect_stderr(f_err):
            pantry_connection = StdioConnectionParams(
                server_params=StdioServerParameters(
                    command="uv",
                    args=["run", "../pantry_mcp_server.py"]
                )
            )

            pantry_toolset = McpToolset(
                connection_params=pantry_connection
            )

            tools.append(pantry_toolset)
            print("[CHEF] ✅ Connected to pantry MCP server")

    except Exception as e:
        print(f"[CHEF] ⚠️  Could not connect to pantry MCP: {e}")

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
7. Respond with the time estimate and status

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
7. Respond with clear status and time estimate

Log all actions with [CHEF] prefix.

Example response format:
"Order received for Greek Salad. Checked pantry - all ingredients available.
Prep time: 15 min, Cook time: 0 min. Total time: 15 minutes. Starting preparation now!"

Or if ingredients needed:
"Order received for Grilled Salmon. Missing 2 units of salmon. Ordering from supplier...
[wait for supplier delivery]
Ingredients restocked. Prep time: 10 min, Cook time: 20 min, Supplier wait: 3 min.
Total time: 33 minutes. Starting preparation now!"
""",
    tools=tools
)
