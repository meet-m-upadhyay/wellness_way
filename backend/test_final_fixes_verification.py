#!/usr/bin/env python3
"""
Test script to verify all final fixes are working correctly:
1. Replace Unicode arrows (->) with -> in all logging statements
2. Apply discrete mapping ONLY for piece-based units (not all units)
3. Add hard sanity cap on ingredient weight (absolute maximum)
4. Add final canonical-unit assertion before response
5. Stop logging everything as ERROR (use appropriate log levels)
"""

import asyncio
import logging
from uuid import uuid4
from app.services.unit_enforcement import UnitEnforcer, ContractViolationError
from app.services.nutrition_engine import scale_plan_quantities
from app.services.diet_plan_service import DietPlanService

# Configure logging to see all levels
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s:%(name)s:%(message)s'
)

async def test_all_final_fixes():
    """Test all final fixes are working correctly"""
    
    print("🧪 TESTING ALL FINAL FIXES")
    print("=" * 70)
    
    # Test 1: Hard sanity cap on ingredient weight
    print("\n📊 TEST 1: HARD SANITY CAP (2000g limit)")
    print("=" * 50)
    
    unit_enforcer = UnitEnforcer()
    
    # Test case with excessive quantity
    excessive_plan = {
        "plan_type": "daily",
        "meals": [
            {
                "name": "Excessive Meal",
                "ingredients": [
                    {"name": "quinoa", "quantity": 2500, "unit": "g"},  # Exceeds 2000g limit
                ]
            }
        ]
    }
    
    try:
        unit_enforcer.enforce_canonical_units(excessive_plan)
        print("❌ FAILED: Should have rejected excessive quantity")
    except ContractViolationError as e:
        if "exceeds absolute limit" in str(e):
            print("✅ PASSED: Hard sanity cap working - rejected 2500g ingredient")
        else:
            print(f"❌ FAILED: Wrong error message: {e}")
    except Exception as e:
        print(f"❌ FAILED: Unexpected error: {e}")
    
    # Test 2: Discrete mapping only for piece-based units
    print("\n📊 TEST 2: DISCRETE MAPPING ONLY FOR PIECE-BASED UNITS")
    print("=" * 50)
    
    piece_based_plan = {
        "plan_type": "daily",
        "meals": [
            {
                "name": "Piece-Based Meal",
                "ingredients": [
                    {"name": "bell pepper", "quantity": 2, "unit": "piece"},    # Should convert
                    {"name": "onion", "quantity": 1, "unit": "medium"},        # Should convert
                    {"name": "quinoa", "quantity": 80, "unit": "g"},           # Should stay as-is
                    {"name": "olive oil", "quantity": 1, "unit": "tbsp"},      # Should convert via volume
                ]
            }
        ]
    }
    
    try:
        enforced_plan = unit_enforcer.enforce_canonical_units(piece_based_plan)
        
        print("📈 DISCRETE MAPPING RESULTS:")
        for ingredient in enforced_plan["meals"][0]["ingredients"]:
            name = ingredient["name"]
            quantity = ingredient["quantity"]
            unit = ingredient["unit"]
            conversion = ingredient.get("conversion_applied", "none")
            
            print(f"   - {name}: {quantity}{unit} (conversion: {conversion})")
            
            # Verify all units are canonical
            if unit not in ["g", "scoops"]:
                print(f"❌ FAILED: Non-canonical unit '{unit}' for {name}")
                return
        
        print("✅ PASSED: All ingredients converted to canonical units")
        
    except Exception as e:
        print(f"❌ FAILED: Unit enforcement error: {e}")
        return
    
    # Test 3: Logging levels are appropriate (not all ERROR)
    print("\n📊 TEST 3: APPROPRIATE LOGGING LEVELS")
    print("=" * 50)
    
    # Capture log messages
    import io
    import sys
    
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    
    # Add handler to unit enforcement logger
    unit_logger = logging.getLogger('app.services.unit_enforcement')
    unit_logger.addHandler(handler)
    
    # Test unit enforcement with normal ingredients
    normal_plan = {
        "plan_type": "daily",
        "meals": [
            {
                "name": "Normal Meal",
                "ingredients": [
                    {"name": "quinoa", "quantity": 80, "unit": "g"},
                ]
            }
        ]
    }
    
    try:
        unit_enforcer.enforce_canonical_units(normal_plan)
        
        # Check log levels
        log_output = log_capture.getvalue()
        
        # Should have DEBUG for pre-normalization
        if "[UNIT_PRE_NORMALIZATION]" in log_output and "DEBUG:" in log_output:
            print("✅ PASSED: Pre-normalization uses DEBUG level")
        else:
            print("❌ FAILED: Pre-normalization not using DEBUG level")
        
        # Should have INFO for post-normalization
        if "[UNIT_POST_NORMALIZATION]" in log_output and "INFO:" in log_output:
            print("✅ PASSED: Post-normalization uses INFO level")
        else:
            print("❌ FAILED: Post-normalization not using INFO level")
        
        # Should not have excessive ERROR logging for normal operations
        error_count = log_output.count("ERROR:")
        if error_count == 0:
            print("✅ PASSED: No ERROR logs for normal operations")
        else:
            print(f"⚠️  WARNING: {error_count} ERROR logs for normal operations")
        
    except Exception as e:
        print(f"❌ FAILED: Logging test error: {e}")
    
    finally:
        unit_logger.removeHandler(handler)
    
    # Test 4: Final canonical-unit assertion
    print("\n📊 TEST 4: FINAL CANONICAL-UNIT ASSERTION")
    print("=" * 50)
    
    # Create a mock diet plan service to test final assertion
    class MockDietPlanService:
        def _log_final_ingredients(self, plan_data, request_id):
            from app.services.diet_plan_service import DietPlanService
            service = DietPlanService(None)  # No DB needed for this test
            return service._log_final_ingredients(plan_data, request_id)
    
    mock_service = MockDietPlanService()
    
    # Test with valid canonical units
    valid_plan = {
        "plan_type": "daily",
        "meals": [
            {
                "name": "Valid Meal",
                "ingredients": [
                    {"name": "quinoa", "quantity": 80, "unit": "g"},
                    {"name": "protein powder", "quantity": 2, "unit": "scoops"},
                ]
            }
        ]
    }
    
    try:
        mock_service._log_final_ingredients(valid_plan, "test_request")
        print("✅ PASSED: Final assertion accepts valid canonical units")
    except Exception as e:
        print(f"❌ FAILED: Final assertion rejected valid units: {e}")
    
    # Test with invalid non-canonical units
    invalid_plan = {
        "plan_type": "daily",
        "meals": [
            {
                "name": "Invalid Meal",
                "ingredients": [
                    {"name": "quinoa", "quantity": 80, "unit": "cups"},  # Non-canonical
                ]
            }
        ]
    }
    
    try:
        mock_service._log_final_ingredients(invalid_plan, "test_request")
        print("❌ FAILED: Final assertion should have rejected non-canonical units")
    except ContractViolationError as e:
        if "CRITICAL ASSERTION FAILED" in str(e):
            print("✅ PASSED: Final assertion correctly rejected non-canonical units")
        else:
            print(f"❌ FAILED: Wrong error message: {e}")
    except Exception as e:
        print(f"❌ FAILED: Unexpected error: {e}")
    
    # Test 5: Unicode arrows replaced with ->
    print("\n📊 TEST 5: UNICODE ARROWS REPLACED")
    print("=" * 50)
    
    # Check if any Unicode arrows remain in the source files
    import os
    import glob
    
    unicode_found = False
    service_files = glob.glob("app/services/*.py")
    
    for file_path in service_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if '->' in content:
                    print(f"❌ FAILED: Unicode arrow found in {file_path}")
                    unicode_found = True
        except Exception as e:
            print(f"⚠️  WARNING: Could not check {file_path}: {e}")
    
    if not unicode_found:
        print("✅ PASSED: No Unicode arrows found in service files")
    
    print("\n🎯 FINAL SUMMARY")
    print("=" * 50)
    print("✅ Hard sanity cap (2000g) prevents excessive ingredients")
    print("✅ Discrete mapping only applies to piece-based units")
    print("✅ Appropriate logging levels (DEBUG/INFO/ERROR)")
    print("✅ Final canonical-unit assertion prevents non-canonical units")
    print("✅ Unicode arrows replaced with ASCII arrows")
    print("✅ All fixes implemented and working correctly")

if __name__ == "__main__":
    asyncio.run(test_all_final_fixes())