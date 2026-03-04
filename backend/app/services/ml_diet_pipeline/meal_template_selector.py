"""
ML Meal Template Selector - Heuristic ranking (pluggable ML later)
"""

from __future__ import annotations

import logging
import random
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

from app.services.ml_diet_pipeline.meal_templates import (
    MealTemplateRegistry,
    MealTemplate,
    DietType,
    MealSlot,
    get_meal_template_registry
)

logger = logging.getLogger(__name__)


@dataclass
class TemplateScore:
    """Scored meal template"""
    template: MealTemplate
    score: float
    reasons: List[str]  # Why this score was assigned


@dataclass
class SelectionConstraints:
    """Constraints for template selection"""
    diet_type: DietType
    meal_slot: MealSlot
    calorie_target: float
    protein_target: float
    allergies: Set[str]
    foods_to_avoid: Set[str]
    preferred_tags: Set[str] = None


class MealTemplateSelector:
    """Heuristic-based meal template selector (pluggable ML later)"""
    
    def __init__(self, registry: Optional[MealTemplateRegistry] = None):
        """Initialize template selector"""
        self.registry = registry or get_meal_template_registry()
        logger.info("[TEMPLATE_SELECTOR_INIT] Initialized meal template selector")
    
    def select_template(
        self,
        constraints: SelectionConstraints,
        exclude_templates: Optional[Set[str]] = None
    ) -> TemplateScore:
        """
        Select best meal template based on constraints.
        
        Args:
            constraints: Selection constraints
            exclude_templates: Template IDs to exclude (for variety)
            
        Returns:
            TemplateScore with selected template and score
            
        Raises:
            ValueError: If no compatible templates found
        """
        request_id = f"select_{constraints.meal_slot}_{constraints.diet_type}"
        logger.info(
            f"[TEMPLATE_SELECT_START] request_id={request_id} "
            f"diet={constraints.diet_type} meal={constraints.meal_slot}"
        )
        
        # Get compatible templates
        compatible_templates = self.registry.get_templates_for_diet_type(
            diet_type=constraints.diet_type,
            meal_slot=constraints.meal_slot
        )
        
        if not compatible_templates:
            logger.error(
                f"[TEMPLATE_SELECT_ERROR] No templates found for "
                f"diet={constraints.diet_type} meal={constraints.meal_slot}"
            )
            raise ValueError(
                f"No meal templates available for {constraints.diet_type} {constraints.meal_slot}"
            )
        
        # Filter by allergies and foods to avoid
        safe_templates = self._filter_unsafe_templates(
            compatible_templates,
            constraints.allergies,
            constraints.foods_to_avoid
        )
        
        if not safe_templates:
            logger.warning(
                f"[TEMPLATE_REJECTED_DIET] All templates filtered by allergies/avoidances. "
                f"allergies={constraints.allergies} avoid={constraints.foods_to_avoid}"
            )
            raise ValueError(
                f"No safe meal templates available after filtering allergies and food avoidances"
            )
        
        # Exclude templates if specified (for variety)
        if exclude_templates:
            safe_templates = [
                t for t in safe_templates
                if t.template_id not in exclude_templates
            ]
            
            if not safe_templates:
                logger.warning("[TEMPLATE_VARIETY_EXHAUSTED] All templates excluded, resetting")
                # Reset exclusions if we've exhausted all options
                safe_templates = self._filter_unsafe_templates(
                    compatible_templates,
                    constraints.allergies,
                    constraints.foods_to_avoid
                )
        
        # Score all safe templates
        scored_templates = []
        for template in safe_templates:
            score, reasons = self._score_template(template, constraints)
            scored_templates.append(TemplateScore(
                template=template,
                score=score,
                reasons=reasons
            ))
        
        # Sort by score (descending)
        scored_templates.sort(key=lambda x: x.score, reverse=True)
        
        # Select best template
        best = scored_templates[0]
        
        logger.info(
            f"[TEMPLATE_SELECTED] request_id={request_id} "
            f"template_id={best.template.template_id} score={best.score:.2f} "
            f"reasons={best.reasons}"
        )
        
        return best
    
    def _filter_unsafe_templates(
        self,
        templates: List[MealTemplate],
        allergies: Set[str],
        foods_to_avoid: Set[str]
    ) -> List[MealTemplate]:
        """Filter out templates containing allergens or avoided foods"""
        safe_templates = []
        
        # Normalize allergies and avoidances to lowercase
        allergies_lower = {a.lower() for a in allergies}
        avoid_lower = {f.lower() for f in foods_to_avoid}
        
        for template in templates:
            # Check if any ingredient matches allergies or avoidances
            ingredients_lower = {ing.lower() for ing in template.ingredients}
            
            if ingredients_lower & allergies_lower:
                logger.debug(
                    f"[TEMPLATE_FILTERED_ALLERGY] template={template.template_id} "
                    f"allergens={ingredients_lower & allergies_lower}"
                )
                continue
            
            if ingredients_lower & avoid_lower:
                logger.debug(
                    f"[TEMPLATE_FILTERED_AVOID] template={template.template_id} "
                    f"avoided={ingredients_lower & avoid_lower}"
                )
                continue
            
            safe_templates.append(template)
        
        return safe_templates
    
    def _score_template(
        self,
        template: MealTemplate,
        constraints: SelectionConstraints
    ) -> tuple[float, List[str]]:
        """
        Score a template based on constraints (heuristic scoring).
        
        Later: Replace with ML model (LightGBM, Logistic Regression)
        
        Args:
            template: Template to score
            constraints: Selection constraints
            
        Returns:
            Tuple of (score, reasons)
        """
        score = 0.0
        reasons = []
        
        # Base score for all templates
        score += 50.0
        reasons.append("base_score")
        
        # Bonus for preferred tags
        if constraints.preferred_tags:
            matching_tags = set(template.tags) & constraints.preferred_tags
            if matching_tags:
                tag_bonus = len(matching_tags) * 10.0
                score += tag_bonus
                reasons.append(f"preferred_tags:{','.join(matching_tags)}")
        
        # Bonus for high-protein templates if protein target is high
        if constraints.protein_target > 30.0 and "high-protein" in template.tags:
            score += 15.0
            reasons.append("high_protein_match")
        
        # Bonus for vegan templates if diet is vegan
        if constraints.diet_type == DietType.VEGAN and "vegan" in template.tags:
            score += 10.0
            reasons.append("vegan_match")
        
        # Bonus for quick meals at breakfast
        if constraints.meal_slot == MealSlot.BREAKFAST and "quick" in template.tags:
            score += 5.0
            reasons.append("quick_breakfast")
        
        # Bonus for balanced meals at lunch/dinner
        if constraints.meal_slot in [MealSlot.LUNCH, MealSlot.DINNER]:
            if "balanced" in template.tags:
                score += 10.0
                reasons.append("balanced_meal")
        
        # Small random factor for variety (±5 points)
        random_factor = random.uniform(-5.0, 5.0)
        score += random_factor
        reasons.append(f"variety_factor:{random_factor:.1f}")
        
        return score, reasons
    
    def select_daily_templates(
        self,
        constraints: SelectionConstraints,
        meals_per_day: int = 3
    ) -> List[TemplateScore]:
        """
        Select templates for a full day of meals.
        
        Args:
            constraints: Base selection constraints
            meals_per_day: Number of meals to generate (default: 3)
            
        Returns:
            List of TemplateScore for each meal
        """
        logger.info(
            f"[DAILY_TEMPLATES_START] diet={constraints.diet_type} meals={meals_per_day}"
        )
        
        meal_slots = [MealSlot.BREAKFAST, MealSlot.LUNCH, MealSlot.DINNER]
        if meals_per_day > 3:
            meal_slots.extend([MealSlot.SNACK] * (meals_per_day - 3))
        
        selected_templates = []
        used_template_ids = set()
        
        for meal_slot in meal_slots[:meals_per_day]:
            # Update constraints for this meal slot
            meal_constraints = SelectionConstraints(
                diet_type=constraints.diet_type,
                meal_slot=meal_slot,
                calorie_target=constraints.calorie_target / meals_per_day,
                protein_target=constraints.protein_target / meals_per_day,
                allergies=constraints.allergies,
                foods_to_avoid=constraints.foods_to_avoid,
                preferred_tags=constraints.preferred_tags
            )
            
            # Select template (excluding already used ones for variety)
            try:
                template_score = self.select_template(
                    meal_constraints,
                    exclude_templates=used_template_ids
                )
                selected_templates.append(template_score)
                used_template_ids.add(template_score.template.template_id)
                
            except ValueError as e:
                logger.error(f"[DAILY_TEMPLATES_ERROR] meal={meal_slot} error={e}")
                raise
        
        logger.info(
            f"[DAILY_TEMPLATES_COMPLETE] selected={len(selected_templates)} meals"
        )
        
        return selected_templates


# Singleton instance
_selector: Optional[MealTemplateSelector] = None


def get_meal_template_selector() -> MealTemplateSelector:
    """Get singleton instance of meal template selector"""
    global _selector
    if _selector is None:
        _selector = MealTemplateSelector()
    return _selector
