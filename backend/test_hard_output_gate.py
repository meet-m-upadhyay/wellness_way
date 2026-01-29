#!/usr/bin/env python3
"""
HARD OUTPUT GATE VALIDATION TEST

This test demonstrates that the backend enforces safety constraints
and prevents unsafe diet plans from reaching the UI.

CRITICAL PROOF POINTS:
1. Plans violating safety constraints are REJECTED
2. Auto-correction works within limits
3. UI never receives non-compliant plans with nutrition data
4. All safety constraints are enforced at runtime
"""

import asyncio
import logging
import json
from typing import Dict, Any
from uuid import UUID, uuid4

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import validation components
from app.services.plan_validation import get_plan_validator, PlanValidationError


def create_unsafe_plan_low_calories() -> Dict[str, Any]:
    """Create a plan that violates minimum calorie constraint"""
    return {
        "plan_type": "daily",
        "date": "2024-01-15",
        "day_name": "Monday",
        "meals": [
            {
                "name": "Light Breakfast",
                "meal_type": "breakfast",
                "ingredients": [
                    {
                        "name": "apple",
                        "quantity": 100,
                        "unit": "g",
                        "nutrition": {
                            "calories": 52,
                            "protein": 0.3,
                            "carbohydrates": 14,
                            "fat": 0.2,
                            "fiber": 2.4,
                            "sodium": 1
                        }
                    }
                ],
                "instructions": "Eat the apple",
                "nutrition": {
                    "calories": 52,
                    "protein": 0.3,
                    "carbohydrates": 14,
                    "fat": 0.2,
                    "fiber": 2.4,
                    "sodium": 1
                }
            },
            {
                "name": "Light Lunch",
                "meal_type": "lunch",
                "ingredients": [
                    {
                        "name": "lettuce",
                        "quantity": 50,
                        "unit": "g",
                        "nutrition": {
                            "calories": 8,
                            "protein": 0.7,
                            "carbohydrates": 1.5,
                            "fat": 0.1,
                            "fiber": 0.6,
                            "sodium": 3
                        }
                    }
                ],
                "instructions": "Eat the lettuce",
                "nutrition": {
                    "calories": 8,
                    "protein": 0.7,
                    "carbohydrates": 1.5,
                    "fat": 0.1,
                    "fiber": 0.6,
                    "sodium": 3
                }
            }
        ],
        "daily_totals": {
            "calories": 60,  # WAY TOO LOW - violates minimum 1200
            "protein": 1.0,   # WAY TOO LOW - violates minimum 50g
            "carbohydrates": 15.5,
            "fat": 0.3,
            "fiber": 3.0,
            "sodium": 4
        }
    }


def create_unsafe_plan_low_protein() -> Dict[str, Any]:
    """Create a plan that violates minimum protein constraint"""
    return {
        "plan_type": "daily",
        "date": "2024-01-15",
        "day_name": "Monday",
        "meals": [
            {
                "name": "High Carb Breakfast",
                "meal_type": "breakfast",
                "ingredients": [
                    {
                        "name": "white rice (cooked)",
                        "quantity": 300,
                        "unit": "g",
                        "nutrition": {
                            "calories": 390,
                            "protein": 7.1,
                            "carbohydrates": 79,
                            "fat": 0.6,
                            "fiber": 0.4,
                            "sodium": 5
                        }
                    }
                ],
                "instructions": "Eat the rice",
                "nutrition": {
                    "calories": 390,
                    "protein": 7.1,
                    "carbohydrates": 79,
                    "fat": 0.6,
                    "fiber": 0.4,
                    "sodium": 5
                }
            },
            {
                "name": "High Carb Lunch",
                "meal_type": "lunch",
                "ingredients": [
                    {
                        "name": "pasta (cooked)",
                        "quantity": 400,
                        "unit": "g",
                        "nutrition": {
                            "calories": 560,
                            "protein": 20,
                            "carbohydrates": 110,
                            "fat": 2.2,
                            "fiber": 6,
                            "sodium": 6
                        }
                    }
                ],
                "instructions": "Eat the pasta",
                "nutrition": {
                    "calories": 560,
                    "protein": 20,
                    "carbohydrates": 110,
                    "fat": 2.2,
                    "fiber": 6,
                    "sodium": 6
                }
            },
            {
                "name": "High Carb Dinner",
                "meal_type": "dinner",
                "ingredients": [
                    {
                        "name": "bread",
                        "quantity": 200,
                        "unit": "g",
                        "nutrition": {
                            "calories": 520,
                            "protein": 16,
                            "carbohydrates": 100,
                            "fat": 6,
                            "fiber": 8,
                            "sodium": 1000
                        }
                    }
                ],
                "instructions": "Eat the bread",
                "nutrition": {
                    "calories": 520,
                    "protein": 16,
                    "carbohydrates": 100,
                    "fat": 6,
                    "fiber": 8,
                    "sodium": 1000
                }
            }
        ],
        "daily_totals": {
            "calories": 1470,  # Adequate calories
            "protein": 43.1,   # TOO LOW - violates minimum 50g protein
            "carbohydrates": 289,
            "fat": 8.8,
            "fiber": 14.4,
            "sodium": 1011
        }
    }


