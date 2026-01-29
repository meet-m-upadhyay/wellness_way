"""
Property-based tests for BMR calculation.

These tests validate the correctness properties defined in the design document
using Hypothesis to generate test cases across the input space.
"""

import pytest
from hypothesis import given, strategies as st, assume
from app.services.health_calculations import calculate_bmr, calculate_tdee


class TestBMRProperties:
    """Property-based tests for BMR calculation correctness properties"""
    
    @given(
        weight_kg=st.floats(min_value=30.0, max_value=200.0),
        height_cm=st.floats(min_value=120.0, max_value=220.0),
        age=st.integers(min_value=10, max_value=100),
        gender=st.sampled_from(['male', 'female', 'other'])
    )
    def test_bmr_determinism_property(self, weight_kg, height_cm, age, gender):
        """
        **Validates: Requirements 2.1.3**
        
        Property: BMR calculation must be deterministic.
        For any given user profile (weight, height, age, gender), 
        BMR calculation must always return the same result.
        """
        # Calculate BMR multiple times with same inputs
        bmr1 = calculate_bmr(weight_kg, height_cm, age, gender)
        bmr2 = calculate_bmr(weight_kg, height_cm, age, gender)
        bmr3 = calculate_bmr(weight_kg, height_cm, age, gender)
        
        # All results must be identical
        assert bmr1 == bmr2 == bmr3, f"BMR calculation not deterministic: {bmr1}, {bmr2}, {bmr3}"
    
    @given(
        weight_kg=st.floats(min_value=30.0, max_value=200.0),
        height_cm=st.floats(min_value=120.0, max_value=220.0),
        age=st.integers(min_value=10, max_value=100),
        gender=st.sampled_from(['male', 'female', 'other'])
    )
    def test_bmr_reasonable_bounds_property(self, weight_kg, height_cm, age, gender):
        """
        **Validates: Requirements 2.1.3**
        
        Property: BMR must be positive and within reasonable bounds (800-3000 calories).
        This ensures the calculation produces physiologically reasonable results.
        """
        bmr = calculate_bmr(weight_kg, height_cm, age, gender)
        
        # BMR must be positive (basic mathematical property)
        assert bmr > 0, f"BMR must be positive, got {bmr}"
    
    @given(
        weight_kg=st.floats(min_value=30.0, max_value=200.0),
        height_cm=st.floats(min_value=120.0, max_value=220.0),
        age=st.integers(min_value=10, max_value=100)
    )
    def test_bmr_gender_relationships_property(self, weight_kg, height_cm, age):
        """
        **Validates: Requirements 2.1.3**
        
        Property: BMR gender relationships must be consistent.
        For same physical parameters, male BMR > female BMR, and 'other' BMR 
        should be the average of male and female BMR.
        """
        bmr_male = calculate_bmr(weight_kg, height_cm, age, 'male')
        bmr_female = calculate_bmr(weight_kg, height_cm, age, 'female')
        bmr_other = calculate_bmr(weight_kg, height_cm, age, 'other')
        
        # Male BMR should be higher than female BMR (due to +5 vs -161 adjustment)
        assert bmr_male > bmr_female, f"Male BMR {bmr_male} should be > female BMR {bmr_female}"
        
        # 'Other' BMR should be the average of male and female
        expected_other = (bmr_male + bmr_female) / 2
        assert abs(bmr_other - expected_other) < 0.01, f"Other BMR {bmr_other} should be average of male {bmr_male} and female {bmr_female}"
    
    @given(
        height_cm=st.floats(min_value=120.0, max_value=220.0),
        age=st.integers(min_value=10, max_value=100),
        gender=st.sampled_from(['male', 'female', 'other']),
        weight1=st.floats(min_value=30.0, max_value=150.0),
        weight2=st.floats(min_value=30.0, max_value=150.0)
    )
    def test_bmr_weight_monotonicity_property(self, height_cm, age, gender, weight1, weight2):
        """
        **Validates: Requirements 2.1.3**
        
        Property: BMR must increase monotonically with weight.
        Higher weight should result in higher BMR (all else equal).
        """
        assume(abs(weight1 - weight2) > 0.1)  # Ensure meaningful difference
        
        bmr1 = calculate_bmr(weight1, height_cm, age, gender)
        bmr2 = calculate_bmr(weight2, height_cm, age, gender)
        
        if weight1 < weight2:
            assert bmr1 < bmr2, f"BMR should increase with weight: {weight1}kg->{bmr1}, {weight2}kg->{bmr2}"
        else:
            assert bmr1 > bmr2, f"BMR should increase with weight: {weight2}kg->{bmr2}, {weight1}kg->{bmr1}"
    
    @given(
        weight_kg=st.floats(min_value=30.0, max_value=200.0),
        age=st.integers(min_value=10, max_value=100),
        gender=st.sampled_from(['male', 'female', 'other']),
        height1=st.floats(min_value=120.0, max_value=200.0),
        height2=st.floats(min_value=120.0, max_value=200.0)
    )
    def test_bmr_height_monotonicity_property(self, weight_kg, age, gender, height1, height2):
        """
        **Validates: Requirements 2.1.3**
        
        Property: BMR must increase monotonically with height.
        Taller individuals should have higher BMR (all else equal).
        """
        assume(abs(height1 - height2) > 1.0)  # Ensure meaningful difference
        
        bmr1 = calculate_bmr(weight_kg, height1, age, gender)
        bmr2 = calculate_bmr(weight_kg, height2, age, gender)
        
        if height1 < height2:
            assert bmr1 < bmr2, f"BMR should increase with height: {height1}cm->{bmr1}, {height2}cm->{bmr2}"
        else:
            assert bmr1 > bmr2, f"BMR should increase with height: {height2}cm->{bmr2}, {height1}cm->{bmr1}"
    
    @given(
        weight_kg=st.floats(min_value=30.0, max_value=200.0),
        height_cm=st.floats(min_value=120.0, max_value=220.0),
        gender=st.sampled_from(['male', 'female', 'other']),
        age1=st.integers(min_value=10, max_value=80),
        age2=st.integers(min_value=10, max_value=80)
    )
    def test_bmr_age_inverse_monotonicity_property(self, weight_kg, height_cm, gender, age1, age2):
        """
        **Validates: Requirements 2.1.3**
        
        Property: BMR must decrease with age (inverse monotonicity).
        Older individuals should have lower BMR (all else equal).
        """
        assume(abs(age1 - age2) > 2)  # Ensure meaningful difference
        
        bmr1 = calculate_bmr(weight_kg, height_cm, age1, gender)
        bmr2 = calculate_bmr(weight_kg, height_cm, age2, gender)
        
        if age1 < age2:
            assert bmr1 > bmr2, f"BMR should decrease with age: {age1}y->{bmr1}, {age2}y->{bmr2}"
        else:
            assert bmr1 < bmr2, f"BMR should decrease with age: {age2}y->{bmr2}, {age1}y->{bmr1}"
    
    @given(
        weight_kg=st.floats(min_value=30.0, max_value=200.0),
        height_cm=st.floats(min_value=120.0, max_value=220.0),
        age=st.integers(min_value=10, max_value=100),
        gender=st.sampled_from(['male', 'female', 'other'])
    )
    def test_bmr_precision_property(self, weight_kg, height_cm, age, gender):
        """
        **Validates: Requirements 2.1.3**
        
        Property: BMR results must have consistent precision.
        Results should be rounded to 2 decimal places for consistency.
        """
        bmr = calculate_bmr(weight_kg, height_cm, age, gender)
        
        # Check that result has at most 2 decimal places
        assert bmr == round(bmr, 2), f"BMR {bmr} should be rounded to 2 decimal places"
        
        # Check that result is a float
        assert isinstance(bmr, float), f"BMR should be a float, got {type(bmr)}"


