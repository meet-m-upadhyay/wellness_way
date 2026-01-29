#!/usr/bin/env python3
"""
Debug Nutrition Aggregation Issue

Reproduces the exact zero nutrition aggregation bug from the logs.
"""

from app.services.plan_validation import DietPlanValidator

def test_aggregation_issue():
    """Test the exact aggregation issue from the logs"""
    
    # This is the structure that plan validation receives (from API format conversion)
    test_plan = {
        "plan_type": "daily",
        "date": "2024-01-26",
        "meals": [
            {
                "type": "breakfast",
                "name": "Greek Yogurt and Hemp Seed Delight",
                "ingredients": [
                    {
                        "name": "greek yogurt plain",  # ← Original name, not canonical
                        "quantity": 150,
                        "unit": "g"
                        # ← NO nutrition field on ingredients
                    }
                ],
                "instructions": "Mix and serve",
                "nutrition": {
                    "calories": 0.0,  # ← This should be ~150 but shows 0
                    "protein": 0.0,   # ← This should be ~15 but shows 0
                    "carbohydrates": 0.0,
                    "fat": 0.0,
                    "fiber": 0.0,
                    "sodium": 0.0
                }
            }
        ]
    }
    
    print("🔍 Testing nutrition aggregation with zero nutrition structure...")
    print(f"Plan structure: {test_plan}")
    
    validator = DietPlanValidator()
    
    # This will trigger the [AGG DEBUG] logs showing the issue
    calories, protein = validator._extract_daily_totals(test_plan)
    
    print(f"\n📈 AGGREGATION RESULTS:")
    print(f"Calories: {calories}")
    print(f"Protein: {protein}")
    
    if calories == 0 or protein == 0:
        print("❌ BUG REPRODUCED: Zero nutrition in aggregation")
        return False
    else:
        print("✅ Aggregation working correctly")
        return True

if __name__ == "__main__":
    success = test_aggregation_issue()
    if not success:
        print("\n🚨 This reproduces the exact bug from the logs!")
        exit(1)