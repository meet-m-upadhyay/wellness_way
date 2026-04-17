"""
NutritionResolver — orchestrates cache, API providers, name simplification,
and LLM substitution to resolve ingredient names to FoodItem-compatible objects.
"""

from __future__ import annotations

import logging
import re
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.models.food_items import FoodItem
from app.services.ml_diet_pipeline.nutrition.providers.base import (
    NutritionProvider,
    NutritionResult,
)

logger = logging.getLogger(__name__)

_MAX_SIMPLIFY_ROUNDS = 3


# ---------------------------------------------------------------------------
# Module-level helper
# ---------------------------------------------------------------------------

def simplify_name(name: str) -> Optional[str]:
    """Progressively simplify a food name.

    Strategy (applied in order, first match wins):
      1. Remove parenthetical: "Paneer (Low Fat)" -> "Paneer"
      2. Remove leading qualifier word: "Amritsari Fish Tikka" -> "Fish Tikka"
      3. Remove trailing qualifier word: "Fish Tikka" -> "Fish"

    Returns ``None`` when the name cannot be simplified further (single word
    or empty after stripping).
    """
    stripped = name.strip()
    if not stripped:
        return None

    # 1. Remove parenthetical content
    without_parens = re.sub(r"\s*\([^)]*\)", "", stripped).strip()
    if without_parens and without_parens != stripped:
        return without_parens

    # 2 & 3. Need at least two words to simplify further
    words = stripped.split()
    if len(words) <= 1:
        return None

    # 2. Remove leading word
    return " ".join(words[1:])


# ---------------------------------------------------------------------------
# Lightweight value object returned by the resolver
# ---------------------------------------------------------------------------

class ResolvedIngredient:
    """FoodItem-compatible object holding resolved nutrition data."""

    def __init__(
        self,
        *,
        id: Any = None,
        canonical_name: str,
        macros: Dict[str, float],
        diet_flags: List[str] | None = None,
        cuisine_tags: List[str] | None = None,
        allergen_flags: List[str] | None = None,
        dataset_source: str = "unknown",
        is_deprecated: bool = False,
    ) -> None:
        self.id = id or uuid.uuid4()
        self.canonical_name = canonical_name
        self.macros = macros
        self.diet_flags = diet_flags or []
        self.cuisine_tags = cuisine_tags or []
        self.allergen_flags = allergen_flags or []
        self.dataset_source = dataset_source
        self.is_deprecated = is_deprecated


# ---------------------------------------------------------------------------
# Main resolver
# ---------------------------------------------------------------------------

