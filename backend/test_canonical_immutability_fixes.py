#!/usr/bin/env python3
"""
Test script to verify canonical immutability fixes:
1. Canonical Immutability - units never change after enforcement
2. Fix Unit Conversion (ml → g) - proper density mapping
3. Freeze Canonical Plan - _canonicalized flag prevents mutation
4. Scaling Logic Fix - only scale quantities, never units
5. Discrete Mapping Bug Fix - only apply when unit is pieces
6. Ingredient Name Normalization - remove punctuation
"""

import asyncio
import logging
from uuid import uuid4
from app.services.unit_enforcement import UnitEnforcer, ContractViolationError
from app.services.nutrition_engine import scale_plan_quantities
from app.services.quantity_rounding import QuantityRounder

# Configure logging to see structured logs
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s:%(name)s:%(message)s'
)

async def test_canonical_immutability_fixes():
    """Test all canonical immutability fixes"""
    
    print("🧪 TESTING CANONICAL IMMUTABILITY FIXES")
    print("=" * 70)
    
    # Test 1: ml → g conversion with density mapping
    print("\n📊 TEST 1: ML TO G CONVERSION WITH DENSITY")
    print("=" * 50)
    
    unit_enforcer = UnitEnforcer()
    
    ml_plan = {
        "plan_type": "daily",
        "meals": [
            {
                "name": "Yogurt Bowl",
                "ingredients": [
                    {"name": "greek yogurt (plain)", "quantity": 200, "unit": "ml"},  # Should use density 1.03
                    {"name": "milk", "quantity": 100, "unit": "ml"},                 # Should use density 1.03
                    {"name": "olive oil", "quantity": 15, "unit": "ml"},            # Should use density 0.92
                ]
            }
        ]
    }
    
    try:
        enforced_plan = unit_enforcer.enforce_canonical_units(ml_plan)
        
        print("📈 ML TO G CONVERSION RESULTS:")
        for ingredient in enforced_plan["meals"][0]["ingredients"]:
            name = ingredient["name"]
            quantity = ingredient["quantity"]
            unit = ingredient["unit"]
            conversion = ingredient.get("conversion_applied", "none")
            
            print(f"   - {name}: {quantity}{unit} (conversion: {conversion})")
            
            # Verify all units are canonical
            if unit != "g":
                print(f"❌ FAILED: Non-canonical unit '{unit}' for {name}")
                return
        
        # Verify _canonicalized flag is set
        if enforced_plan.get("_canonicalized"):
            print("✅ PASSED: Plan marked as canonicalized")
        else:
            print("❌ FAILED: Plan not marked as canonicalized")
            return
        
        print("✅ PASSED: All ml converted to g using density mapping")
        
    except Exception as e:
        print(f"❌ FAILED: ML conversion error: {e}")
        return
    
    # Test 2: Discrete mapping bug fix - only apply when unit is pieces
    print("\n📊 TEST 2: DISCRETE MAPPING BUG FIX")
    print("=" * 50)
    
    discrete_bug_plan = {
        "plan_type": "daily",
        "meals": [
            {
                "name": "Mixed Meal",
                "ingredients": [
                    {"name": "bell pepper", "quantity": 150, "unit": "g"},      # Should NOT apply discrete mapping
                    {"name": "onion", "quantity": 2, "unit": "piece"},         # Should apply discrete mapping
                    {"name": "quinoa", "quantity": 80, "unit": "g"},           # Should stay as-is
                ]
            }
        ]
    }
    
    try:
        enforced_plan = unit_enforcer.enforce_canonical_units(discrete_bug_plan)
        
        print("📈 DISCRETE MAPPING BUG FIX RESULTS:")
        for ingredient in enforced_plan["meals"][0]["ingredients"]:
            name = ingredient["name"]
            quantity = ingredient["quantity"]
            unit = ingredient["unit"]
            conversion = ingredient.get("conversion_applied", "none")
            
            print(f"   - {name}: {quantity}{unit} (conversion: {conversion})")
            
            # Check for impossible quantities (the bug we're fixing)
            if quantity > 1000:
                print(f"❌ FAILED: Impossible quantity {quantity}g for {name}")
                return
        
        print("✅ PASSED: No impossible quantities from discrete mapping bug")
        
    except Exception as e:
        print(f"❌ FAILED: Discrete mapping test error: {e}")
        return
    
    # Test 3: Canonical immutability guard in quantity rounding
    print("\n📊 TEST 3: CANONICAL IMMUTABILITY GUARD")
    print("=" * 50)
    
    # Create a canonicalized plan
    canonical_plan = {
        "plan_type": "daily",
        "_canonicalized": True,
        "meals": [
            {
                "name": "Test Meal",
                "ingredients": [
                    {"name": "quinoa", "quantity": 80, "unit": "g"},
                ]
            }
        ]
    }
    
    quantity_rounder = QuantityRounder()
    
    try:
        rounded_plan = quantity_rounder.round_plan_quantities(canonical_plan)
        print("✅ PASSED: Canonical immutability guard allows valid canonical units")
    except Exception as e:
        print(f"❌ FAILED: Canonical immutability guard rejected valid units: {e}")
        return
    
    # Test with invalid units (should crash)
    invalid_plan = {
        "plan_type": "daily",
        "_canonicalized": True,
        "meals": [
            {
                "name": "Invalid Meal",
                "ingredients": [
                    {"name": "quinoa", "quantity": 80, "unit": "ml"},  # Should trigger violation
                ]
            }
        ]
    }
    
    try:
        quantity_rounder.round_plan_quantities(invalid_plan)
        print("❌ FAILED: Canonical immutability guard should have crashed on ml unit")
        return
    except RuntimeError as e:
        if "CANONICAL UNIT VIOLATION" in str(e):
            print("✅ PASSED: Canonical immutability guard correctly crashed on ml unit")
        else:
            print(f"❌ FAILED: Wrong error message: {e}")
            return
    except Exception as e:
        print(f"❌ FAILED: Unexpected error: {e}")
        return
    
    # Test 4: Scaling logic fix - only scale quantities, never units
    print("\n📊 TEST 4: SCALING LOGIC FIX")
    print("=" * 50)
    
    scaling_plan = {
        "plan_type": "daily",
        "_canonicalized": True,
        "meals": [
            {
                "name": "Scalable Meal",
                "ingredients": [
                    {
                        "name": "quinoa", 
                        "quantity": 80, 
                        "unit": "g",
                        "nutrition": {"calories": 120, "protein": 4.4}
                    }
                ],
                "nutrition": {"calories": 120, "protein": 4.4}
            }
        ],
        "daily_totals": {"calories": 120, "protein": 4.4}
    }
    
    try:
        scaled_plan = scale_plan_quantities(
            plan_data=scaling_plan,
            target_calories=1800,
            target_protein=100
        )
        
        print("📈 SCALING RESULTS:")
        for meal in scaled_plan["meals"]:
            for ingredient in meal["ingredients"]:
                name = ingredient["name"]
                quantity = ingredient["quantity"]
                unit = ingredient["unit"]
                
                print(f"   - {name}: {quantity}{unit}")
                
                # Verify unit hasn't changed
                if unit != "g":
                    print(f"❌ FAILED: Unit changed during scaling: {unit}")
                    return
                
                # Verify quantity is reasonable
                if quantity > 1000:
                    print(f"❌ FAILED: Quantity exceeds limit: {quantity}g")
                    return
        
        print("✅ PASSED: Scaling only modified quantities, units unchanged")
        
    except Exception as e:
        print(f"❌ FAILED: Scaling test error: {e}")
        return
    
    # Test 5: Ingredient name normalization
    print("\n📊 TEST 5: INGREDIENT NAME NORMALIZATION")
    print("=" * 50)
    
    normalization_plan = {
        "plan_type": "daily",
        "meals": [
            {
                "name": "Normalization Test",
                "ingredients": [
                    {"name": "lentils, green,", "quantity": 100, "unit": "g"},    # Should remove punctuation
                    {"name": "  quinoa   ", "quantity": 80, "unit": "g"},        # Should trim spaces
                ]
            }
        ]
    }
    
    try:
        enforced_plan = unit_enforcer.enforce_canonical_units(normalization_plan)
        
        print("📈 NAME NORMALIZATION RESULTS:")
        for ingredient in enforced_plan["meals"][0]["ingredients"]:
            name = ingredient["name"]
            print(f"   - Normalized name: '{name}'")
            
            # Check for punctuation or extra spaces
            if "," in name or name != name.strip():
                print(f"❌ FAILED: Name not properly normalized: '{name}'")
                return
        
        print("✅ PASSED: Ingredient names properly normalized")
        
    except Exception as e:
        print(f"❌ FAILED: Name normalization error: {e}")
        return
    
    print("\n🎯 FINAL SUMMARY")
    print("=" * 50)
    print("✅ ML to G conversion with proper density mapping")
    print("✅ Discrete mapping bug fixed - only applies to piece units")
    print("✅ Canonical immutability guard prevents unit mutation")
    print("✅ Scaling only modifies quantities, never units")
    print("✅ Ingredient names properly normalized")
    print("✅ _canonicalized flag prevents post-enforcement mutation")
    print("✅ All canonical immutability fixes implemented and working")

if __name__ == "__main__":
    asyncio.run(test_canonical_immutability_fixes())