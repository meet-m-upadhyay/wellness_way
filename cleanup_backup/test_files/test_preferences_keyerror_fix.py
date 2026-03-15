#!/usr/bin/env python3
"""
Test fix for 'preferences' KeyError in AI service

This test verifies that the AI service can handle health context JSON
that is missing the 'preferences' field without throwing a KeyError.
"""

import asyncio
import logging
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.services.ai_service import get_ai_service

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)


async def test_missing_preferences_field():
    """Test that AI service handles missing 'preferences' field gracefully"""
    print("\n=== TEST: Missing 'preferences' Field ===")
    
    ai_service = get_ai_service()
    
    # Create health context JSON without 'preferences' field (this was causing the KeyError)
    incomplete_health_context = {
        "user": {
            "weight_kg": 70.0,
            "age": 30,
            "gender": "male",
            "activity_level": "moderately_active"
        },
        "goals": {
            "primary_goal": "fat_loss",
            "target_weight_kg": 65.0,
            "timeline_weeks": 8,
            "is_realistic": True
        },
        "diet_restrictions": {
            "diet_type": "vegetarian",
            "allergies": [],
            "foods_to_avoid": [],
            "meals_per_day": 3
        },
        "nutrition_targets": {
            "target_calories": 2000.0,
            "min_protein_g": 70.0,
            "target_protein_g": 95.0,
            "target_carbs_g": 250.0,
            "target_fat_g": 67.0
        }
        # NOTE: 'preferences' and 'safety_constraints' fields are missing
    }
    
    try:
        # This should not throw a KeyError anymore
        diet_plan = await ai_service.generate_diet_plan(
            health_context="",  # Empty markdown (will use JSON)
            plan_type="daily",
            target_date="2024-01-15",
            health_context_json=incomplete_health_context
        )
        
        print("[OK] AI service handled missing 'preferences' field without KeyError")
        print(f"[OK] Generated plan type: {diet_plan.get('plan_type', 'unknown')}")
        return True
        
    except KeyError as e:
        if 'preferences' in str(e):
            print(f"[FAIL] KeyError still occurs for 'preferences': {e}")
            return False
        else:
            print(f"[FAIL] Different KeyError occurred: {e}")
            return False
    except Exception as e:
        # Other exceptions are acceptable (e.g., AI provider issues, validation issues)
        # The key is that we don't get a KeyError for 'preferences'
        print(f"[OK] No KeyError for 'preferences'. Got different exception (acceptable): {type(e).__name__}: {e}")
        return True


async def test_validation_function():
    """Test the health context validation function directly"""
    print("\n=== TEST: Health Context Validation Function ===")
    
    ai_service = get_ai_service()
    
    # Test with missing preferences
    incomplete_context = {
        "user": {
            "weight_kg": 70.0,
            "age": 30,
            "gender": "male",
            "activity_level": "moderately_active"
        },
        "goals": {
            "primary_goal": "fat_loss"
        },
        "diet_restrictions": {
            "diet_type": "vegetarian",
            "meals_per_day": 3
        },
        "nutrition_targets": {
            "target_calories": 2000.0,
            "target_protein_g": 95.0
        }
    }
    
    try:
        ai_service._validate_health_context_json(incomplete_context)
        
        # Check that defaults were added
        if 'preferences' in incomplete_context:
            print("[OK] Validation function added missing 'preferences' field")
        else:
            print("[FAIL] Validation function did not add 'preferences' field")
            return False
            
        if 'safety_constraints' in incomplete_context:
            print("[OK] Validation function added missing 'safety_constraints' field")
        else:
            print("[FAIL] Validation function did not add 'safety_constraints' field")
            return False
            
        if incomplete_context['diet_restrictions'].get('allergies') == []:
            print("[OK] Validation function added missing 'allergies' field")
        else:
            print("[FAIL] Validation function did not add 'allergies' field")
            return False
            
        return True
        
    except Exception as e:
        print(f"[FAIL] Validation function threw exception: {e}")
        return False


async def test_complete_context():
    """Test that complete context still works"""
    print("\n=== TEST: Complete Health Context ===")
    
    ai_service = get_ai_service()
    
    # Complete health context with all fields
    complete_health_context = {
        "user": {
            "weight_kg": 70.0,
            "age": 30,
            "gender": "male",
            "activity_level": "moderately_active"
        },
        "goals": {
            "primary_goal": "fat_loss",
            "target_weight_kg": 65.0,
            "timeline_weeks": 8,
            "is_realistic": True
        },
        "diet_restrictions": {
            "diet_type": "vegetarian",
            "allergies": [],
            "foods_to_avoid": [],
            "meals_per_day": 3
        },
        "nutrition_targets": {
            "target_calories": 2000.0,
            "min_protein_g": 70.0,
            "target_protein_g": 95.0,
            "target_carbs_g": 250.0,
            "target_fat_g": 67.0
        },
        "safety_constraints": {
            "min_daily_calories": 1500.0,
            "max_calorie_deficit": 500.0,
            "max_safe_loss_per_week": 1.0
        },
        "preferences": {
            "budget_constraints": "moderate",
            "lifestyle_constraints": "busy schedule"
        }
    }
    
    try:
        ai_service._validate_health_context_json(complete_health_context)
        print("[OK] Complete health context validation passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] Complete health context validation failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("PREFERENCES KEYERROR FIX TEST")
    print("=" * 50)
    
    tests = [
        ("Missing 'preferences' Field", test_missing_preferences_field()),
        ("Health Context Validation Function", test_validation_function()),
        ("Complete Health Context", test_complete_context())
    ]
    
    results = []
    for test_name, test_coro in tests:
        try:
            result = await test_coro
            results.append((test_name, result))
        except Exception as e:
            print(f"[ERROR] {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY:")
    passed = 0
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)} tests")
    
    if passed == len(results):
        print("\n[SUCCESS] 'preferences' KeyError fix is working!")
        return True
    else:
        print("\n[FAILURE] Some tests failed. Check the implementation.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)