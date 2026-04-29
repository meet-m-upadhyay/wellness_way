"""
Food registry import service
"""

from __future__ import annotations

from typing import Iterable, Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.models.food_items import FoodItem
from app.models.food_datasets import FoodDataset
from .providers.base import FoodRegistryProvider


def import_food_dataset(
    db: Session,
    provider: FoodRegistryProvider,
    dataset_name: str,
    dataset_version: str,
    registry_version: int,
    import_batch_id: Optional[UUID] = None,
) -> UUID:
    """
    Import food items from a provider and record dataset metadata.
    Marks existing items from the same dataset as deprecated.
    """
    batch_id = import_batch_id or uuid4()

    db.query(FoodItem).filter(
        FoodItem.dataset_source == dataset_name,
        FoodItem.is_deprecated.is_(False),
    ).update({"is_deprecated": True})

    dataset = FoodDataset(
        dataset_name=dataset_name,
        dataset_version=dataset_version,
        import_batch_id=batch_id,
    )
    db.add(dataset)

    foods = provider.fetch_foods()
    for food in foods:
        food.dataset_source = dataset_name
        food.registry_version = registry_version
        db.add(food)

    db.commit()
    return batch_id


def import_food_dataset_in_batches(
    db: Session,
    provider: FoodRegistryProvider,
    dataset_name: str,
    dataset_version: str,
    registry_version: int,
    batch_size: int = 1000,
    import_batch_id: Optional[UUID] = None,
) -> UUID:
    """
    Batch import food items for large datasets.
    """
    batch_id = import_batch_id or uuid4()

    db.query(FoodItem).filter(
        FoodItem.dataset_source == dataset_name,
        FoodItem.is_deprecated.is_(False),
    ).update({"is_deprecated": True})

    dataset = FoodDataset(
        dataset_name=dataset_name,
        dataset_version=dataset_version,
        import_batch_id=batch_id,
    )
    db.add(dataset)
    db.commit()

    for foods in provider.iter_foods(batch_size=batch_size):  # type: ignore[attr-defined]
        for food in foods:
            food.dataset_source = dataset_name
            food.registry_version = registry_version
            db.add(food)
        db.commit()

    return batch_id
