"""
User-related SQLAlchemy ORM models
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, JSON, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.database.connection import Base


class User(Base):
    """User profile model"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Authentication fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)  # Admin privileges
    approval_status = Column(String(20), default='approved', nullable=False)  # 'pending', 'approved', 'declined'
    
    # Profile fields
    name = Column(String(255), nullable=False)
    age = Column(Integer, nullable=True)  # Made nullable for initial registration
    gender = Column(String(20), nullable=True)  # 'male', 'female', 'other'
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    body_fat_percentage = Column(Float, nullable=True)
    muscle_mass_kg = Column(Float, nullable=True)
    activity_level = Column(String(30), nullable=True)  # Activity level enum
    
    # Profile completion status
    profile_completed = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Add constraints via SQLAlchemy CheckConstraint
    __table_args__ = (
        CheckConstraint('age IS NULL OR (age > 0 AND age < 150)', name='check_age_range'),
        CheckConstraint('height_cm IS NULL OR (height_cm > 50 AND height_cm < 300)', name='check_height_range'),
        CheckConstraint('weight_kg IS NULL OR (weight_kg > 20 AND weight_kg < 500)', name='check_weight_range'),
        CheckConstraint('body_fat_percentage IS NULL OR (body_fat_percentage >= 0 AND body_fat_percentage <= 100)', name='check_body_fat_range'),
        CheckConstraint('muscle_mass_kg IS NULL OR muscle_mass_kg >= 0', name='check_muscle_mass_range'),
        CheckConstraint("gender IS NULL OR gender IN ('male', 'female', 'other')", name='check_gender_values'),
        CheckConstraint("activity_level IS NULL OR activity_level IN ('sedentary', 'lightly_active', 'moderately_active', 'very_active', 'extremely_active')", name='check_activity_level_values'),
        CheckConstraint("approval_status IN ('pending', 'approved', 'declined')", name='check_approval_status_values'),
    )

    def is_approved(self) -> bool:
        """Check if user is approved"""
        return self.approval_status == 'approved'
    
    def set_approval_status(self, status: str) -> None:
        """Set user approval status"""
        if status in ['pending', 'approved', 'declined']:
            self.approval_status = status
        else:
            raise ValueError(f"Invalid approval status: {status}")


class HealthGoals(Base):
    """Health goals model"""
    __tablename__ = "health_goals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)  # Foreign key to users
    primary_goal = Column(String(20), nullable=False)  # 'fat_loss', 'muscle_gain', 'maintenance'
    target_weight_kg = Column(Float, nullable=True)
    timeline_weeks = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        CheckConstraint("primary_goal IN ('fat_loss', 'muscle_gain', 'maintenance')", name='check_primary_goal_values'),
        CheckConstraint('target_weight_kg IS NULL OR (target_weight_kg > 20 AND target_weight_kg < 500)', name='check_target_weight_range'),
        CheckConstraint('timeline_weeks IS NULL OR (timeline_weeks > 0 AND timeline_weeks <= 104)', name='check_timeline_range'),  # Max 2 years
    )


class DietPreferences(Base):
    """Diet preferences model"""
    __tablename__ = "diet_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)  # Foreign key to users
    diet_type = Column(String(20), nullable=False)  # 'vegetarian', 'non_vegetarian', 'vegan'
    allergies = Column(JSON, nullable=False, default=list)  # List of allergens
    foods_to_avoid = Column(JSON, nullable=False, default=list)  # List of foods to avoid
    meals_per_day = Column(Integer, nullable=False, default=3)
    cuisine = Column(String(50), nullable=False, default='indian')
    reuse_ingredients = Column(Boolean, nullable=False, default=False)
    budget_constraints = Column(Text, nullable=True)
    lifestyle_constraints = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        CheckConstraint("diet_type IN ('vegetarian', 'non_vegetarian', 'vegan')", name='check_diet_type_values'),
        CheckConstraint('meals_per_day >= 1 AND meals_per_day <= 8', name='check_meals_per_day_range'),
    )


class RegistrationRequest(Base):
    """Registration request model for admin approval system"""
    __tablename__ = "registration_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    google_id = Column(String(255), nullable=True)
    password_hash = Column(String(255), nullable=True)
    status = Column(String(20), default='pending', nullable=False, index=True)  # 'pending', 'approved', 'declined'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'approved', 'declined')", name='check_registration_status_values'),
    )
    
    def approve(self) -> None:
        """Approve the registration request"""
        self.status = 'approved'
        self.updated_at = func.now()
    
    def decline(self) -> None:
        """Decline the registration request"""
        self.status = 'declined'
        self.updated_at = func.now()
    
    def is_pending(self) -> bool:
        """Check if registration request is pending"""
        return self.status == 'pending'