"""
Embedding generation service (MiniLM)
"""

from __future__ import annotations

from typing import List

from .text_normalizer import normalize_text, PREPROCESSING_VERSION


class EmbeddingGenerator:
    """Batch embedding generator using sentence transformers"""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        model_version: str = "default",
    ) -> None:
        self.model_name = model_name
        self.model_version = model_version
        self._model = None

    def _load_model(self) -> None:
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
        except ImportError as exc:
            raise RuntimeError("sentence-transformers is required for embeddings.") from exc
        self._model = SentenceTransformer(self.model_name)

    def generate(self, texts: List[str]) -> List[List[float]]:
        self._load_model()
        normalized = [normalize_text(text) for text in texts]
        embeddings = self._model.encode(normalized, show_progress_bar=False)  # type: ignore[call-arg]
        return [embedding.tolist() for embedding in embeddings]

    @property
    def preprocessing_version(self) -> str:
        return PREPROCESSING_VERSION
