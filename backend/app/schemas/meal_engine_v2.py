"""
Pydantic schemas for the V2 meal engine API.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from uuid import UUID


class V2MealRequest(BaseModel):
    """Request body for V2 meal generation."""
    meal_type: str = Field(default="lunch", description="breakfast, lunch, dinner, or snack")
    cuisine: str = Field(default="indian")
    plan_type: str = Field(default="daily", description="daily or weekly")


class V2MealComponentResponse(BaseModel):
    """A single ingredient in a generated meal."""
    llm_name: str
    resolved_code: Optional[str] = None
    resolved_name: str
    match_method: str
    match_confidence: float
    grams: float
    role: str
    food_group: str = ""


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
    """A single generated meal."""
    archetype: str
    dish_name: str
    components: List[V2MealComponentResponse]
    macros: Dict[str, float]
    score: V2ScoreBreakdownResponse
    cultural_note: Optional[str] = None
    prep_time_minutes: Optional[int] = None
    quality_warning: bool = False


class V2DailyPlanResponse(BaseModel):
    """Response for daily plan generation."""
    meals: List[V2SingleMealResponse]
    daily_totals: Dict[str, float]
    goal: str
    macro_display_order: List[str]
