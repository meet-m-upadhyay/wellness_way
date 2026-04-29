"""
FAISS index builder and persistence utilities
"""

from __future__ import annotations

import logging
from typing import List


logger = logging.getLogger(__name__)


class FaissIndex:
    """Wrapper around FAISS index with persistence"""

    def __init__(self, dimension: int) -> None:
        try:
            import faiss  # type: ignore
        except ImportError as exc:
            raise RuntimeError("faiss is required for indexing.") from exc
        self._faiss = faiss
        self.index = faiss.IndexFlatL2(dimension)

    def add(self, embeddings: List[List[float]]) -> None:
        import numpy as np  # type: ignore
        vectors = np.array(embeddings, dtype="float32")
        self.index.add(vectors)

    def search(self, query_embedding: List[float], top_k: int = 5):
        import numpy as np  # type: ignore
        vector = np.array([query_embedding], dtype="float32")
        distances, indices = self.index.search(vector, top_k)
        return distances[0], indices[0]

    def save(self, path: str) -> None:
        self._faiss.write_index(self.index, path)
        logger.info("[FAISS_INDEX_REBUILT] path=%s", path)

    @classmethod
    def load(cls, path: str) -> "FaissIndex":
        try:
            import faiss  # type: ignore
        except ImportError as exc:
            raise RuntimeError("faiss is required for indexing.") from exc
        index = faiss.read_index(path)
        instance = cls(dimension=index.d)
        instance.index = index
        logger.info("[FAISS_INDEX_LOADED] path=%s", path)
        return instance
