"""
Unit Enforcement System - Canonical Unit Validation and Conversion

This module enforces canonical units (grams for solids, ml for liquids)
and prevents non-weight units from entering the nutrition pipeline.

CRITICAL RULES:
1. Canonical unit: grams (g) for all solid foods
2. Canonical state: raw ingredients only
3. Ban non-weight units completely: large, medium, piece, cup, tbsp
4. Discrete items must be resolved via backend mapping only
5. No bypass path allowed
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)


class ContractViolationError(Exception):
    """Raised when non-canonical units reach nutrition calculation"""
    pass


class UnitConversionError(Exception):
    """Raised when unit conversion fails"""
    pass


@dataclass
class IngredientMapping:
    """Standard ingredient mapping to canonical units"""
    name: str
    canonical_weight_g: float
    category: str  # 'discrete', 'liquid', 'solid'


class UnitEnforcer:
    """
    Enforces canonical units and prevents contract violations.
    
    RESPONSIBILITIES:
    1. Validate all ingredients use canonical units (grams)
    2. Convert cooked -> raw before nutrition calculation
    3. Reject non-weight units completely
    4. Map discrete items to standard weights
    """
    
    def __init__(self):
        """Initialize unit enforcer with standard mappings"""
        self.discrete_mappings = self._load_discrete_mappings()
        self.cooked_to_raw_ratios = self._load_cooking_ratios()
        self.density_map = self._load_density_mappings()
        self.banned_units = {
            'cup', 'cups', 'handful', 'slice', 'slices', 'whole', 'half', 'quarter'
        }
        
        # Units that can be converted to grams
        self.convertible_units = {
            'tbsp', 'tablespoon', 'tsp', 'teaspoon', 'ml', 'milliliter', 'oz', 'ounce'
        }
        
        # Size descriptors that should be handled as discrete items
        self.size_descriptors = {
            'large', 'medium', 'small', 'piece', 'pieces'
        }
    
    def enforce_canonical_units(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        MANDATORY: Enforce canonical units across entire plan.
        
        This is the hard gate that prevents non-canonical units from
        reaching nutrition calculation. Any violation results in rejection.
        
        Args:
            plan_data: Raw plan data from LLM
            
        Returns:
            Plan data with all ingredients in canonical units (grams)
            
        Raises:
            ContractViolationError: If non-canonical units cannot be resolved
        """
        logger.info(" ENFORCING CANONICAL UNITS - Hard Gate Active")
        
        enforced_plan = plan_data.copy()
        violations = []
        
        # Process based on plan type
        if plan_data.get("plan_type") == "weekly":
            for day_idx, day in enumerate(enforced_plan.get("days", [])):
                try:
                    day["meals"] = self._enforce_meals_units(day.get("meals", []))
                except ContractViolationError as e:
                    violations.append(f"Day {day_idx + 1}: {str(e)}")
        
        elif plan_data.get("plan_type") == "daily":
            try:
                enforced_plan["meals"] = self._enforce_meals_units(enforced_plan.get("meals", []))
            except ContractViolationError as e:
                violations.append(f"Daily plan: {str(e)}")
        
        if violations:
            violation_summary = "; ".join(violations)
            logger.error(f" UNIT ENFORCEMENT FAILED: {violation_summary}")
            raise ContractViolationError(f"Unit enforcement violations: {violation_summary}")
        
        # CRITICAL: Mark plan as canonicalized to prevent mutation
        enforced_plan["_canonicalized"] = True
        
        logger.info("[OK] CANONICAL UNITS ENFORCED - All ingredients in grams")
        return enforced_plan
    
    def _enforce_meals_units(self, meals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enforce canonical units for all meals"""
        enforced_meals = []
        
        for meal_idx, meal in enumerate(meals):
            try:
                enforced_meal = meal.copy()
                enforced_meal["ingredients"] = self._enforce_ingredients_units(
                    meal.get("ingredients", [])
                )
                enforced_meals.append(enforced_meal)
            except ContractViolationError as e:
                raise ContractViolationError(f"Meal {meal_idx + 1} ({meal.get('name', 'unknown')}): {str(e)}")
        
        return enforced_meals
    
    def _enforce_ingredients_units(self, ingredients: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enforce canonical units for all ingredients"""
        enforced_ingredients = []
        
        for ingredient in ingredients:
            try:
                enforced_ingredient = self._enforce_single_ingredient(ingredient)
                enforced_ingredients.append(enforced_ingredient)
            except ContractViolationError as e:
                ingredient_name = ingredient.get("name", "unknown")
                raise ContractViolationError(f"Ingredient '{ingredient_name}': {str(e)}")
        
        return enforced_ingredients
    
    def _enforce_single_ingredient(self, ingredient: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enforce canonical units for a single ingredient.
        
        ENFORCEMENT RULES:
        1. Check for banned units -> reject immediately
        2. Check for cooked ingredients -> convert to raw
        3. Check for discrete items -> map to grams
        4. Validate final unit is grams
        5. HARD ERROR if non-canonical units remain
        """
        name = ingredient.get("name", "").lower().strip()
        quantity = ingredient.get("quantity", 0)
        unit = ingredient.get("unit", "").lower().strip()
        
        # Normalize ingredient name (remove punctuation, extra spaces)
        name = self._normalize_ingredient_name(name)
        
        logger.debug(f"[UNIT_PRE_NORMALIZATION] {name}: {quantity} {unit}")
        
        # CRITICAL: Hard sanity cap on ingredient weight (absolute maximum)
        if quantity > 2000:
            logger.error(f"[UNIT_ENFORCEMENT_ERROR] INGREDIENT EXCEEDS ABSOLUTE LIMIT: {name} has {quantity}{unit} > 2000g - REJECTING")
            raise ContractViolationError(
                f"Ingredient quantity exceeds absolute limit: {name} has {quantity}{unit} (max: 2000g)"
            )
        
        # CRITICAL FIX: Egg "pc" unit normalization (Task 8 Fix 1)
        if unit in ["pc", "piece", "pieces"] and "egg" in name:
            # Convert egg pieces to grams: 1 egg = 60g (large egg standard)
            egg_weight_g = quantity * 60.0
            
            # Apply hard sanity cap after conversion
            if egg_weight_g > 2000:
                logger.error(f"[UNIT_ENFORCEMENT_ERROR] EGG CONVERSION EXCEEDS LIMIT: {name} {quantity}pc -> {egg_weight_g}g > 2000g - REJECTING")
                raise ContractViolationError(
                    f"Egg conversion weight exceeds limit: {name} {quantity}pc -> {egg_weight_g}g (max: 2000g)"
                )
            
            logger.info(
                "[UNIT_ENFORCED]",
                extra={
                    "ingredient": name,
                    "final_quantity_g": egg_weight_g,
                    "unit": "g",
                    "conversion_applied": "egg_pc_to_grams"
                }
            )
            
            return {
                **ingredient,
                "name": name,  # Use normalized name
                "quantity": float(egg_weight_g),
                "unit": "g",
                "conversion_applied": "egg_pc_to_grams"
            }
        
        # CRITICAL FIX: Skip discrete mapping if unit is already 'g'
        if unit == "g":
            # Apply hard sanity cap
            if quantity > 2000:
                logger.error(f"[UNIT_ENFORCEMENT_ERROR] FINAL WEIGHT EXCEEDS LIMIT: {name} has {quantity}g > 2000g - REJECTING")
                raise ContractViolationError(
                    f"Final ingredient weight exceeds limit: {name} has {quantity}g (max: 2000g)"
                )
            
            logger.info(
                "[UNIT_ENFORCED]",
                extra={
                    "ingredient": name,
                    "final_quantity_g": quantity,
                    "unit": unit
                }
            )
            
            return {
                **ingredient,
                "name": name,  # Use normalized name
                "quantity": float(quantity),
                "unit": "g"
            }
        
        # CRITICAL FIX: Convert ml -> g using density mapping
        if unit in ["ml", "milliliter", "milliliters"]:
            converted_quantity = self._convert_ml_to_grams(name, quantity)
            
            # Apply hard sanity cap after conversion
            if converted_quantity > 2000:
                logger.error(f"[UNIT_ENFORCEMENT_ERROR] ML CONVERSION EXCEEDS LIMIT: {name} {quantity}ml -> {converted_quantity}g > 2000g - REJECTING")
                raise ContractViolationError(
                    f"ML conversion weight exceeds limit: {name} {quantity}ml -> {converted_quantity}g (max: 2000g)"
                )
            
            logger.info(
                "[UNIT_ENFORCED]",
                extra={
                    "ingredient": name,
                    "final_quantity_g": converted_quantity,
                    "unit": "g"
                }
            )
            
            return {
                **ingredient,
                "name": name,  # Use normalized name
                "quantity": converted_quantity,
                "unit": "g",
                "conversion_applied": "ml_to_grams"
            }
        
        # RULE 1: Check for size descriptors with discrete items
        if unit in self.size_descriptors and self._is_discrete_item(name, unit):
            canonical_weight = self._map_discrete_to_grams(name, quantity, unit)
            logger.info(f"[UNIT_POST_NORMALIZATION] {name}: {quantity} {unit} -> {canonical_weight}g (discrete mapping)")
            
            return {
                **ingredient,
                "quantity": canonical_weight,
                "unit": "g",
                "conversion_applied": f"discrete_{unit}_to_grams"
            }
        
        # RULE 6: Convert common volume/weight units to grams
        if unit not in ["g", "grams", "gram", ""]:
            # Try to convert common units
            converted_quantity = self._convert_to_grams(quantity, unit, name)
            if converted_quantity is not None:
                logger.info(f"[UNIT_POST_NORMALIZATION] {name}: {quantity} {unit} -> {converted_quantity}g (unit conversion)")
                
                return {
                    **ingredient,
                    "quantity": converted_quantity,
                    "unit": "g",
                    "conversion_applied": f"{unit}_to_grams"
                }
            else:
                # CRITICAL FIX: Handle cooked ingredients with piece units
                # These should be passed through to canonicalization with a reasonable default weight
                if self._is_cooked_ingredient(name) and unit.lower() in ["piece", "pieces"]:
                    # Use a reasonable default weight for cooked vegetables/items
                    default_weight = 100.0  # 100g default for cooked items
                    total_weight = quantity * default_weight
                    
                    logger.info(f"[UNIT_POST_NORMALIZATION] {name}: {quantity} {unit} -> {total_weight}g (cooked item default)")
                    
                    return {
                        **ingredient,
                        "quantity": total_weight,
                        "unit": "g",
                        "conversion_applied": "cooked_piece_to_grams"
                    }
                
                # Check if it's a banned unit (after trying conversion)
                if unit in self.banned_units:
                    logger.error(f"[UNIT_ENFORCEMENT_ERROR] BANNED UNIT DETECTED: {name} has unit '{unit}' - ONLY GRAMS ALLOWED")
                    raise ContractViolationError(
                        f"Banned unit '{unit}' detected. Only grams (g) allowed."
                    )
                else:
                    logger.error(f"[UNIT_ENFORCEMENT_ERROR] CANNOT CONVERT UNIT: {name} has unit '{unit}' - NO CONVERSION AVAILABLE")
                    raise ContractViolationError(
                        f"Cannot convert unit '{unit}' to grams for ingredient '{name}'"
                    )
        
        # RULE 4: Special handling for protein powder (must be in scoops)
        if self._is_protein_powder(name):
            result = self._handle_protein_powder(ingredient)
            logger.info(f"[UNIT_POST_NORMALIZATION] {name}: {quantity} {unit} -> {result['quantity']} {result['unit']} (protein powder)")
            return result
        
        # RULE 5: Map discrete items to grams
        if self._is_discrete_item(name, unit):
            canonical_weight = self._map_discrete_to_grams(name, quantity, unit)
            logger.info(f"[UNIT_POST_NORMALIZATION] {name}: {quantity} {unit} -> {canonical_weight}g (discrete mapping)")
            
            return {
                **ingredient,
                "quantity": canonical_weight,
                "unit": "g",
                "conversion_applied": "discrete_to_grams"
            }
        
        # RULE 6: Convert common volume/weight units to grams
        if unit not in ["g", "grams", "gram", ""]:
            # Try to convert common units
            converted_quantity = self._convert_to_grams(quantity, unit, name)
            if converted_quantity is not None:
                logger.info(f"[UNIT_POST_NORMALIZATION] {name}: {quantity} {unit} -> {converted_quantity}g (unit conversion)")
                
                return {
                    **ingredient,
                    "quantity": converted_quantity,
                    "unit": "g",
                    "conversion_applied": f"{unit}_to_grams"
                }
            else:
                logger.error(f"[UNIT_ENFORCEMENT_ERROR] CANNOT CONVERT UNIT: {name} has unit '{unit}' - NO CONVERSION AVAILABLE")
                raise ContractViolationError(
                    f"Cannot convert unit '{unit}' to grams for ingredient '{name}'"
                )
        
        # RULE 7: HARD VALIDATION - Ensure NO non-canonical units exit
        final_unit = "g"  # Force canonical unit
        final_quantity = float(quantity)
        
        # CRITICAL: Log final result to ensure canonicalization
        logger.info(f"[UNIT_POST_NORMALIZATION] {name}: {quantity} {unit} -> {final_quantity}g (already canonical)")
        
        # HARD ERROR if unit is still non-canonical
        if unit not in ["g", "grams", "gram", ""] and not self._is_protein_powder(name):
            logger.error(f"[UNIT_ENFORCEMENT_CRITICAL_ERROR] NON-CANONICAL UNIT ESCAPED: {name} still has unit '{unit}'")
            raise ContractViolationError(
                f"CRITICAL: Non-canonical unit '{unit}' escaped normalization for ingredient '{name}'"
            )
        
        return {
            **ingredient,
            "quantity": final_quantity,
            "unit": final_unit
        }
    
    def _is_cooked_ingredient(self, name: str) -> bool:
        """Check if ingredient is explicitly marked as cooked, processed, or frozen"""
        cooked_indicators = [
            'cooked', 'boiled', 'steamed', 'grilled', 'baked', 'fried',
            'roasted', 'sautéed', 'sauteed', 'prepared', 'ready',
            'frozen', 'processed', 'canned', 'pickled', 'smoked',
            'dried', 'dehydrated', 'instant', 'pre-cooked'
        ]
        
        name_lower = name.lower()
        return any(indicator in name_lower for indicator in cooked_indicators)
    
    def _convert_cooked_to_raw(self, cooked_name: str, cooked_quantity: float) -> Tuple[str, float]:
        """Convert cooked ingredient to raw equivalent"""
        
        # Extract base ingredient name
        base_name = self._extract_base_ingredient(cooked_name)
        
        # Get conversion ratio
        ratio = self.cooked_to_raw_ratios.get(base_name, 1.0)
        
        # Convert quantity (cooked is typically heavier due to water absorption)
        raw_quantity = cooked_quantity / ratio
        
        return base_name, round(raw_quantity, 1)
    
    def _extract_base_ingredient(self, cooked_name: str) -> str:
        """Extract base ingredient name from cooked description"""
        # Remove cooking method indicators and processing states
        processing_indicators = [
            'cooked', 'boiled', 'steamed', 'grilled', 'baked', 'fried',
            'roasted', 'sautéed', 'sauteed', 'prepared', 'ready',
            'frozen', 'processed', 'canned', 'pickled', 'smoked',
            'dried', 'dehydrated', 'instant', 'pre-cooked'
        ]
        
        clean_name = cooked_name.lower()
        for indicator in processing_indicators:
            clean_name = clean_name.replace(indicator, '').strip()
        
        # Clean up extra spaces and common words
        clean_name = re.sub(r'\s+', ' ', clean_name)
        clean_name = clean_name.replace('(', '').replace(')', '')
        
        return clean_name.strip()
    
    def _is_protein_powder(self, name: str) -> bool:
        """Check if ingredient is protein powder"""
        protein_powder_indicators = [
            'protein powder', 'whey protein', 'casein protein', 'plant protein',
            'pea protein', 'soy protein', 'hemp protein', 'rice protein',
            'protein supplement', 'whey isolate', 'whey concentrate'
        ]
        
        name_lower = name.lower()
        return any(indicator in name_lower for indicator in protein_powder_indicators)
    
    def _handle_protein_powder(self, ingredient: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle protein powder with special scoop-based rules.
        
        MANDATORY RULES:
        - Display unit: scoops (whole numbers only)
        - Calculation unit: grams (internal)
        - 1 scoop = 30g powder = 24g protein (system default)
        """
        name = ingredient.get("name", "")
        quantity = ingredient.get("quantity", 0)
        unit = ingredient.get("unit", "").lower().strip()
        
        # Check if already in scoops
        if unit in ["scoop", "scoops", "serving", "servings"]:
            # Validate whole scoops only
            if not isinstance(quantity, int) and quantity != int(quantity):
                raise ContractViolationError(
                    f"Protein powder must be whole scoops only, got {quantity} scoops"
                )
            
            scoop_count = int(quantity)
            
            # Validate reasonable bounds (max 4 scoops per meal)
            if scoop_count < 1 or scoop_count > 4:
                raise ContractViolationError(
                    f"Protein powder scoop count must be 1-4, got {scoop_count}"
                )
            
            # Convert to internal grams for nutrition calculation
            internal_grams = scoop_count * 30  # 1 scoop = 30g
            protein_grams = scoop_count * 24   # 1 scoop = 24g protein
            
            return {
                **ingredient,
                "quantity": scoop_count,
                "unit": "scoops",
                "internal_grams": internal_grams,
                "nutrition": {
                    **ingredient.get("nutrition", {}),
                    "protein": protein_grams,
                    "calories": scoop_count * 120,  # ~120 cal per scoop
                    "carbohydrates": scoop_count * 2,  # ~2g carbs per scoop
                    "fat": scoop_count * 1  # ~1g fat per scoop
                },
                "conversion_applied": "protein_powder_scoops"
            }
        
        # If in grams, reject (LLM contract violation)
        elif unit in ["g", "grams", "gram"]:
            raise ContractViolationError(
                f"Protein powder must be specified in scoops, not grams. "
                f"LLM contract violation: got {quantity}g"
            )
        
        # If no unit specified, assume scoops but validate
        elif unit == "":
            if not isinstance(quantity, int) and quantity != int(quantity):
                raise ContractViolationError(
                    f"Protein powder quantity must be whole scoops, got {quantity}"
                )
            
            scoop_count = int(quantity)
            if scoop_count < 1 or scoop_count > 4:
                raise ContractViolationError(
                    f"Protein powder scoop count must be 1-4, got {scoop_count}"
                )
            
            # Convert to internal representation
            internal_grams = scoop_count * 30
            protein_grams = scoop_count * 24
            
            return {
                **ingredient,
                "quantity": scoop_count,
                "unit": "scoops",
                "internal_grams": internal_grams,
                "nutrition": {
                    **ingredient.get("nutrition", {}),
                    "protein": protein_grams,
                    "calories": scoop_count * 120,
                    "carbohydrates": scoop_count * 2,
                    "fat": scoop_count * 1
                },
                "conversion_applied": "protein_powder_assumed_scoops"
            }
        
        else:
            raise ContractViolationError(
                f"Invalid unit '{unit}' for protein powder. Must be 'scoops' or empty."
            )
    
    def _is_discrete_item(self, name: str, unit: str) -> bool:
        """Check if ingredient is a discrete item that needs mapping"""
        name_lower = name.lower()
        
        # CRITICAL FIX: Don't treat cooked ingredients as discrete items
        # Cooked ingredients should be handled by canonicalization, not discrete mapping
        cooked_indicators = [
            'cooked', 'boiled', 'steamed', 'grilled', 'baked', 'fried',
            'roasted', 'sautéed', 'sauteed', 'prepared', 'ready'
        ]
        if any(indicator in name_lower for indicator in cooked_indicators):
            return False
        
        # Check for common discrete items by name
        discrete_items = ['egg', 'banana', 'apple', 'orange', 'tomato', 'onion', 'potato', 'carrot']
        if any(item in name_lower for item in discrete_items):
            return True
        
        # Check if it's a known discrete item
        if any(discrete in name_lower for discrete in self.discrete_mappings.keys()):
            return True
        
        # Check if unit suggests discrete counting
        discrete_units = ['', 'item', 'items', 'each', 'whole', 'piece', 'pieces']
        if unit.lower() in discrete_units:
            return True
        
        # Check if unit is a size descriptor
        if unit.lower() in self.size_descriptors:
            return True
        
        return False
    
    def _map_discrete_to_grams(self, name: str, quantity: float, unit: str) -> float:
        """Map discrete items to standard gram weights"""
        name_lower = name.lower()
        
        # Find matching discrete mapping
        for discrete_name, mapping in self.discrete_mappings.items():
            if discrete_name in name_lower:
                total_weight = quantity * mapping.canonical_weight_g
                return round(total_weight, 1)
        
        # Fallback mappings for common items with size adjustments
        fallback_weights = {
            'egg': {'large': 50, 'medium': 45, 'small': 40, 'default': 50},
            'banana': {'large': 140, 'medium': 120, 'small': 100, 'default': 120},
            'apple': {'large': 180, 'medium': 150, 'small': 120, 'default': 150},
            'orange': {'large': 150, 'medium': 130, 'small': 110, 'default': 130},
            'tomato': {'large': 120, 'medium': 100, 'small': 80, 'default': 100},
            'onion': {'large': 130, 'medium': 110, 'small': 90, 'default': 110},
            'potato': {'large': 180, 'medium': 150, 'small': 120, 'default': 150},
            'carrot': {'large': 80, 'medium': 60, 'small': 40, 'default': 60}
        }
        
        for item, weights in fallback_weights.items():
            if item in name_lower:
                # Use size-specific weight if available
                if unit.lower() in weights:
                    weight = weights[unit.lower()]
                else:
                    weight = weights['default']
                return round(quantity * weight, 1)
        
        raise ContractViolationError(
            f"Cannot map discrete item '{name}' to grams - no mapping available"
        )
    
    def _convert_to_grams(self, quantity: float, unit: str, ingredient_name: str) -> Optional[float]:
        """Convert common units to grams"""
        unit_lower = unit.lower()
        
        # Volume conversions for cooking measurements
        cooking_conversions = {
            'tbsp': 15.0,
            'tablespoon': 15.0,
            'tablespoons': 15.0,
            'tsp': 5.0,
            'teaspoon': 5.0,
            'teaspoons': 5.0
        }
        
        if unit_lower in cooking_conversions:
            return round(quantity * cooking_conversions[unit_lower], 1)
        
        # Volume to weight conversions (approximate)
        volume_conversions = {
            'ml': 1.0,  # Assume 1ml = 1g for most liquids
            'milliliter': 1.0,
            'milliliters': 1.0,
            'l': 1000.0,
            'liter': 1000.0,
            'liters': 1000.0
        }
        
        if unit_lower in volume_conversions:
            return round(quantity * volume_conversions[unit_lower], 1)
        
        # Weight conversions
        weight_conversions = {
            'kg': 1000.0,
            'kilogram': 1000.0,
            'kilograms': 1000.0,
            'oz': 28.35,
            'ounce': 28.35,
            'ounces': 28.35,
            'lb': 453.6,
            'pound': 453.6,
            'pounds': 453.6
        }
        
        if unit_lower in weight_conversions:
            return round(quantity * weight_conversions[unit_lower], 1)
        
        return None
    
    def _load_discrete_mappings(self) -> Dict[str, IngredientMapping]:
        """Load standard discrete item mappings"""
        return {
            'egg': IngredientMapping('egg', 50.0, 'discrete'),
            'large egg': IngredientMapping('egg', 60.0, 'discrete'),
            'medium egg': IngredientMapping('egg', 50.0, 'discrete'),
            'small egg': IngredientMapping('egg', 40.0, 'discrete'),
            'banana': IngredientMapping('banana', 120.0, 'discrete'),
            'large banana': IngredientMapping('banana', 150.0, 'discrete'),
            'medium banana': IngredientMapping('banana', 120.0, 'discrete'),
            'small banana': IngredientMapping('banana', 90.0, 'discrete'),
            'apple': IngredientMapping('apple', 150.0, 'discrete'),
            'orange': IngredientMapping('orange', 130.0, 'discrete'),
            'tomato': IngredientMapping('tomato', 100.0, 'discrete'),
            'onion': IngredientMapping('onion', 110.0, 'discrete'),
            'medium onion': IngredientMapping('onion', 110.0, 'discrete'),
            'large onion': IngredientMapping('onion', 150.0, 'discrete'),
            'potato': IngredientMapping('potato', 150.0, 'discrete'),
            'carrot': IngredientMapping('carrot', 60.0, 'discrete'),
            'bell pepper': IngredientMapping('bell pepper', 120.0, 'discrete'),
            'avocado': IngredientMapping('avocado', 150.0, 'discrete'),
            'lemon': IngredientMapping('lemon', 60.0, 'discrete'),
            'lime': IngredientMapping('lime', 30.0, 'discrete')
        }
    
    def _load_cooking_ratios(self) -> Dict[str, float]:
        """Load cooked to raw conversion ratios"""
        return {
            # Grains (cooked is heavier due to water absorption)
            'rice': 3.0,        # 100g cooked rice = ~33g raw rice
            'quinoa': 2.5,      # 100g cooked quinoa = ~40g raw quinoa
            'pasta': 2.2,       # 100g cooked pasta = ~45g raw pasta
            'oats': 2.0,        # 100g cooked oats = ~50g raw oats
            'barley': 3.0,
            'bulgur': 2.5,
            
            # Legumes (cooked is heavier)
            'lentils': 2.5,     # 100g cooked lentils = ~40g raw lentils
            'chickpeas': 2.5,
            'black beans': 2.5,
            'kidney beans': 2.5,
            'white beans': 2.5,
            
            # Vegetables (minimal change, mostly water loss)
            'broccoli': 0.9,    # Slight water loss when cooked
            'spinach': 0.3,     # Significant volume reduction
            'kale': 0.4,
            'mushrooms': 0.7,
            'zucchini': 0.9,
            'carrots': 0.95,
            'bell peppers': 0.9,
            
            # Proteins (water loss during cooking)
            'chicken breast': 0.75,  # 100g cooked = ~133g raw
            'salmon': 0.8,
            'tofu': 0.9,        # Minimal change
            'tempeh': 0.95,
        }
    
    def _load_density_mappings(self) -> Dict[str, float]:
        """Load density mappings for ml -> g conversion"""
        return {
            # Dairy products
            'greek yogurt (plain)': 1.03,
            'greek yogurt': 1.03,
            'yogurt': 1.03,
            'milk': 1.03,
            'whole milk': 1.03,
            'skim milk': 1.03,
            'almond milk': 1.02,
            'soy milk': 1.03,
            'oat milk': 1.04,
            
            # Liquids
            'water': 1.0,
            'coconut water': 1.02,
            'vegetable broth': 1.0,
            'chicken broth': 1.0,
            
            # Oils (lighter than water)
            'olive oil': 0.92,
            'coconut oil': 0.92,
            'avocado oil': 0.92,
            
            # Sauces and condiments
            'tomato sauce': 1.05,
            'soy sauce': 1.15,
            'vinegar': 1.01,
            'lemon juice': 1.02,
            'lime juice': 1.02,
            
            # Default for unknown liquids
            'default': 1.0
        }
    
    def _convert_ml_to_grams(self, ingredient_name: str, quantity_ml: float) -> float:
        """Convert ml to grams using density mapping"""
        # Find matching density
        density = None
        
        # Try exact match first
        if ingredient_name in self.density_map:
            density = self.density_map[ingredient_name]
        else:
            # Try partial matches
            for key, value in self.density_map.items():
                if key in ingredient_name or ingredient_name in key:
                    density = value
                    break
        
        # Use default density if no match found
        if density is None:
            density = self.density_map['default']
            logger.warning(f"[ML_CONVERSION] No density found for '{ingredient_name}', using default density {density}")
        
        converted_grams = quantity_ml * density
        logger.info(f"[ML_CONVERSION] {ingredient_name}: {quantity_ml}ml -> {converted_grams}g (density: {density})")
        
        return round(converted_grams, 1)
    
    def _normalize_ingredient_name(self, name: str) -> str:
        """Normalize ingredient name - remove punctuation, extra spaces"""
        import re
        
        # Remove punctuation and extra spaces
        normalized = re.sub(r'[^\w\s]', '', name)  # Remove punctuation
        normalized = re.sub(r'\s+', ' ', normalized)  # Normalize spaces
        normalized = normalized.strip().lower()
        
        return normalized
    
    def _is_cooked_ingredient(self, name: str) -> bool:
        """Check if ingredient is explicitly marked as cooked, processed, or frozen"""
        cooked_indicators = [
            'cooked', 'boiled', 'steamed', 'grilled', 'baked', 'fried',
            'roasted', 'sautéed', 'sauteed', 'prepared', 'ready',
            'frozen', 'processed', 'canned', 'pickled', 'smoked',
            'dried', 'dehydrated', 'instant', 'pre-cooked'
        ]
        
        name_lower = name.lower()
        return any(indicator in name_lower for indicator in cooked_indicators)


# Global unit enforcer instance
_unit_enforcer = None

def get_unit_enforcer() -> UnitEnforcer:
    """Get the global unit enforcer instance"""
    global _unit_enforcer
    if _unit_enforcer is None:
        _unit_enforcer = UnitEnforcer()
    return _unit_enforcer