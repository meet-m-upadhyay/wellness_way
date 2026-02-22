#!/usr/bin/env python3
"""
Test script to trigger aggregation debug logs and see actual meal structure
"""

import asyncio
import logging
from uuid import uuid4
from app.services.plan_validation import DietPlanValidator

# Configure logging to see debug messages
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s:%(name)s:%(message)s'
)

async def test_aggregation_debug():
    """Test aggregation with real meal structure to see debug logs"""
    
    # Create a realistic plan structure that might be causing issues
    test_plan = {
        "plan_type": "daily",
        "date": "2024-01-15",
        "meals": [
            {
                "name": "Greek Yogurt and Hemp Seed Parfait",
                "meal_type": "breakfast",
                "ingredients": [
                    {"name": "greek yogurt", "quantity": 200, "unit": "g"},
                    {"name": "hemp seeds", "quantity": 15, "unit": "g"},
                    {"name": "mixed berries", "quantity": 100, "unit": "g"}
                ],
                "nutrition": {
                    "calories": 467.0,
                    "protein": 22.0,
                    "carbohydrates": 35.0,
                    "fat": 18.0,
                    "fiber": 8.0,
                    "sodium": 120.0
                }
            },
            {
                "name": "Tofu and Quinoa Bowl", 
                "meal_type": "lunch",
                "ingredients": [
                    {"name": "tofu", "quantity": 150, "unit": "g"},
                    {"name": "quinoa", "quantity": 80, "unit": "g"},
                    {"name": "spinach", "quantity": 100, "unit": "g"}
                ],
                "nutrition": {
                    "calories": 534.0,
                    "protein": 28.5,
                    "carbohydrates": 45.0,
                    "fat": 22.0,
                    "fiber": 6.0,
                    "sodium": 180.0
                }
            },
            {
                "name": "Lentil and Spinach Stew",
                "meal_type": "dinner", 
                "ingredients": [
                    {"name": "lentils", "quantity": 120, "unit": "g"},
                    {"name": "spinach", "quantity": 150, "unit": "g"},
                    {"name": "olive oil", "quantity": 10, "unit": "ml"}
                ],
                "nutrition": {
                    "calories": 401.0,
                    "protein": 31.4,
                    "carbohydrates": 38.0,
                    "fat": 12.0,
                    "fiber": 15.0,
                    "sodium": 95.0
                }
            }
        ]
    }
    
    print("🧪 TESTING AGGREGATION DEBUG")
    print("=" * 60)
    
    # Test the aggregation function directly
    validator = DietPlanValidator()
    
    print("📊 Testing _extract_daily_totals with realistic meal structure...")
    print(f"Plan has {len(test_plan['meals'])} meals")
    
    # This should trigger our debug logging
    calories, protein = validator._extract_daily_totals(test_plan)
    
    print(f"\n📈 AGGREGATION RESULTS:")
    print(f"   Calories: {calories}")
    print(f"   Protein: {protein}")
    
    expected_calories = 467.0 + 534.0 + 401.0  # 1402.0
    expected_protein = 22.0 + 28.5 + 31.4      # 81.9
    
    print(f"\n🎯 EXPECTED TOTALS:")
    print(f"   Calories: {expected_calories}")
    print(f"   Protein: {expected_protein}")
    
    if calories == expected_calories and protein == expected_protein:
        print("\n✅ SUCCESS: Aggregation working correctly!")
    else:
        print("\n❌ FAILURE: Aggregation not working correctly!")
        print("   This means the structure-agnostic fix is needed")

if __name__ == "__main__":
    asyncio.run(test_aggregation_debug())