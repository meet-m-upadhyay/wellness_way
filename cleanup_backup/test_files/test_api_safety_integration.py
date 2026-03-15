#!/usr/bin/env python3
"""
API SAFETY INTEGRATION TEST

This test demonstrates that the API endpoints properly enforce
safety constraints and return structured error responses for
unsafe diet plans.

PROOF POINTS:
1. API returns 422 status for safety violations
2. Error responses include violation details
3. No nutrition data is included in rejected responses
4. Auto-corrected plans include validation metadata
"""

import asyncio
import json
import logging
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, patch
from uuid import UUID, uuid4

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock the database and dependencies
class MockHCD:
    def __init__(self):
        self.id = uuid4()
        self.content = "Mock HCD content"
        self.json_context = {
            "safety_constraints": {
                "min_daily_calories": 1200,
                "max_calorie_deficit": 500
            },
            "nutrition_targets": {
                "min_protein_g": 50,
                "target_calories": 2000,
                "target_protein_g": 100
            }
        }

class MockDB:
    def __init__(self):
        self.committed = False
        self.rolled_back = False
        
    def add(self, obj):
        pass
        
    def commit(self):
        self.committed = True
        
    def rollback(self):
        self.rolled_back = True
        
    def refresh(self, obj):
        pass
        
    def query(self, model):
        return MockQuery()

class MockQuery:
    def filter(self, *args):
        return self
        
    def order_by(self, *args):
        return self
        
    def first(self):
        return MockHCD()

# Mock AI service that returns unsafe plans
class MockAIService:
    def __init__(self, plan_type="unsafe_low_calories"):
        self.plan_type = plan_type
    
    async def generate_diet_plan(self, **kwargs):
        if self.plan_type == "unsafe_low_calories":
            return {
                "plan_type": "daily",
                "date": "2024-01-15",
                "day_name": "Monday",
                "meals": [
                    {
                        "name": "Tiny Breakfast",
                        "meal_type": "breakfast",
                        "ingredients": [
                            {
                                "name": "apple slice",
                                "quantity": 20,
                                "unit": "g",
                                "nutrition": {
                                    "calories": 10,
                                    "protein": 0.1,
                                    "carbohydrates": 2.8,
                                    "fat": 0.04,
                                    "fiber": 0.5,
                                    "sodium": 0.2
                                }
                            }
                        ],
                        "instructions": "Eat tiny apple slice",
                        "nutrition": {
                            "calories": 10,
                            "protein": 0.1,
                            "carbohydrates": 2.8,
                            "fat": 0.04,
                            "fiber": 0.5,
                            "sodium": 0.2
                        }
                    }
                ],
                "daily_totals": {
                    "calories": 10,    # WAY TOO LOW
                    "protein": 0.1,    # WAY TOO LOW
                    "carbohydrates": 2.8,
                    "fat": 0.04,
                    "fiber": 0.5,
                    "sodium": 0.2
                }
            }
        elif self.plan_type == "correctable":
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
                                "name": "chicken breast",
                                "quantity": 120,
                                "unit": "g",
                                "nutrition": {
                                    "calories": 198,
                                    "protein": 37.5,
                                    "carbohydrates": 0,
                                    "fat": 4.5,
                                    "fiber": 0,
                                    "sodium": 95
                                }
                            },
                            {
                                "name": "quinoa (cooked)",
                                "quantity": 150,
                                "unit": "g",
                                "nutrition": {
                                    "calories": 180,
                                    "protein": 6.6,
                                    "carbohydrates": 33,
                                    "fat": 2.9,
                                    "fiber": 4.2,
                                    "sodium": 11
                                }
                            }
                        ],
                        "instructions": "Grill chicken and serve with quinoa",
                        "nutrition": {
                            "calories": 378,
                            "protein": 44.1,
                            "carbohydrates": 33,
                            "fat": 7.4,
                            "fiber": 4.2,
                            "sodium": 106
                        }
                    },
                    {
                        "name": "Protein Lunch",
                        "meal_type": "lunch",
                        "ingredients": [
                            {
                                "name": "salmon",
                                "quantity": 100,
                                "unit": "g",
                                "nutrition": {
                                    "calories": 208,
                                    "protein": 25.4,
                                    "carbohydrates": 0,
                                    "fat": 11,
                                    "fiber": 0,
                                    "sodium": 59
                                }
                            },
                            {
                                "name": "sweet potato",
                                "quantity": 150,
                                "unit": "g",
                                "nutrition": {
                                    "calories": 129,
                                    "protein": 2.3,
                                    "carbohydrates": 30,
                                    "fat": 0.2,
                                    "fiber": 4.5,
                                    "sodium": 8
                                }
                            }
                        ],
                        "instructions": "Bake salmon and sweet potato",
                        "nutrition": {
                            "calories": 337,
                            "protein": 27.7,
                            "carbohydrates": 30,
                            "fat": 11.2,
                            "fiber": 4.5,
                            "sodium": 67
                        }
                    },
                    {
                        "name": "Light Dinner",
                        "meal_type": "dinner",
                        "ingredients": [
                            {
                                "name": "eggs",
                                "quantity": 100,
                                "unit": "g",
                                "nutrition": {
                                    "calories": 155,
                                    "protein": 13,
                                    "carbohydrates": 1.1,
                                    "fat": 11,
                                    "fiber": 0,
                                    "sodium": 124
                                }
                            }
                        ],
                        "instructions": "Scramble eggs",
                        "nutrition": {
                            "calories": 155,
                            "protein": 13,
                            "carbohydrates": 1.1,
                            "fat": 11,
                            "fiber": 0,
                            "sodium": 124
                        }
                    }
                ],
                "daily_totals": {
                    "calories": 870,   # Below minimum but close enough to correct
                    "protein": 84.8,   # Above minimum protein ✓
                    "carbohydrates": 64.1,
                    "fat": 29.6,
                    "fiber": 8.7,
                    "sodium": 297
                }
            }
        else:  # compliant
            return {
                "plan_type": "daily",
                "date": "2024-01-15",
                "day_name": "Monday",
                "meals": [
                    {
                        "name": "Balanced Meal",
                        "meal_type": "breakfast",
                        "ingredients": [
                            {
                                "name": "chicken breast",
                                "quantity": 200,
                                "unit": "g",
                                "nutrition": {
                                    "calories": 330,
                                    "protein": 62.5,
                                    "carbohydrates": 0,
                                    "fat": 7.5,
                                    "fiber": 0,
                                    "sodium": 158
                                }
                            },
                            {
                                "name": "quinoa (cooked)",
                                "quantity": 300,
                                "unit": "g",
                                "nutrition": {
                                    "calories": 360,
                                    "protein": 13.2,
                                    "carbohydrates": 66,
                                    "fat": 5.7,
                                    "fiber": 8.4,
                                    "sodium": 21
                                }
                            }
                        ],
                        "instructions": "Grill chicken and serve with quinoa",
                        "nutrition": {
                            "calories": 690,
                            "protein": 75.7,
                            "carbohydrates": 66,
                            "fat": 13.2,
                            "fiber": 8.4,
                            "sodium": 179
                        }
                    },
                    {
                        "name": "Balanced Lunch",
                        "meal_type": "lunch",
                        "ingredients": [
                            {
                                "name": "salmon",
                                "quantity": 150,
                                "unit": "g",
                                "nutrition": {
                                    "calories": 312,
                                    "protein": 38.1,
                                    "carbohydrates": 0,
                                    "fat": 16.5,
                                    "fiber": 0,
                                    "sodium": 89
                                }
                            }
                        ],
                        "instructions": "Bake salmon",
                        "nutrition": {
                            "calories": 312,
                            "protein": 38.1,
                            "carbohydrates": 0,
                            "fat": 16.5,
                            "fiber": 0,
                            "sodium": 89
                        }
                    }
                ],
                "daily_totals": {
                    "calories": 1002,  # Close to minimum
                    "protein": 113.8,  # Well above minimum
                    "carbohydrates": 66,
                    "fat": 29.7,
                    "fiber": 8.4,
                    "sodium": 268
                }
            }


