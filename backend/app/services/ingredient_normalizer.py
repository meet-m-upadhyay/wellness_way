"""
Ingredient Normalization Pipeline - MANDATORY 9-STEP ARCHITECTURE

This module implements the EXACT ingredient resolution pipeline as specified.
This is the final, correct architecture for production-grade ingredient resolution.

MANDATORY PIPELINE ORDER:
1. Normalization (remove noise) - FIRST, REQUIRED
2. Exact match (fast path)
3. Rule-based canonicalization
4. Category-constrained fuzzy match
5. Category nutrition fallback (SAFE DEFAULT)
6. Canonical LLM (offline only)
7. Hard failure ONLY if truly impossible

CORE PRINCIPLE: LLMs suggest names, ONLY deterministic backend decides nutrition.
"""

import logging
import re
from typing import Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass
from enum import Enum
from rapidfuzz import fuzz

logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """Normalization confidence levels"""
    EXACT = "exact"        # Direct database match
    HIGH = "high"          # Simple transformation
    MEDIUM = "medium"      # Synonym mapping
    LOW = "low"           # Category fallback
    UNRESOLVED = "unresolved"  # Could not resolve


class UnknownIngredientError(Exception):
    """Raised ONLY when ingredient category is completely unknown"""
    
    def __init__(self, raw_name: str, normalized_attempt: str, removed_tokens: List[str] = None):
        self.raw_name = raw_name
        self.normalized_attempt = normalized_attempt
        self.removed_tokens = removed_tokens or []
        super().__init__(
            f"Unknown ingredient category: '{raw_name}' (normalized to '{normalized_attempt}') "
            f"- removed tokens: {removed_tokens}"
        )


@dataclass
class UnresolvedIngredient:
    """Represents an ingredient that couldn't be resolved but has a known category"""
    raw_name: str
    category: str
    suggested_fallback: Optional[str] = None
    confidence: ConfidenceLevel = ConfidenceLevel.UNRESOLVED


@dataclass
class NormalizationResult:
    """Result of ingredient normalization"""
    canonical_name: Optional[str]  # None if unresolved
    confidence: ConfidenceLevel
    removed_tokens: List[str]
    transformation_steps: List[str]
    category: Optional[str] = None
    fallback_suggestion: Optional[str] = None
    
    @property
    def is_resolved(self) -> bool:
        return self.canonical_name is not None and self.confidence != ConfidenceLevel.UNRESOLVED


