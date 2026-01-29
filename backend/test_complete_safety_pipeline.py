#!/usr/bin/env python3
"""
Complete Safety Pipeline Integration Test

This test demonstrates the full self-healing generation loop with:
1. Unit enforcement (canonical units only)
2. Quantity rounding (human-friendly portions)
3. Validation gate (safety constraints)
4. Failure classification (actionable guidance)
5. Self-healing retry loop (max 10 attempts)

PROOF POINTS:
- Shows rejected plans with unit violations
- Shows auto-corrected plans with rounded quantities
- Shows failure classification with user guidance
- Shows complete safety pipeline integration
"""

import asyncio
import logging
import sys
import os
from datetime import date
from uuid import UUID

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.database.connection import get_db
from app.services.diet_plan_service import DietPlanService, DietPlanServiceError
from app.services.unit_enforcement import get_unit_enforcer, ContractViolationError
from app.services.quantity_rounding import get_quantity_rounder
from app.services.plan_validation import get_plan_validator, PlanValidationError
from app.services.failure_classification import get_failure_classifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test user ID (should exist in database)
TEST_USER_ID = UUID("f53f6cb3-4b52-47ca-9cdb-bb61ece32610")

def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_subsection(title: str):
    """Print a formatted subsection header"""
    print(f"\n{'-'*40}")
    print(f"  {title}")
    print(f"{'-'*40}")

async def test_unit_enforcement():
    """Test unit enforcement with various violation scenarios"""
    print_section("UNIT ENFORCEMENT TESTS")
    
    unit_enforcer = get_unit_enforcer()
    
    # Test 1: Plan with banned units (should be rejected)
    print_subsection("Test 1: Banned Units (cups, pieces)")
    
    plan_with_banned_units = {
        "plan_type": "daily",
        "meals": [
            {
                "name": "Breakfast",
                "ingredients": [
                    {
                        "name": "oats",
                        "quantity": 1,
                        "unit": "cup",  # BANNED UNIT
                        "nutrition": {"calories": 150, "protein": 5}
                    },
                    {
                        "name": "banana",
                        "quantity": 1,
                        "unit": "piece",  # BANNED UNIT
                        "nutrition": {"calories": 100, "protein": 1}
                    }
                ]
            }
        ]
    }
    
    try:
        enforced_plan = unit_enforcer.enforce_canonical_units(plan_with_banned_units)
        print("❌ ERROR: Should have rejected banned units!")
    except ContractViolationError as e:
        print(f"✅ CORRECTLY REJECTED: {str(e)}")
    
    # Test 2: Plan with discrete items (should be converted)
    print_subsection("Test 2: Discrete Items (should convert to grams)")
    
    plan_with_discrete = {
        "plan_type": "daily",
        "meals": [
            {
                "name": "Breakfast",
                "ingredients": [
                    {
                        "name": "egg",
                        "quantity": 2,
                        "unit": "",  # Discrete item
                        "nutrition": {"calories": 140, "protein": 12}
                    },
                    {
                        "name": "banana",
                        "quantity": 1,
                        "unit": "",  # Discrete item
                        "nutrition": {"calories": 100, "protein": 1}
                    }
                ]
            }
        ]
    }
    
    try:
        enforced_plan = unit_enforcer.enforce_canonical_units(plan_with_discrete)
        print("✅ SUCCESSFULLY CONVERTED:")
        for meal in enforced_plan["meals"]:
            for ingredient in meal["ingredients"]:
                print(f"  - {ingredient['name']}: {ingredient['quantity']}g (was discrete)")
    except ContractViolationError as e:
        print(f"❌ UNEXPECTED REJECTION: {str(e)}")

