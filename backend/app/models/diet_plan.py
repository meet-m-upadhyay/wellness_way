"""
Diet Plan SQLAlchemy ORM model
"""

from sqlalchemy import Column, String, Date, DateTime, JSON, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.database.connection import Base


class DietPlan(Base):
    """Diet plan model for storing generated meal plans"""
    __tablename__ = "diet_plans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)  # Foreign key to users
    hcd_id = Column(UUID(as_uuid=True), nullable=False)  # Foreign key to health_context_documents
    plan_type = Column(String(20), nullable=False)  # 'weekly' or 'daily'
    start_date = Column(Date, nullable=False)
    content = Column(JSON, nullable=False)  # JSON structure with meals and nutrition
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        # Plan type constraints
        CheckConstraint("plan_type IN ('weekly', 'daily')", name='check_plan_type_values'),
    )