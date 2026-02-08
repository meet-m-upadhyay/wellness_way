"""
Scaling Engine - Deterministic portion scaling

This module handles deterministic scaling of meal portions to meet targets.
NO GenAI involvement - pure mathematical scaling.

CRITICAL RULES:
- Math-only scaling
- Accept imperfect results (soft acceptance)
- NO AI retries
- Once a meal is created → NO AI RETRY EVER
"""

import logging
from typing import Dict, List, Any, Optional
from copy import deepcopy

logger = logging.getLogger(__name__)


class ScalingEngine:
    """Deterministic portion scaling engine"""
    
    # Scaling limits to keep portions realistic
    MIN_SCALE_FACTOR = 0.5  # Don't scale below 50%
    MAX_SCALE_FACTOR = 2.0  # Don't scale above 200%
    
    # Acceptable deviation from target (soft acceptance)
    CALORIE_TOLERANCE = 0.15  # ±15%
    PROTEIN_TOLERANCE = 0.10  # ±10%
    
    def __init__(self):
        """Initialize scaling engine"""
        logger.info("[SCALING_ENGINE_INIT] Initialized deterministic scaling engine")
    
    def scale_meal_to_target(
        self,
        meal: Dict[str, Any],
        target_calories: float,
        target_protein: float,
        priority: str = "balanced"
    ) -> Dict[str, Any]:
        """
        Scale meal portions to meet calorie and protein targets.
        
        Args:
            meal: Meal dict with ingredients and nutrition
            target_calories: Target calories for the meal
            target_protein: Target protein for the meal
            priority: Scaling priority ("calories", "protein", or "balanced")
            
        Returns:
            Scaled meal dict
        """
        request_id = f"scale_{meal.get('name', 'unknown')[:20]}"
        logger.info(
            f"[SCALING_START] request_id={request_id} "
            f"target_cal={target_calories:.0f} target_prot={target_protein:.1f}g "
            f"priority={priority}"
        )
        
        # Get current nutrition
        current_nutrition = meal.get("nutrition", {})
        current_calories = current_nutrition.get("calories", 0)
        current_protein = current_nutrition.get("protein", 0)
        
        if current_calories == 0:
            logger.error(f"[SCALING_ERROR] request_id={request_id} Zero calorie meal cannot be scaled")
            return meal  # Return unscaled
        
        # Calculate scale factors
        calorie_scale = target_calories / current_calories
        protein_scale = target_protein / current_protein if current_protein > 0 else 1.0
        
        # Choose scale factor based on priority
        if priority == "calories":
            scale_factor = calorie_scale
        elif priority == "protein":
            scale_factor = protein_scale
        else:  # balanced
            # Use average of both, weighted toward calories
            scale_factor = (calorie_scale * 0.6) + (protein_scale * 0.4)
        
        # Clamp scale factor to realistic limits
        original_scale = scale_factor
        scale_factor = max(self.MIN_SCALE_FACTOR, min(self.MAX_SCALE_FACTOR, scale_factor))
        
        if original_scale != scale_factor:
            logger.warning(
                f"[SCALING_CLAMPED] request_id={request_id} "
                f"original={original_scale:.2f} clamped={scale_factor:.2f}"
            )
        
        # Scale the meal
        scaled_meal = self._apply_scale_factor(meal, scale_factor)
        
        # Log results
        scaled_nutrition = scaled_meal.get("nutrition", {})
        scaled_calories = scaled_nutrition.get("calories", 0)
        scaled_protein = scaled_nutrition.get("protein", 0)
        
        calorie_diff = scaled_calories - target_calories
        protein_diff = scaled_protein - target_protein
        
        logger.info(
            f"[SCALING_APPLIED] request_id={request_id} "
            f"scale_factor={scale_factor:.2f} "
            f"cal={scaled_calories:.0f} (Δ{calorie_diff:+.0f}) "
            f"prot={scaled_protein:.1f}g (Δ{protein_diff:+.1f}g)"
        )
        
        # Check if result is acceptable (soft acceptance)
        calorie_within_tolerance = abs(calorie_diff) <= target_calories * self.CALORIE_TOLERANCE
        protein_within_tolerance = abs(protein_diff) <= target_protein * self.PROTEIN_TOLERANCE
        
        if not (calorie_within_tolerance and protein_within_tolerance):
            logger.warning(
                f"[SCALING_INSUFFICIENT_ACCEPTED] request_id={request_id} "
                f"Outside tolerance but accepted (soft acceptance)"
            )
        
        return scaled_meal
    
    def _apply_scale_factor(
        self,
        meal: Dict[str, Any],
        scale_factor: float
    ) -> Dict[str, Any]:
        """
        Apply scale factor to all meal components.
        
        Args:
            meal: Original meal dict
            scale_factor: Scale factor to apply
            
        Returns:
            Scaled meal dict
        """
        scaled_meal = deepcopy(meal)
        
        # Scale ingredients
        if "ingredients" in scaled_meal:
            for ingredient in scaled_meal["ingredients"]:
                if "quantity" in ingredient:
                    ingredient["quantity"] *= scale_factor
                
                # Scale ingredient nutrition if present
                if "nutrition" in ingredient:
                    for key in ingredient["nutrition"]:
                        if isinstance(ingredient["nutrition"][key], (int, float)):
                            ingredient["nutrition"][key] *= scale_factor
        
        # Scale meal nutrition
        if "nutrition" in scaled_meal:
            for key in scaled_meal["nutrition"]:
                if isinstance(scaled_meal["nutrition"][key], (int, float)):
                    scaled_meal["nutrition"][key] *= scale_factor
        
        return scaled_meal
    
    def scale_day_to_target(
        self,
        meals: List[Dict[str, Any]],
        target_daily_calories: float,
        target_daily_protein: float
    ) -> List[Dict[str, Any]]:
        """
        Scale all meals in a day to meet daily targets.
        
        Args:
            meals: List of meal dicts
            target_daily_calories: Target daily calories
            target_daily_protein: Target daily protein
            
        Returns:
            List of scaled meal dicts
        """
        logger.info(
            f"[DAY_SCALING_START] meal_count={len(meals)} "
            f"target_cal={target_daily_calories:.0f} target_prot={target_daily_protein:.1f}g"
        )
        
        # Calculate current totals
        current_calories = sum(m.get("nutrition", {}).get("calories", 0) for m in meals)
        current_protein = sum(m.get("nutrition", {}).get("protein", 0) for m in meals)
        
        if current_calories == 0:
            logger.error("[DAY_SCALING_ERROR] Zero calorie day cannot be scaled")
            return meals  # Return unscaled
        
        # Calculate global scale factor
        calorie_scale = target_daily_calories / current_calories
        protein_scale = target_daily_protein / current_protein if current_protein > 0 else 1.0
        
        # Use balanced approach
        global_scale = (calorie_scale * 0.6) + (protein_scale * 0.4)
        
        # Clamp to realistic limits
        global_scale = max(self.MIN_SCALE_FACTOR, min(self.MAX_SCALE_FACTOR, global_scale))
        
        logger.info(f"[DAY_SCALING_FACTOR] global_scale={global_scale:.2f}")
        
        # Apply scale to all meals
        scaled_meals = []
        for meal in meals:
            scaled_meal = self._apply_scale_factor(meal, global_scale)
            scaled_meals.append(scaled_meal)
        
        # Calculate final totals
        final_calories = sum(m.get("nutrition", {}).get("calories", 0) for m in scaled_meals)
        final_protein = sum(m.get("nutrition", {}).get("protein", 0) for m in scaled_meals)
        
        logger.info(
            f"[DAY_SCALING_COMPLETE] "
            f"cal={final_calories:.0f} (target={target_daily_calories:.0f}) "
            f"prot={final_protein:.1f}g (target={target_daily_protein:.1f}g)"
        )
        
        return scaled_meals


# Singleton instance
_engine: Optional[ScalingEngine] = None


def get_scaling_engine() -> ScalingEngine:
    """Get singleton instance of scaling engine"""
    global _engine
    if _engine is None:
        _engine = ScalingEngine()
    return _engine
