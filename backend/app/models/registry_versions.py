"""
Global food registry version SQLAlchemy ORM model
"""

from sqlalchemy import Column, Integer, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.database.connection import Base


class RegistryVersion(Base):
    """Global registry version tracking"""
    __tablename__ = "registry_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    registry_version = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("registry_version > 0", name="check_registry_version_positive"),
    )
