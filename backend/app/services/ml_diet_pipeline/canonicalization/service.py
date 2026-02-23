"""
Ingredient canonicalization service (FAISS + embeddings)
"""

from __future__ import annotations

import logging
from typing import Dict, List, Tuple

from sqlalchemy.orm import Session

from app.models.food_items import FoodItem
from app.services.ml_diet_pipeline.embeddings.generator import EmbeddingGenerator
from app.services.ml_diet_pipeline.embeddings.faiss_index import FaissIndex


logger = logging.getLogger(__name__)


class CanonicalizationError(Exception):
    """Raised when canonicalization fails below threshold."""


class IngredientCanonicalizer:
    """Canonicalize ingredient names using embeddings + FAISS."""

    def __init__(
        self,
        db: Session,
        index: FaissIndex,
        embedding_ids: List[str],
        embedding_generator: EmbeddingGenerator,
        accept_threshold: float = 0.90,
        warn_threshold: float = 0.80,
    ) -> None:
        self._db = db
        self._index = index
        self._embedding_ids = embedding_ids
        self._embedding_generator = embedding_generator
        self._accept_threshold = accept_threshold
        self._warn_threshold = warn_threshold

    def canonicalize(self, raw_name: str) -> Dict:
        query_embedding = self._embedding_generator.generate([raw_name])[0]
        distances, indices = self._index.search(query_embedding, top_k=5)

        scored = self._build_scores(distances, indices)
        best = scored[0]

        if best["confidence"] < self._warn_threshold:
            logger.error(
                "[CANONICALIZATION_REJECTED] name=%s confidence=%.3f",
                raw_name,
                best["confidence"],
            )
            raise CanonicalizationError("Confidence below threshold.")

        if best["confidence"] < self._accept_threshold:
            logger.warning(
                "[CANONICALIZATION_LOW_CONF] name=%s confidence=%.3f",
                raw_name,
                best["confidence"],
            )

        result = {
            "ingredient_id": best["ingredient_id"],
            "canonical_name": best["canonical_name"],
            "confidence": best["confidence"],
            "matched_on": "embedding",
            "modifiers": [],
            "top_alternatives": [
                {"ingredient_id": item["ingredient_id"], "confidence": item["confidence"]}
                for item in scored[1:]
            ],
        }
        return result

    def _build_scores(self, distances: List[float], indices: List[int]) -> List[Dict]:
        scored: List[Dict] = []
        for distance, index in zip(distances, indices):
            if index < 0 or index >= len(self._embedding_ids):
                continue
            food_id = self._embedding_ids[index]
            food = self._db.query(FoodItem).filter(FoodItem.id == food_id).first()
            if not food:
                continue
            confidence = self._distance_to_confidence(distance)
            scored.append(
                {
                    "ingredient_id": str(food.id),
                    "canonical_name": food.canonical_name,
                    "confidence": confidence,
                }
            )
        if not scored:
            raise CanonicalizationError("No candidates returned from FAISS.")
        return scored

    def _distance_to_confidence(self, distance: float) -> float:
        if distance <= 0:
            return 1.0
        return 1.0 / (1.0 + distance)
