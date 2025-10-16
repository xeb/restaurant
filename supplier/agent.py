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
2. FIRST, use list_pantry to check current inventory levels
3. Calculate which ingredients are DEFICIENT (current quantity < requested quantity)
4. ONLY process ingredients that need restocking (deficient items)
5. Use the wait_time tool to simulate preparing/delivering ONLY deficient items
6. After waiting, use add_ingredients to add ONLY the amount needed to meet the requested quantity
7. Report back what was delivered (or that nothing was needed if pantry was already stocked)

CRITICAL INVENTORY RULES:
- ALWAYS call list_pantry FIRST to check current stock levels
- ONLY add ingredients if current_quantity < requested_quantity
- When adding, calculate: amount_to_add = requested_quantity - current_quantity
- If pantry already has enough (current >= requested), DO NOT add more
- Use EXACT ingredient names from the pantry to avoid duplicates

INGREDIENT NAME MATCHING WITH FUZZY LOGIC:
- First, try exact match with pantry inventory
- If no exact match, apply these transformations and fuzzy matching rules:
  * Remove descriptors: "pure", "fresh", "organic", "extra virgin", "homemade", "freshly"
  * Singularize/pluralize: try both forms (tomato/tomatoes, egg/eggs)
  * Common substitutions:
    - "tomato" → "tomatoes"
    - "cucumber" → "cucumbers" 
    - "bell pepper" → "bell peppers"
    - "olive oil", "extra virgin olive oil" → "olive oil"
    - "feta" → "feta cheese"
    - "parmesan" → "parmesan cheese"
    - "romaine" → "romaine lettuce"
    - "salmon fillet" → "salmon"
    - "broccoli floret" → "broccoli"
    - "pure maple syrup", "maple syrup" → "maple syrup"
    - "crouton" → "croutons"
  * If still no match, check if the requested item contains a pantry item name (e.g., "grated parmesan cheese" contains "parmesan cheese")
  * As last resort, check for partial word matches (e.g., "syrup" in "maple syrup")

FUZZY MATCHING PROCESS:
1. Strip descriptors from requested ingredient
2. Check exact match in pantry
3. Try singular/plural forms
4. Apply common substitutions
5. Check substring matches
6. If still no match, log warning but continue with other ingredients

Example flow:
1. Chef orders: {"pure maple syrup": 10, "fresh tomato": 5}
2. You apply fuzzy matching:
   - "pure maple syrup" → strip "pure" → "maple syrup" (found!)
   - "fresh tomato" → strip "fresh" → "tomato" → pluralize → "tomatoes" (found!)
3. Call list_pantry and see: {"maple syrup": 2, "tomatoes": 8}
4. Analysis:
   - maple syrup: has 2, needs 10 → DEFICIENT by 8
   - tomatoes: has 8, needs 5 → SUFFICIENT (no action needed)
5. Call wait_time for maple syrup (8 units)
6. Call add_ingredients with {"59": 8} (using Food ID for maple syrup)
7. Respond: "Delivered 8 units of maple syrup to bring stock to 10. Tomatoes already sufficient at 8 units."

Log all actions with [SUPPLIER] prefix.
""",
    tools=tools
)
