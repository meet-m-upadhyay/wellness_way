"""
Health Context Document service layer
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, Dict, Any, List
from uuid import UUID
import logging

from app.models.health_context import HealthContextDocument
from app.models.user import User, HealthGoals, DietPreferences
from app.schemas.health_context import (
    HealthContextDocumentCreate,
    HealthContextDocumentResponse,
    HealthContextDocumentListResponse,
    HealthContextMetrics
)
from app.services.health_calculations import generate_health_context_document

logger = logging.getLogger(__name__)


class HealthContextService:
    """Service class for Health Context Document operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_health_context_document(
        self, 
        user_id: UUID, 
        hcd_data: HealthContextDocumentCreate
    ) -> HealthContextDocumentResponse:
        """
        Create a new Health Context Document for a user.
        
        Args:
            user_id: User ID
            hcd_data: HCD creation data
            
        Returns:
            Created Health Context Document
            
        Raises:
            ValueError: If validation fails or user not found
        """
        try:
            # Verify user exists
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            
            # Generate HCD content using the health calculations service
            hcd_result = generate_health_context_document(
                user_profile=hcd_data.user_profile,
                health_goals=hcd_data.health_goals,
                diet_preferences=hcd_data.diet_preferences
            )
            
            # Get next version number
            max_version = self.db.query(HealthContextDocument.version)\
                .filter(HealthContextDocument.user_id == user_id)\
                .order_by(HealthContextDocument.version.desc())\
                .first()
            
            next_version = (max_version[0] + 1) if max_version else 1
            
            # Deactivate all existing HCDs for this user
            self.db.query(HealthContextDocument)\
                .filter(HealthContextDocument.user_id == user_id)\
                .update({"is_active": False})
            
            # Create new HCD with JSON context
            hcd = HealthContextDocument(
                user_id=user_id,
                version=next_version,
                content=hcd_result['content'],
                json_context=hcd_result['json_context'],  # Store JSON context
                bmr_calories=hcd_result['bmr_calories'],
                tdee_calories=hcd_result['tdee_calories'],
                min_daily_calories=hcd_result['min_daily_calories'],
                max_calorie_deficit=hcd_result['max_calorie_deficit'],
                min_protein_grams=hcd_result['min_protein_grams'],
                is_active=True
            )
            
            self.db.add(hcd)
            self.db.commit()
            self.db.refresh(hcd)
            
            logger.info(f"Created HCD version {next_version} for user {user_id}")
            
            return HealthContextDocumentResponse.model_validate(hcd)
            
        except ValueError:
            raise
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Database integrity error creating HCD for user {user_id}: {e}")
            raise ValueError("Failed to create health context document due to data constraints")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating HCD for user {user_id}: {e}")
            raise
    
    async def get_current_health_context_document(self, user_id: UUID) -> Optional[HealthContextDocumentResponse]:
        """
        Get the current (active) Health Context Document for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Current HCD or None if not found
        """
        try:
            hcd = self.db.query(HealthContextDocument)\
                .filter(HealthContextDocument.user_id == user_id)\
                .filter(HealthContextDocument.is_active == True)\
                .first()
            
            if hcd:
                return HealthContextDocumentResponse.model_validate(hcd)
            return None
        except Exception as e:
            logger.error(f"Error retrieving current HCD for user {user_id}: {e}")
            raise
    
    async def get_health_context_document_by_version(
        self, 
        user_id: UUID, 
        version: int
    ) -> Optional[HealthContextDocumentResponse]:
        """
        Get a specific version of a Health Context Document.
        
        Args:
            user_id: User ID
            version: Version number
            
        Returns:
            HCD or None if not found
        """
        try:
            hcd = self.db.query(HealthContextDocument)\
                .filter(HealthContextDocument.user_id == user_id)\
                .filter(HealthContextDocument.version == version)\
                .first()
            
            if hcd:
                return HealthContextDocumentResponse.model_validate(hcd)
            return None
        except Exception as e:
            logger.error(f"Error retrieving HCD version {version} for user {user_id}: {e}")
            raise
    
    async def get_health_context_document_history(
        self, 
        user_id: UUID, 
        limit: int = 10, 
        offset: int = 0
    ) -> HealthContextDocumentListResponse:
        """
        Get the version history of Health Context Documents for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            
        Returns:
            List of HCDs with metadata
        """
        try:
            # Get total count
            total_count = self.db.query(HealthContextDocument)\
                .filter(HealthContextDocument.user_id == user_id)\
                .count()
            
            # Get documents
            hcds = self.db.query(HealthContextDocument)\
                .filter(HealthContextDocument.user_id == user_id)\
                .order_by(HealthContextDocument.version.desc())\
                .offset(offset)\
                .limit(limit)\
                .all()
            
            # Get active version
            active_hcd = self.db.query(HealthContextDocument)\
                .filter(HealthContextDocument.user_id == user_id)\
                .filter(HealthContextDocument.is_active == True)\
                .first()
            
            active_version = active_hcd.version if active_hcd else None
            
            documents = [HealthContextDocumentResponse.model_validate(hcd) for hcd in hcds]
            
            return HealthContextDocumentListResponse(
                documents=documents,
                total_count=total_count,
                active_version=active_version
            )
        except Exception as e:
            logger.error(f"Error retrieving HCD history for user {user_id}: {e}")
            raise
    
    async def update_health_context_from_profile(self, user_id: UUID) -> HealthContextDocumentResponse:
        """
        Create a new HCD version from the user's current profile, goals, and preferences.
        
        Args:
            user_id: User ID
            
        Returns:
            New HCD version
            
        Raises:
            ValueError: If user or required data not found
        """
        try:
            # Get user profile
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            
            # Get health goals
            goals = self.db.query(HealthGoals).filter(HealthGoals.user_id == user_id).first()
            if not goals:
                raise ValueError("Health goals not found for user")
            
            # Get diet preferences
            preferences = self.db.query(DietPreferences).filter(DietPreferences.user_id == user_id).first()
            if not preferences:
                raise ValueError("Diet preferences not found for user")
            
            # Convert to dictionaries for HCD generation
            user_profile = {
                'name': user.name,
                'age': user.age,
                'gender': user.gender,
                'height_cm': user.height_cm,
                'weight_kg': user.weight_kg,
                'body_fat_percentage': user.body_fat_percentage,
                'muscle_mass_kg': user.muscle_mass_kg,
                'activity_level': user.activity_level
            }
            
            health_goals = {
                'primary_goal': goals.primary_goal,
                'target_weight_kg': goals.target_weight_kg,
                'timeline_weeks': goals.timeline_weeks
            }
            
            diet_preferences = {
                'diet_type': preferences.diet_type,
                'allergies': preferences.allergies or [],
                'foods_to_avoid': preferences.foods_to_avoid or [],
                'meals_per_day': preferences.meals_per_day,
                'budget_constraints': preferences.budget_constraints,
                'lifestyle_constraints': preferences.lifestyle_constraints
            }
            
            # Create HCD data
            hcd_data = HealthContextDocumentCreate(
                user_profile=user_profile,
                health_goals=health_goals,
                diet_preferences=diet_preferences
            )
            
            # Create new HCD
            return await self.create_health_context_document(user_id, hcd_data)
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error updating HCD from profile for user {user_id}: {e}")
            raise
    
    async def get_health_context_metrics(
        self, 
        user_id: UUID, 
        version: Optional[int] = None
    ) -> Optional[HealthContextMetrics]:
        """
        Get calculated health metrics from a Health Context Document.
        
        Args:
            user_id: User ID
            version: Version number (uses active version if None)
            
        Returns:
            Health metrics or None if not found
        """
        try:
            if version is not None:
                hcd = await self.get_health_context_document_by_version(user_id, version)
            else:
                hcd = await self.get_current_health_context_document(user_id)
            
            if not hcd:
                return None
            
            # For now, return basic metrics from HCD
            # In a full implementation, this could parse the content for additional metrics
            return HealthContextMetrics(
                bmr_calories=hcd.bmr_calories,
                tdee_calories=hcd.tdee_calories,
                min_daily_calories=hcd.min_daily_calories,
                max_calorie_deficit=hcd.max_calorie_deficit,
                min_protein_grams=hcd.min_protein_grams,
                target_calories=hcd.tdee_calories - (hcd.max_calorie_deficit / 2),  # Conservative target
                protein_target_grams=hcd.min_protein_grams * 1.2,  # 20% above minimum
                fat_target_grams=(hcd.tdee_calories * 0.25) / 9,  # 25% of calories from fat
                carb_target_grams=((hcd.tdee_calories * 0.5) / 4),  # 50% of calories from carbs
                estimated_weight_change_per_week=-0.5  # Conservative estimate
            )
        except Exception as e:
            logger.error(f"Error retrieving HCD metrics for user {user_id}: {e}")
            raise
    
    async def delete_health_context_document_version(self, user_id: UUID, version: int) -> bool:
        """
        Delete a specific version of a Health Context Document.
        
        Args:
            user_id: User ID
            version: Version number
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            ValueError: If trying to delete the active version
        """
        try:
            hcd = self.db.query(HealthContextDocument)\
                .filter(HealthContextDocument.user_id == user_id)\
                .filter(HealthContextDocument.version == version)\
                .first()
            
            if not hcd:
                return False
            
            if hcd.is_active:
                raise ValueError("Cannot delete the active version. Activate another version first.")
            
            self.db.delete(hcd)
            self.db.commit()
            
            logger.info(f"Deleted HCD version {version} for user {user_id}")
            
            return True
        except ValueError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting HCD version {version} for user {user_id}: {e}")
            raise
    
    async def activate_health_context_document_version(
        self, 
        user_id: UUID, 
        version: int
    ) -> Optional[HealthContextDocumentResponse]:
        """
        Activate a specific version of a Health Context Document.
        
        Args:
            user_id: User ID
            version: Version number to activate
            
        Returns:
            Activated HCD or None if not found
        """
        try:
            hcd = self.db.query(HealthContextDocument)\
                .filter(HealthContextDocument.user_id == user_id)\
                .filter(HealthContextDocument.version == version)\
                .first()
            
            if not hcd:
                return None
            
            # Deactivate all other versions
            self.db.query(HealthContextDocument)\
                .filter(HealthContextDocument.user_id == user_id)\
                .update({"is_active": False})
            
            # Activate the specified version
            hcd.is_active = True
            
            self.db.commit()
            self.db.refresh(hcd)
            
            logger.info(f"Activated HCD version {version} for user {user_id}")
            
            return HealthContextDocumentResponse.model_validate(hcd)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error activating HCD version {version} for user {user_id}: {e}")
            raise
