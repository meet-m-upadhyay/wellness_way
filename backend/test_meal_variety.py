#!/usr/bin/env python3
"""
Test Meal Variety Improvements

Tests that the LLM generates different meals instead of repeating the same ones.
"""

import asyncio
import json
from app.services.ai_service import DietPlanAI

async def test_meal_variety():
    """Test that multiple requests generate different meals"""
    print("Testing meal variety improvements...")
    
    ai_service = DietPlanAI()
    
    # Mock health context
    health_context_json = {
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
    
    meal_names = []
    
    print("Generating 3 meal plans to test variety...")
    
    for i in range(3):
        try:
            print(f"\n--- Request {i+1} ---")
            
            # Get meal ideas (this is what was repeating)
            meal_ideas = await ai_service._get_meal_ideas_from_llm(
                health_context_json, 
                "daily", 
                "2024-01-26",
                f"test-variety-{i}"
            )
            
            # Extract meal names
            request_meals = []
            for meal_type in ['breakfast', 'lunch', 'dinner']:
                if meal_type in meal_ideas:
                    meal_name = meal_ideas[meal_type]['name']
                    request_meals.append(meal_name)
                    print(f"  {meal_type.capitalize()}: {meal_name}")
            
            meal_names.append(request_meals)
            
        except Exception as e:
            print(f"❌ Request {i+1} failed: {e}")
            return False
    
    # Check for variety
    print(f"\n🔍 VARIETY ANALYSIS:")
    all_meals = [meal for request in meal_names for meal in request]
    unique_meals = set(all_meals)
    
    print(f"Total meals generated: {len(all_meals)}")
    print(f"Unique meals: {len(unique_meals)}")
    print(f"Repetition rate: {(len(all_meals) - len(unique_meals)) / len(all_meals) * 100:.1f}%")
    
    # Check for the problematic patterns
    problematic_patterns = [
        "Greek Yogurt", "Tofu", "Lentil", "Bowl", "Parfait", "Stew"
    ]
    
    pattern_count = 0
    for meal in all_meals:
        for pattern in problematic_patterns:
            if pattern.lower() in meal.lower():
                pattern_count += 1
                break
    
    print(f"Meals with old patterns: {pattern_count}/{len(all_meals)}")
    
    if len(unique_meals) >= len(all_meals) * 0.8:  # 80% unique
        print("✅ Good variety achieved!")
        return True
    else:
        print("❌ Still too repetitive")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_meal_variety())
    if not success:
        exit(1)