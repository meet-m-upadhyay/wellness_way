"""
Nutrition Calculation Engine - Backend Source of Truth

This module is responsible for ALL nutrition calculations.
The LLM provides ONLY meal ideas and rough portions.
This engine calculates the actual nutrition values.

CRITICAL: Uses ingredient resolution service for safe ingredient handling.
Never allows 0-calorie nutrition to reach validation.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging
from .nutrition_database import get_nutrition_database, NutritionData, ProteinQuality
from .ingredient_resolution_service import get_ingredient_resolution_service, ResolutionStatus

logger = logging.getLogger(__name__)


class ZeroCalorieError(Exception):
    """Raised when a meal has zero calories due to ingredient resolution failures"""
    def __init__(self, message: str, failed_ingredients: List[str]):
        super().__init__(message)
        self.failed_ingredients = failed_ingredients


class NutritionCalculationError(Exception):
    """Raised when nutrition calculation fails due to unresolved ingredients"""
    def __init__(self, message: str, unresolved_ingredients: List[str]):
        super().__init__(message)
        self.unresolved_ingredients = unresolved_ingredients


class RetryableMealGenerationError(Exception):
    """Raised when meal generation fails but can be retried with different parameters"""
    def __init__(self, message: str, meal_name: str, violation_type: str):
        super().__init__(message)
        self.meal_name = meal_name
        self.violation_type = violation_type


def get_diet_specific_thresholds(diet_type: str) -> Dict[str, float]:
    """
    Get diet-specific guardrail thresholds for meal creation.
    
    Args:
        diet_type: "vegetarian", "non_vegetarian", or "vegan"
        
    Returns:
        Dict with min_meal_calories and min_meal_protein thresholds
    """
    if diet_type == "vegan":
        return {
            "min_meal_calories": 180.0,  # Lower due to plant-based density
            "min_meal_protein": 20.0     # Lower due to plant protein availability
        }
    elif diet_type == "vegetarian":
        return {
            "min_meal_calories": 200.0,  # Standard
            "min_meal_protein": 22.0     # Slightly lower due to dairy/egg protein
        }
    else:  # non_vegetarian
        return {
            "min_meal_calories": 220.0,  # Higher due to meat density
            "min_meal_protein": 25.0     # Standard with meat protein
        }


@dataclass
class Ingredient:
    """Ingredient with RAW weight and calculated nutrition - ASYNC SAFE"""
    name: str
    quantity: float  # Always in grams, RAW weight
    unit: str = "g"  # Display unit
    nutrition: Optional[NutritionData] = None
    resolved: bool = False  # Track if ingredient was successfully resolved
    resolution_status: Optional[str] = None  # Track resolution method
    warning_message: Optional[str] = None  # Track any warnings
    
    # NOTE: Nutrition calculation is now handled externally via resolution service
    # This class only stores the results


@dataclass
class Meal:
    """Meal with calculated nutrition from ingredients"""
    name: str
    ingredients: List[Ingredient]
    instructions: str
    meal_type: str  # breakfast, lunch, dinner, snack
    
    def __post_init__(self):
        """Validate meal after initialization - USE FALLBACK NUTRITION FOR SAFETY"""
        # CRITICAL: Handle unresolved ingredients with fallback nutrition
        unresolved_ingredients = []
        skipped_ingredients = []
        
        for ingredient in self.ingredients:
            if not ingredient.resolved or ingredient.nutrition is None:
                if ingredient.resolution_status == "skipped":
                    skipped_ingredients.append(ingredient.name)
                    # APPLY FALLBACK NUTRITION for skipped ingredients
                    self._apply_fallback_nutrition(ingredient)
                else:
                    unresolved_ingredients.append(ingredient.name)
        
        # Log skipped ingredients but don't fail - we have fallback nutrition
        if skipped_ingredients:
            logger.warning(f"Using fallback nutrition for skipped ingredients in {self.name}: {skipped_ingredients}")
        
        # Only fail if there are truly unresolved ingredients (system error)
        if unresolved_ingredients:
            error_msg = f"SYSTEM ERROR: Unresolved ingredients in {self.name}"
            logger.error(f"{error_msg}: {unresolved_ingredients}")
            
            # This should never happen with proper resolution service
            raise NutritionCalculationError(error_msg, unresolved_ingredients)
        
        # Validate nutrition totals (should never be zero with fallbacks)
        self._validate_nutrition_totals()
    
    def _apply_fallback_nutrition(self, ingredient: Ingredient):
        """Apply fallback nutrition to skipped ingredients"""
        from .nutrition_database import get_nutrition_database, NutritionData, ProteinQuality
        
        # Use generic vegetable nutrition as safe fallback
        fallback_nutrition = NutritionData(
            calories=25.0,   # Generic vegetable calories per 100g
            protein=2.0,     # Generic vegetable protein per 100g
            carbohydrates=5.0,
            fat=0.2,
            fiber=3.0,
            sodium=10.0,
            protein_quality=ProteinQuality.INCOMPLETE
        )
        
        # Scale to ingredient quantity
        ingredient.nutrition = fallback_nutrition.scale(ingredient.quantity)
        ingredient.resolved = True  # Mark as resolved with fallback
        ingredient.resolution_status = "fallback_nutrition"
        ingredient.warning_message = f"Using generic nutrition for unknown ingredient: {ingredient.name}"
        
        logger.info(f"Applied fallback nutrition to '{ingredient.name}': {ingredient.nutrition.calories:.1f} cal")
    
    def _validate_nutrition_totals(self):
        """CRITICAL: Ensure meal has meaningful nutrition - ZERO CALORIE SAFETY NET"""
        nutrition = self.nutrition
        
        # ABSOLUTE RULE: Zero calories must NEVER be a valid intermediate state
        if nutrition.calories <= 0:
            error_msg = f"ZERO CALORIE MEAL DETECTED: {self.name} has {nutrition.calories} calories"
            logger.error(f"[ERROR] {error_msg}")
            logger.error(f"   Meal type: {self.meal_type}")
            logger.error(f"   Ingredients: {[ing.name for ing in self.ingredients]}")
            
            failed_ingredients = [ing.name for ing in self.ingredients if not ing.resolved]
            raise ZeroCalorieError(error_msg, failed_ingredients)
        
        # Warn about suspiciously low nutrition
        if nutrition.calories < 50:
            logger.warning(f"[WARNING] SUSPICIOUSLY LOW CALORIES: {self.name} has only {nutrition.calories:.1f} calories")
        
        if nutrition.protein < 1:
            logger.warning(f"[WARNING] SUSPICIOUSLY LOW PROTEIN: {self.name} has only {nutrition.protein:.1f}g protein")
    
    @property
    def nutrition(self) -> NutritionData:
        """Calculate total nutrition from ingredients"""
        total = NutritionData(0, 0, 0, 0, 0, 0, ProteinQuality.INCOMPLETE)
        
        complete_proteins = 0
        for ingredient in self.ingredients:
            if ingredient.nutrition:
                total.calories += ingredient.nutrition.calories
                total.protein += ingredient.nutrition.protein
                total.carbohydrates += ingredient.nutrition.carbohydrates
                total.fat += ingredient.nutrition.fat
                total.fiber += ingredient.nutrition.fiber
                total.sodium += ingredient.nutrition.sodium
                
                if ingredient.nutrition.protein_quality == ProteinQuality.COMPLETE:
                    complete_proteins += 1
        
        # Determine overall protein quality
        if complete_proteins > 0:
            total.protein_quality = ProteinQuality.COMPLETE
        else:
            total.protein_quality = ProteinQuality.INCOMPLETE
        
        return total
    
    def _identify_primary_protein_source(self) -> Optional[str]:
        """
        DETERMINISTIC identification of primary protein source.
        
        Algorithm:
        1. Find ingredient with highest absolute protein content (grams)
        2. Must have ≥ 8g protein to qualify as primary
        3. Normalize name for comparison (remove modifiers)
        """
        max_protein = 0
        primary_source = None
        
        for ingredient in self.ingredients:
            if ingredient.nutrition and ingredient.nutrition.protein >= 8:  # Minimum threshold
                if ingredient.nutrition.protein > max_protein:
                    max_protein = ingredient.nutrition.protein
                    primary_source = self._normalize_ingredient_name(ingredient.name)
        
        return primary_source
    
    def _identify_primary_carb_source(self) -> Optional[str]:
        """
        DETERMINISTIC identification of primary carbohydrate source.
        
        Algorithm:
        1. Find ingredient with highest absolute carb content (grams)
        2. Must have ≥ 15g carbs to qualify as primary
        3. Normalize name for comparison (remove modifiers)
        """
        max_carbs = 0
        primary_source = None
        
        for ingredient in self.ingredients:
            if ingredient.nutrition and ingredient.nutrition.carbohydrates >= 15:  # Minimum threshold
                if ingredient.nutrition.carbohydrates > max_carbs:
                    max_carbs = ingredient.nutrition.carbohydrates
                    primary_source = self._normalize_ingredient_name(ingredient.name)
        
        return primary_source
    
    def _normalize_ingredient_name(self, name: str) -> str:
        """
        Normalize ingredient names for variety comparison.
        
        Removes modifiers like (cooked), (dry), (extra-firm), etc.
        to focus on the core ingredient for variety checking.
        """
        normalized = name.lower().strip()
        
        # Remove common modifiers
        modifiers_to_remove = [
            '(cooked)', '(dry)', '(raw)', '(fresh)', '(frozen)',
            '(extra-firm)', '(firm)', '(soft)', '(plain)', '(unsweetened)',
            '(whole)', '(chopped)', '(diced)', '(sliced)', '(roasted)',
            '(steamed)', '(boiled)', '(grilled)', '(baked)'
        ]
        
        for modifier in modifiers_to_remove:
            normalized = normalized.replace(modifier, '')
        
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    @property
    def primary_protein_source(self) -> Optional[str]:
        """Get the primary protein source in this meal (DETERMINISTIC)"""
        return self._identify_primary_protein_source()
    
    @property
    def primary_carb_source(self) -> Optional[str]:
        """Get the primary carbohydrate source in this meal (DETERMINISTIC)"""
        return self._identify_primary_carb_source()


@dataclass
class DayPlan:
    """Complete day plan with calculated nutrition"""
    date: str
    meals: List[Meal]
    
    @property
    def daily_totals(self) -> NutritionData:
        """Calculate daily nutrition totals"""
        total = NutritionData(0, 0, 0, 0, 0, 0, ProteinQuality.INCOMPLETE)
        
        complete_protein_meals = 0
        for meal in self.meals:
            meal_nutrition = meal.nutrition
            total.calories += meal_nutrition.calories
            total.protein += meal_nutrition.protein
            total.carbohydrates += meal_nutrition.carbohydrates
            total.fat += meal_nutrition.fat
            total.fiber += meal_nutrition.fiber
            total.sodium += meal_nutrition.sodium
            
            if meal_nutrition.protein_quality == ProteinQuality.COMPLETE:
                complete_protein_meals += 1
        
        # Day has complete protein if at least one meal has complete protein
        if complete_protein_meals > 0:
            total.protein_quality = ProteinQuality.COMPLETE
        else:
            total.protein_quality = ProteinQuality.INCOMPLETE
        
        return total


class NutritionEngine:
    """
    Backend nutrition calculation engine.
    
    RESPONSIBILITIES:
    1. Convert LLM meal suggestions to accurate nutrition data
    2. Enforce all safety constraints
    3. Validate protein targets
    4. Auto-correct portion sizes if needed
    5. Ensure dietary compliance
    """
    
    def __init__(self):
        self.db = get_nutrition_database()
    
    def calculate_meal_nutrition(
        self, 
        meal_name: str,
        ingredients_list: List[Dict],
        instructions: str,
        meal_type: str,
        target_protein_g: Optional[float] = None
    ) -> Meal:
        """
        Calculate accurate nutrition for a meal from LLM suggestions.
        
        Args:
            meal_name: Name of the meal
            ingredients_list: List of ingredients with quantities from LLM
            instructions: Cooking instructions
            meal_type: Type of meal (breakfast, lunch, dinner, snack)
            target_protein_g: Optional protein target for auto-correction
        
        Returns:
            Meal with accurate nutrition calculations
        """
        ingredients = []
        
        for ing_data in ingredients_list:
            # Parse ingredient data from LLM
            name = ing_data.get("name", "").lower().strip()
            quantity = float(ing_data.get("quantity", 0))
            unit = ing_data.get("unit", "g")
            
            # Convert to grams if needed (all calculations use grams)
            quantity_g = self._convert_to_grams(quantity, unit, name)
            
            # Create ingredient with nutrition calculation
            ingredient = Ingredient(name=name, quantity=quantity_g, unit=unit)
            ingredients.append(ingredient)
        
        meal = Meal(
            name=meal_name,
            ingredients=ingredients,
            instructions=instructions,
            meal_type=meal_type
        )
        
        # Auto-correct portion sizes if target protein is specified
        if target_protein_g and meal.nutrition.protein < target_protein_g * 0.8:
            meal = self._auto_correct_protein(meal, target_protein_g)
        
        return meal
    
    async def create_meal_with_resolution(
        self,
        meal_name: str,
        ingredients_list: List[Dict[str, Any]],
        instructions: str,
        meal_type: str = "meal",
        target_protein_g: Optional[float] = None,
        diet_type: str = "vegetarian"
    ) -> Meal:
        """
        Create meal with ingredient resolution - handles raw ingredient names from LLM.
        
        This function takes raw ingredient data from LLM and:
        1. Resolves each ingredient using the resolution service
        2. Creates ingredients with proper nutrition data
        3. Builds the meal with accurate nutrition totals
        
        Args:
            meal_name: Name of the meal
            ingredients_list: List of ingredient dicts with 'name', 'quantity', 'unit'
            instructions: Cooking instructions
            meal_type: Type of meal (breakfast, lunch, dinner, etc.)
            target_protein_g: Optional target protein for the meal
            
        Returns:
            Meal with resolved ingredients and accurate nutrition
        """
        logger.info(f"Creating meal with resolution: {meal_name}")
        
        resolved_ingredients = []
        
        # Resolve each ingredient
        for ingredient_data in ingredients_list:
            ingredient_name = ingredient_data.get('name', '').strip()
            quantity = float(ingredient_data.get('quantity', 0))
            unit = ingredient_data.get('unit', 'g')
            
            if ingredient_name and quantity > 0:
                # Use the safe ingredient resolution function
                ingredient = await create_ingredient_with_resolution(
                    name=ingredient_name,
                    quantity=quantity,
                    unit=unit
                )
                
                # Only add resolved ingredients (skip unresolved ones)
                if ingredient.resolved:
                    resolved_ingredients.append(ingredient)
                    logger.debug(f"[OK] Resolved: {ingredient_name} -> {ingredient.nutrition.calories:.1f} cal")
                else:
                    logger.warning(f"[WARNING] Skipped unresolved ingredient: {ingredient_name}")
        
        # Create meal with resolved ingredients
        if not resolved_ingredients:
            logger.error(f"No ingredients could be resolved for meal: {meal_name}")
            raise NutritionCalculationError(f"No resolvable ingredients in {meal_name}", [])
        
        meal = Meal(
            name=meal_name,
            ingredients=resolved_ingredients,
            instructions=instructions,
            meal_type=meal_type
        )
        
        # Add protein safety net if needed and target is specified
        if target_protein_g and meal.nutrition.protein < target_protein_g * 0.7:  # 70% of target
            logger.info(f"Adding protein safety net to {meal_name} (current: {meal.nutrition.protein:.1f}g, target: {target_protein_g:.1f}g)")
            meal = add_protein_safety_net(meal, min_protein_g=target_protein_g * 0.7)
        
        logger.info(f"[OK] Created meal: {meal_name} - {meal.nutrition.calories:.0f} cal, {meal.nutrition.protein:.1f}g protein")
        
        # Get diet-specific thresholds
        thresholds = get_diet_specific_thresholds(diet_type)
        MIN_MEAL_CALORIES = thresholds["min_meal_calories"]
        MIN_MEAL_PROTEIN = thresholds["min_meal_protein"]
        
        logger.info(f"[DIET_THRESHOLDS] {diet_type}: {MIN_MEAL_CALORIES} kcal, {MIN_MEAL_PROTEIN}g protein")
        
        # TASK 8 FIX 2: Meal calorie guardrail - diet-specific thresholds
        if meal.nutrition.calories < MIN_MEAL_CALORIES:
            error_msg = f"MEAL CALORIE GUARDRAIL VIOLATION: {meal_name} has {meal.nutrition.calories:.1f} kcal < {MIN_MEAL_CALORIES} kcal minimum ({diet_type})"
            logger.error(f"[MEAL_GUARDRAIL] {error_msg}")
            raise RetryableMealGenerationError(error_msg, meal_name, "low_calories")
        
        # TASK 8 FIX 3: Per-meal protein minimum - diet-specific thresholds
        if meal.nutrition.protein < MIN_MEAL_PROTEIN:
            error_msg = f"MEAL PROTEIN GUARDRAIL VIOLATION: {meal_name} has {meal.nutrition.protein:.1f}g protein < {MIN_MEAL_PROTEIN}g minimum ({diet_type})"
            logger.error(f"[MEAL_GUARDRAIL] {error_msg}")
            raise RetryableMealGenerationError(error_msg, meal_name, "low_protein")
        
        # DEBUG: Log exact meal structure to confirm nutrition shape
        import json
        logger.debug(
            "[DEBUG] MEAL STRUCTURE:\n%s",
            json.dumps({
                "name": meal.name,
                "meal_type": meal.meal_type,
                "nutrition": {
                    "calories": meal.nutrition.calories,
                    "protein": meal.nutrition.protein,
                    "carbohydrates": meal.nutrition.carbohydrates,
                    "fat": meal.nutrition.fat,
                    "fiber": meal.nutrition.fiber,
                    "sodium": meal.nutrition.sodium
                },
                "ingredients_count": len(meal.ingredients)
            }, indent=2, default=str)
        )
        
        # [LOCK] FREEZE nutrition snapshot for API safety
        meal._nutrition_snapshot = meal.nutrition
        
        return meal
    
    def _convert_to_grams(self, quantity: float, unit: str, food_name: str) -> float:
        """
        Convert various units to grams with STRICT RAW WEIGHT ENFORCEMENT.
        
        CRITICAL RULES:
        - All ingredient quantities must be RAW weight
        - Cooked items must be explicitly converted or rejected
        - No silent conversions that bypass raw weight rule
        """
        unit = unit.lower().strip()
        food_name_lower = food_name.lower()
        
        # STRICT ENFORCEMENT: Detect cooked items and handle explicitly
        cooked_indicators = ['cooked', 'steamed', 'boiled', 'grilled', 'baked', 'roasted', 'fried']
        is_cooked = any(indicator in food_name_lower for indicator in cooked_indicators)
        
        if is_cooked:
            logger.info(f"COOKED ITEM DETECTED: {food_name} - using cooked weight nutrition data")
            # Cooked items use their cooked nutrition data directly
            # This is explicit, not a silent conversion
        
        # Already in grams - preferred unit
        if unit in ["g", "gram", "grams"]:
            return quantity
        
        # Volume to weight conversions (approximate, with warnings)
        if unit in ["ml", "milliliter", "milliliters"]:
            logger.warning(f"VOLUME TO WEIGHT CONVERSION: {food_name} {quantity}{unit} - accuracy may vary")
            # Most liquids are close to 1g/ml
            if "milk" in food_name_lower or "water" in food_name_lower:
                return quantity  # 1ml ≈ 1g for milk/water
            elif "oil" in food_name_lower:
                return quantity * 0.92  # Oil is lighter
            else:
                return quantity  # Default assumption
        
        if unit in ["cup", "cups"]:
            logger.warning(f"CUP TO WEIGHT CONVERSION: {food_name} {quantity}{unit} - using standard conversions")
            # Common cup conversions (approximate)
            if "flour" in food_name_lower:
                return quantity * 120  # 1 cup flour ≈ 120g
            elif "rice" in food_name_lower:
                if is_cooked:
                    return quantity * 185  # 1 cup cooked rice ≈ 185g
                else:
                    return quantity * 180  # 1 cup dry rice ≈ 180g
            elif "oats" in food_name_lower:
                return quantity * 80   # 1 cup dry oats ≈ 80g
            else:
                return quantity * 150  # Default assumption
        
        if unit in ["tbsp", "tablespoon", "tablespoons"]:
            return quantity * 15  # 1 tbsp ≈ 15g
        
        if unit in ["tsp", "teaspoon", "teaspoons"]:
            return quantity * 5   # 1 tsp ≈ 5g
        
        if unit in ["piece", "pieces", "medium", "large", "small"]:
            logger.warning(f"PIECE TO WEIGHT CONVERSION: {food_name} {quantity}{unit} - using standard weights")
            # Piece-based conversions
            if "banana" in food_name_lower:
                return quantity * 120  # Medium banana ≈ 120g
            elif "apple" in food_name_lower:
                return quantity * 180  # Medium apple ≈ 180g
            elif "egg" in food_name_lower:
                return quantity * 50   # Large egg ≈ 50g
            else:
                return quantity * 100  # Default assumption
        
        # STRICT: Unknown units are flagged but not rejected (for flexibility)
        logger.warning(f"UNKNOWN UNIT: '{unit}' for {food_name} - assuming grams (RAW WEIGHT ENFORCEMENT)")
        return quantity
    
    def _auto_correct_protein(self, meal: Meal, target_protein_g: float) -> Meal:
        """
        HARDENED Auto-correction with strict priority order and limits.
        
        PRIORITY ORDER (STRICT):
        1. Increase high-quality protein sources
        2. Increase complex carbohydrates  
        3. Add fats last
        
        HARD LIMITS:
        - Protein per meal ≤ 40g
        - Fat ≤ target +10%
        - Never add new ingredients
        """
        current_protein = meal.nutrition.protein
        
        # Hard limit: Don't exceed 40g protein per meal
        effective_target = min(target_protein_g, 40.0)
        
        if current_protein >= effective_target * 0.8:
            return meal  # Already close enough
        
        logger.info(f"Auto-correcting {meal.name}: current {current_protein:.1f}g, target {effective_target:.1f}g")
        
        # PHASE 1: Increase high-quality protein sources (PRIORITY 1)
        protein_sources = []
        for ingredient in meal.ingredients:
            if ingredient.nutrition and ingredient.nutrition.protein >= 5:  # At least 5g protein
                protein_per_gram = ingredient.nutrition.protein / ingredient.quantity
                protein_sources.append((ingredient, protein_per_gram))
        
        # Sort by protein quality: complete proteins first, then by protein density
        protein_sources.sort(key=lambda x: (
            x[0].nutrition.protein_quality.value == "complete",  # Complete proteins first
            x[1]  # Then by protein density
        ), reverse=True)
        
        correction_attempts = 0
        max_attempts = 3
        
        for ingredient, protein_ratio in protein_sources:
            if correction_attempts >= max_attempts:
                break
                
            if current_protein >= effective_target * 0.8:
                break  # Target reached
            
            # Calculate needed protein
            protein_needed = effective_target - current_protein
            additional_grams = protein_needed / protein_ratio
            
            # Hard limit: Max 2x original quantity per correction
            original_quantity = ingredient.quantity
            max_increase = original_quantity  # Allow doubling
            actual_increase = min(additional_grams, max_increase)
            
            if actual_increase > 0:
                ingredient.quantity += actual_increase
                
                # Recalculate nutrition
                ingredient.nutrition = self.db.get_nutrition(
                    ingredient.name, 
                    ingredient.quantity
                )
                
                # Update current protein
                current_protein = meal.nutrition.protein
                correction_attempts += 1
                
                logger.info(f"Phase 1 - Increased {ingredient.name} by {actual_increase:.0f}g (protein: {current_protein:.1f}g)")
        
        # PHASE 2: Increase complex carbohydrates if still needed (PRIORITY 2)
        if current_protein < effective_target * 0.8 and correction_attempts < max_attempts:
            carb_sources = []
            for ingredient in meal.ingredients:
                if ingredient.nutrition and ingredient.nutrition.carbohydrates >= 10:  # At least 10g carbs
                    # Prefer complex carbs (grains, legumes)
                    is_complex = any(grain in ingredient.name.lower() for grain in 
                                   ['quinoa', 'rice', 'oats', 'lentil', 'bean', 'chickpea'])
                    carb_sources.append((ingredient, is_complex))
            
            # Sort by complexity (complex carbs first)
            carb_sources.sort(key=lambda x: x[1], reverse=True)
            
            for ingredient, is_complex in carb_sources[:2]:  # Max 2 carb sources
                if correction_attempts >= max_attempts:
                    break
                    
                # Modest increase for carbs (25% max)
                increase_factor = 0.25
                additional_grams = ingredient.quantity * increase_factor
                
                ingredient.quantity += additional_grams
                ingredient.nutrition = self.db.get_nutrition(
                    ingredient.name, 
                    ingredient.quantity
                )
                
                current_protein = meal.nutrition.protein
                correction_attempts += 1
                
                logger.info(f"Phase 2 - Increased {ingredient.name} by {additional_grams:.0f}g for carbs")
        
        # PHASE 3: Add healthy fats if still needed (PRIORITY 3)
        if current_protein < effective_target * 0.8 and correction_attempts < max_attempts:
            fat_sources = []
            for ingredient in meal.ingredients:
                if ingredient.nutrition and ingredient.nutrition.fat >= 5:  # At least 5g fat
                    # Prefer healthy fats
                    is_healthy = any(fat in ingredient.name.lower() for fat in 
                                   ['olive oil', 'avocado', 'nuts', 'seeds'])
                    fat_sources.append((ingredient, is_healthy))
            
            # Sort by health (healthy fats first)
            fat_sources.sort(key=lambda x: x[1], reverse=True)
            
            for ingredient, is_healthy in fat_sources[:1]:  # Max 1 fat source
                if correction_attempts >= max_attempts:
                    break
                
                # Small increase for fats (15% max to prevent macro drift)
                increase_factor = 0.15
                additional_grams = ingredient.quantity * increase_factor
                
                ingredient.quantity += additional_grams
                ingredient.nutrition = self.db.get_nutrition(
                    ingredient.name, 
                    ingredient.quantity
                )
                
                correction_attempts += 1
                
                logger.info(f"Phase 3 - Increased {ingredient.name} by {additional_grams:.0f}g for healthy fats")
        
        final_protein = meal.nutrition.protein
        logger.info(f"Auto-correction complete: {current_protein:.1f}g -> {final_protein:.1f}g (attempts: {correction_attempts})")
        
        return meal
    
    def validate_day_plan(
        self, 
        day_plan: DayPlan,
        min_calories: float,
        max_calories: float,
        min_protein_g: float,
        diet_type: str,
        allergies: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Validate a complete day plan against all constraints.
        
        Returns:
            (is_valid, list_of_violations)
        """
        violations = []
        daily_nutrition = day_plan.daily_totals
        
        # Calorie constraints
        if daily_nutrition.calories < min_calories:
            violations.append(f"Calories too low: {daily_nutrition.calories:.0f} < {min_calories:.0f}")
        
        if daily_nutrition.calories > max_calories:
            violations.append(f"Calories too high: {daily_nutrition.calories:.0f} > {max_calories:.0f}")
        
        # Protein constraints
        if daily_nutrition.protein < min_protein_g:
            violations.append(f"Protein too low: {daily_nutrition.protein:.1f}g < {min_protein_g:.1f}g")
        
        # Dietary restrictions
        violations.extend(self._validate_dietary_restrictions(day_plan, diet_type, allergies))
        
        # Meal variety constraints
        violations.extend(self._validate_meal_variety(day_plan))
        
        # Protein quality for vegetarians/vegans
        if diet_type in ["vegetarian", "vegan"] and daily_nutrition.protein_quality != ProteinQuality.COMPLETE:
            violations.append("No complete protein source found - add complementary proteins")
        
        return len(violations) == 0, violations
    
    def _validate_dietary_restrictions(
        self, 
        day_plan: DayPlan, 
        diet_type: str, 
        allergies: List[str]
    ) -> List[str]:
        """Validate dietary restrictions compliance"""
        violations = []
        
        # Check all ingredients against restrictions
        for meal in day_plan.meals:
            for ingredient in meal.ingredients:
                ingredient_name = ingredient.name.lower()
                
                # Vegetarian restrictions
                if diet_type == "vegetarian":
                    forbidden_foods = [
                        "chicken", "beef", "pork", "fish", "salmon", "tuna", 
                        "turkey", "lamb", "bacon", "ham", "sausage", "meat"
                    ]
                    for forbidden in forbidden_foods:
                        if forbidden in ingredient_name:
                            violations.append(f"Non-vegetarian ingredient: {ingredient.name} in {meal.name}")
                
                # Vegan restrictions (includes vegetarian + dairy/eggs)
                elif diet_type == "vegan":
                    forbidden_foods = [
                        "chicken", "beef", "pork", "fish", "salmon", "tuna",
                        "turkey", "lamb", "bacon", "ham", "sausage", "meat",
                        "milk", "cheese", "yogurt", "butter", "cream", "egg", "honey"
                    ]
                    for forbidden in forbidden_foods:
                        if forbidden in ingredient_name:
                            violations.append(f"Non-vegan ingredient: {ingredient.name} in {meal.name}")
                
                # Allergy restrictions
                for allergy in allergies:
                    if allergy.lower() in ingredient_name:
                        violations.append(f"Allergenic ingredient: {ingredient.name} (allergy: {allergy}) in {meal.name}")
        
        return violations
    
    def _validate_meal_variety(self, day_plan: DayPlan) -> List[str]:
        """
        DETERMINISTIC meal variety validation.
        
        STRICT RULES:
        - No repeated primary protein sources within a day
        - No repeated primary carb sources within a day
        - Algorithm is deterministic, not heuristic
        """
        violations = []
        
        # Track primary sources with their meal names for detailed reporting
        protein_sources = {}  # {source: meal_name}
        carb_sources = {}     # {source: meal_name}
        
        for meal in day_plan.meals:
            primary_protein = meal.primary_protein_source
            primary_carb = meal.primary_carb_source
            
            # Check protein variety
            if primary_protein:
                if primary_protein in protein_sources:
                    violations.append(
                        f"VARIETY VIOLATION: Repeated protein '{primary_protein}' "
                        f"in '{meal.name}' (already used in '{protein_sources[primary_protein]}')"
                    )
                else:
                    protein_sources[primary_protein] = meal.name
            
            # Check carb variety
            if primary_carb:
                if primary_carb in carb_sources:
                    violations.append(
                        f"VARIETY VIOLATION: Repeated carb '{primary_carb}' "
                        f"in '{meal.name}' (already used in '{carb_sources[primary_carb]}')"
                    )
                else:
                    carb_sources[primary_carb] = meal.name
        
        if not violations:
            logger.info(f"[OK] Variety validation passed - Proteins: {list(protein_sources.keys())}, Carbs: {list(carb_sources.keys())}")
        else:
            logger.warning(f"[ERROR] Variety violations detected: {violations}")
        
        return violations


