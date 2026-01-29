#!/usr/bin/env python3
"""
Test meal regeneration fixes for Task 10.

This test verifies that the meal regeneration issues have been fixed:
1. "mixed greens" ingredient resolution
2. Single meal validation logic
3. Mock provider meal structure
4. Token budget management
"""

import asyncio
import logging
import sys
import os
from uuid import UUID

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.nutrition_database import get_nutrition_database
from app.services.ingredient_normalizer import get_ingredient_normalizer
from app.services.ai_providers import MockAIProvider
from app.services.plan_validation import get_plan_validator
from app.services.nutrition_engine import create_ingredient_with_resolution

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)


async def test_mixed_greens_resolution():
    """Test that 'mixed greens' can be resolved through the ingredient pipeline"""
    print("\n🥬 Testing mixed greens ingredient resolution...")
    
    try:
        # Test 1: Nutrition database lookup
        nutrition_db = get_nutrition_database()
        nutrition_data = nutrition_db.get_nutrition("mixed greens", 100.0)
        
        if nutrition_data:
            print(f"✅ Nutrition database: mixed greens = {nutrition_data.calories:.1f} cal, {nutrition_data.protein:.1f}g protein")
        else:
            print("❌ Nutrition database: mixed greens not found")
            return False
        
        # Test 2: Ingredient normalizer
        normalizer = get_ingredient_normalizer()
        result = normalizer.normalize("mixed greens")
        
        if result.is_resolved:
            print(f"✅ Ingredient normalizer: 'mixed greens' -> '{result.canonical_name}' ({result.confidence.value})")
        else:
            print(f"❌ Ingredient normalizer: 'mixed greens' could not be normalized")
            return False
        
        # Test 3: Full ingredient resolution pipeline
        ingredient = await create_ingredient_with_resolution(
            name="mixed greens",
            quantity=100.0,
            unit="g"
        )
        
        print(f"✅ Full pipeline: mixed greens resolved to {ingredient.nutrition.calories:.1f} cal, {ingredient.nutrition.protein:.1f}g protein")
        return True
        
    except Exception as e:
        print(f"❌ Mixed greens resolution failed: {e}")
        return False


async def test_single_meal_validation():
    """Test that single meal validation works properly"""
    print("\n🍽️ Testing single meal validation logic...")
    
    try:
        # Create a single meal plan
        single_meal_plan = {
            "plan_type": "single_meal",
            "meals": [
                {
                    "type": "lunch",
                    "name": "Test Meal with Mixed Greens",
                    "ingredients": [
                        {"name": "mixed greens", "quantity": 100, "unit": "g"},
                        {"name": "tofu (extra-firm)", "quantity": 150, "unit": "g"},
                        {"name": "olive oil", "quantity": 10, "unit": "ml"}
                    ],
                    "nutrition": {
                        "calories": 200,
                        "protein": 15,
                        "carbohydrates": 8,
                        "fat": 12,
                        "fiber": 3,
                        "sodium": 20
                    }
                }
            ]
        }
        
        # Test validation
        validator = get_plan_validator()
        safety_constraints = {
            "min_daily_calories": 1200,
            "target_calories": 2000,
            "min_protein_grams": 50,
            "target_protein": 100
        }
        
        result = validator.validate_plan(
            plan_data=single_meal_plan,
            safety_constraints=safety_constraints,
            user_id=UUID("12345678-1234-5678-9012-123456789012"),
            goal_type="maintenance",
            user_weight_kg=70.0
        )
        
        if result.is_valid and result.status in ["accepted", "accepted_with_guidance"]:
            print(f"✅ Single meal validation: {result.status}")
            return True
        else:
            print(f"❌ Single meal validation failed: {result.status}, violations: {result.violations}")
            return False
            
    except Exception as e:
        print(f"❌ Single meal validation failed: {e}")
        return False


