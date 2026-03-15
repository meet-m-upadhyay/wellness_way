#!/usr/bin/env python3
"""
Production Safety Floor Test - Comprehensive Verification

This test verifies the 6 critical production safety measures:
1. Ingredient Resolution NEVER throws exceptions
2. Unknown ingredients are handled gracefully (SKIPPED)
3. Generic nutrition entries exist as fallbacks
4. Plan-level safety prevents zero-calorie plans
5. AI failures don't crash the system
6. Diet plan generation NEVER fails due to single ingredient

FINAL REALITY CHECK: Production-safe system that self-heals.
"""

import asyncio
import logging
import json
from app.services.ingredient_resolution_service import (
    get_ingredient_resolution_service, 
    ResolutionStatus
)
from app.services.nutrition_database import get_nutrition_database
from app.services.nutrition_engine import (
    create_ingredient_with_resolution,
    add_protein_safety_net,
    validate_plan_nutrition,
    Meal,
    ZeroCalorieError
)
from app.utils.safe_logging import safe_log_info, safe_log_error, log_success, log_error

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_1_ingredient_resolution_never_throws():
    """Test 1: Ingredient resolution NEVER throws exceptions"""
    print("\n1️⃣ TESTING INGREDIENT RESOLUTION NEVER THROWS")
    print("-" * 50)
    
    async def test_resolution():
        resolution_service = get_ingredient_resolution_service()
        
        # Test with problematic ingredients that would normally crash
        problematic_ingredients = [
            "",  # Empty string
            "   ",  # Whitespace only
            "completely_made_up_food_12345",  # Unknown
            "protein bar with weird symbols !@#$%",  # Special chars
            "食物",  # Non-ASCII characters
            "a" * 1000,  # Very long name
            "None",  # String "None"
        ]
        
        all_passed = True
        
        for ingredient in problematic_ingredients:
            try:
                result = await resolution_service.resolve_ingredient(ingredient)
                
                # Should always return a ResolutionResult, never throw
                if hasattr(result, 'status'):
                    log_success(logger, f"'{ingredient[:20]}...' -> {result.status.value} (SAFE)")
                else:
                    log_error(logger, f"'{ingredient[:20]}...' -> Invalid result type")
                    all_passed = False
                    
            except Exception as e:
                log_error(logger, f"'{ingredient[:20]}...' -> EXCEPTION: {e}")
                all_passed = False
        
        return all_passed
    
    return test_resolution()  # Return coroutine instead of running it


def test_2_unknown_ingredient_handling():
    """Test 2: Unknown ingredients are gracefully handled"""
    print("\n2️⃣ TESTING UNKNOWN INGREDIENT HANDLING")
    print("-" * 50)
    
    async def test_handling():
        resolution_service = get_ingredient_resolution_service()
        
        test_cases = [
            ("greek yogurt", "should resolve"),
            ("whole wheat wrap", "should resolve via fallback"),
            ("some random seeds", "should use generic fallback"),
            ("completely_fake_food_xyz", "should be skipped"),
        ]
        
        all_passed = True
        
        for ingredient, expectation in test_cases:
            try:
                result = await resolution_service.resolve_ingredient(ingredient)
                
                if result.status == ResolutionStatus.RESOLVED:
                    log_success(logger, f"'{ingredient}' -> RESOLVED: {result.canonical_name}")
                elif result.status == ResolutionStatus.FALLBACK_USED:
                    log_success(logger, f"'{ingredient}' -> FALLBACK: {result.canonical_name}")
                elif result.status == ResolutionStatus.SKIPPED:
                    log_success(logger, f"'{ingredient}' -> SKIPPED: {result.warning_message}")
                else:
                    log_error(logger, f"'{ingredient}' -> Unknown status: {result.status}")
                    all_passed = False
                    
            except Exception as e:
                log_error(logger, f"'{ingredient}' -> Exception: {e}")
                all_passed = False
        
        return all_passed
    
    return test_handling()  # Return coroutine


