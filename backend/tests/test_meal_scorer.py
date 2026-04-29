"""Tests for the V2 meal engine scorer."""

import pytest
from unittest.mock import MagicMock
from app.services.meal_engine.scoring.scorer import MealScorer, ScoreBreakdown
from app.services.meal_engine.config.loader import ConfigLoader


@pytest.fixture
def scorer():
    """Scorer with mocked DB (no pairing rules loaded from DB)."""
    mock_db = MagicMock()
    mock_db.execute.return_value.fetchall.return_value = [
        MagicMock(
            cuisine="indian", item="sambar",
            preferred=["rice", "idli", "dosa", "vada"],
            acceptable=[],
            incompatible=["roti", "naan", "paratha"],
        ),
        MagicMock(
            cuisine="indian", item="rajma",
            preferred=["rice"],
            acceptable=["roti"],
            incompatible=["dosa", "idli"],
        ),
    ]
    return MealScorer(db=mock_db, config=ConfigLoader())


def _make_meal(archetype, components, macros, cuisine="indian"):
    return {
        "archetype": archetype,
        "cuisine": cuisine,
        "components": components,
        "macros": macros,
    }


class TestMacroAccuracy:

    def test_perfect_macros_score_30(self, scorer):
        meal = _make_meal("thali", [], {"calories": 600, "protein": 25, "carbs": 85, "fat": 15})
        target = {"calories": 600, "protein": 25, "carbs": 85, "fat": 15}
        r = scorer.score_deterministic(meal, target, "maintenance")
        assert r.macro_accuracy == 30.0

    def test_15pct_deviation_scores_partial(self, scorer):
        meal = _make_meal("thali", [], {"calories": 510, "protein": 21, "carbs": 72, "fat": 13})
        target = {"calories": 600, "protein": 25, "carbs": 85, "fat": 15}
        r = scorer.score_deterministic(meal, target, "maintenance")
        assert 5 < r.macro_accuracy < 25

    def test_50pct_deviation_scores_zero(self, scorer):
        meal = _make_meal("thali", [], {"calories": 300, "protein": 10, "carbs": 40, "fat": 5})
        target = {"calories": 600, "protein": 25, "carbs": 85, "fat": 15}
        r = scorer.score_deterministic(meal, target, "maintenance")
        assert r.macro_accuracy == 0


class TestPlateComposition:

    def test_four_categories_score_20(self, scorer):
        components = [
            {"name": "chicken", "food_group": "Poultry"},           # protein
            {"name": "rice", "food_group": "Cereals and Millets"},  # carb
            {"name": "ghee", "food_group": "Edible Oils and Fats"}, # fat
            {"name": "spinach", "food_group": "Green Leafy Vegetables"},  # veg
        ]
        meal = _make_meal("thali", components, {})
        r = scorer.score_deterministic(meal, {}, "maintenance")
        assert r.plate_composition == 20.0

    def test_single_category_scores_5(self, scorer):
        components = [{"name": "rice", "food_group": "Cereals and Millets"}]
        meal = _make_meal("thali", components, {})
        r = scorer.score_deterministic(meal, {}, "maintenance")
        assert r.plate_composition == 5.0


class TestCulinaryCoherence:

    def test_archetype_present_gives_10(self, scorer):
        meal = _make_meal("thali", [], {})
        r = scorer.score_deterministic(meal, {}, "maintenance")
        assert r.culinary_coherence >= 10.0

    def test_no_archetype_gives_less(self, scorer):
        meal = _make_meal("", [], {})
        r = scorer.score_deterministic(meal, {}, "maintenance")
        assert r.culinary_coherence < 20.0

    def test_sambar_roti_penalized(self, scorer):
        components = [
            {"name": "sambar dal", "food_group": "Grain Legumes"},
            {"name": "wheat roti", "food_group": "Cereals and Millets"},
        ]
        meal = _make_meal("thali", components, {}, "indian")
        r = scorer.score_deterministic(meal, {}, "maintenance")
        # sambar + roti is incompatible — should be penalized
        assert r.culinary_coherence < 20.0

    def test_rajma_rice_not_penalized(self, scorer):
        components = [
            {"name": "rajma curry", "food_group": "Grain Legumes"},
            {"name": "steamed rice", "food_group": "Cereals and Millets"},
        ]
        meal = _make_meal("thali", components, {}, "indian")
        r = scorer.score_deterministic(meal, {}, "maintenance")
        assert r.culinary_coherence == 20.0


class TestMicroDiversity:

    def test_four_groups_score_12(self, scorer):
        components = [
            {"name": "a", "food_group": "Grain Legumes"},
            {"name": "b", "food_group": "Cereals and Millets"},
            {"name": "c", "food_group": "Other Vegetables"},
            {"name": "d", "food_group": "Edible Oils and Fats"},
        ]
        meal = _make_meal("thali", components, {})
        r = scorer.score_deterministic(meal, {}, "maintenance")
        assert r.micro_diversity == 12.0

    def test_capped_at_15(self, scorer):
        components = [{"name": str(i), "food_group": f"Group{i}"} for i in range(10)]
        meal = _make_meal("thali", components, {})
        r = scorer.score_deterministic(meal, {}, "maintenance")
        assert r.micro_diversity == 15.0


class TestPracticality:

    def test_reasonable_portions_score_5(self, scorer):
        components = [
            {"name": "rice", "grams": 150},
            {"name": "dal", "grams": 100},
        ]
        meal = _make_meal("thali", components, {})
        r = scorer.score_deterministic(meal, {}, "maintenance")
        assert r.practicality == 5.0

    def test_extreme_portion_penalized(self, scorer):
        components = [{"name": "rice", "grams": 1000}]  # way over 400g
        meal = _make_meal("thali", components, {})
        r = scorer.score_deterministic(meal, {}, "maintenance")
        assert r.practicality < 5.0


class TestScoringBands:

    def test_high_score_is_serve(self, scorer):
        b = ScoreBreakdown(
            macro_accuracy=28, plate_composition=18, culinary_coherence=18,
            micro_diversity=12, goal_alignment=8, practicality=5,
        )
        b.compute_total()
        assert b.band == "serve"
        assert b.total >= 85

    def test_mid_score_is_review(self, scorer):
        b = ScoreBreakdown(
            macro_accuracy=20, plate_composition=15, culinary_coherence=15,
            micro_diversity=9, goal_alignment=7, practicality=5,
        )
        b.compute_total()
        assert b.band == "review"
        assert 70 <= b.total < 85

    def test_low_score_is_regenerate(self, scorer):
        b = ScoreBreakdown(
            macro_accuracy=5, plate_composition=5, culinary_coherence=5,
            micro_diversity=3, goal_alignment=2, practicality=2,
        )
        b.compute_total()
        assert b.band == "regenerate"
        assert b.total < 70
