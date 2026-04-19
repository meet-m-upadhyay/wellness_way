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
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.services.meal_engine.config.loader import ConfigLoader
from app.services.meal_engine.diagnostics import (
    IngredientDiag,
    MealAttemptDiag,
    PipelineDiagnostics,
)
from app.services.meal_engine.generation.prompt_builder import V2PromptBuilder
from app.services.meal_engine.matching.ingredient_matcher import IngredientMatcher
from app.services.meal_engine.nutrition.router import NutritionRouter
from app.services.meal_engine.scoring.scorer import MealScorer, ScoreBreakdown
from app.services.meal_engine.unit_normalizer import UnitNormalizer

logger = logging.getLogger(__name__)

# TODO: SCORING_DEBUG_MODE — temporarily set to 1 retry and threshold 40.
# After Checkpoint C, reassess based on real score distribution:
#   - If scores 65+ consistently → raise threshold to 55 or 70, retries to 2-3
#   - If scores still 40-50 → scoring rubric itself needs investigation
# Do NOT ship to prod with these values.
MAX_RETRIES = 1


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
class MealRecipe:
    """Recipe instructions for a meal."""
    prep_time_min: int = 0
    cook_time_min: int = 0
    steps: List[str] = field(default_factory=list)


@dataclass
class GeneratedMeal:
    """Result of V2 meal generation."""
    archetype: str
    dish_name: str
    components: List[ResolvedComponent]
    macros: Dict[str, float]
    score: ScoreBreakdown
    cultural_note: Optional[str] = None
    recipe: Optional[MealRecipe] = None
    cooked_serving_size_g: Optional[float] = None
    serves: int = 1
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

    def __init__(self, db: Session, config: Optional[ConfigLoader] = None,
                 diagnostics: Optional[PipelineDiagnostics] = None):
        self._db = db
        self._config = config or ConfigLoader()
        self._prompt_builder = V2PromptBuilder(self._config)
        self._matcher = IngredientMatcher(db, self._config)
        self._nutrition_router = NutritionRouter(db, self._config)
        self._scorer = MealScorer(db, self._config)
        self._normalizer = UnitNormalizer(self._config)
        self._diag = diagnostics or PipelineDiagnostics()

    @property
    def diagnostics(self) -> PipelineDiagnostics:
        return self._diag

    async def generate_meal(self, constraints: MealConstraints) -> GeneratedMeal:
        """Generate a single meal with auto-retry on low scores."""
        best_meal = None
        best_score_total = -1
        best_attempt_idx = -1
        previous_weaknesses = ""

        for attempt in range(MAX_RETRIES):
            attempt_diag = MealAttemptDiag(
                attempt_number=attempt + 1,
                meal_type=constraints.meal_type,
            )
            attempt_start = time.perf_counter()

            try:
                meal = await self._generate_one(
                    constraints, attempt, attempt_diag,
                    previous_weaknesses=previous_weaknesses,
                )
                if meal is None:
                    attempt_diag.retry_reason = "generation_failed"
                    attempt_diag.total_ms = (time.perf_counter() - attempt_start) * 1000
                    self._diag.meal_attempts.append(attempt_diag)
                    continue

                attempt_diag.score_total = meal.score.total
                attempt_diag.score_band = meal.score.band
                attempt_diag.archetype = meal.archetype
                attempt_diag.dish_name = meal.dish_name

                if meal.score.total > best_score_total:
                    best_meal = meal
                    best_score_total = meal.score.total
                    best_meal.attempt = attempt + 1
                    best_attempt_idx = len(self._diag.meal_attempts)

                if meal.score.band != "regenerate":
                    attempt_diag.kept = True
                    attempt_diag.total_ms = (time.perf_counter() - attempt_start) * 1000
                    self._diag.meal_attempts.append(attempt_diag)
                    break  # good enough

                # Build feedback for next attempt from score notes
                previous_weaknesses = "; ".join(meal.score.notes) if meal.score.notes else f"score={meal.score.total:.0f}"
                attempt_diag.retry_reason = "low_score"
                logger.info(
                    "Meal scored %d (%s) on attempt %d — retrying",
                    meal.score.total, meal.score.band, attempt + 1,
                )
            except Exception as e:
                attempt_diag.retry_reason = f"exception: {e}"
                logger.warning("Meal generation attempt %d failed: %s", attempt + 1, e)

            attempt_diag.total_ms = (time.perf_counter() - attempt_start) * 1000
            self._diag.meal_attempts.append(attempt_diag)

        # Mark the best attempt as kept
        if best_attempt_idx >= 0 and best_attempt_idx < len(self._diag.meal_attempts):
            self._diag.meal_attempts[best_attempt_idx].kept = True

        if best_meal is None:
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
        self, constraints: MealConstraints, attempt: int,
        attempt_diag: Optional[MealAttemptDiag] = None,
        previous_weaknesses: str = "",
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
            previous_weaknesses=previous_weaknesses,
        )

        # 2. Call LLM
        t0 = time.perf_counter()
        raw_response = await self._call_llm(prompt)
        llm_ms = (time.perf_counter() - t0) * 1000
        if attempt_diag:
            attempt_diag.llm_generation_ms = llm_ms
        if not raw_response:
            return None

        # 3. Parse LLM response (supports both old "components" and new "raw_ingredients")
        raw_meal = self._parse_llm_response(raw_response)
        if not raw_meal:
            return None

        ingredients_list = raw_meal.get("raw_ingredients") or raw_meal.get("components", [])

        # 3.5 Expand composites (roti, naan, dosa, etc.) into raw sub-components
        ingredients_list = self._expand_composites(ingredients_list)

        # 4. Resolve each ingredient (with per-ingredient diagnostics)
        t0 = time.perf_counter()
        resolved = []
        seen_names = set()  # Dedupe: resolve each ingredient once
        for comp in ingredients_list:
            name = comp.get("name", "").strip().lower()
            if name in seen_names:
                # Reuse previous resolution for duplicate ingredient
                for prev in resolved:
                    if prev.llm_name.lower() == name:
                        dup = ResolvedComponent(
                            llm_name=comp.get("name", ""),
                            resolved_code=prev.resolved_code,
                            resolved_name=prev.resolved_name,
                            match_method=prev.match_method,
                            match_confidence=prev.match_confidence,
                            grams=float(comp.get("grams", 0)),
                            role=comp.get("role", ""),
                            food_group=prev.food_group,
                            nutrition_per_100g=prev.nutrition_per_100g,
                        )
                        resolved.append(dup)
                        break
                continue

            seen_names.add(name)
            ing_diag = IngredientDiag(raw_llm_name=comp.get("name", ""))
            r = await self._resolve_component(comp, constraints.cuisine, ing_diag)
            resolved.append(r)
            if attempt_diag:
                attempt_diag.ingredients.append(ing_diag)
        ingredient_ms = (time.perf_counter() - t0) * 1000
        if attempt_diag:
            attempt_diag.ingredient_resolution_ms = ingredient_ms

        # 5. Calculate meal macros
        t0 = time.perf_counter()
        macros = self._calculate_macros(resolved)
        macro_ms = (time.perf_counter() - t0) * 1000
        if attempt_diag:
            attempt_diag.macro_calculation_ms = macro_ms

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
        t0 = time.perf_counter()
        target_macros = {
            "calories": constraints.target_calories,
            "protein": constraints.target_protein,
            "carbs": constraints.target_carbs,
            "fat": constraints.target_fat,
        }
        score = await self._scorer.score(meal_data, target_macros, constraints.primary_goal)
        scoring_ms = (time.perf_counter() - t0) * 1000
        if attempt_diag:
            attempt_diag.scoring_ms = scoring_ms

        # 8. Parse recipe if present
        recipe_data = raw_meal.get("recipe")
        recipe = None
        if recipe_data and isinstance(recipe_data, dict):
            recipe = MealRecipe(
                prep_time_min=recipe_data.get("prep_time_min", 0),
                cook_time_min=recipe_data.get("cook_time_min", 0),
                steps=recipe_data.get("steps", []),
            )

        return GeneratedMeal(
            archetype=raw_meal.get("archetype", "unknown"),
            dish_name=raw_meal.get("dish_name", "Unnamed Meal"),
            components=resolved,
            macros=macros,
            score=score,
            cultural_note=raw_meal.get("cultural_note"),
            recipe=recipe,
            cooked_serving_size_g=raw_meal.get("cooked_serving_size_g"),
            serves=raw_meal.get("serves", 1),
        )

    def _expand_composites(self, ingredients: List[dict]) -> List[dict]:
        """Expand composite ingredients (roti, naan, dosa) into raw sub-components.

        If the LLM outputs "roti" or "naan" despite the prompt rule, this safety net
        decomposes it using composite_ingredients.json ratios.
        Logs every expansion for frequency tracking.
        """
        composites = self._config.composite_ingredients
        expanded = []
        for comp in ingredients:
            name = comp.get("name", "").strip().lower()
            # Strip _comment key and check for composite match
            if name in composites and isinstance(composites[name], dict):
                composite_def = composites[name]
                grams = float(comp.get("grams", 0))
                sub_components = composite_def.get("components", [])
                logger.info(
                    "[COMPOSITE_EXPANSION] '%s' (%gg) → %d sub-components: %s",
                    name, grams,
                    len(sub_components),
                    ", ".join(f"{s['name']} ({s['grams_per_100g'] * grams / 100:.0f}g)" for s in sub_components),
                )
                for sub in sub_components:
                    sub_grams = sub["grams_per_100g"] * grams / 100
                    if sub_grams >= 1:  # skip negligible amounts
                        expanded.append({
                            "name": sub["name"],
                            "grams": round(sub_grams, 1),
                            "role": sub.get("role", comp.get("role", "")),
                        })
            else:
                expanded.append(comp)
        return expanded

    async def _resolve_component(
        self, comp: dict, cuisine: str,
        ing_diag: Optional[IngredientDiag] = None,
    ) -> ResolvedComponent:
        """Resolve a single raw ingredient to IFCT data."""
        ing_start = time.perf_counter()
        # Raw-by-contract: name comes clean from LLM, no stripping needed
        name = comp.get("name", "").strip()
        grams = float(comp.get("grams", 0))
        role = comp.get("role", "")
        food_group = comp.get("food_group", "")

        if ing_diag:
            ing_diag.cleaned_name = name

        # Handle unit-based quantities (e.g., "1 katori")
        if comp.get("unit") and comp.get("quantity"):
            grams = self._normalizer.normalize(
                float(comp["quantity"]), comp["unit"], name
            )

        # Match ingredient
        t0 = time.perf_counter()
        match = await self._matcher.match(name)
        matcher_ms = (time.perf_counter() - t0) * 1000

        if ing_diag:
            ing_diag.match_tier = match.match_method
            ing_diag.match_confidence = match.confidence
            ing_diag.matched_ifct_name = match.ingredient_name if match.found else None
            ing_diag.matched_ifct_code = match.ingredient_code
            ing_diag.matcher_tiers_tried = match.tiers_tried if hasattr(match, 'tiers_tried') else [match.match_method]
            ing_diag.matcher_time_ms = matcher_ms

        # Look up nutrition
        t0 = time.perf_counter()
        nutrition = await self._nutrition_router.lookup(name, cuisine, self._diag)
        nutrition_ms = (time.perf_counter() - t0) * 1000
        nutrition_dict = nutrition.to_macros_dict() if nutrition else None

        if ing_diag:
            ing_diag.nutrition_time_ms = nutrition_ms
            ing_diag.nutrition_provider = nutrition.source if nutrition else "none"
            ing_diag.total_time_ms = (time.perf_counter() - ing_start) * 1000

        # If we matched, get the food_group from DB
        if match.found and not food_group:
            from sqlalchemy import text
            row = self._db.execute(
                text("SELECT food_group FROM v2_ingredients WHERE code = :c"),
                {"c": match.ingredient_code},
            ).fetchone()
            if row:
                food_group = row.food_group

        # Role validation: auto-correct if LLM assigned impossible role for this food_group
        role = self._validate_role(role, food_group, name)

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

    def _validate_role(self, llm_role: str, food_group: str, ingredient_name: str) -> str:
        """Validate and auto-correct ingredient role based on food_group.

        If the LLM assigned a role that's impossible for the ingredient's food_group,
        auto-correct to the first valid role for that food_group. Logs every correction.
        """
        if not food_group:
            return llm_role  # Can't validate without food_group

        valid_roles = self._config.role_validation.get(food_group, [])
        if not valid_roles:
            return llm_role  # Unknown food_group, keep LLM's assignment

        if llm_role in valid_roles:
            return llm_role  # Role is valid

        # Auto-correct to first valid role
        corrected = valid_roles[0]
        logger.warning(
            "[ROLE_CORRECTION] '%s' (food_group=%s): LLM role '%s' → corrected to '%s'",
            ingredient_name, food_group, llm_role, corrected,
        )
        return corrected

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
        """Call Groq LLM with exponential backoff on 429 rate limits."""
        import asyncio
        try:
            import httpx
        except ImportError:
            logger.error("httpx not available")
            return None

        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            logger.error("GROQ_API_KEY not set")
            return None

        backoff_delays = [5, 15, 45]  # seconds

        for attempt_idx in range(len(backoff_delays) + 1):
            try:
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
                            "max_tokens": 1000,
                            "response_format": {"type": "json_object"},
                        },
                        timeout=20.0,
                    )

                    if resp.status_code == 429:
                        if attempt_idx < len(backoff_delays):
                            # Use Retry-After header if present, else use backoff schedule
                            retry_after = resp.headers.get("retry-after")
                            delay = float(retry_after) if retry_after else backoff_delays[attempt_idx]
                            logger.warning(
                                "Groq 429 rate limit — retrying in %.0fs (attempt %d/%d)",
                                delay, attempt_idx + 1, len(backoff_delays),
                            )
                            await asyncio.sleep(delay)
                            continue
                        else:
                            logger.error("Groq 429 exhausted all retries")
                            return None

                    resp.raise_for_status()
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429 and attempt_idx < len(backoff_delays):
                    delay = backoff_delays[attempt_idx]
                    logger.warning("Groq 429 (exception path) — retrying in %.0fs", delay)
                    await asyncio.sleep(delay)
                    continue
                logger.warning("LLM call failed: %s", e)
                return None
            except Exception as e:
                logger.warning("LLM call failed: %s", e)
                return None

        return None

    def _parse_llm_response(self, raw: str) -> Optional[dict]:
        """Parse and validate LLM JSON response.

        Accepts both new schema (raw_ingredients) and old schema (components).
        """
        try:
            data = json.loads(raw)
            if not data.get("raw_ingredients") and not data.get("components"):
                logger.warning("LLM response missing both raw_ingredients and components")
                return None
            return data
        except json.JSONDecodeError as e:
            logger.warning("LLM response is not valid JSON: %s", e)
            return None
