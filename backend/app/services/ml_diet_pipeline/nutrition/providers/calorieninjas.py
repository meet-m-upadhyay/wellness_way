"""API Ninjas nutrition API provider (replaces CalorieNinjas which is shutting down)"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from .base import NutritionProvider, NutritionResult

logger = logging.getLogger(__name__)

API_URL = "https://api.api-ninjas.com/v1/nutrition"


class APINinjasProvider(NutritionProvider):
    """API Ninjas Nutrition API — free tier: 10,000 requests/month."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    @property
    def source_name(self) -> str:
        return "api_ninjas"

    async def lookup(self, ingredient_name: str) -> Optional[NutritionResult]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    API_URL,
                    params={"query": ingredient_name},
                    headers={"X-Api-Key": self._api_key},
                    timeout=15.0,
                )

            if response.status_code == 429:
                logger.warning("[DEBUG][NUTRITION_RATE_LIMITED] provider=api_ninjas")
                return None

            if response.status_code != 200:
                logger.error(
                    f"[DEBUG][NUTRITION_PROVIDER_ERROR] provider=api_ninjas "
                    f"status={response.status_code} ingredient={ingredient_name}"
                )
                return None

            # API Ninjas returns a direct JSON array, not {"items": [...]}
            items = response.json()
            if not isinstance(items, list) or not items:
                logger.info(
                    f"[DEBUG][NUTRITION_NOT_FOUND] provider=api_ninjas ingredient={ingredient_name}"
                )
                return None

            item = items[0]
            serving_g = item.get("serving_size_g") or 100.0

            return NutritionResult.from_serving(
                name=item.get("name", ingredient_name),
                calories=item.get("calories", 0),
                protein=item.get("protein_g", 0),
                fat=item.get("fat_total_g", 0),
                carbohydrates=item.get("carbohydrates_total_g", 0),
                fiber=item.get("fiber_g", 0),
                serving_size_g=serving_g,
                source=self.source_name,
            )

        except httpx.TimeoutException:
            logger.error(f"[DEBUG][NUTRITION_TIMEOUT] provider=api_ninjas ingredient={ingredient_name}")
            return None
        except Exception as e:
            logger.error(f"[DEBUG][NUTRITION_PROVIDER_ERROR] provider=api_ninjas error={e}")
            return None


# Backward-compatible alias
CalorieNinjasProvider = APINinjasProvider
