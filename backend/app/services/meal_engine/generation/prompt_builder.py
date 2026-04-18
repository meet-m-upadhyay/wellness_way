"""
V2 meal generation prompt builder.

Archetype-first approach: the LLM picks an archetype, fills slots with
specific ingredients + grams, specifies cooked vs raw, and outputs
structured JSON. Portion sizes are adjusted to hit macros within +-5%.
"""

import json
from typing import Dict, List, Optional

from app.services.meal_engine.config.loader import ConfigLoader


class V2PromptBuilder:
    """Builds archetype-first meal generation prompts for the LLM."""

    def __init__(self, config: Optional[ConfigLoader] = None):
        self._config = config or ConfigLoader()

    def build(
        self,
        meal_type: str,
        cuisine: str,
        diet_type: str,
        target_calories: float,
        target_protein: float,
        target_carbs: float,
        target_fat: float,
        allergies: List[str] = None,
        foods_to_avoid: List[str] = None,
        exclude_ingredients: List[str] = None,
        attempt: int = 0,
    ) -> str:
        """Build the system + user prompt for meal generation.

        Returns the full prompt string to send to the LLM.
        """
        archetypes = self._get_archetypes_for_meal(meal_type, cuisine)
        archetype_desc = self._format_archetypes(archetypes)

        variety_note = ""
        if attempt > 0:
            variety_note = f"\nIMPORTANT: This is retry #{attempt}. Pick a DIFFERENT archetype and different ingredients than previous attempts."

        exclusion_note = ""
        if exclude_ingredients:
            exclusion_note = f"\nDo NOT use these ingredients (already used in other meals): {', '.join(exclude_ingredients)}"

        allergy_note = ""
        if allergies:
            allergy_note = f"\nUser has allergies to: {', '.join(allergies)}. Strictly avoid these."

        avoid_note = ""
        if foods_to_avoid:
            avoid_note = f"\nUser wants to avoid: {', '.join(foods_to_avoid)}"

        prompt = f"""You are a professional {cuisine} nutritionist creating a {meal_type} meal.

TARGET MACROS (per meal):
- Calories: {target_calories:.0f} kcal
- Protein: {target_protein:.1f}g
- Carbs: {target_carbs:.1f}g
- Fat: {target_fat:.1f}g

DIET TYPE: {diet_type}
{allergy_note}{avoid_note}{exclusion_note}{variety_note}

AVAILABLE ARCHETYPES for {meal_type}:
{archetype_desc}

INSTRUCTIONS:
1. Pick ONE archetype from the list above
2. Fill each slot with a SPECIFIC ingredient and quantity in grams
3. For grains, legumes, and meats: ALWAYS specify "cooked" or "raw" (e.g., "Rice, cooked" not just "Rice")
4. Adjust PORTION SIZES to hit the target macros within ±5%. Do NOT swap ingredients to fix macros — only change grams.
5. Break composite dishes into base ingredients with grams (e.g., "dal" = "Red gram, dal, cooked, 100g" + "Onion, 20g" + "Ghee, 5g")
6. Use common, widely recognized ingredient names

Respond with ONLY this JSON (no markdown, no explanation):
{{
  "archetype": "archetype_key",
  "dish_name": "Human-readable meal name",
  "components": [
    {{
      "name": "Ingredient name (cooked/raw if applicable)",
      "grams": 100,
      "role": "slot_role",
      "food_group": "IFCT food group name"
    }}
  ],
  "cultural_note": "One sentence about why this is a good meal",
  "prep_time_minutes": 15
}}"""
        return prompt

    def _get_archetypes_for_meal(self, meal_type: str, cuisine: str) -> Dict:
        """Get archetypes valid for this meal type and cuisine."""
        cuisine_archetypes = self._config.archetypes.get(cuisine, {})
        valid = {}
        for key, archetype in cuisine_archetypes.items():
            if meal_type in archetype.get("meal_types", []):
                valid[key] = archetype
        return valid

    def _format_archetypes(self, archetypes: Dict) -> str:
        """Format archetypes for the prompt."""
        lines = []
        for key, arch in archetypes.items():
            slots = arch.get("slots", [])
            slot_desc = ", ".join(
                f"{s['role']} ({'required' if s.get('required') else 'optional'})"
                for s in slots
            )
            lines.append(f"- {key}: {arch['name']} — {arch.get('description', '')} [slots: {slot_desc}]")
        return "\n".join(lines) if lines else "No specific archetypes — create a balanced meal."
