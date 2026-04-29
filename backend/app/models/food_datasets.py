"""
Food dataset registry SQLAlchemy ORM model
"""

from sqlalchemy import Column, String, DateTime, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.database.connection import Base


class FoodDataset(Base):
    """Dataset-level versioning metadata"""
    __tablename__ = "food_datasets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    dataset_name = Column(String(50), nullable=False)
    dataset_version = Column(String(50), nullable=False)
    import_batch_id = Column(UUID(as_uuid=True), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("dataset_name", "dataset_version", name="uq_food_datasets_name_version"),
        CheckConstraint("length(dataset_name) > 0", name="check_food_datasets_name"),
        CheckConstraint("length(dataset_version) > 0", name="check_food_datasets_version"),
    )
