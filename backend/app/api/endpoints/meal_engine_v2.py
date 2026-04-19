"""
V2 Meal Engine API endpoints.

Runs alongside existing v1 routes — feature-flagged via enable_meal_engine_v2.
"""

import json
import logging
import time
import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.config import get_settings
from app.schemas.meal_engine_v2 import (
    V2MealRequest,
    V2SingleMealResponse,
    V2DailyPlanResponse,
    V2MealComponentResponse,
    V2RecipeResponse,
    V2ScoreBreakdownResponse,
)
from app.services.meal_engine.diagnostics import PipelineDiagnostics
from app.services.meal_engine.orchestrator import MealEngineV2, MealConstraints
from app.services.meal_engine.config.loader import ConfigLoader

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v2/meal-engine", tags=["Meal Engine V2"])

# V2 supported cuisines — gate non-Indian cuisines until USDA provider data quality is fixed.
# Once USDA validation is built, add "mediterranean", "italian" here.
V2_SUPPORTED_CUISINES = {"indian", "indian_north", "indian_south"}


def _validate_cuisine(cuisine: str):
    """Raise 400 if cuisine is not yet supported by V2."""
    if cuisine.lower() not in V2_SUPPORTED_CUISINES:
        raise HTTPException(
            status_code=400,
            detail=f"V2 engine currently supports Indian cuisine only. '{cuisine}' coming soon. Use V1 engine for non-Indian cuisines.",
        )


def _get_config() -> ConfigLoader:
    return ConfigLoader()


# Goal-specific macro splits (percentage of calories)
# protein is derived from g/kg targets, carbs and fat from these percentages
GOAL_MACRO_SPLITS = {
    "muscle_gain":  {"carbs_pct": 0.50, "fat_pct": 0.22},  # ~50% carbs, ~22% fat, rest protein
    "maintenance":  {"carbs_pct": 0.40, "fat_pct": 0.27},  # ~40% carbs, ~27% fat, rest protein
    "fat_loss":     {"carbs_pct": 0.30, "fat_pct": 0.25},  # ~30% carbs, ~25% fat, rest protein
}


def _compute_meal_macros(ctx: dict, cal_per_meal: float, protein_per_meal: float) -> dict:
    """Compute per-meal carbs and fat targets using HCD values or goal-based splits."""
    meals_per_day = ctx["meals_per_day"]

    # Prefer actual HCD-computed targets if available
    if ctx.get("carbs_target") and ctx.get("fat_target"):
        return {
            "carbs": ctx["carbs_target"] / meals_per_day,
            "fat": ctx["fat_target"] / meals_per_day,
        }

    # Fall back to goal-specific percentages
    goal = ctx.get("primary_goal", "maintenance")
    split = GOAL_MACRO_SPLITS.get(goal, GOAL_MACRO_SPLITS["maintenance"])
    return {
        "carbs": cal_per_meal * split["carbs_pct"] / 4,  # 4 cal/g carbs
        "fat": cal_per_meal * split["fat_pct"] / 9,      # 9 cal/g fat
    }


def _get_user_context(db: Session, user_id: str) -> dict:
    """Extract meal constraints from user's active HealthContextDocument."""
    from sqlalchemy import text

    row = db.execute(
        text("""
            SELECT hcd.json_context, dp.diet_type, dp.cuisine,
                   dp.allergies, dp.foods_to_avoid, dp.meals_per_day,
                   hg.primary_goal
            FROM health_context_documents hcd
            JOIN diet_preferences dp ON dp.user_id = hcd.user_id
            JOIN health_goals hg ON hg.user_id = hcd.user_id
            WHERE hcd.user_id = :uid AND hcd.is_active = true
            ORDER BY hcd.version DESC LIMIT 1
        """),
        {"uid": user_id},
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="No active health context found. Complete your profile first.")

    json_ctx = row.json_context or {}
    nutrition = json_ctx.get("nutrition_targets", {})
    primary_goal = row.primary_goal or "maintenance"

    return {
        "diet_type": row.diet_type or "vegetarian",
        "cuisine": row.cuisine or "indian",
        "allergies": row.allergies or [],
        "foods_to_avoid": row.foods_to_avoid or [],
        "meals_per_day": row.meals_per_day or 3,
        "primary_goal": primary_goal,
        "calorie_target": nutrition.get("target_calories", 2000),
        "protein_target": nutrition.get("target_protein_g", 75),
        "carbs_target": nutrition.get("target_carbs_g"),
        "fat_target": nutrition.get("target_fat_g"),
    }


