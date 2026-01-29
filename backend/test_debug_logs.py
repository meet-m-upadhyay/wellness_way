#!/usr/bin/env python3
"""
Test Debug Logs for Ingredient Resolution

Shows the new debug logs in action.
"""

import asyncio
import logging
from app.services.nutrition_engine import create_ingredient_with_resolution

# Set up logging to see debug messages
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')

async def test_debug_logs():
    """Test that debug logs are working"""
    print("Testing debug logs for ingredient resolution...")
    
    try:
        ingredient = await create_ingredient_with_resolution("bell peppers", 150, "g")
        print(f"\n✅ Success: {ingredient.name} -> {ingredient.nutrition.calories} cal")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_debug_logs())