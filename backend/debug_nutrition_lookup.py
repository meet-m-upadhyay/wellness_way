#!/usr/bin/env python3
"""
Debug script to test nutrition database lookups with common ingredient names.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.nutrition_database import get_nutrition_database
from app.services.nutrition_engine import get_nutrition_engine

def test_nutrition_lookups():
    """Test nutrition database lookups with common ingredient names"""
    
    print("🔍 DEBUGGING NUTRITION DATABASE LOOKUPS")
    print("=" * 50)
    
    db = get_nutrition_database()
    
    # Test common ingredient names that might come from LLM
    test_ingredients = [
        "Greek yogurt (plain)",
        "greek yogurt (plain)",
        "protein powder (vanilla)",
        "whey protein powder",
        "mixed berries",
        "berries (mixed)",
        "almonds (sliced)",
        "almonds",
        "chia seeds",
        "extra-firm tofu",
        "tofu (extra-firm)",
        "cooked red lentils",
        "red lentils (cooked)",
        "cooked quinoa",
        "quinoa (cooked)",
        "roasted chickpeas",
        "chickpeas (cooked)",
        "spinach (fresh)",
        "spinach",
        "avocado",
        "tahini",
        "lemon juice",
        "olive oil",
        "nutritional yeast",
        "hemp seeds",
        "honey"
    ]
    
    print("Testing ingredient lookups:")
    print("-" * 30)
    
    found_count = 0
    missing_count = 0
    
    for ingredient in test_ingredients:
        nutrition = db.get_nutrition(ingredient, 100)  # Test with 100g
        if nutrition:
            print(f"✅ {ingredient}: {nutrition.calories:.0f} cal, {nutrition.protein:.1f}g protein")
            found_count += 1
        else:
            print(f"❌ {ingredient}: NOT FOUND")
            missing_count += 1
    
    print(f"\nSummary: {found_count} found, {missing_count} missing")
    
    # Test the nutrition engine with a sample meal
    print("\n" + "=" * 50)
    print("🧪 TESTING NUTRITION ENGINE WITH SAMPLE MEAL")
    print("=" * 50)
    
    engine = get_nutrition_engine()
    
    # Sample meal data that might come from LLM
    sample_meal = {
        "name": "High-Protein Greek Yogurt Power Bowl",
        "ingredients": [
            {"name": "Greek yogurt (plain)", "quantity": 200, "unit": "g"},
            {"name": "protein powder (vanilla)", "quantity": 30, "unit": "g"},
            {"name": "mixed berries", "quantity": 100, "unit": "g"},
            {"name": "almonds (sliced)", "quantity": 20, "unit": "g"},
            {"name": "chia seeds", "quantity": 10, "unit": "g"},
            {"name": "honey", "quantity": 15, "unit": "g"}
        ],
        "instructions": "Mix and enjoy",
        "meal_type": "breakfast"
    }
    
    print(f"Sample meal: {sample_meal['name']}")
    print("Ingredients:")
    for ing in sample_meal['ingredients']:
        print(f"  - {ing['name']}: {ing['quantity']}{ing['unit']}")
    
    try:
        meal = engine.calculate_meal_nutrition(
            meal_name=sample_meal['name'],
            ingredients_list=sample_meal['ingredients'],
            instructions=sample_meal['instructions'],
            meal_type=sample_meal['meal_type']
        )
        
        print(f"\n✅ MEAL NUTRITION CALCULATED:")
        print(f"   Calories: {meal.nutrition.calories:.1f}")
        print(f"   Protein: {meal.nutrition.protein:.1f}g")
        print(f"   Carbs: {meal.nutrition.carbohydrates:.1f}g")
        print(f"   Fat: {meal.nutrition.fat:.1f}g")
        print(f"   Fiber: {meal.nutrition.fiber:.1f}g")
        
        print(f"\n📋 INGREDIENT BREAKDOWN:")
        for ingredient in meal.ingredients:
            if ingredient.nutrition:
                print(f"   {ingredient.name}: {ingredient.nutrition.calories:.0f} cal, {ingredient.nutrition.protein:.1f}g protein")
            else:
                print(f"   {ingredient.name}: NO NUTRITION DATA")
        
    except Exception as e:
        print(f"❌ ERROR calculating meal nutrition: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_nutrition_lookups()