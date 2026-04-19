"""
V2 Pairing rules — culturally valid food pairings, editable at runtime.
Seeded from config/pairing_rules_seed.json.
"""

from sqlalchemy import Column, String, DateTime, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
import uuid

from app.database.connection import Base


class V2PairingRule(Base):
    """Encodes culturally valid (and invalid) food pairings per cuisine."""
    __tablename__ = "v2_pairing_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cuisine = Column(String(50), nullable=False)
    item = Column(String(100), nullable=False)
    preferred = Column(ARRAY(Text), nullable=False, default=list)
    acceptable = Column(ARRAY(Text), nullable=False, default=list)
    incompatible = Column(ARRAY(Text), nullable=False, default=list)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("cuisine", "item", name="uq_v2_pairing_rules_cuisine_item"),
    )
