"""
Edamam nutrition provider with response caching.

Queries the Edamam Food Database API (parser endpoint) and caches
responses in v2_external_nutrition_cache to conserve the 10K/month
free tier. Graceful no-op if EDAMAM_APP_ID / EDAMAM_APP_KEY are not set.
"""

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.ml_diet_pipeline.nutrition.providers.base import (
    NutritionProvider,
    NutritionResult,
)

logger = logging.getLogger(__name__)

EDAMAM_API_URL = "https://api.edamam.com/api/food-database/v2/parser"
CACHE_TTL_DAYS = 30


class EdamamProvider(NutritionProvider):
    """Nutrition provider using Edamam Food Database API with caching."""

    def __init__(self, db: Session):
        self._db = db
        self._app_id = os.environ.get("EDAMAM_APP_ID")
        self._app_key = os.environ.get("EDAMAM_APP_KEY")
        self._available = bool(self._app_id and self._app_key)
        if not self._available:
            logger.info("Edamam API keys not configured — provider disabled")

    @property
    def source_name(self) -> str:
        return "edamam"

    async def lookup(self, ingredient_name: str) -> Optional[NutritionResult]:
        """Look up per-100g macros via Edamam, with cache layer."""
        if not self._available:
            return None

        query_key = ingredient_name.strip().lower()

        # 1. Check cache
        cached = self._get_cached(query_key)
        if cached is not None:
            return cached

        # 2. Call Edamam API
        result = await self._call_api(query_key)
        if result:
            self._save_cache(query_key, result)
        return result

    def _get_cached(self, query_key: str) -> Optional[NutritionResult]:
        """Check v2_external_nutrition_cache for a fresh entry."""
        row = self._db.execute(
            text("""
                SELECT response_data FROM v2_external_nutrition_cache
                WHERE query_key = :key AND provider = 'edamam'
                AND (expires_at IS NULL OR expires_at > NOW())
                LIMIT 1
            """),
            {"key": query_key},
        ).fetchone()

        if not row:
            return None

        data = row.response_data
        return NutritionResult(
            name=data.get("name", query_key),
            calories=data.get("calories", 0),
            protein=data.get("protein", 0),
            fat=data.get("fat", 0),
            carbohydrates=data.get("carbohydrates", 0),
            fiber=data.get("fiber", 0),
            serving_size_g=100.0,
            source="edamam_cached",
        )

    def _save_cache(self, query_key: str, result: NutritionResult):
        """Store API response in cache."""
        import uuid
        import json

        expires = datetime.now(timezone.utc) + timedelta(days=CACHE_TTL_DAYS)
        self._db.execute(
            text("""
                INSERT INTO v2_external_nutrition_cache (id, query_key, provider, response_data, expires_at)
                VALUES (:id, :key, 'edamam', :data, :expires)
                ON CONFLICT (query_key) DO UPDATE SET
                    response_data = :data, expires_at = :expires
            """),
            {
                "id": str(uuid.uuid4()),
                "key": query_key,
                "data": json.dumps(result.to_macros_dict() | {"name": result.name}),
                "expires": expires,
            },
        )
        self._db.commit()

    async def _call_api(self, query: str) -> Optional[NutritionResult]:
        """Call Edamam parser API and extract per-100g macros."""
        try:
            import httpx

            async with httpx.AsyncClient(verify=False) as client:
                resp = await client.get(
                    EDAMAM_API_URL,
                    params={
                        "app_id": self._app_id,
                        "app_key": self._app_key,
                        "ingr": query,
                        "nutrition-type": "cooking",
                    },
                    timeout=10.0,
                )
                resp.raise_for_status()
                data = resp.json()

            # Extract first parsed food
            hints = data.get("hints", [])
            if not hints:
                logger.debug("Edamam: no results for '%s'", query)
                return None

            food = hints[0].get("food", {})
            nutrients = food.get("nutrients", {})

            return NutritionResult(
                name=food.get("label", query),
                calories=nutrients.get("ENERC_KCAL", 0),
                protein=nutrients.get("PROCNT", 0),
                fat=nutrients.get("FAT", 0),
                carbohydrates=nutrients.get("CHOCDF", 0),
                fiber=nutrients.get("FIBTG", 0),
                serving_size_g=100.0,
                source=self.source_name,
            )

        except Exception as e:
            logger.warning("Edamam API error for '%s': %s", query, e)
            return None
