"""
Constrained GenAI schema contract
"""

from __future__ import annotations

from typing import List
from pydantic import BaseModel, Field


class GenAIMealText(BaseModel):
    meal_name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    prep_time_minutes: int = Field(..., ge=0)
    cook_time_minutes: int = Field(..., ge=0)
    servings: int = Field(..., ge=1)
    steps: List[str] = Field(..., min_items=1)
