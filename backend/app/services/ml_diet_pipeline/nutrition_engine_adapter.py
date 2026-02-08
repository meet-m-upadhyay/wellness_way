"""
Nutrition Engine Adapter - Reuses existing nutrition calculation logic

This module adapts the existing nutrition engine for use in the ML pipeline.
NO GenAI involvement - pure deterministic nutrition calculations.

CRITICAL RULES:
- Reuse existing nutrition database
- NO AI calls
- Deterministic calculations only
- Handle ingredient resolution failures gracefully
"""

import logging
from typing import Dict, List, Any, Optional

from app.services.nutrition_database import get_nutrition_database
from app.services.ingredient_resolution_service import get_ingredient_resolution_service

logger = logging.getLogger(__name__)


class NutritionEngineAdapter:
    """Adapter for existing nutrition engine - deterministic calculations only"""
    
    def __init__(self):
        """Initialize nutrition engine adapter"""
        self.nutrition_db = get_nutrition_database()
        self.resolution_service = get_ingredient_resolution_service()
        logger.info("[NUTRITION_ADAPTER_INIT] Initialized nutrition engine adapter")
    
    def calculate_ingredient_nutrition(
        self,
        ingredient_name: str,
        quantity: float,
        unit: str
    ) -> Dict[str, Any]:
        """
        Calculate nutrition for a single ingredient.
        
        Args:
            ingredient_name: Canonical ingredient name
            quantity: Quantity value
            unit: Unit of measurement
            
        Returns:
            Dict with nutrition data
            
        Raises:
            ValueError: If ingredient not found or calculation fails
        """
        request_id = f"nutr_{ingredient_name[:20]}"
        logger.info(
            f"[NUTRITION_CALC_START] request_id={request_id} "
            f"ingredient='{ingredient_name}' quantity={quantity} unit={unit}"
        )
        
        try:
            # Convert to grams if needed (nutrition DB expects grams)
            if unit.lower() != 'g':
                # For now, assume grams. TODO: Add unit conversion
                logger.warning(f"[NUTRITION_CALC_WARNING] Non-gram unit '{unit}' - assuming grams")
            
            # Look up ingredient in nutrition database
            nutrition_data = self.nutrition_db.get_nutrition(
                food_name=ingredient_name,
                weight_g=quantity
            )
            
            if not nutrition_data:
                logger.error(
                    f"[NUTRITION_CALC_FAILED] request_id={request_id} "
                    f"ingredient='{ingredient_name}' not found in database"
                )
                raise ValueError(f"Ingredient '{ingredient_name}' not found in nutrition database")
            
            # Convert NutritionData to dict
            nutrition_dict = {
                "calories": nutrition_data.calories,
                "protein": nutrition_data.protein,
                "carbohydrates": nutrition_data.carbohydrates,
                "fat": nutrition_data.fat,
                "fiber": nutrition_data.fiber
            }
            
            logger.info(
                f"[NUTRITION_CALC_SUCCESS] request_id={request_id} "
                f"calories={nutrition_dict['calories']:.1f}"
            )
            
            return nutrition_dict
            
        except Exception as e:
            logger.error(
                f"[NUTRITION_CALC_ERROR] request_id={request_id} error={e}"
            )
            raise
    
    def calculate_meal_nutrition(
        self,
        ingredients: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Calculate total nutrition for a meal from ingredients.
        
        Args:
            ingredients: List of ingredient dicts with name, quantity, unit, nutrition
            
        Returns:
            Dict with total nutrition (calories, protein, carbs, fat, fiber)
        """
        logger.info(f"[MEAL_NUTRITION_START] ingredient_count={len(ingredients)}")
        
        totals = {
            "calories": 0.0,
            "protein": 0.0,
            "carbohydrates": 0.0,
            "fat": 0.0,
            "fiber": 0.0
        }
        
        for ingredient in ingredients:
            nutrition = ingredient.get("nutrition", {})
            
            totals["calories"] += nutrition.get("calories", 0.0)
            totals["protein"] += nutrition.get("protein", 0.0)
            totals["carbohydrates"] += nutrition.get("carbohydrates", 0.0)
            totals["fat"] += nutrition.get("fat", 0.0)
            totals["fiber"] += nutrition.get("fiber", 0.0)
        
        logger.info(
            f"[MEAL_NUTRITION_COMPLETE] calories={totals['calories']:.1f} "
            f"protein={totals['protein']:.1f}g"
        )
        
        return totals
    
    def calculate_daily_nutrition(
        self,
        meals: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Calculate total nutrition for a day from meals.
        
        Args:
            meals: List of meal dicts with nutrition data
            
        Returns:
            Dict with daily nutrition totals
        """
        logger.info(f"[DAILY_NUTRITION_START] meal_count={len(meals)}")
        
        totals = {
            "calories": 0.0,
            "protein": 0.0,
            "carbohydrates": 0.0,
            "fat": 0.0,
            "fiber": 0.0
        }
        
        for meal in meals:
            nutrition = meal.get("nutrition", {})
            
            totals["calories"] += nutrition.get("calories", 0.0)
            totals["protein"] += nutrition.get("protein", 0.0)
            totals["carbohydrates"] += nutrition.get("carbohydrates", 0.0)
            totals["fat"] += nutrition.get("fat", 0.0)
            totals["fiber"] += nutrition.get("fiber", 0.0)
        
        logger.info(
            f"[DAILY_NUTRITION_COMPLETE] calories={totals['calories']:.1f} "
            f"protein={totals['protein']:.1f}g"
        )
        
        return totals


# Singleton instance
_adapter: Optional[NutritionEngineAdapter] = None


def get_nutrition_engine_adapter() -> NutritionEngineAdapter:
    """Get singleton instance of nutrition engine adapter"""
    global _adapter
    if _adapter is None:
        _adapter = NutritionEngineAdapter()
    return _adapter
