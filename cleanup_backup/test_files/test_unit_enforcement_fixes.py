#!/usr/bin/env python3
"""
Test Unit Enforcement + Low-Calorie Meal Guardrails (Task 8)

This test verifies the four precision fixes:
1. Egg "pc" unit normalization for eggs only
2. Meals with <200 kcal should never pass creation
3. Per-meal protein minimum of 25g
4. Remove emojis from backend logs (ASCII safety)
"""

import asyncio
import logging
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.services.unit_enforcement import get_unit_enforcer, ContractViolationError
from app.services.nutrition_engine import (
    get_nutrition_engine, create_ingredient_with_resolution, 
    RetryableMealGenerationError, NutritionCalculationError
)

# Configure logging to see the ASCII replacements
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)


def test_egg_unit_normalization():
    """Test Fix 1: Egg 'pc' unit normalization for eggs only"""
    print("\n=== TEST 1: Egg 'pc' Unit Normalization ===")
    
    unit_enforcer = get_unit_enforcer()
    
    # Test case 1: Egg with "pc" unit should be converted to grams
    egg_ingredient = {
        "name": "egg",
        "quantity": 2,
        "unit": "pc"
    }
    
    try:
        result = unit_enforcer._enforce_single_ingredient(egg_ingredient)
        expected_weight = 2 * 60.0  # 2 eggs * 60g each = 120g
        
        if result["quantity"] == expected_weight and result["unit"] == "g":
            print(f"[OK] Egg conversion: 2 pc -> {result['quantity']}g")
        else:
            print(f"[FAIL] Egg conversion failed: got {result['quantity']}{result['unit']}")
            return False
    except Exception as e:
        print(f"[FAIL] Egg conversion threw exception: {e}")
        return False
    
    # Test case 2: Non-egg ingredient with "pc" should NOT be converted using egg logic
    apple_ingredient = {
        "name": "apple",
        "quantity": 1,
        "unit": "pc"
    }
    
    try:
        result = unit_enforcer._enforce_single_ingredient(apple_ingredient)
        # Apple should use discrete mapping, not egg conversion
        if result["quantity"] != 60.0:  # Egg weight
            print(f"[OK] Apple with pc unit handled correctly: {result['quantity']}g")
        else:
            print(f"[FAIL] Apple incorrectly used egg conversion")
            return False
    except Exception as e:
        print(f"[OK] Apple with pc unit handled (may throw exception for unknown mapping): {e}")
    
    print("[OK] Egg unit normalization test passed")
    return True


async def test_meal_calorie_guardrail():
    """Test Fix 2: Meals with <200 kcal should never pass creation"""
    print("\n=== TEST 2: Meal Calorie Guardrail ===")
    
    nutrition_engine = get_nutrition_engine()
    
    # Create a very low-calorie meal that should trigger the guardrail
    low_cal_ingredients = [
        {"name": "spinach", "quantity": 50, "unit": "g"},  # Very low calorie
        {"name": "bell pepper", "quantity": 30, "unit": "g"}  # Very low calorie
    ]
    
    try:
        meal = await nutrition_engine.create_meal_with_resolution(
            meal_name="Low Calorie Test Meal",
            ingredients_list=low_cal_ingredients,
            instructions="Mix ingredients",
            meal_type="test"
        )
        print(f"[FAIL] Low calorie meal was allowed: {meal.nutrition.calories} kcal")
        return False
    except RetryableMealGenerationError as e:
        if "CALORIE GUARDRAIL VIOLATION" in str(e):
            print(f"[OK] Meal calorie guardrail triggered: {e}")
            return True
        else:
            print(f"[FAIL] Wrong exception type: {e}")
            return False
    except Exception as e:
        print(f"[FAIL] Unexpected exception: {e}")
        return False


async def test_meal_protein_guardrail():
    """Test Fix 3: Per-meal protein minimum of 25g"""
    print("\n=== TEST 3: Meal Protein Guardrail ===")
    
    nutrition_engine = get_nutrition_engine()
    
    # Create a low-protein meal that should trigger the guardrail
    low_protein_ingredients = [
        {"name": "rice (cooked)", "quantity": 200, "unit": "g"},  # High calorie, low protein
        {"name": "olive oil", "quantity": 10, "unit": "g"}  # High calorie, no protein
    ]
    
    try:
        meal = await nutrition_engine.create_meal_with_resolution(
            meal_name="Low Protein Test Meal",
            ingredients_list=low_protein_ingredients,
            instructions="Mix ingredients",
            meal_type="test"
        )
        print(f"[FAIL] Low protein meal was allowed: {meal.nutrition.protein}g protein")
        return False
    except RetryableMealGenerationError as e:
        if "PROTEIN GUARDRAIL VIOLATION" in str(e):
            print(f"[OK] Meal protein guardrail triggered: {e}")
            return True
        else:
            print(f"[FAIL] Wrong exception type: {e}")
            return False
    except Exception as e:
        print(f"[FAIL] Unexpected exception: {e}")
        return False


