"""
Ingredient Canonicalization Service - Cooked-to-Raw Normalization

This module handles the canonicalization boundary where cooked/processed ingredients
from LLM output are normalized to raw canonical ingredients BEFORE integrity validation.

CRITICAL PIPELINE ORDER:
LLM Output → Unit Enforcement → Cooked-to-Raw Normalization → Canonical Ingredient Rewrite → Integrity Validation

CANONICALIZATION RULES:
1. Cooked/processed ingredient names are allowed in LLM output
2. They must be fully normalized to raw canonical ingredients BEFORE integrity validation
3. Integrity validation must ONLY see canonical raw ingredients

Examples:
- "cooked quinoa" → "quinoa (dry)"
- "lentils green cooked" → "lentils (green, dry)"
- "steamed broccoli" → "broccoli"
"""

import logging
from typing import Dict, List, Any, Tuple
import re

logger = logging.getLogger(__name__)


class IngredientCanonicalizer:
    """
    Canonicalizes cooked/processed ingredients to raw canonical forms.
    
    This is the strict normalization boundary that ensures integrity validation
    only sees canonical raw ingredient names.
    """
    
    def __init__(self):
        """Initialize canonicalizer with cooked-to-raw mappings"""
        self.cooked_to_raw_ratios = self._load_cooking_ratios()
        self.cooked_indicators = [
            'cooked', 'boiled', 'steamed', 'grilled', 'baked', 'fried',
            'roasted', 'sautéed', 'sauteed', 'prepared', 'ready',
            'frozen', 'processed', 'canned', 'pickled', 'smoked',
            'dried', 'dehydrated', 'instant', 'pre-cooked'
        ]
    
    def canonicalize_plan_ingredients(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        MANDATORY: Canonicalize all cooked/processed ingredients to raw forms.
        
        This is the normalization boundary that ensures integrity validation
        only sees canonical raw ingredient names.
        
        Args:
            plan_data: Plan data with potentially cooked ingredient names
            
        Returns:
            Plan data with all ingredients canonicalized to raw forms
        """
        logger.info("[CANONICALIZATION_START] Starting cooked-to-raw normalization")
        
        canonicalized_plan = plan_data.copy()
        
        # Process based on plan type
        if plan_data.get("plan_type") == "weekly":
            for day_idx, day in enumerate(canonicalized_plan.get("days", [])):
                day["meals"] = self._canonicalize_meals(day.get("meals", []))
        elif plan_data.get("plan_type") == "daily":
            canonicalized_plan["meals"] = self._canonicalize_meals(canonicalized_plan.get("meals", []))
        
        logger.info("[CANONICALIZATION_COMPLETE] All ingredients canonicalized to raw forms")
        return canonicalized_plan
    
    def _canonicalize_meals(self, meals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Canonicalize ingredients in all meals"""
        canonicalized_meals = []
        
        for meal in meals:
            canonicalized_meal = meal.copy()
            canonicalized_meal["ingredients"] = self._canonicalize_ingredients(
                meal.get("ingredients", [])
            )
            canonicalized_meals.append(canonicalized_meal)
        
        return canonicalized_meals
    
    def _canonicalize_ingredients(self, ingredients: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Canonicalize all ingredients to raw forms"""
        canonicalized_ingredients = []
        
        for ingredient in ingredients:
            canonicalized_ingredient = self._canonicalize_single_ingredient(ingredient)
            canonicalized_ingredients.append(canonicalized_ingredient)
        
        return canonicalized_ingredients
    
    def _canonicalize_single_ingredient(self, ingredient: Dict[str, Any]) -> Dict[str, Any]:
        """
        Canonicalize a single ingredient from cooked to raw form.
        
        CANONICALIZATION RULES:
        1. Check if ingredient name indicates cooked/processed state
        2. Extract base ingredient name
        3. Apply cooked-to-raw conversion factor
        4. Rewrite ingredient name to canonical raw form
        5. Log the transformation
        """
        name = ingredient.get("name", "").lower().strip()
        quantity = ingredient.get("quantity", 0)
        unit = ingredient.get("unit", "g")
        
        logger.debug(f"[CANONICALIZATION_START] ingredient={name}")
        
        # Check if ingredient is cooked/processed
        if self._is_cooked_ingredient(name):
            # Extract base ingredient and convert to raw
            raw_name, raw_quantity = self._convert_cooked_to_raw(name, quantity)
            
            logger.info(
                "[CANONICALIZATION_MAP]",
                extra={
                    "original": name,
                    "canonical": raw_name,
                    "factor": raw_quantity / max(quantity, 0.1)  # Avoid division by zero
                }
            )
            
            canonicalized_ingredient = {
                **ingredient,
                "name": raw_name,
                "quantity": raw_quantity,
                "unit": unit,
                "canonicalization_applied": "cooked_to_raw",
                "original_name": name  # Keep for audit trail
            }
            
            logger.info(
                "[CANONICALIZATION_RESULT]",
                extra={
                    "final_name": raw_name,
                    "final_quantity": raw_quantity
                }
            )
            
            return canonicalized_ingredient
        
        else:
            # Ingredient is already in raw form
            logger.debug(f"[CANONICALIZATION_SKIP] ingredient={name} (already raw)")
            return ingredient
    
    def _is_cooked_ingredient(self, name: str) -> bool:
        """Check if ingredient is explicitly marked as cooked, processed, or frozen"""
        name_lower = name.lower()
        return any(indicator in name_lower for indicator in self.cooked_indicators)
    
    def _convert_cooked_to_raw(self, cooked_name: str, cooked_quantity: float) -> Tuple[str, float]:
        """Convert cooked ingredient to raw equivalent"""
        
        # Extract base ingredient name
        base_name = self._extract_base_ingredient(cooked_name)
        
        # Get conversion ratio
        ratio = self.cooked_to_raw_ratios.get(base_name, 1.0)
        
        # Convert quantity (cooked is typically heavier due to water absorption)
        raw_quantity = cooked_quantity / ratio
        
        # Round to integer to avoid decimal precision violations
        raw_quantity = round(raw_quantity)
        
        # Canonicalize the name to standard raw form
        canonical_raw_name = self._canonicalize_raw_name(base_name)
        
        # CRITICAL: Apply ingredient name normalizer to ensure exact DB key match
        normalized_name = ingredient_name_normalizer(canonical_raw_name)
        
        return normalized_name, raw_quantity
    
    def _extract_base_ingredient(self, cooked_name: str) -> str:
        """Extract base ingredient name from cooked description"""
        # Remove cooking method indicators and processing states
        clean_name = cooked_name.lower()
        for indicator in self.cooked_indicators:
            clean_name = clean_name.replace(indicator, '').strip()
        
        # Clean up extra spaces and common words
        clean_name = re.sub(r'\s+', ' ', clean_name)
        clean_name = clean_name.replace('(', '').replace(')', '')
        
        return clean_name.strip()
    
    def _canonicalize_raw_name(self, base_name: str) -> str:
        """
        Canonicalize base ingredient name to standard raw form.
        
        Examples:
        - "quinoa" → "quinoa (dry)"
        - "lentils green" → "lentils (green, dry)"
        - "rice" → "rice (dry)"
        """
        base_name = base_name.strip()
        
        # Grain canonicalization
        if "quinoa" in base_name:
            return "quinoa (dry)"
        elif "rice" in base_name:
            if "brown" in base_name:
                return "rice (brown, dry)"
            else:
                return "rice (dry)"
        elif "oats" in base_name:
            return "oats (rolled, dry)"
        elif "barley" in base_name:
            return "barley (dry)"
        elif "bulgur" in base_name:
            return "bulgur (dry)"
        
        # Legume canonicalization
        elif "lentils" in base_name or "lentil" in base_name:
            if "red" in base_name:
                return "lentils (red, dry)"
            elif "green" in base_name:
                return "lentils (green, dry)"
            else:
                return "lentils (dry)"
        elif "chickpeas" in base_name or "chickpea" in base_name:
            return "chickpeas (dry)"
        elif "black beans" in base_name:
            return "black beans (dry)"
        elif "kidney beans" in base_name:
            return "kidney beans (dry)"
        elif "white beans" in base_name:
            return "white beans (dry)"
        
        # Vegetable canonicalization (most vegetables don't change much when cooked)
        elif "broccoli" in base_name:
            return "broccoli"
        elif "spinach" in base_name:
            return "spinach"
        elif "kale" in base_name:
            return "kale"
        elif "mushrooms" in base_name or "mushroom" in base_name:
            return "mushrooms"
        elif "zucchini" in base_name:
            return "zucchini"
        elif "carrots" in base_name or "carrot" in base_name:
            return "carrots"
        elif "bell peppers" in base_name or "bell pepper" in base_name:
            return "bell peppers"
        
        # Protein canonicalization - ONLY VEGETARIAN PROTEINS
        elif "tofu" in base_name:
            if "extra" in base_name or "firm" in base_name:
                return "tofu (extra-firm)"
            else:
                return "tofu (extra-firm)"  # Default to extra-firm
        elif "tempeh" in base_name:
            return "tempeh"
        elif "chicken" in base_name or "meat" in base_name or "beef" in base_name or "pork" in base_name:
            # CRITICAL FIX: Non-vegetarian proteins not supported - use tofu as substitute
            logger.warning(f"Non-vegetarian protein '{base_name}' canonicalized to tofu (extra-firm)")
            return "tofu (extra-firm)"
        
        # Default: return as-is if no specific canonicalization rule
        else:
            return base_name
    
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
            'lentil': 2.5,      # Singular form
            'chickpeas': 2.5,
            'chickpea': 2.5,    # Singular form
            'black beans': 2.5,
            'kidney beans': 2.5,
            'white beans': 2.5,
            
            # Vegetables (minimal change, mostly water loss)
            'broccoli': 0.9,    # Slight water loss when cooked
            'spinach': 0.3,     # Significant volume reduction
            'kale': 0.4,
            'mushrooms': 0.7,
            'mushroom': 0.7,    # Singular form
            'zucchini': 0.9,
            'carrots': 0.95,
            'carrot': 0.95,     # Singular form
            'bell peppers': 0.9,
            'bell pepper': 0.9, # Singular form
            
            # Proteins (water loss during cooking)
            'chicken breast': 0.75,  # 100g cooked = ~133g raw
            'salmon': 0.8,
            'tofu': 0.9,        # Minimal change
            'tempeh': 0.95,
        }


def ingredient_name_normalizer(canonical_name: str) -> str:
    """
    DETERMINISTIC ingredient name normalizer to ensure exact DB key matches.
    
    This function maps canonical ingredient names to exact nutrition database keys.
    CRITICAL: Every canonical name must map to an existing database key.
    
    Args:
        canonical_name: Canonical ingredient name from canonicalizer
        
    Returns:
        Exact nutrition database key
    """
    # Direct mappings for exact matches
    name_mappings = {
        # Grains - ensure exact DB key matches
        "quinoa (dry)": "quinoa (dry)",
        "rice (dry)": "brown rice (dry)",  # Default rice to brown rice
        "rice (brown, dry)": "brown rice (dry)",
        "oats (rolled, dry)": "oats (rolled, dry)",
        "barley (dry)": "barley (pearled, dry)",
        "bulgur (dry)": "bulgur wheat (dry)",
        
        # Legumes - ensure exact DB key matches  
        "lentils (dry)": "lentils (red, dry)",  # Default to red lentils
        "lentils (red, dry)": "lentils (red, dry)",
        "lentils (green, dry)": "lentils (red, dry)",  # Map green to red (same nutrition)
        "chickpeas (dry)": "chickpeas (dry)",
        "black beans (dry)": "black beans (dry)",
        "kidney beans (dry)": "kidney beans (dry)",
        "white beans (dry)": "white beans (dry)",
        
        # Vegetables - ensure exact DB key matches
        "broccoli": "broccoli",
        "spinach": "spinach", 
        "kale": "kale",
        "mushrooms": "mushrooms (white)",
        "zucchini": "zucchini",
        "carrots": "carrots",
        "bell peppers": "bell peppers (mixed)",
        
        # Proteins - ONLY VEGETARIAN (map non-veg to tofu)
        "chicken breast (raw)": "tofu (extra-firm)",  # CRITICAL FIX
        "salmon (raw)": "tofu (extra-firm)",  # CRITICAL FIX
        "tofu": "tofu (extra-firm)",
        "tempeh": "tempeh",
        
        # Dairy
        "greek yogurt": "greek yogurt (plain)",
        "cottage cheese": "cottage cheese",
        "paneer": "paneer",
        "milk": "milk (whole)",
        "cheese": "cheese (cheddar)",
        
        # Nuts and seeds
        "almonds": "almonds",
        "walnuts": "walnuts",
        "cashews": "cashews",
        "peanuts": "peanuts",
        "sunflower seeds": "sunflower seeds",
        "pumpkin seeds": "pumpkin seeds",
        "chia seeds": "chia seeds",
        "flax seeds": "flax seeds",
        "hemp seeds": "hemp seeds",
        
        # Fruits
        "banana": "banana",
        "apple": "apple", 
        "berries": "mixed berries",
        "orange": "orange",
        
        # Oils and fats
        "olive oil": "olive oil",
        "coconut oil": "coconut oil",
        "almond butter": "almond butter",
        "peanut butter": "peanut butter",
    }
    
    # Check for exact mapping first
    if canonical_name in name_mappings:
        mapped_name = name_mappings[canonical_name]
        logger.debug(f"[INGREDIENT_NAME_NORMALIZER] '{canonical_name}' -> '{mapped_name}'")
        return mapped_name
    
    # If no exact mapping, return as-is (will be caught by nutrition lookup)
    logger.debug(f"[INGREDIENT_NAME_NORMALIZER] '{canonical_name}' -> '{canonical_name}' (no mapping)")
    return canonical_name


# Global canonicalizer instance
_ingredient_canonicalizer = None

def get_ingredient_canonicalizer() -> IngredientCanonicalizer:
    """Get the global ingredient canonicalizer instance"""
    global _ingredient_canonicalizer
    if _ingredient_canonicalizer is None:
        _ingredient_canonicalizer = IngredientCanonicalizer()
    return _ingredient_canonicalizer