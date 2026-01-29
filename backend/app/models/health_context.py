"""
Health Context Document SQLAlchemy ORM model
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from app.database.connection import Base


class HealthContextDocument(Base):
    """Health Context Document model for versioned, immutable health profiles"""
    __tablename__ = "health_context_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)  # Foreign key to users
    version = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)  # Markdown content
    json_context = Column(JSONB, nullable=True)  # Machine-readable JSON context
    bmr_calories = Column(Float, nullable=False)
    tdee_calories = Column(Float, nullable=False)
    min_daily_calories = Column(Float, nullable=False)
    max_calorie_deficit = Column(Float, nullable=False)
    min_protein_grams = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    __table_args__ = (
        # Ensure unique version per user
        UniqueConstraint('user_id', 'version', name='uq_user_version'),
        # Calorie constraints
        CheckConstraint('bmr_calories > 0', name='check_bmr_positive'),
        CheckConstraint('tdee_calories > bmr_calories', name='check_tdee_greater_than_bmr'),
        CheckConstraint('min_daily_calories >= bmr_calories', name='check_min_calories_above_bmr'),
        CheckConstraint('max_calorie_deficit > 0', name='check_max_deficit_positive'),
        CheckConstraint('min_protein_grams > 0', name='check_min_protein_positive'),
        # Version constraints
        CheckConstraint('version > 0', name='check_version_positive'),
    )