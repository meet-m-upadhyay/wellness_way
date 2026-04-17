"""Tests for NutritionResolver — cache, API, simplification, and LLM fallback."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ml_diet_pipeline.nutrition.providers.base import NutritionResult
from app.services.ml_diet_pipeline.nutrition.resolver import (
    NutritionResolver,
    ResolvedIngredient,
    simplify_name,
)


# ---------------------------------------------------------------------------
# simplify_name tests
# ---------------------------------------------------------------------------

class TestSimplifyName:
    def test_removes_parenthetical(self):
        assert simplify_name("Paneer (Low Fat)") == "Paneer"

    def test_removes_parenthetical_mid_string(self):
        assert simplify_name("Chicken (Grilled) Breast") == "Chicken Breast"

    def test_removes_leading_word_when_no_parens(self):
        assert simplify_name("Amritsari Fish Tikka") == "Fish Tikka"

    def test_removes_leading_word_two_words(self):
        assert simplify_name("Fish Tikka") == "Tikka"

    def test_single_word_returns_none(self):
        assert simplify_name("Paneer") is None

    def test_empty_string_returns_none(self):
        assert simplify_name("") is None

    def test_whitespace_only_returns_none(self):
        assert simplify_name("   ") is None

    def test_progressive_simplification(self):
        """Chain simplify_name to verify multi-round behavior."""
        name = "Amritsari Fish Tikka"
        s1 = simplify_name(name)
        assert s1 == "Fish Tikka"
        s2 = simplify_name(s1)
        assert s2 == "Tikka"
        s3 = simplify_name(s2)
        assert s3 is None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_food_item(
    name: str = "Chicken Tikka",
    macros: dict = None,
    api_verified: bool = True,
    source: str = "calorieninjas",
):
    """Return a mock FoodItem with sensible defaults."""
    item = MagicMock()
    item.id = uuid.uuid4()
    item.canonical_name = name
    item.macros = macros or {"calories": 150, "protein": 28, "fat": 3.5, "carbohydrates": 2, "fiber": 0}
    item.diet_flags = ["non-veg"]
    item.cuisine_tags = ["indian"]
    item.allergen_flags = []
    item.dataset_source = source
    item.is_deprecated = False
    item.api_verified = api_verified
    return item


def _make_nutrition_result(name: str = "Chicken Tikka", source: str = "calorieninjas"):
    return NutritionResult(
        name=name,
        calories=150.0,
        protein=28.0,
        fat=3.5,
        carbohydrates=2.0,
        fiber=0.0,
        serving_size_g=100.0,
        source=source,
    )


def _mock_db_returning(item):
    """Build a mock Session whose query().filter().first() returns *item*."""
    db = MagicMock()
    query_mock = MagicMock()
    filter_mock = MagicMock()
    filter_mock.first.return_value = item
    query_mock.filter.return_value = filter_mock
    db.query.return_value = query_mock
    return db


# ---------------------------------------------------------------------------
# resolve_one tests
# ---------------------------------------------------------------------------

class TestResolveOneCacheHit:
    @pytest.mark.asyncio
    async def test_cache_hit_skips_api(self):
        """When a verified item exists in DB, no API call is made."""
        food_item = _make_food_item()
        db = _mock_db_returning(food_item)

        primary = AsyncMock()
        primary.lookup = AsyncMock(return_value=_make_nutrition_result())

        resolver = NutritionResolver(db=db, primary_provider=primary)
        result = await resolver.resolve_one("Chicken Tikka")

        assert result is not None
        assert result.canonical_name == "Chicken Tikka"
        # Primary should never have been called
        primary.lookup.assert_not_awaited()


class TestResolveOneCacheMissCallsPrimary:
    @pytest.mark.asyncio
    async def test_cache_miss_calls_primary(self):
        """When cache returns nothing, primary provider is called."""
        db = _mock_db_returning(None)

        api_result = _make_nutrition_result()
        primary = AsyncMock()
        primary.lookup = AsyncMock(return_value=api_result)
        primary.source_name = "calorieninjas"

        resolver = NutritionResolver(db=db, primary_provider=primary)
        result = await resolver.resolve_one("Chicken Tikka")

        assert result is not None
        assert result.canonical_name == "Chicken Tikka"
        assert result.macros["protein"] == 28.0
        primary.lookup.assert_awaited_once_with("Chicken Tikka")


class TestResolveOnePrimaryMissFallsToFallback:
    @pytest.mark.asyncio
    async def test_primary_miss_uses_fallback(self):
        """When primary returns None, fallback is tried."""
        db = _mock_db_returning(None)

        primary = AsyncMock()
        primary.lookup = AsyncMock(return_value=None)

        fallback_result = _make_nutrition_result(source="usda")
        fallback = AsyncMock()
        fallback.lookup = AsyncMock(return_value=fallback_result)
        fallback.source_name = "usda"

        resolver = NutritionResolver(
            db=db, primary_provider=primary, fallback_provider=fallback
        )
        result = await resolver.resolve_one("Chicken Tikka")

        assert result is not None
        assert result.dataset_source == "usda"
        fallback.lookup.assert_awaited_once_with("Chicken Tikka")


class TestResolveOneSimplification:
    @pytest.mark.asyncio
    async def test_all_miss_triggers_simplification(self):
        """When cache + APIs miss, the name is simplified and retried."""
        # DB always misses for all calls (cache lookups with different names)
        db = _mock_db_returning(None)

        primary = AsyncMock()
        # Fail for original, succeed for simplified
        async def _primary_side_effect(name):
            if name == "Fish Tikka" or name == "Tikka":
                return None
            if name == "Amritsari Fish Tikka":
                return None
            return None
        primary.lookup = AsyncMock(side_effect=_primary_side_effect)

        fallback = AsyncMock()
        # Succeed on the simplified "Fish Tikka"
        async def _fallback_side_effect(name):
            if name == "Fish Tikka":
                return _make_nutrition_result(name="Fish Tikka", source="usda")
            return None
        fallback.lookup = AsyncMock(side_effect=_fallback_side_effect)

        resolver = NutritionResolver(
            db=db, primary_provider=primary, fallback_provider=fallback
        )
        result = await resolver.resolve_one("Amritsari Fish Tikka")

        assert result is not None
        assert result.canonical_name == "Fish Tikka"
        assert result.dataset_source == "usda"


class TestResolveOneUnresolvable:
    @pytest.mark.asyncio
    async def test_unresolvable_returns_none(self):
        """When nothing works, resolve_one returns None."""
        db = _mock_db_returning(None)

        primary = AsyncMock()
        primary.lookup = AsyncMock(return_value=None)
        fallback = AsyncMock()
        fallback.lookup = AsyncMock(return_value=None)

        resolver = NutritionResolver(
            db=db,
            primary_provider=primary,
            fallback_provider=fallback,
            llm_generator=None,
        )
        result = await resolver.resolve_one("X")

        assert result is None


class TestResolveOneLLMSubstitution:
    @pytest.mark.asyncio
    async def test_llm_substitution_tried_after_simplification(self):
        """When simplification exhausted, LLM substitute is attempted."""
        db = _mock_db_returning(None)

        primary = AsyncMock()
        primary.lookup = AsyncMock(return_value=None)
        fallback = AsyncMock()
        fallback.lookup = AsyncMock(return_value=None)

        llm = AsyncMock()
        llm.suggest_substitute = AsyncMock(return_value="Tofu")

        # Make API return result for the LLM substitute
        async def _primary_for_substitute(name):
            if name == "Tofu":
                return _make_nutrition_result(name="Tofu", source="calorieninjas")
            return None
        primary.lookup = AsyncMock(side_effect=_primary_for_substitute)

        resolver = NutritionResolver(
            db=db,
            primary_provider=primary,
            fallback_provider=fallback,
            llm_generator=llm,
        )
        result = await resolver.resolve_one("Obscure Regional Cheese")

        assert result is not None
        assert result.canonical_name == "Tofu"
        llm.suggest_substitute.assert_awaited_once()


# ---------------------------------------------------------------------------
# resolve_portfolio tests
# ---------------------------------------------------------------------------

class TestResolvePortfolio:
    @pytest.mark.asyncio
    async def test_groups_by_category(self):
        """resolved ingredients are placed in the correct category buckets."""
        food_item = _make_food_item()
        db = _mock_db_returning(food_item)

        resolver = NutritionResolver(db=db)
        ingredients = [
            {"name": "Chicken Tikka", "category": "protein"},
            {"name": "Brown Rice", "category": "starch"},
            {"name": "Spinach", "category": "vegetables"},
        ]
        result = await resolver.resolve_portfolio(ingredients)

        assert len(result["protein"]) == 1
        assert len(result["starch"]) == 1
        assert len(result["vegetables"]) == 1
        assert len(result["fat"]) == 0

    @pytest.mark.asyncio
    async def test_unknown_category_defaults_to_protein(self):
        """Unknown category falls back to 'protein' bucket."""
        food_item = _make_food_item()
        db = _mock_db_returning(food_item)

        resolver = NutritionResolver(db=db)
        ingredients = [{"name": "Mystery Item", "category": "condiment"}]
        result = await resolver.resolve_portfolio(ingredients)

        assert len(result["protein"]) == 1


# ---------------------------------------------------------------------------
# ResolvedIngredient tests
# ---------------------------------------------------------------------------

class TestResolvedIngredient:
    def test_defaults(self):
        ri = ResolvedIngredient(
            canonical_name="Paneer",
            macros={"calories": 265, "protein": 18},
        )
        assert ri.canonical_name == "Paneer"
        assert ri.diet_flags == []
        assert ri.cuisine_tags == []
        assert ri.allergen_flags == []
        assert ri.is_deprecated is False
        assert ri.id is not None

    def test_custom_fields(self):
        ri = ResolvedIngredient(
            canonical_name="Paneer",
            macros={"calories": 265},
            diet_flags=["vegetarian"],
            cuisine_tags=["indian"],
            allergen_flags=["dairy"],
            dataset_source="usda",
        )
        assert ri.diet_flags == ["vegetarian"]
        assert ri.dataset_source == "usda"


# ---------------------------------------------------------------------------
# _cache_and_return DB interaction tests
# ---------------------------------------------------------------------------

class TestCacheAndReturn:
    def test_new_item_gets_committed(self):
        """_cache_and_return adds a new FoodItem and commits."""
        db = MagicMock()
        resolver = NutritionResolver(db=db)

        api_result = _make_nutrition_result()
        ri = resolver._cache_and_return(
            api_result,
            diet_flags=["non-veg"],
            cuisine_tags=["indian"],
            allergen_flags=[],
        )

        db.add.assert_called_once()
        db.commit.assert_called_once()
        assert ri.canonical_name == "Chicken Tikka"
        assert ri.macros["protein"] == 28.0

    def test_db_write_failure_does_not_raise(self):
        """DB failures are caught; the ResolvedIngredient is still returned."""
        db = MagicMock()
        db.commit.side_effect = Exception("connection lost")

        resolver = NutritionResolver(db=db)
        api_result = _make_nutrition_result()

        # Should not raise
        ri = resolver._cache_and_return(
            api_result,
            diet_flags=[],
            cuisine_tags=[],
            allergen_flags=[],
        )

        assert ri is not None
        assert ri.canonical_name == "Chicken Tikka"
        db.rollback.assert_called_once()
