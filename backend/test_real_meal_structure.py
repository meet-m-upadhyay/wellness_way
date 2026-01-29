#!/usr/bin/env python3
"""
Test script to see what structure the AI service actually produces
"""

import asyncio
import logging
from uuid import uuid4
from app.services.nutrition_engine import NutritionEngine, Meal, Ingredient, NutritionData, ProteinQuality

# Configure logging to see debug messages
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s:%(name)s:%(message)s'
)

async def test_real_meal_structure():
    """Test what structure meals actually have when created by nutrition engine"""
    
    print("🧪 TESTING REAL MEAL STRUCTURE FROM NUTRITION ENGINE")
    print("=" * 60)
    
    # Create a meal using the actual nutrition engine process
    nutrition_engine = NutritionEngine()
    
    # Simulate what AI service would provide
    ai_meal_data = {
        "name": "Greek Yogurt and Hemp Seed Parfait",
        "ingredients": [
            {"name": "greek yogurt", "quantity": 200, "unit": "g"},
            {"name": "hemp seeds", "quantity": 15, "unit": "g"},
            {"name": "mixed berries", "quantity": 100, "unit": "g"}
        ],
        "instructions": "Mix ingredients together",
        "meal_type": "breakfast"
    }
    
    print("📊 Creating meal using create_meal_with_resolution...")
    
    try:
        # This is what actually gets called in the pipeline
        meal = await nutrition_engine.create_meal_with_resolution(
            meal_name=ai_meal_data["name"],
            ingredients_list=ai_meal_data["ingredients"],
            instructions=ai_meal_data["instructions"],
            meal_type=ai_meal_data["meal_type"]
        )
        
        print(f"\n📈 MEAL OBJECT CREATED:")
        print(f"   Type: {type(meal)}")
        print(f"   Name: {meal.name}")
        print(f"   Nutrition Type: {type(meal.nutrition)}")
        print(f"   Nutrition: {meal.nutrition}")
        
        # Now let's see what happens when this gets serialized to dict
        # This is what would happen in the safety pipeline
        meal_dict = {
            "name": meal.name,
            "meal_type": meal.meal_type,
            "ingredients": [
                {
                    "name": ing.name,
                    "quantity": ing.quantity,
                    "unit": ing.unit,
                    "nutrition": ing.nutrition.__dict__ if ing.nutrition else None
                }
                for ing in meal.ingredients
            ],
            "nutrition": meal.nutrition.__dict__ if hasattr(meal.nutrition, '__dict__') else meal.nutrition,
            "instructions": meal.instructions
        }
        
        print(f"\n📋 SERIALIZED MEAL DICT:")
        print(f"   Nutrition field type: {type(meal_dict['nutrition'])}")
        print(f"   Nutrition field: {meal_dict['nutrition']}")
        
        # Test our aggregation function with this structure
        from app.services.plan_validation import DietPlanValidator
        
        test_plan = {
            "plan_type": "daily",
            "meals": [meal_dict]
        }
        
        validator = DietPlanValidator()
        print(f"\n🔍 TESTING AGGREGATION WITH REAL STRUCTURE:")
        calories, protein = validator._extract_daily_totals(test_plan)
        
        print(f"\n📈 AGGREGATION RESULTS:")
        print(f"   Calories: {calories}")
        print(f"   Protein: {protein}")
        
        if calories and protein and calories > 0 and protein > 0:
            print("\n✅ SUCCESS: Real meal structure works with aggregation!")
        else:
            print("\n❌ FAILURE: Real meal structure doesn't work with aggregation!")
            print("   This reveals the actual data structure issue")
            
    except Exception as e:
        print(f"\n❌ ERROR creating meal: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_real_meal_structure())