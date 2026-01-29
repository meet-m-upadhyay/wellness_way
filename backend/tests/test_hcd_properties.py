"""
Property-based tests for Health Context Document generation.

These tests validate the correctness properties for HCD generation
as specified in the design document.
"""

import pytest
from hypothesis import given, strategies as st, assume
from app.services.health_calculations import generate_health_context_document


# Strategy for generating valid user profiles
user_profile_strategy = st.fixed_dictionaries({
    'name': st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    'age': st.integers(min_value=18, max_value=100),
    'gender': st.sampled_from(['male', 'female', 'other']),
    'height_cm': st.floats(min_value=140.0, max_value=220.0),  # More realistic height range
    'weight_kg': st.floats(min_value=40.0, max_value=150.0),   # More realistic weight range
    'body_fat_percentage': st.one_of(st.none(), st.floats(min_value=5.0, max_value=50.0)),
    'muscle_mass_kg': st.one_of(st.none(), st.floats(min_value=15.0, max_value=60.0)),
    'activity_level': st.sampled_from(['sedentary', 'lightly_active', 'moderately_active', 'very_active', 'extremely_active'])
})

# Strategy for generating valid health goals
health_goals_strategy = st.fixed_dictionaries({
    'primary_goal': st.sampled_from(['fat_loss', 'muscle_gain', 'maintenance']),
    'target_weight_kg': st.one_of(st.none(), st.floats(min_value=30.0, max_value=200.0)),
    'timeline_weeks': st.one_of(st.none(), st.integers(min_value=1, max_value=52))
})

# Strategy for generating valid diet preferences
diet_preferences_strategy = st.fixed_dictionaries({
    'diet_type': st.sampled_from(['vegetarian', 'non_vegetarian', 'vegan']),
    'allergies': st.lists(st.text(min_size=1, max_size=20), max_size=10),
    'foods_to_avoid': st.lists(st.text(min_size=1, max_size=20), max_size=10),
    'meals_per_day': st.integers(min_value=1, max_value=8),
    'budget_constraints': st.one_of(st.none(), st.text(max_size=200)),
    'lifestyle_constraints': st.one_of(st.none(), st.text(max_size=200))
})


