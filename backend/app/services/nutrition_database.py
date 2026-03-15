"""
Nutrition Database Service - Single Source of Truth for Food Nutrition Data

This module provides the authoritative nutrition data for all foods.
ALL nutrition calculations must go through this service.
The LLM is NEVER the source of nutrition data.

CRITICAL RULE: Nutrition lookup must NEVER return 0 nutrition silently.
Unknown ingredients must raise IngredientResolutionError.
"""

from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

class ConfidenceLevel(Enum):
    """Confidence level for ingredient normalization"""
    EXACT = "exact"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class UnknownIngredientError(Exception):
    """Raised when an ingredient cannot be normalized/resolved"""
    def __init__(self, raw_name: str, normalized_attempt: str = None, removed_tokens: list = None):
        self.raw_name = raw_name
        self.normalized_attempt = normalized_attempt or raw_name
        self.removed_tokens = removed_tokens or []
        super().__init__(f"Unknown ingredient: {raw_name}")

logger = logging.getLogger(__name__)


def normalize_ingredient_name_for_lookup(name: str) -> str:
    """
    SAFE ingredient name normalization for nutrition lookup only.
    
    This function maps ingredient names to exact nutrition database keys
    to fix string normalization mismatches. NO HEURISTICS, NO AI.
    
    Args:
        name: Ingredient name to normalize
        
    Returns:
        Normalized name for database lookup
    """

    name = name.lower().strip()
    # Static mapping - exact matches only
    NAME_LOOKUP_MAP = {
        # Greek yogurt variations
        "greek yogurt plain": "greek yogurt (plain)",
        "greek yogurt": "greek yogurt (plain)",
        
        # Tofu variations  
        "tofu extrafirm": "tofu (extra-firm)",
        "tofu extra-firm": "tofu (extra-firm)",
        "tofu": "tofu (extra-firm)",
        
        # Lentil variations
        "lentils red dry": "lentils (red, dry)",
        "lentils red cooked": "lentils (red, cooked)",  # Add cooked mapping
        "lentils green dry": "lentils (red, dry)",  # Map green to red (same nutrition)
        "lentils green cooked": "lentils (green, cooked)",  # Add green cooked
        "lentils": "lentils (red, dry)",
        
        # Rice variations
        "rice dry": "brown rice (dry)",
        "rice": "brown rice (dry)",
        
        # Quinoa variations
        "quinoa dry": "quinoa (dry)",
        "quinoa": "quinoa (dry)",
        
        # Oats variations
        "oats rolled dry": "oats (rolled, dry)",
        "oats": "oats (rolled, dry)",
        
        # Chickpea variations
        "chickpeas dry": "chickpeas (dry)",
        "chickpeas": "chickpeas (dry)",
        
        # Bean variations
        "black beans dry": "black beans (dry)",
        "black beans": "black beans (dry)",
        "kidney beans dry": "kidney beans (dry)", 
        "kidney beans": "kidney beans (dry)",
        "white beans dry": "white beans (dry)",
        "white beans": "white beans (dry)",
        
        # Nut variations
        "almonds sliced": "almonds (sliced)",
        
        # Milk variations
        "milk whole": "milk (whole)",
        "milk": "milk (whole)",
        
        # Cheese variations
        "cheese cheddar": "cheese (cheddar)",
        "cheese": "cheese (cheddar)",
        
        # Egg variations
        "eggs whole": "eggs (whole)",
        "eggs": "eggs (whole)",
        
        # Protein powder variations
        "protein powder vanilla": "protein powder (vanilla)",
        "whey protein": "whey protein powder",
        
        # Mixed berries variations
        "berries mixed": "mixed berries",
        "berries": "mixed berries",
        
        # Brown rice variations
        "brown rice dry": "brown rice (dry)",
        "brown rice": "brown rice (dry)",
        
        # Mushroom variations
        "mushrooms white": "mushrooms (white)",
        "mushrooms": "mushrooms (white)",
        
        # Bell pepper variations
        "bell peppers mixed": "bell peppers (mixed)",

        # ======================
        # DAIRY & EGGS
        # ======================
        "eggs": "eggs (whole)",
        "eggs whole": "eggs (whole)",

        # ======================
        # CHICKEN (RAW)
        # ======================
        "chicken": "chicken breast (raw)",
        "chicken breast": "chicken breast (raw)",
        "chicken breast skinless": "chicken breast (raw)",
        "chicken breast (skinless)": "chicken breast (raw)",
        "skinless chicken breast": "chicken breast (raw)",
        "chicken thigh": "chicken thigh (raw)",
        "chicken drumstick": "chicken drumstick (raw)",
        "whole chicken": "whole chicken (raw)",

        # ======================
        # FISH (RAW)
        # ======================
        "salmon": "salmon (raw)",
        "salmon atlantic": "salmon (raw)",
        "salmon japan": "salmon (raw)",
        "salmon (atlantic)": "salmon (raw)",
        "salmon (atlantic, farmed)": "salmon (raw)",
        "salmon farmed": "salmon (raw)",
        "tuna": "tuna (raw)",
        "cod": "cod (raw)",
        "tilapia": "tilapia (raw)",
        "fish": "white fish (raw)",

        # ======================
        # SEAFOOD
        # ======================
        "shrimp": "shrimp (raw)",
        "prawns": "prawns (raw)",

    }
    
    return NAME_LOOKUP_MAP.get(name, name)


