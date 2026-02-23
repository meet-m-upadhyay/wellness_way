"""
Food registry audit log SQLAlchemy ORM model
"""

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from app.database.connection import Base


class FoodAuditLog(Base):
    """Audit log for food registry manual overrides and corrections"""
    __tablename__ = "food_audit_log"

    audit_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    food_id = Column(UUID(as_uuid=True), nullable=False)
    field_changed = Column(String(100), nullable=False)
    old_value = Column(JSONB, nullable=True)
    new_value = Column(JSONB, nullable=True)
    changed_by = Column(String(255), nullable=False)
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    reason = Column(Text, nullable=True)
