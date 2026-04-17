"""LLM-based meal suggestion service for the hybrid nutrition pipeline."""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, Dict, List, Optional

from .schema import LLMSuggestionResponse

logger = logging.getLogger(__name__)

_DIET_PRIORITY_RULES = """
Diet priority rules (must be respected strictly):
- non-vegetarian: Prefer non-veg (chicken, mutton, fish, prawns) as primary protein. Egg second. Veg/vegan acceptable but lower priority.
- eggetarian: No meat/fish. Prefer egg-based protein. Veg/vegan acceptable but lower priority.
- vegetarian: No meat/fish/eggs. Prefer dairy (paneer, yogurt, cheese). Vegan acceptable but lower priority.
- vegan: No animal products. Only plant proteins (lentils, tofu, chickpeas, tempeh, etc.).
"""


class LLMMealSuggester:
    """Suggests meal ingredients via an LLM generator callable."""

    def __init__(self, generator: Callable[[Dict[str, Any]], Any]) -> None:
        """
        Args:
            generator: Async callable that accepts a payload dict and returns a dict.
                       Expected to be a Groq (or compatible) generator configured externally.
        """
        self._generator = generator

    async def suggest_meals(
        self,
        diet_type: str,
        cuisine: str,
        meal_types: List[str],
        allergies: Optional[List[str]] = None,
        foods_to_avoid: Optional[List[str]] = None,
        exclude_ingredients: Optional[List[str]] = None,
        primary_goal: Optional[str] = None,
        budget_constraints: Optional[str] = None,
        lifestyle_constraints: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Ask the LLM to suggest meal ingredients and return a flat list of ingredient dicts.

        Returns an empty list if the LLM fails, returns bad JSON, or validation fails.
        """
        allergies = allergies or []
        foods_to_avoid = foods_to_avoid or []
        exclude_ingredients = exclude_ingredients or []

        prompt = self._build_prompt(
            diet_type=diet_type,
            cuisine=cuisine,
            meal_types=meal_types,
            allergies=allergies,
            foods_to_avoid=foods_to_avoid,
            exclude_ingredients=exclude_ingredients,
            primary_goal=primary_goal,
            budget_constraints=budget_constraints,
            lifestyle_constraints=lifestyle_constraints,
        )

        payload: Dict[str, Any] = {
            "action": "suggest_meals",
            "prompt": prompt,
        }

        logger.debug("[DEBUG][LLM_SUGGESTER] Sending suggest_meals payload to generator")

        try:
            raw = await self._generator(payload)
        except Exception as exc:  # noqa: BLE001
            logger.debug("[DEBUG][LLM_SUGGESTER] Generator raised an exception: %s", exc)
            return []

        logger.debug("[DEBUG][LLM_SUGGESTER] Raw generator response received")

        try:
            validated = LLMSuggestionResponse.model_validate(raw)
        except Exception as exc:  # noqa: BLE001
            logger.debug("[DEBUG][LLM_SUGGESTER] Validation failed: %s", exc)
            return []

        ingredients: List[Dict[str, Any]] = []
        for meal in validated.meals:
            for ingredient in meal.ingredients:
                ingredients.append(ingredient.model_dump())

        logger.debug(
            "[DEBUG][LLM_SUGGESTER] Returning %d ingredients from %d meals",
            len(ingredients),
            len(validated.meals),
        )
        return ingredients

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_prompt(
        self,
        diet_type: str,
        cuisine: str,
        meal_types: List[str],
        allergies: List[str],
        foods_to_avoid: List[str],
        exclude_ingredients: List[str],
        primary_goal: Optional[str],
        budget_constraints: Optional[str],
        lifestyle_constraints: Optional[str],
    ) -> str:
        meal_types_str = ", ".join(meal_types) if meal_types else "breakfast, lunch, dinner"
        allergies_str = ", ".join(allergies) if allergies else "none"
        avoid_str = ", ".join(foods_to_avoid) if foods_to_avoid else "none"
        exclude_str = ", ".join(exclude_ingredients) if exclude_ingredients else "none"
        goal_str = primary_goal or "maintain weight"
        budget_str = budget_constraints or "no specific budget constraints"
        lifestyle_str = lifestyle_constraints or "no specific lifestyle constraints"

        schema_example = json.dumps(
            {
                "meals": [
                    {
                        "meal_type": "breakfast",
                        "ingredients": [
                            {
                                "name": "chicken breast",
                                "category": "protein",
                                "diet_flags": ["non-vegetarian"],
                                "cuisine_tags": ["indian"],
                                "allergen_flags": [],
                            },
                            {
                                "name": "brown rice",
                                "category": "starch",
                                "diet_flags": ["vegan", "vegetarian"],
                                "cuisine_tags": ["indian"],
                                "allergen_flags": [],
                            },
                            {
                                "name": "spinach",
                                "category": "vegetables",
                                "diet_flags": ["vegan", "vegetarian"],
                                "cuisine_tags": ["indian"],
                                "allergen_flags": [],
                            },
                            {
                                "name": "olive oil",
                                "category": "fat",
                                "diet_flags": ["vegan", "vegetarian"],
                                "cuisine_tags": ["indian"],
                                "allergen_flags": [],
                            },
                        ],
                    }
                ]
            },
            indent=2,
        )

        prompt = f"""You are a professional nutritionist and meal planner.

Your task is to suggest realistic meal ingredients for a {diet_type} diet following {cuisine} cuisine preferences.

{_DIET_PRIORITY_RULES}

User details:
- Diet type: {diet_type}
- Cuisine preference: {cuisine}
- Meals to plan: {meal_types_str}
- Primary health goal: {goal_str}
- Allergies (MUST AVOID): {allergies_str}
- Foods to avoid: {avoid_str}
- Exclude for variety (already used recently): {exclude_str}
- Budget constraints: {budget_str}
- Lifestyle constraints: {lifestyle_str}

Instructions:
1. For EACH meal listed above, suggest EXACTLY 4 ingredients — one per category: protein, starch, vegetables, fat.
2. Use common ingredient names that are recognisable in a standard nutrition database (e.g., "chicken breast", "brown rice", "spinach", "olive oil").
3. For each ingredient, provide:
   - "name": common name (nutrition DB recognisable, lowercase)
   - "category": one of "protein", "starch", "vegetables", "fat"
   - "diet_flags": list of applicable flags from ["vegan", "vegetarian", "eggetarian", "non-vegetarian"]
   - "cuisine_tags": list of relevant cuisine tags (e.g., ["indian"], ["mediterranean"])
   - "allergen_flags": list of allergens present (e.g., ["gluten", "dairy", "nuts", "eggs", "soy"]) — empty list if none
4. Do NOT include any ingredient from the allergies list: {allergies_str}.
5. Do NOT include any ingredient from the foods-to-avoid list: {avoid_str}.
6. Do NOT repeat ingredients from the exclusion list: {exclude_str}.
7. Respect the diet priority rules above for ingredient selection.

Respond with ONLY valid JSON matching exactly this schema (no markdown, no explanation):
{schema_example}

Replace the example with your actual suggestions for: {meal_types_str}.
"""
        return prompt
