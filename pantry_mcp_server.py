#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "fastmcp",
#     "fire",
# ]
# ///
"""Pantry MCP Server - Manages ingredient inventory using Food IDs.

This server tracks available ingredients by Food ID and their quantities.
It loads the food database (food.json) to provide name lookups.
Both the chef and supplier agents use this to check and update inventory.
"""

from fastmcp import FastMCP
import fire
import json
import os
from typing import Dict, List

mcp = FastMCP()

# File paths
PANTRY_FILE = "pantry.json"
FOOD_FILE = "food.json"

# Global data
PANTRY_INVENTORY: Dict[str, float] = {}  # food_id -> quantity
FOOD_DATABASE: Dict[str, Dict] = {}  # food_id -> {id, name}

def load_food_database() -> Dict[str, Dict]:
    """Load food database from JSON file."""
    if os.path.exists(FOOD_FILE):
        try:
            with open(FOOD_FILE, 'r') as f:
                data = json.load(f)
                foods = data.get("foods", {})
                print(f"[PANTRY] Loaded food database from {FOOD_FILE} ({len(foods)} foods)")
                return foods
        except Exception as e:
            print(f"[PANTRY] ⚠️  Error loading {FOOD_FILE}: {e}")
            return {}
    else:
        print(f"[PANTRY] ⚠️  No {FOOD_FILE} found!")
        return {}

def load_pantry() -> Dict[str, float]:
    """Load pantry inventory from JSON file."""
    if os.path.exists(PANTRY_FILE):
        try:
            with open(PANTRY_FILE, 'r') as f:
                inventory = json.load(f)
                print(f"[PANTRY] Loaded inventory from {PANTRY_FILE} ({len(inventory)} items)")
                return inventory
        except Exception as e:
            print(f"[PANTRY] ⚠️  Error loading {PANTRY_FILE}: {e}, using empty inventory")
            return {}
    else:
        print(f"[PANTRY] No {PANTRY_FILE} found, starting with empty inventory")
        return {}

def save_pantry(inventory: Dict[str, float]) -> None:
    """Save pantry inventory to JSON file."""
    try:
        with open(PANTRY_FILE, 'w') as f:
            json.dump(inventory, f, indent=2)
        print(f"[PANTRY] 💾 Saved inventory to {PANTRY_FILE}")
    except Exception as e:
        print(f"[PANTRY] ⚠️  Error saving to {PANTRY_FILE}: {e}")

def get_food_name(food_id: int) -> str:
    """Get food name from food ID."""
    food_data = FOOD_DATABASE.get(str(food_id))
    if food_data:
        return food_data.get("name", f"Unknown({food_id})")
    return f"Unknown({food_id})"

# Load data at startup
FOOD_DATABASE = load_food_database()
PANTRY_INVENTORY = load_pantry()

@mcp.tool
def list_foods(search: str = None) -> dict:
    """List all available foods in the database, optionally filtered by search term.

    Args:
        search: Optional search term to filter food names (case-insensitive)

    Returns:
        List of foods with their IDs and names
    """
    print(f"[PANTRY] Listing foods" + (f" matching '{search}'" if search else ""))

    foods = []
    for food_id, food_data in FOOD_DATABASE.items():
        name = food_data.get("name", "")
        if search is None or search.lower() in name.lower():
            foods.append({
                "id": food_data.get("id"),
                "name": name
            })

    # Sort by ID
    foods.sort(key=lambda x: x["id"])

    print(f"[PANTRY] Found {len(foods)} foods")
    return {
        "foods": foods,
        "count": len(foods)
    }

@mcp.tool
def list_pantry() -> dict:
    """List all items currently in the pantry with their names and quantities.

    Returns:
        List of pantry items with food IDs, names, and quantities
    """
    # RELOAD from disk to get latest data
    global PANTRY_INVENTORY
    PANTRY_INVENTORY = load_pantry()

    print(f"[PANTRY] Listing pantry contents")

    items = []
    for food_id, quantity in PANTRY_INVENTORY.items():
        items.append({
            "food_id": int(food_id),
            "name": get_food_name(int(food_id)),
            "quantity": quantity
        })

    # Sort by food ID
    items.sort(key=lambda x: x["food_id"])

    print(f"[PANTRY] Pantry contains {len(items)} different items")
    return {
        "items": items,
        "count": len(items)
    }

@mcp.tool
def check_pantry(food_id: int = None) -> dict:
    """Check pantry inventory for a specific food ID or all items.

    Args:
        food_id: Optional food ID to check. If None, returns all inventory.

    Returns:
        Dictionary with food quantities
    """
    # RELOAD from disk to get latest data
    global PANTRY_INVENTORY
    PANTRY_INVENTORY = load_pantry()

    print(f"[PANTRY] Checking inventory for: {f'Food ID {food_id}' if food_id else 'ALL'}")

    if food_id is not None:
        quantity = PANTRY_INVENTORY.get(str(food_id), 0)
        food_name = get_food_name(food_id)
        result = {
            "food_id": food_id,
            "name": food_name,
            "quantity": quantity,
            "available": quantity > 0
        }
        print(f"[PANTRY] {food_name} (ID {food_id}): {quantity} units")
        return result
    else:
        items = []
        for food_id_str, quantity in PANTRY_INVENTORY.items():
            fid = int(food_id_str)
            items.append({
                "food_id": fid,
                "name": get_food_name(fid),
                "quantity": quantity
            })
        print(f"[PANTRY] Total items in pantry: {len(items)}")
        return {"items": items, "total_items": len(items)}

