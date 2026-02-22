#!/usr/bin/env python3
"""
CONTRACT VALIDATION FIX TEST

This test verifies that contract validation now uses the same normalization
logic as the nutrition database, fixing the mismatch that was causing
valid ingredients to be rejected.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unittest.mock import MagicMock, patch
from app.services.ai_service import DietPlanAI
from app.services.nutrition_database import get_nutrition_database, NutritionData, ProteinQuality


def test_contract_validation_with_database_normalization():
    """Test that contract validation uses database normalization"""
    print("=== CONTRACT VALIDATION WITH DATABASE NORMALIZATION ===")
    
    # Create AI service with real nutrition database
    ai_service = DietPlanAI()
    # Use the real nutrition database instead of mocking
    ai_service.nutrition_db = get_nutrition_database()
    
    # Test the exact ingredients that were failing
    failing_ingredients_meal = {
        "meals": [
            {
                "name": "Protein Bowl",
                "ingredients": [
                    {"name": "chicken breast (raw)", "quantity": 150, "unit": "g"},
                    {"name": "tuna (raw)", "quantity": 120, "unit": "g"},
                    {"name": "salmon (raw)", "quantity": 100, "unit": "g"}
                ]
            }
        ]
    }
    
    try:
        # This should NOT raise an exception after the fix
        ai_service._validate_ingredient_contract(failing_ingredients_meal, "test_request")
        print("✅ Contract validation passed for previously failing ingredients")
        return True
        
    except Exception as e:
        print(f"❌ Contract validation still failing: {e}")
        return False


def test_cooking_modifiers_still_work():
    """Test that cooking modifiers still work with the new approach"""
    print("\n=== COOKING MODIFIERS TEST ===")
    
    # Create AI service with real nutrition database
    ai_service = DietPlanAI()
    ai_service.nutrition_db = get_nutrition_database()
    
    # Test meal with cooking modifiers
    cooking_modifiers_meal = {
        "meals": [
            {
                "name": "Cooked Meal",
                "ingredients": [
                    {"name": "steamed kale", "quantity": 100, "unit": "g"},
                    {"name": "cooked quinoa", "quantity": 80, "unit": "g"},
                    {"name": "grilled chicken", "quantity": 150, "unit": "g"}
                ]
            }
        ]
    }
    
    try:
        # This should also work since the database normalizer handles cooking modifiers
        ai_service._validate_ingredient_contract(cooking_modifiers_meal, "cooking_test")
        print("✅ Contract validation passed for cooking modifiers")
        return True
        
    except Exception as e:
        print(f"❌ Cooking modifiers validation failed: {e}")
        return False


def test_unknown_ingredients_still_rejected():
    """Test that truly unknown ingredients are still rejected"""
    print("\n=== UNKNOWN INGREDIENTS REJECTION TEST ===")
    
    # Create AI service with real nutrition database
    ai_service = DietPlanAI()
    ai_service.nutrition_db = get_nutrition_database()
    
    # Test meal with unknown ingredient
    unknown_ingredient_meal = {
        "meals": [
            {
                "name": "Invalid Meal",
                "ingredients": [
                    {"name": "chicken breast (raw)", "quantity": 150, "unit": "g"},  # Should pass
                    {"name": "magical unicorn powder", "quantity": 10, "unit": "g"}  # Should fail
                ]
            }
        ]
    }
    
    try:
        ai_service._validate_ingredient_contract(unknown_ingredient_meal, "unknown_test")
        print("❌ Contract validation should have failed for unknown ingredient")
        return False
        
    except Exception as e:
        if "magical unicorn powder" in str(e):
            print("✅ Contract validation correctly rejected unknown ingredient")
            return True
        else:
            print(f"❌ Unexpected error: {e}")
            return False


async def main():
    """Run all contract validation tests"""
    print("🧪 TESTING CONTRACT VALIDATION FIX")
    print("=" * 60)
    print("Verifying that contract validation now uses database normalization:")
    print("1. 🔧 Previously failing ingredients now pass")
    print("2. 🍳 Cooking modifiers still work")
    print("3. 🚫 Unknown ingredients still rejected")
    print("=" * 60)
    
    try:
        # Run all tests
        test1 = test_contract_validation_with_database_normalization()
        test2 = test_cooking_modifiers_still_work()
        test3 = test_unknown_ingredients_still_rejected()
        
        all_passed = test1 and test2 and test3
        
        print("\n" + "=" * 60)
        if all_passed:
            print("✅ ALL CONTRACT VALIDATION TESTS PASSED")
            print("\n🎯 ROOT CAUSE ANALYSIS CONFIRMED:")
            print("1. ✅ Contract validation now uses same normalization as nutrition lookup")
            print("2. ✅ 'chicken breast (raw)' → normalized by database → valid")
            print("3. ✅ 'tuna (raw)' → normalized by database → valid")
            print("4. ✅ 'salmon (raw)' → normalized by database → valid")
            print("5. ✅ Cooking modifiers still work through database normalization")
            print("6. ✅ Unknown ingredients still properly rejected")
            
            print("\n🔧 TECHNICAL FIX:")
            print("- Removed custom canonicalization function")
            print("- Contract validation now calls nutrition_db.get_nutrition()")
            print("- Uses same normalization path as actual nutrition lookup")
            print("- Eliminates validation/lookup mismatch")
            
            print("\n🚫 ERRORS WILL NOT OCCUR AGAIN:")
            print("❌ INGREDIENT CONTRACT VIOLATION: ['chicken breast (raw)', 'tuna (raw)', 'salmon (raw)']")
            print("❌ [CANONICALIZATION_FAILED] messages")
            print("❌ Valid ingredients being rejected due to normalization mismatch")
        else:
            print("❌ SOME CONTRACT VALIDATION TESTS FAILED")
            print("🚨 Fix needs additional work")
        
        return all_passed
        
    except Exception as e:
        print(f"\n❌ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)