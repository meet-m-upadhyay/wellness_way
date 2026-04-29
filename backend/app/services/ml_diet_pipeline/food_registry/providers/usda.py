"""
USDA FoodData Central registry provider
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Iterable, List, Dict, Any, Optional
from uuid import uuid4

from app.models.food_items import FoodItem
from .base import FoodRegistryProvider


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class USDAProviderConfig:
    dataset_name: str
    dataset_version: str
    registry_version: int
    source_path: Optional[str] = None


class USDAFoodRegistryProvider(FoodRegistryProvider):
    """USDA FoodData Central provider (full load, batch iteration)"""

    def __init__(
        self,
        config: USDAProviderConfig,
        records: Optional[Iterable[Dict[str, Any]]] = None,
        include_data_types: Optional[Iterable[str]] = None,
    ) -> None:
        self._config = config
        self._records = list(records) if records is not None else None
        self._include_data_types = set(include_data_types or {"Foundation", "SR Legacy"})

        if self._records is None and not self._config.source_path:
            raise ValueError("USDA provider requires source_path or records.")

    def fetch_foods(self) -> List[FoodItem]:
        foods: List[FoodItem] = []
        for record in self._load_records():
            if not self._is_whole_ingredient(record):
                continue
            item = self._record_to_food_item(record)
            if item is not None:
                foods.append(item)
        return foods

    def get_by_id(self, food_id: str) -> FoodItem:
        for record in self._load_records():
            if str(record.get("fdcId", "")) == str(food_id):
                item = self._record_to_food_item(record)
                if item is None:
                    break
                return item
        raise KeyError(f"USDA food id not found: {food_id}")

    def iter_foods(self, batch_size: int = 1000) -> Iterable[List[FoodItem]]:
        batch: List[FoodItem] = []
        for record in self._load_records():
            if not self._is_whole_ingredient(record):
                continue
            item = self._record_to_food_item(record)
            if item is None:
                continue
            batch.append(item)
            if len(batch) >= batch_size:
                yield batch
                batch = []
        if batch:
            yield batch

    def _load_records(self) -> Iterable[Dict[str, Any]]:
        if self._records is not None:
            return self._records

        records: List[Dict[str, Any]] = []
        with open(self._config.source_path, "r", encoding="utf-8") as handle:
            raw = handle.read().strip()
            if raw.startswith("["):
                records = json.loads(raw)
            else:
                for line in raw.splitlines():
                    if not line.strip():
                        continue
                    records.append(json.loads(line))
        self._records = records
        return records

    def _is_whole_ingredient(self, record: Dict[str, Any]) -> bool:
        data_type = record.get("dataType")
        if data_type and data_type not in self._include_data_types:
            return False
        if data_type == "Branded":
            return False
        return True

    def _record_to_food_item(self, record: Dict[str, Any]) -> Optional[FoodItem]:
        macros = self._extract_macros(record)
        if macros is None:
            return None

        return FoodItem(
            id=uuid4(),
            canonical_name=str(record.get("description", "")).strip(),
            dataset_source=self._config.dataset_name,
            dataset_food_id=str(record.get("fdcId", "")).strip(),
            registry_version=self._config.registry_version,
            macros=macros,
            diet_flags=[],
            allergen_flags=[],
            cuisine_tags=[],
            is_deprecated=False,
        )

    def _extract_macros(self, record: Dict[str, Any]) -> Optional[Dict[str, float]]:
        nutrients = record.get("foodNutrients") or []
        if not isinstance(nutrients, list):
            return None

        def find_value(names: Iterable[str]) -> Optional[float]:
            for nutrient in nutrients:
                nutrient_name = (
                    str(nutrient.get("nutrientName") or nutrient.get("name") or "")
                ).lower()
                if nutrient_name in names:
                    value = nutrient.get("value")
                    if value is None:
                        return None
                    try:
                        return float(value)
                    except (TypeError, ValueError):
                        return None
            return None

        calories = find_value({"energy", "energy (kcal)"})
        protein = find_value({"protein"})
        fat = find_value({"total lipid (fat)", "fat"})
        carbs = find_value({"carbohydrate, by difference", "carbohydrate"})

        if any(value is None for value in (calories, protein, fat, carbs)):
            logger.warning(
                "Skipping USDA record %s due to missing macros.",
                record.get("fdcId"),
            )
            return None

        return {
            "calories": calories,
            "protein": protein,
            "fat": fat,
            "carbohydrates": carbs,
        }
