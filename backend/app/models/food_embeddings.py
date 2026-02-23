"""
Food embeddings SQLAlchemy ORM model
"""

from sqlalchemy import Column, String, DateTime, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from app.database.connection import Base


class FoodEmbedding(Base):
    """Embedding record for a food item"""
    __tablename__ = "food_embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    food_id = Column(UUID(as_uuid=True), nullable=False)

    embedding_vector = Column(JSONB, nullable=False)
    normalized_text_used_for_embedding = Column(String(255), nullable=False)
    preprocessing_version = Column(String(50), nullable=False)
    embedding_model_name = Column(String(100), nullable=False)
    embedding_model_version = Column(String(50), nullable=False)

    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "food_id",
            "embedding_model_name",
            "embedding_model_version",
            "preprocessing_version",
            name="uq_food_embeddings_versioning",
        ),
        CheckConstraint("length(normalized_text_used_for_embedding) > 0", name="check_embedding_text_nonempty"),
    )
