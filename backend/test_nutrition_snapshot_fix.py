#!/usr/bin/env python3
"""
Test Nutrition Snapshot Fix

Verifies that the nutrition snapshot prevents zero nutrition in API conversion.
"""

import asyncio
import logging
from app.services.nutrition_engine import create_ingredient_with_resolution
from app.services.ai_service import DietPlanAI

# Set up logging to see debug messages
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')

async def test_nutrition_snapshot():
    """Test that nutrition snapshot prevents zero nutrition bug"""
    print("Testing nutrition snapshot fix...")
    
    # Create a meal with ingredients
    try:
        ingredient = await create_ingredient_with_resolution("greek yogurt (plain)", 150, "g")
        print(f"✅ Ingredient created: {ingredient.name} -> {ingredient.nutrition.calories} cal")
        
        # Check if nutrition snapshot exists
        if hasattr(ingredient, '_nutrition_snapshot'):
            print(f"✅ Nutrition snapshot exists: {ingredient._nutrition_snapshot.calories} cal")
        else:
            print("❌ No nutrition snapshot found")
        
        # Test API conversion (this would normally be done by AI service)
        ai_service = DietPlanAI()
        
        # Create a mock meal object for testing
        class MockMeal:
            def __init__(self):
                self.name = "Test Meal"
                self.ingredients = [ingredient]
                self._nutrition_snapshot = ingredient.nutrition
            
            @property
            def nutrition(self):
                # Simulate the bug where this returns 0
                from app.services.nutrition_database import NutritionData, ProteinQuality
                return NutritionData(0, 0, 0, 0, 0, 0, ProteinQuality.INCOMPLETE)
        
        mock_meal = MockMeal()
        
        # Test the API conversion helper
        api_nutrition = ai_service._get_meal_nutrition_for_api(mock_meal)
        print(f"✅ API nutrition: {api_nutrition}")
        
        if api_nutrition['calories'] > 0:
            print("🎉 Nutrition snapshot fix working - API gets real nutrition!")
            return True
        else:
            print("❌ Nutrition snapshot fix failed - still getting 0 nutrition")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_nutrition_snapshot())
    if not success:
        exit(1)