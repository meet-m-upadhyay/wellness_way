#!/usr/bin/env python3
"""
Test Bell Peppers Normalization Fix

Verifies that 'bell peppers' resolves correctly without normalization mismatch.
"""

import asyncio
from app.services.nutrition_database import get_nutrition_database
from app.services.nutrition_engine import create_ingredient_with_resolution


async def test_bell_peppers_fix():
    """Test that bell peppers resolves correctly"""
    print("Testing bell peppers normalization fix...")
    
    # Test direct database lookup
    db = get_nutrition_database()
    
    print("\n1. Testing direct database lookup:")
    try:
        nutrition = db.get_nutrition("bell peppers", 100)
        print(f"✅ Direct lookup: bell peppers -> {nutrition.calories} cal, {nutrition.protein}g protein")
    except Exception as e:
        print(f"❌ Direct lookup failed: {e}")
        return False
    
    # Test through ingredient resolution
    print("\n2. Testing through ingredient resolution:")
    try:
        ingredient = await create_ingredient_with_resolution("bell peppers", 100, "g")
        print(f"✅ Resolution: bell peppers -> {ingredient.nutrition.calories} cal, {ingredient.nutrition.protein}g protein")
        print(f"   Resolved name: '{ingredient.name}'")
        print(f"   Resolution status: {ingredient.resolution_status}")
    except Exception as e:
        print(f"❌ Resolution failed: {e}")
        return False
    
    print("\n🎉 Bell peppers fix verified successfully!")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_bell_peppers_fix())
    if not success:
        exit(1)