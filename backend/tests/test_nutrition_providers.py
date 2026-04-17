"""Tests for nutrition API providers"""

import pytest
from app.services.ml_diet_pipeline.nutrition.providers.base import NutritionResult


class TestNutritionResult:
    def test_create_result_with_valid_data(self):
        result = NutritionResult(
            name="Chicken Tikka",
            calories=150.0,
            protein=28.0,
            fat=3.5,
            carbohydrates=2.0,
            fiber=0.0,
            serving_size_g=100.0,
            source="calorieninjas",
        )
        assert result.name == "Chicken Tikka"
        assert result.calories == 150.0
        assert result.protein == 28.0
        assert result.source == "calorieninjas"

    def test_to_macros_dict(self):
        result = NutritionResult(
            name="Chicken Tikka",
            calories=150.0,
            protein=28.0,
            fat=3.5,
            carbohydrates=2.0,
            fiber=0.0,
            serving_size_g=100.0,
            source="calorieninjas",
        )
        macros = result.to_macros_dict()
        assert macros == {
            "calories": 150.0,
            "protein": 28.0,
            "fat": 3.5,
            "carbohydrates": 2.0,
            "fiber": 0.0,
        }

    def test_normalize_to_per_100g(self):
        # API returns macros for a 200g serving
        result = NutritionResult.from_serving(
            name="Brown Rice",
            calories=230.0,
            protein=4.8,
            fat=1.8,
            carbohydrates=46.0,
            fiber=3.6,
            serving_size_g=200.0,
            source="calorieninjas",
        )
        assert result.calories == pytest.approx(115.0)
        assert result.protein == pytest.approx(2.4)
        assert result.serving_size_g == 200.0  # original preserved