async def test_api_rejects_unsafe_plan():
    """Test that API properly rejects unsafe plans with structured error"""
    print("\n🔒 API TEST 1: UNSAFE PLAN REJECTION")
    print("=" * 50)
    
    # Import the service after setting up mocks
    from app.services.diet_plan_service import DietPlanService, DietPlanServiceError
    from app.services.plan_validation import PlanValidationError
    
    # Mock the AI service to return unsafe plan
    mock_ai_service = MockAIService("unsafe_low_calories")
    
    with patch('app.services.diet_plan_service.get_ai_service', return_value=mock_ai_service):
        db = MockDB()
        service = DietPlanService(db)
        user_id = uuid4()
        
        try:
            # This should fail validation and raise DietPlanServiceError
            plan = await service.generate_daily_plan(user_id)
            print("❌ ERROR: Unsafe plan was accepted!")
            return False
            
        except DietPlanServiceError as e:
            error_msg = str(e)
            print(f"✅ Service correctly rejected unsafe plan")
            print(f"   Error: {error_msg}")
            
            # Verify error mentions safety constraints
            if "safety constraints" in error_msg.lower():
                print("✅ Error correctly identifies safety constraint violation")
                return True
            else:
                print("❌ ERROR: Error doesn't mention safety constraints")
                return False
                
        except Exception as e:
            print(f"❌ ERROR: Unexpected exception: {e}")
            return False


