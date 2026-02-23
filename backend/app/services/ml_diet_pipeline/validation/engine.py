"""
Deterministic validation engine
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Set


logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    passed: bool
    warnings: List[str]
    errors: List[str]


class ValidationEngine:
    """Validate plans against deterministic constraints"""

    def validate_daily_plan(
        self,
        meals: List[Dict],
        min_calories: float,
        max_calories: float,
        min_protein: float,
        allergens: Set[str],
        foods_to_avoid: Set[str],
    ) -> ValidationResult:
        warnings: List[str] = []
        errors: List[str] = []

        totals = self._calculate_totals(meals)
        if totals["calories"] < min_calories or totals["calories"] > max_calories:
            errors.append("daily_calories_out_of_bounds")
        if totals["protein"] < min_protein:
            errors.append("daily_protein_below_minimum")

        if self._contains_restricted(meals, allergens, foods_to_avoid):
            errors.append("restricted_ingredient_present")

        if errors:
            logger.error("[VALIDATION_FAILED] errors=%s", ",".join(errors))
            return ValidationResult(False, warnings, errors)

        return ValidationResult(True, warnings, errors)

    def _calculate_totals(self, meals: List[Dict]) -> Dict[str, float]:
        totals = {"calories": 0.0, "protein": 0.0, "fat": 0.0, "carbohydrates": 0.0}
        for meal in meals:
            nutrition = meal.get("nutrition", {})
            totals["calories"] += nutrition.get("calories", 0.0)
            totals["protein"] += nutrition.get("protein", 0.0)
            totals["fat"] += nutrition.get("fat", 0.0)
            totals["carbohydrates"] += nutrition.get("carbohydrates", 0.0)
        return totals

    def _contains_restricted(
        self,
        meals: List[Dict],
        allergens: Set[str],
        foods_to_avoid: Set[str],
    ) -> bool:
        restricted = {item.lower() for item in allergens.union(foods_to_avoid)}
        for meal in meals:
            for ingredient in meal.get("ingredients", []):
                name = str(ingredient.get("name", "")).lower()
                if name in restricted:
                    return True
        return False
