"""
Meal Template Registry - Deterministic ingredient sets

This module provides static meal templates with predefined ingredient lists.
NO creativity here - just deterministic ingredient combinations.

CRITICAL RULES:
- Templates are diet-type aware
- NO quantities here (handled by scaling engine)
- NO GenAI involvement
- Templates must be validated against nutrition DB
"""

import logging
from typing import Dict, List, Set
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class DietType(str, Enum):
    """Supported diet types"""
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    NON_VEGETARIAN = "non-vegetarian"
    EGGETARIAN = "eggetarian"


class MealSlot(str, Enum):
    """Meal time slots"""
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


@dataclass
class MealTemplate:
    """Meal template with deterministic ingredients"""
    template_id: str
    name: str
    meal_slot: MealSlot
    ingredients: List[str]  # Canonical ingredient names only
    diet_types: Set[DietType]  # Which diet types this template supports
    tags: List[str]  # For filtering (high-protein, low-carb, etc.)


class MealTemplateRegistry:
    """Registry of static meal templates"""
    
    def __init__(self):
        """Initialize meal template registry"""
        self.templates: Dict[str, MealTemplate] = {}
        self._load_templates()
        logger.info(f"[TEMPLATE_REGISTRY_INIT] Loaded {len(self.templates)} meal templates")
    
    def _load_templates(self):
        """Load all meal templates"""
        
        # BREAKFAST TEMPLATES
        self._register_template(MealTemplate(
            template_id="protein_scramble",
            name="Protein Scramble",
            meal_slot=MealSlot.BREAKFAST,
            ingredients=["eggs (whole)", "spinach", "olive oil", "tomatoes"],
            diet_types={DietType.VEGETARIAN, DietType.EGGETARIAN, DietType.NON_VEGETARIAN},
            tags=["high-protein", "quick"]
        ))
        
        self._register_template(MealTemplate(
            template_id="oatmeal_bowl",
            name="Oatmeal Bowl",
            meal_slot=MealSlot.BREAKFAST,
            ingredients=["oats (rolled, dry)", "milk (whole)", "banana", "almonds"],
            diet_types={DietType.VEGETARIAN, DietType.NON_VEGETARIAN},
            tags=["high-fiber", "filling"]
        ))
        
        self._register_template(MealTemplate(
            template_id="vegan_smoothie_bowl",
            name="Vegan Smoothie Bowl",
            meal_slot=MealSlot.BREAKFAST,
            ingredients=["banana", "berries (mixed)", "almond milk", "chia seeds", "oats (rolled, dry)"],
            diet_types={DietType.VEGAN, DietType.VEGETARIAN, DietType.NON_VEGETARIAN},
            tags=["vegan", "antioxidants"]
        ))
        
        self._register_template(MealTemplate(
            template_id="greek_yogurt_parfait",
            name="Greek Yogurt Parfait",
            meal_slot=MealSlot.BREAKFAST,
            ingredients=["greek yogurt (plain)", "berries (mixed)", "almonds"],
            diet_types={DietType.VEGETARIAN, DietType.NON_VEGETARIAN},
            tags=["high-protein", "probiotic"]
        ))
        
        # LUNCH TEMPLATES
        self._register_template(MealTemplate(
            template_id="chicken_rice_bowl",
            name="Chicken Rice Bowl",
            meal_slot=MealSlot.LUNCH,
            ingredients=["chicken breast", "brown rice (dry)", "broccoli", "bell peppers", "olive oil"],
            diet_types={DietType.NON_VEGETARIAN},
            tags=["high-protein", "balanced"]
        ))
        
        self._register_template(MealTemplate(
            template_id="lentil_curry",
            name="Lentil Curry",
            meal_slot=MealSlot.LUNCH,
            ingredients=["lentils (red, dry)", "tomatoes", "onions", "spinach", "brown rice (dry)", "olive oil"],
            diet_types={DietType.VEGAN, DietType.VEGETARIAN, DietType.NON_VEGETARIAN},
            tags=["high-protein", "vegan", "fiber"]
        ))
        
        self._register_template(MealTemplate(
            template_id="quinoa_salad",
            name="Quinoa Salad",
            meal_slot=MealSlot.LUNCH,
            ingredients=["quinoa (dry)", "chickpeas (dry)", "cucumber", "tomatoes", "olive oil"],
            diet_types={DietType.VEGAN, DietType.VEGETARIAN, DietType.NON_VEGETARIAN},
            tags=["vegan", "complete-protein", "fresh"]
        ))
        
        self._register_template(MealTemplate(
            template_id="paneer_tikka_bowl",
            name="Paneer Tikka Bowl",
            meal_slot=MealSlot.LUNCH,
            ingredients=["paneer", "bell peppers", "onions", "brown rice (dry)", "greek yogurt (plain)"],
            diet_types={DietType.VEGETARIAN, DietType.NON_VEGETARIAN},
            tags=["high-protein", "indian"]
        ))
        
        self._register_template(MealTemplate(
            template_id="tofu_stir_fry",
            name="Tofu Stir Fry",
            meal_slot=MealSlot.LUNCH,
            ingredients=["tofu (extra-firm)", "broccoli", "bell peppers", "brown rice (dry)", "olive oil"],
            diet_types={DietType.VEGAN, DietType.VEGETARIAN, DietType.NON_VEGETARIAN},
            tags=["vegan", "high-protein", "asian"]
        ))
        
        # DINNER TEMPLATES
        self._register_template(MealTemplate(
            template_id="grilled_salmon_veggies",
            name="Grilled Salmon with Vegetables",
            meal_slot=MealSlot.DINNER,
            ingredients=["salmon", "sweet potato", "broccoli", "olive oil"],
            diet_types={DietType.NON_VEGETARIAN},
            tags=["high-protein", "omega-3", "low-carb"]
        ))
        
        self._register_template(MealTemplate(
            template_id="chickpea_pasta",
            name="Chickpea Pasta",
            meal_slot=MealSlot.DINNER,
            ingredients=["chickpeas (dry)", "tomatoes", "spinach", "olive oil"],
            diet_types={DietType.VEGAN, DietType.VEGETARIAN, DietType.NON_VEGETARIAN},
            tags=["vegan", "high-protein", "high-fiber"]
        ))
        
        self._register_template(MealTemplate(
            template_id="egg_fried_rice",
            name="Egg Fried Rice",
            meal_slot=MealSlot.DINNER,
            ingredients=["eggs (whole)", "brown rice (dry)", "bell peppers", "onions", "olive oil"],
            diet_types={DietType.VEGETARIAN, DietType.EGGETARIAN, DietType.NON_VEGETARIAN},
            tags=["quick", "protein", "comfort-food"]
        ))
        
        self._register_template(MealTemplate(
            template_id="black_bean_tacos",
            name="Black Bean Tacos",
            meal_slot=MealSlot.DINNER,
            ingredients=["black beans (dry)", "avocado", "tomatoes", "onions"],
            diet_types={DietType.VEGAN, DietType.VEGETARIAN, DietType.NON_VEGETARIAN},
            tags=["vegan", "mexican", "fiber"]
        ))
        
        self._register_template(MealTemplate(
            template_id="turkey_sweet_potato",
            name="Turkey with Sweet Potato",
            meal_slot=MealSlot.DINNER,
            ingredients=["turkey breast", "sweet potato", "broccoli", "olive oil"],
            diet_types={DietType.NON_VEGETARIAN},
            tags=["high-protein", "lean", "balanced"]
        ))
        
        # SNACK TEMPLATES
        self._register_template(MealTemplate(
            template_id="protein_shake",
            name="Protein Shake",
            meal_slot=MealSlot.SNACK,
            ingredients=["whey protein powder", "banana", "almond milk", "peanut butter"],
            diet_types={DietType.VEGETARIAN, DietType.NON_VEGETARIAN},
            tags=["high-protein", "quick", "post-workout"]
        ))
        
        self._register_template(MealTemplate(
            template_id="hummus_veggies",
            name="Hummus with Vegetables",
            meal_slot=MealSlot.SNACK,
            ingredients=["hummus", "bell peppers", "cucumber"],
            diet_types={DietType.VEGAN, DietType.VEGETARIAN, DietType.NON_VEGETARIAN},
            tags=["vegan", "protein", "fiber"]
        ))
        
        self._register_template(MealTemplate(
            template_id="nuts_fruit",
            name="Mixed Nuts and Fruit",
            meal_slot=MealSlot.SNACK,
            ingredients=["almonds", "walnuts", "apple"],
            diet_types={DietType.VEGAN, DietType.VEGETARIAN, DietType.NON_VEGETARIAN},
            tags=["vegan", "healthy-fats", "energy"]
        ))
    
    def _register_template(self, template: MealTemplate):
        """Register a meal template"""
        self.templates[template.template_id] = template
        logger.debug(f"[TEMPLATE_REGISTERED] id={template.template_id} name='{template.name}'")
    
    def get_template(self, template_id: str) -> MealTemplate:
        """Get a specific template by ID"""
        if template_id not in self.templates:
            raise ValueError(f"Template '{template_id}' not found")
        return self.templates[template_id]
    
    def get_templates_for_diet_type(
        self,
        diet_type: DietType,
        meal_slot: MealSlot = None
    ) -> List[MealTemplate]:
        """
        Get all templates compatible with a diet type.
        
        Args:
            diet_type: Diet type to filter by
            meal_slot: Optional meal slot filter
            
        Returns:
            List of compatible templates
        """
        compatible = []
        
        for template in self.templates.values():
            # Check diet type compatibility
            if diet_type not in template.diet_types:
                continue
            
            # Check meal slot if specified
            if meal_slot and template.meal_slot != meal_slot:
                continue
            
            compatible.append(template)
        
        logger.info(
            f"[TEMPLATES_FILTERED] diet_type={diet_type} meal_slot={meal_slot} "
            f"count={len(compatible)}"
        )
        
        return compatible
    
    def get_all_ingredients(self) -> Set[str]:
        """Get set of all unique ingredients across all templates"""
        all_ingredients = set()
        for template in self.templates.values():
            all_ingredients.update(template.ingredients)
        return all_ingredients


# Singleton instance
_registry: MealTemplateRegistry = None


def get_meal_template_registry() -> MealTemplateRegistry:
    """Get singleton instance of meal template registry"""
    global _registry
    if _registry is None:
        _registry = MealTemplateRegistry()
    return _registry