@mcp.tool
def take_ingredients(ingredients: dict) -> dict:
    """Remove ingredients from pantry by Food ID (chef taking ingredients for a recipe).

    Args:
        ingredients: Dictionary of food IDs (as strings) to quantities needed

    Returns:
        Success status and updated inventory or list of missing ingredients
    """
    # RELOAD from disk to get latest data
    global PANTRY_INVENTORY
    PANTRY_INVENTORY = load_pantry()

    print(f"[PANTRY] Chef requesting ingredients: {ingredients}")

    missing = []

    # First check if all ingredients are available
    for food_id_str, quantity in ingredients.items():
        available = PANTRY_INVENTORY.get(food_id_str, 0)
        if available < quantity:
            food_name = get_food_name(int(food_id_str))
            missing.append({
                "food_id": int(food_id_str),
                "name": food_name,
                "needed": quantity,
                "available": available,
                "shortage": quantity - available
            })

    if missing:
        print(f"[PANTRY] ❌ Cannot fulfill request - missing ingredients: {missing}")
        return {
            "success": False,
            "message": "Insufficient ingredients",
            "missing": missing
        }

    # Take ingredients from pantry
    for food_id_str, quantity in ingredients.items():
        PANTRY_INVENTORY[food_id_str] -= quantity
        food_name = get_food_name(int(food_id_str))
        print(f"[PANTRY] Took {quantity} units of {food_name} (ID {food_id_str}, remaining: {PANTRY_INVENTORY[food_id_str]})")

    # Save to file
    save_pantry(PANTRY_INVENTORY)

    print(f"[PANTRY] ✅ Successfully provided all ingredients")
    updated = {food_id_str: PANTRY_INVENTORY[food_id_str] for food_id_str in ingredients.keys()}
    return {
        "success": True,
        "message": "All ingredients provided",
        "updated_inventory": updated
    }

@mcp.tool
def add_ingredients(ingredients: dict) -> dict:
    """Add ingredients to pantry by Food ID (supplier restocking).

    Args:
        ingredients: Dictionary of food IDs (as strings) to quantities to add

    Returns:
        Success status and updated inventory
    """
    # RELOAD from disk to get latest data
    global PANTRY_INVENTORY
    PANTRY_INVENTORY = load_pantry()

    print(f"[PANTRY] Supplier adding ingredients: {ingredients}")

    for food_id_str, quantity in ingredients.items():
        current = PANTRY_INVENTORY.get(food_id_str, 0)
        PANTRY_INVENTORY[food_id_str] = current + quantity
        food_name = get_food_name(int(food_id_str))
        print(f"[PANTRY] Added {quantity} units of {food_name} (ID {food_id_str}, now: {PANTRY_INVENTORY[food_id_str]})")

    # Save to file
    save_pantry(PANTRY_INVENTORY)

    print(f"[PANTRY] ✅ Successfully restocked {len(ingredients)} items")
    updated = {food_id_str: PANTRY_INVENTORY[food_id_str] for food_id_str in ingredients.keys()}
    return {
        "success": True,
        "message": f"Added {len(ingredients)} ingredient types",
        "updated_inventory": updated
    }

@mcp.tool
def get_low_stock_items(threshold: int = 3) -> dict:
    """Get list of ingredients that are running low.

    Args:
        threshold: Quantity threshold for low stock (default: 3)

    Returns:
        List of low stock ingredients with IDs and names
    """
    # RELOAD from disk to get latest data
    global PANTRY_INVENTORY
    PANTRY_INVENTORY = load_pantry()

    print(f"[PANTRY] Checking for items below {threshold} units")

    low_stock = []
    for food_id_str, quantity in PANTRY_INVENTORY.items():
        if quantity <= threshold:
            food_name = get_food_name(int(food_id_str))
            low_stock.append({
                "food_id": int(food_id_str),
                "name": food_name,
                "quantity": quantity
            })

    print(f"[PANTRY] Found {len(low_stock)} low stock items")
    return {
        "low_stock_items": low_stock,
        "count": len(low_stock),
        "threshold": threshold
    }

def main(transport="stdio", host="0.0.0.0", port=8725):
    """Run the pantry MCP server."""
    if transport in ["sse", "streamable-http"]:
        mcp.run(transport=transport, host=host, port=port)
    elif transport == "stdio":
        mcp.run()
    else:
        raise Exception(f"Invalid parameters {transport=} {host=} {port=}")

if __name__ == "__main__":
    fire.Fire(main)
