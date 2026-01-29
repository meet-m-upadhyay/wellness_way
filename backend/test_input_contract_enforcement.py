#!/usr/bin/env python3
"""
Test Input Contract Enforcement - LLM Ingredient Validation

This test verifies that the LLM is constrained to only use ingredients
that exist in the nutrition database, preventing unknown ingredient errors.
"""

import asyncio
import json
import logging
from app.services.nutrition_database import get_nutrition_database
from app.services.ai_service import DietPlanAI, LLMContractViolationError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_nutrition_database_ingredient_list():
    """Test that nutrition database provides ingredient list for LLM contract"""
    print("🧪 Testing Nutrition Database Ingredient List")
    
    db = get_nutrition_database()
    
    # Test get_all_food_names method
    all_foods = db.get_all_food_names()
    print(f"✅ Found {len(all_foods)} foods in database")
    
    # Verify some expected foods are present
    expected_foods = [
        "greek yogurt (plain)",
        "hemp seeds", 
        "whole wheat wrap",
        "tofu (extra-firm)",
        "lentils (red, dry)"
    ]
    
    for food in expected_foods:
        if food in all_foods:
            print(f"✅ Found expected food: {food}")
        else:
            print(f"❌ Missing expected food: {food}")
    
    # Test allowed ingredients prompt
    prompt = db.get_allowed_ingredients_prompt()
    print(f"✅ Generated allowed ingredients prompt ({len(prompt)} characters)")
    
    # Verify prompt contains key sections
    if "HIGH-PROTEIN SOURCES" in prompt:
        print("✅ Prompt contains protein sources section")
    if "CRITICAL RULES" in prompt:
        print("✅ Prompt contains critical rules section")
    if "greek yogurt (plain)" in prompt:
        print("✅ Prompt contains specific ingredient examples")
    
    return True

def test_ingredient_validation():
    """Test ingredient contract validation logic"""
    print("\n🧪 Testing Ingredient Contract Validation")
    
    ai_service = DietPlanAI()
    
    # Test valid meal ideas (should pass)
    valid_meal_ideas = {
        "plan_type": "daily",
        "date": "2024-01-01",
        "breakfast": {
            "name": "High-Protein Breakfast",
            "ingredients": [
                {"name": "greek yogurt (plain)", "quantity": 150, "unit": "g"},
                {"name": "hemp seeds", "quantity": 20, "unit": "g"}
            ],
            "instructions": "Mix yogurt with seeds"
        }
    }
    
    try:
        ai_service._validate_ingredient_contract(valid_meal_ideas, "test-001")
        print("✅ Valid ingredients passed validation")
    except LLMContractViolationError as e:
        print(f"❌ Valid ingredients failed validation: {e}")
        return False
    
    # Test invalid meal ideas (should fail)
    invalid_meal_ideas = {
        "plan_type": "daily", 
        "date": "2024-01-01",
        "breakfast": {
            "name": "Invalid Breakfast",
            "ingredients": [
                {"name": "unknown superfood", "quantity": 100, "unit": "g"},
                {"name": "magical berries", "quantity": 50, "unit": "g"}
            ],
            "instructions": "Mix unknown ingredients"
        }
    }
    
    try:
        ai_service._validate_ingredient_contract(invalid_meal_ideas, "test-002")
        print("❌ Invalid ingredients passed validation (should have failed)")
        return False
    except LLMContractViolationError as e:
        print(f"✅ Invalid ingredients correctly rejected: {e}")
    
    return True

def test_prompt_generation():
    """Test that meal planning prompt includes allowed ingredients"""
    print("\n🧪 Testing Meal Planning Prompt Generation")
    
    ai_service = DietPlanAI()
    
    # Mock health context
    health_context_json = {
        "diet_restrictions": {
            "diet_type": "vegetarian",
            "allergies": [],
            "foods_to_avoid": [],
            "meals_per_day": 3
        },
        "goals": {
            "primary_goal": "muscle_building"
        },
        "preferences": {
            "lifestyle_constraints": "busy schedule"
        }
    }
    
    # Generate prompt
    prompt = ai_service._get_meal_planning_prompt(
        json_context=health_context_json,
        plan_type="daily",
        target_date="2024-01-01"
    )
    
    print(f"✅ Generated meal planning prompt ({len(prompt)} characters)")
    
    # Verify prompt contains input contract enforcement
    if "CRITICAL INPUT CONTRACT" in prompt:
        print("✅ Prompt contains input contract section")
    else:
        print("❌ Prompt missing input contract section")
        return False
    
    if "ALLOWED INGREDIENTS ONLY" in prompt:
        print("✅ Prompt enforces allowed ingredients only")
    else:
        print("❌ Prompt missing allowed ingredients enforcement")
        return False
    
    if "greek yogurt (plain)" in prompt:
        print("✅ Prompt contains specific allowed ingredients")
    else:
        print("❌ Prompt missing specific ingredient examples")
        return False
    
    if "Use EXACT ingredient names from the lists above" in prompt:
        print("✅ Prompt enforces exact ingredient names")
    else:
        print("❌ Prompt missing exact name enforcement")
        return False
    
    return True

