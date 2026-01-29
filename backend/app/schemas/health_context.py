"""
Health Context Document Pydantic schemas
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID


class HealthContextDocumentBase(BaseModel):
    """Base health context document schema"""
    content: str = Field(..., min_length=100, description="Markdown content of the HCD")
    bmr_calories: float = Field(..., gt=0, description="Basal Metabolic Rate in calories")
    tdee_calories: float = Field(..., gt=0, description="Total Daily Energy Expenditure in calories")
    min_daily_calories: float = Field(..., gt=0, description="Minimum safe daily calories")
    max_calorie_deficit: float = Field(..., gt=0, description="Maximum safe calorie deficit")
    min_protein_grams: float = Field(..., gt=0, description="Minimum daily protein requirement")

    @validator('content')
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError('Content cannot be empty')
        if len(v.strip()) < 100:
            raise ValueError('Content must be at least 100 characters long')
        return v.strip()

    @validator('tdee_calories')
    def validate_tdee_greater_than_bmr(cls, v, values):
        if 'bmr_calories' in values and v <= values['bmr_calories']:
            raise ValueError('TDEE must be greater than BMR')
        return round(v, 2)

    @validator('min_daily_calories')
    def validate_min_calories(cls, v, values):
        if 'bmr_calories' in values and v < values['bmr_calories']:
            raise ValueError('Minimum daily calories cannot be below BMR')
        return round(v, 2)

    @validator('bmr_calories', 'max_calorie_deficit', 'min_protein_grams')
    def validate_positive_values(cls, v):
        if v <= 0:
            raise ValueError('Value must be positive')
        return round(v, 2)


class HealthContextDocumentCreate(BaseModel):
    """Schema for creating a health context document"""
    user_profile: Dict[str, Any] = Field(..., description="User profile data")
    health_goals: Dict[str, Any] = Field(..., description="Health goals data")
    diet_preferences: Dict[str, Any] = Field(..., description="Diet preferences data")

    @validator('user_profile')
    def validate_user_profile(cls, v):
        required_fields = ['name', 'age', 'gender', 'height_cm', 'weight_kg', 'activity_level']
        for field in required_fields:
            if field not in v:
                raise ValueError(f'Missing required user profile field: {field}')
        return v

    @validator('health_goals')
    def validate_health_goals(cls, v):
        if 'primary_goal' not in v:
            raise ValueError('Missing required health goal field: primary_goal')
        return v

    @validator('diet_preferences')
    def validate_diet_preferences(cls, v):
        required_fields = ['diet_type', 'allergies', 'foods_to_avoid', 'meals_per_day']
        for field in required_fields:
            if field not in v:
                raise ValueError(f'Missing required diet preference field: {field}')
        return v


class HealthContextDocumentResponse(HealthContextDocumentBase):
    """Schema for health context document responses"""
    id: UUID
    user_id: UUID
    version: int = Field(..., gt=0, description="Document version number")
    created_at: datetime
    is_active: bool = Field(default=True, description="Whether this is the active version")

    class Config:
        from_attributes = True


class HealthContextDocumentListResponse(BaseModel):
    """Schema for listing health context documents"""
    documents: List[HealthContextDocumentResponse]
    total_count: int
    active_version: Optional[int] = None


class HealthContextMetrics(BaseModel):
    """Schema for health context metrics summary"""
    bmr_calories: float
    tdee_calories: float
    min_daily_calories: float
    max_calorie_deficit: float
    min_protein_grams: float
    target_calories: float
    protein_target_grams: float
    fat_target_grams: float
    carb_target_grams: float
    estimated_weight_change_per_week: float

    class Config:
        from_attributes = True