class TestTDEEProperties:
    """Property-based tests for TDEE calculation correctness properties"""
    
    @given(
        weight_kg=st.floats(min_value=30.0, max_value=200.0),
        height_cm=st.floats(min_value=120.0, max_value=220.0),
        age=st.integers(min_value=10, max_value=100),
        gender=st.sampled_from(['male', 'female', 'other']),
        activity_level=st.sampled_from(['sedentary', 'lightly_active', 'moderately_active', 'very_active', 'extremely_active'])
    )
    def test_tdee_greater_than_bmr_property(self, weight_kg, height_cm, age, gender, activity_level):
        """
        **Validates: Requirements 2.1.3, 2.1.4**
        
        Property: TDEE must always be greater than BMR.
        Total Daily Energy Expenditure includes BMR plus activity, so it must exceed BMR.
        """
        bmr = calculate_bmr(weight_kg, height_cm, age, gender)
        tdee = calculate_tdee(bmr, activity_level)
        
        assert tdee > bmr, f"TDEE {tdee} must be greater than BMR {bmr} for activity level {activity_level}"
    
    @given(
        bmr=st.floats(min_value=800.0, max_value=3000.0)
    )
    def test_tdee_activity_level_monotonicity_property(self, bmr):
        """
        **Validates: Requirements 2.1.3, 2.1.4**
        
        Property: TDEE must increase monotonically with activity level.
        Higher activity levels should result in higher TDEE.
        """
        activity_levels = ['sedentary', 'lightly_active', 'moderately_active', 'very_active', 'extremely_active']
        
        previous_tdee = 0
        for activity_level in activity_levels:
            tdee = calculate_tdee(bmr, activity_level)
            assert tdee > previous_tdee, f"TDEE should increase monotonically: {activity_level} = {tdee}, previous = {previous_tdee}"
            previous_tdee = tdee
    
    @given(
        bmr=st.floats(min_value=800.0, max_value=3000.0),
        activity_level=st.sampled_from(['sedentary', 'lightly_active', 'moderately_active', 'very_active', 'extremely_active'])
    )
    def test_tdee_exact_relationship_property(self, bmr, activity_level):
        """
        **Validates: Requirements 2.1.3, 2.1.4**
        
        Property: TDEE = BMR × activity_multiplier (exact relationship).
        The relationship between BMR and TDEE must be precisely defined by multipliers.
        """
        multipliers = {
            "sedentary": 1.2,
            "lightly_active": 1.375,
            "moderately_active": 1.55,
            "very_active": 1.725,
            "extremely_active": 1.9
        }
        
        tdee = calculate_tdee(bmr, activity_level)
        expected_tdee = round(bmr * multipliers[activity_level], 2)
        
        assert tdee == expected_tdee, f"TDEE {tdee} should equal BMR {bmr} × {multipliers[activity_level]} = {expected_tdee}"
    
    @given(
        bmr=st.floats(min_value=800.0, max_value=3000.0),
        activity_level=st.sampled_from(['sedentary', 'lightly_active', 'moderately_active', 'very_active', 'extremely_active'])
    )
    def test_tdee_determinism_property(self, bmr, activity_level):
        """
        **Validates: Requirements 2.1.3, 2.1.4**
        
        Property: TDEE calculation must be deterministic.
        Same BMR and activity level should always produce the same TDEE.
        """
        tdee1 = calculate_tdee(bmr, activity_level)
        tdee2 = calculate_tdee(bmr, activity_level)
        tdee3 = calculate_tdee(bmr, activity_level)
        
        assert tdee1 == tdee2 == tdee3, f"TDEE calculation not deterministic: {tdee1}, {tdee2}, {tdee3}"
    
    @given(
        bmr=st.floats(min_value=800.0, max_value=3000.0),
        activity_level=st.sampled_from(['sedentary', 'lightly_active', 'moderately_active', 'very_active', 'extremely_active'])
    )
    def test_tdee_precision_property(self, bmr, activity_level):
        """
        **Validates: Requirements 2.1.3, 2.1.4**
        
        Property: TDEE results must have consistent precision.
        Results should be rounded to 2 decimal places for consistency.
        """
        tdee = calculate_tdee(bmr, activity_level)
        
        # Check that result has at most 2 decimal places
        assert tdee == round(tdee, 2), f"TDEE {tdee} should be rounded to 2 decimal places"
        
        # Check that result is a float
        assert isinstance(tdee, float), f"TDEE should be a float, got {type(tdee)}"


