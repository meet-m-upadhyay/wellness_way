"""
Structured logging helpers for ML pipeline
"""

from __future__ import annotations

import logging
from typing import Optional


logger = logging.getLogger("ml_diet_pipeline")


def log_event(event: str, request_id: Optional[str] = None, **kwargs) -> None:
    payload = {"event": event, **kwargs}
    if request_id:
        payload["request_id"] = request_id
    logger.info(payload)
