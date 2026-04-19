"""Tests for pairing rule validation within the scorer."""

import pytest
from unittest.mock import MagicMock
from app.services.meal_engine.scoring.scorer import MealScorer
from app.services.meal_engine.config.loader import ConfigLoader


@pytest.fixture
def scorer_with_rules():
    """Scorer with Indian pairing rules mocked."""
    mock_db = MagicMock()
    mock_db.execute.return_value.fetchall.return_value = [
        MagicMock(cuisine="indian", item="sambar",
                  preferred=["rice", "idli", "dosa", "vada"],
                  acceptable=[], incompatible=["roti", "naan"]),
        MagicMock(cuisine="indian", item="rajma",
                  preferred=["rice"], acceptable=["roti"],
                  incompatible=["dosa", "idli"]),
        MagicMock(cuisine="indian", item="biryani",
                  preferred=["raita", "curd"], acceptable=["salad"],
                  incompatible=["roti", "naan", "rice"]),
        MagicMock(cuisine="indian", item="chole",
                  preferred=["bhature", "rice", "roti"], acceptable=["naan"],
                  incompatible=["dosa"]),
    ]
    return MealScorer(db=mock_db, config=ConfigLoader())


def _meal(components, cuisine="indian"):
    return {
        "archetype": "thali",
        "cuisine": cuisine,
        "components": [{"name": c, "food_group": ""} for c in components],
        "macros": {},
    }


class TestPairingValidation:

    def test_rajma_rice_valid(self, scorer_with_rules):
        m = _meal(["rajma curry", "steamed rice"])
        r = scorer_with_rules.score_deterministic(m, {}, "maintenance")
        assert r.culinary_coherence == 20.0  # no penalty

    def test_sambar_roti_invalid(self, scorer_with_rules):
        m = _meal(["sambar", "roti"])
        r = scorer_with_rules.score_deterministic(m, {}, "maintenance")
        assert r.culinary_coherence < 20.0  # penalized

    def test_sambar_rice_valid(self, scorer_with_rules):
        m = _meal(["sambar", "rice"])
        r = scorer_with_rules.score_deterministic(m, {}, "maintenance")
        assert r.culinary_coherence == 20.0

    def test_biryani_roti_invalid(self, scorer_with_rules):
        m = _meal(["biryani", "roti"])
        r = scorer_with_rules.score_deterministic(m, {}, "maintenance")
        assert r.culinary_coherence < 20.0

    def test_biryani_raita_valid(self, scorer_with_rules):
        m = _meal(["biryani", "raita"])
        r = scorer_with_rules.score_deterministic(m, {}, "maintenance")
        assert r.culinary_coherence == 20.0

    def test_chole_dosa_invalid(self, scorer_with_rules):
        m = _meal(["chole masala", "dosa"])
        r = scorer_with_rules.score_deterministic(m, {}, "maintenance")
        assert r.culinary_coherence < 20.0

    def test_no_rules_no_penalty(self, scorer_with_rules):
        m = _meal(["paneer tikka", "naan"])
        r = scorer_with_rules.score_deterministic(m, {}, "maintenance")
        assert r.culinary_coherence == 20.0  # paneer not in rules, no penalty

    def test_non_indian_cuisine_no_indian_rules(self, scorer_with_rules):
        m = _meal(["pasta", "chicken"], cuisine="italian")
        r = scorer_with_rules.score_deterministic(m, {}, "maintenance")
        assert r.culinary_coherence == 20.0  # no italian rules loaded