class TestHCDGenerationProperties:
    """Property-based tests for HCD generation correctness."""
    
    @given(
        user_profile=user_profile_strategy,
        health_goals=health_goals_strategy,
        diet_preferences=diet_preferences_strategy
    )
    def test_hcd_completeness_property(self, user_profile, health_goals, diet_preferences):
        """
        **Validates: Requirements 2.4.2**
        
        Property: Every generated HCD must contain all required sections and valid calculated values.
        
        This test ensures that regardless of input variations, the HCD always contains:
        - All required markdown sections
        - All calculated metrics (BMR, TDEE, constraints)
        - Valid numerical values within reasonable bounds
        - Proper formatting and structure
        """
        # Ensure muscle mass doesn't exceed total weight (biological constraint)
        if user_profile['muscle_mass_kg'] is not None:
            assume(user_profile['muscle_mass_kg'] <= user_profile['weight_kg'])
        
        # Ensure target weight is reasonable relative to current weight
        if health_goals['target_weight_kg'] is not None:
            weight_diff = abs(health_goals['target_weight_kg'] - user_profile['weight_kg'])
            assume(weight_diff <= 50.0)  # No more than 50kg difference
        
        result = generate_health_context_document(
            user_profile, health_goals, diet_preferences
        )
        
        # Property 1: All required fields must be present
        required_fields = [
            'content', 'bmr_calories', 'tdee_calories', 
            'min_daily_calories', 'max_calorie_deficit', 'min_protein_grams',
            'calorie_targets', 'macro_targets'
        ]
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"
        
        # Property 2: Content must be non-empty markdown
        content = result['content']
        assert isinstance(content, str)
        assert len(content) > 0
        assert content.startswith('# Health Context Document')
        
        # Property 3: All required sections must be present
        required_sections = [
            '## User Profile',
            '## Health Goals', 
            '## Diet Preferences',
            '## Calculated Metrics',
            '## Safety Guidelines'
        ]
        for section in required_sections:
            assert section in content, f"Missing required section: {section}"
        
        # Property 4: Calculated values must be positive and reasonable
        assert result['bmr_calories'] > 0
        assert result['tdee_calories'] > result['bmr_calories']
        assert result['min_daily_calories'] >= result['bmr_calories']
        assert result['max_calorie_deficit'] > 0
        assert result['min_protein_grams'] > 0
        
        # Property 5: BMR should be within reasonable human bounds (700-3500 calories)
        # Allowing for very small/elderly individuals who may have lower BMR
        assert 700 <= result['bmr_calories'] <= 3500
        
        # Property 6: TDEE should be reasonable multiple of BMR (1.19x to 2.1x)
        # Note: Allowing for floating point precision and edge cases
        tdee_bmr_ratio = result['tdee_calories'] / result['bmr_calories']
        assert 1.19 <= tdee_bmr_ratio <= 2.1
        
        # Property 7: User data must be preserved in content
        assert user_profile['name'] in content
        assert str(user_profile['age']) in content
        assert user_profile['gender'].title() in content
        assert str(user_profile['height_cm']) in content
        assert str(user_profile['weight_kg']) in content
    
    @given(
        user_profile=user_profile_strategy,
        health_goals=health_goals_strategy,
        diet_preferences=diet_preferences_strategy
    )
    def test_hcd_safety_constraints_property(self, user_profile, health_goals, diet_preferences):
        """
        **Validates: Requirements 2.4.3**
        
        Property: HCD must include system-calculated safety constraints that are mathematically sound.
        
        This test ensures that safety constraints are:
        - Always present in the HCD
        - Mathematically consistent with each other
        - Within safe physiological bounds
        - Properly referenced in safety guidelines
        """
        # Apply same biological constraints as previous test
        if user_profile['muscle_mass_kg'] is not None:
            assume(user_profile['muscle_mass_kg'] <= user_profile['weight_kg'])
        
        if health_goals['target_weight_kg'] is not None:
            weight_diff = abs(health_goals['target_weight_kg'] - user_profile['weight_kg'])
            assume(weight_diff <= 50.0)
        
        result = generate_health_context_document(
            user_profile, health_goals, diet_preferences
        )
        
        content = result['content']
        
        # Property 1: Safety constraints section must exist
        assert '## Safety Guidelines' in content
        assert '### Mandatory Requirements' in content
        assert '### Dietary Restrictions' in content
        
        # Property 2: Minimum calories must never be below BMR
        assert result['min_daily_calories'] >= result['bmr_calories']
        
        # Property 3: Maximum deficit must be reasonable (not more than 20% of TDEE or 500 cal)
        max_theoretical_deficit = min(result['tdee_calories'] * 0.2, 500)
        assert result['max_calorie_deficit'] <= max_theoretical_deficit + 1  # Allow for rounding
        
        # Property 4: Protein requirements must be at least 0.8g per kg body weight
        min_theoretical_protein = user_profile['weight_kg'] * 0.8
        assert result['min_protein_grams'] >= min_theoretical_protein - 1  # Allow for rounding
        
        # Property 5: Safety values must be referenced in guidelines text
        assert f"{result['max_calorie_deficit']:.1f}" in content
        assert f"{result['min_daily_calories']:.1f}" in content
        assert f"{result['min_protein_grams']:.1f}" in content
        
        # Property 6: Dietary restrictions must be properly enforced
        if diet_preferences['allergies']:
            allergies_text = ', '.join(diet_preferences['allergies'])
            assert allergies_text in content
            assert 'Strictly avoid all listed allergies' in content
        
        if diet_preferences['foods_to_avoid']:
            avoid_text = ', '.join(diet_preferences['foods_to_avoid'])
            assert avoid_text in content
            assert 'Exclude all foods to avoid' in content
        
        # Property 7: Diet type must be enforced
        diet_display = diet_preferences['diet_type'].replace('_', ' ').title()
        assert diet_display in content
        assert 'Respect diet type' in content
    
    @given(
        user_profile=user_profile_strategy,
        health_goals=health_goals_strategy,
        diet_preferences=diet_preferences_strategy
    )
    def test_hcd_deterministic_property(self, user_profile, health_goals, diet_preferences):
        """
        **Validates: Requirements 2.4.1**
        
        Property: HCD generation must be deterministic - identical inputs produce identical outputs.
        
        This test ensures that the HCD generation process is reproducible and consistent,
        which is crucial for versioning and immutability requirements.
        """
        # Apply biological constraints
        if user_profile['muscle_mass_kg'] is not None:
            assume(user_profile['muscle_mass_kg'] <= user_profile['weight_kg'])
        
        if health_goals['target_weight_kg'] is not None:
            weight_diff = abs(health_goals['target_weight_kg'] - user_profile['weight_kg'])
            assume(weight_diff <= 50.0)
        
        # Generate HCD twice with identical inputs
        result1 = generate_health_context_document(
            user_profile, health_goals, diet_preferences
        )
        result2 = generate_health_context_document(
            user_profile, health_goals, diet_preferences
        )
        
        # Property: All outputs must be identical
        assert result1['content'] == result2['content']
        assert result1['bmr_calories'] == result2['bmr_calories']
        assert result1['tdee_calories'] == result2['tdee_calories']
        assert result1['min_daily_calories'] == result2['min_daily_calories']
        assert result1['max_calorie_deficit'] == result2['max_calorie_deficit']
        assert result1['min_protein_grams'] == result2['min_protein_grams']
        assert result1['calorie_targets'] == result2['calorie_targets']
        assert result1['macro_targets'] == result2['macro_targets']
    
    @given(
        user_profile=user_profile_strategy,
        health_goals=health_goals_strategy,
        diet_preferences=diet_preferences_strategy
    )
    def test_hcd_goal_consistency_property(self, user_profile, health_goals, diet_preferences):
        """
        **Validates: Requirements 2.4.2, 2.2.4**
        
        Property: Calorie and macro targets must be consistent with the user's primary goal.
        
        This test ensures that:
        - Fat loss goals result in calorie deficits
        - Muscle gain goals result in calorie surpluses  
        - Maintenance goals result in balanced calories
        - Protein targets are appropriate for each goal
        """
        # Apply biological constraints
        if user_profile['muscle_mass_kg'] is not None:
            assume(user_profile['muscle_mass_kg'] <= user_profile['weight_kg'])
        
        if health_goals['target_weight_kg'] is not None:
            weight_diff = abs(health_goals['target_weight_kg'] - user_profile['weight_kg'])
            assume(weight_diff <= 50.0)
        
        result = generate_health_context_document(
            user_profile, health_goals, diet_preferences
        )
        
        tdee = result['tdee_calories']
        target_calories = result['calorie_targets']['target_calories']
        primary_goal = health_goals['primary_goal']
        
        # Property 1: Goal-appropriate calorie targets
        if primary_goal == 'fat_loss':
            # Fat loss should have calorie deficit (target < TDEE)
            assert target_calories < tdee, "Fat loss should have calorie deficit"
            
        elif primary_goal == 'muscle_gain':
            # Muscle gain should have calorie surplus (target > TDEE)
            assert target_calories > tdee, "Muscle gain should have calorie surplus"
            
        elif primary_goal == 'maintenance':
            # Maintenance should be close to TDEE (within small margin)
            calorie_diff = abs(target_calories - tdee)
            assert calorie_diff <= 50, "Maintenance should be close to TDEE"
        
        # Property 2: Protein targets should be appropriate for goal
        protein_per_kg = result['macro_targets']['protein_grams'] / user_profile['weight_kg']
        
        if primary_goal == 'muscle_gain':
            # Muscle gain should have higher protein (1.2+ g/kg)
            assert protein_per_kg >= 1.2, "Muscle gain should have high protein"
            
        elif primary_goal == 'fat_loss':
            # Fat loss should have moderate protein (1.0+ g/kg)
            assert protein_per_kg >= 1.0, "Fat loss should have moderate protein"
            
        else:  # maintenance
            # Maintenance should have standard protein (0.8+ g/kg)
            assert protein_per_kg >= 0.8, "Maintenance should have standard protein"
        
        # Property 3: Macro calories should sum to target calories (within rounding)
        macro_total = (
            result['macro_targets']['protein_calories'] +
            result['macro_targets']['fat_calories'] +
            result['macro_targets']['carb_calories']
        )
        calorie_diff = abs(macro_total - target_calories)
        assert calorie_diff <= 5, "Macro calories should sum to target calories"
    
    @given(
        user_profile=user_profile_strategy,
        health_goals=health_goals_strategy,
        diet_preferences=diet_preferences_strategy
    )
    def test_hcd_preference_preservation_property(self, user_profile, health_goals, diet_preferences):
        """
        **Validates: Requirements 2.4.2, 2.3.5**
        
        Property: All user preferences and restrictions must be accurately preserved in the HCD.
        
        This test ensures that dietary preferences, allergies, and restrictions are:
        - Completely preserved in the HCD content
        - Properly formatted for AI consumption
        - Referenced in safety guidelines
        - Not lost or corrupted during generation
        """
        # Apply biological constraints
        if user_profile['muscle_mass_kg'] is not None:
            assume(user_profile['muscle_mass_kg'] <= user_profile['weight_kg'])
        
        if health_goals['target_weight_kg'] is not None:
            weight_diff = abs(health_goals['target_weight_kg'] - user_profile['weight_kg'])
            assume(weight_diff <= 50.0)
        
        result = generate_health_context_document(
            user_profile, health_goals, diet_preferences
        )
        
        content = result['content']
        
        # Property 1: Diet type must be preserved and formatted
        diet_display = diet_preferences['diet_type'].replace('_', ' ').title()
        assert diet_display in content
        
        # Property 2: Allergies must be preserved (if any)
        if diet_preferences['allergies']:
            allergies_text = ', '.join(diet_preferences['allergies'])
            assert allergies_text in content
        else:
            assert 'None' in content  # Should show "None" for empty allergies
        
        # Property 3: Foods to avoid must be preserved (if any)
        if diet_preferences['foods_to_avoid']:
            avoid_text = ', '.join(diet_preferences['foods_to_avoid'])
            assert avoid_text in content
        else:
            assert 'None' in content  # Should show "None" for empty avoid list
        
        # Property 4: Meals per day must be preserved
        assert str(diet_preferences['meals_per_day']) in content
        
        # Property 5: Optional constraints should be handled properly
        if diet_preferences.get('budget_constraints'):
            assert diet_preferences['budget_constraints'] in content
        
        if diet_preferences.get('lifestyle_constraints'):
            assert diet_preferences['lifestyle_constraints'] in content
        
        # Property 6: All preferences must be referenced in safety guidelines
        assert f"exactly {diet_preferences['meals_per_day']} meals per day" in content
        
        # Property 7: Content should be AI-readable (structured format)
        # Check that preferences are in a structured section
        assert '## Diet Preferences' in content
        assert '**Diet Type:**' in content
        assert '**Allergies:**' in content
        assert '**Foods to Avoid:**' in content
        assert '**Meals per Day:**' in content