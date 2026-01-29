"""
Unit tests for health calculation services.

Tests the BMR, TDEE, and safety constraint calculations to ensure
they meet the requirements and correctness properties.
"""

import pytest
from app.services.health_calculations import (
    calculate_bmr,
    calculate_tdee,
    calculate_safety_constraints,
    calculate_calorie_targets,
    calculate_macro_targets
)


class TestBMRCalculation:
    """Test BMR calculation using Mifflin-St Jeor equation"""
    
    def test_bmr_male_calculation(self):
        """Test BMR calculation for male using known values"""
        # Test case: 30-year-old male, 80kg, 180cm
        # Expected: 10*80 + 6.25*180 - 5*30 + 5 = 800 + 1125 - 150 + 5 = 1780
        bmr = calculate_bmr(80.0, 180.0, 30, "male")
        assert bmr == 1780.0
    
    def test_bmr_female_calculation(self):
        """Test BMR calculation for female using known values"""
        # Test case: 25-year-old female, 65kg, 165cm
        # Expected: 10*65 + 6.25*165 - 5*25 - 161 = 650 + 1031.25 - 125 - 161 = 1395.25
        bmr = calculate_bmr(65.0, 165.0, 25, "female")
        assert bmr == 1395.25
    
    def test_bmr_other_gender_calculation(self):
        """Test BMR calculation for 'other' gender (average of male/female)"""
        # Test case: 35-year-old, 70kg, 170cm
        # Male: 10*70 + 6.25*170 - 5*35 + 5 = 700 + 1062.5 - 175 + 5 = 1592.5
        # Female: 10*70 + 6.25*170 - 5*35 - 161 = 700 + 1062.5 - 175 - 161 = 1426.5
        # Average: (1592.5 + 1426.5) / 2 = 1509.5
        bmr = calculate_bmr(70.0, 170.0, 35, "other")
        assert bmr == 1509.5
    
    def test_bmr_determinism(self):
        """Test that BMR calculation is deterministic"""
        # Same inputs should always produce same output
        bmr1 = calculate_bmr(75.0, 175.0, 28, "male")
        bmr2 = calculate_bmr(75.0, 175.0, 28, "male")
        bmr3 = calculate_bmr(75.0, 175.0, 28, "male")
        
        assert bmr1 == bmr2 == bmr3
    
    def test_bmr_reasonable_bounds(self):
        """Test that BMR is positive for realistic inputs"""
        # Test various realistic inputs
        test_cases = [
            (50.0, 150.0, 20, "female"),  # Small person
            (100.0, 200.0, 25, "male"),   # Large person
            (70.0, 170.0, 60, "female"),  # Older person
            (80.0, 180.0, 18, "male"),    # Young person
        ]
        
        for weight, height, age, gender in test_cases:
            bmr = calculate_bmr(weight, height, age, gender)
            assert bmr > 0, f"BMR {bmr} must be positive for {weight}kg, {height}cm, {age}y, {gender}"
    
    def test_bmr_input_validation(self):
        """Test BMR calculation input validation"""
        # Test invalid weight
        with pytest.raises(ValueError, match="Weight must be between 0 and 500 kg"):
            calculate_bmr(-10.0, 170.0, 25, "male")
        
        with pytest.raises(ValueError, match="Weight must be between 0 and 500 kg"):
            calculate_bmr(600.0, 170.0, 25, "male")
        
        # Test invalid height
        with pytest.raises(ValueError, match="Height must be between 0 and 300 cm"):
            calculate_bmr(70.0, -10.0, 25, "male")
        
        with pytest.raises(ValueError, match="Height must be between 0 and 300 cm"):
            calculate_bmr(70.0, 400.0, 25, "male")
        
        # Test invalid age
        with pytest.raises(ValueError, match="Age must be between 0 and 150 years"):
            calculate_bmr(70.0, 170.0, -5, "male")
        
        with pytest.raises(ValueError, match="Age must be between 0 and 150 years"):
            calculate_bmr(70.0, 170.0, 200, "male")
        
        # Test invalid gender
        with pytest.raises(ValueError, match="Gender must be 'male', 'female', or 'other'"):
            calculate_bmr(70.0, 170.0, 25, "invalid")
    
    def test_bmr_edge_cases(self):
        """Test BMR calculation edge cases"""
        # More realistic minimum valid inputs
        bmr_min = calculate_bmr(40.0, 120.0, 18, "female")
        assert isinstance(bmr_min, float)
        assert bmr_min > 0
        
        # More realistic maximum valid inputs  
        bmr_max = calculate_bmr(150.0, 220.0, 80, "male")
        assert isinstance(bmr_max, float)
        assert bmr_max > 0
    
    def test_bmr_precision(self):
        """Test BMR calculation precision (rounded to 2 decimal places)"""
        bmr = calculate_bmr(70.5, 175.3, 28, "male")
        # Check that result has at most 2 decimal places
        assert bmr == round(bmr, 2)


