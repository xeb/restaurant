#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "google-adk[a2a]",
#     "fastmcp",
#     "fire",
# ]
# ///
"""Supplier Agent - Supplies ingredients to the restaurant.

This agent receives orders for ingredients, waits a random time (2-5 seconds),
and then adds the ingredients to the pantry via the pantry MCP server.
"""

import io
import sys
import time
import random
import warnings
import logging
from contextlib import redirect_stdout, redirect_stderr

# Suppress warnings from Google ADK and GenAI
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message="Deprecated. Please migrate to the async method.")
warnings.filterwarnings("ignore", message=".*there are non-text parts in the response.*")

# Suppress logger warnings - set level and disable propagation
for logger_name in ['google.genai.types', 'google.genai', 'google.adk', 'google.adk.tools', 'google.adk.sessions']:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.ERROR)
    logger.propagate = False

from google.adk import Agent
from google.adk.tools import FunctionTool

try:
    from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset as McpToolset
    from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams, StdioServerParameters
except ImportError:
    print("Error: Could not import MCP tools", file=sys.stderr)
    McpToolset = None

def wait_time(item: str, quantity: int) -> dict:
    """Simulate waiting for supplier delivery (instant for fast UI).

    Args:
        item: The ingredient being supplied
        quantity: The quantity being supplied

    Returns:
        Status and wait time information
    """
    print(f"[SUPPLIER] 📦 Preparing {quantity} units of {item}...")
    print(f"[SUPPLIER] ✅ {item} ready for delivery!")

    return {
        "item": item,
        "quantity": quantity,
        "wait_seconds": 0,
        "status": "ready_for_delivery"
    }

# Create tools list
tools = [FunctionTool(wait_time)]

# Add pantry MCP tools
if McpToolset:
    # Determine pantry MCP server path (works from both root and supplier/ directory)
    import os

    # Try to find pantry_mcp_server.py in multiple locations
    possible_paths = [
        "pantry_mcp_server.py",           # When running from root (webapp)
        "../pantry_mcp_server.py",        # When running from supplier/ (a2a_server)
    ]

    pantry_path = None
    for path in possible_paths:
        if os.path.exists(path):
            # Convert to absolute path so it works regardless of current directory
            pantry_path = os.path.abspath(path)
            break

    if pantry_path is None:
        print(f"[SUPPLIER] ⚠️  Could not find pantry_mcp_server.py in any of: {possible_paths}")
    else:
        try:
            # Suppress MCP connection messages
            f_out = io.StringIO()
            f_err = io.StringIO()

            with redirect_stdout(f_out), redirect_stderr(f_err):
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
                print(f"[SUPPLIER] ✅ Connected to pantry MCP server (using {pantry_path})")

        except Exception as e:
            print(f"[SUPPLIER] ⚠️  Could not connect to pantry MCP: {e}")

# Create the supplier agent
root_agent = Agent(
    model="gemini-2.5-flash",
    name="supplier_agent",
    description="Supplier agent that provides ingredients to the restaurant",
    instruction="""You are a food supplier for a restaurant.

Your job is to:
1. Receive orders for ingredients from the chef
2. FIRST, use list_pantry to check what ingredient names already exist in the pantry
3. Match the requested ingredients to the EXACT names already in the pantry to avoid duplicates
4. Use the wait_time tool to simulate preparing/delivering each ingredient type
5. After waiting, use add_ingredients with the EXACT pantry names to restock
6. Report back to the chef that the ingredients have been delivered

CRITICAL RULES TO PREVENT DUPLICATES:
- ALWAYS call list_pantry FIRST before adding any ingredients
- Use the EXACT ingredient name that already exists in the pantry (e.g., if pantry has "tomatoes", use "tomatoes" NOT "tomato" or "cherry tomatoes")
- Match ingredient variations to existing names:
  * "tomato" → use "tomatoes" if it exists
  * "cucumber" → use "cucumbers" if it exists
  * "bell pepper" → use "bell peppers" if it exists
  * "olive oil", "extra virgin olive oil" → use "olive oil" if it exists
  * "feta" → use "feta cheese" if it exists
  * "parmesan" → use "parmesan cheese" if it exists
  * "romaine" → use "romaine lettuce" if it exists
  * "salmon fillet" → use "salmon" if it exists
  * "broccoli floret" → use "broccoli" if it exists
- If unsure about the exact name, prefer the plural form or the name that's already in the pantry
- NEVER create new ingredient variants like "red onion" if "onion" exists, or "dried oregano" if "oregano" exists

Example flow:
1. Chef orders: {"tomatoes": 10, "feta": 5}
2. You call list_pantry to see existing names
3. You see pantry has "tomatoes" and "feta cheese"
4. You call wait_time for the order
5. You call add_ingredients with {"tomatoes": 10, "feta cheese": 5} using EXACT pantry names
6. You respond: "Delivered 10 tomatoes and 5 feta cheese to the pantry"

Log all actions with [SUPPLIER] prefix.
""",
    tools=tools
)
