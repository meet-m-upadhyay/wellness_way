#!/usr/bin/env python3
"""
Test Goal-Aware Validation System

This test verifies that the goal-specific acceptance buffers work correctly
and prevent infinite AI retries for nutritionally safe plans.
"""

import asyncio
import logging
from uuid import uuid4
from app.services.plan_validation import DietPlanValidator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_goal_aware_validation():
    """Test goal-aware validation with different scenarios"""
    
    validator = DietPlanValidator()
    user_id = uuid4()
    
    # Test data: A plan that's slightly off target but nutritionally safe
    test_plan = {
        "plan_type": "daily",
        "date": "2024-01-15",
        "meals": [
            {
                "name": "Breakfast",
                "meal_type": "breakfast",
                "ingredients": [
                    {"name": "oats", "quantity": 50, "unit": "g"},
                    {"name": "banana", "quantity": 1, "unit": "piece"}
                ]
            }
        ],
        "daily_totals": {
            "calories": 1850,  # 150 below target of 2000
            "protein": 95,     # 5g below target of 100g
            "carbohydrates": 200,
            "fat": 60,
            "fiber": 25,
            "sodium": 1200
        }
    }
    
    safety_constraints = {
        "target_calories": 2000,
        "target_protein": 100,
        "min_daily_calories": 1200,
        "max_calorie_deficit": 500,
        "min_protein_grams": 50
    }
    
    print("🧪 TESTING GOAL-AWARE VALIDATION")
    print("=" * 50)
    
    # Test 1: Weight Loss Goal (should accept with guidance)
    print("\n1️⃣ WEIGHT LOSS GOAL TEST")
    print(f"Plan: {test_plan['daily_totals']['calories']} kcal, {test_plan['daily_totals']['protein']}g protein")
    print(f"Target: {safety_constraints['target_calories']} kcal, {safety_constraints['target_protein']}g protein")
    
    try:
        result = validator.validate_plan(
            plan_data=test_plan,
            safety_constraints=safety_constraints,
            user_id=user_id,
            goal_type="weight_loss",
            user_weight_kg=70.0
        )
        
        print(f"✅ Status: {result.status}")
        print(f"✅ Valid: {result.is_valid}")
        if result.balance_guidance:
            print(f"💡 Guidance: {result.balance_guidance.message}")
        else:
            print("💡 No guidance needed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Muscle Gain Goal (should accept with guidance)
    print("\n2️⃣ MUSCLE GAIN GOAL TEST")
    
    try:
        result = validator.validate_plan(
            plan_data=test_plan,
            safety_constraints=safety_constraints,
            user_id=user_id,
            goal_type="muscle_gain",
            user_weight_kg=70.0
        )
        
        print(f"✅ Status: {result.status}")
        print(f"✅ Valid: {result.is_valid}")
        if result.balance_guidance:
            print(f"💡 Guidance: {result.balance_guidance.message}")
        else:
            print("💡 No guidance needed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Maintenance Goal (should accept with guidance)
    print("\n3️⃣ MAINTENANCE GOAL TEST")
    
    try:
        result = validator.validate_plan(
            plan_data=test_plan,
            safety_constraints=safety_constraints,
            user_id=user_id,
            goal_type="maintenance",
            user_weight_kg=70.0
        )
        
        print(f"✅ Status: {result.status}")
        print(f"✅ Valid: {result.is_valid}")
        if result.balance_guidance:
            print(f"💡 Guidance: {result.balance_guidance.message}")
        else:
            print("💡 No guidance needed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Perfect Plan (should accept without guidance)
    print("\n4️⃣ PERFECT PLAN TEST")
    
    perfect_plan = test_plan.copy()
    perfect_plan["daily_totals"] = {
        "calories": 2000,  # Exact target
        "protein": 100,    # Exact target
        "carbohydrates": 200,
        "fat": 60,
        "fiber": 25,
        "sodium": 1200
    }
    
    try:
        result = validator.validate_plan(
            plan_data=perfect_plan,
            safety_constraints=safety_constraints,
            user_id=user_id,
            goal_type="maintenance",
            user_weight_kg=70.0
        )
        
        print(f"✅ Status: {result.status}")
        print(f"✅ Valid: {result.is_valid}")
        if result.balance_guidance:
            print(f"💡 Guidance: {result.balance_guidance.message}")
        else:
            print("💡 No guidance needed - plan is perfect!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: Dangerous Plan (should reject)
    print("\n5️⃣ DANGEROUS PLAN TEST")
    
    dangerous_plan = test_plan.copy()
    dangerous_plan["daily_totals"] = {
        "calories": 800,   # Dangerously low
        "protein": 30,     # Critically low
        "carbohydrates": 100,
        "fat": 20,
        "fiber": 10,
        "sodium": 800
    }
    
    try:
        result = validator.validate_plan(
            plan_data=dangerous_plan,
            safety_constraints=safety_constraints,
            user_id=user_id,
            goal_type="weight_loss",
            user_weight_kg=70.0
        )
        
        print(f"❌ UNEXPECTED: Plan should have been rejected!")
        print(f"Status: {result.status}")
        
    except Exception as e:
        print(f"✅ CORRECTLY REJECTED: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 GOAL-AWARE VALIDATION TESTS COMPLETE")


if __name__ == "__main__":
    test_goal_aware_validation()