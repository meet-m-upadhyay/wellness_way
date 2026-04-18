"""
Config loader for the v2 meal engine.

Loads JSON config files at startup, validates basic structure,
and optionally hot-reloads in dev mode.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).parent


class ConfigLoader:
    """Loads and caches JSON configs for the meal engine."""

    def __init__(self, config_dir: Path = CONFIG_DIR, dev_mode: bool = False):
        self._config_dir = config_dir
        self._dev_mode = dev_mode
        self._cache: Dict[str, Any] = {}
        self._load_all()

    def _load_file(self, filename: str) -> Any:
        path = self._config_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        if not data:
            raise ValueError(f"Config file is empty: {path}")
        return data

    def _load_all(self):
        files = [
            "archetypes.json",
            "scoring_weights.json",
            "unit_conversions.json",
            "goal_macro_order.json",
            "canonical_foods.json",
        ]
        for f in files:
            try:
                self._cache[f] = self._load_file(f)
                logger.debug("Loaded config: %s", f)
            except Exception as e:
                logger.error("Failed to load config %s: %s", f, e)
                raise

    def _get(self, filename: str) -> Any:
        if self._dev_mode:
            # Hot-reload in dev mode
            self._cache[filename] = self._load_file(filename)
        return self._cache[filename]

    @property
    def archetypes(self) -> dict:
        return self._get("archetypes.json")

    @property
    def scoring_weights(self) -> dict:
        return self._get("scoring_weights.json")

    @property
    def unit_conversions(self) -> dict:
        return self._get("unit_conversions.json")

    @property
    def goal_macro_order(self) -> dict:
        return self._get("goal_macro_order.json")

    @property
    def canonical_foods(self) -> dict:
        return self._get("canonical_foods.json")

    @property
    def slot_to_food_groups(self) -> dict:
        """Extract the slot→food_groups mapping from archetypes config."""
        return self.archetypes.get("_slot_to_food_groups", {})

    def reload(self):
        """Force reload all configs."""
        self._load_all()
        logger.info("All configs reloaded")
