"""
ML Pipeline Orchestrator - Glues all ML components together
"""

from __future__ import annotations

import logging
import os
from typing import Dict, List, Any, Optional
from datetime import date, timedelta
from uuid import UUID
from sqlalchemy.orm import Session
from app.services.ml_diet_pipeline.meal_template_selector import (
    get_meal_template_selector,
    SelectionConstraints,
    MealTemplateSelector
)
from app.services.ml_diet_pipeline.meal_templates import (
    get_meal_template_registry,
    DietType,
    MealSlot
)
from app.services.ml_diet_pipeline.nutrition.engine import NutritionEngine
from app.services.ml_diet_pipeline.scaling.engine import ScalingEngine
from app.services.ml_diet_pipeline.validation.engine import ValidationEngine
from app.services.ml_diet_pipeline.genai.service import GenAIService
from app.services.ml_diet_pipeline.canonicalization.service import IngredientCanonicalizer
from app.services.ml_diet_pipeline.embeddings.generator import EmbeddingGenerator
from app.services.ml_diet_pipeline.embeddings.faiss_index import FaissIndex
from app.services.nutrition_database import get_nutrition_database

logger = logging.getLogger(__name__)


class MLPipelineOrchestrator:
    """Orchestrates the complete ML diet plan generation pipeline"""
    
    template_selector: Any
    nutrition_adapter: Any
    scaling_engine: Any
    validation_engine: Any
    text_generator: Any
    canonicalizer: Optional[Any]
    
    def __init__(self, components: Optional[Dict[str, Any]] = None):
        """Initialize orchestrator with all components"""
        if components:
            self.template_selector = components.get("template_selector") or get_meal_template_selector()
            self.scaling_engine = components.get("scaling_engine")
            self.validation_engine = components.get("validation_engine")
            self.text_generator = components.get("genai_service")
            self.canonicalizer = components.get("canonicalizer")
            self.nutrition_adapter = components.get("nutrition_engine") 
        else:
            self.template_selector = get_meal_template_selector()
            self.scaling_engine = None
            self.validation_engine = None
            self.text_generator = None
            self.canonicalizer = None
            self.nutrition_adapter = None

        self.template_registry = get_meal_template_registry()
        self.nutrition_db = get_nutrition_database()
        
        logger.info("[ML_ORCHESTRATOR_INIT] Initialized ML pipeline orchestrator")
    
    async def generate_daily_plan(
        self,
        db: Session,
        user_id: UUID,
        health_context: Dict[str, Any],
        target_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Generate a daily meal plan using ML pipeline.
        
        Args:
            user_id: User ID
            health_context: User's health context (JSON format)
            target_date: Target date for the plan
            
        Returns:
            Complete daily plan dict
            
        Raises:
            Exception: If generation fails
        """
        request_id = f"ml_daily_{user_id}_{target_date or date.today()}"
        logger.info(f"[ML_PIPELINE_START] request_id={request_id} plan_type=daily")
        
        try:
            # Extract user constraints from health context
            constraints = self._extract_constraints(health_context)
            
            # STEP 1: Select meal templates (ML)
            logger.info(f"[ML_STEP_1] Template selection")
            daily_templates = self.template_selector.select_daily_templates(
                constraints=constraints,
                meals_per_day=3  # breakfast, lunch, dinner
            )
            
            # STEP 2: Build meals with nutrition (deterministic)
            logger.info(f"[ML_STEP_2] Nutrition calculation")
            meals = []
            for template_score in daily_templates:
                template = template_score.template
                
                # Build meal with nutrition
                meal = await self._build_meal_from_template(
                    db=db,
                    template=template,
                    target_calories=constraints.calorie_target / 3,
                    target_protein=constraints.protein_target / 3
                )
                meals.append(meal)
            
            # STEP 3: Scale meals to targets (deterministic)
            logger.info(f"[ML_STEP_3] Portion scaling")
            scaled_meals = self.scaling_engine.scale_day_to_target(
                meals=meals,
                target_daily_calories=constraints.calorie_target,
                target_daily_protein=constraints.protein_target
            )
            
            # STEP 4: Validate plan (rules-only)
            logger.info(f"[ML_STEP_4] Validation")
            validation_result = self.validation_engine.validate_daily_plan(
                meals=scaled_meals,
                diet_type=constraints.diet_type.value,
                target_daily_calories=constraints.calorie_target,
                target_daily_protein=constraints.protein_target
            )
            
            if not validation_result.passed:
                logger.warning(
                    f"[ML_VALIDATION_SOFT_FAIL] Accepting plan with warnings: "
                    f"{validation_result.warnings}"
                )
            
            # STEP 5: Generate text (constrained GenAI)
            logger.info(f"[ML_STEP_5] Text generation")
            plan_text = self.text_generator.generate_daily_plan_text(
                meals=scaled_meals,
                diet_type=constraints.diet_type.value
            )
            
            # STEP 6: Calculate daily totals
            daily_totals = self.nutrition_adapter.calculate_daily_nutrition(scaled_meals)
            
            # Build final plan structure
            plan_data = {
                "plan_type": "daily",
                "date": (target_date or date.today()).isoformat(),
                "day_name": (target_date or date.today()).strftime("%A"),
                "meals": scaled_meals,
                "daily_totals": daily_totals,
                "summary": plan_text.get("summary", ""),
                "notes": plan_text.get("notes", ""),
                "validation_warnings": validation_result.warnings,
                "generated_by": "ml_pipeline"
            }
            
            logger.info(f"[ML_PIPELINE_SUCCESS] request_id={request_id}")
            return plan_data
            
        except Exception as e:
            logger.error(f"[ML_PIPELINE_FAILED] request_id={request_id} error={e}")
            raise
    
    async def generate_weekly_plan(
        self,
        db: Session,
        user_id: UUID,
        health_context: Dict[str, Any],
        start_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Generate a weekly meal plan using ML pipeline.
        
        Args:
            user_id: User ID
            health_context: User's health context (JSON format)
            start_date: Start date for the week
            
        Returns:
            Complete weekly plan dict
            
        Raises:
            Exception: If generation fails
        """
        request_id = f"ml_weekly_{user_id}_{start_date or date.today()}"
        logger.info(f"[ML_PIPELINE_START] request_id={request_id} plan_type=weekly")
        
        try:
            # Extract user constraints
            constraints = self._extract_constraints(health_context)
            
            # Generate 7 daily plans
            start = start_date or date.today()
            days = []
            
            for day_offset in range(7):
                current_date = start + timedelta(days=day_offset)
                
                logger.info(f"[ML_WEEKLY_DAY] Generating day {day_offset + 1}/7: {current_date}")
                
                # Generate daily plan
                daily_plan = await self.generate_daily_plan(
                    db=db,
                    user_id=user_id,
                    health_context=health_context,
                    target_date=current_date
                )
                
                days.append(daily_plan)
            
            # Calculate weekly totals
            weekly_totals = {
                "calories": sum(day["daily_totals"]["calories"] for day in days),
                "protein": sum(day["daily_totals"]["protein"] for day in days),
                "carbohydrates": sum(day["daily_totals"]["carbohydrates"] for day in days),
                "fat": sum(day["daily_totals"]["fat"] for day in days),
                "fiber": sum(day["daily_totals"]["fiber"] for day in days)
            }
            
            # Build final plan structure
            plan_data = {
                "plan_type": "weekly",
                "start_date": start.isoformat(),
                "days": days,
                "weekly_totals": weekly_totals,
                "generated_by": "ml_pipeline"
            }
            
            logger.info(f"[ML_PIPELINE_SUCCESS] request_id={request_id}")
            return plan_data
            
        except Exception as e:
            logger.error(f"[ML_PIPELINE_FAILED] request_id={request_id} error={e}")
            raise
    
    def _extract_constraints(self, health_context: Dict[str, Any]) -> SelectionConstraints:
        """Extract selection constraints from health context"""
        
        # Parse diet type
        diet_type_str = health_context.get("diet_type", "vegetarian").lower()
        diet_type_map = {
            "vegetarian": DietType.VEGETARIAN,
            "vegan": DietType.VEGAN,
            "non-vegetarian": DietType.NON_VEGETARIAN,
            "non_vegetarian": DietType.NON_VEGETARIAN,
            "eggetarian": DietType.EGGETARIAN
        }
        diet_type = diet_type_map.get(diet_type_str, DietType.VEGETARIAN)
        
        # Extract targets
        calorie_target = health_context.get("tdee_calories", 2000)
        protein_target = health_context.get("min_protein_grams", 60)
        
        # Extract restrictions
        allergies = set(health_context.get("allergies", []))
        foods_to_avoid = set(health_context.get("foods_to_avoid", []))
        
        return SelectionConstraints(
            diet_type=diet_type,
            meal_slot=MealSlot.BREAKFAST,  # Will be overridden per meal
            calorie_target=calorie_target,
            protein_target=protein_target,
            allergies=allergies,
            foods_to_avoid=foods_to_avoid,
            preferred_tags=set()
        )
    
    async def _build_meal_from_template(
        self,
        db: Session,
        template,
        target_calories: float,
        target_protein: float
    ) -> Dict[str, Any]:
        """Build a meal with nutrition from a template"""
        
        # Get nutrition database ingredients list
        all_db_ingredients = self.nutrition_db.get_all_food_names()
        
        # Build ingredients with initial portions (100g each)
        ingredients = []
        for ingredient_name in template.ingredients:
            try:
                # STEP 2a: Canonicalization (ML Vector Search)
                canonicalizer = self.canonicalizer
                if canonicalizer is not None:
                    try:
                        canon_result = canonicalizer.canonicalize(db, ingredient_name)
                        food_id = canon_result["ingredient_id"]
                        logger.info(f"[ML_CANONICALIZED] {ingredient_name} -> {canon_result['canonical_name']} (conf: {canon_result['confidence']:.3f})")
                        
                        # Use the specific nutrition engine to get macros from registry
                        nutrition = self.nutrition_adapter.calculate_ingredient_nutrition(
                            food_id=food_id,
                            quantity_g=100
                        )
                    except Exception as ce:
                        logger.warning(f"[ML_CANON_FAILED] {ingredient_name}: {ce}. Falling back to legacy adapter.")
                        # Fallback to legacy name-based adapter
                        nutrition = self.nutrition_adapter.calculate_ingredient_nutrition(
                            ingredient_name=ingredient_name,
                            quantity=100,
                            unit="g"
                        )
                else:
                    # Legacy fallback if no canonicalizer
                    nutrition = self.nutrition_adapter.calculate_ingredient_nutrition(
                        ingredient_name=ingredient_name,
                        quantity=100,
                        unit="g"
                    )
                
                ingredients.append({
                    "name": ingredient_name,
                    "quantity": 100,
                    "unit": "g",
                    "nutrition": nutrition
                })
            except Exception as e:
                logger.warning(f"[ML_INGREDIENT_SKIP] {ingredient_name}: {e}")
                continue
        
        if not ingredients:
            raise ValueError(f"No valid ingredients for template {template.template_id}")
        
        # Calculate meal nutrition
        meal_nutrition = self.nutrition_adapter.calculate_meal_nutrition(ingredients)
        
        # Generate text
        meal_text = self.text_generator.generate_meal_text(
            ingredients=ingredients,
            meal_type=template.meal_slot.value,
            diet_type=template.diet_types
        )
        
        # Build meal dict
        meal = {
            "type": template.meal_slot.value,
            "name": meal_text["name"],
            "ingredients": ingredients,
            "instructions": meal_text["instructions"],
            "nutrition": meal_nutrition,
            "template_id": template.template_id
        }
        
        return meal


# Singleton instance
_orchestrator: Optional[MLPipelineOrchestrator] = None


def get_ml_pipeline_orchestrator(db: Optional[Session] = None) -> MLPipelineOrchestrator:
    """Get instance of ML pipeline orchestrator with database components"""
    global _orchestrator
    if _orchestrator is None:
        if db:
            components = build_ml_pipeline_components(db)
            _orchestrator = MLPipelineOrchestrator(components=components)
        else:
            _orchestrator = MLPipelineOrchestrator()
    return _orchestrator


def build_ml_pipeline_components(db):
    """
    Build new ML pipeline components for the deterministic+ML+GenAI stack.
    """
    logger.info("[ML_PIPELINE_INIT] Building components")
    import json

    def no_op_generator(payload):
        return payload

    index_dir = os.path.join(os.path.dirname(__file__), "canonicalization", "index")
    index_path = os.path.join(index_dir, "faiss.index")
    mapping_path = os.path.join(index_dir, "faiss_mapping.json")
    
    canonicalizer = None
    try:
        if os.path.exists(index_path) and os.path.exists(mapping_path):
            with open(mapping_path, "r") as f:
                embedding_ids = json.load(f)
            index = FaissIndex.load(index_path)
            canonicalizer = IngredientCanonicalizer(
                index=index,
                embedding_ids=embedding_ids,
                embedding_generator=EmbeddingGenerator()
            )
        else:
            logging.getLogger(__name__).warning("FAISS index files not found.")
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to load Canonicalizer: {e}")

    return {
        "template_selector": MealTemplateSelector(),
        "nutrition_engine": NutritionEngine(db),
        "scaling_engine": ScalingEngine(),
        "validation_engine": ValidationEngine(),
        "genai_service": GenAIService(generator=no_op_generator),
        "canonicalizer": canonicalizer,
    }