class TestTDEECalculation:
    """Test TDEE calculation with activity level multipliers"""
    
    def test_tdee_calculation_all_levels(self):
        """Test TDEE calculation for all activity levels"""
        bmr = 1500.0
        
        expected_results = {
            "sedentary": 1500.0 * 1.2,
            "lightly_active": 1500.0 * 1.375,
            "moderately_active": 1500.0 * 1.55,
            "very_active": 1500.0 * 1.725,
            "extremely_active": 1500.0 * 1.9
        }
        
        for activity_level, expected in expected_results.items():
            tdee = calculate_tdee(bmr, activity_level)
            assert tdee == round(expected, 2)
    
    def test_tdee_greater_than_bmr(self):
        """Test that TDEE is always greater than BMR"""
        bmr = 1600.0
        activity_levels = ["sedentary", "lightly_active", "moderately_active", "very_active", "extremely_active"]
        
        for level in activity_levels:
            tdee = calculate_tdee(bmr, level)
            assert tdee > bmr, f"TDEE {tdee} should be greater than BMR {bmr} for {level}"
    
    def test_tdee_monotonic_increase(self):
        """Test that TDEE increases monotonically with activity level"""
        bmr = 1700.0
        activity_levels = ["sedentary", "lightly_active", "moderately_active", "very_active", "extremely_active"]
        
        previous_tdee = 0
        for level in activity_levels:
            tdee = calculate_tdee(bmr, level)
            assert tdee > previous_tdee, f"TDEE should increase monotonically: {level} = {tdee}"
            previous_tdee = tdee
    
    def test_tdee_input_validation(self):
        """Test TDEE calculation input validation"""
        # Test invalid BMR
        with pytest.raises(ValueError, match="BMR must be positive"):
            calculate_tdee(-100.0, "sedentary")
        
        with pytest.raises(ValueError, match="BMR must be positive"):
            calculate_tdee(0.0, "sedentary")
        
        # Test invalid activity level
        with pytest.raises(ValueError, match="Activity level must be one of"):
            calculate_tdee(1500.0, "invalid_level")
    
    def test_tdee_precision(self):
        """Test TDEE calculation precision (rounded to 2 decimal places)"""
        bmr = 1567.33
        tdee = calculate_tdee(bmr, "moderately_active")
        # Check that result has at most 2 decimal places
        assert tdee == round(tdee, 2)


class TestSafetyConstraints:
    """Test safety constraints calculation"""
    
    def test_safety_constraints_basic(self):
        """Test basic safety constraints calculation"""
        constraints = calculate_safety_constraints(70.0, 170.0, 30, "male", "moderately_active")
        
        # Check all required keys are present
        required_keys = ["min_daily_calories", "max_calorie_deficit", "min_protein_grams", "bmr_calories", "tdee_calories"]
        for key in required_keys:
            assert key in constraints
        
        # Check that min calories equals BMR
        assert constraints["min_daily_calories"] == constraints["bmr_calories"]
        
        # Check that TDEE > BMR
        assert constraints["tdee_calories"] > constraints["bmr_calories"]
        
        # Check that max deficit is reasonable (≤ 20% of TDEE and ≤ 500)
        max_allowed_deficit = min(constraints["tdee_calories"] * 0.2, 500)
        assert constraints["max_calorie_deficit"] == round(max_allowed_deficit, 2)
    
    def test_safety_constraints_protein_by_goal(self):
        """Test that protein requirements vary by goal"""
        weight = 70.0
        
        # Test different goals
        maintenance = calculate_safety_constraints(weight, 170.0, 30, "male", "moderately_active", "maintenance")
        fat_loss = calculate_safety_constraints(weight, 170.0, 30, "male", "moderately_active", "fat_loss")
        muscle_gain = calculate_safety_constraints(weight, 170.0, 30, "male", "moderately_active", "muscle_gain")
        
        # Protein should increase: maintenance < fat_loss < muscle_gain
        assert maintenance["min_protein_grams"] < fat_loss["min_protein_grams"]
        assert fat_loss["min_protein_grams"] < muscle_gain["min_protein_grams"]
        
        # Check specific multipliers
        assert maintenance["min_protein_grams"] == weight * 0.8
        assert fat_loss["min_protein_grams"] == weight * 1.0
        assert muscle_gain["min_protein_grams"] == weight * 1.2
    
    def test_safety_constraints_max_deficit_limits(self):
        """Test that max deficit respects both percentage and absolute limits"""
        # Test case where 20% of TDEE > 500 (should cap at 500)
        high_tdee_constraints = calculate_safety_constraints(100.0, 200.0, 25, "male", "extremely_active")
        assert high_tdee_constraints["max_calorie_deficit"] <= 500
        
        # Test case where 20% of TDEE < 500 (should use percentage)
        low_tdee_constraints = calculate_safety_constraints(50.0, 150.0, 60, "female", "sedentary")
        expected_deficit = low_tdee_constraints["tdee_calories"] * 0.2
        assert abs(low_tdee_constraints["max_calorie_deficit"] - expected_deficit) < 0.01


