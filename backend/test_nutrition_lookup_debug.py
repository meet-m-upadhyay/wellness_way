#!/usr/bin/env python3
"""
Debug script to test nutrition lookup and identify why meal nutrition values are zero.

This will test the complete nutrition lookup pipeline:
1. Ingredient name normalization
2. Nutrition database lookup
3. Ingredient creation with resolution
4. Meal nutrition aggregation
"""

import asyncio
import logging
from app.services.nutrition_database import get_nutrition_database
from app.services.ingredient_normalizer import get_ingredient_normalizer
from app.services.ingredient_resolution_service import get_ingredient_resolution_service
from app.services.nutrition_engine import create_ingredient_with_resolution, Meal

# Configure logging to see all details
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)

async def test_nutrition_lookup_pipeline():
    """Test the complete nutrition lookup pipeline"""
    
    print("🔍 TESTING NUTRITION LOOKUP PIPELINE")
    print("=" * 80)
    
    # Test ingredients from canonicalization (these should be canonical already)
    test_ingredients = [
        {"name": "quinoa (dry)", "quantity": 60, "unit": "g"},
        {"name": "lentils (green, dry)", "quantity": 100, "unit": "g"},
        {"name": "broccoli", "quantity": 89, "unit": "g"},
        {"name": "rice (dry)", "quantity": 40, "unit": "g"},
        {"name": "chicken breast (raw)", "quantity": 200, "unit": "g"},
        {"name": "spinach", "quantity": 200, "unit": "g"},
    ]
    
    # Test 1: Direct nutrition database lookup
    print("\n📊 TEST 1: DIRECT NUTRITION DATABASE LOOKUP")
    print("=" * 60)
    
    nutrition_db = get_nutrition_database()
    
    for ingredient_data in test_ingredients:
        name = ingredient_data["name"]
        quantity = ingredient_data["quantity"]
        
        print(f"\n[NUTRITION_LOOKUP_INPUT] name='{name}' qty={quantity} unit=g")
        
        try:
            nutrition = nutrition_db.get_nutrition(name, quantity)
            if nutrition:
                print(f"[NUTRITION_LOOKUP_RESULT] calories={nutrition.calories:.1f} protein={nutrition.protein:.1f}g")
                if nutrition.calories == 0 and quantity > 0:
                    print(f"[NUTRITION_LOOKUP_MISS] ingredient={name} - ZERO CALORIES DETECTED!")
            else:
                print(f"[NUTRITION_LOOKUP_MISS] ingredient={name} - None returned")
        except Exception as e:
            print(f"[NUTRITION_LOOKUP_ERROR] ingredient={name} - {e}")
    
    # Test 2: Ingredient normalization
    print("\n📊 TEST 2: INGREDIENT NORMALIZATION")
    print("=" * 60)
    
    normalizer = get_ingredient_normalizer()
    
    for ingredient_data in test_ingredients:
        name = ingredient_data["name"]
        
        print(f"\n[NORMALIZATION_INPUT] name='{name}'")
        
        try:
            result = normalizer.normalize(name)
            print(f"[NORMALIZATION_RESULT] canonical='{result.canonical_name}' confidence={result.confidence.value}")
        except Exception as e:
            print(f"[NORMALIZATION_ERROR] ingredient={name} - {e}")
    
    # Test 3: Ingredient resolution service
    print("\n📊 TEST 3: INGREDIENT RESOLUTION SERVICE")
    print("=" * 60)
    
    resolution_service = get_ingredient_resolution_service()
    
    for ingredient_data in test_ingredients:
        name = ingredient_data["name"]
        
        print(f"\n[RESOLUTION_INPUT] name='{name}'")
        
        try:
            result = await resolution_service.resolve_ingredient(name)
            print(f"[RESOLUTION_RESULT] status={result.status.value} canonical='{result.canonical_name}' confidence={result.confidence}")
        except Exception as e:
            print(f"[RESOLUTION_ERROR] ingredient={name} - {e}")
    
    # Test 4: Create ingredient with resolution
    print("\n📊 TEST 4: CREATE INGREDIENT WITH RESOLUTION")
    print("=" * 60)
    
    resolved_ingredients = []
    
    for ingredient_data in test_ingredients:
        name = ingredient_data["name"]
        quantity = ingredient_data["quantity"]
        unit = ingredient_data["unit"]
        
        print(f"\n[INGREDIENT_CREATION_INPUT] name='{name}' qty={quantity} unit={unit}")
        
        try:
            ingredient = await create_ingredient_with_resolution(name, quantity, unit)
            print(f"[INGREDIENT_CREATION_RESULT] resolved={ingredient.resolved} nutrition_calories={ingredient.nutrition.calories if ingredient.nutrition else 'None'}")
            
            if ingredient.nutrition:
                print(f"    calories={ingredient.nutrition.calories:.1f} protein={ingredient.nutrition.protein:.1f}g")
                if ingredient.nutrition.calories == 0 and quantity > 0:
                    print(f"    ❌ ZERO CALORIES DETECTED for {name}!")
            else:
                print(f"    ❌ NO NUTRITION DATA for {name}!")
            
            resolved_ingredients.append(ingredient)
            
        except Exception as e:
            print(f"[INGREDIENT_CREATION_ERROR] ingredient={name} - {e}")
    
    # Test 5: Meal nutrition aggregation
    print("\n📊 TEST 5: MEAL NUTRITION AGGREGATION")
    print("=" * 60)
    
    if resolved_ingredients:
        try:
            test_meal = Meal(
                name="Test Meal",
                ingredients=resolved_ingredients,
                instructions="Test meal for debugging",
                meal_type="lunch"
            )
            
            nutrition = test_meal.nutrition
            print(f"[MEAL_NUTRITION_RESULT] total_calories={nutrition.calories:.1f} total_protein={nutrition.protein:.1f}g")
            
            if nutrition.calories == 0:
                print("❌ MEAL HAS ZERO CALORIES!")
                print("Individual ingredient nutrition:")
                for ing in resolved_ingredients:
                    if ing.nutrition:
                        print(f"  - {ing.name}: {ing.nutrition.calories:.1f} cal, {ing.nutrition.protein:.1f}g protein")
                    else:
                        print(f"  - {ing.name}: NO NUTRITION DATA")
            else:
                print("✅ Meal has valid nutrition")
                
        except Exception as e:
            print(f"[MEAL_CREATION_ERROR] {e}")
    
    # Test 6: Check nutrition database contents
    print("\n📊 TEST 6: NUTRITION DATABASE CONTENTS CHECK")
    print("=" * 60)
    
    # Check if our canonical names exist in the database
    db_foods = nutrition_db._foods
    print(f"Total foods in database: {len(db_foods)}")
    
    print("\nChecking if our canonical names exist in database:")
    for ingredient_data in test_ingredients:
        name = ingredient_data["name"]
        if name in db_foods:
            nutrition = db_foods[name]
            print(f"  ✅ {name}: {nutrition.calories} cal/100g, {nutrition.protein}g protein/100g")
        else:
            print(f"  ❌ {name}: NOT FOUND in database")
            # Look for similar names
            similar = [key for key in db_foods.keys() if any(word in key for word in name.split())]
            if similar:
                print(f"      Similar names: {similar[:3]}")
    
    print("\n🎯 SUMMARY")
    print("=" * 80)
    print("This test should help identify where the nutrition lookup is failing.")
    print("Look for:")
    print("1. Ingredients not found in nutrition database")
    print("2. Normalization failures")
    print("3. Resolution service issues")
    print("4. Zero nutrition values being returned")

if __name__ == "__main__":
    asyncio.run(test_nutrition_lookup_pipeline())