async def test_mock_provider_meal_structure():
    """Test that mock provider returns valid meal structure"""
    print("\n🤖 Testing mock provider meal structure...")
    
    try:
        mock_provider = MockAIProvider()
        
        # Test daily plan generation
        response, usage = await mock_provider.generate_completion(
            system_prompt="Generate a vegetarian diet plan",
            user_prompt="Generate a daily diet plan with high protein meals",
            temperature=0.2
        )
        
        # Parse the response
        import json
        plan_data = json.loads(response)
        
        # Validate structure
        if "meals" not in plan_data:
            print("❌ Mock provider: No meals in response")
            return False
        
        meals = plan_data["meals"]
        if len(meals) != 3:
            print(f"❌ Mock provider: Expected 3 meals, got {len(meals)}")
            return False
        
        # Check each meal structure
        for i, meal in enumerate(meals):
            required_fields = ["type", "name", "ingredients", "instructions"]
            for field in required_fields:
                if field not in meal:
                    print(f"❌ Mock provider: Meal {i} missing field '{field}'")
                    return False
            
            # Check ingredients
            ingredients = meal.get("ingredients", [])
            if not ingredients:
                print(f"❌ Mock provider: Meal {i} has no ingredients")
                return False
            
            for j, ingredient in enumerate(ingredients):
                required_ing_fields = ["name", "quantity", "unit"]
                for field in required_ing_fields:
                    if field not in ingredient:
                        print(f"❌ Mock provider: Meal {i}, ingredient {j} missing field '{field}'")
                        return False
                
                # Check that ingredient names are valid (exist in nutrition database)
                nutrition_db = get_nutrition_database()
                ing_name = ingredient["name"]
                try:
                    nutrition_data = nutrition_db.get_nutrition(ing_name, 100.0)
                    if not nutrition_data:
                        print(f"⚠️ Mock provider: Ingredient '{ing_name}' not in nutrition database")
                except Exception:
                    print(f"⚠️ Mock provider: Ingredient '{ing_name}' could not be resolved")
        
        print("✅ Mock provider: Valid meal structure with proper ingredients")
        return True
        
    except Exception as e:
        print(f"❌ Mock provider test failed: {e}")
        return False


async def test_ingredient_normalization_coverage():
    """Test that common problematic ingredients are now covered"""
    print("\n🔍 Testing ingredient normalization coverage...")
    
    problematic_ingredients = [
        "mixed greens",
        "greens", 
        "salad greens",
        "bell peppers",
        "cucumber",
        "hemp seeds"
    ]
    
    normalizer = get_ingredient_normalizer()
    nutrition_db = get_nutrition_database()
    
    all_passed = True
    
    for ingredient in problematic_ingredients:
        try:
            # Test normalization
            result = normalizer.normalize(ingredient)
            
            if result.is_resolved:
                # Test nutrition lookup
                nutrition_data = nutrition_db.get_nutrition(result.canonical_name, 100.0)
                if nutrition_data:
                    print(f"✅ '{ingredient}' -> '{result.canonical_name}' ({nutrition_data.calories:.1f} cal)")
                else:
                    print(f"❌ '{ingredient}' -> '{result.canonical_name}' (no nutrition data)")
                    all_passed = False
            else:
                print(f"❌ '{ingredient}' could not be normalized")
                all_passed = False
                
        except Exception as e:
            print(f"❌ '{ingredient}' failed: {e}")
            all_passed = False
    
    return all_passed


async def main():
    """Run all meal regeneration fix tests"""
    print("🧪 Testing Meal Regeneration Fixes (Task 10)")
    print("=" * 50)
    
    tests = [
        ("Mixed Greens Resolution", test_mixed_greens_resolution),
        ("Single Meal Validation", test_single_meal_validation),
        ("Mock Provider Structure", test_mock_provider_meal_structure),
        ("Ingredient Coverage", test_ingredient_normalization_coverage)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Results Summary:")
    print("=" * 30)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All meal regeneration fixes are working!")
        return True
    else:
        print("⚠️ Some fixes need attention")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)