#!/usr/bin/env python3
"""
Integration test for nutrition database with ingredient normalizer.
Tests the complete pipeline: LLM names -> Normalizer -> Nutrition Database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.nutrition_database import get_nutrition_database
from app.services.nutrition_engine import get_nutrition_engine
from app.services.ingredient_normalizer import UnknownIngredientError

def test_nutrition_integration():
    """Test complete nutrition pipeline with LLM-style ingredient names"""
    
    print("🔗 TESTING NUTRITION INTEGRATION PIPELINE")
    print("=" * 50)
    
    db = get_nutrition_database()
    
    # Test LLM-style ingredient names (the ones causing 0-calorie failures)
    llm_style_ingredients = [
        "organic free-range eggs",
        "Greek-style yogurt",
        "extra virgin olive oil", 
        "broccoli florets",
        "baby spinach",
        "cherry tomatoes",
        "vanilla protein powder",
        "chocolate whey protein",
        "plant protein blend",
        "sliced almonds",
        "fresh berries",
        "rolled oats",
        "garbanzo beans",
        "red lentils",
        "brown rice"
    ]
    
    print("✅ SUCCESSFUL NUTRITION LOOKUPS:")
    print("-" * 30)
    
    success_count = 0
    total_calories = 0
    total_protein = 0
    
    for ingredient in llm_style_ingredients:
        try:
            nutrition = db.get_nutrition(ingredient, 100)  # Test with 100g
            print(f"✅ {ingredient}: {nutrition.calories:.0f} cal, {nutrition.protein:.1f}g protein")
            success_count += 1
            total_calories += nutrition.calories
            total_protein += nutrition.protein
        except UnknownIngredientError as e:
            print(f"❌ {ingredient}: NORMALIZATION FAILED - {e}")
        except Exception as e:
            print(f"❌ {ingredient}: UNEXPECTED ERROR - {e}")
    
    print(f"\nSuccess rate: {success_count}/{len(llm_style_ingredients)} ({success_count/len(llm_style_ingredients)*100:.1f}%)")
    print(f"Total nutrition (100g each): {total_calories:.0f} cal, {total_protein:.1f}g protein")
    
    # Test the nutrition engine with LLM-style meal
    print("\n" + "=" * 50)
    print("🧪 TESTING NUTRITION ENGINE WITH LLM-STYLE MEAL")
    print("=" * 50)
    
    engine = get_nutrition_engine()
    
    # LLM-style meal that would previously cause 0-calorie failure
    llm_meal = {
        "name": "High-Protein Breakfast Bowl",
        "ingredients": [
            {"name": "Greek-style yogurt", "quantity": 200, "unit": "g"},
            {"name": "vanilla protein powder", "quantity": 30, "unit": "g"},
            {"name": "fresh berries", "quantity": 100, "unit": "g"},
            {"name": "sliced almonds", "quantity": 20, "unit": "g"},
            {"name": "organic honey", "quantity": 15, "unit": "g"}
        ],
        "instructions": "Mix and enjoy",
        "meal_type": "breakfast"
    }
    
    print(f"LLM-style meal: {llm_meal['name']}")
    print("LLM-generated ingredients:")
    for ing in llm_meal['ingredients']:
        print(f"  - {ing['name']}: {ing['quantity']}{ing['unit']}")
    
    try:
        meal = engine.calculate_meal_nutrition(
            meal_name=llm_meal['name'],
            ingredients_list=llm_meal['ingredients'],
            instructions=llm_meal['instructions'],
            meal_type=llm_meal['meal_type']
        )
        
        print(f"\n✅ MEAL NUTRITION CALCULATED SUCCESSFULLY:")
        print(f"   Calories: {meal.nutrition.calories:.1f}")
        print(f"   Protein: {meal.nutrition.protein:.1f}g")
        print(f"   Carbs: {meal.nutrition.carbohydrates:.1f}g")
        print(f"   Fat: {meal.nutrition.fat:.1f}g")
        
        # Verify no zero nutrition (the critical issue)
        if meal.nutrition.calories > 0 and meal.nutrition.protein > 0:
            print(f"\n🎉 SUCCESS: No zero-calorie nutrition detected!")
            print(f"   This meal would have previously failed with 0 calories/0 protein")
        else:
            print(f"\n🚨 FAILURE: Still getting zero nutrition!")
            print(f"   Calories: {meal.nutrition.calories}, Protein: {meal.nutrition.protein}")
        
        print(f"\n📋 INGREDIENT BREAKDOWN:")
        for ingredient in meal.ingredients:
            if ingredient.nutrition:
                print(f"   {ingredient.name}: {ingredient.nutrition.calories:.0f} cal, {ingredient.nutrition.protein:.1f}g protein")
            else:
                print(f"   {ingredient.name}: NO NUTRITION DATA")
        
    except UnknownIngredientError as e:
        print(f"❌ INGREDIENT NORMALIZATION FAILED: {e}")
        print(f"   Raw: '{e.raw_name}' -> Normalized: '{e.normalized_attempt}'")
        print(f"   This is the exact error that was causing 0-calorie failures!")
        
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    # Test unknown ingredient handling
    print("\n" + "=" * 50)
    print("🚨 TESTING UNKNOWN INGREDIENT HANDLING")
    print("=" * 50)
    
    unknown_meal = {
        "name": "Meal with Unknown Ingredient",
        "ingredients": [
            {"name": "greek yogurt (plain)", "quantity": 200, "unit": "g"},
            {"name": "mysterious superfood xyz", "quantity": 50, "unit": "g"}  # This should fail
        ],
        "instructions": "Test unknown ingredient",
        "meal_type": "test"
    }
    
    try:
        meal = engine.calculate_meal_nutrition(
            meal_name=unknown_meal['name'],
            ingredients_list=unknown_meal['ingredients'],
            instructions=unknown_meal['instructions'],
            meal_type=unknown_meal['meal_type']
        )
        print(f"⚠️ UNEXPECTED: Unknown ingredient was accepted!")
        
    except UnknownIngredientError as e:
        print(f"✅ CORRECT: Unknown ingredient properly rejected")
        print(f"   Error: {e}")
        print(f"   This prevents 0-calorie nutrition from reaching validation")

if __name__ == "__main__":
    test_nutrition_integration()