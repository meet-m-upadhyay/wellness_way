"""
V2 Meal Engine Orchestrator.

End-to-end meal generation pipeline:
1. Build archetype-first prompt
2. Call LLM for meal suggestion
3. Resolve each ingredient via IngredientMatcher
4. Look up nutrition via NutritionRouter
5. Normalize units via UnitNormalizer
6. Calculate meal macros
7. Score via MealScorer
8. Auto-regenerate if score < 70 (max 3 retries)
9. Return meal with resolved IFCT codes + match confidence
"""

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.services.meal_engine.config.loader import ConfigLoader
from app.services.meal_engine.generation.prompt_builder import V2PromptBuilder
from app.services.meal_engine.matching.ingredient_matcher import IngredientMatcher
from app.services.meal_engine.nutrition.router import NutritionRouter
from app.services.meal_engine.scoring.scorer import MealScorer, ScoreBreakdown
from app.services.meal_engine.unit_normalizer import UnitNormalizer

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


@dataclass
class ResolvedComponent:
    """A meal component with resolved IFCT data."""
    llm_name: str
    resolved_code: Optional[str]
    resolved_name: str
    match_method: str
    match_confidence: float
    grams: float
    role: str
    food_group: str
    nutrition_per_100g: Optional[Dict] = None


@dataclass
class GeneratedMeal:
    """Result of V2 meal generation."""
    archetype: str
    dish_name: str
    components: List[ResolvedComponent]
    macros: Dict[str, float]
    score: ScoreBreakdown
    cultural_note: Optional[str] = None
    prep_time_minutes: Optional[int] = None
    quality_warning: bool = False
    attempt: int = 1


@dataclass
class MealConstraints:
    """Input constraints for meal generation."""
    meal_type: str = "lunch"
    cuisine: str = "indian"
    diet_type: str = "vegetarian"
    target_calories: float = 600
    target_protein: float = 25
    target_carbs: float = 80
    target_fat: float = 15
    allergies: List[str] = field(default_factory=list)
    foods_to_avoid: List[str] = field(default_factory=list)
    exclude_ingredients: List[str] = field(default_factory=list)
    primary_goal: str = "maintenance"