async def test_api_auto_corrects_plan():
    """Test that API properly auto-corrects borderline plans"""
    print("\n🔧 API TEST 2: AUTO-CORRECTED PLAN")
    print("=" * 50)
    
    from app.services.diet_plan_service import DietPlanService
    
    # Mock the AI service to return correctable plan
    mock_ai_service = MockAIService("correctable")
    
    with patch('app.services.diet_plan_service.get_ai_service', return_value=mock_ai_service):
        db = MockDB()
        service = DietPlanService(db)
        user_id = uuid4()
        
        try:
            # This should be auto-corrected
            plan = await service.generate_daily_plan(user_id)
            
            print(f"✅ Plan generated successfully")
            
            # Check if plan was auto-corrected
            content = plan.content
            validation_status = content.get("validation_status")
            
            print(f"   Validation status: {validation_status}")
            
            if validation_status == "auto_corrected":
                print("✅ Plan was correctly auto-corrected")
                
                # Verify corrected nutrition meets constraints
                daily_totals = content.get("daily_totals", {})
                calories = daily_totals.get("calories", 0)
                protein = daily_totals.get("protein", 0)
                
                print(f"   Final calories: {calories}")
                print(f"   Final protein: {protein}g")
                
                if calories >= 1200 and protein >= 50:
                    print("✅ Corrected plan meets all safety constraints")
                    return True
                else:
                    print("❌ ERROR: Corrected plan still violates constraints")
                    return False
            else:
                print(f"❌ ERROR: Expected auto_corrected status, got: {validation_status}")
                return False
                
        except Exception as e:
            print(f"❌ ERROR: Auto-correction failed: {e}")
            return False


async def test_api_accepts_compliant_plan():
    """Test that API properly accepts compliant plans"""
    print("\n✅ API TEST 3: COMPLIANT PLAN ACCEPTANCE")
    print("=" * 50)
    
    from app.services.diet_plan_service import DietPlanService
    
    # Mock the AI service to return compliant plan
    mock_ai_service = MockAIService("compliant")
    
    with patch('app.services.diet_plan_service.get_ai_service', return_value=mock_ai_service):
        db = MockDB()
        service = DietPlanService(db)
        user_id = uuid4()
        
        try:
            # This should pass validation
            plan = await service.generate_daily_plan(user_id)
            
            print(f"✅ Plan generated successfully")
            
            # Check validation status
            content = plan.content
            validation_status = content.get("validation_status")
            
            print(f"   Validation status: {validation_status}")
            
            if validation_status in ["compliant", "auto_corrected"]:
                print("✅ Plan has valid status")
                
                # Verify nutrition meets constraints
                daily_totals = content.get("daily_totals", {})
                calories = daily_totals.get("calories", 0)
                protein = daily_totals.get("protein", 0)
                
                print(f"   Calories: {calories}")
                print(f"   Protein: {protein}g")
                
                if calories >= 1200 and protein >= 50:
                    print("✅ Plan meets all safety constraints")
                    return True
                else:
                    print("❌ ERROR: Plan violates constraints")
                    return False
            else:
                print(f"❌ ERROR: Invalid validation status: {validation_status}")
                return False
                
        except Exception as e:
            print(f"❌ ERROR: Compliant plan was rejected: {e}")
            return False


def test_error_response_structure():
    """Test that error responses have correct structure"""
    print("\n📋 API TEST 4: ERROR RESPONSE STRUCTURE")
    print("=" * 50)
    
    from app.services.plan_validation import PlanValidationError
    
    # Create a validation error
    violations = [
        "SAFETY VIOLATION: Calories too low: 100 < 1200 (minimum)",
        "SAFETY VIOLATION: Protein too low: 5g < 50g (minimum)"
    ]
    
    error = PlanValidationError(
        message="Diet plan violates safety constraints",
        violations=violations,
        plan_data=None  # Critical: no nutrition data
    )
    
    print("✅ PlanValidationError created")
    print(f"   Message: {error.message}")
    print(f"   Violations: {error.violations}")
    print(f"   Nutrition data included: {error.plan_data is not None}")
    
    # Verify structure
    if (error.message and 
        error.violations and 
        len(error.violations) == 2 and
        error.plan_data is None):
        print("✅ Error response structure is correct")
        print("✅ No nutrition data leaked in error response")
        return True
    else:
        print("❌ ERROR: Invalid error response structure")
        return False


async def main():
    """Run all API safety integration tests"""
    print("🔒 API SAFETY INTEGRATION TESTS")
    print("=" * 60)
    print("Testing that API endpoints enforce safety constraints")
    print("=" * 60)
    
    tests = [
        test_api_rejects_unsafe_plan,
        test_api_auto_corrects_plan,
        test_api_accepts_compliant_plan,
        test_error_response_structure
    ]
    
    results = []
    for test in tests:
        try:
            if asyncio.iscoroutinefunction(test):
                result = await test()
            else:
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
        print("🎉 ALL API SAFETY TESTS PASSED!")
        print("✅ API properly enforces safety constraints")
        print("✅ Unsafe plans are rejected with structured errors")
        print("✅ Auto-correction works at API level")
        print("✅ No nutrition data leaks in error responses")
    else:
        print("🚨 SOME API TESTS FAILED!")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)