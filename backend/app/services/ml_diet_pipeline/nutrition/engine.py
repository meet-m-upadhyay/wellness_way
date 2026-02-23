"""
Deterministic nutrition engine using food registry
"""

from __future__ import annotations

from typing import Dict, List

from sqlalchemy.orm import Session

from app.models.food_items import FoodItem


class NutritionEngine:
    """Deterministic nutrition calculations backed by registry"""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_food_macros(self, food_id: str) -> Dict[str, float]:
        food = self._db.query(FoodItem).filter(FoodItem.id == food_id).first()
        if not food:
            raise ValueError(f"Food item not found: {food_id}")
        return dict(food.macros)

    def calculate_ingredient_nutrition(self, food_id: str, quantity_g: float) -> Dict[str, float]:
        macros = self.get_food_macros(food_id)
        factor = quantity_g / 100.0
        return {
            "calories": macros["calories"] * factor,
            "protein": macros["protein"] * factor,
            "fat": macros["fat"] * factor,
            "carbohydrates": macros["carbohydrates"] * factor,
        }

    def calculate_meal_nutrition(self, ingredients: List[Dict]) -> Dict[str, float]:
        totals = {"calories": 0.0, "protein": 0.0, "fat": 0.0, "carbohydrates": 0.0}
        for ingredient in ingredients:
            nutrition = ingredient.get("nutrition") or {}
            totals["calories"] += nutrition.get("calories", 0.0)
            totals["protein"] += nutrition.get("protein", 0.0)
            totals["fat"] += nutrition.get("fat", 0.0)
            totals["carbohydrates"] += nutrition.get("carbohydrates", 0.0)
        return totals
