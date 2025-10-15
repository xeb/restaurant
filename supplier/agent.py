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
    """Simulate waiting for supplier delivery.

    Args:
        item: The ingredient being supplied
        quantity: The quantity being supplied

    Returns:
        Status and wait time information
    """
    wait_seconds = random.randint(2, 5)
    print(f"[SUPPLIER] 📦 Preparing {quantity} units of {item}... (will take {wait_seconds} seconds)")

    time.sleep(wait_seconds)

    print(f"[SUPPLIER] ✅ {item} ready for delivery!")

    return {
        "item": item,
        "quantity": quantity,
        "wait_seconds": wait_seconds,
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
2. Use the wait_time tool to simulate preparing/delivering each ingredient type
3. After waiting, use the pantry tools to add_ingredients to restock the pantry
4. Report back to the chef that the ingredients have been delivered

IMPORTANT:
- Always call wait_time FIRST for each ingredient order to simulate delivery time
- After wait_time completes, call add_ingredients to add them to the pantry
- Be clear and concise in your responses
- Log all actions to stdout with [SUPPLIER] prefix

Example flow:
1. Chef orders: {"tomatoes": 10, "cheese": 5}
2. You call wait_time for the order (simulating delivery)
3. You call add_ingredients with the same quantities
4. You respond: "Delivered 10 tomatoes and 5 cheese to the pantry"
""",
    tools=tools
)