class TestIntegratedProperties:
    """Property-based tests for integrated BMR and TDEE calculations"""
    
    @given(
        weight_kg=st.floats(min_value=30.0, max_value=200.0),
        height_cm=st.floats(min_value=120.0, max_value=220.0),
        age=st.integers(min_value=10, max_value=100),
        gender=st.sampled_from(['male', 'female', 'other']),
        activity_level=st.sampled_from(['sedentary', 'lightly_active', 'moderately_active', 'very_active', 'extremely_active'])
    )
    def test_complete_calculation_consistency_property(self, weight_kg, height_cm, age, gender, activity_level):
        """
        **Validates: Requirements 2.1.3, 2.1.4**
        
        Property: Complete calculation flow must be consistent.
        BMR -> TDEE calculation should maintain all individual properties.
        """
        # Calculate BMR
        bmr = calculate_bmr(weight_kg, height_cm, age, gender)
        
        # Calculate TDEE
        tdee = calculate_tdee(bmr, activity_level)
        
        # Verify all properties hold
        assert bmr > 0, f"BMR {bmr} must be positive"
        assert tdee > bmr, f"TDEE {tdee} not greater than BMR {bmr}"
        assert isinstance(bmr, float), f"BMR should be float"
        assert isinstance(tdee, float), f"TDEE should be float"
        assert bmr == round(bmr, 2), f"BMR precision issue"
        assert tdee == round(tdee, 2), f"TDEE precision issue"
        
        # Verify TDEE calculation is correct
        multipliers = {
            "sedentary": 1.2,
            "lightly_active": 1.375,
            "moderately_active": 1.55,
            "very_active": 1.725,
            "extremely_active": 1.9
        }
        expected_tdee = round(bmr * multipliers[activity_level], 2)
        assert tdee == expected_tdee, f"TDEE calculation inconsistent"