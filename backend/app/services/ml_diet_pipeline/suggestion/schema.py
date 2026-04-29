"""Pydantic schemas for LLM meal suggestion input/output"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class LLMIngredient(BaseModel):
    """A single ingredient suggested by the LLM."""
    name: str = Field(..., min_length=1)
    category: str = Field(..., pattern="^(protein|starch|vegetables|fat)$")
    diet_flags: List[str] = Field(default_factory=list)
    cuisine_tags: List[str] = Field(default_factory=list)
    allergen_flags: List[str] = Field(default_factory=list)


class LLMMealSuggestion(BaseModel):
    """A single meal suggested by the LLM."""
    meal_type: str = Field(..., min_length=1)
    ingredients: List[LLMIngredient] = Field(..., min_length=1)


class LLMSuggestionResponse(BaseModel):
    """Top-level LLM response containing one or more meals."""
    meals: List[LLMMealSuggestion] = Field(..., min_length=1)
