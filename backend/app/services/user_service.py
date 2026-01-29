"""
User service layer for handling user profile operations
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, Dict, Any, List
from uuid import UUID
import logging

from app.models.user import User, HealthGoals, DietPreferences
from app.schemas.user import (
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileResponse,
    HealthGoalsCreate,
    HealthGoalsUpdate,
    HealthGoalsResponse,
    DietPreferencesCreate,
    DietPreferencesUpdate,
    DietPreferencesResponse,
    CompleteUserProfileCreate,
    CompleteUserProfileResponse
)
from app.core.security import sanitize_user_input, InputSanitizer

logger = logging.getLogger(__name__)


class UserService:
    """Service class for user-related operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_user_profile(self, profile_data: UserProfileCreate) -> UserProfileResponse:
        """
        Create a new user profile.
        
        Args:
            profile_data: User profile creation data
            
        Returns:
            Created user profile
            
        Raises:
            ValueError: If validation fails
            IntegrityError: If database constraints are violated
        """
        try:
            # Create user instance
            user = User(
                email=profile_data.email,
                name=profile_data.name,
                age=profile_data.age,
                gender=profile_data.gender,
                height_cm=profile_data.height_cm,
                weight_kg=profile_data.weight_kg,
                body_fat_percentage=profile_data.body_fat_percentage,
                muscle_mass_kg=profile_data.muscle_mass_kg,
                activity_level=profile_data.activity_level
            )
            
            # Add to database
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"Created user profile for {user.name} (ID: {user.id})")
            
            return UserProfileResponse.model_validate(user)
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Database integrity error creating user profile: {e}")
            raise ValueError("Failed to create user profile due to data constraints")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating user profile: {e}")
            raise
    
    async def get_all_users(self, limit: int = 100, offset: int = 0) -> List[UserProfileResponse]:
        """
        Get all user profiles with pagination.
        
        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip
            
        Returns:
            List of user profiles
        """
        try:
            users = self.db.query(User).offset(offset).limit(limit).all()
            return [UserProfileResponse.model_validate(user) for user in users]
        except Exception as e:
            logger.error(f"Error retrieving all users: {e}")
            raise
    
    async def get_user_profile(self, user_id: UUID) -> Optional[UserProfileResponse]:
        """
        Get user profile by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User profile or None if not found
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                return UserProfileResponse.model_validate(user)
            return None
        except Exception as e:
            logger.error(f"Error retrieving user profile {user_id}: {e}")
            raise
    
    async def update_user_profile(self, user_id: UUID, profile_data: UserProfileUpdate) -> Optional[UserProfileResponse]:
        """
        Update user profile.
        
        Args:
            user_id: User ID
            profile_data: Updated profile data
            
        Returns:
            Updated user profile or None if not found
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            # Update only provided fields
            update_data = profile_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(user, field, value)
            
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"Updated user profile {user_id}")
            
            return UserProfileResponse.model_validate(user)
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Database integrity error updating user profile {user_id}: {e}")
            raise ValueError("Failed to update user profile due to data constraints")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating user profile {user_id}: {e}")
            raise
    
    async def delete_user_profile(self, user_id: UUID) -> bool:
        """
        Delete user profile.
        
        Args:
            user_id: User ID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            self.db.delete(user)
            self.db.commit()
            
            logger.info(f"Deleted user profile {user_id}")
            
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting user profile {user_id}: {e}")
            raise
    
    async def create_health_goals(self, user_id: UUID, goals_data: HealthGoalsCreate) -> HealthGoalsResponse:
        """
        Create health goals for a user.
        
        Args:
            user_id: User ID
            goals_data: Health goals data
            
        Returns:
            Created health goals
        """
        try:
            # Verify user exists
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            
            # Delete existing goals (replace pattern)
            self.db.query(HealthGoals).filter(HealthGoals.user_id == user_id).delete()
            
            # Create new goals
            goals = HealthGoals(
                user_id=user_id,
                primary_goal=goals_data.primary_goal,
                target_weight_kg=goals_data.target_weight_kg,
                timeline_weeks=goals_data.timeline_weeks
            )
            
            self.db.add(goals)
            self.db.commit()
            self.db.refresh(goals)
            
            logger.info(f"Created health goals for user {user_id}")
            
            return HealthGoalsResponse.model_validate(goals)
            
        except ValueError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating health goals for user {user_id}: {e}")
            raise
    
    async def get_health_goals(self, user_id: UUID) -> Optional[HealthGoalsResponse]:
        """
        Get health goals for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Health goals or None if not found
        """
        try:
            goals = self.db.query(HealthGoals).filter(HealthGoals.user_id == user_id).first()
            if goals:
                return HealthGoalsResponse.model_validate(goals)
            return None
        except Exception as e:
            logger.error(f"Error retrieving health goals for user {user_id}: {e}")
            raise
    
    async def update_health_goals(self, user_id: UUID, goals_data: HealthGoalsUpdate) -> Optional[HealthGoalsResponse]:
        """
        Update health goals for a user.
        
        Args:
            user_id: User ID
            goals_data: Updated goals data
            
        Returns:
            Updated health goals or None if not found
        """
        try:
            goals = self.db.query(HealthGoals).filter(HealthGoals.user_id == user_id).first()
            if not goals:
                return None
            
            # Update only provided fields
            update_data = goals_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(goals, field, value)
            
            self.db.commit()
            self.db.refresh(goals)
            
            logger.info(f"Updated health goals for user {user_id}")
            
            return HealthGoalsResponse.model_validate(goals)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating health goals for user {user_id}: {e}")
            raise
    
    async def create_diet_preferences(self, user_id: UUID, preferences_data: DietPreferencesCreate) -> DietPreferencesResponse:
        """
        Create diet preferences for a user.
        
        Args:
            user_id: User ID
            preferences_data: Diet preferences data
            
        Returns:
            Created diet preferences
        """
        try:
            # Verify user exists
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            
            # Delete existing preferences (replace pattern)
            self.db.query(DietPreferences).filter(DietPreferences.user_id == user_id).delete()
            
            # Create new preferences
            preferences = DietPreferences(
                user_id=user_id,
                diet_type=preferences_data.diet_type,
                allergies=preferences_data.allergies,
                foods_to_avoid=preferences_data.foods_to_avoid,
                meals_per_day=preferences_data.meals_per_day,
                budget_constraints=preferences_data.budget_constraints,
                lifestyle_constraints=preferences_data.lifestyle_constraints
            )
            
            self.db.add(preferences)
            self.db.commit()
            self.db.refresh(preferences)
            
            logger.info(f"Created diet preferences for user {user_id}")
            
            return DietPreferencesResponse.model_validate(preferences)
            
        except ValueError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating diet preferences for user {user_id}: {e}")
            raise
    
    async def get_diet_preferences(self, user_id: UUID) -> Optional[DietPreferencesResponse]:
        """
        Get diet preferences for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Diet preferences or None if not found
        """
        try:
            preferences = self.db.query(DietPreferences).filter(DietPreferences.user_id == user_id).first()
            if preferences:
                return DietPreferencesResponse.model_validate(preferences)
            return None
        except Exception as e:
            logger.error(f"Error retrieving diet preferences for user {user_id}: {e}")
            raise
    
    async def update_diet_preferences(self, user_id: UUID, preferences_data: DietPreferencesUpdate) -> Optional[DietPreferencesResponse]:
        """
        Update diet preferences for a user.
        
        Args:
            user_id: User ID
            preferences_data: Updated preferences data
            
        Returns:
            Updated diet preferences or None if not found
        """
        try:
            preferences = self.db.query(DietPreferences).filter(DietPreferences.user_id == user_id).first()
            if not preferences:
                return None
            
            # Update only provided fields
            update_data = preferences_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(preferences, field, value)
            
            self.db.commit()
            self.db.refresh(preferences)
            
            logger.info(f"Updated diet preferences for user {user_id}")
            
            return DietPreferencesResponse.model_validate(preferences)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating diet preferences for user {user_id}: {e}")
            raise
    
    async def create_complete_profile(self, profile_data: CompleteUserProfileCreate) -> CompleteUserProfileResponse:
        """
        Create a complete user profile with goals and preferences.
        
        Args:
            profile_data: Complete profile data
            
        Returns:
            Complete user profile
        """
        try:
            # Create user profile first
            user_profile = await self.create_user_profile(profile_data.profile)
            user_id = user_profile.id
            
            # Create health goals
            health_goals = await self.create_health_goals(user_id, profile_data.goals)
            
            # Create diet preferences
            diet_preferences = await self.create_diet_preferences(user_id, profile_data.preferences)
            
            logger.info(f"Created complete profile for user {user_id}")
            
            return CompleteUserProfileResponse(
                profile=user_profile,
                goals=health_goals,
                preferences=diet_preferences
            )
            
        except Exception as e:
            logger.error(f"Error creating complete profile: {e}")
            raise
    
    async def create_complete_profile_for_user(self, user_id: UUID, profile_data: CompleteUserProfileCreate) -> CompleteUserProfileResponse:
        """
        Create a complete profile (goals and preferences) for an existing authenticated user.
        
        Args:
            user_id: Existing user ID
            profile_data: Complete profile data
            
        Returns:
            Complete user profile
        """
        try:
            # Get existing user
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            
            # Update user profile with new data
            profile_update_data = UserProfileUpdate(
                name=profile_data.profile.name,
                age=profile_data.profile.age,
                gender=profile_data.profile.gender,
                height_cm=profile_data.profile.height_cm,
                weight_kg=profile_data.profile.weight_kg,
                body_fat_percentage=profile_data.profile.body_fat_percentage,
                muscle_mass_kg=profile_data.profile.muscle_mass_kg,
                activity_level=profile_data.profile.activity_level
            )
            
            # Update user profile
            updated_profile = await self.update_user_profile(user_id, profile_update_data)
            if not updated_profile:
                raise ValueError("Failed to update user profile")
            
            # Mark profile as completed
            user.profile_completed = True
            self.db.commit()
            self.db.refresh(user)
            updated_profile.profile_completed = True
            
            # Create health goals
            health_goals = await self.create_health_goals(user_id, profile_data.goals)
            
            # Create diet preferences
            diet_preferences = await self.create_diet_preferences(user_id, profile_data.preferences)
            
            logger.info(f"Created complete profile for existing user {user_id}")
            
            return CompleteUserProfileResponse(
                profile=updated_profile,
                goals=health_goals,
                preferences=diet_preferences
            )
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error creating complete profile for user {user_id}: {e}")
            raise

    async def get_complete_profile(self, user_id: UUID) -> Optional[CompleteUserProfileResponse]:
        """
        Get complete user profile with goals and preferences.
        
        Args:
            user_id: User ID
            
        Returns:
            Complete user profile or None if not found
        """
        try:
            # Get user profile
            user_profile = await self.get_user_profile(user_id)
            if not user_profile:
                return None
            
            # Get health goals
            health_goals = await self.get_health_goals(user_id)
            if not health_goals:
                return None
            
            # Get diet preferences
            diet_preferences = await self.get_diet_preferences(user_id)
            if not diet_preferences:
                return None
            
            return CompleteUserProfileResponse(
                profile=user_profile,
                goals=health_goals,
                preferences=diet_preferences
            )
            
        except Exception as e:
            logger.error(f"Error retrieving complete profile for user {user_id}: {e}")
            raise