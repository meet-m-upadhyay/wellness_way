"""
ML Pipeline Orchestrator - Glues all ML components together
"""

from __future__ import annotations

import logging
import os
from enum import Enum
from typing import Dict, List, Any, Optional, Set
from datetime import date, timedelta
from uuid import UUID
from types import SimpleNamespace
from sqlalchemy.orm import Session
from app.services.ml_diet_pipeline.discovery_engine import DiscoveryEngine, get_discovery_engine
from app.services.ml_diet_pipeline.daily_assembler import DailyAssembler, get_daily_assembler
class DietType(Enum):
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    NON_VEGETARIAN = "non-vegetarian"
    EGGETARIAN = "eggetarian"

class MealSlot(Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"
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
    
    discovery_engine: Any
    daily_assembler: Any
    nutrition_engine: Any
    scaling_engine: Any
    validation_engine: Any
    genai_service: Any
    canonicalizer: Optional[Any]
    
    def __init__(self, components: Optional[Dict[str, Any]] = None):
        """Initialize orchestrator with all components"""
        if components:
            self.discovery_engine = components.get("discovery_engine") or get_discovery_engine()
            self.daily_assembler = components.get("daily_assembler") or get_daily_assembler()
            self.genai_service = components.get("genai_service")
            self.nutrition_engine = components.get("nutrition_engine")
            self.scaling_engine = components.get("scaling_engine")
            self.validation_engine = components.get("validation_engine")
            self.canonicalizer = components.get("canonicalizer")
        else:
            self.discovery_engine = get_discovery_engine()
            self.daily_assembler = get_daily_assembler()
            self.genai_service = None
            self.nutrition_engine = None
            self.scaling_engine = None
            self.validation_engine = None
            self.canonicalizer = None

        # self.template_registry = get_meal_template_registry() # Removed as templates are no longer directly used
        self.nutrition_db = get_nutrition_database()
        
        logger.info("[ML_ORCHESTRATOR_INIT] Initialized ML pipeline orchestrator")
    
    async def generate_daily_plan(
        self,
        db: Session,
        user_id: UUID,
        health_context: Dict[str, Any],
        target_date: Optional[date] = None,
        exclude_templates: Optional[Set[str]] = None
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
            # STEP 0: Extract constraints from health context
            constraints = self._extract_constraints(health_context)
            logger.info(f"[ML_STEP_0] Extracted constraints: diet={constraints.diet_type.value} cal={constraints.calorie_target}")

            # STEP 1: Discover Portfolio (Finding ingredients)
            logger.info(f"[ML_STEP_1] Daily Portfolio Discovery")
            portfolio = self.discovery_engine.discover_daily_portfolio(
                db=db,
                diet_type=constraints.diet_type.value,
                allergies=constraints.allergies,
                exclude_ingredients=exclude_templates
            )
            
            # STEP 2: Assemble Day (Solving portions & splitting meals)
            logger.info(f"[ML_STEP_2] Daily Portions Assembly")
            # Extract meals_per_day from nested constraints
            meals_per_day = constraints.meals_per_day or 3
            if meals_per_day != 3:
                logger.warning(f"[ML_OVERRIDE] Forcing 3 meals instead of {meals_per_day} for legacy frontend compat")
                meals_per_day = 3
            
            raw_meals = self.daily_assembler.assemble_day(
                portfolio=portfolio,
                target_calories=constraints.calorie_target,
                target_protein=constraints.protein_target,
                meals_per_day=meals_per_day
            )
            
            # STEP 3: Creative Generation (Recipes)
            logger.info(f"[ML_STEP_3] Creative Recipe Generation")
            final_meals = []
            for raw_meal in raw_meals:
                # Generate creative text from fixed ingredients
                creative_text = await self.genai_service.generate_meal_text(
                    ingredients=[
                        {"name": ing["name"], "quantity": round(ing["quantity"]), "unit": ing["unit"]}
                        for ing in raw_meal["ingredients"]
                    ],
                    meal_type=raw_meal["type"],
                    diet_type=constraints.diet_type.value
                )
                
                # Format instructions as a clear bulleted list
                steps = creative_text.get("steps", [])
                if isinstance(steps, list):
                    instructions_str = "\n".join([f"• {step.strip()}" for step in steps if step.strip()])
                else:
                    instructions_str = str(steps)

                raw_meal.update({
                    "name": creative_text.get("meal_name", "Healthy Meal"),
                    "description": creative_text.get("description", ""),
                    "instructions": instructions_str,
                    "prep_time": creative_text.get("prep_time_minutes", 10),
                    "cook_time": creative_text.get("cook_time_minutes", 15),
                    "servings": creative_text.get("servings", 1)
                })
                final_meals.append(raw_meal)

            # STEP 4: Final Validation
            logger.info(f"[ML_STEP_4] Validating daily plan")
            validation_result = self.validation_engine.validate_daily_plan(
                meals=final_meals,
                diet_type=constraints.diet_type.value,
                target_daily_calories=constraints.calorie_target,
                target_daily_protein=constraints.protein_target
            )
            
            if not validation_result.passed:
                logger.warning(
                    f"[ML_VALIDATION_SOFT_FAIL] Accepting plan with warnings: "
                    f"{validation_result.warnings}"
                )
            
            # STEP 5: Generate text (constrained GenAI) - This step is now integrated into STEP 3 for meal text
            # For daily summary, we can generate it based on final_meals
            daily_summary_text = self.genai_service.generate_daily_plan_text(
                meals=final_meals,
                diet_type=constraints.diet_type.value
            )
            
            # STEP 6: Calculate daily totals
            daily_totals = self.nutrition_engine.calculate_daily_nutrition(final_meals)
            
            # Build final plan structure
            plan_data = {
                "plan_type": "daily",
                "date": str(target_date or date.today()),
                "day_name": (target_date or date.today()).strftime("%A"),
                "meals": final_meals,
                "daily_totals": daily_totals,
                "summary": daily_summary_text.get("summary", ""),
                "notes": daily_summary_text.get("notes", ""),
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
            
            # Track used templates across the week
            used_template_ids = set()
            
            for day_offset in range(7):
                current_date = start + timedelta(days=day_offset)
                
                logger.info(f"[ML_WEEKLY_DAY] Generating day {day_offset + 1}/7: {current_date}")
                
                # Generate daily plan with exclusion for variety
                daily_plan = await self.generate_daily_plan(
                    db=db,
                    user_id=user_id,
                    health_context=health_context,
                    target_date=current_date,
                    exclude_templates=used_template_ids # Reusing parameter name for ingredient names
                )
                
                # Add used ingredients to exclusions
                for meal in daily_plan.get("meals", []):
                    for ing in meal.get("ingredients", []):
                        used_template_ids.add(ing["name"])
                
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

    async def regenerate_meal(
        self,
        db: Session,
        user_id: UUID,
        health_context: Dict[str, Any],
        meal_type: str,
        exclude_ingredients: Optional[Set[str]] = None
    ) -> Dict[str, Any]:
        """
        Regenerate a specific meal for a user.
        
        Args:
            db: Database session
            user_id: User UUID
            health_context: User's health context
            meal_type: Type of meal to regenerate (breakfast, lunch, dinner, snack)
            exclude_ingredients: Set of ingredient names to exclude for variety
            
        Returns:
            A single meal dictionary
        """
        request_id = f"ml_regen_{user_id}_{meal_type}"
        logger.info(f"[ML_REGENERATE_MEAL] request_id={request_id} meal_type={meal_type}")
        
        # 1. Extract constraints
        constraints = self._extract_constraints(health_context)
        
        # 2. Discover portfolio (excluding current ingredients for variety)
        portfolio = self.discovery_engine.discover_daily_portfolio(
            db=db,
            diet_type=constraints.diet_type.value,
            allergies=constraints.allergies,
            exclude_ingredients=exclude_ingredients
        )
        
        # 3. Assemble (we assemble a full day to keep macro distribution consistent)
        raw_meals = self.daily_assembler.assemble_day(
            portfolio=portfolio,
            target_calories=constraints.calorie_target,
            target_protein=constraints.protein_target,
            meals_per_day=constraints.meals_per_day or 3
        )
        
        # 4. Pick the meal that matches the type or index
        # For simplicity, we'll try to find a meal of the same type
        target_meal = None
        for meal in raw_meals:
            if meal["type"] == meal_type:
                target_meal = meal
                break
        
        if not target_meal:
            # Fallback to first meal if type not found
            target_meal = raw_meals[0]
            target_meal["type"] = meal_type # Coerce type
            
        # 5. Generate creative text
        creative_text = await self.genai_service.generate_meal_text(
            ingredients=[
                {"name": ing["name"], "quantity": round(ing["quantity"]), "unit": ing["unit"]}
                for ing in target_meal["ingredients"]
            ],
            meal_type=meal_type,
            diet_type=constraints.diet_type.value
        )
        
        # Format instructions as a clear bulleted list
        steps = creative_text.get("steps", [])
        if isinstance(steps, list):
            instructions_str = "\n".join([f"• {step.strip()}" for step in steps if step.strip()])
        else:
            instructions_str = str(steps)

        target_meal.update({
            "name": creative_text.get("meal_name", "Healthy Meal"),
            "description": creative_text.get("description", ""),
            "instructions": instructions_str,
            "prep_time": creative_text.get("prep_time_minutes", 10),
            "cook_time": creative_text.get("cook_time_minutes", 15),
            "servings": creative_text.get("servings", 1)
        })
        
        return target_meal
    
    def _extract_constraints(self, health_context: Dict[str, Any]) -> Any:
        """Extract selection constraints from health context"""
        # Resolve nested keys from HCD JSON context if present
        diet_section = health_context.get("diet_restrictions", {})
        nutrition_section = health_context.get("nutrition_targets", {})
        
        # Robustly extract meals_per_day
        meals_per_day = (
            diet_section.get("meals_per_day") or 
            health_context.get("meals_per_day") or 
            3
        )

        diet_type_str = (
            diet_section.get("diet_type") or 
            health_context.get("diet_type") or 
            "vegetarian"
        ).lower()
        
        logger.info(f"[ML_DEBUG] Extracted diet_type_str: {diet_type_str}")

        diet_type_map = {
            "vegetarian": DietType.VEGETARIAN,
            "vegan": DietType.VEGAN,
            "non-vegetarian": DietType.NON_VEGETARIAN,
            "non_vegetarian": DietType.NON_VEGETARIAN,
            "eggetarian": DietType.EGGETARIAN
        }
        diet_type = diet_type_map.get(diet_type_str, DietType.VEGETARIAN)
        
        # Extract targets (favor nutrition_targets section if available)
        calorie_target = (
            nutrition_section.get("target_calories") or 
            health_context.get("tdee_calories") or 
            2000
        )
        protein_target = (
            nutrition_section.get("target_protein_g") or 
            health_context.get("min_protein_grams") or 
            60
        )
        
        # Extract restrictions
        allergies = set(diet_section.get("allergies", health_context.get("allergies", [])))
        foods_to_avoid = set(diet_section.get("foods_to_avoid", health_context.get("foods_to_avoid", [])))
        
        return SimpleNamespace(
            diet_type=diet_type,
            calorie_target=calorie_target,
            protein_target=protein_target,
            allergies=set(health_context.get("allergies", [])),
            foods_to_avoid=set(health_context.get("foods_to_avoid", [])),
            meals_per_day=int(meals_per_day)
        )
    
    async def _dummy_build_meal(self):
        pass

def get_groq_generator():
    """Returns an async generator that calls Groq/OpenAI for recipe generation"""
    from app.core.config import get_settings
    import httpx
    import json
    
    settings = get_settings()
    api_key = settings.get_groq_api_key()
    model = settings.ai.groq_model
    
    async def generate(payload):
        if not api_key:
            return None # Fallback to service-level mock
            
        meal_type = payload.get("meal_type", "meal")
        ingredients = payload.get("ingredients", [])
        diet_type = payload.get("diet_type", "any")
        
        prompt = f"""
        Generate a creative recipe name, description, and instructions for a {meal_type} with these ingredients:
        {json.dumps(ingredients)}
        The user follows a {diet_type} diet.
        
        IMPORTANT RULES:
        1. Use VERY SIMPLE English. No difficult words.
        2. Keep instructions short and clear.
        3. Respond ONLY with a JSON object following this schema:
        {{
            "meal_name": "Simple Name",
            "description": "Very simple short description",
            "prep_time_minutes": 10,
            "cook_time_minutes": 15,
            "servings": 1,
            "steps": ["Short step 1", "Short step 2"]
        }}
        """
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": "You are a professional nutritionist and chef. You only respond with valid JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        "response_format": {"type": "json_object"}
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                return json.loads(content)
        except Exception as e:
            logging.getLogger(__name__).error(f"Groq generation failed: {e}")
            return None

    return generate

# Singleton instance
_orchestrator: Optional[MLPipelineOrchestrator] = None


def get_ml_pipeline_orchestrator(db: Optional[Session] = None) -> MLPipelineOrchestrator:
    """Get instance of ML pipeline orchestrator with database components
    
    Tasks:
    - [x] Fix dietary filtering bug (stop meat appearing for vegetarians)
    - [x] Update `orchestrator.py` to pass correct `diet_type` to discovery engine
    - [x] Implement keyword-based fallback in `DiscoveryEngine.py` for unflagged items
    - [x] Enable Real LLM (Groq) integration
        - [x] Update `GenAIService` to handle async LLM calls
        - [x] Implement Groq/OpenAI client generator in `orchestrator.py`
        - [x] Verify schema compliance and plan quality
    """
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

    def mock_genai_generator(payload):
        """Schema-compliant mock generator for GenAI"""
        meal_type = payload.get("meal_type", "meal")
        ingredients = payload.get("ingredients", [])
        main_ing = ingredients[0]["name"] if ingredients else "ingredients"
        
        return {
            "meal_name": f"{meal_type.capitalize()} with {main_ing}",
            "description": f"A balanced {meal_type} featuring {main_ing}.",
            "prep_time_minutes": 10,
            "cook_time_minutes": 15,
            "servings": 1,
            "steps": [
                f"Prepare the {main_ing}.",
                "Combine all ingredients in a bowl.",
                "Serve immediately and enjoy!"
            ]
        }

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
        "discovery_engine": get_discovery_engine(),
        "daily_assembler": get_daily_assembler(),
        "nutrition_engine": NutritionEngine(db),
        "scaling_engine": ScalingEngine(),
        "validation_engine": ValidationEngine(),
        "genai_service": GenAIService(generator=get_groq_generator()),
        "canonicalizer": canonicalizer,
    }