class TestCalorieTargets:
    """Test calorie target calculations"""
    
    def test_maintenance_goal(self):
        """Test calorie targets for maintenance goal"""
        targets = calculate_calorie_targets(70.0, 170.0, 30, "male", "moderately_active", "maintenance")
        
        # For maintenance, target should equal TDEE
        constraints = calculate_safety_constraints(70.0, 170.0, 30, "male", "moderately_active", "maintenance")
        assert targets["target_calories"] == constraints["tdee_calories"]
        assert targets["weekly_deficit"] == 0
        assert targets["estimated_loss_per_week"] == 0
    
    def test_fat_loss_goal(self):
        """Test calorie targets for fat loss goal"""
        targets = calculate_calorie_targets(70.0, 170.0, 30, "male", "moderately_active", "fat_loss")
        
        constraints = calculate_safety_constraints(70.0, 170.0, 30, "male", "moderately_active", "fat_loss")
        
        # Target should be less than TDEE but not less than BMR
        assert targets["target_calories"] < constraints["tdee_calories"]
        assert targets["target_calories"] >= constraints["min_daily_calories"]
        
        # Should have positive deficit and weight loss
        assert targets["weekly_deficit"] > 0
        assert targets["estimated_loss_per_week"] > 0
    
    def test_muscle_gain_goal(self):
        """Test calorie targets for muscle gain goal"""
        targets = calculate_calorie_targets(70.0, 170.0, 30, "male", "moderately_active", "muscle_gain")
        
        constraints = calculate_safety_constraints(70.0, 170.0, 30, "male", "moderately_active", "muscle_gain")
        
        # Target should be greater than TDEE (surplus)
        assert targets["target_calories"] > constraints["tdee_calories"]
        
        # Should have negative deficit (surplus) and negative weight loss (gain)
        assert targets["weekly_deficit"] < 0
        assert targets["estimated_loss_per_week"] < 0
    
    def test_fat_loss_with_timeline(self):
        """Test fat loss targets with specific timeline"""
        current_weight = 80.0
        target_weight = 75.0  # 5kg loss
        timeline_weeks = 10
        
        targets = calculate_calorie_targets(
            current_weight, 170.0, 30, "male", "moderately_active", "fat_loss",
            target_weight, timeline_weeks
        )
        
        # Should calculate appropriate deficit for timeline
        weight_to_lose = current_weight - target_weight
        expected_weekly_loss = weight_to_lose / timeline_weeks
        
        # Allow some tolerance due to safety constraints
        assert abs(targets["estimated_loss_per_week"] - expected_weekly_loss) < 0.2


