"""
Simplified Diet Plan Pydantic schemas
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime, date
from uuid import UUID


class NutritionInfoResponse(BaseModel):
    """Schema for nutrition information"""
    calories: float = Field(..., ge=0, description="Calories")
    protein: float = Field(..., ge=0, description="Protein in grams")
    carbohydrates: float = Field(..., ge=0, description="Carbohydrates in grams")
    fat: float = Field(..., ge=0, description="Fat in grams")
    fiber: Optional[float] = Field(None, ge=0, description="Fiber in grams")


class IngredientResponse(BaseModel):
    """Schema for meal ingredients"""
    name: str = Field(..., min_length=1, description="Ingredient name")
    quantity: float = Field(..., gt=0, description="Quantity amount")
    unit: str = Field(..., min_length=1, description="Unit of measurement")


class MealResponse(BaseModel):
    """Schema for individual meals"""
    type: Literal["breakfast", "lunch", "dinner", "snack"] = Field(..., description="Meal type")
    name: str = Field(..., min_length=1, description="Meal name")
    ingredients: List[IngredientResponse] = Field(..., min_items=1, description="List of ingredients")
    instructions: str = Field(..., min_length=10, description="Preparation instructions")
    nutrition: NutritionInfoResponse = Field(..., description="Nutritional information")


class DayPlanResponse(BaseModel):
    """Schema for a single day's meal plan"""
    date: date = Field(..., description="Date for this day's plan")
    meals: List[MealResponse] = Field(..., min_items=1, description="List of meals for the day")
    daily_totals: NutritionInfoResponse = Field(..., description="Total nutrition for the day")


class DietPlanCreate(BaseModel):
    """Schema for creating a diet plan"""
    plan_type: Literal["weekly", "daily"] = Field(..., description="Type of diet plan")
    start_date: date = Field(..., description="Start date of the plan")
    target_calories: Optional[float] = Field(None, gt=0, description="Target daily calories")
    special_instructions: Optional[str] = Field(None, max_length=1000, description="Special instructions")


class DietPlanResponse(BaseModel):
    """Schema for diet plan responses"""
    id: UUID
    user_id: UUID
    hcd_id: UUID = Field(..., description="Health Context Document ID used for generation")
    plan_type: Literal["weekly", "daily"] = Field(..., description="Type of diet plan")
    start_date: date = Field(..., description="Start date of the plan")
    content: Dict[str, Any] = Field(..., description="Plan content as JSON")
    created_at: datetime

    class Config:
        from_attributes = True