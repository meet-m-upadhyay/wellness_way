"""
Indian unit normalizer — converts serving units to grams.

Uses config/unit_conversions.json for the mapping.
Strips common plurals (rotis→roti, phulkas→phulka).
Falls through to raw grams for unknown units.
"""

import re
from typing import Optional

from app.services.meal_engine.config.loader import ConfigLoader


class UnitNormalizer:
    """Converts Indian serving units to grams."""

    def __init__(self, config: Optional[ConfigLoader] = None):
        self._config = config or ConfigLoader()
        self._conversions = self._config.unit_conversions

    def normalize(self, quantity: float, unit: str, ingredient_name: str = "") -> float:
        """Convert quantity + unit to grams.

        Args:
            quantity: Number of units (e.g., 2)
            unit: Unit name (e.g., "katori", "rotis", "g", "ml")
            ingredient_name: Optional, for context-aware conversion

        Returns:
            Weight in grams.
        """
        if not unit:
            return quantity

        cleaned = self._clean_unit(unit)

        # Direct match
        if cleaned in self._conversions:
            return quantity * self._conversions[cleaned]

        # If unit is already grams/gram
        if cleaned in ("g", "gram", "grams", "gm"):
            return quantity

        # ml ≈ g for water-based liquids (rough approximation)
        if cleaned in ("ml", "millilitre", "milliliter"):
            return quantity

        # kg → g
        if cleaned in ("kg", "kilogram"):
            return quantity * 1000

        # Unknown unit — return as-is (assume grams)
        return quantity

    def _clean_unit(self, unit: str) -> str:
        """Lowercase, strip whitespace, remove trailing 's' for plurals."""
        cleaned = unit.lower().strip()
        # Strip common plural suffixes
        if cleaned.endswith("s") and len(cleaned) > 2:
            singular = cleaned[:-1]
            if singular in self._conversions:
                return singular
        # Strip trailing 'es' (e.g., "slices" → "slice")
        if cleaned.endswith("es") and len(cleaned) > 3:
            singular = cleaned[:-2]
            if singular in self._conversions:
                return singular
        return cleaned
