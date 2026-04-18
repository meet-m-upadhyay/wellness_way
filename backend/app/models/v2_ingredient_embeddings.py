"""
V2 Ingredient embeddings — pgvector storage for semantic ingredient matching.
Uses all-MiniLM-L6-v2 (384-dim, normalized).
"""

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.database.connection import Base

# pgvector import — lazy-safe: the column type is only evaluated at
# migration / table-creation time, not at module import.
try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    # Allow model import to succeed even if pgvector isn't installed yet.
    # The migration will fail, prompting the user to install it.
    Vector = None


class V2IngredientEmbedding(Base):
    """384-dim embedding vector for a v2_ingredient, stored via pgvector."""
    __tablename__ = "v2_ingredient_embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ingredient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("v2_ingredients.id"),
        nullable=False,
        unique=True,
    )
    embedding = Column(Vector(384) if Vector else String, nullable=False)
    text_used = Column(String(500), nullable=False)
    model_name = Column(String(100), nullable=False, server_default="all-MiniLM-L6-v2")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