class IngredientResolutionError(Exception):
    """
    CRITICAL: Raised when ingredient cannot be resolved to nutrition data.
    
    This error prevents 0-calorie nutrition from reaching validation.
    Must be classified as 'ingredient_name_resolution_failure' for adaptive retry.
    """
    
    def __init__(self, ingredient_name: str, failure_reason: str, normalization_attempt: str = None):
        self.ingredient_name = ingredient_name
        self.failure_reason = failure_reason
        self.normalization_attempt = normalization_attempt
        self.classification = "ingredient_name_resolution_failure"
        
        super().__init__(
            f"Ingredient resolution failed: '{ingredient_name}' - {failure_reason}"
        )


class ProteinQuality(Enum):
    """Protein quality classification for vegetarian/vegan planning"""
    COMPLETE = "complete"      # Contains all essential amino acids
    INCOMPLETE = "incomplete"  # Missing some essential amino acids
    COMPLEMENTARY = "complementary"  # Pairs well with other proteins


@dataclass
class NutritionData:
    """Nutrition data per 100g RAW weight"""
    calories: float
    protein: float
    carbohydrates: float
    fat: float
    fiber: float
    sodium: float
    protein_quality: ProteinQuality
    
    def scale(self, weight_g: float) -> 'NutritionData':
        """Scale nutrition data for a specific weight in grams"""
        factor = weight_g / 100.0
        return NutritionData(
            calories=self.calories * factor,
            protein=self.protein * factor,
            carbohydrates=self.carbohydrates * factor,
            fat=self.fat * factor,
            fiber=self.fiber * factor,
            sodium=self.sodium * factor,
            protein_quality=self.protein_quality
        )