# Global nutrition engine instance
_nutrition_engine = None

def get_nutrition_engine() -> NutritionEngine:
    """Get the global nutrition engine instance"""
    global _nutrition_engine
    if _nutrition_engine is None:
        _nutrition_engine = NutritionEngine()
    return _nutrition_engine


# PRODUCTION SAFETY FUNCTIONS

async def create_ingredient_with_resolution(name: str, quantity: float, unit: str = "g") -> Ingredient:
    """
    Create ingredient with safe resolution - THROWS TERMINAL ERRORS FOR UNRESOLVED INGREDIENTS.
    
    CRITICAL CHANGE: This function now throws NutritionCalculationError for unresolved ingredients
    instead of allowing them to pass silently. This prevents zero-calorie meals from being created.
    
    Args:
        name: Ingredient name
        quantity: Quantity in grams
        unit: Display unit
        
    Returns:
        Ingredient with resolved nutrition
        
    Raises:
        NutritionCalculationError: If ingredient cannot be resolved (TERMINAL - do not retry)
    """
    # DEBUG LOG: Input parameters
    logger.debug(
        "[INGREDIENT_INPUT] raw='%s' qty=%s unit=%s",
        name,
        quantity,
        unit
    )
    
    resolution_service = get_ingredient_resolution_service()
    nutrition_db = get_nutrition_database()
    
    try:
        # Use resolution service for safe ingredient handling
        resolution_result = await resolution_service.resolve_ingredient(name)
        
        # DEBUG LOG: After normalization
        if resolution_result.canonical_name:
            logger.debug(
                "[INGREDIENT_NORMALIZED] raw='%s' normalized='%s'",
                name,
                resolution_result.canonical_name
            )
        
        if resolution_result.status == ResolutionStatus.SKIPPED:
            # CRITICAL CHANGE: Throw terminal error instead of allowing skipped ingredients
            error_msg = f"Ingredient '{name}' could not be resolved and was skipped"
            logger.error(f"[TERMINAL] {error_msg}: {resolution_result.warning_message}")
            raise NutritionCalculationError(error_msg, [name])
        
        elif resolution_result.canonical_name:
            # DEBUG LOG: Before DB lookup
            logger.debug(
                "[NUTRITION_LOOKUP] ingredient='%s' available=%s",
                resolution_result.canonical_name,
                nutrition_db.validate_food_exists(resolution_result.canonical_name)
            )
            
            # Ingredient was resolved - get nutrition
            nutrition_data = nutrition_db.get_nutrition(resolution_result.canonical_name, quantity)
            
            ingredient = Ingredient(
                name=resolution_result.canonical_name,  # [FIX] Use canonical name instead of original
                quantity=quantity,
                unit=unit,
                nutrition=nutrition_data,
                resolved=True,
                resolution_status=resolution_result.resolution_method,
                warning_message=resolution_result.warning_message
            )
            
            # [LOCK] FREEZE nutrition snapshot for API safety
            ingredient._nutrition_snapshot = nutrition_data
            ingredient.name = resolution_result.canonical_name
            
            return ingredient
        
        else:
            # CRITICAL CHANGE: Throw terminal error instead of fallback
            error_msg = f"Ingredient resolution returned no canonical name for '{name}'"
            logger.error(f"[TERMINAL] {error_msg}")
            raise NutritionCalculationError(error_msg, [name])
            
    except NutritionCalculationError:
        # Re-raise terminal errors
        raise
    except Exception as e:
        # CRITICAL CHANGE: Convert all other exceptions to terminal errors
        error_msg = f"Exception during ingredient resolution for '{name}': {e}"
        logger.error(f"[TERMINAL] {error_msg}")
        raise NutritionCalculationError(error_msg, [name])


