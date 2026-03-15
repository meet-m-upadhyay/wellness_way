"""
CSV Food registry provider
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Iterable
from uuid import uuid4

from app.models.food_items import FoodItem
from .base import FoodRegistryProvider


@dataclass(frozen=True)
class CSVProviderConfig:
    dataset_name: str
    dataset_version: str
    registry_version: int
    source_path: str
    column_map: Dict[str, str]


class CSVFoodRegistryProvider(FoodRegistryProvider):
    """CSV-based provider with column mapping"""

    def __init__(self, config: CSVProviderConfig) -> None:
        self._config = config

    def fetch_foods(self) -> List[FoodItem]:
        foods: List[FoodItem] = []
        for row in self._load_rows():
            item = self._row_to_food_item(row)
            if item is not None:
                foods.append(item)
        return foods

    def get_by_id(self, food_id: str) -> FoodItem:
        for row in self._load_rows():
            if str(row.get(self._config.column_map["dataset_food_id"], "")).strip() == str(food_id):
                item = self._row_to_food_item(row)
                if item is not None:
                    return item
        raise KeyError(f"CSV food id not found: {food_id}")

    def iter_foods(self, batch_size: int = 1000) -> Iterable[List[FoodItem]]:
        batch: List[FoodItem] = []
        for row in self._load_rows():
            item = self._row_to_food_item(row)
            if item is None:
                continue
            batch.append(item)
            if len(batch) >= batch_size:
                yield batch
                batch = []
        if batch:
            yield batch

    def _load_rows(self) -> Iterable[Dict[str, Any]]:
        with open(self._config.source_path, "r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                yield row

    def _row_to_food_item(self, row: Dict[str, Any]) -> Optional[FoodItem]:
        def get_float(field: str) -> Optional[float]:
            value = row.get(self._config.column_map.get(field, ""))
            if value is None:
                return None
            try:
                return float(value)
            except (TypeError, ValueError):
                return None

        macros = {
            "calories": get_float("calories"),
            "protein": get_float("protein"),
            "fat": get_float("fat"),
            "carbohydrates": get_float("carbohydrates"),
        }

        if any(value is None for value in macros.values()):
            return None

        return FoodItem(
            id=uuid4(),
            canonical_name=str(row.get(self._config.column_map["canonical_name"], "")).strip(),
            dataset_source=self._config.dataset_name,
            dataset_food_id=str(row.get(self._config.column_map["dataset_food_id"], "")).strip(),
            registry_version=self._config.registry_version,
            macros=macros,
            diet_flags=[],
            allergen_flags=[],
            cuisine_tags=[],
            is_deprecated=False,
        )
