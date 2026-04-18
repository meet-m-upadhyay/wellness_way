"""Tests for the V2 ingredient matcher.

These tests require a seeded v2_ingredients table.
Skip if DB is not available.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch


class TestIngredientMatcherUnit:
    """Unit tests using mocked DB."""

    def _make_matcher(self, rows_by_query=None):
        from app.services.meal_engine.matching.ingredient_matcher import IngredientMatcher
        mock_db = MagicMock()

        def mock_execute(query, params=None):
            result = MagicMock()
            if rows_by_query and params:
                key = list(params.values())[0] if params else None
                row = rows_by_query.get(key)
                result.fetchone.return_value = row
                result.fetchall.return_value = []
            else:
                result.fetchone.return_value = None
                result.fetchall.return_value = []
            return result

        mock_db.execute.side_effect = mock_execute
        # Clear class-level cache
        IngredientMatcher._name_cache = None
        return IngredientMatcher(mock_db)

    def test_match_result_found(self):
        from app.services.meal_engine.matching.ingredient_matcher import MatchResult
        r = MatchResult("A003", "Bajra", "exact", 1.0)
        assert r.found is True

    def test_match_result_not_found(self):
        from app.services.meal_engine.matching.ingredient_matcher import MatchResult
        r = MatchResult(None, "unknown", "none", 0.0)
        assert r.found is False

    def test_exact_match_returns_result(self):
        row = MagicMock()
        row.code = "A003"
        row.name = "Bajra"

        matcher = self._make_matcher({"bajra": row})
        result = asyncio.run(matcher.match("Bajra"))
        assert result.match_method == "exact"
        assert result.confidence == 1.0
        assert result.ingredient_code == "A003"

    def test_no_match_returns_none_code(self):
        matcher = self._make_matcher({})
        result = asyncio.run(matcher.match("xyznonexistent"))
        assert result.found is False
        assert result.match_method == "none"
        assert result.confidence == 0.0

    def test_empty_input_returns_none(self):
        matcher = self._make_matcher({})
        result = asyncio.run(matcher.match(""))
        assert result.found is False

    def test_clear_cache(self):
        from app.services.meal_engine.matching.ingredient_matcher import IngredientMatcher
        IngredientMatcher._name_cache = [("A001", "Test", [])]
        IngredientMatcher.clear_cache()
        assert IngredientMatcher._name_cache is None