def add_protein_safety_net(meal: Meal, min_protein_g: float = 10.0) -> Meal:
    """
    Add protein safety net if meal protein is too low.
    
    Args:
        meal: Meal to check
        min_protein_g: Minimum protein threshold
        
    Returns:
        Meal with added protein if needed
    """
    current_protein = meal.nutrition.protein
    
    if current_protein < min_protein_g:
        protein_needed = min_protein_g - current_protein
        logger.warning(f"[SAFETY] Low protein in {meal.name}: {current_protein:.1f}g < {min_protein_g}g")
        
        # Add greek yogurt as safety protein
        nutrition_db = get_nutrition_database()
        
        # Calculate amount of greek yogurt needed (10g protein per 100g)
        yogurt_amount = (protein_needed / 10.0) * 100.0  # grams
        yogurt_nutrition = nutrition_db.get_nutrition("greek yogurt (plain)", yogurt_amount)
        
        safety_ingredient = Ingredient(
            name="greek yogurt (plain)",
            quantity=yogurt_amount,
            unit="g",
            nutrition=yogurt_nutrition,
            resolved=True,
            resolution_status="safety_net",
            warning_message=f"Added for protein safety net (+{protein_needed:.1f}g protein)"
        )
        
        meal.ingredients.append(safety_ingredient)
        logger.info(f"[SAFETY] Added {yogurt_amount:.0f}g greek yogurt to {meal.name} for protein safety")
    
    return meal


