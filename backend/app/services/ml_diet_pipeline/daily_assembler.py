"""
Daily Assembler - Portion calculation and meal distribution
"""

from __future__ import annotations

import logging
from typing import Dict, List, Any
from app.models.food_items import FoodItem
from app.services.ml_diet_pipeline.meal_templates import get_template_registry

logger = logging.getLogger(__name__)


class DailyAssembler:
    """Calculates ingredient quantities and distributes them into meals"""

    def __init__(self):
        """Initialize daily assembler"""
        self.template_registry = get_template_registry()
        logger.info("[DAILY_ASSEMBLER_INIT] Initialized dynamic daily assembler with templates")

    def assemble_day(
        self,
        portfolio: Dict[str, List[FoodItem]],
        target_calories: float,
        target_protein: float,
        primary_goal: str = "maintain",
        meals_per_day: int = 3,
        cuisine: str = "indian",
        diet_type: str = None,
    ) -> List[Dict[str, Any]]:
        """
        Calculates portions using a Multi-Stage Protien-First Scaler.
        """
        logger.info(
            f"[ASSEMBLER_START] target_cal={target_calories} target_prot={target_protein} "
            f"goal={primary_goal} meals={meals_per_day} cuisine={cuisine}"
        )
        
        meals = []
        for i in range(meals_per_day):
            meal_target_cal = target_calories / meals_per_day
            meal_target_prot = target_protein / meals_per_day
            
            meal_type = self._get_meal_type(i, meals_per_day)
            
            # Fetch a culinary archetype for this meal slot
            template = self.template_registry.get_template(cuisine, meal_type)
            template_components = template.get("components", {})
            
            # 1. Picking Ingredients matching the culinary archetype
            main_protein = self.template_registry.select_best_ingredient(portfolio.get("protein", []), template_components.get("protein", []), diet_type=diet_type)
            main_starch = self.template_registry.select_best_ingredient(portfolio.get("starch", []), template_components.get("starch", []), diet_type=diet_type)
            main_fat = self.template_registry.select_best_ingredient(portfolio.get("fat", []), template_components.get("fat", []), diet_type=diet_type)

            # For vegetables/fruits category, we pick up to two matching ones
            meal_veggies = []
            available_veggies = portfolio.get("vegetables", [])
            for _ in range(min(2, len(available_veggies))):
                veg = self.template_registry.select_best_ingredient(available_veggies, template_components.get("vegetables", []), diet_type=diet_type)
                # Deduplicate based on object canonical_name to prevent inserting identical duplicated elements
                if veg and not any(v.canonical_name == veg.canonical_name for v in meal_veggies):
                    meal_veggies.append(veg)
            
            meal_quantity_map = {}
            
            # STAGE 1: Lock Protein Grams
            if main_protein:
                protein_per_100g = main_protein.macros.get("protein", 8) or 1
                # We need meal_target_prot from this source
                # Note: This source also adds calories
                protein_grams = (meal_target_prot / protein_per_100g) * 100
                
                # Goal-based capping for protein
                max_p = 400 if primary_goal == "muscle gain" else 300
                protein_grams = max(80, min(max_p, protein_grams))
                meal_quantity_map[main_protein] = protein_grams
            
            # STAGE 2: Add Fixed Volume Veggies (Low Calorie Fillers)
            for veg in meal_veggies:
                meal_quantity_map[veg] = 120.0 # Standard portion for wellness
                
            # STAGE 3: Calculate Remaining Calorie Gap
            current_cal = sum((qty / 100) * item.macros.get("calories", 0) for item, qty in meal_quantity_map.items())
            remaining_cal = meal_target_cal - current_cal
            
            # STAGE 4: Fill Gap with Starch and Fat (Non-Protein sources)
            if remaining_cal > 0:
                if main_starch and main_fat:
                    # 70/30 split between starch and fat for the gap
                    starch_cal = remaining_cal * 0.75
                    fat_cal = remaining_cal * 0.25
                    
                    starch_per_100g = main_starch.macros.get("calories", 300) or 100
                    fat_per_100g = main_fat.macros.get("calories", 800) or 100
                    
                    meal_quantity_map[main_starch] = (starch_cal / starch_per_100g) * 100
                    meal_quantity_map[main_fat] = (fat_cal / fat_per_100g) * 100
                elif main_starch:
                    starch_per_100g = main_starch.macros.get("calories", 300) or 100
                    meal_quantity_map[main_starch] = (remaining_cal / starch_per_100g) * 100
                elif main_fat:
                    fat_per_100g = main_fat.macros.get("calories", 800) or 100
                    meal_quantity_map[main_fat] = (remaining_cal / fat_per_100g) * 100
            
            # STAGE 5: Sanitization & Goal-Based Adjustments
            # If Fat Loss and we overshot calories, scale down ONLY starch and fat
            final_meal_cal = sum((qty / 100) * item.macros.get("calories", 0) for item, qty in meal_quantity_map.items())
            
            if final_meal_cal > meal_target_cal + 50:
                scale_factor = meal_target_cal / final_meal_cal
                if primary_goal == "fat loss":
                    # Lean optimization: Reduce starch/fat first before protein
                    if main_starch in meal_quantity_map: meal_quantity_map[main_starch] *= (scale_factor * 0.8)
                    if main_fat in meal_quantity_map: meal_quantity_map[main_fat] *= (scale_factor * 0.8)
                else:
                    for k in meal_quantity_map:
                        meal_quantity_map[k] *= scale_factor

            # 2. Build Final Meal Objects
            meal_ingredients = []
            meal_macros = {"calories": 0.0, "protein": 0.0, "carbohydrates": 0.0, "fat": 0.0}
            
            for item, grams in meal_quantity_map.items():
                factor = grams / 100.0
                macros = item.macros or {}
                item_macros = {k: (v * factor if isinstance(v, (int, float)) else v) for k, v in macros.items()}
                
                meal_ingredients.append({
                    "id": str(item.id),
                    "name": item.canonical_name,
                    "quantity": round(grams, 1),
                    "unit": "g",
                    "nutrition": item_macros
                })
                for k in meal_macros:
                    meal_macros[k] += item_macros.get(k, 0)

            archetype_name = template["name"]
            if "{" in archetype_name:
                archetype_name = archetype_name.format(
                    starch=main_starch.canonical_name if main_starch else "Starch",
                    protein=main_protein.canonical_name if main_protein else "Protein"
                )

            meals.append({
                "meal_index": i + 1,
                "type": meal_type,
                "archetype": archetype_name,
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

