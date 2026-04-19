"""
Pydantic schemas for the V2 meal engine API.

v2.1: Raw-ingredient model with recipe.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class V2MealRequest(BaseModel):
    """Request body for V2 meal generation."""
    meal_type: str = Field(default="lunch", description="breakfast, lunch, dinner, or snack")
    cuisine: str = Field(default="indian")
    plan_type: str = Field(default="daily", description="daily or weekly")


class V2MealComponentResponse(BaseModel):
    """A single raw ingredient in a generated meal."""
    llm_name: str
    resolved_code: Optional[str] = None
    resolved_name: str
    match_method: str
    match_confidence: float
    grams: float
    role: str
    food_group: str = ""


class V2RecipeResponse(BaseModel):
    """Recipe instructions for a meal."""
    prep_time_min: int = 0
    cook_time_min: int = 0
    steps: List[str] = []


class V2ScoreBreakdownResponse(BaseModel):
    """Scoring breakdown for a meal."""
    macro_accuracy: float
    plate_composition: float
    culinary_coherence: float
    micro_diversity: float
    goal_alignment: float
    practicality: float
    total: float
    band: str


class V2SingleMealResponse(BaseModel):
    """A single generated meal with raw ingredients and recipe."""
    archetype: str
    dish_name: str
    components: List[V2MealComponentResponse]  # kept for backward compat
    macros: Dict[str, float]
    score: V2ScoreBreakdownResponse
    cultural_note: Optional[str] = None
    recipe: Optional[V2RecipeResponse] = None
    cooked_serving_size_g: Optional[float] = None
    serves: int = 1
    quality_warning: bool = False


class V2DailyPlanResponse(BaseModel):
    """Response for daily plan generation."""
    id: Optional[str] = None
    meals: List[V2SingleMealResponse]
    daily_totals: Dict[str, float]
    goal: str
    macro_display_order: List[str]
    engine_version: str = "v2"
    schema_version: str = "v2.1_raw_ingredients"
    serving_note: str = "Weights shown are raw. Cooked serving sizes are approximate."
