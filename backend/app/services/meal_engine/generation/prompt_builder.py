"""
V2 meal generation prompt builder.

Archetype-first approach with raw-ingredient model:
- LLM picks an archetype, outputs raw ingredients + recipe
- All weights are RAW (as-purchased), matching IFCT data structure
- Recipe transforms raw ingredients into the finished dish
- No cooked/raw suffixes on ingredient names — raw by contract
"""

from typing import Dict, List, Optional

from app.services.meal_engine.config.loader import ConfigLoader


# Valid ingredient roles (fixed set)
VALID_ROLES = (
    "grain", "protein_animal", "protein_dairy", "protein_legume",
    "vegetable", "leafy_green", "starchy_vegetable", "fruit",
    "nuts_seeds", "fat_cooking", "dairy", "aromatics", "spice",
    "sweetener", "herb",
)

# Few-shot examples demonstrating the exact JSON schema
_EXAMPLE_SIMPLE = """{
  "dish_name": "Dal Rice with Spinach",
  "archetype": "thali",
  "serves": 1,
  "raw_ingredients": [
    {"name": "red gram dal", "grams": 50, "role": "protein_legume"},
    {"name": "basmati rice", "grams": 75, "role": "grain"},
    {"name": "spinach", "grams": 50, "role": "leafy_green"},
    {"name": "onion", "grams": 30, "role": "aromatics"},
    {"name": "tomato", "grams": 40, "role": "aromatics"},
    {"name": "mustard oil", "grams": 5, "role": "fat_cooking"},
    {"name": "turmeric powder", "grams": 1, "role": "spice"},
    {"name": "cumin seeds", "grams": 2, "role": "spice"},
    {"name": "green chilli", "grams": 3, "role": "spice"}
  ],
  "recipe": {
    "prep_time_min": 10,
    "cook_time_min": 25,
    "steps": [
      "Wash and soak red gram dal for 15 minutes. Wash and soak rice separately.",
      "Pressure cook dal with turmeric powder and 200ml water for 3 whistles.",
      "Meanwhile, heat mustard oil in a pan. Add cumin seeds and let them splutter.",
      "Add chopped onion and sauté until translucent. Add chopped tomato and cook until soft.",
      "Add washed spinach and slit green chilli. Cook until spinach wilts.",
      "Mix the tempering into the cooked dal. Simmer for 5 minutes.",
      "Cook soaked rice in 150ml water until fluffy. Serve dal over rice with spinach."
    ]
  },
  "cooked_serving_size_g": 450,
  "cultural_note": "A complete North Indian everyday meal with balanced protein from dal and iron from spinach."
}"""

_EXAMPLE_COMPLEX = """{
  "dish_name": "Chicken Biryani with Raita",
  "archetype": "one_pot",
  "serves": 1,
  "raw_ingredients": [
    {"name": "basmati rice", "grams": 80, "role": "grain"},
    {"name": "chicken breast", "grams": 120, "role": "protein_animal"},
    {"name": "onion", "grams": 60, "role": "aromatics"},
    {"name": "tomato", "grams": 40, "role": "aromatics"},
    {"name": "yogurt", "grams": 30, "role": "dairy"},
    {"name": "ghee", "grams": 8, "role": "fat_cooking"},
    {"name": "ginger", "grams": 5, "role": "aromatics"},
    {"name": "garlic", "grams": 5, "role": "aromatics"},
    {"name": "garam masala", "grams": 3, "role": "spice"},
    {"name": "turmeric powder", "grams": 1, "role": "spice"},
    {"name": "mint leaves", "grams": 5, "role": "herb"},
    {"name": "cucumber", "grams": 30, "role": "vegetable"}
  ],
  "recipe": {
    "prep_time_min": 20,
    "cook_time_min": 40,
    "steps": [
      "Wash basmati rice and soak for 20 minutes.",
      "Cut chicken breast into bite-sized pieces. Marinate with yogurt, turmeric, half the garam masala, and minced ginger-garlic for 15 minutes.",
      "Heat ghee in a heavy-bottomed pot. Add sliced onions and fry until golden brown.",
      "Add chopped tomato and remaining garam masala. Cook until tomatoes are soft.",
      "Add marinated chicken and cook on medium heat for 8-10 minutes until chicken is sealed.",
      "Drain soaked rice and layer on top of the chicken. Add 160ml water and torn mint leaves.",
      "Cover tightly and cook on low heat for 20 minutes. Do not open the lid.",
      "Let rest for 5 minutes. Grate cucumber into a small bowl, mix with a pinch of salt for raita.",
      "Fluff biryani gently and serve with cucumber raita."
    ]
  },
  "cooked_serving_size_g": 500,
  "cultural_note": "Classic Hyderabadi-style dum biryani with cooling cucumber raita on the side."
}"""