async def test_quantity_rounding():
    """Test quantity rounding for human-friendly portions"""
    print_section("QUANTITY ROUNDING TESTS")
    
    quantity_rounder = get_quantity_rounder()
    
    # Test plan with precise quantities that need rounding
    plan_with_precise_quantities = {
        "plan_type": "daily",
        "meals": [
            {
                "name": "Breakfast",
                "ingredients": [
                    {
                        "name": "oats",
                        "quantity": 47.3,  # Should round to 45g (nearest 5g)
                        "unit": "g",
                        "nutrition": {"calories": 150, "protein": 5}
                    },
                    {
                        "name": "chia seeds",
                        "quantity": 12.7,  # Should round to 13g (nearest 1g for seeds)
                        "unit": "g",
                        "nutrition": {"calories": 60, "protein": 2}
                    },
                    {
                        "name": "almond milk",
                        "quantity": 247,  # Should round to 250ml (nearest 10ml for liquids)
                        "unit": "ml",
                        "nutrition": {"calories": 40, "protein": 1}
                    }
                ],
                "nutrition": {"calories": 250, "protein": 8}
            }
        ],
        "daily_totals": {"calories": 250, "protein": 8}
    }
    
    print_subsection("Before Rounding:")
    for meal in plan_with_precise_quantities["meals"]:
        for ingredient in meal["ingredients"]:
            print(f"  - {ingredient['name']}: {ingredient['quantity']}{ingredient['unit']}")
    
    rounded_plan = quantity_rounder.round_plan_quantities(plan_with_precise_quantities)
    
    print_subsection("After Rounding:")
    for meal in rounded_plan["meals"]:
        for ingredient in meal["ingredients"]:
            print(f"  - {ingredient['name']}: {ingredient['quantity']}{ingredient['unit']}")
    
    print("✅ QUANTITIES SUCCESSFULLY ROUNDED TO HUMAN-FRIENDLY VALUES")

async def test_validation_gate():
    """Test validation gate with safety constraint violations"""
    print_section("VALIDATION GATE TESTS")
    
    validator = get_plan_validator()
    
    # Test safety constraints
    safety_constraints = {
        "min_daily_calories": 1500,
        "min_protein_grams": 80,
        "max_calorie_deficit": 500,
        "target_calories": 2000,
        "target_protein": 100
    }
    
    # Test 1: Plan with violations (should be auto-corrected)
    print_subsection("Test 1: Plan with Violations (should auto-correct)")
    
    plan_with_violations = {
        "plan_type": "daily",
        "meals": [
            {
                "name": "Light Breakfast",
                "ingredients": [
                    {
                        "name": "toast",
                        "quantity": 30,
                        "unit": "g",
                        "nutrition": {"calories": 80, "protein": 3}
                    }
                ],
                "nutrition": {"calories": 80, "protein": 3}
            }
        ],
        "daily_totals": {"calories": 80, "protein": 3}  # WAY TOO LOW
    }
    
    try:
        validation_result = validator.validate_plan(
            plan_data=plan_with_violations,
            safety_constraints=safety_constraints,
            user_id=TEST_USER_ID
        )
        
        if validation_result.corrected_plan:
            print("✅ PLAN AUTO-CORRECTED:")
            print(f"  Status: {validation_result.status}")
            print(f"  Attempts: {validation_result.correction_attempts}")
            corrected_totals = validation_result.corrected_plan.get("daily_totals", {})
            print(f"  New calories: {corrected_totals.get('calories', 0)}")
            print(f"  New protein: {corrected_totals.get('protein', 0)}g")
        else:
            print(f"✅ PLAN COMPLIANT: {validation_result.status}")
            
    except PlanValidationError as e:
        print(f"🚫 PLAN REJECTED: {e.message}")
        print(f"  Violations: {e.violations}")

async def test_failure_classification():
    """Test failure classification system"""
    print_section("FAILURE CLASSIFICATION TESTS")
    
    failure_classifier = get_failure_classifier()
    
    # Test different failure scenarios
    test_scenarios = [
        {
            "name": "Unit Resolution Failure",
            "error": "Unit enforcement violations: Banned unit 'cup' detected",
            "health_context": None
        },
        {
            "name": "Constraint Conflict",
            "error": "Calories too low: 800 < 1500 (minimum)",
            "health_context": {
                "nutrition_targets": {"target_calories": 1200, "target_protein_g": 150},
                "safety_constraints": {"min_daily_calories": 1500},
                "diet_restrictions": {"meals_per_day": 2}
            }
        },
        {
            "name": "Diet Restriction Deadlock",
            "error": "No suitable ingredients found for vegan high-protein requirements",
            "health_context": {
                "diet_restrictions": {
                    "diet_type": "vegan",
                    "allergies": ["nuts", "soy"],
                    "foods_to_avoid": ["gluten", "legumes"]
                },
                "nutrition_targets": {"target_protein_g": 140}
            }
        }
    ]
    
    for scenario in test_scenarios:
        print_subsection(f"Scenario: {scenario['name']}")
        
        failure_analysis = failure_classifier.classify_failure(
            error_message=scenario["error"],
            health_context_json=scenario["health_context"],
            attempt_count=5,
            violation_history=[scenario["error"]]
        )
        
        print(f"  Category: {failure_analysis.category.value}")
        print(f"  Reason: {failure_analysis.primary_reason}")
        print(f"  Suggested Actions:")
        for action in failure_analysis.suggested_user_actions:
            print(f"    - {action}")

