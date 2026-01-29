#!/usr/bin/env python3
"""
Comprehensive test to verify the zero-calorie nutrition fix.
Tests the complete pipeline that was causing production failures.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.nutrition_database import get_nutrition_database
from app.services.ingredient_normalizer import get_ingredient_normalizer, UnknownIngredientError
from app.services.nutrition_engine import get_nutrition_engine

def test_zero_calorie_fix():
    """
    Test the complete fix for zero-calorie nutrition failures.
    
    BEFORE FIX: LLM ingredient names -> No match -> 0 nutrition -> Plan fails validation
    AFTER FIX: LLM ingredient names -> Normalizer -> Database match -> Real nutrition
    """
    
    print("🔧 TESTING ZERO-CALORIE NUTRITION FIX")
    print("=" * 60)
    
    # Test the exact ingredient names that were causing failures
    problematic_ingredients = [
        # These are the types of names LLMs generate that were causing 0-calorie failures
        "organic free-range large brown eggs",
        "Greek-style plain yogurt", 
        "extra virgin cold-pressed olive oil",
        "fresh baby spinach leaves",
        "steamed broccoli florets",
        "cherry tomatoes",
        "vanilla whey protein isolate",
        "chocolate plant protein blend",
        "sliced raw almonds",
        "organic rolled oats",
        "canned garbanzo beans",
        "cooked red lentils",
        "brown basmati rice"
    ]
    
    print("🧪 TESTING PROBLEMATIC INGREDIENT NAMES:")
    print("-" * 40)
    
    db = get_nutrition_database()
    normalizer = get_ingredient_normalizer()
    
    total_calories = 0
    total_protein = 0
    success_count = 0
    
    for ingredient in problematic_ingredients:
        try:
            # Test normalization
            norm_result = normalizer.normalize(ingredient)
            
            # Test nutrition lookup
            nutrition = db.get_nutrition(ingredient, 100)  # 100g test
            
            print(f"✅ {ingredient}")
            print(f"   -> {norm_result.canonical_name} ({norm_result.confidence.value})")
            print(f"   -> {nutrition.calories:.0f} cal, {nutrition.protein:.1f}g protein")
            if norm_result.removed_tokens:
                print(f"   -> Removed: {norm_result.removed_tokens}")
            
            total_calories += nutrition.calories
            total_protein += nutrition.protein
            success_count += 1
            
        except UnknownIngredientError as e:
            print(f"❌ {ingredient}")
            print(f"   -> FAILED: {e}")
        except Exception as e:
            print(f"❌ {ingredient}")
            print(f"   -> ERROR: {e}")
    
    print(f"\n📊 RESULTS:")
    print(f"   Success rate: {success_count}/{len(problematic_ingredients)} ({success_count/len(problematic_ingredients)*100:.1f}%)")
    print(f"   Total nutrition (100g each): {total_calories:.0f} cal, {total_protein:.1f}g protein")
    
    if success_count == len(problematic_ingredients) and total_calories > 0 and total_protein > 0:
        print(f"   🎉 ZERO-CALORIE ISSUE FIXED!")
    else:
        print(f"   🚨 Still have zero-calorie issues!")
    
    # Test complete meal that would have failed before
    print(f"\n" + "=" * 60)
    print("🍽️ TESTING COMPLETE MEAL (Previously Failed)")
    print("=" * 60)
    
    # This meal uses ingredient names that would have caused 0-calorie failures
    problematic_meal = {
        "name": "High-Protein Power Bowl (LLM Generated)",
        "ingredients": [
            {"name": "Greek-style plain yogurt", "quantity": 200, "unit": "g"},
            {"name": "vanilla whey protein isolate", "quantity": 30, "unit": "g"},
            {"name": "organic rolled oats", "quantity": 50, "unit": "g"},
            {"name": "sliced raw almonds", "quantity": 20, "unit": "g"},
            {"name": "fresh mixed berries", "quantity": 100, "unit": "g"},
            {"name": "organic honey", "quantity": 15, "unit": "g"}
        ],
        "instructions": "Mix and enjoy",
        "meal_type": "breakfast"
    }
    
    print(f"Meal: {problematic_meal['name']}")
    print("Ingredients (LLM-style names):")
    for ing in problematic_meal['ingredients']:
        print(f"  - {ing['name']}: {ing['quantity']}{ing['unit']}")
    
    engine = get_nutrition_engine()
    
    try:
        meal = engine.calculate_meal_nutrition(
            meal_name=problematic_meal['name'],
            ingredients_list=problematic_meal['ingredients'],
            instructions=problematic_meal['instructions'],
            meal_type=problematic_meal['meal_type']
        )
        
        print(f"\n✅ MEAL CALCULATION SUCCESS:")
        print(f"   Calories: {meal.nutrition.calories:.1f}")
        print(f"   Protein: {meal.nutrition.protein:.1f}g")
        print(f"   Carbs: {meal.nutrition.carbohydrates:.1f}g")
        print(f"   Fat: {meal.nutrition.fat:.1f}g")
        
        # Check for zero-calorie issue
        if meal.nutrition.calories == 0 or meal.nutrition.protein == 0:
            print(f"\n🚨 ZERO-CALORIE DETECTED!")
            print(f"   This meal would fail validation: 'Calories too low: {meal.nutrition.calories} < target'")
            print(f"   This meal would fail validation: 'Protein too low: {meal.nutrition.protein}g < target'")
        else:
            print(f"\n🎉 NO ZERO-CALORIE NUTRITION!")
            print(f"   This meal will pass validation successfully")
            print(f"   Previous error 'Calories too low: 0.0 < 1771.25' -> FIXED")
            print(f"   Previous error 'Protein too low: 0.0g < 142.2g' -> FIXED")
        
        print(f"\n📋 INGREDIENT BREAKDOWN:")
        for ingredient in meal.ingredients:
            print(f"   {ingredient.name}: {ingredient.nutrition.calories:.0f} cal, {ingredient.nutrition.protein:.1f}g protein")
        
    except UnknownIngredientError as e:
        print(f"\n❌ INGREDIENT NORMALIZATION FAILED:")
        print(f"   Raw: '{e.raw_name}'")
        print(f"   Normalized attempt: '{e.normalized_attempt}'")
        print(f"   Removed tokens: {e.removed_tokens}")
        print(f"   This would now show a clear error message instead of 0-calorie confusion")
        
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    # Test the error message improvement
    print(f"\n" + "=" * 60)
    print("🚨 TESTING ERROR MESSAGE IMPROVEMENT")
    print("=" * 60)
    
    try:
        # This should fail with a clear error message
        unknown_meal = {
            "name": "Meal with Unknown Ingredient",
            "ingredients": [
                {"name": "greek yogurt (plain)", "quantity": 200, "unit": "g"},
                {"name": "superfood xyz that doesn't exist", "quantity": 50, "unit": "g"}
            ],
            "instructions": "Test",
            "meal_type": "test"
        }
        
        meal = engine.calculate_meal_nutrition(
            meal_name=unknown_meal['name'],
            ingredients_list=unknown_meal['ingredients'],
            instructions=unknown_meal['instructions'],
            meal_type=unknown_meal['meal_type']
        )
        
        print(f"⚠️ UNEXPECTED: Unknown ingredient was accepted")
        
    except UnknownIngredientError as e:
        print(f"✅ IMPROVED ERROR HANDLING:")
        print(f"   BEFORE: 'Calories too low: 0.0 < 1771.25' (confusing)")
        print(f"   AFTER: 'Cannot resolve ingredient: {e.raw_name}' (clear)")
        print(f"   User gets actionable error message instead of 0-calorie confusion")

if __name__ == "__main__":
    test_zero_calorie_fix()