def create_correctable_plan() -> Dict[str, Any]:
    """Create a plan that can be auto-corrected"""
    return {
        "plan_type": "daily",
        "date": "2024-01-15",
        "day_name": "Monday",
        "meals": [
            {
                "name": "Protein Breakfast",
                "meal_type": "breakfast",
                "ingredients": [
                    {
                        "name": "eggs",
                        "quantity": 100,  # 2 eggs
                        "unit": "g",
                        "nutrition": {
                            "calories": 155,
                            "protein": 13,
                            "carbohydrates": 1.1,
                            "fat": 11,
                            "fiber": 0,
                            "sodium": 124
                        }
                    },
                    {
                        "name": "oats (dry)",
                        "quantity": 40,
                        "unit": "g",
                        "nutrition": {
                            "calories": 150,
                            "protein": 5,
                            "carbohydrates": 27,
                            "fat": 3,
                            "fiber": 4,
                            "sodium": 2
                        }
                    }
                ],
                "instructions": "Scramble eggs and serve with oatmeal",
                "nutrition": {
                    "calories": 305,
                    "protein": 18,
                    "carbohydrates": 28.1,
                    "fat": 14,
                    "fiber": 4,
                    "sodium": 126
                }
            },
            {
                "name": "Protein Lunch",
                "meal_type": "lunch",
                "ingredients": [
                    {
                        "name": "chicken breast",
                        "quantity": 80,  # Small portion - can be increased
                        "unit": "g",
                        "nutrition": {
                            "calories": 132,
                            "protein": 25,
                            "carbohydrates": 0,
                            "fat": 3,
                            "fiber": 0,
                            "sodium": 63
                        }
                    },
                    {
                        "name": "quinoa (cooked)",
                        "quantity": 100,
                        "unit": "g",
                        "nutrition": {
                            "calories": 120,
                            "protein": 4.4,
                            "carbohydrates": 22,
                            "fat": 1.9,
                            "fiber": 2.8,
                            "sodium": 7
                        }
                    }
                ],
                "instructions": "Grill chicken and serve with quinoa",
                "nutrition": {
                    "calories": 252,
                    "protein": 29.4,
                    "carbohydrates": 22,
                    "fat": 4.9,
                    "fiber": 2.8,
                    "sodium": 70
                }
            }
        ],
        "daily_totals": {
            "calories": 557,   # TOO LOW - but correctable by increasing portions
            "protein": 47.4,   # CLOSE to minimum 50g - correctable
            "carbohydrates": 50.1,
            "fat": 18.9,
            "fiber": 6.8,
            "sodium": 196
        }
    }