class NutritionResolver:
    """Orchestrates DB cache, API providers, name simplification, and LLM
    substitution to resolve ingredient names into nutrition data."""

    def __init__(
        self,
        db: Session,
        primary_provider: Optional[NutritionProvider] = None,
        fallback_provider: Optional[NutritionProvider] = None,
        llm_generator: Optional[Any] = None,
    ) -> None:
        self._db = db
        self._primary = primary_provider
        self._fallback = fallback_provider
        self._llm = llm_generator

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def resolve_portfolio(
        self,
        ingredients: List[Dict[str, Any]],
        diet_type: Optional[str] = None,
        cuisine: Optional[str] = None,
    ) -> Dict[str, List[ResolvedIngredient]]:
        """Resolve a list of ingredient dicts and group by category.

        Each dict is expected to have at least ``"name"``; optional keys:
        ``"category"``, ``"diet_flags"``, ``"cuisine_tags"``, ``"allergen_flags"``.
        """
        result_map: Dict[str, List[ResolvedIngredient]] = {
            "protein": [],
            "starch": [],
            "vegetables": [],
            "fat": [],
        }

        total = len(ingredients)
        resolved_count = 0

        for ing in ingredients:
            name = ing.get("name", "")
            category = ing.get("category", "protein")
            diet_flags = ing.get("diet_flags") or (
                [diet_type] if diet_type else []
            )
            cuisine_tags = ing.get("cuisine_tags") or (
                [cuisine] if cuisine else []
            )
            allergen_flags = ing.get("allergen_flags") or []

            resolved = await self.resolve_one(
                ingredient_name=name,
                diet_flags=diet_flags,
                cuisine_tags=cuisine_tags,
                allergen_flags=allergen_flags,
                category=category,
            )

            if resolved is not None:
                bucket = category if category in result_map else "protein"
                result_map[bucket].append(resolved)
                resolved_count += 1
            else:
                logger.warning(
                    f"[DEBUG][NUTRITION_RESOLVE_FAIL] ingredient={name} "
                    f"category={category}"
                )

        logger.info(
            f"[DEBUG][NUTRITION_RESOLVE_COMPLETE] resolved={resolved_count}/{total}"
        )
        return result_map

    async def resolve_one(
        self,
        ingredient_name: str,
        diet_flags: Optional[List[str]] = None,
        cuisine_tags: Optional[List[str]] = None,
        allergen_flags: Optional[List[str]] = None,
        category: Optional[str] = None,
    ) -> Optional[ResolvedIngredient]:
        """Full resolution chain for a single ingredient name.

        Order:
          1. DB cache (ILIKE, api_verified=True)
          2. Primary API (CalorieNinjas)
          3. Fallback API (USDA)
          4. Name simplification (up to 3 rounds, retry cache+API each round)
          5. LLM substitution
          6. None on total failure
        """
        diet_flags = diet_flags or []
        cuisine_tags = cuisine_tags or []
        allergen_flags = allergen_flags or []

        # --- Step 1: cache ---
        cached = self._cache_lookup(ingredient_name)
        if cached is not None:
            logger.info(
                f"[DEBUG][NUTRITION_CACHE_HIT] ingredient={ingredient_name}"
            )
            return self._food_item_to_resolved(cached)

        # --- Step 2 & 3: API lookup ---
        api_result = await self._api_lookup(ingredient_name)
        if api_result is not None:
            logger.info(
                f"[DEBUG][NUTRITION_API_HIT] ingredient={ingredient_name} "
                f"source={api_result.source}"
            )
            return self._cache_and_return(
                api_result, diet_flags, cuisine_tags, allergen_flags
            )

        # --- Step 4: simplification loop ---
        current_name = ingredient_name
        for round_num in range(1, _MAX_SIMPLIFY_ROUNDS + 1):
            simplified = simplify_name(current_name)
            if simplified is None:
                break
            logger.info(
                f"[DEBUG][NUTRITION_SIMPLIFY] round={round_num} "
                f"original={ingredient_name} simplified={simplified}"
            )
            current_name = simplified

            cached = self._cache_lookup(simplified)
            if cached is not None:
                logger.info(
                    f"[DEBUG][NUTRITION_CACHE_HIT_SIMPLIFIED] "
                    f"ingredient={simplified}"
                )
                return self._food_item_to_resolved(cached)

            api_result = await self._api_lookup(simplified)
            if api_result is not None:
                logger.info(
                    f"[DEBUG][NUTRITION_API_HIT_SIMPLIFIED] "
                    f"ingredient={simplified} source={api_result.source}"
                )
                return self._cache_and_return(
                    api_result, diet_flags, cuisine_tags, allergen_flags
                )

        # --- Step 5: LLM substitution ---
        substitute_name = await self._ask_llm_substitute(
            ingredient_name, diet_flags, cuisine_tags, category
        )
        if substitute_name is not None:
            logger.info(
                f"[DEBUG][NUTRITION_LLM_SUBSTITUTE] original={ingredient_name} "
                f"substitute={substitute_name}"
            )
            cached = self._cache_lookup(substitute_name)
            if cached is not None:
                return self._food_item_to_resolved(cached)

            api_result = await self._api_lookup(substitute_name)
            if api_result is not None:
                return self._cache_and_return(
                    api_result, diet_flags, cuisine_tags, allergen_flags
                )

        # --- Step 6: total failure ---
        logger.warning(
            f"[DEBUG][NUTRITION_UNRESOLVED] ingredient={ingredient_name}"
        )
        return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _cache_lookup(self, name: str) -> Optional[FoodItem]:
        """Fuzzy ILIKE cache lookup for an api_verified food item."""
        try:
            return (
                self._db.query(FoodItem)
                .filter(
                    FoodItem.canonical_name.ilike(f"%{name}%"),
                    FoodItem.api_verified.is_(True),
                )
                .first()
            )
        except Exception as exc:
            logger.error(
                f"[DEBUG][NUTRITION_CACHE_ERROR] name={name} error={exc}"
            )
            return None

    async def _api_lookup(self, name: str) -> Optional[NutritionResult]:
        """Try primary provider, then fallback."""
        if self._primary is not None:
            result = await self._primary.lookup(name)
            if result is not None:
                return result

        if self._fallback is not None:
            result = await self._fallback.lookup(name)
            if result is not None:
                return result

        return None

    def _cache_and_return(
        self,
        api_result: NutritionResult,
        diet_flags: List[str],
        cuisine_tags: List[str],
        allergen_flags: List[str],
        existing_item: Optional[FoodItem] = None,
    ) -> ResolvedIngredient:
        """Persist API result into the DB cache and return a ResolvedIngredient.

        If *existing_item* is given (an unverified row) we update it in place;
        otherwise we insert a new row.
        """
        macros = api_result.to_macros_dict()
        source = api_result.source
        name_snake = re.sub(r"\s+", "_", api_result.name.strip().lower())
        food_id = f"{source}_{name_snake}"

        if existing_item is not None:
            try:
                existing_item.macros = macros
                existing_item.api_verified = True
                flag_modified(existing_item, "macros")
                self._db.commit()
                logger.info(
                    f"[DEBUG][NUTRITION_CACHE_UPDATE] "
                    f"name={existing_item.canonical_name}"
                )
            except Exception as exc:
                self._db.rollback()
                logger.error(
                    f"[DEBUG][NUTRITION_CACHE_UPDATE_ERROR] error={exc}"
                )
            return ResolvedIngredient(
                id=existing_item.id,
                canonical_name=existing_item.canonical_name,
                macros=macros,
                diet_flags=diet_flags,
                cuisine_tags=cuisine_tags,
                allergen_flags=allergen_flags,
                dataset_source=source,
                is_deprecated=False,
            )

        # New item
        new_item = FoodItem(
            canonical_name=api_result.name,
            dataset_source=source,
            dataset_food_id=food_id,
            registry_version=1,
            macros=macros,
            diet_flags=diet_flags,
            cuisine_tags=cuisine_tags,
            allergen_flags=allergen_flags,
            is_deprecated=False,
            api_verified=True,
        )
        try:
            self._db.add(new_item)
            self._db.commit()
            logger.info(
                f"[DEBUG][NUTRITION_CACHE_INSERT] name={api_result.name} "
                f"source={source}"
            )
        except Exception as exc:
            self._db.rollback()
            logger.error(
                f"[DEBUG][NUTRITION_CACHE_INSERT_ERROR] "
                f"name={api_result.name} error={exc}"
            )

        return ResolvedIngredient(
            id=new_item.id,
            canonical_name=api_result.name,
            macros=macros,
            diet_flags=diet_flags,
            cuisine_tags=cuisine_tags,
            allergen_flags=allergen_flags,
            dataset_source=source,
            is_deprecated=False,
        )

    async def _ask_llm_substitute(
        self,
        original_name: str,
        diet_flags: List[str],
        cuisine_tags: List[str],
        category: Optional[str],
    ) -> Optional[str]:
        """Ask the LLM generator for a nutritionally similar substitute."""
        if self._llm is None:
            return None
        try:
            import json
            diet_str = ", ".join(diet_flags) if diet_flags else "any"
            cuisine_str = ", ".join(cuisine_tags) if cuisine_tags else "any"
            payload = {
                "action": "suggest_substitute",
                "original_ingredient": original_name,
                "diet_type": diet_str,
                "cuisine": cuisine_str,
                "category": category or "protein",
            }
            raw = await self._llm(payload)
            if raw and isinstance(raw, dict) and "substitute" in raw:
                substitute = raw["substitute"]
                logger.info(
                    f"[DEBUG][NUTRITION_LLM_SUBSTITUTE] original=\"{original_name}\" "
                    f"substitute=\"{substitute}\""
                )
                return substitute.strip() if isinstance(substitute, str) else None
            return None
        except Exception as exc:
            logger.error(
                f"[DEBUG][NUTRITION_LLM_ERROR] original={original_name} "
                f"error={exc}"
            )
            return None

    # ------------------------------------------------------------------
    # Conversion helper
    # ------------------------------------------------------------------

    @staticmethod
    def _food_item_to_resolved(item: FoodItem) -> ResolvedIngredient:
        """Convert a FoodItem ORM instance to a ResolvedIngredient."""
        return ResolvedIngredient(
            id=item.id,
            canonical_name=item.canonical_name,
            macros=dict(item.macros) if item.macros else {},
            diet_flags=list(item.diet_flags) if item.diet_flags else [],
            cuisine_tags=list(item.cuisine_tags) if item.cuisine_tags else [],
            allergen_flags=list(item.allergen_flags) if item.allergen_flags else [],
            dataset_source=item.dataset_source,
            is_deprecated=item.is_deprecated,
        )
