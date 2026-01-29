"""
Quantity Rounding & Humanization Utility

This module provides centralized rounding for all ingredient quantities
before they reach the UI. Ensures human-friendly, practical quantities.

MANDATORY RULES:
1. Solid foods: Round to nearest 5g
2. Seeds/powders: Round to nearest 1g  
3. Liquids: Round to nearest 10ml
4. Discrete items: Whole numbers only
5. No value with more than 1 decimal place may reach UI
"""

import logging
from typing import Dict, List, Any
import math

logger = logging.getLogger(__name__)


class QuantityRounder:
    """
    Centralized quantity rounding for human-friendly portions.
    
    This is the final step before data reaches the UI to ensure
    all quantities are practical and easy to measure.
    """
    
    def __init__(self):
        """Initialize quantity rounder with category mappings"""
        self.seed_powder_keywords = {
            'seed', 'seeds', 'powder', 'flour', 'spice', 'spices',
            'seasoning', 'salt', 'pepper', 'cumin', 'paprika',
            'turmeric', 'cinnamon', 'ginger', 'garlic powder',
            'onion powder', 'nutritional yeast', 'protein powder',
            'chia', 'flax', 'sesame', 'sunflower', 'pumpkin'
        }
        
        self.liquid_keywords = {
            'milk', 'water', 'juice', 'oil', 'vinegar', 'sauce',
            'broth', 'stock', 'cream', 'yogurt', 'kefir',
            'coconut milk', 'almond milk', 'soy milk', 'oat milk'
        }
        
        self.discrete_keywords = {
            'egg', 'eggs', 'banana', 'bananas', 'apple', 'apples',
            'orange', 'oranges', 'tomato', 'tomatoes', 'onion', 'onions',
            'potato', 'potatoes', 'carrot', 'carrots', 'avocado', 'avocados'
        }
    
    def _validate_canonical_immutability(self, plan_data: Dict[str, Any], stage: str):
        """
        CRITICAL: Validate that no non-canonical units exist after canonicalization.
        
        This is intentional - we want the system to crash loudly if violated.
        
        Args:
            plan_data: Plan data to validate
            stage: Current processing stage name
            
        Raises:
            RuntimeError: If canonical unit violation detected
        """
        # Process meals based on plan type
        meals_to_check = []
        if plan_data.get("plan_type") == "weekly":
            for day in plan_data.get("days", []):
                meals_to_check.extend(day.get("meals", []))
        else:
            meals_to_check = plan_data.get("meals", [])
        
        for meal in meals_to_check:
            for ingredient in meal.get("ingredients", []):
                unit = ingredient.get("unit", "")
                name = ingredient.get("name", "unknown")
                
                if unit not in ["g", "scoops"]:
                    logger.critical(
                        "[CANONICAL_VIOLATION]",
                        extra={
                            "ingredient": name,
                            "unit": unit,
                            "stage": stage
                        }
                    )
                    raise RuntimeError(
                        f"CANONICAL UNIT VIOLATION: Ingredient '{name}' has unit '{unit}' in stage '{stage}'. "
                        f"Only 'g' and 'scoops' allowed after canonicalization."
                    )
    
    def round_plan_quantities(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        MANDATORY: Round all quantities in plan before UI return.
        
        This is the final humanization step that ensures all quantities
        are practical and easy to measure in a real kitchen.
        
        CRITICAL: Canonical immutability guard - prevents mutation after unit enforcement.
        
        Args:
            plan_data: Plan data with canonical units (grams)
            
        Returns:
            Plan data with rounded, human-friendly quantities
            
        Raises:
            RuntimeError: If canonical unit violation detected
        """
        # CRITICAL: Canonical immutability guard
        if plan_data.get("_canonicalized"):
            self._validate_canonical_immutability(plan_data, "quantity_rounding")
        
        logger.info(" ROUNDING QUANTITIES - Final Humanization Step")
        
        rounded_plan = plan_data.copy()
        
        # Process based on plan type
        if plan_data.get("plan_type") == "weekly":
            for day in rounded_plan.get("days", []):
                day["meals"] = self._round_meals_quantities(day.get("meals", []))
                # Recalculate daily totals after rounding
                day["daily_totals"] = self._recalculate_daily_totals(day["meals"])
            
            # Recalculate weekly totals
            if "days" in rounded_plan:
                rounded_plan["weekly_totals"] = self._recalculate_weekly_totals(rounded_plan["days"])
        
        elif plan_data.get("plan_type") == "daily":
            rounded_plan["meals"] = self._round_meals_quantities(rounded_plan.get("meals", []))
            # Recalculate daily totals after rounding
            rounded_plan["daily_totals"] = self._recalculate_daily_totals(rounded_plan["meals"])
        
        logger.info(" QUANTITIES ROUNDED - All values human-friendly")
        return rounded_plan
    
    def _round_meals_quantities(self, meals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Round quantities for all meals"""
        rounded_meals = []
        
        for meal in meals:
            rounded_meal = meal.copy()
            rounded_meal["ingredients"] = self._round_ingredients_quantities(
                meal.get("ingredients", [])
            )
            # Recalculate meal nutrition after rounding
            rounded_meal["nutrition"] = self._recalculate_meal_nutrition(rounded_meal["ingredients"])
            rounded_meals.append(rounded_meal)
        
        return rounded_meals
    
    def _round_ingredients_quantities(self, ingredients: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Round quantities for all ingredients"""
        rounded_ingredients = []
        
        for ingredient in ingredients:
            rounded_ingredient = self._round_single_ingredient(ingredient)
            rounded_ingredients.append(rounded_ingredient)
        
        return rounded_ingredients
    
    def _round_single_ingredient(self, ingredient: Dict[str, Any]) -> Dict[str, Any]:
        """
        Round a single ingredient quantity based on category.
        
        MANDATORY ROUNDING RULES (FINAL OUTPUT GATE):
        1. Solid foods: Round to nearest 5g (NO DECIMALS)
        2. Seeds/powders: Round to nearest 1g (NO DECIMALS) 
        3. Liquids: Round to nearest 10ml (NO DECIMALS)
        4. Discrete items: Whole numbers only (NO DECIMALS)
        5. Protein powder: Whole scoops only (SPECIAL CASE)
        
        HARD RULE: No quantity with more than 0 decimal places reaches UI
        """
        name = ingredient.get("name", "").lower()
        quantity = ingredient.get("quantity", 0)
        unit = ingredient.get("unit", "g")
        
        # SPECIAL CASE: Protein powder (already handled in unit enforcement)
        if unit == "scoops" or self._is_protein_powder_ingredient(name):
            # Protein powder should already be whole scoops from unit enforcement
            rounded_quantity = max(1, int(round(quantity)))
            return {
                **ingredient,
                "quantity": rounded_quantity,
                "unit": "scoops",
                "rounding_applied": True
            }
        
        # Determine ingredient category
        category = self._categorize_ingredient(name, unit)
        
        # Apply category-specific rounding (ALL INTEGERS)
        if category == "discrete":
            # Discrete items: whole numbers only
            rounded_quantity = max(1, int(round(quantity)))
            
        elif category == "seed_powder":
            # Seeds/powders: round to nearest 1g (INTEGER)
            rounded_quantity = max(1, int(round(quantity)))
            
        elif category == "liquid":
            # CRITICAL FIX: After canonicalization, all liquids are in grams
            # Do NOT convert back to ml - this violates canonical immutability
            # Liquids: round to nearest 10g (INTEGER) - treat as solid after canonicalization
            rounded_quantity = max(10, int(self._round_to_nearest(quantity, 10)))
            
        else:
            # Solid foods: round to nearest 5g (INTEGER)
            rounded_quantity = max(5, int(self._round_to_nearest(quantity, 5)))
        
        # FINAL OUTPUT GATE: Ensure NO DECIMALS
        if isinstance(rounded_quantity, float):
            rounded_quantity = int(rounded_quantity)
        
        # Validate no decimals leaked through
        if not isinstance(rounded_quantity, int):
            raise ValueError(f"CRITICAL: Decimal leaked to UI: {rounded_quantity}")
        
        # Log significant changes
        if abs(quantity - rounded_quantity) / max(quantity, 1) > 0.2:  # >20% change
            logger.info(f"Significant rounding: {name} {quantity}g -> {rounded_quantity}g")
        
        return {
            **ingredient,
            "quantity": rounded_quantity,
            "unit": unit,
            "original_quantity": quantity,  # Keep for nutrition recalculation
            "rounding_applied": True
        }
    
    def _is_protein_powder_ingredient(self, name: str) -> bool:
        """Check if ingredient name indicates protein powder"""
        protein_powder_indicators = [
            'protein powder', 'whey protein', 'casein protein', 'plant protein',
            'pea protein', 'soy protein', 'hemp protein', 'rice protein'
        ]
        return any(indicator in name for indicator in protein_powder_indicators)
    
    def _categorize_ingredient(self, name: str, unit: str) -> str:
        """Categorize ingredient for appropriate rounding"""
        name_lower = name.lower()
        
        # Check for discrete items first
        if any(keyword in name_lower for keyword in self.discrete_keywords):
            return "discrete"
        
        # Check for seeds/powders
        if any(keyword in name_lower for keyword in self.seed_powder_keywords):
            return "seed_powder"
        
        # Check for liquids
        if any(keyword in name_lower for keyword in self.liquid_keywords):
            return "liquid"
        
        # Check unit hints
        if unit in ["ml", "milliliter", "milliliters", "l", "liter", "liters"]:
            return "liquid"
        
        # Default to solid food
        return "solid"
    
    def _round_to_nearest(self, value: float, nearest: int) -> float:
        """Round value to nearest specified increment"""
        return round(value / nearest) * nearest
    
    def _recalculate_meal_nutrition(self, ingredients: List[Dict[str, Any]]) -> Dict[str, float]:
        """Recalculate meal nutrition after quantity rounding"""
        totals = {
            "calories": 0.0,
            "protein": 0.0,
            "carbohydrates": 0.0,
            "fat": 0.0,
            "fiber": 0.0,
            "sodium": 0.0
        }
        
        for ingredient in ingredients:
            # Get original and new quantities
            original_quantity = ingredient.get("original_quantity", ingredient.get("quantity", 0))
            new_quantity = ingredient.get("quantity", 0)
            
            # Calculate scaling factor
            if original_quantity > 0:
                scale_factor = new_quantity / original_quantity
            else:
                scale_factor = 1.0
            
            # Scale nutrition proportionally
            original_nutrition = ingredient.get("nutrition", {})
            for nutrient in totals:
                original_value = original_nutrition.get(nutrient, 0)
                scaled_value = original_value * scale_factor
                totals[nutrient] += scaled_value
        
        # Round nutrition values to 1 decimal place
        return {k: round(v, 1) for k, v in totals.items()}
    
    def _recalculate_daily_totals(self, meals: List[Dict[str, Any]]) -> Dict[str, float]:
        """Recalculate daily totals after meal rounding"""
        totals = {
            "calories": 0.0,
            "protein": 0.0,
            "carbohydrates": 0.0,
            "fat": 0.0,
            "fiber": 0.0,
            "sodium": 0.0
        }
        
        for meal in meals:
            meal_nutrition = meal.get("nutrition", {})
            for nutrient in totals:
                totals[nutrient] += meal_nutrition.get(nutrient, 0)
        
        return {k: round(v, 1) for k, v in totals.items()}
    
    def _recalculate_weekly_totals(self, days: List[Dict[str, Any]]) -> Dict[str, float]:
        """Recalculate weekly totals after daily rounding"""
        totals = {
            "calories": 0.0,
            "protein": 0.0,
            "carbohydrates": 0.0,
            "fat": 0.0,
            "fiber": 0.0,
            "sodium": 0.0
        }
        
        for day in days:
            daily_totals = day.get("daily_totals", {})
            for nutrient in totals:
                totals[nutrient] += daily_totals.get(nutrient, 0)
        
        return {k: round(v, 1) for k, v in totals.items()}


# Global quantity rounder instance
_quantity_rounder = None

def get_quantity_rounder() -> QuantityRounder:
    """Get the global quantity rounder instance"""
    global _quantity_rounder
    if _quantity_rounder is None:
        _quantity_rounder = QuantityRounder()
    return _quantity_rounder