class MealEngineV2:
    """V2 meal generation pipeline."""

    def __init__(self, db: Session, config: Optional[ConfigLoader] = None):
        self._db = db
        self._config = config or ConfigLoader()
        self._prompt_builder = V2PromptBuilder(self._config)
        self._matcher = IngredientMatcher(db, self._config)
        self._nutrition_router = NutritionRouter(db, self._config)
        self._scorer = MealScorer(db, self._config)
        self._normalizer = UnitNormalizer(self._config)

    async def generate_meal(self, constraints: MealConstraints) -> GeneratedMeal:
        """Generate a single meal with auto-retry on low scores."""
        best_meal = None
        best_score_total = -1

        for attempt in range(MAX_RETRIES):
            try:
                meal = await self._generate_one(constraints, attempt)
                if meal is None:
                    continue

                if meal.score.total > best_score_total:
                    best_meal = meal
                    best_score_total = meal.score.total
                    best_meal.attempt = attempt + 1

                if meal.score.band != "regenerate":
                    break  # good enough

                logger.info(
                    "Meal scored %d (%s) on attempt %d — retrying",
                    meal.score.total, meal.score.band, attempt + 1,
                )
            except Exception as e:
                logger.warning("Meal generation attempt %d failed: %s", attempt + 1, e)
                continue

        if best_meal is None:
            # Fallback: return a minimal meal with quality warning
            best_meal = GeneratedMeal(
                archetype="unknown",
                dish_name="Meal generation failed",
                components=[],
                macros={},
                score=ScoreBreakdown(),
                quality_warning=True,
            )

        if best_meal.score.total < 70:
            best_meal.quality_warning = True

        return best_meal

    async def _generate_one(
        self, constraints: MealConstraints, attempt: int
    ) -> Optional[GeneratedMeal]:
        """Single generation attempt."""
        # 1. Build prompt
        prompt = self._prompt_builder.build(
            meal_type=constraints.meal_type,
            cuisine=constraints.cuisine,
            diet_type=constraints.diet_type,
            target_calories=constraints.target_calories,
            target_protein=constraints.target_protein,
            target_carbs=constraints.target_carbs,
            target_fat=constraints.target_fat,
            allergies=constraints.allergies,
            foods_to_avoid=constraints.foods_to_avoid,
            exclude_ingredients=constraints.exclude_ingredients,
            attempt=attempt,
        )

        # 2. Call LLM
        raw_response = await self._call_llm(prompt)
        if not raw_response:
            return None

        # 3. Parse LLM response
        raw_meal = self._parse_llm_response(raw_response)
        if not raw_meal:
            return None

        # 4. Resolve each ingredient
        resolved = []
        for comp in raw_meal.get("components", []):
            r = await self._resolve_component(comp, constraints.cuisine)
            resolved.append(r)

        # 5. Calculate meal macros
        macros = self._calculate_macros(resolved)

        # 6. Build meal structure for scoring
        meal_data = {
            "archetype": raw_meal.get("archetype", ""),
            "cuisine": constraints.cuisine,
            "components": [
                {
                    "name": r.resolved_name,
                    "role": r.role,
                    "grams": r.grams,
                    "food_group": r.food_group,
                }
                for r in resolved
            ],
            "macros": macros,
        }

        # 7. Score
        target_macros = {
            "calories": constraints.target_calories,
            "protein": constraints.target_protein,
            "carbs": constraints.target_carbs,
            "fat": constraints.target_fat,
        }
        score = await self._scorer.score(meal_data, target_macros, constraints.primary_goal)

        return GeneratedMeal(
            archetype=raw_meal.get("archetype", "unknown"),
            dish_name=raw_meal.get("dish_name", "Unnamed Meal"),
            components=resolved,
            macros=macros,
            score=score,
            cultural_note=raw_meal.get("cultural_note"),
            prep_time_minutes=raw_meal.get("prep_time_minutes"),
        )

    @staticmethod
    def _clean_ingredient_name(raw_name: str) -> str:
        """Strip grams, quantities, cooking descriptors from LLM ingredient name."""
        import re
        name = raw_name.strip()
        # Remove trailing quantity+unit: ", 100g", ", 80 g", ", 2 cups"
        name = re.sub(r',?\s*\d+\.?\d*\s*(g|gm|grams?|ml|kg|cups?|tbsp|tsp|katori|pieces?)\s*$', '', name, flags=re.IGNORECASE)
        # Remove leading quantity: "2 rotis" -> "rotis"
        name = re.sub(r'^\d+\.?\d*\s*(g|gm|grams?\s+of\s+)?', '', name, flags=re.IGNORECASE)
        return name.strip().rstrip(',').strip()

    async def _resolve_component(
        self, comp: dict, cuisine: str
    ) -> ResolvedComponent:
        """Resolve a single LLM component to IFCT data."""
        name = self._clean_ingredient_name(comp.get("name", ""))
        grams = float(comp.get("grams", 0))
        role = comp.get("role", "")
        food_group = comp.get("food_group", "")

        # Handle unit-based quantities (e.g., "1 katori")
        if comp.get("unit") and comp.get("quantity"):
            grams = self._normalizer.normalize(
                float(comp["quantity"]), comp["unit"], name
            )

        # Match ingredient
        match = await self._matcher.match(name)

        # Look up nutrition
        nutrition = await self._nutrition_router.lookup(name, cuisine)
        nutrition_dict = nutrition.to_macros_dict() if nutrition else None

        # If we matched and the match has a food_group, prefer that
        if match.found and not food_group:
            # Query food_group from DB
            from sqlalchemy import text
            row = self._db.execute(
                text("SELECT food_group FROM v2_ingredients WHERE code = :c"),
                {"c": match.ingredient_code},
            ).fetchone()
            if row:
                food_group = row.food_group

        return ResolvedComponent(
            llm_name=name,
            resolved_code=match.ingredient_code,
            resolved_name=match.ingredient_name if match.found else name,
            match_method=match.match_method,
            match_confidence=match.confidence,
            grams=grams,
            role=role,
            food_group=food_group,
            nutrition_per_100g=nutrition_dict,
        )

    def _calculate_macros(self, components: List[ResolvedComponent]) -> Dict[str, float]:
        """Sum macros across all components, scaling from per-100g to actual grams."""
        totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0}

        for comp in components:
            if comp.nutrition_per_100g and comp.grams > 0:
                scale = comp.grams / 100.0
                totals["calories"] += (comp.nutrition_per_100g.get("calories", 0) * scale)
                totals["protein"] += (comp.nutrition_per_100g.get("protein", 0) * scale)
                totals["carbs"] += (comp.nutrition_per_100g.get("carbohydrates", 0) * scale)
                totals["fat"] += (comp.nutrition_per_100g.get("fat", 0) * scale)
                totals["fiber"] += (comp.nutrition_per_100g.get("fiber", 0) * scale)

        return {k: round(v, 1) for k, v in totals.items()}

    async def _call_llm(self, prompt: str) -> Optional[str]:
        """Call Groq LLM and return raw response content."""
        try:
            import httpx

            api_key = os.environ.get("GROQ_API_KEY")
            if not api_key:
                logger.error("GROQ_API_KEY not set")
                return None

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
                        "temperature": 0.6,
                        "max_tokens": 500,
                        "response_format": {"type": "json_object"},
                    },
                    timeout=15.0,
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]

        except Exception as e:
            logger.warning("LLM call failed: %s", e)
            return None

    def _parse_llm_response(self, raw: str) -> Optional[dict]:
        """Parse and validate LLM JSON response."""
        try:
            data = json.loads(raw)
            if not data.get("components"):
                logger.warning("LLM response missing components")
                return None
            return data
        except json.JSONDecodeError as e:
            logger.warning("LLM response is not valid JSON: %s", e)
            return None
