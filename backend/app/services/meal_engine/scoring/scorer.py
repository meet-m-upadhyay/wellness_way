"""
Hybrid meal scorer — deterministic rules + optional LLM-judge.

6 scoring dimensions (0-100 total):
  - Macro Accuracy (30 pts)
  - Plate Composition (20 pts)
  - Culinary Coherence (20 pts)
  - Micronutrient Diversity (15 pts)
  - Goal Alignment (10 pts)
  - Practicality (5 pts)

Scoring bands:
  85-100: serve
  70-84:  serve with quality log
  <70:    auto-regenerate (max 3 retries)
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.meal_engine.config.loader import ConfigLoader

logger = logging.getLogger(__name__)


@dataclass
class ScoreBreakdown:
    """Detailed scoring breakdown for a meal."""
    macro_accuracy: float = 0.0       # 0-30
    plate_composition: float = 0.0    # 0-20
    culinary_coherence: float = 0.0   # 0-20
    micro_diversity: float = 0.0      # 0-15
    goal_alignment: float = 0.0       # 0-10
    practicality: float = 0.0         # 0-5
    total: float = 0.0                # 0-100
    band: str = "regenerate"          # "serve", "review", "regenerate"
    notes: List[str] = field(default_factory=list)

    def compute_total(self):
        self.total = (
            self.macro_accuracy
            + self.plate_composition
            + self.culinary_coherence
            + self.micro_diversity
            + self.goal_alignment
            + self.practicality
        )
        self.total = max(0, min(100, self.total))
        if self.total >= 85:
            self.band = "serve"
        elif self.total >= 70:
            self.band = "review"
        else:
            self.band = "regenerate"


class MealScorer:
    """Scores generated meals using deterministic rules + optional LLM coherence judge."""

    def __init__(self, db: Optional[Session] = None, config: Optional[ConfigLoader] = None):
        self._db = db
        self._config = config or ConfigLoader()
        self._weights = self._config.scoring_weights
        self._pairing_cache = None

    async def score(
        self,
        meal: dict,
        target_macros: dict,
        user_goal: str,
    ) -> ScoreBreakdown:
        """Score a meal across all dimensions.

        Args:
            meal: Dict with keys: archetype, components[], macros{}, cuisine
            target_macros: Dict with keys: calories, protein, carbs, fat
            user_goal: One of: muscle_gain, fat_loss, keto, endurance, maintenance

        Returns:
            ScoreBreakdown with per-dimension scores and overall band.
        """
        breakdown = self.score_deterministic(meal, target_macros, user_goal)

        # Skip LLM judge for clearly good meals
        if breakdown.total >= 85:
            return breakdown

        # Optional LLM coherence judge for borderline meals
        llm_coherence = await self._score_llm_coherence(meal)
        if llm_coherence is not None:
            # Blend: average of deterministic and LLM coherence
            breakdown.culinary_coherence = (breakdown.culinary_coherence + llm_coherence) / 2
            breakdown.compute_total()

        return breakdown

    def score_deterministic(
        self,
        meal: dict,
        target_macros: dict,
        user_goal: str,
    ) -> ScoreBreakdown:
        """Pure deterministic scoring (no LLM calls)."""
        breakdown = ScoreBreakdown()

        breakdown.macro_accuracy = self._score_macros(meal, target_macros)
        breakdown.plate_composition = self._score_composition(meal)
        breakdown.culinary_coherence = self._score_coherence(meal)
        breakdown.micro_diversity = self._score_diversity(meal)
        breakdown.goal_alignment = self._score_goal_alignment(meal, target_macros, user_goal)
        breakdown.practicality = self._score_practicality(meal)
        breakdown.compute_total()

        return breakdown

    # --- Dimension 1: Macro Accuracy (30 pts) ---

    def _score_macros(self, meal: dict, target: dict) -> float:
        w = self._weights["macro_accuracy"]
        max_pts = w["max_points"]
        full_threshold = w["full_marks_threshold_pct"]
        zero_threshold = w["zero_marks_threshold_pct"]

        macros = meal.get("macros", {})
        deviations = []

        for key in ["calories", "protein", "carbs", "fat"]:
            actual = macros.get(key, 0)
            target_val = target.get(key, 0)
            if target_val > 0:
                dev = abs(actual - target_val) / target_val
                deviations.append(dev)

        if not deviations:
            return 0

        avg_dev = sum(deviations) / len(deviations)

        if avg_dev <= full_threshold:
            return max_pts
        elif avg_dev >= zero_threshold:
            return 0
        else:
            # Linear interpolation
            ratio = (avg_dev - full_threshold) / (zero_threshold - full_threshold)
            return max_pts * (1 - ratio)

    # --- Dimension 2: Plate Composition (20 pts) ---

    def _score_composition(self, meal: dict) -> float:
        w = self._weights["plate_composition"]
        max_pts = w["max_points"]
        pts_per_slot = w["points_per_slot"]

        components = meal.get("components", [])
        slot_mapping = self._config.slot_to_food_groups

        # Check for presence of major categories
        categories_present = set()
        for comp in components:
            food_group = comp.get("food_group", "")
            for slot, groups in slot_mapping.items():
                if food_group in groups:
                    # Collapse protein subtypes
                    if slot.startswith("protein"):
                        categories_present.add("protein")
                    elif slot in ("grain", "starchy_vegetable"):
                        categories_present.add("carb")
                    elif slot == "fat_cooking":
                        categories_present.add("fat")
                    elif slot in ("vegetable", "leafy_green"):
                        categories_present.add("veg")

        return min(max_pts, len(categories_present) * pts_per_slot)

    # --- Dimension 3: Culinary Coherence (20 pts) ---

    def _score_coherence(self, meal: dict) -> float:
        w = self._weights["culinary_coherence"]
        archetype_pts = w["archetype_match_points"]
        pairing_pts = w["pairing_valid_points"]
        incompatible_penalty = w["pairing_incompatible_penalty"]

        score = 0.0

        # Archetype match: does the meal declare an archetype?
        if meal.get("archetype"):
            score += archetype_pts

        # Pairing validation
        cuisine = meal.get("cuisine", "indian")
        component_names = [c.get("name", "").lower() for c in meal.get("components", [])]

        pairing_score = pairing_pts  # start at full, deduct for violations
        rules = self._get_pairing_rules(cuisine)

        for rule_item, rule_data in rules.items():
            # Check if this rule's item is in the meal
            item_present = any(rule_item in name for name in component_names)
            if not item_present:
                continue

            # Check for incompatible pairings
            incompatible = rule_data.get("incompatible", [])
            for inc in incompatible:
                if any(inc in name for name in component_names):
                    pairing_score += incompatible_penalty
                    break  # one penalty per rule item

        score += max(0, pairing_score)
        return min(w["max_points"], score)

    def _get_pairing_rules(self, cuisine: str) -> dict:
        """Load pairing rules from DB (cached)."""
        if self._pairing_cache is not None:
            return self._pairing_cache.get(cuisine, {})

        self._pairing_cache = {}
        if not self._db:
            return {}

        rows = self._db.execute(
            text("SELECT cuisine, item, preferred, acceptable, incompatible FROM v2_pairing_rules")
        ).fetchall()

        for row in rows:
            if row.cuisine not in self._pairing_cache:
                self._pairing_cache[row.cuisine] = {}
            self._pairing_cache[row.cuisine][row.item] = {
                "preferred": row.preferred or [],
                "acceptable": row.acceptable or [],
                "incompatible": row.incompatible or [],
            }

        return self._pairing_cache.get(cuisine, {})

    # --- Dimension 4: Micronutrient Diversity (15 pts) ---

    def _score_diversity(self, meal: dict) -> float:
        w = self._weights["micro_diversity"]
        max_pts = w["max_points"]
        pts_per_group = w["points_per_food_group"]

        food_groups = set()
        for comp in meal.get("components", []):
            fg = comp.get("food_group")
            if fg:
                food_groups.add(fg)

        return min(max_pts, len(food_groups) * pts_per_group)

    # --- Dimension 5: Goal Alignment (10 pts) ---

    def _score_goal_alignment(self, meal: dict, target: dict, goal: str) -> float:
        w = self._weights["goal_alignment"]
        max_pts = w["max_points"]

        macro_order = self._config.goal_macro_order.get(goal, [])
        if not macro_order:
            return max_pts * 0.5  # unknown goal, give half credit

        macros = meal.get("macros", {})
        priority_macro = macro_order[0]  # most important macro for this goal

        # Check if the priority macro is close to target
        actual = macros.get(priority_macro, 0)
        target_val = target.get(priority_macro, 0)

        if target_val <= 0:
            return max_pts * 0.5

        deviation = abs(actual - target_val) / target_val
        if deviation <= 0.05:
            return max_pts
        elif deviation <= 0.15:
            return max_pts * 0.7
        elif deviation <= 0.25:
            return max_pts * 0.4
        return 0

    # --- Dimension 6: Practicality (5 pts) ---

    def _score_practicality(self, meal: dict) -> float:
        w = self._weights["practicality"]
        max_pts = w["max_points"]
        min_g = w["min_portion_g"]
        max_g = w["max_portion_g"]
        penalty = w["penalty_per_violation"]

        score = max_pts
        for comp in meal.get("components", []):
            grams = comp.get("grams", 0)
            if grams < min_g or grams > max_g:
                score += penalty  # negative penalty

        return max(0, score)

    # --- Optional LLM Coherence Judge ---

    async def _score_llm_coherence(self, meal: dict) -> Optional[float]:
        """Ask Groq LLM to rate meal coherence 0-20."""
        try:
            import httpx
            import json
            import os

            api_key = os.environ.get("GROQ_API_KEY")
            if not api_key:
                return None

            components_str = ", ".join(
                f"{c.get('name', '?')} ({c.get('grams', '?')}g)"
                for c in meal.get("components", [])
            )
            archetype = meal.get("archetype", "unknown")
            cuisine = meal.get("cuisine", "unknown")

            prompt = f"""Rate this {cuisine} meal for culinary coherence on a scale of 0-20.

Archetype: {archetype}
Components: {components_str}

Criteria:
- Does this feel like a real meal someone would actually eat?
- Are the components culturally coherent for {cuisine} cuisine?
- Would a grandmother recognize this as a proper meal?

Respond with ONLY a JSON object: {{"score": 0-20, "reason": "brief explanation"}}"""

            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "llama-3.1-8b-instant",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.1,
                        "max_tokens": 80,
                        "response_format": {"type": "json_object"},
                    },
                    timeout=10.0,
                )
                resp.raise_for_status()
                data = resp.json()
                content = json.loads(data["choices"][0]["message"]["content"])
                score = float(content.get("score", 10))
                return max(0, min(20, score))

        except Exception as e:
            logger.debug("LLM coherence judge failed: %s", e)
            return None
