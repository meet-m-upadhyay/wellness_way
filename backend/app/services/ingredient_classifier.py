"""
Ingredient Classification & Diet Compliance System

This module provides deterministic ingredient classification that does NOT rely on:
- Exact string matches
- LLM reasoning  
- Nutrition database presence

CRITICAL: Classification must work for ANY ingredient name, even if not in nutrition DB.
"""

import logging
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import re

logger = logging.getLogger(__name__)


class IngredientCategory(Enum):
    """Primary ingredient categories for diet compliance"""
    MEAT = "meat"
    FISH = "fish" 
    DAIRY = "dairy"
    EGG = "egg"
    PLANT = "plant"
    SUPPLEMENT = "supplement"
    UNKNOWN = "unknown"


class SupplementSource(Enum):
    """Supplement source classification for diet compliance"""
    DAIRY_BASED = "dairy_based"      # Whey, casein
    PLANT_BASED = "plant_based"      # Pea, soy, hemp, rice
    UNKNOWN_SOURCE = "unknown_source"


@dataclass
class ClassificationResult:
    """Result of ingredient classification"""
    category: IngredientCategory
    supplement_source: Optional[SupplementSource] = None
    confidence: float = 1.0
    matched_keywords: List[str] = None
    
    def __post_init__(self):
        if self.matched_keywords is None:
            self.matched_keywords = []
    
    @property
    def is_vegetarian_compliant(self) -> bool:
        """Check if ingredient is vegetarian compliant"""
        if self.category in [IngredientCategory.MEAT, IngredientCategory.FISH]:
            return False
        
        if self.category == IngredientCategory.SUPPLEMENT:
            # Unknown source supplements are assumed vegetarian (but not vegan) for safety
            return self.supplement_source in [SupplementSource.DAIRY_BASED, SupplementSource.PLANT_BASED, SupplementSource.UNKNOWN_SOURCE]
        
        return self.category in [
            IngredientCategory.DAIRY, 
            IngredientCategory.EGG, 
            IngredientCategory.PLANT
        ]
    
    @property 
    def is_vegan_compliant(self) -> bool:
        """Check if ingredient is vegan compliant"""
        if self.category in [IngredientCategory.MEAT, IngredientCategory.FISH, 
                           IngredientCategory.DAIRY, IngredientCategory.EGG]:
            return False
        
        if self.category == IngredientCategory.SUPPLEMENT:
            # Only plant-based supplements are vegan compliant
            return self.supplement_source == SupplementSource.PLANT_BASED
        
        return self.category == IngredientCategory.PLANT