def create_compliant_plan() -> Dict[str, Any]:
    """Create a plan that meets all safety constraints"""
    return {
        "plan_type": "daily",
        "date": "2024-01-15",
        "day_name": "Monday",
        "meals": [
            {
                "name": "Balanced Breakfast",
                "meal_type": "breakfast",
                "ingredients": [
                    {
                        "name": "eggs",
                        "quantity": 150,  # 3 eggs
                        "unit": "g",
                        "nutrition": {
                            "calories": 233,
                            "protein": 19.5,
                            "carbohydrates": 1.7,
                            "fat": 16.5,
                            "fiber": 0,
                            "sodium": 186
                        }
                    },
                    {
                        "name": "oats (dry)",
                        "quantity": 80,  # Larger portion
                        "unit": "g",
                        "nutrition": {
                            "calories": 300,
                            "protein": 10,
                            "carbohydrates": 54,
                            "fat": 6,
                            "fiber": 8,
                            "sodium": 4
                        }
                    }
                ],
                "instructions": "Scramble eggs and serve with oatmeal",
                "nutrition": {
                    "calories": 533,
                    "protein": 29.5,
                    "carbohydrates": 55.7,
                    "fat": 22.5,
                    "fiber": 8,
                    "sodium": 190
                }
            },
            {
                "name": "Balanced Lunch",
                "meal_type": "lunch",
                "ingredients": [
                    {
                        "name": "chicken breast",
                        "quantity": 150,  # Larger portion
                        "unit": "g",
                        "nutrition": {
                            "calories": 248,
                            "protein": 46.9,
                            "carbohydrates": 0,
                            "fat": 5.6,
                            "fiber": 0,
                            "sodium": 119
                        }
                    },
                    {
                        "name": "quinoa (cooked)",
                        "quantity": 200,  # Larger portion
                        "unit": "g",
                        "nutrition": {
                            "calories": 240,
                            "protein": 8.8,
                            "carbohydrates": 44,
                            "fat": 3.8,
                            "fiber": 5.6,
                            "sodium": 14
                        }
                    }
                ],
                "instructions": "Grill chicken and serve with quinoa",
                "nutrition": {
                    "calories": 488,
                    "protein": 55.7,
                    "carbohydrates": 44,
                    "fat": 9.4,
                    "fiber": 5.6,
                    "sodium": 133
                }
            },
            {
                "name": "Balanced Dinner",
                "meal_type": "dinner",
                "ingredients": [
                    {
                        "name": "salmon",
                        "quantity": 120,  # Larger portion
                        "unit": "g",
                        "nutrition": {
                            "calories": 250,
                            "protein": 30.5,
                            "carbohydrates": 0,
                            "fat": 13.2,
                            "fiber": 0,
                            "sodium": 71
                        }
                    },
                    {
                        "name": "sweet potato",
                        "quantity": 200,  # Larger portion
                        "unit": "g",
                        "nutrition": {
                            "calories": 172,
                            "protein": 3.1,
                            "carbohydrates": 40,
                            "fat": 0.3,
                            "fiber": 6,
                            "sodium": 11
                        }
                    }
                ],
                "instructions": "Bake salmon and sweet potato",
                "nutrition": {
                    "calories": 422,
                    "protein": 33.6,
                    "carbohydrates": 40,
                    "fat": 13.5,
                    "fiber": 6,
                    "sodium": 82
                }
            }
        ],
        "daily_totals": {
            "calories": 1443,  # WELL ABOVE minimum 1200 ✓
            "protein": 118.8,  # WELL ABOVE minimum 50g ✓
            "carbohydrates": 139.7,
            "fat": 45.4,
            "fiber": 19.6,
            "sodium": 405
        }
    }