def _to_response(meal, goal: str, config: ConfigLoader) -> V2SingleMealResponse:
    """Convert GeneratedMeal to API response."""
    recipe = None
    if meal.recipe:
        recipe = V2RecipeResponse(
            prep_time_min=meal.recipe.prep_time_min,
            cook_time_min=meal.recipe.cook_time_min,
            steps=meal.recipe.steps,
        )

    return V2SingleMealResponse(
        archetype=meal.archetype,
        dish_name=meal.dish_name,
        components=[
            V2MealComponentResponse(
                llm_name=c.llm_name,
                resolved_code=c.resolved_code,
                resolved_name=c.resolved_name,
                match_method=c.match_method,
                match_confidence=c.match_confidence,
                grams=c.grams,
                role=c.role,
                food_group=c.food_group,
            )
            for c in meal.components
        ],
        macros=meal.macros,
        score=V2ScoreBreakdownResponse(
            macro_accuracy=meal.score.macro_accuracy,
            plate_composition=meal.score.plate_composition,
            culinary_coherence=meal.score.culinary_coherence,
            micro_diversity=meal.score.micro_diversity,
            goal_alignment=meal.score.goal_alignment,
            practicality=meal.score.practicality,
            total=meal.score.total,
            band=meal.score.band,
        ),
        cultural_note=meal.cultural_note,
        recipe=recipe,
        cooked_serving_size_g=meal.cooked_serving_size_g,
        serves=meal.serves,
        quality_warning=meal.quality_warning,
    )


def _save_v2_plan(db: Session, user_id: str, plan_response: V2DailyPlanResponse) -> str:
    """Save a V2 plan to the diet_plans table. Returns the plan ID."""
    plan_id = str(uuid.uuid4())

    # Get active HCD id
    hcd_row = db.execute(
        text("SELECT id FROM health_context_documents WHERE user_id = :uid AND is_active = true ORDER BY version DESC LIMIT 1"),
        {"uid": user_id},
    ).fetchone()
    hcd_id = str(hcd_row.id) if hcd_row else user_id

    content = plan_response.model_dump()

    # Delete old V2 plans for this user (keep max 3)
    db.execute(
        text("""
            DELETE FROM diet_plans WHERE id IN (
                SELECT id FROM diet_plans
                WHERE user_id = :uid AND engine_version = 'v2'
                ORDER BY created_at DESC
                OFFSET 2
            )
        """),
        {"uid": user_id},
    )

    db.execute(
        text("""
            INSERT INTO diet_plans (id, user_id, hcd_id, plan_type, start_date, content, engine_version)
            VALUES (:id, :uid, :hcd_id, 'daily', :start_date, :content, 'v2')
        """),
        {
            "id": plan_id,
            "uid": user_id,
            "hcd_id": hcd_id,
            "start_date": date.today().isoformat(),
            "content": json.dumps(content),
        },
    )
    db.commit()
    return plan_id


async def _parse_request(raw_request: Request) -> V2MealRequest:
    """Parse request body, handling BaseHTTPMiddleware byte consumption."""
    try:
        body = await raw_request.body()
        if body:
            data = json.loads(body)
            return V2MealRequest(**data)
    except Exception:
        pass
    return V2MealRequest()


@router.post("/generate-meal", response_model=V2SingleMealResponse)
async def generate_single_meal(
    raw_request: Request,
    db: Session = Depends(get_db),
    x_user_id: Optional[str] = Header(None),
):
    """Generate a single meal using the V2 engine."""
    settings = get_settings()
    if not getattr(settings, "enable_meal_engine_v2", False):
        raise HTTPException(status_code=403, detail="V2 meal engine is not enabled")

    request = await _parse_request(raw_request)
    user_id = x_user_id or "f53f6cb3-4b52-47ca-9cdb-bb61ece32610"
    ctx = _get_user_context(db, user_id)
    cuisine = request.cuisine or ctx["cuisine"]
    _validate_cuisine(cuisine)
    config = _get_config()

    meals_per_day = ctx["meals_per_day"]
    cal_per_meal = ctx["calorie_target"] / meals_per_day
    protein_per_meal = ctx["protein_target"] / meals_per_day
    meal_macros = _compute_meal_macros(ctx, cal_per_meal, protein_per_meal)

    constraints = MealConstraints(
        meal_type=request.meal_type,
        cuisine=cuisine,
        diet_type=ctx["diet_type"],
        target_calories=cal_per_meal,
        target_protein=protein_per_meal,
        target_carbs=meal_macros["carbs"],
        target_fat=meal_macros["fat"],
        allergies=ctx["allergies"],
        foods_to_avoid=ctx["foods_to_avoid"],
        primary_goal=ctx["primary_goal"],
    )

    pipeline_diag = PipelineDiagnostics()
    pipeline_start = time.perf_counter()
    engine = MealEngineV2(db, config, diagnostics=pipeline_diag)
    meal = await engine.generate_meal(constraints)
    pipeline_diag.total_pipeline_ms = (time.perf_counter() - pipeline_start) * 1000
    pipeline_diag.log_output()

    return _to_response(meal, ctx["primary_goal"], config)