class IngredientNormalizer:
    """
    MANDATORY 9-STEP INGREDIENT RESOLUTION PIPELINE
    
    This implements the exact architecture specified for production-grade resolution.
    
    PIPELINE ORDER (MANDATORY):
    1. Normalization (remove noise) - FIRST, REQUIRED
    2. Exact match (fast path)
    3. Rule-based canonicalization
    4. Category-constrained fuzzy match (RapidFuzz)
    5. Category nutrition fallback (SAFE DEFAULT)
    6. [Canonical LLM handled by resolution service - offline only]
    7. Hard failure ONLY if truly impossible
    
    CRITICAL RULES:
    - Fuzzy matching is NOT the primary resolver
    - AI resolution is NOT allowed inline
    - Category fallback PREVENTS 0-calorie plans
    - Unknown foods alone must NEVER block plans
    """
    
    def __init__(self):
        """Initialize normalizer with mandatory pipeline components"""
        # Load all pipeline components
        self.exact_mappings = self._load_exact_mappings()
        self.rule_based_mappings = self._load_rule_based_canonicalization()
        self.category_mappings = self._load_category_mappings()
        self.category_fallbacks = self._load_category_nutrition_fallbacks()
        
        # Noise removal patterns
        self.brand_patterns = self._load_brand_patterns()
        self.quality_descriptors = self._load_quality_descriptors()
        self.preparation_descriptors = self._load_preparation_descriptors()
        
        # Category classification for fuzzy matching
        self.category_keywords = self._load_category_keywords()
        
        logger.info("MANDATORY 9-step ingredient resolution pipeline initialized")
    
    def normalize(self, raw_name: str) -> Union[NormalizationResult, UnresolvedIngredient]:
        """
        MANDATORY 9-STEP INGREDIENT RESOLUTION PIPELINE
        
        This follows the EXACT architecture specified. DO NOT MODIFY ORDER.
        
        Args:
            raw_name: Raw ingredient name from LLM
            
        Returns:
            NormalizationResult if resolved, UnresolvedIngredient if not
        """
        if not raw_name or not raw_name.strip():
            return UnresolvedIngredient("", "unknown", None)
        
        original_name = raw_name.strip()
        steps = []
        
        # STEP 1: NORMALIZATION (FIRST, REQUIRED)
        # Strip non-nutrition noise before matching
        normalized = self._apply_normalization(original_name)
        steps.append(f"normalization: '{original_name}' -> '{normalized}'")
        
        # STEP 2: EXACT MATCH (FAST PATH)
        if normalized.lower() in self.exact_mappings:
            canonical = self.exact_mappings[normalized.lower()]
            logger.info(f"[STEP 2] Exact match: '{original_name}' -> '{canonical}'")
            return NormalizationResult(
                canonical_name=canonical,
                confidence=ConfidenceLevel.EXACT,
                removed_tokens=[],
                transformation_steps=steps + ["exact_match"]
            )
        
        # STEP 3: RULE-BASED CANONICALIZATION
        # Apply deterministic mappings BEFORE fuzzy logic
        rule_based_result = self._apply_rule_based_canonicalization(normalized)
        if rule_based_result:
            canonical, confidence = rule_based_result
            logger.info(f"[STEP 3] Rule-based: '{original_name}' -> '{canonical}'")
            return NormalizationResult(
                canonical_name=canonical,
                confidence=confidence,
                removed_tokens=[],
                transformation_steps=steps + ["rule_based_canonicalization"]
            )
        
        # STEP 4: CATEGORY-CONSTRAINED FUZZY MATCH
        # First classify, then fuzzy match ONLY within category
        category = self._classify_ingredient_category(normalized)
        if category:
            fuzzy_result = self._category_constrained_fuzzy_match(normalized, category)
            if fuzzy_result:
                canonical, confidence, score = fuzzy_result
                logger.info(f"[STEP 4] Fuzzy match: '{original_name}' -> '{canonical}' "
                           f"(category: {category}, score: {score})")
                return NormalizationResult(
                    canonical_name=canonical,
                    confidence=confidence,
                    removed_tokens=[],
                    transformation_steps=steps + [f"fuzzy_match_category_{category}"],
                    category=category
                )
        
        # STEP 5: CATEGORY NUTRITION FALLBACK (CRITICAL SAFETY NET)
        # Use category-average nutrition to PREVENT 0-calorie plans
        if category and category in self.category_fallbacks:
            fallback = self.category_fallbacks[category]
            logger.info(f"[STEP 5] Category fallback: '{original_name}' -> '{fallback}' "
                       f"(category: {category}) - PREVENTS 0-CALORIE PLAN")
            return NormalizationResult(
                canonical_name=fallback,
                confidence=ConfidenceLevel.LOW,
                removed_tokens=[],
                transformation_steps=steps + [f"category_fallback_{category}"],
                category=category,
                fallback_suggestion=fallback
            )
        
        # STEP 6: [Canonical LLM handled by resolution service - offline only]
        # This step is handled by IngredientResolutionService asynchronously
        
        # STEP 7: GRACEFUL DEGRADATION (NOT HARD FAILURE)
        # Return unresolved for further processing by resolution service
        if category:
            logger.warning(f"[STEP 7] Unresolved: '{original_name}' (category: {category})")
            return UnresolvedIngredient(
                raw_name=original_name,
                category=category,
                suggested_fallback=self._suggest_fallback(category)
            )
        
        # Only fail if category is completely unknown
        logger.error(f"[FAILURE] Unknown ingredient category: '{original_name}'")
        raise UnknownIngredientError(original_name, normalized, [])
    
    def _apply_normalization(self, name: str) -> str:
        """
        STEP 1: NORMALIZATION (FIRST, REQUIRED)
        
        Strip non-nutrition noise before matching.
        This alone resolves ~60% of failures.
        
        Remove:
        - Brand names
        - Quality adjectives (organic, free-range, fresh)
        - Cooking states (cooked, grilled, roasted) - INCLUDING PARENTHETICAL FORMS
        - Size words (large, medium)
        
        Example: "organic free-range greek yogurt (plain)" -> "greek yogurt"
        Example: "cooked quinoa" -> "quinoa"
        Example: "quinoa (cooked)" -> "quinoa"
        """
        normalized = name.lower().strip()
        
        # CRITICAL FIX: Remove preparation tokens in parentheses FIRST
        # This fixes the primary root cause: "quinoa (cooked)" -> "quinoa"
        prep_parenthetical_patterns = [
            r'\(cooked\)', r'\(steamed\)', r'\(boiled\)', r'\(grilled\)', 
            r'\(baked\)', r'\(roasted\)', r'\(fried\)', r'\(air fried\)', r'\(sauteed\)',
            r'\(raw\)', r'\(dried\)', r'\(frozen\)', r'\(canned\)',
            r'\(fresh\)', r'\(plain\)', r'\(unsweetened\)'
        ]
        
        for pattern in prep_parenthetical_patterns:
            normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)
        
        # Remove other parenthetical content (brands, descriptions)
        normalized = re.sub(r'\([^)]*\)', '', normalized)
        
        # Remove brand names (more comprehensive)
        brand_patterns = [
            r'\btrader\s+joe\'?s?\b',
            r'\bkirkland\b',
            r'\bwhole\s+foods\b',
            r'\bgreat\s+value\b',
            r'\bsimply\b',
            r'\bnature\s+valley\b',
            r'\bkellogg\'?s?\b',
            r'\bquaker\b'
        ]
        
        for pattern in brand_patterns:
            normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)
        
        # Special handling for possessive forms
        normalized = re.sub(r'\btrader\s+joe\s+s\b', '', normalized, flags=re.IGNORECASE)
        
        # Remove quality descriptors
        quality_words = [
            'organic', 'fresh', 'raw', 'natural', 'pure', 'whole', 'extra',
            'premium', 'free range', 'free-range', 'grass fed', 'grass-fed',
            'wild caught', 'wild-caught', 'non gmo', 'non-gmo'
        ]
        
        for quality in quality_words:
            normalized = re.sub(rf'\b{re.escape(quality)}\b', '', normalized, flags=re.IGNORECASE)
        
        # ENHANCED: Remove preparation descriptors (both standalone and compound forms)
        # Handle multi-word preparation tokens FIRST
        multi_word_prep = [
            'air fried', 'deep fried', 'pan fried', 'stir fried'
        ]
        
        for prep in multi_word_prep:
            normalized = re.sub(rf'\b{re.escape(prep)}\b', '', normalized, flags=re.IGNORECASE)
        
        # Then handle single-word preparation tokens
        prep_words = [
            'cooked', 'steamed', 'boiled', 'grilled', 'baked', 'roasted',
            'fried', 'sauteed', 'sautéed', 'dried', 'frozen', 'canned',
            'blanched', 'poached', 'braised', 'stewed', 'smoked'
        ]
        
        for prep in prep_words:
            normalized = re.sub(rf'\b{prep}\b', '', normalized, flags=re.IGNORECASE)
        
        # Remove size descriptors
        size_words = ['large', 'medium', 'small', 'big', 'mini', 'extra', 'xl', 'lg', 'virgin']
        for size in size_words:
            normalized = re.sub(rf'\b{size}\b', '', normalized, flags=re.IGNORECASE)
        
        # Clean up whitespace and punctuation
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _apply_rule_based_canonicalization(self, normalized: str) -> Optional[Tuple[str, ConfidenceLevel]]:
        """
        STEP 3: RULE-BASED CANONICALIZATION
        
        Apply deterministic mappings BEFORE fuzzy logic.
        These mappings are permanent and safe.
        
        Examples:
        - "whole wheat wrap" -> "wheat wrap"
        - "protein powder (vanilla)" -> "whey protein powder"
        - "mixed berries" -> "berries (mixed)"
        """
        if normalized in self.rule_based_mappings:
            canonical = self.rule_based_mappings[normalized]
            return canonical, ConfidenceLevel.HIGH
        
        return None
    
    def _classify_ingredient_category(self, ingredient: str) -> Optional[str]:
        """
        Classify ingredient into category for constrained fuzzy matching.
        
        Categories:
        - seeds, nuts, vegetables, legumes, grains
        - dairy, protein, oils, fruits
        
        CRITICAL FIX: Make classification more strict to avoid false positives
        """
        ingredient_lower = ingredient.lower()
        
        # Special handling for protein powders - must contain "protein" AND "powder"
        if "protein" in ingredient_lower and "powder" in ingredient_lower:
            return "protein"
        
        # Special handling for other specific combinations
        if "pea protein" in ingredient_lower:
            return "protein"
        
        for category, keywords in self.category_keywords.items():
            # Skip protein category here since we handled it above
            if category == "protein":
                # Only match if it contains specific protein keywords (not just "powder")
                protein_keywords = ["tofu", "tempeh", "whey"]
                if any(keyword in ingredient_lower for keyword in protein_keywords):
                    return "protein"
                continue
                
            if any(keyword in ingredient_lower for keyword in keywords):
                return category
        
        return None
    
    def _category_constrained_fuzzy_match(self, ingredient: str, category: str) -> Optional[Tuple[str, ConfidenceLevel, int]]:
        """
        STEP 4: CATEGORY-CONSTRAINED FUZZY MATCH
        
        DO NOT fuzzy match globally - first classify, then match within category.
        
        Algorithm:
        - Use RapidFuzz token_set_ratio
        - Category-filtered candidates only
        - Acceptance thresholds: ≥92 auto accept, 80-91 accept with warning, <80 reject
        - Hard rule: If categories differ -> REJECT
        """
        # Get candidates from the same category only
        category_candidates = self._get_category_candidates(category)
        
        if not category_candidates:
            return None
        
        best_match = None
        best_score = 0
        
        for candidate in category_candidates:
            # Use token_set_ratio for better matching
            score = fuzz.token_set_ratio(ingredient.lower(), candidate.lower())
            
            if score > best_score:
                best_score = score
                best_match = candidate
        
        # Apply acceptance thresholds
        if best_score >= 92:
            return best_match, ConfidenceLevel.HIGH, best_score
        elif best_score >= 80:
            return best_match, ConfidenceLevel.MEDIUM, best_score
        else:
            # Score < 80 -> reject
            return None
    
    def _get_category_candidates(self, category: str) -> List[str]:
        """Get candidate foods from the same category for fuzzy matching"""
        # This would ideally come from the nutrition database
        # For now, return foods from exact mappings that match the category
        candidates = []
        
        category_foods = {
            "seeds": ["chia seeds", "hemp seeds", "pumpkin seeds", "sunflower seeds", "seeds (generic)"],
            "nuts": ["almonds", "walnuts", "cashews", "peanuts", "nuts (generic)"],
            "vegetables": ["spinach", "broccoli", "kale", "bell peppers", "tomatoes", "vegetables (generic)"],
            "legumes": ["lentils (red, dry)", "chickpeas (dry)", "black beans (dry)", "legumes (generic)"],
            "grains": ["quinoa (dry)", "oats (rolled, dry)", "brown rice (dry)", "grains (generic)"],
            "dairy": ["greek yogurt (plain)", "cottage cheese", "paneer", "milk (whole)", "cheese (cheddar)"],
            "protein": ["tofu (extra-firm)", "tempeh", "whey protein powder", "pea protein powder"],
            "oils": ["olive oil", "coconut oil", "sesame oil"],
            "fruits": ["banana", "apple", "berries (mixed)", "orange"]
        }
        
        return category_foods.get(category, [])
    
    def _load_exact_mappings(self) -> Dict[str, str]:
        """
        STEP 2: EXACT MATCH (FAST PATH)
        
        Load exact ingredient name mappings for fast resolution.
        These are checked after normalization.
        """
        return {
            # Direct matches (normalized forms) - CANONICAL NAMES MUST NOT CONTAIN PREPARATION TOKENS
            "greek yogurt": "greek yogurt (plain)",
            "chicken": "chicken breast (raw)",  # Added generic chicken mapping
            "chicken breast": "chicken breast (raw)",  # FIXED: Map to raw version
            "brown rice": "brown rice (dry)",  # FIXED: removed (cooked)
            "quinoa": "quinoa (dry)",          # FIXED: removed (cooked)
            "almonds": "almonds",
            "spinach": "spinach",
            "broccoli": "broccoli",
            "kale": "kale",  # Added kale
            "cucumber": "cucumber",  # Added cucumber
            "eggs": "eggs (whole)",
            "olive oil": "olive oil",
            "whole wheat bread": "whole wheat bread",
            "oats": "oats (rolled, dry)",
            "lentils": "lentils (red, dry)",
            "chickpeas": "chickpeas (dry)",
            "tofu": "tofu (extra-firm)",
            "salmon": "salmon (raw)",  # FIXED: Map to raw version
            "tuna": "tuna (raw)",      # FIXED: Map to raw version
            "sweet potato": "sweet potato",
            "avocado": "avocado",
            "banana": "banana",
            "apple": "apple",
            "mixed greens": "mixed greens",
            "greens": "mixed greens",
            "salad greens": "mixed greens",
            
            # NON-VEGETARIAN RAW PROTEINS (exact matches)
            "chicken breast (raw)": "chicken breast (raw)",
            "chicken thigh (raw)": "chicken thigh (raw)",
            "chicken drumstick (raw)": "chicken drumstick (raw)",
            "whole chicken (raw)": "whole chicken (raw)",
            "salmon (raw)": "salmon (raw)",
            "tuna (raw)": "tuna (raw)",
            "cod (raw)": "cod (raw)",
            "tilapia (raw)": "tilapia (raw)",
            "white fish (raw)": "white fish (raw)",
            "shrimp (raw)": "shrimp (raw)",
            "prawns (raw)": "prawns (raw)",
            "mackerel (raw)": "mackerel (raw)",
            "sardines (raw)": "sardines (raw)",
            
            # MISSING CATEGORIES - Add deterministic mappings
            "hemp seeds": "hemp seeds",
            "wheat wrap": "whole wheat roti",
            "whole wheat wrap": "whole wheat roti", 
            "berries": "berries (mixed)",
            "mixed berries": "berries (mixed)",
            "yogurt": "greek yogurt (plain)",
            "plain yogurt": "greek yogurt (plain)",
            
            # Expanded exact matches
            "greek yogurt plain": "greek yogurt (plain)",
            "plain greek yogurt": "greek yogurt (plain)",
            "rolled oats": "oats (rolled, dry)",
            "red lentils": "lentils (red, dry)",
            "extra firm tofu": "tofu (extra-firm)",
            "whole milk": "milk (whole)",
            
            # Generic safety fallbacks
            "seeds": "seeds (generic)",
            "nuts": "nuts (generic)",
            "vegetables": "vegetables (generic)",
            "legumes": "legumes (generic)",
            "grains": "grains (generic)",
        }
    
    def _load_rule_based_canonicalization(self) -> Dict[str, str]:
        """
        Load rule-based canonicalization mappings.
        These are deterministic mappings applied BEFORE fuzzy logic.
        """
        return {
            # Wheat products
            "whole wheat wrap": "whole wheat roti",
            "wheat wrap": "whole wheat roti",
            "wheat tortilla": "whole wheat roti",
            "flour tortilla": "whole wheat roti",
            "wrap": "whole wheat roti",
            "tortilla": "whole wheat roti",
            "flatbread": "whole wheat roti",
            
            # Protein variations
            "protein powder vanilla": "whey protein powder",
            "protein powder chocolate": "whey protein powder",
            "vanilla protein powder": "whey protein powder",
            "whey protein": "whey protein powder",
            
            # Mixed ingredients
            "mixed berries": "berries (mixed)",
            "berry mix": "berries (mixed)",
            "mixed nuts": "nuts (generic)",
            "trail mix": "nuts (generic)",
            
            # Grain variations
            "rolled oats": "oats (rolled, dry)",
            "old fashioned oats": "oats (rolled, dry)",
            "steel cut oats": "oats (rolled, dry)",
            
            # Vegetable variations
            "mixed vegetables": "vegetables (generic)",
            "veggie mix": "vegetables (generic)",
            "roasted vegetables": "vegetables (generic)",
        }
    
    def _load_category_nutrition_fallbacks(self) -> Dict[str, str]:
        """
        STEP 5: CATEGORY NUTRITION FALLBACK (CRITICAL SAFETY NET)
        
        Use category-average nutrition to PREVENT 0-calorie plans.
        This is SAFE and INDUSTRY STANDARD.
        """
        return {
            "seeds": "seeds (generic)",
            "nuts": "nuts (generic)",
            "vegetables": "vegetables (generic)",
            "legumes": "legumes (generic)",
            "grains": "grains (generic)",
            "dairy": "greek yogurt (plain)",
            "protein": "tofu (extra-firm)",
            "oils": "olive oil",
            "fruits": "banana"
        }
    
    def _load_category_keywords(self) -> Dict[str, List[str]]:
        """Load category classification keywords - EXPANDED for better coverage"""
        return {
            "seeds": ["seed", "seeds", "chia", "hemp", "pumpkin", "sunflower", "flax", "sesame"],
            "nuts": ["nut", "nuts", "almond", "walnut", "cashew", "peanut", "pecan", "pistachio"],
            "vegetables": ["vegetable", "veggie", "spinach", "broccoli", "kale", "pepper", "tomato", "onion", "carrot", "celery", "cucumber", "mixed greens", "greens"],
            "legumes": ["bean", "beans", "lentil", "lentils", "chickpea", "chickpeas", "legume", "pea", "peas"],
            "grains": ["grain", "grains", "oat", "oats", "rice", "quinoa", "wheat", "flour", "bread", "wrap", "tortilla", "roti"],
            "dairy": ["milk", "yogurt", "cheese", "cottage", "dairy", "cream", "paneer"],
            "protein": ["protein", "tofu", "tempeh", "powder", "whey", "pea protein"],
            "oils": ["oil", "oils", "olive", "coconut", "sesame"],
            "fruits": ["fruit", "fruits", "berry", "berries", "apple", "banana", "orange", "grape", "strawberry", "blueberry"]
        }
    
    def _load_category_mappings(self) -> Dict[str, str]:
        """Load category-based fallback mappings (legacy - kept for compatibility)"""
        return {
            # Legacy category mappings
            "grain_product": "whole wheat roti",
            "bread_product": "whole wheat bread", 
            "flatbread": "whole wheat roti",
            "wrap_product": "whole wheat roti",
            "dairy_protein": "greek yogurt (plain)",
            "plant_protein": "tofu (extra-firm)",
            "legume_protein": "lentils (red, dry)",
            "leafy_green": "spinach",
            "cruciferous": "broccoli",
            "root_vegetable": "sweet potato",
            "cooking_oil": "olive oil",
            "nut_fat": "almonds",
        }
    
    def _suggest_fallback(self, category: str) -> Optional[str]:
        """Suggest a fallback ingredient for unresolved categories"""
        fallback_suggestions = {
            "seeds": "seeds (generic)",
            "nuts": "nuts (generic)",
            "vegetables": "vegetables (generic)",
            "legumes": "legumes (generic)",
            "grains": "grains (generic)",
            "dairy": "greek yogurt (plain)",
            "protein": "tofu (extra-firm)",
            "oils": "olive oil",
            "fruits": "banana"
        }
        return fallback_suggestions.get(category)
    
    def _load_brand_patterns(self) -> List[str]:
        """Load brand name patterns to remove"""
        return [
            'organic', 'trader joe', 'trader joes', 'whole foods', 'kirkland',
            'great value', 'simply', 'nature valley', 'kellogg', 'quaker'
        ]
    
    def _load_quality_descriptors(self) -> Set[str]:
        """Load quality descriptor words to remove"""
        return {
            'organic', 'fresh', 'raw', 'natural', 'pure', 'whole', 'extra', 
            'premium', 'free range', 'grass fed', 'wild caught', 'non gmo'
        }
    
    def _load_preparation_descriptors(self) -> Set[str]:
        """Load preparation descriptor words to remove"""
        return {
            'cooked', 'steamed', 'boiled', 'grilled', 'baked', 'roasted', 
            'fried', 'sauteed', 'raw', 'dried', 'frozen', 'canned'
        }


# Global normalizer instance
_normalizer_instance = None

def get_ingredient_normalizer() -> IngredientNormalizer:
    """Get the global ingredient normalizer instance"""
    global _normalizer_instance
    if _normalizer_instance is None:
        _normalizer_instance = IngredientNormalizer()
    return _normalizer_instance