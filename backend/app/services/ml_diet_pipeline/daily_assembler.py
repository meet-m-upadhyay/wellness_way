"""
Daily Assembler - Portion calculation and meal distribution
"""

from __future__ import annotations

import logging
from typing import Dict, List, Any
from app.models.food_items import FoodItem

logger = logging.getLogger(__name__)


class DailyAssembler:
    """Calculates ingredient quantities and distributes them into meals"""

    def __init__(self):
        """Initialize daily assembler"""
        logger.info("[DAILY_ASSEMBLER_INIT] Initialized dynamic daily assembler")

    def assemble_day(
        self,
        portfolio: Dict[str, List[FoodItem]],
        target_calories: float,
        target_protein: float,
        meals_per_day: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Calculates portions for the portfolio and splits into meals.
        
        Args:
            portfolio: Discovered ingredients portfolio
            target_calories: Total calories for the day
            target_protein: Total protein for the day
            meals_per_day: How many meals to split into
            
        Returns:
            List of meal dictionaries
        """
        logger.info(
            f"[ASSEMBLER_START] target_cal={target_calories} target_prot={target_protein} "
            f"meals={meals_per_day}"
        )
        
        meals = []
        for i in range(meals_per_day):
            meal_target_cal = target_calories / meals_per_day
            meal_target_prot = target_protein / meals_per_day
            
            # 1. Select specific ingredients for THIS meal
            # Use modulo to cycle through available portfolio ingredients
            main_protein = portfolio["protein"][i % len(portfolio["protein"])]
            main_starch = portfolio["starch"][i % len(portfolio["starch"])]
            main_fat = portfolio["fat"][i % len(portfolio["fat"])]
            
            # Pick a subset of vegetables for this meal
            meal_veggies = [portfolio["vegetables"][(i + j) % len(portfolio["vegetables"])] for j in range(min(2, len(portfolio["vegetables"])))]
            
            meal_quantity_map = {}
            
            # STEP A: Protein targeting
            protein_per_100g = main_protein.macros.get("protein", 8) 
            protein_source_grams = (meal_target_prot / (protein_per_100g or 1)) * 100
            protein_source_grams = max(50, min(300, protein_source_grams))
            meal_quantity_map[main_protein] = protein_source_grams
            
            # STEP B: Fixed Veggie Volumes
            for veg in meal_veggies:
                meal_quantity_map[veg] = 100.0 # 100g per selected veg
                
            # STEP C: Initial Starch/Fat estimates
            current_cal = sum((qty / 100) * item.macros.get("calories", 0) for item, qty in meal_quantity_map.items())
            remaining_cal = meal_target_cal - current_cal
            
            starch_per_100g = main_starch.macros.get("calories", 300) or 100
            starch_grams = (remaining_cal * 0.7 / starch_per_100g) * 100 
            starch_grams = max(30, min(300, starch_grams))
            meal_quantity_map[main_starch] = starch_grams
            
            current_cal = sum((qty / 100) * item.macros.get("calories", 0) for item, qty in meal_quantity_map.items())
            remaining_cal = max(0, meal_target_cal - current_cal)
            
            fat_per_100g = main_fat.macros.get("calories", 800) or 100
            fat_grams = (remaining_cal / fat_per_100g) * 100
            fat_grams = max(5, min(50, fat_grams))
            meal_quantity_map[main_fat] = fat_grams

            # STEP D: Final scaling pass to hit calorie target exactly
            current_meal_cal = sum((qty / 100) * item.macros.get("calories", 0) for item, qty in meal_quantity_map.items())
            
            if current_meal_cal > 0 and abs(current_meal_cal - meal_target_cal) > 20:
                scale_factor = meal_target_cal / current_meal_cal
                meal_quantity_map[main_starch] *= scale_factor
                meal_quantity_map[main_fat] *= scale_factor
                meal_quantity_map[main_starch] = min(600, meal_quantity_map[main_starch])

            # 2. Build the Meal Object
            meal_ingredients = []
            meal_macros = {"calories": 0.0, "protein": 0.0, "carbohydrates": 0.0, "fat": 0.0}
            
            for item, grams in meal_quantity_map.items():
                factor = grams / 100.0
                item_macros = {
                    k: (v * factor if isinstance(v, (int, float)) else v)
                    for k, v in item.macros.items()
                }
                
                meal_ingredients.append({
                    "id": str(item.id),
                    "name": item.canonical_name,
                    "quantity": grams,
                    "unit": "g",
                    "nutrition": item_macros
                })
                
                for k in meal_macros:
                    meal_macros[k] += item_macros.get(k, 0)

            meals.append({
                "meal_index": i + 1,
                "type": self._get_meal_type(i, meals_per_day),
                "ingredients": meal_ingredients,
                "nutrition": meal_macros
            })
            
        return meals

    def _get_meal_type(self, index: int, total: int) -> str:
        if total == 3:
            return ["breakfast", "lunch", "dinner"][index]
        return f"meal_{index + 1}"

def get_daily_assembler() -> DailyAssembler:
    """Get singleton instance"""
    return DailyAssembler()