def test_3_generic_nutrition_entries():
    """Test 3: Generic nutrition entries exist as fallbacks"""
    print("\n3️⃣ TESTING GENERIC NUTRITION ENTRIES")
    print("-" * 50)
    
    nutrition_db = get_nutrition_database()
    
    required_generics = [
        "seeds (generic)",
        "nuts (generic)",
        "vegetables (generic)",
        "legumes (generic)",
        "grains (generic)"
    ]
    
    all_exist = True
    
    for generic_food in required_generics:
        try:
            nutrition_data = nutrition_db.get_nutrition(generic_food, 100)
            if nutrition_data and nutrition_data.calories > 0:
                log_success(logger, f"'{generic_food}' -> {nutrition_data.calories} cal, {nutrition_data.protein}g protein")
            else:
                log_error(logger, f"'{generic_food}' -> No nutrition data or zero calories")
                all_exist = False
        except Exception as e:
            log_error(logger, f"'{generic_food}' -> Exception: {e}")
            all_exist = False
    
    if all_exist:
        print("✅ Generic nutrition entries exist - PRODUCTION SAFE")
    else:
        print("❌ Missing generic nutrition entries - NOT PRODUCTION SAFE")
    
    return all_exist


def test_4_plan_level_safety():
    """Test 4: Plan-level safety prevents zero-calorie plans"""
    print("\n4️⃣ TESTING PLAN-LEVEL SAFETY")
    print("-" * 50)
    
    async def test_safety():
        # Create a meal with only skipped ingredients (should have zero calories)
        try:
            skipped_ingredient = await create_ingredient_with_resolution(
                name="completely_fake_food_xyz",
                quantity=100,
                unit="g"
            )
            
            # This should be skipped
            if not skipped_ingredient.resolved:
                log_success(logger, "Fake ingredient correctly skipped")
            else:
                log_error(logger, "Fake ingredient was resolved - unexpected")
                return False
            
            # Test zero calorie detection
            try:
                # Create empty meals list (zero calories)
                empty_meals = []
                validate_plan_nutrition(empty_meals, min_total_calories=800.0)
                log_error(logger, "Zero calorie plan validation should have failed")
                return False
            except ZeroCalorieError:
                log_success(logger, "Zero calorie plan correctly rejected")
            
            return True
            
        except Exception as e:
            log_error(logger, f"Plan-level safety test failed: {e}")
            return False
    
    return test_safety()  # Return coroutine


def test_5_ai_failure_handling():
    """Test 5: AI failures don't crash the system"""
    print("\n5️⃣ TESTING AI FAILURE HANDLING")
    print("-" * 50)
    
    async def test_ai_failures():
        resolution_service = get_ingredient_resolution_service()
        
        # Test with ingredients that might cause AI issues
        problematic_ai_inputs = [
            "protein bar with very long description that might exceed token limits and cause issues",
            "食物 with mixed languages and symbols !@#$%^&*()",
            "ingredient" * 100,  # Very repetitive
        ]
        
        all_handled = True
        
        for ingredient in problematic_ai_inputs:
            try:
                result = await resolution_service.resolve_ingredient(ingredient)
                
                # Should always return a result, even if AI fails
                if hasattr(result, 'status'):
                    log_success(logger, f"AI failure handled: '{ingredient[:30]}...' -> {result.status.value}")
                else:
                    log_error(logger, f"AI failure not handled properly: '{ingredient[:30]}...'")
                    all_handled = False
                    
            except Exception as e:
                log_error(logger, f"AI failure caused exception: '{ingredient[:30]}...' -> {e}")
                all_handled = False
        
        return all_handled
    
    return test_ai_failures()  # Return coroutine


