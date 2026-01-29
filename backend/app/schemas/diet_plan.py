"""
Pydantic schemas for diet plan API endpoints
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Literal
from datetime import date, datetime
from uuid import UUID


class IngredientSchema(BaseModel):
    """Schema for meal ingredients"""
    name: str = Field(..., min_length=1, max_length=200)
    quantity: float = Field(..., gt=0)
    unit: str = Field(..., min_length=1, max_length=50)


class NutritionSchema(BaseModel):
    """Schema for nutritional information"""
    calories: float = Field(..., ge=0)
    protein: float = Field(..., ge=0)
    carbohydrates: float = Field(..., ge=0)
    fat: float = Field(..., ge=0)
    fiber: Optional[float] = Field(None, ge=0)
    sodium: Optional[float] = Field(None, ge=0)


class MealSchema(BaseModel):
    """Schema for individual meals"""
    type: Literal["breakfast", "lunch", "dinner", "snack"] = Field(...)
    name: str = Field(..., min_length=1, max_length=200)
    ingredients: List[IngredientSchema] = Field(..., min_items=1)
    instructions: str = Field(..., min_length=1)
    nutrition: NutritionSchema = Field(...)


class DayPlanSchema(BaseModel):
    """Schema for daily meal plan"""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    day_name: str = Field(..., min_length=1, max_length=20)
    meals: List[MealSchema] = Field(..., min_items=1)
    daily_totals: NutritionSchema = Field(...)
    
    @validator('date')
    def validate_date_format(cls, v):
        try:
            date.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')


class WeeklyPlanContentSchema(BaseModel):
    """Schema for weekly plan content"""
    plan_type: Literal["weekly"] = Field(...)
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    days: List[DayPlanSchema] = Field(..., min_items=7, max_items=7)
    weekly_totals: NutritionSchema = Field(...)
    
    @validator('start_date')
    def validate_start_date_format(cls, v):
        try:
            date.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError('Start date must be in YYYY-MM-DD format')


class DailyPlanContentSchema(BaseModel):
    """Schema for daily plan content"""
    plan_type: Literal["daily"] = Field(...)
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    day_name: str = Field(..., min_length=1, max_length=20)
    meals: List[MealSchema] = Field(..., min_items=1)
    daily_totals: NutritionSchema = Field(...)
    
    @validator('date')
    def validate_date_format(cls, v):
        try:
            date.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')


class BalanceGuidanceSchema(BaseModel):
    """Schema for optional balance guidance when plan is acceptable but not exact"""
    type: str = Field(..., description="Guidance type: info | warning")
    severity: str = Field(..., description="Guidance severity: low | medium")
    message: str = Field(..., description="User-friendly guidance message")
    calorie_delta: float = Field(..., description="Calorie difference from target")
    protein_delta: float = Field(..., description="Protein difference from target")


class DietPlanResponse(BaseModel):
    """Schema for diet plan API responses with mandatory validation status"""
    id: UUID = Field(...)
    user_id: UUID = Field(...)
    hcd_id: UUID = Field(...)
    plan_type: Literal["weekly", "daily"] = Field(...)
    start_date: date = Field(...)
    content: Dict[str, Any] = Field(...)
    created_at: datetime = Field(...)
    
    # MANDATORY: Validation status must be included in all responses
    validation_status: Optional[str] = Field(None, description="Plan validation status: accepted | accepted_with_guidance | retryable_failure | hard_safety_violation")
    validation_violations: Optional[List[str]] = Field(None, description="List of validation violations if any")
    
    # NEW: Optional balance guidance for buffer-accepted plans
    balance_guidance: Optional[BalanceGuidanceSchema] = Field(None, description="Optional guidance when plan is acceptable but not exact")
    
    class Config:
        from_attributes = True


class GenerateWeeklyPlanRequest(BaseModel):
    """Request schema for weekly plan generation"""
    start_date: Optional[date] = Field(None, description="Start date for the weekly plan (defaults to next Monday)")


class GenerateDailyPlanRequest(BaseModel):
    """Request schema for daily plan generation"""
    target_date: Optional[date] = Field(None, description="Target date for the daily plan (defaults to today)")


class RegenerateMealRequest(BaseModel):
    """Request schema for meal regeneration"""
    day_index: int = Field(..., ge=0, le=6, description="Day index (0-6 for weekly plans, 0 for daily)")
    meal_index: int = Field(..., ge=0, description="Meal index within the day")


class RegenerateDayRequest(BaseModel):
    """Request schema for day regeneration"""
    day_index: int = Field(..., ge=0, le=6, description="Day index (0-6)")


class DietPlanListResponse(BaseModel):
    """Schema for diet plan list responses"""
    plans: List[DietPlanResponse] = Field(...)
    total: int = Field(..., ge=0)


class DietPlanSummary(BaseModel):
    """Schema for diet plan summary information"""
    id: UUID = Field(...)
    plan_type: Literal["weekly", "daily"] = Field(...)
    start_date: date = Field(...)
    created_at: datetime = Field(...)
    total_calories: Optional[float] = Field(None, description="Total calories in the plan")
    total_meals: Optional[int] = Field(None, description="Total number of meals in the plan")
    
    class Config:
        from_attributes = True


class DietPlanSummaryListResponse(BaseModel):
    """Schema for diet plan summary list responses"""
    plans: List[DietPlanSummary] = Field(...)
    total: int = Field(..., ge=0)


# Error response schemas
class ErrorResponse(BaseModel):
    """Schema for error responses"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    code: Optional[str] = Field(None, description="Error code")


class SafetyViolationResponse(BaseModel):
    """Schema for safety violation responses - NEVER includes nutrition data"""
    status: Literal["rejected"] = Field(...)
    violations: List[str] = Field(..., description="List of safety constraint violations")
    message: str = Field(..., description="User-friendly error message")
    # CRITICAL: No nutrition data included in rejected plans


class ValidationErrorResponse(BaseModel):
    """Schema for validation error responses"""
    error: str = Field(..., description="Error message")
    validation_errors: List[Dict[str, Any]] = Field(..., description="Detailed validation errors")


# Success response schemas
class SuccessResponse(BaseModel):
    """Schema for success responses"""
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional response data")


class PlanGenerationStatusResponse(BaseModel):
    """Schema for plan generation status responses"""
    status: Literal["generating", "completed", "failed"] = Field(...)
    message: str = Field(..., description="Status message")
    plan_id: Optional[UUID] = Field(None, description="Plan ID if generation completed")
    error: Optional[str] = Field(None, description="Error message if generation failed")