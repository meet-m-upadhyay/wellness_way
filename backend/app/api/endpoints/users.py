"""
User profile API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database.connection import get_db
from app.schemas.user import (
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileResponse,
    UserProfileCreateAuthenticated,
    HealthGoalsCreate,
    HealthGoalsUpdate,
    HealthGoalsResponse,
    DietPreferencesCreate,
    DietPreferencesUpdate,
    DietPreferencesResponse,
    CompleteUserProfileCreate,
    CompleteUserProfileCreateAuthenticated,
    CompleteUserProfileResponse
)
from app.services.user_service import UserService
from app.middleware.auth import get_current_active_user
from app.middleware.admin import get_current_admin_user
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/profile", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_user_profile(
    profile_data: UserProfileCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new user profile.
    
    **Validates: Requirements 2.1.1, 2.1.2, 2.1.4, 2.1.5**
    """
    try:
        user_service = UserService(db)
        user = await user_service.create_user_profile(profile_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user profile"
        )


@router.get("/profiles", response_model=List[UserProfileResponse])
async def get_all_users(
    limit: int = 100,
    offset: int = 0,
    admin_user: User = Depends(get_current_admin_user),  # Require admin privileges
    db: Session = Depends(get_db)
):
    """
    Get all user profiles with pagination.
    
    **ADMIN ONLY**: This endpoint returns all users and requires admin privileges.
    Only meetupadhyaykgp@gmail.com has admin access.
    
    Args:
        limit: Maximum number of users to return (default: 100)
        offset: Number of users to skip (default: 0)
    
    Returns:
        List of user profiles
    """
    try:
        user_service = UserService(db)
        users = await user_service.get_all_users(limit=limit, offset=offset)
        return users
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.get("/profile/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get user profile by ID.
    """
    try:
        user_service = UserService(db)
        user = await user_service.get_user_profile(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )


@router.put("/profile/{user_id}", response_model=UserProfileResponse)
async def update_user_profile(
    user_id: UUID,
    profile_data: UserProfileUpdate,
    db: Session = Depends(get_db)
):
    """
    Update user profile.
    """
    try:
        user_service = UserService(db)
        user = await user_service.update_user_profile(user_id, profile_data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )


@router.delete("/profile/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_profile(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete user profile.
    """
    try:
        user_service = UserService(db)
        success = await user_service.delete_user_profile(user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user profile"
        )


# Health Goals endpoints
@router.post("/profile/{user_id}/goals", response_model=HealthGoalsResponse, status_code=status.HTTP_201_CREATED)
async def create_health_goals(
    user_id: UUID,
    goals_data: HealthGoalsCreate,
    db: Session = Depends(get_db)
):
    """
    Create health goals for a user.
    
    **Validates: Requirements 2.2.1, 2.2.2, 2.2.3**
    """
    try:
        user_service = UserService(db)
        goals = await user_service.create_health_goals(user_id, goals_data)
        return goals
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create health goals"
        )


@router.get("/profile/{user_id}/goals", response_model=HealthGoalsResponse)
async def get_health_goals(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get health goals for a user.
    """
    try:
        user_service = UserService(db)
        goals = await user_service.get_health_goals(user_id)
        if not goals:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Health goals not found"
            )
        return goals
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve health goals"
        )


@router.put("/profile/{user_id}/goals", response_model=HealthGoalsResponse)
async def update_health_goals(
    user_id: UUID,
    goals_data: HealthGoalsUpdate,
    db: Session = Depends(get_db)
):
    """
    Update health goals for a user.
    """
    try:
        user_service = UserService(db)
        goals = await user_service.update_health_goals(user_id, goals_data)
        if not goals:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Health goals not found"
            )
        return goals
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update health goals"
        )


# Diet Preferences endpoints
@router.post("/profile/{user_id}/preferences", response_model=DietPreferencesResponse, status_code=status.HTTP_201_CREATED)
async def create_diet_preferences(
    user_id: UUID,
    preferences_data: DietPreferencesCreate,
    db: Session = Depends(get_db)
):
    """
    Create diet preferences for a user.
    
    **Validates: Requirements 2.3.1, 2.3.2, 2.3.3, 2.3.4**
    """
    try:
        user_service = UserService(db)
        preferences = await user_service.create_diet_preferences(user_id, preferences_data)
        return preferences
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create diet preferences"
        )


@router.get("/profile/{user_id}/preferences", response_model=DietPreferencesResponse)
async def get_diet_preferences(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get diet preferences for a user.
    """
    try:
        user_service = UserService(db)
        preferences = await user_service.get_diet_preferences(user_id)
        if not preferences:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diet preferences not found"
            )
        return preferences
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve diet preferences"
        )


@router.put("/profile/{user_id}/preferences", response_model=DietPreferencesResponse)
async def update_diet_preferences(
    user_id: UUID,
    preferences_data: DietPreferencesUpdate,
    db: Session = Depends(get_db)
):
    """
    Update diet preferences for a user.
    """
    try:
        user_service = UserService(db)
        preferences = await user_service.update_diet_preferences(user_id, preferences_data)
        if not preferences:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diet preferences not found"
            )
        return preferences
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update diet preferences"
        )


# Complete profile endpoints
@router.post("/complete-profile", response_model=CompleteUserProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_complete_user_profile(
    profile_data: CompleteUserProfileCreate,
    db: Session = Depends(get_db)
):
    """
    Create a complete user profile with goals and preferences in one request.
    
    **Validates: Requirements 2.1.1, 2.1.2, 2.1.4, 2.1.5, 2.2.1, 2.2.2, 2.2.3, 2.3.1, 2.3.2, 2.3.3, 2.3.4**
    """
    try:
        user_service = UserService(db)
        complete_profile = await user_service.create_complete_profile(profile_data)
        return complete_profile
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create complete user profile"
        )


@router.post("/my-profile", response_model=CompleteUserProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_my_complete_profile(
    profile_data: CompleteUserProfileCreateAuthenticated,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a complete user profile for the authenticated user.
    
    **Validates: Requirements 2.1.1, 2.1.2, 2.1.4, 2.1.5, 2.2.1, 2.2.2, 2.2.3, 2.3.1, 2.3.2, 2.3.3, 2.3.4**
    """
    try:
        user_service = UserService(db)
        
        # Create the complete profile data with the authenticated user's email
        complete_profile_data = CompleteUserProfileCreate(
            profile=UserProfileCreate(
                email=current_user.email,
                **profile_data.profile.dict()
            ),
            goals=profile_data.goals,
            preferences=profile_data.preferences
        )
        
        complete_profile = await user_service.create_complete_profile_for_user(
            current_user.id, complete_profile_data
        )
        return complete_profile
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create complete user profile"
        )


@router.get("/complete-profile/{user_id}", response_model=CompleteUserProfileResponse)
async def get_complete_user_profile(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get complete user profile with goals and preferences.
    """
    try:
        user_service = UserService(db)
        complete_profile = await user_service.get_complete_profile(user_id)
        if not complete_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Complete user profile not found"
            )
        return complete_profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GET_COMPLETE_PROFILE_ERROR] user_id={user_id} error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve complete user profile: {str(e)}" if logger.isEnabledFor(logging.DEBUG) else "Failed to retrieve complete user profile"
        )