class V2PromptBuilder:
    """Builds archetype-first meal generation prompts with raw-ingredient model."""

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
        previous_weaknesses: str = "",
    ) -> str:
        """Build the prompt for meal generation.

        Args:
            previous_weaknesses: Feedback from prior attempt's score breakdown
                (e.g., "low vegetable diversity, excessive oil").
        """
        archetypes = self._get_archetypes_for_meal(meal_type, cuisine)
        archetype_desc = self._format_archetypes(archetypes)

        # Contextual notes
        retry_note = ""
        if attempt > 0:
            retry_note = f"\nThis is retry #{attempt}. Pick a DIFFERENT archetype and different ingredients."
            if previous_weaknesses:
                retry_note += f"\nPrevious attempt weaknesses: {previous_weaknesses}. Fix these."

        exclusion_note = ""
        if exclude_ingredients:
            exclusion_note = f"\nDo NOT use these ingredients (already in other meals today): {', '.join(exclude_ingredients[:15])}"

        allergy_note = ""
        if allergies:
            allergy_note = f"\nALLERGIES (strictly avoid): {', '.join(allergies)}"

        avoid_note = ""
        if foods_to_avoid:
            avoid_note = f"\nFoods to avoid: {', '.join(foods_to_avoid)}"

        prompt = f"""You are a professional {cuisine} nutritionist. Create a {meal_type} for 1 person.

TARGET MACROS (guideline — prioritize a real, coherent dish over exact numbers):
- Calories: {target_calories:.0f} kcal
- Protein: {target_protein:.0f}g
- Carbs: {target_carbs:.0f}g
- Fat: {target_fat:.0f}g

DIET TYPE: {diet_type}
{allergy_note}{avoid_note}{exclusion_note}{retry_note}

AVAILABLE ARCHETYPES for {meal_type}:
{archetype_desc}

INGREDIENT RULES (follow ALL of these):
- Every ingredient MUST be in raw, as-purchased form
- NEVER append ", cooked" or ", raw" to names — form is always raw by definition
- NEVER append quantities or units to names ("X, 1 piece", "X, 120g") — use the grams field
- NEVER output composite ingredients ("mixed vegetables", "peas and carrots") — list each vegetable separately with its own grams
- When the dish has roti/naan/paratha/dosa/idli, list the RAW FLOUR and FAT separately — do NOT output "roti" or "naan" as an ingredient
- Do NOT list salt, water, black pepper, or any ingredient under 1g that contributes no meaningful macros. These are implied in the recipe but not tracked as ingredients.
- NEVER list prepared spice blends, masalas, sauces, or pastes as a single ingredient UNLESS they are on this allowed list: garam masala, sambar powder, chaat masala, pav bhaji masala, biryani masala. Anything NOT on this list must be decomposed into component spices.
  WRONG: "chicken ghee roast masala", "curry paste", "tikka masala mix", "curry powder"
  RIGHT: list the component spices separately (turmeric powder, coriander powder, chili powder, etc.)
- Processed/concentrated forms of raw ingredients are NOT raw ingredients — list the raw form instead.
  WRONG: "tomato puree", "coconut milk from carton", "canned beans"
  RIGHT: "tomato", "coconut", "dried kidney beans"
- Use the SIMPLEST correct name. Do NOT prepend species or unnecessary qualifiers:
  WRONG: "chicken egg"   RIGHT: "egg"
  WRONG: "cow milk"      RIGHT: "milk"
  WRONG: "chopped cilantro"  RIGHT: "coriander leaves"
  Use qualifiers ONLY to disambiguate variety: "basmati rice" (not just "rice"), "red chili powder" (not just "chili"), "whole wheat flour" (not just "flour")
- Oil listed = what ends up IN the dish (~70% of cooking oil, rest stays in pan). Limit total oil/ghee/butter to 10g or less per meal.
- Every ingredient needs a role from: {', '.join(VALID_ROLES)}
- Keep total ingredients between 5-12 per meal. A simple breakfast needs 5-7, a complex thali needs 8-12. More than 12 is too many.

RECIPE RULES:
- Include 4-10 clear cooking steps that transform the raw ingredients into the dish
- Steps should be specific enough to actually follow
- Every ingredient listed above MUST appear in at least one recipe step
- SELF-CONSISTENCY: The dish_name must accurately reflect the actual ingredients. If the dish uses basmati rice, say "basmati rice" in the name — not "brown rice" which is a different variety. Do not name ingredients in the dish that differ from what is listed.

EXAMPLE 1 — Simple dal rice:
{_EXAMPLE_SIMPLE}

EXAMPLE 2 — Complex biryani:
{_EXAMPLE_COMPLEX}

Respond with ONLY the JSON object (no markdown, no explanation). Use the EXACT schema shown in the examples."""
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
