#!/usr/bin/env python3
"""
Demonstration script for Health Context Document generation.

This script shows how the HCD generation works with sample user data.
"""

from app.services.health_calculations import generate_health_context_document


def main():
    """Demonstrate HCD generation with sample data."""
    
    print("Health Context Document Generation Demo")
    print("=" * 50)
    
    # Sample user profile
    user_profile = {
        'name': 'Alex Johnson',
        'age': 28,
        'gender': 'male',
        'height_cm': 175.0,
        'weight_kg': 80.0,
        'body_fat_percentage': 15.0,
        'muscle_mass_kg': 35.0,
        'activity_level': 'moderately_active'
    }
    
    # Sample health goals
    health_goals = {
        'primary_goal': 'fat_loss',
        'target_weight_kg': 75.0,
        'timeline_weeks': 12
    }
    
    # Sample diet preferences
    diet_preferences = {
        'diet_type': 'non_vegetarian',
        'allergies': ['nuts', 'shellfish'],
        'foods_to_avoid': ['processed_sugar', 'fried_foods'],
        'meals_per_day': 4,
        'budget_constraints': 'Moderate budget - $50-70 per week',
        'lifestyle_constraints': 'Busy work schedule, prefers meal prep'
    }
    
    print("Input Data:")
    print(f"User: {user_profile['name']}, {user_profile['age']} years old")
    print(f"Physical: {user_profile['height_cm']}cm, {user_profile['weight_kg']}kg")
    print(f"Goal: {health_goals['primary_goal']} - target {health_goals['target_weight_kg']}kg in {health_goals['timeline_weeks']} weeks")
    print(f"Diet: {diet_preferences['diet_type']}, {diet_preferences['meals_per_day']} meals/day")
    print(f"Allergies: {', '.join(diet_preferences['allergies'])}")
    print()
    
    # Generate HCD
    print("Generating Health Context Document...")
    result = generate_health_context_document(
        user_profile, health_goals, diet_preferences
    )
    
    print("Generated HCD Summary:")
    print(f"BMR: {result['bmr_calories']:.1f} calories/day")
    print(f"TDEE: {result['tdee_calories']:.1f} calories/day")
    print(f"Target Calories: {result['calorie_targets']['target_calories']:.1f} calories/day")
    print(f"Protein Target: {result['macro_targets']['protein_grams']:.1f}g/day")
    print(f"Min Daily Calories: {result['min_daily_calories']:.1f}")
    print(f"Max Deficit: {result['max_calorie_deficit']:.1f} calories")
    print()
    
    print("Full Health Context Document:")
    print("-" * 50)
    print(result['content'])
    
    # Demonstrate with different goal
    print("\n" + "=" * 50)
    print("Muscle Gain Example:")
    print("=" * 50)
    
    muscle_gain_goals = {
        'primary_goal': 'muscle_gain',
        'target_weight_kg': 85.0,
        'timeline_weeks': 16
    }
    
    result2 = generate_health_context_document(
        user_profile, muscle_gain_goals, diet_preferences
    )
    
    print(f"Muscle Gain Target Calories: {result2['calorie_targets']['target_calories']:.1f} calories/day")
    print(f"Muscle Gain Protein Target: {result2['macro_targets']['protein_grams']:.1f}g/day")
    print(f"Estimated Weight Gain: {abs(result2['calorie_targets']['estimated_loss_per_week']):.2f} kg/week")


if __name__ == "__main__":
    main()