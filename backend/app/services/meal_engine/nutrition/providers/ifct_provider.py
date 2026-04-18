"""
IFCT nutrition provider — queries v2_ingredients for local Indian food data.

Lookup chain:
  1. Exact match on name (case-insensitive)
  2. Match on search_aliases array
  3. Canonical food defaults (for ambiguous common terms)
"""

import logging
from typing import Optional

from sqlalchemy import text, func
from sqlalchemy.orm import Session

from app.services.ml_diet_pipeline.nutrition.providers.base import (
    NutritionProvider,
    NutritionResult,
)
from app.services.meal_engine.config.loader import ConfigLoader

logger = logging.getLogger(__name__)


class IFCTProvider(NutritionProvider):
    """Nutrition provider backed by the local IFCT v2_ingredients table."""

    def __init__(self, db: Session, config: Optional[ConfigLoader] = None):
        self._db = db
        self._config = config or ConfigLoader()

    @property
    def source_name(self) -> str:
        return "ifct_2017"

    async def lookup(self, ingredient_name: str) -> Optional[NutritionResult]:
        """Look up per-100g macros for an ingredient in v2_ingredients."""
        name_lower = ingredient_name.strip().lower()

        # 1. Exact name match
        row = self._query_by_name(name_lower)
        if row:
            return self._to_result(row)

        # 2. Search aliases match
        row = self._query_by_alias(name_lower)
        if row:
            return self._to_result(row)

        # 3. Canonical defaults
        row = self._query_canonical(name_lower)
        if row:
            logger.info("IFCT canonical default for '%s' -> %s", ingredient_name, row.name)
            return self._to_result(row)

        return None

    def _query_by_name(self, name_lower: str):
        """Exact match on name (case-insensitive)."""
        result = self._db.execute(
            text("""
                SELECT id, code, name, kcal, protein_g, fat_g, carbs_g, fiber_g,
                       sugar_g, sat_fat_g, cholesterol_mg, sodium_mg,
                       data_quality, form
                FROM v2_ingredients
                WHERE LOWER(name) = :name
                LIMIT 1
            """),
            {"name": name_lower},
        )
        return result.fetchone()

    def _query_by_alias(self, name_lower: str):
        """Match on search_aliases array."""
        result = self._db.execute(
            text("""
                SELECT id, code, name, kcal, protein_g, fat_g, carbs_g, fiber_g,
                       sugar_g, sat_fat_g, cholesterol_mg, sodium_mg,
                       data_quality, form
                FROM v2_ingredients
                WHERE :name = ANY(search_aliases)
                LIMIT 1
            """),
            {"name": name_lower},
        )
        return result.fetchone()

    def _query_canonical(self, name_lower: str):
        """Check canonical_foods.json for a default IFCT code."""
        canonical = self._config.canonical_foods
        # Try exact key match
        entry = canonical.get(name_lower)
        if not entry or not entry.get("default_code"):
            # Try partial: "chicken breast" → check if "chicken" is a key
            for key in canonical:
                if key in name_lower or name_lower in key:
                    entry = canonical[key]
                    break
        if not entry or not entry.get("default_code"):
            return None

        code = entry["default_code"]
        result = self._db.execute(
            text("""
                SELECT id, code, name, kcal, protein_g, fat_g, carbs_g, fiber_g,
                       sugar_g, sat_fat_g, cholesterol_mg, sodium_mg,
                       data_quality, form
                FROM v2_ingredients
                WHERE code = :code
                LIMIT 1
            """),
            {"code": code},
        )
        return result.fetchone()

    def _to_result(self, row) -> NutritionResult:
        """Convert a DB row to NutritionResult (per-100g)."""
        return NutritionResult(
            name=row.name,
            calories=row.kcal or 0,
            protein=row.protein_g or 0,
            fat=row.fat_g or 0,
            carbohydrates=row.carbs_g or 0,
            fiber=row.fiber_g or 0,
            serving_size_g=100.0,
            source=self.source_name,
        )
