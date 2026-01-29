"""
Unit tests for Health Context Document generation.

Tests the generate_health_context_document function and its helper functions
to ensure proper HCD generation from user data.
"""

import pytest
from app.services.health_calculations import (
    generate_health_context_document,
    _generate_hcd_markdown
)


class TestHealthContextDocumentGeneration:
    """Test suite for HCD generation functionality."""
    
    def test_generate_hcd_complete_profile(self):
        """Test HCD generation with complete user profile."""
        user_profile = {
            'name': 'John Doe',
            'age': 30,
            'gender': 'male',
            'height_cm': 175.0,
            'weight_kg': 80.0,
            'body_fat_percentage': 15.0,
            'muscle_mass_kg': 35.0,
            'activity_level': 'moderately_active'
        }
        
        health_goals = {
            'primary_goal': 'fat_loss',
            'target_weight_kg': 75.0,
            'timeline_weeks': 12
        }
        
        diet_preferences = {
            'diet_type': 'non_vegetarian',
            'allergies': ['nuts', 'shellfish'],
            'foods_to_avoid': ['processed_sugar'],
            'meals_per_day': 3,
            'budget_constraints': 'Moderate budget',
            'lifestyle_constraints': 'Busy schedule'
        }
        
        result = generate_health_context_document(
            user_profile, health_goals, diet_preferences
        )
        
        # Check that all required fields are present
        assert 'content' in result
        assert 'bmr_calories' in result
        assert 'tdee_calories' in result
        assert 'min_daily_calories' in result
        assert 'max_calorie_deficit' in result
        assert 'min_protein_grams' in result
        assert 'calorie_targets' in result
        assert 'macro_targets' in result
        
        # Check that content is a non-empty string
        assert isinstance(result['content'], str)
        assert len(result['content']) > 0
        
        # Check that calculated values are reasonable
        assert result['bmr_calories'] > 0
        assert result['tdee_calories'] > result['bmr_calories']
        assert result['min_daily_calories'] >= result['bmr_calories']
        assert result['max_calorie_deficit'] > 0
        assert result['min_protein_grams'] > 0
        
        # Check that markdown contains key sections
        content = result['content']
        assert '# Health Context Document' in content
        assert '## User Profile' in content
        assert '## Health Goals' in content
        assert '## Diet Preferences' in content
        assert '## Calculated Metrics' in content
        assert '## Safety Guidelines' in content
        
        # Check that user data is included
        assert 'John Doe' in content
        assert '30 years' in content
        assert 'Male' in content
        assert '175.0 cm' in content
        assert '80.0 kg' in content
        assert 'nuts, shellfish' in content
        assert 'processed_sugar' in content
    
    def test_generate_hcd_minimal_profile(self):
        """Test HCD generation with minimal required data."""
        user_profile = {
            'name': 'Jane Smith',
            'age': 25,
            'gender': 'female',
            'height_cm': 165.0,
            'weight_kg': 60.0,
            'activity_level': 'sedentary'
        }
        
        health_goals = {
            'primary_goal': 'maintenance'
        }
        
        diet_preferences = {
            'diet_type': 'vegetarian',
            'allergies': [],
            'foods_to_avoid': [],
            'meals_per_day': 4
        }
        
        result = generate_health_context_document(
            user_profile, health_goals, diet_preferences
        )
        
        # Check that all required fields are present
        assert 'content' in result
        assert isinstance(result['content'], str)
        assert len(result['content']) > 0
        
        # Check that optional fields are handled properly
        content = result['content']
        assert 'Not specified' in content  # For missing optional fields
        assert 'None' in content  # For empty lists
        assert 'Jane Smith' in content
        assert 'Vegetarian' in content
        assert 'Maintenance' in content
    
    def test_generate_hcd_missing_required_fields(self):
        """Test that missing required fields raise ValueError."""
        # Missing name in user profile
        incomplete_profile = {
            'age': 30,
            'gender': 'male',
            'height_cm': 175.0,
            'weight_kg': 80.0,
            'activity_level': 'moderately_active'
        }
        
        health_goals = {'primary_goal': 'fat_loss'}
        diet_preferences = {
            'diet_type': 'non_vegetarian',
            'allergies': [],
            'foods_to_avoid': [],
            'meals_per_day': 3
        }
        
        with pytest.raises(ValueError, match="Missing required user profile field: name"):
            generate_health_context_document(
                incomplete_profile, health_goals, diet_preferences
            )
        
        # Missing primary goal
        complete_profile = {
            'name': 'John Doe',
            'age': 30,
            'gender': 'male',
            'height_cm': 175.0,
            'weight_kg': 80.0,
            'activity_level': 'moderately_active'
        }
        
        incomplete_goals = {}
        
        with pytest.raises(ValueError, match="Missing required health goal field: primary_goal"):
            generate_health_context_document(
                complete_profile, incomplete_goals, diet_preferences
            )
        
        # Missing diet type
        incomplete_preferences = {
            'allergies': [],
            'foods_to_avoid': [],
            'meals_per_day': 3
        }
        
        with pytest.raises(ValueError, match="Missing required diet preference field: diet_type"):
            generate_health_context_document(
                complete_profile, health_goals, incomplete_preferences
            )
    
    def test_hcd_markdown_structure(self):
        """Test that generated markdown has proper structure."""
        user_profile = {
            'name': 'Test User',
            'age': 35,
            'gender': 'other',
            'height_cm': 170.0,
            'weight_kg': 70.0,
            'body_fat_percentage': 20.0,
            'muscle_mass_kg': 30.0,
            'activity_level': 'very_active'
        }
        
        health_goals = {
            'primary_goal': 'muscle_gain',
            'target_weight_kg': 75.0,
            'timeline_weeks': 16
        }
        
        diet_preferences = {
            'diet_type': 'vegan',
            'allergies': ['soy', 'gluten'],
            'foods_to_avoid': ['refined_oils'],
            'meals_per_day': 5,
            'budget_constraints': 'High budget',
            'lifestyle_constraints': 'Flexible schedule'
        }
        
        result = generate_health_context_document(
            user_profile, health_goals, diet_preferences
        )
        
        content = result['content']
        
        # Check markdown structure
        assert content.startswith('# Health Context Document')
        assert '## User Profile' in content
        assert '## Health Goals' in content
        assert '## Diet Preferences' in content
        assert '## Calculated Metrics' in content
        assert '### Metabolic Calculations' in content
        assert '### Safety Constraints' in content
        assert '### Calorie Targets' in content
        assert '### Macronutrient Targets' in content
        assert '## Safety Guidelines' in content
        assert '### Mandatory Requirements' in content
        assert '### Dietary Restrictions' in content
        assert '### Nutritional Balance' in content
        
        # Check that calculated values are included
        assert f"{result['bmr_calories']:.1f}" in content
        assert f"{result['tdee_calories']:.1f}" in content
        assert f"{result['min_daily_calories']:.1f}" in content
        assert f"{result['max_calorie_deficit']:.1f}" in content
        assert f"{result['min_protein_grams']:.1f}" in content
        
        # Check that safety guidelines reference actual values
        assert 'soy, gluten' in content
        assert 'refined_oils' in content
        assert 'Vegan only' in content
        assert '5 meals per day' in content
    
    def test_hcd_different_goals(self):
        """Test HCD generation with different primary goals."""
        base_profile = {
            'name': 'Test User',
            'age': 28,
            'gender': 'female',
            'height_cm': 160.0,
            'weight_kg': 55.0,
            'activity_level': 'lightly_active'
        }
        
        base_preferences = {
            'diet_type': 'vegetarian',
            'allergies': [],
            'foods_to_avoid': [],
            'meals_per_day': 3
        }
        
        # Test fat loss goal
        fat_loss_goals = {'primary_goal': 'fat_loss'}
        result_fat_loss = generate_health_context_document(
            base_profile, fat_loss_goals, base_preferences
        )
        
        # Test muscle gain goal
        muscle_gain_goals = {'primary_goal': 'muscle_gain'}
        result_muscle_gain = generate_health_context_document(
            base_profile, muscle_gain_goals, base_preferences
        )
        
        # Test maintenance goal
        maintenance_goals = {'primary_goal': 'maintenance'}
        result_maintenance = generate_health_context_document(
            base_profile, maintenance_goals, base_preferences
        )
        
        # Check that different goals produce different calorie targets
        fat_loss_calories = result_fat_loss['calorie_targets']['target_calories']
        muscle_gain_calories = result_muscle_gain['calorie_targets']['target_calories']
        maintenance_calories = result_maintenance['calorie_targets']['target_calories']
        
        # Muscle gain should have highest calories, fat loss lowest
        assert muscle_gain_calories > maintenance_calories
        assert maintenance_calories > fat_loss_calories
        
        # Check that protein requirements differ
        fat_loss_protein = result_fat_loss['min_protein_grams']
        muscle_gain_protein = result_muscle_gain['min_protein_grams']
        maintenance_protein = result_maintenance['min_protein_grams']
        
        # Muscle gain should have highest protein requirement
        assert muscle_gain_protein > maintenance_protein
        assert muscle_gain_protein > fat_loss_protein
    
    def test_hcd_activity_level_impact(self):
        """Test that different activity levels affect TDEE and targets."""
        base_profile = {
            'name': 'Test User',
            'age': 30,
            'gender': 'male',
            'height_cm': 180.0,
            'weight_kg': 75.0
        }
        
        base_goals = {'primary_goal': 'maintenance'}
        base_preferences = {
            'diet_type': 'non_vegetarian',
            'allergies': [],
            'foods_to_avoid': [],
            'meals_per_day': 3
        }
        
        activity_levels = ['sedentary', 'lightly_active', 'moderately_active', 'very_active', 'extremely_active']
        results = []
        
        for activity in activity_levels:
            profile = {**base_profile, 'activity_level': activity}
            result = generate_health_context_document(profile, base_goals, base_preferences)
            results.append(result)
        
        # Check that TDEE increases with activity level
        tdees = [result['tdee_calories'] for result in results]
        for i in range(1, len(tdees)):
            assert tdees[i] > tdees[i-1], f"TDEE should increase with activity level"
        
        # Check that target calories also increase (for maintenance goal)
        target_calories = [result['calorie_targets']['target_calories'] for result in results]
        for i in range(1, len(target_calories)):
            assert target_calories[i] > target_calories[i-1], f"Target calories should increase with activity level"
    
    def test_hcd_content_completeness(self):
        """Test that HCD content includes all necessary information for AI."""
        user_profile = {
            'name': 'Complete User',
            'age': 40,
            'gender': 'male',
            'height_cm': 185.0,
            'weight_kg': 90.0,
            'body_fat_percentage': 18.0,
            'muscle_mass_kg': 40.0,
            'activity_level': 'moderately_active'
        }
        
        health_goals = {
            'primary_goal': 'fat_loss',
            'target_weight_kg': 85.0,
            'timeline_weeks': 10
        }
        
        diet_preferences = {
            'diet_type': 'non_vegetarian',
            'allergies': ['dairy', 'eggs'],
            'foods_to_avoid': ['fried_foods', 'alcohol'],
            'meals_per_day': 4,
            'budget_constraints': 'Premium budget',
            'lifestyle_constraints': 'Home cooking preferred'
        }
        
        result = generate_health_context_document(
            user_profile, health_goals, diet_preferences
        )
        
        content = result['content']
        
        # Check that all user data is present
        assert 'Complete User' in content
        assert '40 years' in content
        assert 'Male' in content
        assert '185.0 cm' in content
        assert '90.0 kg' in content
        assert '18.0%' in content
        assert '40.0 kg' in content
        assert 'Moderately Active' in content
        
        # Check goals
        assert 'Fat Loss' in content
        assert '85.0 kg' in content
        assert '10 weeks' in content
        
        # Check preferences
        assert 'Non Vegetarian' in content
        assert 'dairy, eggs' in content
        assert 'fried_foods, alcohol' in content
        assert '4' in content
        assert 'Premium budget' in content
        assert 'Home cooking preferred' in content
        
        # Check that safety guidelines are specific and actionable
        assert 'Never exceed maximum calorie deficit' in content
        assert 'Never go below minimum calories' in content
        assert 'Always meet minimum protein' in content
        assert 'Strictly avoid all listed allergies' in content
        assert 'Exclude all foods to avoid' in content
        assert 'Respect diet type' in content
        
        # Check that specific values are mentioned in guidelines
        assert f"{result['max_calorie_deficit']:.1f} calories per day" in content
        assert f"{result['min_daily_calories']:.1f} calories per day" in content
        assert f"{result['min_protein_grams']:.1f} grams per day" in content