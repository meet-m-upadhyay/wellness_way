"""
Deterministic scaling engine
"""

from __future__ import annotations

import logging
from typing import Dict, List


logger = logging.getLogger(__name__)


class ScalingEngine:
    """Deterministic portion scaling"""

    def scale_meal(self, meal: Dict, target_calories: float) -> Dict:
        nutrition = meal.get("nutrition", {})
        current_calories = nutrition.get("calories", 0.0)
        if current_calories <= 0:
            return meal

        factor = target_calories / current_calories
        for ingredient in meal.get("ingredients", []):
            ingredient["quantity"] = round(ingredient["quantity"] * factor, 2)
            ingredient_nutrition = ingredient.get("nutrition", {})
            ingredient["nutrition"] = {
                key: value * factor for key, value in ingredient_nutrition.items()
            }

        meal["nutrition"] = {
            key: value * factor for key, value in nutrition.items()
        }

        logger.info("[SCALING_APPLIED] target=%.1f factor=%.4f", target_calories, factor)
        return meal

    def scale_day_to_target(
        self,
        meals: List[Dict],
        target_daily_calories: float,
        **kwargs
    ) -> List[Dict]:
        total_calories = sum(meal.get("nutrition", {}).get("calories", 0.0) for meal in meals)
        if total_calories <= 0:
            return meals

        factor = target_daily_calories / total_calories
        scaled_meals = []
        for meal in meals:
            scaled = self.scale_meal(meal, meal.get("nutrition", {}).get("calories", 0.0) * factor)
            scaled_meals.append(scaled)
        return scaled_meals