def test_ascii_logging():
    """Test Fix 4: Remove emojis from backend logs (ASCII safety)"""
    print("\n=== TEST 4: ASCII Logging ===")
    
    # This test checks that the code changes were made
    # The actual logging will be visible in the other tests
    
    # Check unit_enforcement.py
    with open('app/services/unit_enforcement.py', 'r', encoding='utf-8') as f:
        unit_content = f.read()
    
    if '✅' in unit_content or '🔒' in unit_content or '⚠️' in unit_content:
        print("[FAIL] Emojis still found in unit_enforcement.py")
        return False
    
    # Check nutrition_engine.py
    with open('app/services/nutrition_engine.py', 'r', encoding='utf-8') as f:
        nutrition_content = f.read()
    
    if '✅' in nutrition_content or '🔒' in nutrition_content or '⚠️' in nutrition_content:
        print("[FAIL] Emojis still found in nutrition_engine.py")
        return False
    
    # Check ai_service.py
    with open('app/services/ai_service.py', 'r', encoding='utf-8') as f:
        ai_content = f.read()
    
    if '✅' in ai_content:
        print("[FAIL] Emojis still found in ai_service.py")
        return False
    
    print("[OK] ASCII logging test passed - no emojis found in main service files")
    return True


async def test_high_quality_meal_passes():
    """Test that high-quality meals still pass all guardrails"""
    print("\n=== TEST 5: High-Quality Meal Passes ===")
    
    nutrition_engine = get_nutrition_engine()
    
    # Create a high-quality meal that should pass all guardrails
    good_ingredients = [
        {"name": "tofu (extra-firm)", "quantity": 150, "unit": "g"},  # High protein
        {"name": "quinoa (cooked)", "quantity": 100, "unit": "g"},   # Good carbs + protein
        {"name": "spinach", "quantity": 100, "unit": "g"},          # Nutrients
        {"name": "olive oil", "quantity": 10, "unit": "g"}          # Healthy fats
    ]
    
    try:
        meal = await nutrition_engine.create_meal_with_resolution(
            meal_name="High Quality Test Meal",
            ingredients_list=good_ingredients,
            instructions="Cook and mix ingredients",
            meal_type="test"
        )
        
        if meal.nutrition.calories >= 200 and meal.nutrition.protein >= 25:
            print(f"[OK] High-quality meal passed: {meal.nutrition.calories:.1f} kcal, {meal.nutrition.protein:.1f}g protein")
            return True
        else:
            print(f"[FAIL] High-quality meal didn't meet thresholds: {meal.nutrition.calories:.1f} kcal, {meal.nutrition.protein:.1f}g protein")
            return False
    except Exception as e:
        print(f"[FAIL] High-quality meal threw exception: {e}")
        return False


async def main():
    """Run all tests"""
    print("UNIT ENFORCEMENT + LOW-CALORIE MEAL GUARDRAILS TEST")
    print("=" * 60)
    
    tests = [
        ("Egg Unit Normalization", test_egg_unit_normalization()),
        ("Meal Calorie Guardrail", test_meal_calorie_guardrail()),
        ("Meal Protein Guardrail", test_meal_protein_guardrail()),
        ("ASCII Logging", test_ascii_logging()),
        ("High-Quality Meal Passes", test_high_quality_meal_passes())
    ]
    
    results = []
    for test_name, test_coro in tests:
        try:
            if asyncio.iscoroutine(test_coro):
                result = await test_coro
            else:
                result = test_coro
            results.append((test_name, result))
        except Exception as e:
            print(f"[ERROR] {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY:")
    passed = 0
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)} tests")
    
    if passed == len(results):
        print("\n[SUCCESS] All Unit Enforcement + Meal Guardrail fixes are working!")
        return True
    else:
        print("\n[FAILURE] Some tests failed. Check the implementation.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)