class NutritionDatabase:
    """
    Authoritative nutrition database.
    
    CRITICAL RULES:
    1. ALL weights are RAW weight unless explicitly stated
    2. ALL nutrition values are per 100g RAW weight
    3. LLM suggestions are NEVER used for nutrition calculations
    4. This is the ONLY source of nutrition truth
    """
    
    def __init__(self):
        self._foods = self._initialize_database()
        logger.info(f"Nutrition database initialized with {len(self._foods)} foods")
    
    def _initialize_database(self) -> Dict[str, NutritionData]:
        """Initialize the nutrition database with common foods"""
        
        # High-protein vegetarian sources (prioritized)
        foods = {
            # COMPLETE PROTEINS (Vegetarian)
            "greek yogurt (plain)": NutritionData(59, 10.0, 3.6, 0.4, 0, 36, ProteinQuality.COMPLETE),
            "cottage cheese": NutritionData(98, 11.1, 3.4, 4.3, 0, 364, ProteinQuality.COMPLETE),
            "paneer": NutritionData(265, 18.3, 1.2, 20.8, 0, 16, ProteinQuality.COMPLETE),
            "eggs (whole)": NutritionData(155, 13.0, 1.1, 11.0, 0, 124, ProteinQuality.COMPLETE),
            "egg whites": NutritionData(52, 10.9, 0.7, 0.2, 0, 166, ProteinQuality.COMPLETE),
            "milk (whole)": NutritionData(61, 3.2, 4.8, 3.3, 0, 40, ProteinQuality.COMPLETE),
            "cheese (cheddar)": NutritionData(402, 25.0, 1.3, 33.0, 0, 621, ProteinQuality.COMPLETE),
            
            # SOY PROTEINS (Complete)
            "tofu (extra-firm)": NutritionData(70, 8.1, 1.9, 4.2, 0.4, 7, ProteinQuality.COMPLETE),
            "extra-firm tofu": NutritionData(70, 8.1, 1.9, 4.2, 0.4, 7, ProteinQuality.COMPLETE),
            "tempeh": NutritionData(192, 19.0, 9.4, 11.0, 9.0, 9, ProteinQuality.COMPLETE),
            "edamame": NutritionData(121, 11.9, 8.9, 5.2, 5.2, 5, ProteinQuality.COMPLETE),
            "soy milk": NutritionData(33, 2.9, 1.2, 1.6, 0.4, 51, ProteinQuality.COMPLETE),
            
            # LEGUMES (Incomplete but high protein)
            "lentils (red, dry)": NutritionData(352, 24.6, 63.1, 1.1, 10.7, 6, ProteinQuality.INCOMPLETE),
            "lentils (red, cooked)": NutritionData(116, 9.0, 20.1, 0.4, 7.9, 2, ProteinQuality.INCOMPLETE),  # Cooked version
            "lentils (green, dry)": NutritionData(352, 25.8, 60.1, 1.1, 10.7, 6, ProteinQuality.INCOMPLETE),
            "lentils (green, cooked)": NutritionData(116, 9.0, 20.1, 0.4, 7.9, 2, ProteinQuality.INCOMPLETE),  # Cooked version
            "chickpeas (dry)": NutritionData(364, 19.3, 61.0, 6.0, 17.4, 24, ProteinQuality.INCOMPLETE),
            "roasted chickpeas": NutritionData(364, 19.3, 61.0, 6.0, 17.4, 24, ProteinQuality.INCOMPLETE),
            "black beans (dry)": NutritionData(341, 21.6, 62.4, 1.4, 15.5, 5, ProteinQuality.INCOMPLETE),
            "kidney beans (dry)": NutritionData(333, 23.6, 60.0, 0.8, 24.9, 24, ProteinQuality.INCOMPLETE),
            "white beans (dry)": NutritionData(333, 23.4, 60.3, 0.9, 15.2, 16, ProteinQuality.INCOMPLETE),
            "pinto beans (dry)": NutritionData(347, 21.4, 62.6, 1.2, 15.5, 12, ProteinQuality.INCOMPLETE),
            
            # NUTS & SEEDS (Incomplete but complementary)
            "almonds": NutritionData(579, 21.2, 21.6, 49.9, 12.5, 1, ProteinQuality.INCOMPLETE),
            "almonds (sliced)": NutritionData(579, 21.2, 21.6, 49.9, 12.5, 1, ProteinQuality.INCOMPLETE),
            "walnuts": NutritionData(654, 15.2, 13.7, 65.2, 6.7, 2, ProteinQuality.INCOMPLETE),
            "cashews": NutritionData(553, 18.2, 30.2, 43.9, 3.3, 12, ProteinQuality.INCOMPLETE),
            "peanuts": NutritionData(567, 25.8, 16.1, 49.2, 8.5, 18, ProteinQuality.INCOMPLETE),
            "chia seeds": NutritionData(486, 16.5, 42.1, 30.7, 34.4, 16, ProteinQuality.INCOMPLETE),
            "hemp seeds": NutritionData(553, 31.6, 8.7, 48.8, 4.0, 5, ProteinQuality.COMPLETE),
            "pumpkin seeds": NutritionData(559, 30.2, 10.7, 49.1, 6.0, 7, ProteinQuality.INCOMPLETE),
            "sunflower seeds": NutritionData(584, 20.8, 20.0, 51.5, 8.6, 9, ProteinQuality.INCOMPLETE),
            
            # GRAINS (Complementary proteins)
            "quinoa (dry)": NutritionData(368, 14.1, 64.2, 6.1, 7.0, 5, ProteinQuality.COMPLETE),
            "oats (rolled, dry)": NutritionData(389, 16.9, 66.3, 6.9, 10.6, 2, ProteinQuality.INCOMPLETE),
            "brown rice (dry)": NutritionData(370, 7.9, 77.2, 2.9, 3.5, 7, ProteinQuality.INCOMPLETE),
            "whole wheat flour": NutritionData(340, 13.2, 72.0, 2.5, 10.7, 2, ProteinQuality.INCOMPLETE),
            "buckwheat (dry)": NutritionData(343, 13.3, 71.5, 3.4, 10.0, 1, ProteinQuality.INCOMPLETE),
            "amaranth (dry)": NutritionData(371, 13.6, 65.3, 7.0, 6.7, 4, ProteinQuality.COMPLETE),
            
            # VEGETABLES (Low protein but important)
            "spinach": NutritionData(23, 2.9, 3.6, 0.4, 2.2, 79, ProteinQuality.INCOMPLETE),
            "spinach (fresh)": NutritionData(23, 2.9, 3.6, 0.4, 2.2, 79, ProteinQuality.INCOMPLETE),
            "broccoli": NutritionData(34, 2.8, 6.6, 0.4, 2.6, 33, ProteinQuality.INCOMPLETE),
            "steamed broccoli": NutritionData(34, 2.8, 6.6, 0.4, 2.6, 33, ProteinQuality.INCOMPLETE),
            "kale": NutritionData(49, 4.3, 8.8, 0.9, 3.6, 38, ProteinQuality.INCOMPLETE),
            "bell peppers": NutritionData(31, 1.0, 7.3, 0.3, 2.5, 4, ProteinQuality.INCOMPLETE),
            "tomatoes": NutritionData(18, 0.9, 3.9, 0.2, 1.2, 5, ProteinQuality.INCOMPLETE),
            "cucumber": NutritionData(16, 0.8, 3.6, 0.1, 0.5, 2, ProteinQuality.INCOMPLETE),  # Added cucumber
            "avocado": NutritionData(160, 2.0, 8.5, 14.7, 6.7, 7, ProteinQuality.INCOMPLETE),
            "sweet potato": NutritionData(86, 1.6, 20.1, 0.1, 3.0, 54, ProteinQuality.INCOMPLETE),
            "roasted sweet potato": NutritionData(86, 1.6, 20.1, 0.1, 3.0, 54, ProteinQuality.INCOMPLETE),
            "regular potato": NutritionData(77, 2.0, 17.5, 0.1, 2.1, 6, ProteinQuality.INCOMPLETE),
            
            # FRUITS (Low protein, carb sources)
            "banana": NutritionData(89, 1.1, 22.8, 0.3, 2.6, 1, ProteinQuality.INCOMPLETE),
            "apple": NutritionData(52, 0.3, 13.8, 0.2, 2.4, 1, ProteinQuality.INCOMPLETE),
            "berries (mixed)": NutritionData(57, 0.7, 14.5, 0.3, 2.4, 1, ProteinQuality.INCOMPLETE),
            "mixed berries": NutritionData(57, 0.7, 14.5, 0.3, 2.4, 1, ProteinQuality.INCOMPLETE),
            "orange": NutritionData(47, 0.9, 11.8, 0.1, 2.4, 0, ProteinQuality.INCOMPLETE),
            
            # FATS & OILS
            "olive oil": NutritionData(884, 0, 0, 100.0, 0, 2, ProteinQuality.INCOMPLETE),
            "coconut oil": NutritionData(862, 0, 0, 100.0, 0, 0, ProteinQuality.INCOMPLETE),
            "almond butter": NutritionData(614, 21.2, 18.8, 55.5, 10.3, 1, ProteinQuality.INCOMPLETE),
            "peanut butter": NutritionData(588, 25.1, 19.6, 50.4, 6.0, 17, ProteinQuality.INCOMPLETE),
            "tahini": NutritionData(595, 18.1, 18.0, 53.8, 9.3, 115, ProteinQuality.INCOMPLETE),
            
            # PLANT MILKS
            "almond milk": NutritionData(17, 0.6, 1.5, 1.1, 0.4, 63, ProteinQuality.INCOMPLETE),
            "oat milk": NutritionData(47, 1.0, 7.0, 1.5, 0.8, 101, ProteinQuality.INCOMPLETE),
            
            # PROTEIN POWDERS (Complete)
            "whey protein powder": NutritionData(354, 80.0, 7.0, 1.9, 0, 200, ProteinQuality.COMPLETE),
            "protein powder (vanilla)": NutritionData(354, 80.0, 7.0, 1.9, 0, 200, ProteinQuality.COMPLETE),
            "pea protein powder": NutritionData(373, 80.0, 7.0, 6.0, 6.0, 1200, ProteinQuality.INCOMPLETE),
            "hemp protein powder": NutritionData(374, 50.0, 8.0, 11.0, 40.0, 10, ProteinQuality.COMPLETE),
            
            # CONDIMENTS & SEASONINGS
            "nutritional yeast": NutritionData(325, 45.0, 35.0, 7.0, 20.0, 10, ProteinQuality.INCOMPLETE),
            "hummus": NutritionData(166, 8.0, 14.3, 9.6, 6.0, 379, ProteinQuality.INCOMPLETE),
            "salsa": NutritionData(36, 1.6, 7.0, 0.2, 1.4, 430, ProteinQuality.INCOMPLETE),
            "honey": NutritionData(304, 0.3, 82.4, 0, 0.2, 4, ProteinQuality.INCOMPLETE),
            "maple syrup": NutritionData(260, 0, 67.0, 0.2, 0, 12, ProteinQuality.INCOMPLETE),
            "cinnamon": NutritionData(247, 4.0, 81.0, 1.2, 53.1, 10, ProteinQuality.INCOMPLETE),
            "lemon juice": NutritionData(22, 0.4, 6.9, 0.2, 0.3, 2, ProteinQuality.INCOMPLETE),
            "soy sauce": NutritionData(8, 1.3, 0.8, 0, 0.1, 5493, ProteinQuality.INCOMPLETE),
            "sesame oil": NutritionData(884, 0, 0, 100.0, 0, 0, ProteinQuality.INCOMPLETE),
            "hemp seed oil": NutritionData(884, 0, 0, 100.0, 0, 0, ProteinQuality.INCOMPLETE),
            "mixed herbs (dried)": NutritionData(233, 9.0, 47.0, 4.3, 27.8, 76, ProteinQuality.INCOMPLETE),
            
            # COOKED GRAINS & LEGUMES (important for accurate portions)
            "cooked quinoa": NutritionData(120, 4.6, 21.3, 2.0, 2.3, 2, ProteinQuality.COMPLETE),
            "cooked brown rice": NutritionData(112, 2.3, 23.0, 0.9, 1.8, 5, ProteinQuality.INCOMPLETE),
            "cooked white rice": NutritionData(130, 2.7, 28.2, 0.3, 0.4, 5, ProteinQuality.INCOMPLETE),
            "red lentils (cooked)": NutritionData(116, 9.0, 20.1, 0.4, 7.9, 2, ProteinQuality.INCOMPLETE),
            "cooked red lentils": NutritionData(116, 9.0, 20.1, 0.4, 7.9, 2, ProteinQuality.INCOMPLETE),
            "green lentils (cooked)": NutritionData(116, 9.0, 20.1, 0.4, 7.9, 2, ProteinQuality.INCOMPLETE),
            "lentils (green, cooked)": NutritionData(116, 9.0, 20.1, 0.4, 7.9, 2, ProteinQuality.INCOMPLETE),
            "chickpeas (cooked)": NutritionData(164, 8.9, 27.4, 2.6, 7.6, 7, ProteinQuality.INCOMPLETE),
            "black beans (cooked)": NutritionData(132, 8.9, 23.7, 0.5, 8.7, 2, ProteinQuality.INCOMPLETE),
            
            # MIXED VEGETABLES (common in recipes)
            "roasted vegetables": NutritionData(45, 2.0, 9.0, 0.5, 3.0, 25, ProteinQuality.INCOMPLETE),
            "mixed vegetables": NutritionData(40, 2.0, 8.0, 0.3, 3.0, 20, ProteinQuality.INCOMPLETE),
            "chopped broccoli": NutritionData(34, 2.8, 6.6, 0.4, 2.6, 33, ProteinQuality.INCOMPLETE),
            "onions": NutritionData(40, 1.1, 9.3, 0.1, 1.7, 4, ProteinQuality.INCOMPLETE),
            "red onions": NutritionData(40, 1.1, 9.3, 0.1, 1.7, 4, ProteinQuality.INCOMPLETE),
            "yellow onions": NutritionData(40, 1.1, 9.3, 0.1, 1.7, 4, ProteinQuality.INCOMPLETE),
            
            # BREAD & WRAPS (common in meal plans)
            "whole wheat bread": NutritionData(247, 13.2, 41.0, 4.2, 6.0, 400, ProteinQuality.INCOMPLETE),
            "whole grain bread": NutritionData(247, 13.2, 41.0, 4.2, 6.0, 400, ProteinQuality.INCOMPLETE),
            "whole wheat tortilla": NutritionData(300, 9.0, 50.0, 8.0, 4.0, 600, ProteinQuality.INCOMPLETE),
            "whole wheat wrap": NutritionData(300, 9.0, 50.0, 8.0, 4.0, 600, ProteinQuality.INCOMPLETE),
            "whole wheat roti": NutritionData(300, 9.0, 50.0, 8.0, 4.0, 600, ProteinQuality.INCOMPLETE),
            "flour tortilla": NutritionData(300, 8.0, 48.0, 8.0, 3.0, 650, ProteinQuality.INCOMPLETE),
            "whole wheat buns": NutritionData(250, 12.0, 42.0, 4.0, 5.0, 420, ProteinQuality.INCOMPLETE),
            
            # ADDITIONAL VEGETABLES
            "mixed greens": NutritionData(20, 2.0, 4.0, 0.2, 2.0, 10, ProteinQuality.INCOMPLETE),
            "roasted bell peppers": NutritionData(35, 1.2, 8.0, 0.3, 2.8, 5, ProteinQuality.INCOMPLETE),
            "portobello mushrooms": NutritionData(22, 3.0, 3.9, 0.4, 1.3, 9, ProteinQuality.INCOMPLETE),
            "mushrooms": NutritionData(22, 3.0, 3.9, 0.4, 1.3, 9, ProteinQuality.INCOMPLETE),
            "cucumber": NutritionData(16, 0.7, 3.6, 0.1, 0.5, 2, ProteinQuality.INCOMPLETE),
            "lettuce": NutritionData(15, 1.4, 2.9, 0.2, 1.3, 28, ProteinQuality.INCOMPLETE),
            "tomato": NutritionData(18, 0.9, 3.9, 0.2, 1.2, 5, ProteinQuality.INCOMPLETE),
            "garlic": NutritionData(149, 6.4, 33.1, 0.5, 2.1, 17, ProteinQuality.INCOMPLETE),
            
            # BERRIES
            "blueberries": NutritionData(57, 0.7, 14.5, 0.3, 2.4, 1, ProteinQuality.INCOMPLETE),
            "strawberries": NutritionData(32, 0.7, 7.7, 0.3, 2.0, 1, ProteinQuality.INCOMPLETE),
            "raspberries": NutritionData(52, 1.2, 11.9, 0.7, 6.5, 1, ProteinQuality.INCOMPLETE),
            
            # ADDITIONAL CHEESE
            "feta cheese": NutritionData(264, 14.2, 4.1, 21.3, 0, 917, ProteinQuality.COMPLETE),
            "goat cheese": NutritionData(364, 21.6, 2.5, 29.8, 0, 515, ProteinQuality.COMPLETE),
            "mozzarella cheese": NutritionData(300, 22.2, 2.2, 22.4, 0, 627, ProteinQuality.COMPLETE),
            
            # GENERIC SAFETY FALLBACKS (minimal nutrition for unknown ingredients)
            "seeds (generic)": NutritionData(550, 20.0, 20.0, 45.0, 10.0, 5, ProteinQuality.INCOMPLETE),
            "nuts (generic)": NutritionData(600, 15.0, 15.0, 55.0, 8.0, 5, ProteinQuality.INCOMPLETE),
            "vegetables (generic)": NutritionData(25, 2.0, 5.0, 0.2, 3.0, 10, ProteinQuality.INCOMPLETE),
            "legumes (generic)": NutritionData(120, 8.0, 20.0, 1.0, 8.0, 5, ProteinQuality.INCOMPLETE),
            "grains (generic)": NutritionData(350, 10.0, 70.0, 2.0, 5.0, 5, ProteinQuality.INCOMPLETE),

            # ============================
            # NON-VEGETARIAN – RAW PROTEINS
            # ============================

            # POULTRY (RAW)
            "chicken breast (raw)": NutritionData(120, 22.5, 0.0, 2.6, 0.0, 74, ProteinQuality.COMPLETE),
            "chicken thigh (raw)": NutritionData(177, 18.0, 0.0, 12.0, 0.0, 83, ProteinQuality.COMPLETE),
            "chicken drumstick (raw)": NutritionData(161, 18.3, 0.0, 9.2, 0.0, 86, ProteinQuality.COMPLETE),
            "whole chicken (raw)": NutritionData(143, 18.0, 0.0, 7.5, 0.0, 82, ProteinQuality.COMPLETE),

            # FATTY FISH (RAW)
            "salmon (raw)": NutritionData(208, 20.4, 0.0, 13.4, 0.0, 59, ProteinQuality.COMPLETE),
            "mackerel (raw)": NutritionData(205, 18.6, 0.0, 13.9, 0.0, 90, ProteinQuality.COMPLETE),
            "sardines (raw)": NutritionData(208, 24.6, 0.0, 11.5, 0.0, 307, ProteinQuality.COMPLETE),

            # LEAN FISH (RAW)
            "tuna (raw)": NutritionData(144, 23.3, 0.0, 4.9, 0.0, 39, ProteinQuality.COMPLETE),
            "cod (raw)": NutritionData(82, 18.0, 0.0, 0.7, 0.0, 54, ProteinQuality.COMPLETE),
            "tilapia (raw)": NutritionData(96, 20.1, 0.0, 1.7, 0.0, 56, ProteinQuality.COMPLETE),
            "white fish (raw)": NutritionData(82, 18.0, 0.0, 0.7, 0.0, 60, ProteinQuality.COMPLETE),

            # SEAFOOD (RAW)
            "shrimp (raw)": NutritionData(99, 24.0, 0.2, 0.3, 0.0, 111, ProteinQuality.COMPLETE),
            "prawns (raw)": NutritionData(97, 23.8, 0.0, 0.3, 0.0, 119, ProteinQuality.COMPLETE),

            # EGGS (RAW – already present, kept for completeness)
            "eggs (whole)": NutritionData(155, 13.0, 1.1, 11.0, 0.0, 124, ProteinQuality.COMPLETE),
            "egg whites": NutritionData(52, 10.9, 0.7, 0.2, 0.0, 166, ProteinQuality.COMPLETE),

        }
        
        return foods
    
    def get_nutrition(self, food_name: str, weight_g: float) -> Optional[NutritionData]:
        """
        Get nutrition data for a specific food and weight.
        
        CRITICAL: This method must NEVER return None silently.
        Unknown ingredients must raise UnknownIngredientError.
        
        Args:
            food_name: Name of the food (will be normalized)
            weight_g: Weight in grams (RAW weight)
        
        Returns:
            NutritionData scaled to the specified weight
            
        Raises:
            UnknownIngredientError: If ingredient cannot be resolved after normalization
        """
        # MANDATORY LOG: Input to nutrition lookup
        logger.info(f"[NUTRITION_LOOKUP_INPUT] name='{food_name}' qty={weight_g} unit=g")
        
        # MANDATORY: Normalize ingredient name (minimal fallback)
        canonical_name = normalize_ingredient_name_for_lookup(food_name)
        
        logger.info(
            "[NORMALIZED_FALLBACK] '%s' -> '%s'",
            food_name,
            canonical_name
        )
        
        # Look up normalized ingredient in database
        # SAFE FIX: Apply name normalization for exact database key matching
        lookup_name = normalize_ingredient_name_for_lookup(canonical_name)
        
        # NORMALIZATION FALLBACK GUARD: If normalized name doesn't exist, fall back to original
        if lookup_name not in self._foods:
            logger.warning(
                "[NUTRITION_NORMALIZATION_FALLBACK] "
                "normalized='%s' not found, falling back to original='%s'",
                lookup_name,
                canonical_name
            )
            lookup_name = canonical_name
        
        # NON-BREAKING LOG: Show input, lookup name, and result
        logger.info(
            "[NUTRITION_LOOKUP] input='%s' lookup='%s' found=%s",
            canonical_name,
            lookup_name,
            lookup_name in self._foods
        )
        
        if lookup_name in self._foods:
            base_nutrition = self._foods[lookup_name]
            scaled_nutrition = base_nutrition.scale(weight_g)
            
            # MANDATORY LOG: Nutrition lookup result
            logger.info(f"[NUTRITION_LOOKUP_RESULT] calories={scaled_nutrition.calories:.1f} protein={scaled_nutrition.protein:.1f}g")
            
            # HARD ASSERTION: Check for zero nutrition
            if scaled_nutrition.calories == 0 and weight_g > 0:
                logger.critical(f"[NUTRITION_LOOKUP_MISS] ingredient={food_name} - ZERO CALORIES WITH NON-ZERO QUANTITY")
                raise RuntimeError(f"CRITICAL: Ingredient nutrition resolution failed for '{food_name}' - got zero calories with {weight_g}g quantity")
            
            logger.debug(
                "[NUTRITION_FOUND] %s %sg = %.1f cal, %.1f protein",
                canonical_name,
                weight_g,
                scaled_nutrition.calories,
                scaled_nutrition.protein
            )
            
            return scaled_nutrition
        
        # CRITICAL: If normalized ingredient not in database, this is a system error
        logger.error(
            "[SYSTEM_ERROR] Normalized ingredient '%s' not in database. Original='%s'",
            lookup_name,
            food_name
        )
        
        # MANDATORY LOG: Nutrition lookup miss
        logger.error(f"[NUTRITION_LOOKUP_MISS] ingredient={food_name}")
        
        # Raise error instead of returning None
        raise UnknownIngredientError(
            raw_name=food_name,
            normalized_attempt=canonical_name,
            removed_tokens=[]
        )
    
    def search_foods(self, query: str) -> List[str]:
        """Search for foods matching a query"""
        query = query.lower().strip()
        matches = [name for name in self._foods.keys() if query in name]
        return sorted(matches)
    
    def get_high_protein_foods(self, min_protein_per_100g: float = 15.0) -> List[Tuple[str, float]]:
        """Get foods with high protein content"""
        high_protein = []
        for name, nutrition in self._foods.items():
            if nutrition.protein >= min_protein_per_100g:
                high_protein.append((name, nutrition.protein))
        
        return sorted(high_protein, key=lambda x: x[1], reverse=True)
    
    def get_complete_proteins(self) -> List[str]:
        """Get foods that are complete protein sources"""
        return [name for name, nutrition in self._foods.items() 
                if nutrition.protein_quality == ProteinQuality.COMPLETE]
    
    def validate_food_exists(self, food_name: str) -> bool:
        """Check if a food exists in the database"""
        return food_name.lower().strip() in self._foods
    
    def get_all_food_names(self) -> List[str]:
        """
        Get all food names in the database for LLM input contract enforcement.
        
        Returns:
            Sorted list of all food names in the database
        """
        return sorted(list(self._foods.keys()))
    
    def get_allowed_ingredients_prompt(self) -> str:
        """
        Generate a prompt section with allowed ingredients for LLM input contract enforcement.
        
        This constrains the LLM to ONLY use ingredients that exist in the nutrition database,
        preventing unknown ingredient errors and zero-calorie plans.
        
        Returns:
            Formatted prompt section with allowed ingredients
        """
        all_foods = self.get_all_food_names()
        
        # Group foods by category for better LLM understanding
        proteins = [f for f in all_foods if any(keyword in f for keyword in [
            'protein', 'tofu', 'tempeh', 'yogurt', 'cheese', 'egg', 'milk', 'beans', 'lentils', 
            'chickpeas', 'nuts', 'seeds', 'quinoa', 'hemp', 'pea protein', 'whey'
        ])]
        
        grains = [f for f in all_foods if any(keyword in f for keyword in [
            'rice', 'oats', 'bread', 'flour', 'quinoa', 'buckwheat', 'amaranth', 'tortilla', 
            'wrap', 'roti', 'buns'
        ])]
        
        vegetables = [f for f in all_foods if any(keyword in f for keyword in [
            'spinach', 'broccoli', 'kale', 'peppers', 'tomato', 'avocado', 'potato', 'onion',
            'mushroom', 'cucumber', 'lettuce', 'garlic', 'vegetables', 'greens'
        ])]
        
        fruits = [f for f in all_foods if any(keyword in f for keyword in [
            'banana', 'apple', 'berries', 'orange', 'strawberries', 'blueberries', 'raspberries'
        ])]
        
        fats_oils = [f for f in all_foods if any(keyword in f for keyword in [
            'oil', 'butter', 'tahini', 'almond milk', 'oat milk', 'soy milk'
        ])]

        non_veg = [f for f in all_foods if any(keyword in f for keyword in [
            'chicken', 'salmon', 'tuna', 'fish', 'shrimp', 'prawns', 'mackerel', 'sardines'
        ])]
        
        # Create formatted prompt section
        prompt_section = """
CRITICAL INPUT CONTRACT - ALLOWED INGREDIENTS ONLY:

You MUST ONLY use ingredients from this exact list. Using any ingredient not on this list will cause system failure.

HIGH-PROTEIN SOURCES (prioritize these):
""" + ", ".join(proteins[:20]) + """

GRAINS & CARBS:
""" + ", ".join(grains[:15]) + """

VEGETABLES:
""" + ", ".join(vegetables[:15]) + """

FRUITS:
""" + ", ".join(fruits[:10]) + """

FATS & OILS:
""" + ", ".join(fats_oils[:10]) + """

NON-VEGETARIAN RAW PROTEINS (ONLY if diet_type = non_vegetarian):
""" + ", ".join(non_veg[:15]) + """

IMPORTANT:
- Do NOT add region, origin, breed, or preparation labels
- Always use canonical names exactly as listed
- Example: use "salmon (raw)", NOT "salmon japan" or "atlantic salmon"

CRITICAL RULES:
- Use EXACT ingredient names from the lists above
- Do NOT modify ingredient names (no "organic", "fresh", "raw" prefixes)
- Do NOT use generic terms like "berries", "seeds", "yogurt" - use specific ones
- Do NOT use brand names like "Trader Joe's" - use generic ingredient names
- If you need an ingredient not listed, choose the closest alternative from the list

EXAMPLES OF CORRECT USAGE:
✓ "greek yogurt (plain)" (not "yogurt" or "organic greek yogurt")
✓ "hemp seeds" (not "hemp" or "hemp hearts")
✓ "whole wheat wrap" (not "wrap" or "tortilla wrap")
✓ "berries (mixed)" (not "berries" or "fresh berries")
"""
        
        return prompt_section


# Global nutrition database instance
_nutrition_db = None

def get_nutrition_database() -> NutritionDatabase:
    """Get the global nutrition database instance"""
    global _nutrition_db
    if _nutrition_db is None:
        _nutrition_db = NutritionDatabase()
    return _nutrition_db