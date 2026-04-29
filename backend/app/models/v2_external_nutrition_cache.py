"""
V2 External nutrition cache — caches Edamam / USDA API responses
to conserve rate-limited free tiers.
"""

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from app.database.connection import Base


class V2ExternalNutritionCache(Base):
    """Cache of external nutrition API responses, keyed by query string."""
    __tablename__ = "v2_external_nutrition_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_key = Column(String(255), nullable=False, unique=True)   # lowercase, trimmed
    provider = Column(String(50), nullable=False)                   # 'edamam' or 'usda'
    response_data = Column(JSONB, nullable=False)                   # per-100g macros
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)     # optional TTL