@router.post("/generate-daily", response_model=V2DailyPlanResponse)
async def generate_daily_plan(
    raw_request: Request,
    db: Session = Depends(get_db),
    x_user_id: Optional[str] = Header(None),
):
    """Generate a full day's meals using the V2 engine."""
    settings = get_settings()
    if not getattr(settings, "enable_meal_engine_v2", False):
        raise HTTPException(status_code=403, detail="V2 meal engine is not enabled")

    request = await _parse_request(raw_request)
    user_id = x_user_id or "f53f6cb3-4b52-47ca-9cdb-bb61ece32610"
    ctx = _get_user_context(db, user_id)
    cuisine = request.cuisine or ctx["cuisine"]
    _validate_cuisine(cuisine)
    config = _get_config()

    meals_per_day = ctx["meals_per_day"]
    cal_per_meal = ctx["calorie_target"] / meals_per_day
    protein_per_meal = ctx["protein_target"] / meals_per_day
    meal_macros = _compute_meal_macros(ctx, cal_per_meal, protein_per_meal)

    logger.info(
        "[V2_TARGETS] user=%s goal=%s | daily: %d cal, %dg protein, %dg carbs, %dg fat | per meal: %d cal, %dg protein, %dg carbs, %dg fat",
        user_id, ctx["primary_goal"],
        ctx["calorie_target"], ctx["protein_target"],
        ctx.get("carbs_target") or 0, ctx.get("fat_target") or 0,
        cal_per_meal, protein_per_meal,
        meal_macros["carbs"], meal_macros["fat"],
    )

    meal_types = ["breakfast", "lunch", "dinner"][:meals_per_day]
    generated_meals = []
    used_ingredients = []

    # Shared diagnostics across all meals in this daily plan
    pipeline_diag = PipelineDiagnostics()
    pipeline_start = time.perf_counter()

    for meal_type in meal_types:
        constraints = MealConstraints(
            meal_type=meal_type,
            cuisine=cuisine,
            diet_type=ctx["diet_type"],
            target_calories=cal_per_meal,
            target_protein=protein_per_meal,
            target_carbs=meal_macros["carbs"],
            target_fat=meal_macros["fat"],
            allergies=ctx["allergies"],
            foods_to_avoid=ctx["foods_to_avoid"],
            exclude_ingredients=used_ingredients,
            primary_goal=ctx["primary_goal"],
        )

        engine = MealEngineV2(db, config, diagnostics=pipeline_diag)
        meal = await engine.generate_meal(constraints)
        generated_meals.append(meal)

        # Track used ingredients for variety
        used_ingredients.extend(
            c.resolved_name for c in meal.components if c.resolved_code
        )

    pipeline_diag.total_pipeline_ms = (time.perf_counter() - pipeline_start) * 1000
    # Log full diagnostics
    pipeline_diag.log_output()

    # Calculate daily totals
    daily_totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0}
    for meal in generated_meals:
        for key in daily_totals:
            daily_totals[key] += meal.macros.get(key, 0)
    daily_totals = {k: round(v, 1) for k, v in daily_totals.items()}

    # Macro display order based on goal
    macro_order = config.goal_macro_order.get(ctx["primary_goal"], ["calories", "protein", "carbs", "fat", "fiber"])

    plan_response = V2DailyPlanResponse(
        meals=[_to_response(m, ctx["primary_goal"], config) for m in generated_meals],
        daily_totals=daily_totals,
        goal=ctx["primary_goal"],
        macro_display_order=macro_order,
    )

    # Save to DB
    try:
        plan_id = _save_v2_plan(db, user_id, plan_response)
        plan_response.id = plan_id
    except Exception as e:
        logger.warning("Failed to save V2 plan to DB: %s", e)

    return plan_response


@router.get("/latest", response_model=Optional[V2DailyPlanResponse])
async def get_latest_v2_plan(
    db: Session = Depends(get_db),
    x_user_id: Optional[str] = Header(None),
):
    """Get the latest V2 plan for the user."""
    user_id = x_user_id or "f53f6cb3-4b52-47ca-9cdb-bb61ece32610"

    row = db.execute(
        text("""
            SELECT id, content FROM diet_plans
            WHERE user_id = :uid AND engine_version = 'v2'
            ORDER BY created_at DESC LIMIT 1
        """),
        {"uid": user_id},
    ).fetchone()

    if not row:
        return None

    content = row.content if isinstance(row.content, dict) else json.loads(row.content)
    content["id"] = str(row.id)
    return V2DailyPlanResponse(**content)
