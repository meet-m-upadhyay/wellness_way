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
]