"""USDA FoodData Central nutrition API provider"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from .base import NutritionProvider, NutritionResult

logger = logging.getLogger(__name__)

SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

# USDA nutrient name mapping
_NUTRIENT_MAP = {
    "Energy": "calories",
    "Protein": "protein",
    "Total lipid (fat)": "fat",
    "Carbohydrate, by difference": "carbohydrates",
    "Fiber, total dietary": "fiber",
}


class USDAProvider(NutritionProvider):
    """USDA FoodData Central — free, unlimited requests."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    @property
    def source_name(self) -> str:
        return "usda"

    async def lookup(self, ingredient_name: str) -> Optional[NutritionResult]:
        try:
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.get(
                    SEARCH_URL,
                    params={
                        "query": ingredient_name,
                        "api_key": self._api_key,
                        "pageSize": 1,
                        "dataType": "Foundation,SR Legacy",
                    },
                    timeout=15.0,
                )

            if response.status_code != 200:
                logger.error(
                    f"[DEBUG][NUTRITION_PROVIDER_ERROR] provider=usda "
                    f"status={response.status_code} ingredient={ingredient_name}"
                )
                return None

            data = response.json()
            foods = data.get("foods", [])
            if not foods:
                logger.info(f"[DEBUG][NUTRITION_NOT_FOUND] provider=usda ingredient={ingredient_name}")
                return None

            food = foods[0]
            nutrients = {n["nutrientName"]: n.get("value", 0) for n in food.get("foodNutrients", [])}

            macros = {}
            for usda_name, our_key in _NUTRIENT_MAP.items():
                macros[our_key] = nutrients.get(usda_name, 0)

            # USDA values are per 100g by default
            return NutritionResult(
                name=food.get("description", ingredient_name).title(),
                calories=macros.get("calories", 0),
                protein=macros.get("protein", 0),
                fat=macros.get("fat", 0),
                carbohydrates=macros.get("carbohydrates", 0),
                fiber=macros.get("fiber", 0),
                serving_size_g=100.0,
                source=self.source_name,
            )

        except httpx.TimeoutException:
            logger.error(f"[DEBUG][NUTRITION_TIMEOUT] provider=usda ingredient={ingredient_name}")
            return None
        except Exception as e:
            logger.error(f"[DEBUG][NUTRITION_PROVIDER_ERROR] provider=usda error={e}")
            return None