class TestMacroTargets:
    """Test macronutrient target calculations"""
    
    def test_macro_targets_basic(self):
        """Test basic macro target calculation"""
        target_calories = 2000.0
        weight_kg = 70.0
        
        macros = calculate_macro_targets(target_calories, weight_kg, "maintenance")
        
        # Check all required keys
        required_keys = ["protein_grams", "fat_grams", "carb_grams", "protein_calories", "fat_calories", "carb_calories"]
        for key in required_keys:
            assert key in macros
        
        # Check that calories add up to target (within rounding tolerance)
        total_calories = macros["protein_calories"] + macros["fat_calories"] + macros["carb_calories"]
        assert abs(total_calories - target_calories) < 1.0
        
        # Check calorie conversions
        assert abs(macros["protein_calories"] - macros["protein_grams"] * 4) < 0.1
        assert abs(macros["fat_calories"] - macros["fat_grams"] * 9) < 0.1
        assert abs(macros["carb_calories"] - macros["carb_grams"] * 4) < 0.1
    
    def test_macro_targets_by_goal(self):
        """Test that macro targets vary appropriately by goal"""
        target_calories = 2000.0
        weight_kg = 70.0
        
        maintenance = calculate_macro_targets(target_calories, weight_kg, "maintenance")
        fat_loss = calculate_macro_targets(target_calories, weight_kg, "fat_loss")
        muscle_gain = calculate_macro_targets(target_calories, weight_kg, "muscle_gain")
        
        # Protein should increase with goal intensity
        assert maintenance["protein_grams"] < fat_loss["protein_grams"]
        assert fat_loss["protein_grams"] < muscle_gain["protein_grams"]
        
        # Check specific protein targets
        assert maintenance["protein_grams"] == weight_kg * 1.0
        assert fat_loss["protein_grams"] == weight_kg * 1.2
        assert muscle_gain["protein_grams"] == weight_kg * 1.6
    
    def test_macro_targets_fat_percentage(self):
        """Test that fat targets are 25% of calories"""
        target_calories = 2000.0
        weight_kg = 70.0
        
        macros = calculate_macro_targets(target_calories, weight_kg, "maintenance")
        
        expected_fat_calories = target_calories * 0.25
        assert abs(macros["fat_calories"] - expected_fat_calories) < 1.0  # Allow for rounding
    
    def test_macro_targets_insufficient_calories(self):
        """Test error handling for insufficient calories"""
        # Very low calories with high protein requirement should fail
        with pytest.raises(ValueError, match="Insufficient calories for balanced macro distribution"):
            calculate_macro_targets(500.0, 100.0, "muscle_gain")


class TestIntegration:
    """Integration tests combining multiple calculations"""
    
    def test_complete_calculation_flow(self):
        """Test complete flow from user data to all calculations"""
        # Sample user data
        weight_kg = 75.0
        height_cm = 175.0
        age = 28
        gender = "male"
        activity_level = "moderately_active"
        primary_goal = "fat_loss"
        
        # Calculate BMR
        bmr = calculate_bmr(weight_kg, height_cm, age, gender)
        assert bmr > 0
        
        # Calculate TDEE
        tdee = calculate_tdee(bmr, activity_level)
        assert tdee > bmr
        
        # Calculate safety constraints
        constraints = calculate_safety_constraints(weight_kg, height_cm, age, gender, activity_level, primary_goal)
        assert constraints["bmr_calories"] == bmr
        assert constraints["tdee_calories"] == tdee
        
        # Calculate calorie targets
        targets = calculate_calorie_targets(weight_kg, height_cm, age, gender, activity_level, primary_goal)
        assert constraints["min_daily_calories"] <= targets["target_calories"] <= tdee
        
        # Calculate macro targets
        macros = calculate_macro_targets(targets["target_calories"], weight_kg, primary_goal)
        total_macro_calories = macros["protein_calories"] + macros["fat_calories"] + macros["carb_calories"]
        assert abs(total_macro_calories - targets["target_calories"]) < 1.0
    
    def test_realistic_user_scenarios(self):
        """Test calculations with realistic user scenarios"""
        scenarios = [
            # (weight, height, age, gender, activity, goal)
            (60.0, 160.0, 25, "female", "lightly_active", "fat_loss"),
            (85.0, 185.0, 35, "male", "very_active", "muscle_gain"),
            (70.0, 170.0, 45, "other", "sedentary", "maintenance"),
            (55.0, 155.0, 22, "female", "extremely_active", "muscle_gain"),
            (90.0, 180.0, 50, "male", "moderately_active", "fat_loss"),
        ]
        
        for weight, height, age, gender, activity, goal in scenarios:
            # All calculations should complete without errors
            bmr = calculate_bmr(weight, height, age, gender)
            tdee = calculate_tdee(bmr, activity)
            constraints = calculate_safety_constraints(weight, height, age, gender, activity, goal)
            targets = calculate_calorie_targets(weight, height, age, gender, activity, goal)
            macros = calculate_macro_targets(targets["target_calories"], weight, goal)
            
            # Basic sanity checks
            assert 800 <= bmr <= 3000
            assert tdee > bmr
            assert constraints["min_daily_calories"] == bmr
            assert targets["target_calories"] > 0
            assert macros["protein_grams"] > 0
            assert macros["fat_grams"] > 0
            assert macros["carb_grams"] > 0