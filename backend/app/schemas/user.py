"""
User-related Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, Literal, List
from datetime import datetime
from uuid import UUID

from app.core.security import InputSanitizer


class UserProfileBase(BaseModel):
    """Base user profile schema with common fields"""
    name: str = Field(..., min_length=1, max_length=255, description="User's full name")
    age: Optional[int] = Field(None, ge=13, le=120, description="Age in years (13-120)")
    gender: Optional[Literal["male", "female", "other"]] = Field(None, description="Gender")
    height_cm: Optional[float] = Field(None, ge=50.0, le=300.0, description="Height in centimeters (50-300)")
    weight_kg: Optional[float] = Field(None, ge=20.0, le=500.0, description="Weight in kilograms (20-500)")
    body_fat_percentage: Optional[float] = Field(None, ge=0.0, le=100.0, description="Body fat percentage (0-100)")
    muscle_mass_kg: Optional[float] = Field(None, ge=0.0, description="Muscle mass in kilograms")
    activity_level: Optional[Literal["sedentary", "lightly_active", "moderately_active", "very_active", "extremely_active"]] = Field(
        None, description="Activity level"
    )

    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty or only whitespace')
        # Apply security sanitization
        sanitized_name = InputSanitizer.sanitize_name(v.strip())
        return sanitized_name

    @validator('height_cm')
    def validate_height(cls, v):
        if v is not None and (v < 50 or v > 300):
            raise ValueError('Height must be between 50 and 300 cm')
        return round(v, 2) if v is not None else v

    @validator('weight_kg')
    def validate_weight(cls, v):
        if v is not None and (v < 20 or v > 500):
            raise ValueError('Weight must be between 20 and 500 kg')
        return round(v, 2) if v is not None else v

    @validator('body_fat_percentage')
    def validate_body_fat(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Body fat percentage must be between 0 and 100')
        return round(v, 2) if v is not None else v

    @validator('muscle_mass_kg')
    def validate_muscle_mass(cls, v):
        if v is not None and v < 0:
            raise ValueError('Muscle mass cannot be negative')
        return round(v, 2) if v is not None else v


class UserProfileCreate(UserProfileBase):
    """Schema for creating a new user profile"""
    email: EmailStr = Field(..., description="User email address")
    
    @validator('email')
    def validate_email(cls, v):
        # Apply security sanitization
        return InputSanitizer.sanitize_email(str(v))


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile (all fields optional)"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    age: Optional[int] = Field(None, ge=13, le=120)
    gender: Optional[Literal["male", "female", "other"]] = None
    height_cm: Optional[float] = Field(None, ge=50.0, le=300.0)
    weight_kg: Optional[float] = Field(None, ge=20.0, le=500.0)
    body_fat_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    muscle_mass_kg: Optional[float] = Field(None, ge=0.0)
    activity_level: Optional[Literal["sedentary", "lightly_active", "moderately_active", "very_active", "extremely_active"]] = None

    @validator('name')
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Name cannot be empty or only whitespace')
        # Apply security sanitization
        if v is not None:
            sanitized_name = InputSanitizer.sanitize_name(v.strip())
            return sanitized_name
        return v

    @validator('height_cm')
    def validate_height(cls, v):
        if v is not None and (v < 50 or v > 300):
            raise ValueError('Height must be between 50 and 300 cm')
        return round(v, 2) if v is not None else v

    @validator('weight_kg')
    def validate_weight(cls, v):
        if v is not None and (v < 20 or v > 500):
            raise ValueError('Weight must be between 20 and 500 kg')
        return round(v, 2) if v is not None else v

    @validator('body_fat_percentage')
    def validate_body_fat(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Body fat percentage must be between 0 and 100')
        return round(v, 2) if v is not None else v

    @validator('muscle_mass_kg')
    def validate_muscle_mass(cls, v):
        if v is not None and v < 0:
            raise ValueError('Muscle mass cannot be negative')
        return round(v, 2) if v is not None else v


class UserProfileResponse(UserProfileBase):
    """Schema for user profile responses"""
    id: UUID
    email: str = Field(..., description="User email address")
    is_active: bool = Field(..., description="User active status")
    is_admin: bool = Field(..., description="Admin privileges")
    profile_completed: bool = Field(..., description="Profile completion status")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HealthGoalsBase(BaseModel):
    """Base health goals schema"""
    primary_goal: Literal["fat_loss", "muscle_gain", "maintenance"] = Field(..., description="Primary health goal")
    target_weight_kg: Optional[float] = Field(None, ge=20.0, le=500.0, description="Target weight in kg")
    timeline_weeks: Optional[int] = Field(None, ge=1, le=104, description="Timeline in weeks (1-104)")

    @validator('target_weight_kg')
    def validate_target_weight(cls, v):
        if v is not None and (v < 20 or v > 500):
            raise ValueError('Target weight must be between 20 and 500 kg')
        return round(v, 2) if v is not None else v

    @validator('timeline_weeks')
    def validate_timeline(cls, v):
        if v is not None and (v < 1 or v > 104):
            raise ValueError('Timeline must be between 1 and 104 weeks (2 years)')
        return v


class HealthGoalsCreate(HealthGoalsBase):
    """Schema for creating health goals"""
    pass


class HealthGoalsUpdate(BaseModel):
    """Schema for updating health goals (all fields optional)"""
    primary_goal: Optional[Literal["fat_loss", "muscle_gain", "maintenance"]] = None
    target_weight_kg: Optional[float] = Field(None, ge=20.0, le=500.0)
    timeline_weeks: Optional[int] = Field(None, ge=1, le=104)

    @validator('target_weight_kg')
    def validate_target_weight(cls, v):
        if v is not None and (v < 20 or v > 500):
            raise ValueError('Target weight must be between 20 and 500 kg')
        return round(v, 2) if v is not None else v

    @validator('timeline_weeks')
    def validate_timeline(cls, v):
        if v is not None and (v < 1 or v > 104):
            raise ValueError('Timeline must be between 1 and 104 weeks')
        return v


class HealthGoalsResponse(HealthGoalsBase):
    """Schema for health goals responses"""
    id: UUID
    user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class DietPreferencesBase(BaseModel):
    """Base diet preferences schema"""
    diet_type: Literal["vegetarian", "non_vegetarian", "vegan"] = Field(..., description="Diet type")
    allergies: List[str] = Field(default_factory=list, description="List of allergies")
    foods_to_avoid: List[str] = Field(default_factory=list, description="List of foods to avoid")
    meals_per_day: int = Field(3, ge=1, le=8, description="Number of meals per day (1-8)")
    cuisine: str = Field("indian", min_length=1, max_length=50, description="Preferred cuisine")
    reuse_ingredients: bool = Field(False, description="Whether to reuse base ingredients across the day")
    budget_constraints: Optional[str] = Field(None, max_length=500, description="Budget constraints")
    lifestyle_constraints: Optional[str] = Field(None, max_length=500, description="Lifestyle constraints")

    @validator('allergies')
    def validate_allergies(cls, v):
        if not isinstance(v, list):
            raise ValueError('Allergies must be a list')
        # Apply security sanitization
        return InputSanitizer.sanitize_list_field(v, max_items=20, max_item_length=50)

    @validator('foods_to_avoid')
    def validate_foods_to_avoid(cls, v):
        if not isinstance(v, list):
            raise ValueError('Foods to avoid must be a list')
        # Apply security sanitization
        return InputSanitizer.sanitize_list_field(v, max_items=20, max_item_length=50)

    @validator('budget_constraints')
    def validate_budget_constraints(cls, v):
        if v is not None and len(v.strip()) == 0:
            return None
        return v.strip() if v is not None else v

    @validator('lifestyle_constraints')
    def validate_lifestyle_constraints(cls, v):
        if v is not None and len(v.strip()) == 0:
            return None
        return v.strip() if v is not None else v


class DietPreferencesCreate(DietPreferencesBase):
    """Schema for creating diet preferences"""
    pass


class DietPreferencesUpdate(BaseModel):
    """Schema for updating diet preferences (all fields optional)"""
    diet_type: Optional[Literal["vegetarian", "non_vegetarian", "vegan"]] = None
    allergies: Optional[List[str]] = None
    foods_to_avoid: Optional[List[str]] = None
    meals_per_day: Optional[int] = Field(None, ge=1, le=8)
    cuisine: Optional[str] = Field(None, min_length=1, max_length=50)
    reuse_ingredients: Optional[bool] = None
    budget_constraints: Optional[str] = Field(None, max_length=500)
    lifestyle_constraints: Optional[str] = Field(None, max_length=500)

    @validator('allergies')
    def validate_allergies(cls, v):
        if v is not None:
            if not isinstance(v, list):
                raise ValueError('Allergies must be a list')
            # Apply security sanitization
            return InputSanitizer.sanitize_list_field(v, max_items=20, max_item_length=50)
        return v

    @validator('foods_to_avoid')
    def validate_foods_to_avoid(cls, v):
        if v is not None:
            if not isinstance(v, list):
                raise ValueError('Foods to avoid must be a list')
            # Apply security sanitization
            return InputSanitizer.sanitize_list_field(v, max_items=20, max_item_length=50)
        return v

    @validator('budget_constraints')
    def validate_budget_constraints(cls, v):
        if v is not None and len(v.strip()) == 0:
            return None
        # Apply security sanitization
        if v is not None:
            return InputSanitizer.sanitize_text_field(v.strip(), max_length=500)
        return v

    @validator('lifestyle_constraints')
    def validate_lifestyle_constraints(cls, v):
        if v is not None and len(v.strip()) == 0:
            return None
        # Apply security sanitization
        if v is not None:
            return InputSanitizer.sanitize_text_field(v.strip(), max_length=500)
        return v


class DietPreferencesResponse(DietPreferencesBase):
    """Schema for diet preferences responses"""
    id: UUID
    user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfileCreateAuthenticated(UserProfileBase):
    """Schema for creating a user profile when user is already authenticated (no email required)"""
    pass


class CompleteUserProfileCreate(BaseModel):
    """Schema for creating a complete user profile with goals and preferences"""
    profile: UserProfileCreate
    goals: HealthGoalsCreate
    preferences: DietPreferencesCreate


class CompleteUserProfileCreateAuthenticated(BaseModel):
    """Schema for creating a complete user profile for authenticated users"""
    profile: UserProfileCreateAuthenticated
    goals: HealthGoalsCreate
    preferences: DietPreferencesCreate


class CompleteUserProfileResponse(BaseModel):
    """Schema for complete user profile responses"""
    profile: UserProfileResponse
    goals: HealthGoalsResponse
    preferences: DietPreferencesResponse