class IngredientClassifier:
    """
    Deterministic ingredient classifier using semantic keyword analysis.
    
    DESIGN PRINCIPLES:
    1. Token-based analysis (not exact string matching)
    2. Semantic keyword groups with priority
    3. Works independently of nutrition database
    4. Deterministic and reproducible results
    """
    
    def __init__(self):
        """Initialize classifier with keyword mappings"""
        self.meat_keywords = self._load_meat_keywords()
        self.fish_keywords = self._load_fish_keywords()
        self.dairy_keywords = self._load_dairy_keywords()
        self.egg_keywords = self._load_egg_keywords()
        self.plant_keywords = self._load_plant_keywords()
        self.supplement_keywords = self._load_supplement_keywords()
        
        logger.info("Ingredient classifier initialized with semantic keyword groups")
    
    def classify_ingredient(self, ingredient_name: str) -> ClassificationResult:
        """
        Classify ingredient using deterministic semantic analysis.
        
        Args:
            ingredient_name: Raw ingredient name from any source
            
        Returns:
            ClassificationResult with category and compliance info
        """
        # Normalize and tokenize
        tokens = self._normalize_and_tokenize(ingredient_name)
        
        logger.debug(f"Classifying '{ingredient_name}' -> tokens: {tokens}")
        
        # Apply classification rules in priority order
        
        # 1. SUPPLEMENT DETECTION (highest priority - most specific)
        supplement_result = self._classify_supplement(tokens, ingredient_name)
        if supplement_result:
            return supplement_result
        
        # 1.5. WHEY/CASEIN DETECTION (dairy proteins without "protein" keyword)
        dairy_protein_keywords = {'whey', 'casein'}
        if any(keyword in tokens for keyword in dairy_protein_keywords):
            matched = [kw for kw in dairy_protein_keywords if kw in tokens]
            return ClassificationResult(
                category=IngredientCategory.SUPPLEMENT,
                supplement_source=SupplementSource.DAIRY_BASED,
                confidence=0.95,
                matched_keywords=matched
            )
        
        # 1.7. PLANT-BASED MILK/BUTTER DETECTION (higher priority than dairy)
        plant_dairy_alternatives = {
            'soy milk', 'almond milk', 'oat milk', 'coconut milk', 'rice milk',
            'almond butter', 'peanut butter', 'cashew butter', 'sunflower butter'
        }
        ingredient_lower = ingredient_name.lower().strip()
        for alt in plant_dairy_alternatives:
            if alt in ingredient_lower:
                return ClassificationResult(
                    category=IngredientCategory.PLANT,
                    confidence=0.95,
                    matched_keywords=[alt]
                )
        
        # 2. MEAT DETECTION (high priority - safety critical)
        if self._matches_category(tokens, self.meat_keywords):
            matched = self._get_matched_keywords(tokens, self.meat_keywords)
            return ClassificationResult(
                category=IngredientCategory.MEAT,
                confidence=0.95,
                matched_keywords=matched
            )
        
        # 3. FISH DETECTION (high priority - safety critical)  
        if self._matches_category(tokens, self.fish_keywords):
            matched = self._get_matched_keywords(tokens, self.fish_keywords)
            return ClassificationResult(
                category=IngredientCategory.FISH,
                confidence=0.95,
                matched_keywords=matched
            )
        
        # 4. DAIRY DETECTION (medium priority)
        if self._matches_category(tokens, self.dairy_keywords):
            matched = self._get_matched_keywords(tokens, self.dairy_keywords)
            return ClassificationResult(
                category=IngredientCategory.DAIRY,
                confidence=0.90,
                matched_keywords=matched
            )
        
        # 5. EGG DETECTION (medium priority)
        if self._matches_category(tokens, self.egg_keywords):
            matched = self._get_matched_keywords(tokens, self.egg_keywords)
            return ClassificationResult(
                category=IngredientCategory.EGG,
                confidence=0.90,
                matched_keywords=matched
            )
        
        # 6. PLANT DETECTION (lower priority - catch remaining)
        if self._matches_category(tokens, self.plant_keywords):
            matched = self._get_matched_keywords(tokens, self.plant_keywords)
            return ClassificationResult(
                category=IngredientCategory.PLANT,
                confidence=0.85,
                matched_keywords=matched
            )
        
        # 7. DEFAULT TO UNKNOWN (requires manual review)
        logger.warning(f"Could not classify ingredient: {ingredient_name}")
        return ClassificationResult(
            category=IngredientCategory.UNKNOWN,
            confidence=0.0,
            matched_keywords=[]
        )
    
    def _normalize_and_tokenize(self, ingredient_name: str) -> Set[str]:
        """
        Normalize ingredient name and extract semantic tokens.
        
        NORMALIZATION RULES:
        1. Convert to lowercase
        2. Remove parentheses and brackets
        3. Split on whitespace and punctuation
        4. Remove common modifiers (cooked, fresh, etc.)
        5. Extract meaningful tokens
        """
        # Convert to lowercase and remove special characters
        normalized = ingredient_name.lower()
        normalized = re.sub(r'[()[\]{}]', ' ', normalized)
        normalized = re.sub(r'[,.-]', ' ', normalized)
        
        # Split into tokens
        raw_tokens = normalized.split()
        
        # Remove common modifiers that don't affect classification
        modifiers_to_remove = {
            'fresh', 'frozen', 'dried', 'raw', 'cooked', 'steamed', 'boiled',
            'grilled', 'baked', 'roasted', 'fried', 'sauteed', 'organic',
            'free-range', 'grass-fed', 'wild', 'farmed', 'canned', 'bottled',
            'extra', 'super', 'premium', 'natural', 'pure', 'whole', 'low-fat',
            'non-fat', 'reduced', 'light', 'diet', 'sugar-free', 'unsweetened',
            'plain', 'unflavored', 'flavored'
        }
        
        # Keep meaningful tokens
        meaningful_tokens = set()
        for token in raw_tokens:
            if token and len(token) > 1 and token not in modifiers_to_remove:
                meaningful_tokens.add(token)
        
        return meaningful_tokens
    
    def _classify_supplement(self, tokens: Set[str], original_name: str) -> Optional[ClassificationResult]:
        """
        Classify protein supplements with source detection.
        
        SUPPLEMENT DETECTION RULES:
        1. Must contain 'protein' keyword
        2. Determine source (dairy vs plant vs unknown)
        3. Handle various naming patterns
        """
        # Check if this is a protein supplement
        if 'protein' not in tokens:
            return None
        
        # Determine supplement source
        supplement_source = SupplementSource.UNKNOWN_SOURCE
        matched_keywords = ['protein']
        
        # DAIRY-BASED SUPPLEMENTS
        dairy_supplement_indicators = {
            'whey', 'casein', 'milk', 'dairy'
        }
        
        if any(indicator in tokens for indicator in dairy_supplement_indicators):
            supplement_source = SupplementSource.DAIRY_BASED
            matched_keywords.extend([kw for kw in dairy_supplement_indicators if kw in tokens])
        
        # PLANT-BASED SUPPLEMENTS  
        else:
            plant_supplement_indicators = {
                'pea', 'soy', 'hemp', 'rice', 'plant', 'vegan', 'vegetarian',
                'brown', 'quinoa', 'amaranth', 'chia', 'spirulina'
            }
            
            if any(indicator in tokens for indicator in plant_supplement_indicators):
                supplement_source = SupplementSource.PLANT_BASED
                matched_keywords.extend([kw for kw in plant_supplement_indicators if kw in tokens])
        
        # Additional supplement keywords
        supplement_keywords = {
            'powder', 'isolate', 'concentrate', 'blend', 'supplement', 'shake'
        }
        matched_keywords.extend([kw for kw in supplement_keywords if kw in tokens])
        
        return ClassificationResult(
            category=IngredientCategory.SUPPLEMENT,
            supplement_source=supplement_source,
            confidence=0.95,
            matched_keywords=matched_keywords
        )
    
    def _matches_category(self, tokens: Set[str], category_keywords: Dict[str, Set[str]]) -> bool:
        """Check if tokens match any keyword group in category"""
        for keyword_group in category_keywords.values():
            if any(keyword in tokens for keyword in keyword_group):
                return True
        return False
    
    def _get_matched_keywords(self, tokens: Set[str], category_keywords: Dict[str, Set[str]]) -> List[str]:
        """Get list of matched keywords for debugging"""
        matched = []
        for keyword_group in category_keywords.values():
            matched.extend([kw for kw in keyword_group if kw in tokens])
        return matched
    
    def _load_meat_keywords(self) -> Dict[str, Set[str]]:
        """Load meat detection keywords grouped by type"""
        return {
            'beef': {'beef', 'steak', 'hamburger', 'ground', 'chuck', 'sirloin', 'ribeye'},
            'pork': {'pork', 'bacon', 'ham', 'sausage', 'pepperoni', 'prosciutto'},
            'poultry': {'chicken', 'turkey', 'duck', 'goose', 'poultry'},
            'lamb': {'lamb', 'mutton'},
            'game': {'venison', 'rabbit', 'bison', 'elk'},
            'processed': {'salami', 'chorizo', 'bratwurst', 'hot', 'dog'}
        }
    
    def _load_fish_keywords(self) -> Dict[str, Set[str]]:
        """Load fish/seafood detection keywords"""
        return {
            'fish': {'fish', 'salmon', 'tuna', 'cod', 'halibut', 'trout', 'bass', 'tilapia'},
            'shellfish': {'shrimp', 'crab', 'lobster', 'scallop', 'oyster', 'mussel', 'clam'},
            'other_seafood': {'squid', 'octopus', 'anchovy', 'sardine', 'mackerel'}
        }
    
    def _load_dairy_keywords(self) -> Dict[str, Set[str]]:
        """Load dairy detection keywords"""
        return {
            'milk': {'milk', 'dairy'},
            'cheese': {'cheese', 'cheddar', 'mozzarella', 'parmesan', 'feta', 'goat', 'swiss'},
            'yogurt': {'yogurt', 'greek'},
            'cream': {'cream', 'butter', 'ghee'},
            'other': {'cottage', 'ricotta', 'mascarpone', 'brie', 'camembert'}
        }
    
    def _load_egg_keywords(self) -> Dict[str, Set[str]]:
        """Load egg detection keywords"""
        return {
            'eggs': {'egg', 'eggs', 'whites', 'yolk', 'yolks', 'albumen'}
        }
    
    def _load_plant_keywords(self) -> Dict[str, Set[str]]:
        """Load plant-based food keywords"""
        return {
            'vegetables': {
                'broccoli', 'spinach', 'kale', 'lettuce', 'tomato', 'onion', 'garlic',
                'carrot', 'celery', 'pepper', 'cucumber', 'zucchini', 'eggplant',
                'mushroom', 'avocado', 'potato', 'sweet'
            },
            'fruits': {
                'apple', 'banana', 'orange', 'berry', 'berries', 'strawberry', 
                'blueberry', 'raspberry', 'grape', 'lemon', 'lime', 'mango'
            },
            'grains': {
                'rice', 'quinoa', 'oats', 'wheat', 'barley', 'buckwheat', 
                'amaranth', 'millet', 'bread', 'pasta', 'flour'
            },
            'legumes': {
                'lentil', 'lentils', 'bean', 'beans', 'chickpea', 'chickpeas',
                'pea', 'peas', 'soy', 'tofu', 'tempeh', 'edamame'
            },
            'nuts_seeds': {
                'almond', 'almonds', 'walnut', 'walnuts', 'cashew', 'cashews',
                'peanut', 'peanuts', 'seed', 'seeds', 'chia', 'hemp', 'flax'
            },
            'oils': {
                'oil', 'olive', 'coconut', 'sesame', 'sunflower', 'safflower'
            }
        }
    
    def _load_supplement_keywords(self) -> Dict[str, Set[str]]:
        """Load supplement detection keywords"""
        return {
            'protein_types': {'protein', 'whey', 'casein', 'isolate', 'concentrate'},
            'forms': {'powder', 'shake', 'supplement', 'blend'},
            'sources': {'pea', 'soy', 'hemp', 'rice', 'plant', 'dairy', 'milk'}
        }