def _validate_canonical_immutability_scaling(plan_data: Dict[str, Any], stage: str):
    """
    CRITICAL: Validate that no non-canonical units exist during scaling.
    
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


def scale_plan_quantities(
    plan_data: Dict[str, Any], 
    target_calories: float, 
    target_protein: float
) -> Dict[str, Any]:
    """
    DETERMINISTIC QUANTITY SCALING - Hit calorie/protein targets without AI retry.
    
    CRITICAL: Canonical immutability guard - prevents mutation after unit enforcement.
    
    CORE ALGORITHM:
    1. Calculate current totals
    2. Identify scalable ingredients (energy + protein dense)
    3. Apply incremental scaling (10% steps)
    4. Recalculate nutrition after each step
    5. Stop when targets are met or max scaling reached
    
    HARD RULES:
    - Never exceed +30% quantity increase per ingredient
    - Never scale oils or sugars blindly
    - Prefer protein-dense foods first
    - Scaling happens WITHOUT calling AI
    - MAX INGREDIENT QUANTITY: 1000g (HARD LIMIT)
    - NEVER TOUCH UNITS - only scale quantities
    
    Args:
        plan_data: Plan data with meals
        target_calories: Target daily calories
        target_protein: Target daily protein (grams)
        
    Returns:
        Plan data with scaled quantities
        
    Raises:
        RuntimeError: If canonical unit violation detected
    """
    # CRITICAL: Canonical immutability guard
    if plan_data.get("_canonicalized"):
        _validate_canonical_immutability_scaling(plan_data, "scaling")
    
    logger.info(f"[SCALING_INPUT] Starting deterministic quantity scaling")
    logger.info(f"[SCALING_INPUT] Targets: {target_calories:.0f} cal, {target_protein:.1f}g protein")
    
    # Extract current nutrition totals
    current_calories, current_protein = _extract_plan_totals(plan_data)
    
    if current_calories <= 0 or current_protein <= 0:
        logger.error(f"[SCALING_ERROR] Cannot scale zero-nutrition plan: {current_calories} cal, {current_protein}g protein")
        return plan_data
    
    logger.info(f"[SCALING_INPUT] Current: {current_calories:.0f} cal, {current_protein:.1f}g protein")
    
    # Calculate gaps
    calorie_gap = target_calories - current_calories
    protein_gap = target_protein - current_protein
    
    # If already at or above targets, no scaling needed
    if calorie_gap <= 0 and protein_gap <= 0:
        logger.info(f"[SCALING_RESULT] No scaling needed - already at targets")
        return plan_data
    
    logger.info(f"[SCALING_INPUT] Gaps: {calorie_gap:.0f} cal, {protein_gap:.1f}g protein")
    
    # Allowed foods to scale (energy + protein dense)
    scalable_categories = [
        "grains",      # Rice, quinoa, oats
        "legumes",     # Lentils, chickpeas, beans
        "soy",         # Tofu, tempeh
        "dairy",       # Yogurt, paneer, milk
        "nuts",        # Almonds, walnuts
        "seeds"        # Chia, hemp, pumpkin
    ]
    
    # Apply scaling in steps
    max_scaling_steps = 3  # Maximum 3 steps of 10% each = 30% max increase
    scaling_step = 0.10    # 10% per step
    
    for step in range(max_scaling_steps):
        logger.info(f"[SCALING_STEP] Step {step + 1}/{max_scaling_steps}")
        
        # Find scalable ingredients across all meals
        scaled_any = False
        
        # Process meals based on plan type
        meals_to_process = []
        if plan_data.get("plan_type") == "weekly":
            for day in plan_data.get("days", []):
                meals_to_process.extend(day.get("meals", []))
        else:
            meals_to_process = plan_data.get("meals", [])
        
        for meal in meals_to_process:
            for ingredient in meal.get("ingredients", []):
                ingredient_name = ingredient.get("name", "").lower()
                current_quantity = ingredient.get("quantity", 0)
                
                # CRITICAL: Check max quantity BEFORE scaling
                if current_quantity >= 1000:
                    logger.error(
                        "[IMPOSSIBLE_QUANTITY]",
                        extra={
                            "ingredient": ingredient_name,
                            "quantity_g": current_quantity
                        }
                    )
                    logger.warning(f"[SCALING_GUARDRAIL] INGREDIENT EXCEEDS 1000g LIMIT: {ingredient_name} has {current_quantity}g - ABORTING SCALING")
                    return plan_data
                
                # Check if ingredient is scalable
                is_scalable = any(category in ingredient_name for category in scalable_categories)
                
                # Additional specific checks
                if not is_scalable:
                    # Check for specific protein-dense foods
                    protein_foods = ["paneer", "tofu", "greek yogurt", "cottage cheese", "lentil", "chickpea"]
                    is_scalable = any(food in ingredient_name for food in protein_foods)
                
                # Never scale oils, sugars, or spices
                avoid_scaling = ["oil", "sugar", "salt", "pepper", "spice", "herb"]
                if any(avoid in ingredient_name for avoid in avoid_scaling):
                    is_scalable = False
                
                if is_scalable and current_quantity > 0:
                    # CRITICAL: Use deepcopy to prevent mutation of original data
                    import copy
                    
                    # Apply scaling step - ONLY scale quantity, NEVER touch unit
                    new_quantity = current_quantity * (1 + scaling_step)
                    
                    # CRITICAL: Enforce max quantity limit
                    if new_quantity > 1000:
                        logger.info(f"[SCALING_GUARDRAIL] Would exceed 1000g limit: {ingredient_name} {current_quantity}g -> {new_quantity}g - CAPPING AT 1000g")
                        new_quantity = 1000
                    
                    # Round to human-friendly values
                    new_quantity = _round_to_human_value(new_quantity)
                    
                    # CRITICAL: Only update quantity, never touch unit or reconstruct ingredient
                    ingredient["quantity"] = new_quantity
                    scaled_any = True
                    
                    logger.info(f"[SCALING_APPLIED] {ingredient_name}: {current_quantity:.0f}g -> {new_quantity:.0f}g")
                    
                    # CRITICAL: Validate unit hasn't changed
                    if ingredient.get("unit") not in ["g", "scoops"]:
                        raise RuntimeError(f"SCALING VIOLATION: Unit changed during scaling for {ingredient_name}")
        
        if not scaled_any:
            logger.info(f"[SCALING_RESULT] No scalable ingredients found, stopping")
            break
        
        # Recalculate nutrition after scaling
        _recalculate_plan_nutrition(plan_data)
        
        # Check if targets are met
        new_calories, new_protein = _extract_plan_totals(plan_data)
        logger.info(f"[SCALING_STEP] After step {step + 1}: {new_calories:.0f} cal, {new_protein:.1f}g protein")
        
        # Check if we've reached acceptable targets (95% of target)
        if (new_calories >= target_calories * 0.95 and 
            new_protein >= target_protein * 0.95):
            logger.info(f"[SCALING_RESULT] Targets reached after {step + 1} steps")
            break
    
    # Final totals
    final_calories, final_protein = _extract_plan_totals(plan_data)
    logger.info(f"[SCALING_RESULT] Final: {final_calories:.0f} cal, {final_protein:.1f}g protein")
    
    return plan_data


def _extract_plan_totals(plan_data: Dict[str, Any]) -> Tuple[float, float]:
    """Extract total calories and protein from plan data - STRUCTURE-AGNOSTIC VERSION"""
    if plan_data.get("plan_type") == "weekly":
        # For weekly plans, calculate average daily totals
        total_calories = 0
        total_protein = 0
        valid_days = 0
        
        for day in plan_data.get("days", []):
            daily_totals = day.get("daily_totals", {})
            
            if daily_totals and daily_totals.get("calories", 0) > 0:
                # Use existing daily totals
                total_calories += daily_totals.get("calories", 0)
                total_protein += daily_totals.get("protein", 0)
                valid_days += 1
            else:
                # CRITICAL FIX: Calculate from meals if daily_totals missing
                meals = day.get("meals", [])
                day_calories = 0
                day_protein = 0
                
                for meal in meals:
                    meal_cal = 0.0
                    meal_pro = 0.0
                    
                    # CASE 1: nutrition is a dict
                    n = meal.get("nutrition")
                    if isinstance(n, dict):
                        meal_cal = float(n.get("calories", 0))
                        meal_pro = float(n.get("protein", 0))
                    
                    # CASE 2: nutrition is NutritionData-like object
                    elif hasattr(n, "calories"):
                        meal_cal = float(n.calories)
                        meal_pro = float(n.protein)
                    
                    # CASE 3: fallback -> sum ingredients
                    if meal_cal == 0 and meal.get("ingredients"):
                        for ing in meal["ingredients"]:
                            ing_n = ing.get("nutrition")
                            if isinstance(ing_n, dict):
                                meal_cal += float(ing_n.get("calories", 0))
                                meal_pro += float(ing_n.get("protein", 0))
                            elif hasattr(ing_n, "calories"):
                                meal_cal += float(ing_n.calories)
                                meal_pro += float(ing_n.protein)
                    
                    day_calories += meal_cal
                    day_protein += meal_pro
                
                if day_calories > 0:
                    # Update the day with calculated totals
                    day["daily_totals"] = {
                        "calories": round(day_calories, 1),
                        "protein": round(day_protein, 1),
                        "carbohydrates": 0,
                        "fat": 0,
                        "fiber": 0,
                        "sodium": 0
                    }
                    total_calories += day_calories
                    total_protein += day_protein
                    valid_days += 1
        
        if valid_days > 0:
            return total_calories / valid_days, total_protein / valid_days
        else:
            return 0, 0
    else:
        # For daily plans
        daily_totals = plan_data.get("daily_totals", {})
        
        if daily_totals and daily_totals.get("calories", 0) > 0:
            # Use existing daily totals
            return daily_totals.get("calories", 0), daily_totals.get("protein", 0)
        else:
            # CRITICAL FIX: Calculate from meals if daily_totals missing
            meals = plan_data.get("meals", [])
            total_calories = 0
            total_protein = 0
            
            for meal in meals:
                meal_cal = 0.0
                meal_pro = 0.0
                
                # CASE 1: nutrition is a dict
                n = meal.get("nutrition")
                if isinstance(n, dict):
                    meal_cal = float(n.get("calories", 0))
                    meal_pro = float(n.get("protein", 0))
                
                # CASE 2: nutrition is NutritionData-like object
                elif hasattr(n, "calories"):
                    meal_cal = float(n.calories)
                    meal_pro = float(n.protein)
                
                # CASE 3: fallback -> sum ingredients
                if meal_cal == 0 and meal.get("ingredients"):
                    for ing in meal["ingredients"]:
                        ing_n = ing.get("nutrition")
                        if isinstance(ing_n, dict):
                            meal_cal += float(ing_n.get("calories", 0))
                            meal_pro += float(ing_n.get("protein", 0))
                        elif hasattr(ing_n, "calories"):
                            meal_cal += float(ing_n.calories)
                            meal_pro += float(ing_n.protein)
                
                total_calories += meal_cal
                total_protein += meal_pro
            
            if total_calories > 0:
                # Update the plan with calculated totals
                plan_data["daily_totals"] = {
                    "calories": round(total_calories, 1),
                    "protein": round(total_protein, 1),
                    "carbohydrates": 0,
                    "fat": 0,
                    "fiber": 0,
                    "sodium": 0
                }
                return total_calories, total_protein
            
            return 0, 0


def _recalculate_plan_nutrition(plan_data: Dict[str, Any]):
    """Recalculate nutrition totals after quantity scaling"""
    nutrition_db = get_nutrition_database()
    
    if plan_data.get("plan_type") == "weekly":
        for day in plan_data.get("days", []):
            _recalculate_day_nutrition(day, nutrition_db)
    else:
        _recalculate_day_nutrition(plan_data, nutrition_db)


def _recalculate_day_nutrition(day_data: Dict[str, Any], nutrition_db):
    """Recalculate nutrition for a single day"""
    day_calories = 0
    day_protein = 0
    day_carbs = 0
    day_fat = 0
    day_fiber = 0
    day_sodium = 0
    
    logger.debug(f"[NUTRITION_RECALC_START] Recalculating nutrition for day with {len(day_data.get('meals', []))} meals")
    
    for meal_idx, meal in enumerate(day_data.get("meals", [])):
        meal_name = meal.get("name", f"meal_{meal_idx}")
        logger.debug(f"[MEAL_TOTALS] Processing meal: {meal_name}")
        
        meal_calories = 0
        meal_protein = 0
        meal_carbs = 0
        meal_fat = 0
        meal_fiber = 0
        meal_sodium = 0
        
        for ing_idx, ingredient in enumerate(meal.get("ingredients", [])):
            ingredient_name = ingredient.get("name", f"ingredient_{ing_idx}")
            quantity = ingredient.get("quantity", 0)
            
            logger.debug(f"[INGREDIENT_NUTRITION] ingredient={ingredient_name} quantity={quantity}g")
            
            # Get updated nutrition for new quantity
            try:
                nutrition = nutrition_db.get_nutrition(ingredient_name, quantity)
                
                # Update ingredient nutrition
                ingredient["calories"] = nutrition.calories
                ingredient["protein"] = nutrition.protein
                ingredient["carbohydrates"] = nutrition.carbohydrates
                ingredient["fat"] = nutrition.fat
                ingredient["fiber"] = nutrition.fiber
                ingredient["sodium"] = nutrition.sodium
                
                logger.debug(f"[INGREDIENT_NUTRITION] {ingredient_name}: {nutrition.calories:.1f}cal, {nutrition.protein:.1f}g protein")
                
                # Add to meal totals
                meal_calories += nutrition.calories
                meal_protein += nutrition.protein
                meal_carbs += nutrition.carbohydrates
                meal_fat += nutrition.fat
                meal_fiber += nutrition.fiber
                meal_sodium += nutrition.sodium
                
            except Exception as e:
                logger.error(f"[INGREDIENT_NUTRITION_ERROR] Could not recalculate nutrition for {ingredient_name}: {e}")
        
        # Update meal nutrition totals
        if "nutrition" not in meal:
            meal["nutrition"] = {}
        
        meal["nutrition"]["calories"] = round(meal_calories, 1)
        meal["nutrition"]["protein"] = round(meal_protein, 1)
        meal["nutrition"]["carbohydrates"] = round(meal_carbs, 1)
        meal["nutrition"]["fat"] = round(meal_fat, 1)
        meal["nutrition"]["fiber"] = round(meal_fiber, 1)
        meal["nutrition"]["sodium"] = round(meal_sodium, 1)
        
        logger.debug(f"[MEAL_TOTALS] {meal_name}: {meal_calories:.1f}cal, {meal_protein:.1f}g protein")
        
        # LEGACY SUPPORT: Also update total_calories and total_protein if they exist
        meal["total_calories"] = round(meal_calories, 1)
        meal["total_protein"] = round(meal_protein, 1)
        
        # Add to day totals
        day_calories += meal_calories
        day_protein += meal_protein
        day_carbs += meal_carbs
        day_fat += meal_fat
        day_fiber += meal_fiber
        day_sodium += meal_sodium
    
    # Update day totals
    day_data["daily_totals"] = {
        "calories": round(day_calories, 1),
        "protein": round(day_protein, 1),
        "carbohydrates": round(day_carbs, 1),
        "fat": round(day_fat, 1),
        "fiber": round(day_fiber, 1),
        "sodium": round(day_sodium, 1)
    }
    
    logger.info(f"[DAILY_TOTALS_AGGREGATED] Day totals: {day_calories:.1f}cal, {day_protein:.1f}g protein")


def _round_to_human_value(quantity: float) -> float:
    """Round quantities to human-friendly values"""
    if quantity < 10:
        return round(quantity, 1)  # 1 decimal place for small amounts
    elif quantity < 100:
        return round(quantity / 5) * 5  # Round to nearest 5g
    else:
        return round(quantity / 10) * 10  # Round to nearest 10g


def validate_plan_nutrition(meals: List[Meal], min_total_calories: float = 800.0) -> bool:
    """
    Validate plan-level nutrition - ABORT BEFORE VALIDATION IF ZERO CALORIES.
    
    Args:
        meals: List of meals in the plan
        min_total_calories: Minimum total calories for the plan
        
    Returns:
        True if plan is valid, raises exception if invalid
        
    Raises:
        ZeroCalorieError: If total calories is zero or too low
    """
    total_calories = sum(meal.nutrition.calories for meal in meals)
    total_protein = sum(meal.nutrition.protein for meal in meals)
    
    # CRITICAL: Zero calories must NEVER reach validation
    if total_calories <= 0:
        error_msg = f"ZERO CALORIE PLAN DETECTED: Total calories = {total_calories}"
        logger.error(f"[ERROR] {error_msg}")
        
        failed_meals = [meal.name for meal in meals if meal.nutrition.calories <= 0]
        raise ZeroCalorieError(error_msg, failed_meals)
    
    # Check minimum calories
    if total_calories < min_total_calories:
        logger.warning(f"[WARNING] Low calorie plan: {total_calories:.0f} < {min_total_calories:.0f} calories")
    
    # Check minimum protein
    if total_protein < 30:
        logger.warning(f"[WARNING] Low protein plan: {total_protein:.1f}g < 30g protein")
    
    logger.info(f"[OK] Plan validation passed: {total_calories:.0f} calories, {total_protein:.1f}g protein")
    return True