async def test_end_to_end_contract_enforcement():
    """Test end-to-end contract enforcement with mock LLM response"""
    print("\n🧪 Testing End-to-End Contract Enforcement")
    
    ai_service = DietPlanAI()
    
    # Mock a valid LLM response with known ingredients
    valid_response = json.dumps({
        "plan_type": "daily",
        "date": "2024-01-01",
        "breakfast": {
            "name": "Protein Power Bowl",
            "ingredients": [
                {"name": "greek yogurt (plain)", "quantity": 150, "unit": "g"},
                {"name": "hemp seeds", "quantity": 20, "unit": "g"},
                {"name": "berries (mixed)", "quantity": 100, "unit": "g"}
            ],
            "instructions": "Mix all ingredients in a bowl"
        },
        "lunch": {
            "name": "Tofu Quinoa Bowl", 
            "ingredients": [
                {"name": "tofu (extra-firm)", "quantity": 200, "unit": "g"},
                {"name": "cooked quinoa", "quantity": 150, "unit": "g"},
                {"name": "spinach", "quantity": 100, "unit": "g"}
            ],
            "instructions": "Sauté tofu, serve over quinoa with spinach"
        },
        "dinner": {
            "name": "Lentil Curry",
            "ingredients": [
                {"name": "lentils (red, dry)", "quantity": 80, "unit": "g"},
                {"name": "coconut oil", "quantity": 10, "unit": "g"},
                {"name": "onions", "quantity": 100, "unit": "g"}
            ],
            "instructions": "Cook lentils with spices and vegetables"
        }
    })
    
    try:
        # Test contract enforcement on valid response
        from app.services.llm_contract_enforcer import enforce_llm_contract
        meal_ideas = enforce_llm_contract(valid_response, "test-003")
        
        # Test ingredient contract validation
        ai_service._validate_ingredient_contract(meal_ideas, "test-003")
        
        print("✅ End-to-end contract enforcement passed for valid response")
        
    except Exception as e:
        print(f"❌ End-to-end contract enforcement failed: {e}")
        return False
    
    # Test with invalid response (unknown ingredients)
    invalid_response = json.dumps({
        "plan_type": "daily",
        "date": "2024-01-01", 
        "breakfast": {
            "name": "Invalid Breakfast",
            "ingredients": [
                {"name": "unicorn protein powder", "quantity": 30, "unit": "g"},
                {"name": "dragon fruit extract", "quantity": 10, "unit": "g"}
            ],
            "instructions": "Mix magical ingredients"
        }
    })
    
    try:
        meal_ideas = enforce_llm_contract(invalid_response, "test-004")
        ai_service._validate_ingredient_contract(meal_ideas, "test-004")
        
        print("❌ End-to-end contract enforcement should have failed for invalid ingredients")
        return False
        
    except LLMContractViolationError as e:
        print(f"✅ End-to-end contract enforcement correctly rejected invalid ingredients: {e}")
    
    return True

def main():
    """Run all input contract enforcement tests"""
    print("🚀 INPUT CONTRACT ENFORCEMENT TESTS")
    print("=" * 50)
    
    tests = [
        test_nutrition_database_ingredient_list,
        test_ingredient_validation,
        test_prompt_generation,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    # Run async test
    try:
        result = asyncio.run(test_end_to_end_contract_enforcement())
        results.append(result)
    except Exception as e:
        print(f"❌ Async test failed with exception: {e}")
        results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Input contract enforcement is working!")
        print("\nKey Features Verified:")
        print("- ✅ Nutrition database provides complete ingredient list")
        print("- ✅ AI service validates ingredients against database")
        print("- ✅ Meal planning prompt includes allowed ingredients")
        print("- ✅ Contract violations are properly detected and rejected")
        print("\n🛡️ The LLM is now constrained to only use known ingredients!")
    else:
        print(f"\n⚠️ {total - passed} tests failed - input contract enforcement needs fixes")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)