class DietComplianceValidator:
    """
    Validates ingredient lists against dietary restrictions using classification.
    
    VALIDATION RULES:
    - Vegetarian: No MEAT or FISH
    - Vegan: No MEAT, FISH, DAIRY, EGG, or dairy-based supplements
    - Unknown ingredients always fail validation (safety first)
    """
    
    def __init__(self):
        self.classifier = IngredientClassifier()
    
    def validate_diet_compliance(
        self, 
        ingredients: List[str], 
        diet_type: str
    ) -> Tuple[bool, List[str]]:
        """
        Validate ingredient list against diet restrictions.
        
        Args:
            ingredients: List of ingredient names
            diet_type: 'vegetarian', 'vegan', or 'omnivore'
            
        Returns:
            (is_compliant, list_of_violations)
        """
        if diet_type.lower() == 'omnivore':
            return True, []  # No restrictions
        
        violations = []
        
        for ingredient_name in ingredients:
            classification = self.classifier.classify_ingredient(ingredient_name)
            
            # UNKNOWN ingredients always fail (safety first)
            if classification.category == IngredientCategory.UNKNOWN:
                violations.append(
                    f"Unknown ingredient '{ingredient_name}' - cannot verify diet compliance"
                )
                continue
            
            # Check vegetarian compliance
            if diet_type.lower() == 'vegetarian':
                if not classification.is_vegetarian_compliant:
                    violations.append(
                        f"Non-vegetarian ingredient: '{ingredient_name}' "
                        f"(category: {classification.category.value})"
                    )
            
            # Check vegan compliance  
            elif diet_type.lower() == 'vegan':
                if not classification.is_vegan_compliant:
                    reason = self._get_vegan_violation_reason(classification)
                    violations.append(
                        f"Non-vegan ingredient: '{ingredient_name}' {reason}"
                    )
        
        is_compliant = len(violations) == 0
        return is_compliant, violations
    
    def _get_vegan_violation_reason(self, classification: ClassificationResult) -> str:
        """Get specific reason for vegan violation"""
        if classification.category == IngredientCategory.SUPPLEMENT:
            if classification.supplement_source == SupplementSource.DAIRY_BASED:
                return "(dairy-based supplement)"
            elif classification.supplement_source == SupplementSource.UNKNOWN_SOURCE:
                return "(supplement source unknown)"
        
        return f"(category: {classification.category.value})"


# Global instances
_ingredient_classifier = None
_diet_compliance_validator = None

def get_ingredient_classifier() -> IngredientClassifier:
    """Get global ingredient classifier instance"""
    global _ingredient_classifier
    if _ingredient_classifier is None:
        _ingredient_classifier = IngredientClassifier()
    return _ingredient_classifier

def get_diet_compliance_validator() -> DietComplianceValidator:
    """Get global diet compliance validator instance"""
    global _diet_compliance_validator
    if _diet_compliance_validator is None:
        _diet_compliance_validator = DietComplianceValidator()
    return _diet_compliance_validator