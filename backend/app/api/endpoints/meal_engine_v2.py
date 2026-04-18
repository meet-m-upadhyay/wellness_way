"""
V2 Meal Engine API endpoints.

Runs alongside existing v1 routes — feature-flagged via enable_meal_engine_v2.
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.config import get_settings
from app.schemas.meal_engine_v2 import (
    V2MealRequest,
    V2SingleMealResponse,
    V2DailyPlanResponse,
    V2MealComponentResponse,
    V2ScoreBreakdownResponse,
)
from app.services.meal_engine.orchestrator import MealEngineV2, MealConstraints
from app.services.meal_engine.config.loader import ConfigLoader

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v2/meal-engine", tags=["Meal Engine V2"])


def _get_config() -> ConfigLoader:
    return ConfigLoader()


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
    return {
        "diet_type": row.diet_type or "vegetarian",
        "cuisine": row.cuisine or "indian",
        "allergies": row.allergies or [],
        "foods_to_avoid": row.foods_to_avoid or [],
        "meals_per_day": row.meals_per_day or 3,
        "primary_goal": row.primary_goal or "maintenance",
        "calorie_target": json_ctx.get("calorie_target", 2000),
        "protein_target": json_ctx.get("protein_target", 75),
    }


def _to_response(meal, goal: str, config: ConfigLoader) -> V2SingleMealResponse:
    """Convert GeneratedMeal to API response."""
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
        prep_time_minutes=meal.prep_time_minutes,
        quality_warning=meal.quality_warning,
    )


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
    config = _get_config()

    meals_per_day = ctx["meals_per_day"]
    cal_per_meal = ctx["calorie_target"] / meals_per_day
    protein_per_meal = ctx["protein_target"] / meals_per_day

    constraints = MealConstraints(
        meal_type=request.meal_type,
        cuisine=request.cuisine or ctx["cuisine"],
        diet_type=ctx["diet_type"],
        target_calories=cal_per_meal,
        target_protein=protein_per_meal,
        target_carbs=cal_per_meal * 0.45 / 4,  # ~45% carbs
        target_fat=cal_per_meal * 0.30 / 9,    # ~30% fat
        allergies=ctx["allergies"],
        foods_to_avoid=ctx["foods_to_avoid"],
        primary_goal=ctx["primary_goal"],
    )

    engine = MealEngineV2(db, config)
    meal = await engine.generate_meal(constraints)

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
    config = _get_config()

    meals_per_day = ctx["meals_per_day"]
    cal_per_meal = ctx["calorie_target"] / meals_per_day
    protein_per_meal = ctx["protein_target"] / meals_per_day
    cuisine = request.cuisine or ctx["cuisine"]

    meal_types = ["breakfast", "lunch", "dinner"][:meals_per_day]
    generated_meals = []
    used_ingredients = []

    for meal_type in meal_types:
        constraints = MealConstraints(
            meal_type=meal_type,
            cuisine=cuisine,
            diet_type=ctx["diet_type"],
            target_calories=cal_per_meal,
            target_protein=protein_per_meal,
            target_carbs=cal_per_meal * 0.45 / 4,
            target_fat=cal_per_meal * 0.30 / 9,
            allergies=ctx["allergies"],
            foods_to_avoid=ctx["foods_to_avoid"],
            exclude_ingredients=used_ingredients,
            primary_goal=ctx["primary_goal"],
        )

        engine = MealEngineV2(db, config)
        meal = await engine.generate_meal(constraints)
        generated_meals.append(meal)

        # Track used ingredients for variety
        used_ingredients.extend(
            c.resolved_name for c in meal.components if c.resolved_code
        )

    # Calculate daily totals
    daily_totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0}
    for meal in generated_meals:
        for key in daily_totals:
            daily_totals[key] += meal.macros.get(key, 0)
    daily_totals = {k: round(v, 1) for k, v in daily_totals.items()}

    # Macro display order based on goal
    macro_order = config.goal_macro_order.get(ctx["primary_goal"], ["calories", "protein", "carbs", "fat", "fiber"])

    return V2DailyPlanResponse(
        meals=[_to_response(m, ctx["primary_goal"], config) for m in generated_meals],
        daily_totals=daily_totals,
        goal=ctx["primary_goal"],
        macro_display_order=macro_order,
    )