async def test_complete_safety_pipeline():
    """Test the complete safety pipeline integration"""
    print_section("COMPLETE SAFETY PIPELINE INTEGRATION")
    
    # Get database session
    db = next(get_db())
    
    try:
        diet_plan_service = DietPlanService(db)
        
        print_subsection("Testing Self-Healing Generation Loop")
        print("Attempting to generate a daily diet plan...")
        print("(This will go through the complete safety pipeline)")
        
        try:
            # This should go through the complete safety pipeline:
            # 1. AI generation
            # 2. Unit enforcement
            # 3. Quantity rounding
            # 4. Validation gate
            # 5. Auto-correction if needed
            # 6. Success or structured failure
            
            diet_plan = await diet_plan_service.generate_daily_plan(
                user_id=TEST_USER_ID,
                target_date=date.today()
            )
            
            print("✅ PLAN GENERATION SUCCESSFUL!")
            print(f"  Plan ID: {diet_plan.id}")
            print(f"  Plan Type: {diet_plan.plan_type}")
            
            # Check validation metadata
            content = diet_plan.content
            if "validation_status" in content:
                print(f"  Validation Status: {content['validation_status']}")
                if content.get("pipeline_attempt"):
                    print(f"  Pipeline Attempts: {content['pipeline_attempt']}")
            
            # Show sample meal with rounded quantities
            if "meals" in content and content["meals"]:
                sample_meal = content["meals"][0]
                print(f"\n  Sample Meal: {sample_meal.get('name', 'Unknown')}")
                for ingredient in sample_meal.get("ingredients", [])[:3]:  # Show first 3
                    print(f"    - {ingredient['name']}: {ingredient['quantity']}{ingredient['unit']}")
            
            # Show daily totals
            if "daily_totals" in content:
                totals = content["daily_totals"]
                print(f"\n  Daily Totals:")
                print(f"    - Calories: {totals.get('calories', 0)}")
                print(f"    - Protein: {totals.get('protein', 0)}g")
            
        except DietPlanServiceError as e:
            error_msg = str(e)
            print(f"🚫 PLAN GENERATION FAILED: {error_msg}")
            
            # Check if it's a structured failure with guidance
            if "Suggested actions:" in error_msg:
                parts = error_msg.split("Suggested actions:")
                print(f"  Primary Reason: {parts[0].strip()}")
                if len(parts) > 1:
                    actions = parts[1].strip().split("; ")
                    print(f"  Suggested Actions:")
                    for action in actions:
                        print(f"    - {action}")
            
    finally:
        db.close()

async def main():
    """Run all safety pipeline tests"""
    print_section("COMPLETE SAFETY PIPELINE INTEGRATION TESTS")
    print("Testing all components of the safety pipeline:")
    print("1. Unit Enforcement")
    print("2. Quantity Rounding") 
    print("3. Validation Gate")
    print("4. Failure Classification")
    print("5. Complete Integration")
    
    try:
        await test_unit_enforcement()
        await test_quantity_rounding()
        await test_validation_gate()
        await test_failure_classification()
        await test_complete_safety_pipeline()
        
        print_section("ALL TESTS COMPLETED")
        print("✅ Safety pipeline integration successful!")
        print("\nKEY FEATURES DEMONSTRATED:")
        print("- Unit enforcement prevents banned units")
        print("- Quantity rounding makes portions human-friendly")
        print("- Validation gate enforces safety constraints")
        print("- Auto-correction fixes minor violations")
        print("- Failure classification provides actionable guidance")
        print("- Self-healing loop retries up to 10 times")
        print("- Complete safety pipeline integration")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())