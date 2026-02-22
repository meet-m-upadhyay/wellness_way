#!/usr/bin/env python3
"""
Test script to verify the canonicalization boundary fixes:

1. Cooked ingredients are allowed in LLM output
2. They are normalized to raw canonical forms BEFORE integrity validation
3. Integrity validation only sees canonical raw ingredients
4. Safety assertion crashes if cooked ingredients reach integrity validation

Pipeline Order Test:
LLM Output → Unit Enforcement → Cooked-to-Raw Canonicalization → Integrity Validation
"""

import asyncio
import logging
from app.services.unit_enforcement import UnitEnforcer
from app.services.ingredient_canonicalizer import get_ingredient_canonicalizer
from app.services.plan_validation import DietPlanValidator

# Configure logging to see structured logs
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)

async def test_canonicalization_boundary():
    """Test the canonicalization boundary fixes"""
    
    print("🧪 TESTING CANONICALIZATION BOUNDARY FIXES")
    print("=" * 80)
    
    # Test 1: Cooked ingredients in LLM output should be normalized
    print("\n📊 TEST 1: COOKED INGREDIENT NORMALIZATION")
    print("=" * 60)
    
    # Create a plan with cooked ingredients (typical LLM output)
    cooked_plan = {
        "plan_type": "daily",
        "meals": [
            {
                "name": "Cooked Grain Bowl",
                "ingredients": [
                    {"name": "cooked quinoa", "quantity": 150, "unit": "g"},
                    {"name": "lentils green cooked", "quantity": 100, "unit": "g"},
                    {"name": "steamed broccoli", "quantity": 80, "unit": "g"},
                ]
            },
            {
                "name": "Mixed Meal",
                "ingredients": [
                    {"name": "boiled rice", "quantity": 120, "unit": "g"},
                    {"name": "grilled chicken breast", "quantity": 150, "unit": "g"},
                    {"name": "sautéed spinach", "quantity": 60, "unit": "g"},
                ]
            }
        ]
    }
    
    # Step 1: Unit enforcement (should pass - doesn't reject cooked ingredients)
    unit_enforcer = UnitEnforcer()
    try:
        enforced_plan = unit_enforcer.enforce_canonical_units(cooked_plan)
        print("✅ Unit enforcement passed with cooked ingredients")
    except Exception as e:
        print(f"❌ FAILED: Unit enforcement rejected cooked ingredients: {e}")
        return
    
    # Step 2: Canonicalization (should normalize cooked to raw)
    canonicalizer = get_ingredient_canonicalizer()
    try:
        canonicalized_plan = canonicalizer.canonicalize_plan_ingredients(enforced_plan)
        print("✅ Canonicalization completed")
        
        # Verify all ingredients are now in raw canonical form
        print("\n📈 CANONICALIZATION RESULTS:")
        for meal in canonicalized_plan["meals"]:
            print(f"  {meal['name']}:")
            for ingredient in meal["ingredients"]:
                name = ingredient["name"]
                quantity = ingredient["quantity"]
                unit = ingredient["unit"]
                original_name = ingredient.get("original_name", "N/A")
                canonicalization = ingredient.get("canonicalization_applied", "none")
                
                print(f"    - {name}: {quantity}{unit} (from: {original_name}, canonicalization: {canonicalization})")
                
                # Check that no cooked indicators remain
                cooked_indicators = ['cooked', 'boiled', 'steamed', 'grilled', 'sautéed', 'fried']
                if any(indicator in name.lower() for indicator in cooked_indicators):
                    print(f"❌ FAILED: Cooked indicator still present in '{name}'")
                    return
        
        print("✅ All cooked ingredients normalized to raw canonical forms")
        
    except Exception as e:
        print(f"❌ FAILED: Canonicalization error: {e}")
        return
    
    # Test 2: Integrity validation should only see raw ingredients
    print("\n📊 TEST 2: INTEGRITY VALIDATION WITH RAW INGREDIENTS")
    print("=" * 60)
    
    validator = DietPlanValidator()
    
    try:
        # This should pass - integrity validation sees only raw ingredients
        violations = validator._check_integrity_violations(canonicalized_plan)
        
        if not violations:
            print("✅ Integrity validation passed with canonicalized ingredients")
        else:
            print(f"❌ FAILED: Integrity validation found violations: {violations}")
            return
        
    except RuntimeError as e:
        if "CRITICAL: Integrity validation ran before canonicalization" in str(e):
            print(f"❌ FAILED: Safety assertion triggered incorrectly: {e}")
            return
        else:
            print(f"❌ FAILED: Unexpected runtime error: {e}")
            return
    except Exception as e:
        print(f"❌ FAILED: Integrity validation error: {e}")
        return
    
    # Test 3: Safety assertion should crash if cooked ingredients reach integrity validation
    print("\n📊 TEST 3: SAFETY ASSERTION TEST")
    print("=" * 60)
    
    # Create a plan with cooked ingredients that bypasses canonicalization
    uncanonicalized_plan = {
        "plan_type": "daily",
        "meals": [
            {
                "name": "Uncanonicalized Meal",
                "ingredients": [
                    {"name": "cooked quinoa", "quantity": 150, "unit": "g"},  # Should trigger assertion
                ]
            }
        ]
    }
    
    try:
        # This should crash with safety assertion
        violations = validator._check_integrity_violations(uncanonicalized_plan)
        print("❌ FAILED: Safety assertion should have crashed on cooked ingredients")
        return
    except RuntimeError as e:
        if "CRITICAL: Integrity validation ran before canonicalization" in str(e):
            print("✅ Safety assertion correctly crashed on cooked ingredients")
        else:
            print(f"❌ FAILED: Wrong error message: {e}")
            return
    except Exception as e:
        print(f"❌ FAILED: Unexpected error: {e}")
        return
    
    # Test 4: Complete pipeline order test
    print("\n📊 TEST 4: COMPLETE PIPELINE ORDER TEST")
    print("=" * 60)
    
    # Test the complete pipeline: Unit Enforcement → Canonicalization → Integrity Validation
    pipeline_test_plan = {
        "plan_type": "daily",
        "meals": [
            {
                "name": "Pipeline Test Meal",
                "ingredients": [
                    {"name": "cooked quinoa", "quantity": 200, "unit": "ml"},     # ML + cooked
                    {"name": "steamed broccoli", "quantity": 1, "unit": "piece"}, # Discrete + cooked
                    {"name": "boiled lentils", "quantity": 100, "unit": "g"},    # Already g + cooked
                ]
            }
        ]
    }
    
    try:
        # Step 1: Unit enforcement
        step1_plan = unit_enforcer.enforce_canonical_units(pipeline_test_plan)
        print("✅ Pipeline Step 1: Unit enforcement completed")
        
        # Step 2: Canonicalization
        step2_plan = canonicalizer.canonicalize_plan_ingredients(step1_plan)
        print("✅ Pipeline Step 2: Canonicalization completed")
        
        # Step 3: Integrity validation
        violations = validator._check_integrity_violations(step2_plan)
        
        if not violations:
            print("✅ Pipeline Step 3: Integrity validation passed")
        else:
            print(f"❌ FAILED: Pipeline integrity validation found violations: {violations}")
            return
        
        # Verify final state
        print("\n📈 FINAL PIPELINE RESULTS:")
        for meal in step2_plan["meals"]:
            print(f"  {meal['name']}:")
            for ingredient in meal["ingredients"]:
                name = ingredient["name"]
                quantity = ingredient["quantity"]
                unit = ingredient["unit"]
                print(f"    - {name}: {quantity}{unit}")
                
                # Verify no cooked indicators
                cooked_indicators = ['cooked', 'boiled', 'steamed', 'grilled', 'sautéed', 'fried']
                if any(indicator in name.lower() for indicator in cooked_indicators):
                    print(f"❌ FAILED: Cooked indicator in final result: '{name}'")
                    return
                
                # Verify canonical units
                if unit not in ["g", "scoops"]:
                    print(f"❌ FAILED: Non-canonical unit in final result: '{unit}'")
                    return
        
        print("✅ Complete pipeline produced canonical raw ingredients with canonical units")
        
    except Exception as e:
        print(f"❌ FAILED: Complete pipeline test error: {e}")
        return
    
    # Test 5: Specific canonicalization mappings
    print("\n📊 TEST 5: SPECIFIC CANONICALIZATION MAPPINGS")
    print("=" * 60)
    
    mapping_test_plan = {
        "plan_type": "daily",
        "meals": [
            {
                "name": "Mapping Test",
                "ingredients": [
                    {"name": "cooked quinoa", "quantity": 250, "unit": "g"},        # Should become "quinoa (dry)"
                    {"name": "lentils red cooked", "quantity": 200, "unit": "g"},  # Should become "lentils (red, dry)"
                    {"name": "steamed broccoli", "quantity": 100, "unit": "g"},    # Should become "broccoli"
                    {"name": "boiled rice", "quantity": 300, "unit": "g"},         # Should become "rice (dry)"
                ]
            }
        ]
    }
    
    try:
        # Apply canonicalization
        step1_plan = unit_enforcer.enforce_canonical_units(mapping_test_plan)
        mapped_plan = canonicalizer.canonicalize_plan_ingredients(step1_plan)
        
        # Check specific mappings
        expected_mappings = {
            "cooked quinoa": "quinoa (dry)",
            "lentils red cooked": "lentils (red, dry)",
            "steamed broccoli": "broccoli",
            "boiled rice": "rice (dry)"
        }
        
        print("📈 CANONICALIZATION MAPPINGS:")
        for meal in mapped_plan["meals"]:
            for ingredient in meal["ingredients"]:
                final_name = ingredient["name"]
                original_name = ingredient.get("original_name", "N/A")
                
                if original_name in expected_mappings:
                    expected = expected_mappings[original_name]
                    if final_name == expected:
                        print(f"    ✅ {original_name} -> {final_name}")
                    else:
                        print(f"    ❌ {original_name} -> {final_name} (expected: {expected})")
                        return
                else:
                    print(f"    ℹ️ {original_name} -> {final_name} (no specific mapping expected)")
        
        print("✅ All canonicalization mappings correct")
        
    except Exception as e:
        print(f"❌ FAILED: Canonicalization mapping test error: {e}")
        return
    
    print("\n🎯 FINAL SUMMARY")
    print("=" * 80)
    print("✅ Cooked ingredients allowed in LLM output")
    print("✅ Canonicalization normalizes cooked to raw forms")
    print("✅ Integrity validation only sees canonical raw ingredients")
    print("✅ Safety assertion crashes if cooked ingredients reach validation")
    print("✅ Complete pipeline order: Unit Enforcement → Canonicalization → Validation")
    print("✅ Specific canonicalization mappings work correctly")
    print("✅ CANONICALIZATION BOUNDARY FIXES WORKING CORRECTLY")

if __name__ == "__main__":
    asyncio.run(test_canonicalization_boundary())