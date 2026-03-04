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

    def get_food_macros(self, food_id: str = None, name: str = None) -> Dict[str, float]:
        if food_id:
            food = self._db.query(FoodItem).filter(FoodItem.id == food_id).first()
        elif name:
            food = self._db.query(FoodItem).filter(FoodItem.canonical_name.ilike(f"%{name}%")).first()
        else:
            raise ValueError("Must provide either food_id or name")
            
        if not food:
            raise ValueError(f"Food item not found: {food_id or name}")
        return dict(food.macros)

    def calculate_ingredient_nutrition(self, food_id: str = None, quantity_g: float = None, **kwargs) -> Dict[str, float]:
        target_food_id = food_id
        target_quantity = quantity_g if quantity_g is not None else kwargs.get("quantity")
        target_name = kwargs.get("ingredient_name")

        if target_quantity is None:
            raise ValueError("Quantity must be provided")

        macros = self.get_food_macros(food_id=target_food_id, name=target_name)
        factor = target_quantity / 100.0
        return {
            "calories": macros.get("calories", 0) * factor,
            "protein": macros.get("protein", 0) * factor,
            "fat": macros.get("fat", 0) * factor,
            "carbohydrates": macros.get("carbohydrates", 0) * factor,
            "fiber": macros.get("fiber", 0) * factor,
        }

    def calculate_meal_nutrition(self, ingredients: List[Dict]) -> Dict[str, float]:
        totals = {"calories": 0.0, "protein": 0.0, "fat": 0.0, "carbohydrates": 0.0, "fiber": 0.0}
        for ingredient in ingredients:
            nutrition = ingredient.get("nutrition") or {}
            totals["calories"] += nutrition.get("calories", 0.0)
            totals["protein"] += nutrition.get("protein", 0.0)
            totals["fat"] += nutrition.get("fat", 0.0)
            totals["carbohydrates"] += nutrition.get("carbohydrates", 0.0)
            totals["fiber"] += nutrition.get("fiber", 0.0)
        return totals

    def calculate_daily_nutrition(self, meals: List[Dict]) -> Dict[str, float]:
        totals = {"calories": 0.0, "protein": 0.0, "fat": 0.0, "carbohydrates": 0.0, "fiber": 0.0}
        for meal in meals:
            nutrition = meal.get("nutrition") or {}
            totals["calories"] += nutrition.get("calories", 0.0)
            totals["protein"] += nutrition.get("protein", 0.0)
            totals["fat"] += nutrition.get("fat", 0.0)
            totals["carbohydrates"] += nutrition.get("carbohydrates", 0.0)
            totals["fiber"] += nutrition.get("fiber", 0.0)
        return totals
