"""
Cuisine-aware nutrition router.

Picks the provider chain based on cuisine:
  Indian  → IFCT → Edamam (cached) → USDA
  Western → USDA → Edamam (cached)

Skips Edamam gracefully if keys are not configured.
"""

import logging
import os
from typing import Optional, List

from sqlalchemy.orm import Session

from app.services.ml_diet_pipeline.nutrition.providers.base import (
    NutritionProvider,
    NutritionResult,
)
from app.services.meal_engine.nutrition.providers.ifct_provider import IFCTProvider
from app.services.meal_engine.nutrition.providers.edamam_provider import EdamamProvider
from app.services.meal_engine.config.loader import ConfigLoader

logger = logging.getLogger(__name__)

# Lazy import of existing USDA provider to avoid circular imports
_usda_provider = None


def _get_usda_provider():
    global _usda_provider
    if _usda_provider is None:
        from app.services.ml_diet_pipeline.nutrition.providers.usda import USDAProvider
        api_key = os.environ.get("USDA_API_KEY", "")
        if not api_key:
            logger.info("USDA_API_KEY not set — USDA provider disabled")
            return None
        _usda_provider = USDAProvider(api_key)
    return _usda_provider


# Provider chain per cuisine
CUISINE_CHAINS = {
    "indian": ["ifct", "edamam", "usda"],
    "indian_north": ["ifct", "edamam", "usda"],
    "indian_south": ["ifct", "edamam", "usda"],
    "mediterranean": ["usda", "edamam"],
    "italian": ["usda", "edamam"],
    "default": ["usda", "edamam"],
}


class NutritionRouter:
    """Routes nutrition lookups to the appropriate provider chain based on cuisine."""

    def __init__(self, db: Session, config: Optional[ConfigLoader] = None):
        self._db = db
        self._config = config or ConfigLoader()

        # Initialize providers
        self._providers = {
            "ifct": IFCTProvider(db, self._config),
            "edamam": EdamamProvider(db),
            "usda": _get_usda_provider(),
        }

    @staticmethod
    def _clean_name(name: str) -> str:
        """Strip grams/quantities from ingredient name before lookup."""
        import re
        cleaned = name.strip()
        cleaned = re.sub(r',?\s*\d+\.?\d*\s*(g|gm|grams?|ml|kg)\s*$', '', cleaned, flags=re.IGNORECASE)
        return cleaned.strip().rstrip(',').strip()

    async def lookup(
        self, ingredient_name: str, cuisine: str = "indian"
    ) -> Optional[NutritionResult]:
        """Look up nutrition data using the cuisine-appropriate provider chain.

        Args:
            ingredient_name: Name of the ingredient.
            cuisine: Cuisine context (determines provider order).

        Returns:
            NutritionResult (per-100g) or None if all providers miss.
        """
        ingredient_name = self._clean_name(ingredient_name)
        chain = CUISINE_CHAINS.get(cuisine.lower(), CUISINE_CHAINS["default"])

        for provider_key in chain:
            provider = self._providers.get(provider_key)
            if provider is None:
                continue

            try:
                result = await provider.lookup(ingredient_name)
                if result is not None:
                    logger.debug(
                        "Nutrition resolved: '%s' via %s (cuisine=%s)",
                        ingredient_name, result.source, cuisine,
                    )
                    return result
            except Exception as e:
                logger.warning(
                    "Provider %s failed for '%s': %s",
                    provider_key, ingredient_name, e,
                )
                continue

        logger.warning("No nutrition data found for '%s' (cuisine=%s)", ingredient_name, cuisine)
        return None
