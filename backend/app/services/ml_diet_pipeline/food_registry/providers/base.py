"""
Food registry provider interface
"""

from abc import ABC, abstractmethod
from typing import List

from app.models.food_items import FoodItem


class FoodRegistryProvider(ABC):
    """Interface for pluggable food registry data sources"""

    @abstractmethod
    def fetch_foods(self) -> List[FoodItem]:
        """Fetch the full dataset (initially full load)."""
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, food_id: str) -> FoodItem:
        """Fetch a single food item by provider-specific ID."""
        raise NotImplementedError
