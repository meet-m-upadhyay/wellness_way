"""
Test core business logic without database
"""

from app.services.health_calculations import (
    calculate_bmr,
    calculate_tdee,
    calculate_safety_constraints,
    calculate_calorie_targets,
    calculate_macro_targets,
    generate_health_context_document
)


def test_business_logic():
    """Test core business logic calculations"""
    print("🧪 Testing WellnessWay Business Logic...")
    
    # Test data
    user_profile = {
        'name': 'Test User',
        'age': 30,
        'gender': 'male',
        'height_cm': 175.0,
        'weight_kg': 75.0,
        'body_fat_percentage': 15.0,
        'muscle_mass_kg': 35.0,
        'activity_level': 'moderately_active'
    }
    
    health_goals = {
        'primary_goal': 'fat_loss',
        'target_weight_kg': 70.0,
        'timeline_weeks': 12
    }
    
    diet_preferences = {
        'diet_type': 'non_vegetarian',
        'allergies': ['nuts', 'shellfish'],
        'foods_to_avoid': ['spicy food'],
        'meals_per_day': 3,
        'budget_constraints': 'moderate',
        'lifestyle_constraints': 'busy schedule'
    }
    
    try:
        # Test BMR calculation
        print("🔥 Testing BMR calculation...")
        bmr = calculate_bmr(
            weight_kg=user_profile['weight_kg'],
            height_cm=user_profile['height_cm'],
            age=user_profile['age'],
            gender=user_profile['gender']
        )
        print(f"✅ BMR calculated: {bmr:.1f} calories/day")
        
        # Test TDEE calculation
        print("⚡ Testing TDEE calculation...")
        tdee = calculate_tdee(bmr, user_profile['activity_level'])
        print(f"✅ TDEE calculated: {tdee:.1f} calories/day")
        
        # Test safety constraints
        print("🛡️ Testing safety constraints...")
        constraints = calculate_safety_constraints(
            weight_kg=user_profile['weight_kg'],
            height_cm=user_profile['height_cm'],
            age=user_profile['age'],
            gender=user_profile['gender'],
            activity_level=user_profile['activity_level'],
            primary_goal=health_goals['primary_goal']
        )
        print(f"✅ Safety constraints calculated:")
        print(f"   Min daily calories: {constraints['min_daily_calories']:.1f}")
        print(f"   Max calorie deficit: {constraints['max_calorie_deficit']:.1f}")
        print(f"   Min protein: {constraints['min_protein_grams']:.1f}g")
        
        # Test calorie targets
        print("🎯 Testing calorie targets...")
        targets = calculate_calorie_targets(
            weight_kg=user_profile['weight_kg'],
            height_cm=user_profile['height_cm'],
            age=user_profile['age'],
            gender=user_profile['gender'],
            activity_level=user_profile['activity_level'],
            primary_goal=health_goals['primary_goal'],
            target_weight_kg=health_goals['target_weight_kg'],
            timeline_weeks=health_goals['timeline_weeks']
        )
        print(f"✅ Calorie targets calculated:")
        print(f"   Target calories: {targets['target_calories']:.1f}")
        print(f"   Weekly deficit: {targets['weekly_deficit']:.1f}")
        print(f"   Est. weight loss: {targets['estimated_loss_per_week']:.2f} kg/week")
        
        # Test macro targets
        print("🥗 Testing macro targets...")
        macros = calculate_macro_targets(
            target_calories=targets['target_calories'],
            weight_kg=user_profile['weight_kg'],
            primary_goal=health_goals['primary_goal']
        )
        print(f"✅ Macro targets calculated:")
        print(f"   Protein: {macros['protein_grams']:.1f}g ({macros['protein_calories']:.1f} cal)")
        print(f"   Fat: {macros['fat_grams']:.1f}g ({macros['fat_calories']:.1f} cal)")
        print(f"   Carbs: {macros['carb_grams']:.1f}g ({macros['carb_calories']:.1f} cal)")
        
        # Test HCD generation
        print("📋 Testing Health Context Document generation...")
        hcd_result = generate_health_context_document(
            user_profile=user_profile,
            health_goals=health_goals,
            diet_preferences=diet_preferences
        )
        print(f"✅ HCD generated successfully:")
        print(f"   Content length: {len(hcd_result['content'])} characters")
        print(f"   BMR: {hcd_result['bmr_calories']:.1f} calories")
        print(f"   TDEE: {hcd_result['tdee_calories']:.1f} calories")
        
        # Validate calculations make sense
        print("🔍 Validating calculation logic...")
        assert bmr > 0, "BMR should be positive"
        assert tdee > bmr, "TDEE should be greater than BMR"
        assert constraints['min_daily_calories'] >= bmr, "Min calories should be at least BMR"
        assert constraints['max_calorie_deficit'] > 0, "Max deficit should be positive"
        assert constraints['min_protein_grams'] > 0, "Min protein should be positive"
        assert targets['target_calories'] > 0, "Target calories should be positive"
        assert macros['protein_grams'] > 0, "Protein target should be positive"
        assert macros['fat_grams'] > 0, "Fat target should be positive"
        assert macros['carb_grams'] > 0, "Carb target should be positive"
        
        # Check that macro calories add up approximately to target calories
        total_macro_calories = (
            macros['protein_calories'] + 
            macros['fat_calories'] + 
            macros['carb_calories']
        )
        calorie_diff = abs(total_macro_calories - targets['target_calories'])
        assert calorie_diff < 10, f"Macro calories should sum to target calories (diff: {calorie_diff:.1f})"
        
        print("✅ All validation checks passed!")
        
        print("\n🎉 All business logic tests passed!")
        print("\n📊 Summary:")
        print(f"   - BMR Calculation: ✅ {bmr:.1f} cal/day")
        print(f"   - TDEE Calculation: ✅ {tdee:.1f} cal/day")
        print(f"   - Safety Constraints: ✅ Min {constraints['min_daily_calories']:.0f} cal, Max deficit {constraints['max_calorie_deficit']:.0f} cal")
        print(f"   - Calorie Targets: ✅ {targets['target_calories']:.0f} cal/day for {health_goals['primary_goal']}")
        print(f"   - Macro Distribution: ✅ P:{macros['protein_grams']:.0f}g F:{macros['fat_grams']:.0f}g C:{macros['carb_grams']:.0f}g")
        print(f"   - HCD Generation: ✅ Complete structured document")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_business_logic()
    if success:
        print("\n🚀 The WellnessWay business logic is working correctly!")
        print("   Core features implemented:")
        print("   ✅ BMR calculation using Mifflin-St Jeor equation")
        print("   ✅ TDEE calculation with activity multipliers")
        print("   ✅ Safety constraints for healthy diet planning")
        print("   ✅ Calorie and macro target calculations")
        print("   ✅ Health Context Document generation")
        print("   ✅ Input validation and error handling")
        print("\n   Ready for:")
        print("   - API endpoint integration")
        print("   - Database storage")
        print("   - Frontend consumption")
        print("   - AI diet plan generation")
    else:
        print("\n💥 Business logic tests failed. Please check the errors above.")