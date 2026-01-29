#!/usr/bin/env python3
"""
Test all the fixes together:
1. JSON repair for malformed LLM responses
2. Soft acceptance logic for plans within 90-95% of target
3. Ingredient contract validation
"""

import json
from app.services.llm_contract_enforcer import enforce_llm_contract, RetryableLLMError
from app.services.plan_validation import DietPlanValidator
from app.services.nutrition_database import get_nutrition_database
from uuid import UUID

def test_json_repair_fix():
    """Test that JSON repair handles unterminated strings"""
    print("=== Testing JSON Repair Fix ===")
    
    # Test the specific malformed JSON from error logs
    malformed_json = '''{\n  "plan_type": "daily",\n  "date": "2024-01-26",\n  "breakfast": {\n    "name": "Greek Yogurt and Hemp Seed Bowl",\n    "ingredients": [\n      {"name": "greek yogurt (plain)", "quantity": 150, "unit": "'''
    
    try:
        parsed = enforce_llm_contract(malformed_json, "test-repair")
        print("✅ JSON repair successful")
        print(f"   Parsed keys: {list(parsed.keys())}")
        
        # Verify structure
        if 'breakfast' in parsed and 'ingredients' in parsed['breakfast']:
            ingredients = parsed['breakfast']['ingredients']
            print(f"   Ingredients array length: {len(ingredients)}")
        
        return True
    except Exception as e:
        print(f"❌ JSON repair failed: {e}")
        return False

def test_soft_acceptance_fix():
    """Test that soft acceptance works for plans within 90-95% of target"""
    print("\n=== Testing Soft Acceptance Fix ===")
    
    validator = DietPlanValidator()
    
    # Create a plan that should trigger soft acceptance (92% of calories, 90% of protein)
    plan_data = {
        "plan_type": "daily",
        "meals": [
            {
                "name": "Test Meal 1",
                "nutrition": {"calories": 550, "protein": 30},
                "ingredients": []
            },
            {
                "name": "Test Meal 2", 
                "nutrition": {"calories": 550, "protein": 30},
                "ingredients": []
            },
            {
                "name": "Test Meal 3",
                "nutrition": {"calories": 550, "protein": 30},
                "ingredients": []
            }
        ]
    }
    # Total: 1650 calories, 90 protein
    
    safety_constraints = {
        "target_calories": 1800.0,      # Plan has 1650 (91.7% of target)
        "target_protein": 100.0,        # Plan has 90 (90% of target)
        "min_daily_calories": 1200.0,
        "min_protein_grams": 60.0
    }
    
    try:
        result = validator.validate_plan(
            plan_data=plan_data, 
            safety_constraints=safety_constraints, 
            user_id=UUID("12345678-1234-5678-9012-123456789012"),
            goal_type="weight_loss",
            user_weight_kg=70.0
        )
        
        if result.is_valid:
            print("✅ Soft acceptance working")
            print(f"   Status: {result.status}")
            if result.balance_guidance:
                print(f"   Guidance provided: {len(result.balance_guidance.message)} chars")
            return True
        else:
            print("❌ Plan rejected when it should be accepted")
            print(f"   Status: {result.status}")
            print(f"   Violations: {result.violations}")
            return False
            
    except Exception as e:
        print(f"❌ Soft acceptance test failed: {e}")
        return False

def test_ingredient_validation_fix():
    """Test that ingredient validation works correctly"""
    print("\n=== Testing Ingredient Validation Fix ===")
    
    db = get_nutrition_database()
    
    # Test ingredients that should exist
    valid_ingredients = [
        "lentils (red, cooked)",
        "greek yogurt (plain)",
        "tofu (extra-firm)",
        "cooked quinoa"  # Fixed: use "cooked quinoa" instead of "quinoa (cooked)"
    ]
    
    # Test ingredients that should not exist
    invalid_ingredients = [
        "magical protein powder",
        "unicorn meat",
        "non-existent ingredient"
    ]
    
    all_passed = True
    
    print("Testing valid ingredients:")
    for ingredient in valid_ingredients:
        exists = db.validate_food_exists(ingredient)
        if exists:
            print(f"   ✅ {ingredient}")
        else:
            print(f"   ❌ {ingredient} (should exist but doesn't)")
            all_passed = False
    
    print("Testing invalid ingredients:")
    for ingredient in invalid_ingredients:
        exists = db.validate_food_exists(ingredient)
        if not exists:
            print(f"   ✅ {ingredient} (correctly rejected)")
        else:
            print(f"   ❌ {ingredient} (should not exist but does)")
            all_passed = False
    
    return all_passed

def test_complete_meal_plan_json():
    """Test a complete meal plan JSON that should work end-to-end"""
    print("\n=== Testing Complete Meal Plan JSON ===")
    
    complete_json = '''{
  "plan_type": "daily",
  "date": "2024-01-26",
  "breakfast": {
    "name": "Greek Yogurt Bowl",
    "ingredients": [
      {"name": "greek yogurt (plain)", "quantity": 150, "unit": "g"},
      {"name": "hemp seeds", "quantity": 20, "unit": "g"}
    ],
    "instructions": "Mix yogurt and hemp seeds"
  },
  "lunch": {
    "name": "Tofu Quinoa Bowl",
    "ingredients": [
      {"name": "tofu (extra-firm)", "quantity": 200, "unit": "g"},
      {"name": "cooked quinoa", "quantity": 100, "unit": "g"}
    ],
    "instructions": "Combine tofu and quinoa"
  },
  "dinner": {
    "name": "Lentil Stew",
    "ingredients": [
      {"name": "lentils (red, cooked)", "quantity": 150, "unit": "g"},
      {"name": "spinach", "quantity": 100, "unit": "g"}
    ],
    "instructions": "Cook lentils with spinach"
  }
}'''
    
    try:
        # Test JSON parsing
        parsed = enforce_llm_contract(complete_json, "test-complete")
        print("✅ Complete JSON parsing successful")
        
        # Test ingredient validation
        db = get_nutrition_database()
        all_ingredients_valid = True
        
        for meal_type in ['breakfast', 'lunch', 'dinner']:
            if meal_type in parsed:
                meal = parsed[meal_type]
                if 'ingredients' in meal:
                    for ingredient in meal['ingredients']:
                        ingredient_name = ingredient.get('name', '')
                        if not db.validate_food_exists(ingredient_name):
                            print(f"   ❌ Invalid ingredient: {ingredient_name}")
                            all_ingredients_valid = False
        
        if all_ingredients_valid:
            print("✅ All ingredients validated successfully")
        
        return all_ingredients_valid
        
    except Exception as e:
        print(f"❌ Complete meal plan test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing all fixes together...\n")
    
    results = []
    results.append(test_json_repair_fix())
    results.append(test_soft_acceptance_fix())
    results.append(test_ingredient_validation_fix())
    results.append(test_complete_meal_plan_json())
    
    print(f"\n=== SUMMARY ===")
    print(f"Tests passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("🎉 All fixes are working correctly!")
        return True
    else:
        print("❌ Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)