def test_rejected_plan_low_calories():
    """Test that plans with insufficient calories are REJECTED"""
    print("\n🔒 TEST 1: REJECTED PLAN (Low Calories)")
    print("=" * 50)
    
    validator = get_plan_validator()
    unsafe_plan = create_unsafe_plan_low_calories()
    
    safety_constraints = {
        "min_daily_calories": 1200,
        "min_protein_grams": 50,
        "max_calorie_deficit": 500
    }
    
    user_id = uuid4()
    
    try:
        result = validator.validate_plan(unsafe_plan, safety_constraints, user_id)
        print("❌ ERROR: Plan should have been REJECTED but was accepted!")
        return False
    except PlanValidationError as e:
        print(f"✅ Plan CORRECTLY REJECTED")
        print(f"   Violations: {e.violations}")
        print(f"   Message: {e.message}")
        print(f"   Nutrition data included: {e.plan_data is not None}")
        
        # Verify no nutrition data in rejected plan
        if e.plan_data is not None:
            print("❌ ERROR: Rejected plan includes nutrition data!")
            return False
        
        return True


def test_rejected_plan_low_protein():
    """Test that plans with insufficient protein that cannot be corrected are REJECTED"""
    print("\n🔒 TEST 2: REJECTED PLAN (Low Protein - Uncorrectable)")
    print("=" * 50)
    
    validator = get_plan_validator()
    
    # Create a plan with NO protein sources that cannot be corrected
    unsafe_plan = {
        "plan_type": "daily",
        "date": "2024-01-15",
        "day_name": "Monday",
        "meals": [
            {
                "name": "Pure Sugar",
                "meal_type": "breakfast",
                "ingredients": [
                    {
                        "name": "sugar",
                        "quantity": 100,
                        "unit": "g",
                        "nutrition": {
                            "calories": 400,
                            "protein": 0,  # Zero protein - cannot be increased
                            "carbohydrates": 100,
                            "fat": 0,
                            "fiber": 0,
                            "sodium": 0
                        }
                    }
                ],
                "instructions": "Eat sugar",
                "nutrition": {
                    "calories": 400,
                    "protein": 0,
                    "carbohydrates": 100,
                    "fat": 0,
                    "fiber": 0,
                    "sodium": 0
                }
            },
            {
                "name": "Pure Oil",
                "meal_type": "lunch",
                "ingredients": [
                    {
                        "name": "vegetable oil",
                        "quantity": 100,
                        "unit": "ml",
                        "nutrition": {
                            "calories": 800,
                            "protein": 0,  # Zero protein - cannot be increased
                            "carbohydrates": 0,
                            "fat": 90,
                            "fiber": 0,
                            "sodium": 0
                        }
                    }
                ],
                "instructions": "Drink oil",
                "nutrition": {
                    "calories": 800,
                    "protein": 0,
                    "carbohydrates": 0,
                    "fat": 90,
                    "fiber": 0,
                    "sodium": 0
                }
            }
        ],
        "daily_totals": {
            "calories": 1200,  # Meets calorie minimum
            "protein": 0,      # ZERO protein - impossible to correct by increasing portions
            "carbohydrates": 100,
            "fat": 90,
            "fiber": 0,
            "sodium": 0
        }
    }
    
    safety_constraints = {
        "min_daily_calories": 1200,
        "min_protein_grams": 50,
        "max_calorie_deficit": 500
    }
    
    user_id = uuid4()
    
    print("Plan nutrition (uncorrectable):")
    print(f"   Calories: {unsafe_plan['daily_totals']['calories']} (meets minimum)")
    print(f"   Protein: {unsafe_plan['daily_totals']['protein']}g (ZERO - cannot increase)")
    
    try:
        result = validator.validate_plan(unsafe_plan, safety_constraints, user_id)
        print("❌ ERROR: Plan should have been REJECTED but was accepted!")
        print(f"   Status: {result.status}")
        if result.corrected_plan:
            corrected_protein = result.corrected_plan['daily_totals']['protein']
            print(f"   Corrected protein: {corrected_protein}g")
        return False
    except PlanValidationError as e:
        print(f"✅ Plan CORRECTLY REJECTED")
        print(f"   Violations: {e.violations}")
        print(f"   Message: {e.message}")
        print(f"   Nutrition data included: {e.plan_data is not None}")
        
        # Verify no nutrition data in rejected plan
        if e.plan_data is not None:
            print("❌ ERROR: Rejected plan includes nutrition data!")
            return False
        
        return True


