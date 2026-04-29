"""
Text normalization utilities for embedding generation
"""

import re

PREPROCESSING_VERSION = "v1"


def normalize_text(text: str) -> str:
    """
    Normalize text deterministically for embeddings.
    """
    normalized = text.lower().strip()
    normalized = re.sub(r"[^a-z0-9\s]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized
