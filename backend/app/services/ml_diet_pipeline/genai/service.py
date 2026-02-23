"""
Constrained GenAI service wrapper
"""

from __future__ import annotations

import logging
from typing import Callable, Dict, Any

from .schema import GenAIMealText


logger = logging.getLogger(__name__)


class GenAIService:
    """Schema-enforced GenAI helper"""

    def __init__(self, generator: Callable[[Dict[str, Any]], Dict[str, Any]]) -> None:
        self._generator = generator

    def generate_meal_text(self, payload: Dict[str, Any]) -> GenAIMealText:
        raw = self._generator(payload)
        try:
            validated = GenAIMealText.model_validate(raw)
            logger.info("[GENAI_SCHEMA_VALID]")
            return validated
        except Exception:
            logger.warning("[GENAI_SCHEMA_INVALID_FALLBACK]")
            return GenAIMealText(
                meal_name=payload.get("fallback_name", "Meal"),
                description=payload.get("fallback_description", "Meal description."),
                prep_time_minutes=0,
                cook_time_minutes=0,
                servings=1,
                steps=["Prepare ingredients", "Assemble meal"],
            )
