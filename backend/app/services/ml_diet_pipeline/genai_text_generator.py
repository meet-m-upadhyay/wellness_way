"""
GenAI Text Generator - Constrained LLM for text ONLY

This module uses GenAI ONLY for generating meal names, instructions, and descriptions.
Ingredients and quantities are READ-ONLY - NO nutrition calculations.

CRITICAL RULES:
- Ingredients and quantities are INPUT (read-only)
- Only generate: meal name, instructions, description
- Deterministic fallback if GenAI fails
- NO nutrition calculations by LLM
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class GenAITextGenerator:
    """Constrained GenAI for text generation only"""
    
    def __init__(self):
        """Initialize text generator"""
        logger.info("[GENAI_TEXT_INIT] Initialized constrained GenAI text generator")
    
    def generate_meal_text(
        self,
        ingredients: List[Dict[str, Any]],
        meal_type: str,
        diet_type: str
    ) -> Dict[str, str]:
        """
        Generate meal name and instructions for given ingredients.
        
        Args:
            ingredients: List of ingredient dicts (READ-ONLY)
            meal_type: Type of meal (breakfast, lunch, dinner, snack)
            diet_type: User's diet type
            
        Returns:
            Dict with 'name' and 'instructions'
        """
        request_id = f"text_{meal_type}_{len(ingredients)}"
        logger.info(
            f"[GENAI_TEXT_START] request_id={request_id} "
            f"meal_type={meal_type} ingredient_count={len(ingredients)}"
        )
        
        try:
            # TODO: Call LLM with constrained prompt
            # For now, use deterministic fallback
            result = self._generate_fallback_text(ingredients, meal_type, diet_type)
            
            logger.info(f"[GENAI_TEXT_FALLBACK] request_id={request_id} Using deterministic text")
            
            return result
            
        except Exception as e:
            logger.error(f"[GENAI_TEXT_ERROR] request_id={request_id} error={e}")
            # Always fallback on error
            return self._generate_fallback_text(ingredients, meal_type, diet_type)
    
    def _generate_fallback_text(
        self,
        ingredients: List[Dict[str, Any]],
        meal_type: str,
        diet_type: str
    ) -> Dict[str, str]:
        """
        Generate deterministic fallback text.
        
        Args:
            ingredients: List of ingredient dicts
            meal_type: Type of meal
            diet_type: User's diet type
            
        Returns:
            Dict with 'name' and 'instructions'
        """
        # Extract ingredient names
        ingredient_names = [ing.get("name", "ingredient") for ing in ingredients]
        
        # Generate simple meal name
        if len(ingredient_names) >= 2:
            primary = ingredient_names[0].title()
            secondary = ingredient_names[1].title()
            meal_name = f"{primary} and {secondary} {meal_type.title()}"
        else:
            meal_name = f"{ingredient_names[0].title()} {meal_type.title()}"
        
        # Generate simple instructions
        instructions = self._generate_simple_instructions(ingredients, meal_type)
        
        return {
            "name": meal_name,
            "instructions": instructions,
            "description": f"A nutritious {diet_type} {meal_type} featuring {', '.join(ingredient_names[:3])}"
        }
    
    def _generate_simple_instructions(
        self,
        ingredients: List[Dict[str, Any]],
        meal_type: str
    ) -> str:
        """Generate simple cooking instructions"""
        
        # Basic instruction templates by meal type
        if meal_type == "breakfast":
            return (
                "1. Prepare all ingredients\n"
                "2. Cook or combine ingredients as needed\n"
                "3. Serve fresh and enjoy your breakfast"
            )
        elif meal_type == "lunch":
            return (
                "1. Prepare and wash all ingredients\n"
                "2. Cook main ingredients until done\n"
                "3. Combine with sides and seasonings\n"
                "4. Serve warm"
            )
        elif meal_type == "dinner":
            return (
                "1. Prep all ingredients\n"
                "2. Cook protein and main ingredients\n"
                "3. Add vegetables and seasonings\n"
                "4. Cook until everything is done\n"
                "5. Serve hot"
            )
        else:  # snack
            return (
                "1. Prepare ingredients\n"
                "2. Combine or arrange as desired\n"
                "3. Enjoy as a healthy snack"
            )
    
    def generate_daily_plan_text(
        self,
        meals: List[Dict[str, Any]],
        diet_type: str
    ) -> Dict[str, str]:
        """
        Generate text for a daily plan.
        
        Args:
            meals: List of meal dicts
            diet_type: User's diet type
            
        Returns:
            Dict with plan-level text
        """
        logger.info(f"[GENAI_DAILY_TEXT_START] meal_count={len(meals)} diet={diet_type}")
        
        # Generate simple daily summary
        total_calories = sum(m.get("nutrition", {}).get("calories", 0) for m in meals)
        total_protein = sum(m.get("nutrition", {}).get("protein", 0) for m in meals)
        
        summary = (
            f"A balanced {diet_type} meal plan with {len(meals)} meals, "
            f"providing approximately {total_calories:.0f} calories and "
            f"{total_protein:.1f}g of protein."
        )
        
        return {
            "summary": summary,
            "notes": "Adjust portions based on your individual needs and activity level."
        }


# Singleton instance
_generator: Optional[GenAITextGenerator] = None


def get_genai_text_generator() -> GenAITextGenerator:
    """Get singleton instance of GenAI text generator"""
    global _generator
    if _generator is None:
        _generator = GenAITextGenerator()
    return _generator
