"""Tests for the V2 meal engine unit normalizer."""

import pytest
from app.services.meal_engine.unit_normalizer import UnitNormalizer
from app.services.meal_engine.config.loader import ConfigLoader


@pytest.fixture
def normalizer():
    return UnitNormalizer(ConfigLoader())


class TestUnitNormalizer:

    def test_katori(self, normalizer):
        assert normalizer.normalize(1, "katori", "dal") == 150.0

    def test_multiple_rotis(self, normalizer):
        assert normalizer.normalize(2, "roti", "wheat") == 80.0

    def test_phulka_plural(self, normalizer):
        assert normalizer.normalize(3, "phulkas", "wheat") == 90.0

    def test_dosa(self, normalizer):
        assert normalizer.normalize(1, "dosa", "rice") == 80.0

    def test_idli(self, normalizer):
        assert normalizer.normalize(2, "idli", "rice") == 80.0

    def test_paratha(self, normalizer):
        assert normalizer.normalize(1, "paratha", "wheat") == 60.0

    def test_cup(self, normalizer):
        assert normalizer.normalize(1, "cup", "milk") == 240.0

    def test_tbsp(self, normalizer):
        assert normalizer.normalize(2, "tbsp", "oil") == 30.0

    def test_grams_passthrough(self, normalizer):
        assert normalizer.normalize(100, "g", "rice") == 100.0

    def test_gram_spelled_out(self, normalizer):
        assert normalizer.normalize(50, "grams", "paneer") == 50.0

    def test_kg(self, normalizer):
        assert normalizer.normalize(0.5, "kg", "chicken") == 500.0

    def test_unknown_unit_passthrough(self, normalizer):
        assert normalizer.normalize(200, "foobar", "rice") == 200.0

    def test_empty_unit(self, normalizer):
        assert normalizer.normalize(100, "", "rice") == 100.0

    def test_plural_slices(self, normalizer):
        assert normalizer.normalize(2, "slices", "bread") == 60.0

    def test_naan(self, normalizer):
        assert normalizer.normalize(1, "naan", "wheat") == 80.0

    def test_bhatura(self, normalizer):
        assert normalizer.normalize(1, "bhatura", "wheat") == 70.0
