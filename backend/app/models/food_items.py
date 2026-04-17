"""
Food registry SQLAlchemy ORM model
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from app.database.connection import Base


class FoodItem(Base):
    """Food registry item (immutable macro truth)"""
    __tablename__ = "food_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    canonical_name = Column(String(255), nullable=False)
    dataset_source = Column(String(50), nullable=False)
    dataset_food_id = Column(String(100), nullable=False)
    registry_version = Column(Integer, nullable=False)

    macros = Column(JSONB, nullable=False)
    diet_flags = Column(JSONB, nullable=False, default=list)
    allergen_flags = Column(JSONB, nullable=False, default=list)
    cuisine_tags = Column(JSONB, nullable=False, default=list)

    is_deprecated = Column(Boolean, default=False, nullable=False)
    api_verified = Column(Boolean, default=False, nullable=False, server_default="false")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("dataset_source", "dataset_food_id", name="uq_food_items_dataset_source_id"),
        CheckConstraint("registry_version > 0", name="check_food_items_registry_version"),
    )