def test_auto_corrected_plan():
    """Test that borderline plans are AUTO-CORRECTED"""
    print("\n🔧 TEST 3: AUTO-CORRECTED PLAN")
    print("=" * 50)
    
    validator = get_plan_validator()
    correctable_plan = create_correctable_plan()
    
    safety_constraints = {
        "min_daily_calories": 1200,
        "min_protein_grams": 50,
        "max_calorie_deficit": 500
    }
    
    user_id = uuid4()
    
    print("BEFORE correction:")
    print(f"   Calories: {correctable_plan['daily_totals']['calories']}")
    print(f"   Protein: {correctable_plan['daily_totals']['protein']}g")
    
    try:
        result = validator.validate_plan(correctable_plan, safety_constraints, user_id)
        
        if result.status == "auto_corrected":
            print(f"✅ Plan AUTO-CORRECTED successfully")
            print(f"   Status: {result.status}")
            print(f"   Attempts: {result.correction_attempts}")
            
            if result.corrected_plan:
                corrected_totals = result.corrected_plan['daily_totals']
                print("AFTER correction:")
                print(f"   Calories: {corrected_totals['calories']}")
                print(f"   Protein: {corrected_totals['protein']}g")
                
                # Verify constraints are now met
                if (corrected_totals['calories'] >= safety_constraints['min_daily_calories'] and
                    corrected_totals['protein'] >= safety_constraints['min_protein_grams']):
                    print("✅ All safety constraints now satisfied")
                    return True
                else:
                    print("❌ ERROR: Corrected plan still violates constraints!")
                    return False
            else:
                print("❌ ERROR: No corrected plan returned!")
                return False
        else:
            print(f"❌ ERROR: Expected auto-correction but got status: {result.status}")
            return False
            
    except PlanValidationError as e:
        print(f"❌ ERROR: Plan should have been corrected but was rejected: {e.message}")
        return False


def test_compliant_plan():
    """Test that compliant plans pass validation"""
    print("\n✅ TEST 4: COMPLIANT PLAN")
    print("=" * 50)
    
    validator = get_plan_validator()
    compliant_plan = create_compliant_plan()
    
    safety_constraints = {
        "min_daily_calories": 1200,
        "min_protein_grams": 50,
        "max_calorie_deficit": 500
    }
    
    user_id = uuid4()
    
    print("Plan nutrition:")
    print(f"   Calories: {compliant_plan['daily_totals']['calories']}")
    print(f"   Protein: {compliant_plan['daily_totals']['protein']}g")
    
    try:
        result = validator.validate_plan(compliant_plan, safety_constraints, user_id)
        
        if result.status in ["compliant", "auto_corrected"]:
            print(f"✅ Plan VALID - status: {result.status}")
            print(f"   Violations: {result.violations}")
            return True
        else:
            print(f"❌ ERROR: Unexpected status: {result.status}")
            return False
            
    except PlanValidationError as e:
        print(f"❌ ERROR: Valid plan was rejected: {e.message}")
        return False


def main():
    """Run all validation tests"""
    print("🔒 HARD OUTPUT GATE VALIDATION TESTS")
    print("=" * 60)
    print("Testing that unsafe diet plans CANNOT reach the UI")
    print("=" * 60)
    
    tests = [
        test_rejected_plan_low_calories,
        test_rejected_plan_low_protein,
        test_auto_corrected_plan,
        test_compliant_plan
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ TEST FAILED with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"Test {i+1}: {test.__name__} - {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Hard output gate is working correctly!")
        print("✅ Unsafe plans CANNOT reach the UI")
        print("✅ Auto-correction works within limits")
        print("✅ Safety constraints are enforced at runtime")
    else:
        print("🚨 SOME TESTS FAILED - Hard output gate needs fixes!")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)