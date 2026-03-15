#!/usr/bin/env python3
"""
Test the refactored architecture to verify nutrition calculation fixes.
"""

import asyncio
import json
from app.services.ai_service import get_ai_service
from app.services.health_calculations import generate_health_context_document

async def test_nutrition_calculation_fix():
    """Test that the refactored architecture fixes nutrition calculation mismatches"""
    
    print("🧪 Testing Refactored Architecture - Nutrition Calculation Fix")
    print("=" * 60)
    
    # Create test user data (same as the user's example)
    user_profile = {
        'name': 'Meet Upadhyay',
        'age': 26,
        'gender': 'male',
        'height_cm': 177.0,
        'weight_kg': 79.0,
        'body_fat_percentage': 20.2,
        'muscle_mass_kg': 59.9,
        'activity_level': 'moderately_active'
    }
    
    health_goals = {
        'primary_goal': 'fat_loss',
        'target_weight_kg': 72.0,
        'timeline_weeks': 4
    }
    
    diet_preferences = {
        'diet_type': 'vegetarian',
        'allergies': [],
        'foods_to_avoid': [],
        'meals_per_day': 3,
        'budget_constraints': 'Avoid expensive',
        'lifestyle_constraints': 'Busy schedule, Quick meals, Less meal prep time, High protein meals'
    }
    
    try:
        # Step 1: Generate Health Context Document with JSON context
        print("📋 Step 1: Generating Health Context Document...")
        hcd_result = generate_health_context_document(
            user_profile=user_profile,
            health_goals=health_goals,
            diet_preferences=diet_preferences
        )
        
        print(f"✅ HCD Generated Successfully")
        print(f"   Target Calories: {hcd_result['json_context']['nutrition_targets']['target_calories']}")
        print(f"   Target Protein: {hcd_result['json_context']['nutrition_targets']['target_protein_g']}g")
        print()
        
        # Step 2: Generate diet plan using new architecture
        print("🍽️  Step 2: Generating Daily Diet Plan...")
        ai_service = get_ai_service()
        
        diet_plan = await ai_service.generate_diet_plan(
            health_context=hcd_result['content'],  # Markdown for backward compatibility
            health_context_json=hcd_result['json_context'],  # JSON for new architecture
            plan_type="daily",
            target_date="2026-01-25"
        )
        
        print(f"✅ Diet Plan Generated Successfully")
        print()
        
        # Step 3: Verify nutrition calculations
        print("🔍 Step 3: Verifying Nutrition Calculations...")
        
        # Extract nutrition data
        meals = diet_plan.get('meals', [])
        daily_totals = diet_plan.get('daily_totals', {})
        
        # Calculate actual totals from meals
        calculated_totals = {
            'calories': 0,
            'protein': 0,
            'carbohydrates': 0,
            'fat': 0,
            'fiber': 0,
            'sodium': 0
        }
        
        print("📊 Individual Meal Nutrition:")
        for i, meal in enumerate(meals, 1):
            meal_nutrition = meal.get('nutrition', {})
            print(f"   Meal {i} ({meal.get('name', 'Unknown')}):")
            print(f"     Calories: {meal_nutrition.get('calories', 0)}")
            print(f"     Protein: {meal_nutrition.get('protein', 0)}g")
            
            # Add to calculated totals
            for key in calculated_totals:
                calculated_totals[key] += meal_nutrition.get(key, 0)
        
        print()
        print("📈 Daily Totals Comparison:")
        print(f"   AI Claimed Protein: {daily_totals.get('protein', 0)}g")
        print(f"   Calculated Protein: {calculated_totals['protein']}g")
        print(f"   AI Claimed Calories: {daily_totals.get('calories', 0)}")
        print(f"   Calculated Calories: {calculated_totals['calories']}")
        
        # Check for discrepancies
        protein_discrepancy = abs(daily_totals.get('protein', 0) - calculated_totals['protein'])
        calorie_discrepancy = abs(daily_totals.get('calories', 0) - calculated_totals['calories'])
        
        print()
        print("🎯 Discrepancy Analysis:")
        print(f"   Protein Discrepancy: {protein_discrepancy:.1f}g")
        print(f"   Calorie Discrepancy: {calorie_discrepancy:.1f}")
        
        # Determine if fix was successful
        if protein_discrepancy <= 5 and calorie_discrepancy <= 50:
            print("✅ SUCCESS: Nutrition calculations are now accurate!")
            print("   The refactored architecture has fixed the calculation mismatch.")
        else:
            print("❌ ISSUE: Significant discrepancies still exist.")
            print("   The refactor may need additional work.")
        
        print()
        print("🏆 Architecture Test Summary:")
        print(f"   - HCD Generation: ✅ Working")
        print(f"   - JSON Context: ✅ Generated")
        print(f"   - Diet Plan Generation: ✅ Working")
        print(f"   - Nutrition Accuracy: {'✅ Fixed' if protein_discrepancy <= 5 else '❌ Needs Work'}")
        
        return diet_plan
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(test_nutrition_calculation_fix())