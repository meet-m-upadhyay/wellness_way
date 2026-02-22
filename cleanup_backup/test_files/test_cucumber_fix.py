#!/usr/bin/env python3
"""
Test Cucumber Fix - Verify that cucumber ingredient is now properly resolved
"""

import asyncio
from app.services.nutrition_engine import create_ingredient_with_resolution
from app.services.ingredient_normalizer import get_ingredient_normalizer
from app.services.nutrition_database import get_nutrition_database
from app.services.ingredient_classifier import IngredientClassifier

def test_cucumber_classification():
    """Test that cucumber is properly classified"""
    print("=== Testing Cucumber Classification ===")
    
    classifier = IngredientClassifier()
    result = classifier.classify_ingredient('cucumber')
    
    print(f"Classification result:")
    print(f"  Category: {result.category}")
    print(f"  Vegetarian compliant: {result.is_vegetarian_compliant}")
    print(f"  Vegan compliant: {result.is_vegan_compliant}")
    print(f"  Confidence: {result.confidence}")
    
    if result.category.value == "plant" and result.is_vegetarian_compliant and result.is_vegan_compliant:
        print("✅ Cucumber classification working")
        return True
    else:
        print("❌ Cucumber classification failed")
        return False

def test_cucumber_normalization():
    """Test that cucumber is properly normalized"""
    print("\n=== Testing Cucumber Normalization ===")
    
    normalizer = get_ingredient_normalizer()
    
    try:
        result = normalizer.normalize('cucumber')
        print(f"Normalization result:")
        print(f"  Canonical name: {result.canonical_name}")
        print(f"  Confidence: {result.confidence}")
        
        if result.canonical_name == "cucumber" and result.confidence.value == "exact":
            print("✅ Cucumber normalization working")
            return True
        else:
            print("❌ Cucumber normalization failed")
            return False
    except Exception as e:
        print(f"❌ Cucumber normalization failed: {e}")
        return False

def test_cucumber_nutrition_lookup():
    """Test that cucumber nutrition data exists"""
    print("\n=== Testing Cucumber Nutrition Lookup ===")
    
    db = get_nutrition_database()
    
    try:
        nutrition = db.get_nutrition('cucumber', 100)
        print(f"Nutrition data (per 100g):")
        print(f"  Calories: {nutrition.calories}")
        print(f"  Protein: {nutrition.protein}g")
        print(f"  Carbs: {nutrition.carbohydrates}g")
        print(f"  Fat: {nutrition.fat}g")
        
        if nutrition.calories > 0:
            print("✅ Cucumber nutrition lookup working")
            return True
        else:
            print("❌ Cucumber nutrition lookup failed - zero calories")
            return False
    except Exception as e:
        print(f"❌ Cucumber nutrition lookup failed: {e}")
        return False

async def test_cucumber_ingredient_resolution():
    """Test full ingredient resolution pipeline"""
    print("\n=== Testing Cucumber Ingredient Resolution ===")
    
    try:
        ingredient = await create_ingredient_with_resolution(
            name='cucumber',
            quantity=150,  # 150g cucumber
            unit='g'
        )
        
        print(f"Ingredient resolution result:")
        print(f"  Name: {ingredient.name}")
        print(f"  Quantity: {ingredient.quantity}g")
        print(f"  Resolved: {ingredient.resolved}")
        print(f"  Resolution status: {ingredient.resolution_status}")
        
        if ingredient.nutrition:
            print(f"  Nutrition (150g):")
            print(f"    Calories: {ingredient.nutrition.calories}")
            print(f"    Protein: {ingredient.nutrition.protein}g")
        
        if ingredient.resolved and ingredient.nutrition and ingredient.nutrition.calories > 0:
            print("✅ Cucumber ingredient resolution working")
            return True
        else:
            print("❌ Cucumber ingredient resolution failed")
            return False
    except Exception as e:
        print(f"❌ Cucumber ingredient resolution failed: {e}")
        return False

async def test_cucumber_in_meal():
    """Test cucumber in a complete meal"""
    print("\n=== Testing Cucumber in Meal ===")
    
    from app.services.nutrition_engine import get_nutrition_engine
    
    try:
        engine = get_nutrition_engine()
        
        # Create a meal with cucumber
        meal = await engine.create_meal_with_resolution(
            meal_name="Fresh Salad",
            ingredients_list=[
                {"name": "cucumber", "quantity": 100, "unit": "g"},
                {"name": "tomatoes", "quantity": 100, "unit": "g"},
                {"name": "spinach", "quantity": 50, "unit": "g"}
            ],
            instructions="Mix all vegetables together",
            meal_type="lunch"
        )
        
        print(f"Meal creation result:")
        print(f"  Name: {meal.name}")
        print(f"  Ingredients: {len(meal.ingredients)}")
        print(f"  Total calories: {meal.nutrition.calories}")
        print(f"  Total protein: {meal.nutrition.protein}g")
        
        # Check that cucumber is included
        cucumber_found = any(ing.name == "cucumber" for ing in meal.ingredients)
        
        if cucumber_found and meal.nutrition.calories > 0:
            print("✅ Cucumber in meal working")
            return True
        else:
            print("❌ Cucumber in meal failed")
            return False
    except Exception as e:
        print(f"❌ Cucumber in meal failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all cucumber tests"""
    print("Testing cucumber fix...\n")
    
    results = []
    results.append(test_cucumber_classification())
    results.append(test_cucumber_normalization())
    results.append(test_cucumber_nutrition_lookup())
    results.append(await test_cucumber_ingredient_resolution())
    results.append(await test_cucumber_in_meal())
    
    print(f"\n=== SUMMARY ===")
    print(f"Tests passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("🎉 Cucumber fix is working correctly!")
        print("The 'Unknown ingredient category: cucumber' error should be resolved.")
        return True
    else:
        print("❌ Some cucumber tests failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    if not success:
        exit(1)