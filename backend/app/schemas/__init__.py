"""
Pydantic schemas for request/response validation
"""

from .user import (
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileResponse,
    HealthGoalsCreate,
    HealthGoalsUpdate,
    HealthGoalsResponse,
    DietPreferencesCreate,
    DietPreferencesUpdate,
    DietPreferencesResponse
)

from .health_context import (
    HealthContextDocumentResponse,
    HealthContextDocumentCreate
)

# Diet plan schemas will be added in a later task
# from .diet_plan_simple import (
#     DietPlanCreate,
#     DietPlanResponse,
#     MealResponse,
#     NutritionInfoResponse
# )

__all__ = [
    # User schemas
    "UserProfileCreate",
    "UserProfileUpdate", 
    "UserProfileResponse",
    "HealthGoalsCreate",
    "HealthGoalsUpdate",
    "HealthGoalsResponse",
    "DietPreferencesCreate",
    "DietPreferencesUpdate",
    "DietPreferencesResponse",
    
    # Health context schemas
    "HealthContextDocumentResponse",
    "HealthContextDocumentCreate",
    
    # Diet plan schemas - will be added later
    # "DietPlanCreate",
    # "DietPlanResponse",
    # "MealResponse",
    # "NutritionInfoResponse"
]