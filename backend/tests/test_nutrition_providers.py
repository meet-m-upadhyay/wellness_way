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


import httpx
from unittest.mock import AsyncMock, patch

from app.services.ml_diet_pipeline.nutrition.providers.calorieninjas import CalorieNinjasProvider


class TestCalorieNinjasProvider:
    @pytest.mark.asyncio
    async def test_source_name(self):
        provider = CalorieNinjasProvider(api_key="test-key")
        assert provider.source_name == "calorieninjas"

    @pytest.mark.asyncio
    async def test_lookup_success(self):
        mock_response = httpx.Response(
            200,
            json={
                "items": [
                    {
                        "name": "chicken tikka",
                        "calories": 150.0,
                        "protein_g": 28.0,
                        "fat_total_g": 3.5,
                        "carbohydrates_total_g": 2.0,
                        "fiber_g": 0.0,
                        "serving_size_g": 100.0,
                    }
                ]
            },
            request=httpx.Request("GET", "https://api.calorieninjas.com/v1/nutrition"),
        )

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            provider = CalorieNinjasProvider(api_key="test-key")
            result = await provider.lookup("chicken tikka")

        assert result is not None
        assert result.name == "chicken tikka"
        assert result.protein == 28.0
        assert result.source == "calorieninjas"

    @pytest.mark.asyncio
    async def test_lookup_empty_items(self):
        mock_response = httpx.Response(
            200,
            json={"items": []},
            request=httpx.Request("GET", "https://api.calorieninjas.com/v1/nutrition"),
        )

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            provider = CalorieNinjasProvider(api_key="test-key")
            result = await provider.lookup("nonexistent food xyz")

        assert result is None

    @pytest.mark.asyncio
    async def test_lookup_api_error_returns_none(self):
        mock_response = httpx.Response(
            500,
            text="Internal Server Error",
            request=httpx.Request("GET", "https://api.calorieninjas.com/v1/nutrition"),
        )

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            provider = CalorieNinjasProvider(api_key="test-key")
            result = await provider.lookup("chicken tikka")

        assert result is None

    @pytest.mark.asyncio
    async def test_lookup_normalizes_to_per_100g(self):
        mock_response = httpx.Response(
            200,
            json={
                "items": [
                    {
                        "name": "brown rice",
                        "calories": 230.0,
                        "protein_g": 4.8,
                        "fat_total_g": 1.8,
                        "carbohydrates_total_g": 46.0,
                        "fiber_g": 3.6,
                        "serving_size_g": 200.0,
                    }
                ]
            },
            request=httpx.Request("GET", "https://api.calorieninjas.com/v1/nutrition"),
        )

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            provider = CalorieNinjasProvider(api_key="test-key")
            result = await provider.lookup("brown rice")

        assert result is not None
        assert result.calories == pytest.approx(115.0)
        assert result.protein == pytest.approx(2.4)


from app.services.ml_diet_pipeline.nutrition.providers.usda import USDAProvider


class TestUSDAProvider:
    @pytest.mark.asyncio
    async def test_source_name(self):
        provider = USDAProvider(api_key="test-key")
        assert provider.source_name == "usda"

    @pytest.mark.asyncio
    async def test_lookup_success(self):
        mock_response = httpx.Response(
            200,
            json={
                "foods": [
                    {
                        "description": "Chicken, broilers or fryers, breast, skinless",
                        "foodNutrients": [
                            {"nutrientName": "Energy", "unitName": "KCAL", "value": 165.0},
                            {"nutrientName": "Protein", "unitName": "G", "value": 31.0},
                            {"nutrientName": "Total lipid (fat)", "unitName": "G", "value": 3.6},
                            {"nutrientName": "Carbohydrate, by difference", "unitName": "G", "value": 0.0},
                            {"nutrientName": "Fiber, total dietary", "unitName": "G", "value": 0.0},
                        ],
                    }
                ]
            },
            request=httpx.Request("GET", "https://api.nal.usda.gov/fdc/v1/foods/search"),
        )

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            provider = USDAProvider(api_key="test-key")
            result = await provider.lookup("chicken breast")

        assert result is not None
        assert result.protein == 31.0
        assert result.calories == 165.0
        assert result.source == "usda"

    @pytest.mark.asyncio
    async def test_lookup_no_results(self):
        mock_response = httpx.Response(
            200,
            json={"foods": []},
            request=httpx.Request("GET", "https://api.nal.usda.gov/fdc/v1/foods/search"),
        )

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            provider = USDAProvider(api_key="test-key")
            result = await provider.lookup("nonexistent food xyz")

        assert result is None

    @pytest.mark.asyncio
    async def test_lookup_api_error_returns_none(self):
        mock_response = httpx.Response(
            500,
            text="Internal Server Error",
            request=httpx.Request("GET", "https://api.nal.usda.gov/fdc/v1/foods/search"),
        )

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            provider = USDAProvider(api_key="test-key")
            result = await provider.lookup("chicken breast")

        assert result is None
