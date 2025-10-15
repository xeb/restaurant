#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "fastmcp",
#     "fire",
# ]
# ///
"""Menu MCP Server - Provides artisanal menu descriptions for the waiter.

This server manages the restaurant's menu with curated descriptions.
The waiter agent uses this to answer customer questions about menu items.
"""

from fastmcp import FastMCP
import fire
import json
import os
from typing import Dict, List, Optional

mcp = FastMCP()

# File paths
MENU_FILE = "menu.json"

# Global data
MENU_DATA: Dict = {}

def load_menu() -> Dict:
    """Load menu from JSON file."""
    if os.path.exists(MENU_FILE):
        try:
            with open(MENU_FILE, 'r') as f:
                data = json.load(f)
                print(f"[MENU] Loaded {len(data.get('menu', {}))} menu items from {MENU_FILE}")
                return data
        except Exception as e:
            print(f"[MENU] ⚠️  Error loading {MENU_FILE}: {e}")
            return {"menu": {}}
    else:
        print(f"[MENU] ⚠️  No {MENU_FILE} found!")
        return {"menu": {}}

# Load menu at startup
MENU_DATA = load_menu()

@mcp.tool
def list_menu(category: Optional[str] = None) -> dict:
    """List all menu items with descriptions, optionally filtered by category.

    Args:
        category: Optional category filter (e.g., "Salads", "Breakfast & Brunch", "Seafood")

    Returns:
        List of menu items with their descriptions and details
    """
    print(f"[MENU] Listing menu items" + (f" in category '{category}'" if category else ""))

    menu = MENU_DATA.get("menu", {})
    items = []

    for item_name, item_data in menu.items():
        if category is None or item_data.get("category") == category:
            items.append({
                "name": item_data.get("name"),
                "category": item_data.get("category"),
                "description": item_data.get("description"),
                "price": item_data.get("price"),
                "dietary": item_data.get("dietary", []),
                "prep_time": item_data.get("prep_time"),
                "cook_time": item_data.get("cook_time")
            })

    # Sort by category then name
    items.sort(key=lambda x: (x["category"], x["name"]))

    print(f"[MENU] Found {len(items)} menu items")
    return {
        "items": items,
        "count": len(items)
    }

@mcp.tool
def get_menu_item(item_name: str) -> dict:
    """Get detailed information about a specific menu item.

    Args:
        item_name: Name of the menu item (e.g., "Greek Salad")

    Returns:
        Full details about the menu item including description, price, dietary info
    """
    print(f"[MENU] Looking up menu item: {item_name}")

    menu = MENU_DATA.get("menu", {})

    if item_name in menu:
        item = menu[item_name]
        print(f"[MENU] ✅ Found {item_name}")
        return {
            "success": True,
            "item": {
                "name": item.get("name"),
                "category": item.get("category"),
                "description": item.get("description"),
                "price": item.get("price"),
                "dietary": item.get("dietary", []),
                "prep_time": item.get("prep_time"),
                "cook_time": item.get("cook_time")
            }
        }
    else:
        print(f"[MENU] ❌ Menu item '{item_name}' not found")
        return {
            "success": False,
            "message": f"Menu item '{item_name}' not found"
        }

@mcp.tool
def list_categories() -> dict:
    """List all available menu categories.

    Returns:
        List of unique menu categories
    """
    print(f"[MENU] Listing menu categories")

    menu = MENU_DATA.get("menu", {})
    categories = set()

    for item_data in menu.values():
        category = item_data.get("category")
        if category:
            categories.add(category)

    categories_list = sorted(list(categories))

    print(f"[MENU] Found {len(categories_list)} categories")
    return {
        "categories": categories_list,
        "count": len(categories_list)
    }

@mcp.tool
def search_menu(query: str) -> dict:
    """Search menu items by keyword in name or description.

    Args:
        query: Search term (searches in name and description)

    Returns:
        List of matching menu items
    """
    print(f"[MENU] Searching menu for: '{query}'")

    menu = MENU_DATA.get("menu", {})
    query_lower = query.lower()
    matches = []

    for item_name, item_data in menu.items():
        name_match = query_lower in item_data.get("name", "").lower()
        desc_match = query_lower in item_data.get("description", "").lower()

        if name_match or desc_match:
            matches.append({
                "name": item_data.get("name"),
                "category": item_data.get("category"),
                "description": item_data.get("description"),
                "price": item_data.get("price"),
                "dietary": item_data.get("dietary", [])
            })

    print(f"[MENU] Found {len(matches)} matches for '{query}'")
    return {
        "matches": matches,
        "count": len(matches),
        "query": query
    }

def main(transport="stdio", host="0.0.0.0", port=8727):
    """Run the menu MCP server."""
    if transport in ["sse", "streamable-http"]:
        mcp.run(transport=transport, host=host, port=port)
    elif transport == "stdio":
        mcp.run()
    else:
        raise Exception(f"Invalid parameters {transport=} {host=} {port=}")

if __name__ == "__main__":
    fire.Fire(main)
