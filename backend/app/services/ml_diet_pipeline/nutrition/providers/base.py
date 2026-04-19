"""Base classes for nutrition API providers"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class NutritionResult:
    """Verified macros for a food item, normalized to per-100g."""

    name: str
    calories: float
    protein: float
    fat: float
    carbohydrates: float
    fiber: float
    serving_size_g: float
    source: str

    def to_macros_dict(self) -> dict:
        return {
            "calories": self.calories,
            "protein": self.protein,
            "fat": self.fat,
            "carbohydrates": self.carbohydrates,
            "fiber": self.fiber,
        }

    @classmethod
    def from_serving(
        cls,
        name: str,
        calories: float,
        protein: float,
        fat: float,
        carbohydrates: float,
        fiber: float,
        serving_size_g: float,
        source: str,
    ) -> NutritionResult:
        """Create a NutritionResult normalized to per-100g from a non-100g serving."""
        if serving_size_g <= 0:
            serving_size_g = 100.0
        factor = 100.0 / serving_size_g
        return cls(
            name=name,
            calories=calories * factor,
            protein=protein * factor,
            fat=fat * factor,
            carbohydrates=carbohydrates * factor,
            fiber=fiber * factor,
            serving_size_g=serving_size_g,
            source=source,
        )


class NutritionProvider(ABC):
    """Abstract base class for nutrition API providers."""

    @abstractmethod
    async def lookup(self, ingredient_name: str) -> Optional[NutritionResult]:
        """Look up macros for an ingredient. Returns None if not found."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Provider identifier for dataset_source field."""
