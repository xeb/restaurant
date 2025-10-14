#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "fastmcp",
#     "fire",
# ]
# ///
"""Pantry MCP Server - Manages ingredient inventory for the restaurant.

This server tracks available ingredients and their quantities.
Both the chef and supplier agents use this to check and update inventory.
"""

from fastmcp import FastMCP
import fire
from typing import Dict

mcp = FastMCP()

# Pantry inventory - ingredient name to quantity mapping
PANTRY_INVENTORY: Dict[str, int] = {
    "quinoa": 5,
    "avocado": 8,
    "chickpeas": 10,
    "spinach": 6,
    "cucumber": 7,
    "tomatoes": 12,
    "salmon": 4,
    "broccoli": 5,
    "bell_peppers": 6,
    "olive_oil": 20,
    "flour": 15,
    "butter": 10,
    "sugar": 12,
    "chocolate_chips": 8,
    "eggs": 24,
    "feta_cheese": 4,
    "olives": 6,
    "beef": 3,
    "soy_sauce": 8,
    "ginger": 5,
    "bread": 8,
    "lime": 10,
    "coconut_milk": 6,
    "curry_powder": 5,
    "cauliflower": 4,
    "milk": 8,
    "baking_powder": 10,
    "romaine_lettuce": 6,
    "parmesan": 5,
    "berries": 12,
    "banana": 10,
    "almond_milk": 6,
    "chia_seeds": 8,
    "granola": 5,
}

@mcp.tool
def check_pantry(ingredient: str = None) -> dict:
    """Check pantry inventory for a specific ingredient or all ingredients.

    Args:
        ingredient: Optional ingredient name to check. If None, returns all inventory.

    Returns:
        Dictionary with ingredient quantities or single ingredient quantity.
    """
    print(f"[PANTRY] Checking inventory for: {ingredient if ingredient else 'ALL'}")

    if ingredient:
        quantity = PANTRY_INVENTORY.get(ingredient, 0)
        result = {ingredient: quantity, "available": quantity > 0}
        print(f"[PANTRY] {ingredient}: {quantity} units")
        return result
    else:
        print(f"[PANTRY] Total items in pantry: {len(PANTRY_INVENTORY)}")
        return {"inventory": PANTRY_INVENTORY, "total_items": len(PANTRY_INVENTORY)}

@mcp.tool
def take_ingredients(ingredients: dict) -> dict:
    """Remove ingredients from pantry (chef taking ingredients for a recipe).

    Args:
        ingredients: Dictionary of ingredient names to quantities needed

    Returns:
        Success status and updated inventory or list of missing ingredients
    """
    print(f"[PANTRY] Chef requesting ingredients: {ingredients}")

    missing = []

    # First check if all ingredients are available
    for ingredient, quantity in ingredients.items():
        available = PANTRY_INVENTORY.get(ingredient, 0)
        if available < quantity:
            missing.append({
                "ingredient": ingredient,
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
    for ingredient, quantity in ingredients.items():
        PANTRY_INVENTORY[ingredient] -= quantity
        print(f"[PANTRY] Took {quantity} units of {ingredient} (remaining: {PANTRY_INVENTORY[ingredient]})")

    print(f"[PANTRY] ✅ Successfully provided all ingredients")
    return {
        "success": True,
        "message": "All ingredients provided",
        "updated_inventory": {k: PANTRY_INVENTORY[k] for k in ingredients.keys()}
    }

@mcp.tool
def add_ingredients(ingredients: dict) -> dict:
    """Add ingredients to pantry (supplier restocking).

    Args:
        ingredients: Dictionary of ingredient names to quantities to add

    Returns:
        Success status and updated inventory
    """
    print(f"[PANTRY] Supplier adding ingredients: {ingredients}")

    for ingredient, quantity in ingredients.items():
        current = PANTRY_INVENTORY.get(ingredient, 0)
        PANTRY_INVENTORY[ingredient] = current + quantity
        print(f"[PANTRY] Added {quantity} units of {ingredient} (now: {PANTRY_INVENTORY[ingredient]})")

    print(f"[PANTRY] ✅ Successfully restocked {len(ingredients)} items")
    return {
        "success": True,
        "message": f"Added {len(ingredients)} ingredient types",
        "updated_inventory": {k: PANTRY_INVENTORY[k] for k in ingredients.keys()}
    }

@mcp.tool
def get_low_stock_items(threshold: int = 3) -> dict:
    """Get list of ingredients that are running low.

    Args:
        threshold: Quantity threshold for low stock (default: 3)

    Returns:
        List of low stock ingredients
    """
    print(f"[PANTRY] Checking for items below {threshold} units")

    low_stock = {k: v for k, v in PANTRY_INVENTORY.items() if v <= threshold}

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