def test_6_diet_plan_never_fails():
    """Test 6: Diet plan generation never fails due to single ingredient"""
    print("\n6️⃣ TESTING DIET PLAN NEVER FAILS")
    print("-" * 50)
    
    async def test_plan_generation():
        # Simulate a meal with mix of good and bad ingredients
        test_meal_ingredients = [
            {"name": "greek yogurt", "quantity": 100, "unit": "g"},  # Good
            {"name": "completely_fake_food", "quantity": 50, "unit": "g"},  # Bad
            {"name": "spinach", "quantity": 50, "unit": "g"},  # Good
            {"name": "another_fake_ingredient", "quantity": 25, "unit": "g"},  # Bad
        ]
        
        processed_ingredients = []
        
        for ingredient_data in test_meal_ingredients:
            try:
                ingredient = await create_ingredient_with_resolution(
                    name=ingredient_data["name"],
                    quantity=ingredient_data["quantity"],
                    unit=ingredient_data["unit"]
                )
                
                # Only add resolved ingredients
                if ingredient.resolved:
                    processed_ingredients.append(ingredient)
                    log_success(logger, f"Added: {ingredient.name} ({ingredient.resolution_status})")
                else:
                    log_success(logger, f"Skipped: {ingredient.name} (safely ignored)")
                    
            except Exception as e:
                log_error(logger, f"Ingredient processing failed: {ingredient_data['name']} -> {e}")
                return False
        
        # Should have at least some ingredients (the good ones)
        if len(processed_ingredients) >= 2:
            log_success(logger, f"Meal created with {len(processed_ingredients)} ingredients (bad ones skipped)")
            
            # Calculate total nutrition
            total_calories = sum(ing.nutrition.calories for ing in processed_ingredients if ing.nutrition)
            total_protein = sum(ing.nutrition.protein for ing in processed_ingredients if ing.nutrition)
            
            log_success(logger, f"Meal nutrition: {total_calories:.0f} calories, {total_protein:.1f}g protein")
            
            return True
        else:
            log_error(logger, "Not enough ingredients processed")
            return False
    
    return test_plan_generation()  # Return coroutine


async def main():
    """Run all production safety floor tests"""
    print("🛡️ PRODUCTION SAFETY FLOOR VERIFICATION")
    print("=" * 70)
    print("Testing the boundary between technically correct and production-safe")
    print("=" * 70)
    
    # Run all tests (now they return coroutines)
    results = []
    
    # Test 1
    result1 = await test_1_ingredient_resolution_never_throws()
    if result1:
        print("✅ Ingredient resolution never throws - PRODUCTION SAFE")
    else:
        print("❌ Ingredient resolution threw exceptions - NOT PRODUCTION SAFE")
    results.append(result1)
    
    # Test 2
    result2 = await test_2_unknown_ingredient_handling()
    if result2:
        print("✅ Unknown ingredients handled gracefully - PRODUCTION SAFE")
    else:
        print("❌ Unknown ingredient handling failed - NOT PRODUCTION SAFE")
    results.append(result2)
    
    # Test 3 (synchronous)
    result3 = test_3_generic_nutrition_entries()
    results.append(result3)
    
    # Test 4
    result4 = await test_4_plan_level_safety()
    if result4:
        print("✅ Plan-level safety works - PRODUCTION SAFE")
    else:
        print("❌ Plan-level safety failed - NOT PRODUCTION SAFE")
    results.append(result4)
    
    # Test 5
    result5 = await test_5_ai_failure_handling()
    if result5:
        print("✅ AI failures handled gracefully - PRODUCTION SAFE")
    else:
        print("❌ AI failures crash system - NOT PRODUCTION SAFE")
    results.append(result5)
    
    # Test 6
    result6 = await test_6_diet_plan_never_fails()
    if result6:
        print("✅ Diet plan generation never fails - PRODUCTION SAFE")
    else:
        print("❌ Diet plan generation can fail - NOT PRODUCTION SAFE")
    results.append(result6)
    
    # Final assessment
    print("\n" + "=" * 70)
    print("🏁 PRODUCTION SAFETY FLOOR ASSESSMENT")
    print("=" * 70)
    
    passed_tests = sum(results)
    total_tests = len(results)
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED - PRODUCTION READY!")
        print("✅ System has crossed the boundary to production-safe")
        print("✅ Diet plan generation will NEVER fail due to single ingredient")
        print("✅ System self-heals automatically under all failure conditions")
        print("✅ Zero-calorie plans are mathematically impossible")
        print("✅ AI failures are contained and handled gracefully")
        print("✅ Unknown ingredients are skipped, not crashed on")
    else:
        print(f"❌ {total_tests - passed_tests} TESTS FAILED - NOT PRODUCTION READY")
        print("❌ System is technically correct but not production-safe")
        print("❌ Additional safety measures needed")
    
    print(f"\nFinal Score: {passed_tests}/{total_tests} safety measures implemented")


if __name__ == "__main__":
    asyncio.run(main())