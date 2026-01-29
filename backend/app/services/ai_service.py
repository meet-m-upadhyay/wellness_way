"""
AI service for diet plan generation - REFACTORED ARCHITECTURE

This module provides ONLY meal ideation using LLM.
ALL nutrition calculations are handled by the nutrition engine.
The LLM is NEVER the source of truth for nutrition data.

CRITICAL SEPARATION OF CONCERNS:
- LLM: Meal names, ingredients, rough portions, instructions
- Backend: All nutrition calculations, safety validation, constraint enforcement
"""

import json
import logging
import re
from typing import Dict, List, Optional, Any
from openai import AsyncOpenAI
import asyncio
from datetime import datetime
from uuid import uuid4, UUID
import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings
from app.services.ai_providers import get_ai_provider, MockAIProvider
from app.services.ai_provider_manager import get_provider_manager, RetryResult
from app.services.nutrition_engine import (
    get_nutrition_engine, DayPlan, Meal, 
    ZeroCalorieError, NutritionCalculationError
)
from app.services.nutrition_database import get_nutrition_database
from app.services.ingredient_normalizer import UnknownIngredientError
from app.services.nutrition_database import IngredientResolutionError
from app.services.llm_contract_enforcer import enforce_llm_contract, LLMContractViolation, RetryableLLMError

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """Base exception for AI service errors"""
    pass


class AIServiceTimeoutError(AIServiceError):
    """Raised when AI service request times out"""
    pass


class AIServiceValidationError(AIServiceError):
    """Raised when AI response validation fails"""
    pass


class LLMContractViolationError(AIServiceError):
    """Raised when LLM violates the contract by including nutrition data"""
    pass


class RetryableLLMError(AIServiceError):
    """Raised when LLM output is malformed but retryable (e.g., invalid JSON)"""
    pass


class AIServiceRateLimitError(AIServiceError):
    """Raised when all providers are rate limited"""
    pass


class AIServiceProviderError(AIServiceError):
    """Raised when all providers fail"""
    pass


class OpenAIClient:
    """OpenAI API client wrapper with error handling and retries"""
    
    def __init__(self):
        """Initialize OpenAI client with configuration"""
        api_key = settings.get_openai_api_key()
        if not api_key:
            raise AIServiceError("OpenAI API key not configured")
        
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = settings.ai.openai_model
        self.max_tokens = settings.ai.openai_max_tokens
        self.temperature = settings.ai.openai_temperature
        self.timeout = settings.ai.openai_timeout
        
        logger.info(f"OpenAI client initialized with model: {self.model}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((AIServiceTimeoutError, Exception))
    )
    async def generate_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: Optional[Dict] = None
    ) -> tuple[str, Dict[str, Any]]:
        """
        Generate completion using OpenAI API with retries.
        
        Args:
            system_prompt: System prompt defining AI behavior
            user_prompt: User prompt with specific request
            response_format: Optional JSON schema for structured output
        
        Returns:
            Tuple of (AI response content, usage data)
            
        Raises:
            AIServiceError: If API call fails after retries
            AIServiceTimeoutError: If request times out
        """
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Prepare request parameters
            request_params = {
                "model": self.model,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "timeout": self.timeout
            }
            
            # Add response format if specified (for structured output)
            if response_format:
                request_params["response_format"] = response_format
            
            logger.info(f"Making OpenAI API request with model: {self.model}")
            
            # Make API call with timeout
            response = await asyncio.wait_for(
                self.client.chat.completions.create(**request_params),
                timeout=self.timeout
            )
            
            # Extract content from response
            if not response.choices:
                raise AIServiceError("No response choices returned from OpenAI")
            
            content = response.choices[0].message.content
            if not content:
                raise AIServiceError("Empty content returned from OpenAI")
            
            # Extract usage data
            usage_data = {}
            if hasattr(response, 'usage') and response.usage:
                usage_data = {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }
            
            logger.info("OpenAI API request completed successfully")
            return content.strip(), usage_data
            
        except asyncio.TimeoutError:
            logger.error(f"OpenAI API request timed out after {self.timeout} seconds")
            raise AIServiceTimeoutError(f"Request timed out after {self.timeout} seconds")
        
        except Exception as e:
            logger.error(f"OpenAI API request failed: {str(e)}")
            raise AIServiceError(f"OpenAI API request failed: {str(e)}")


class DietPlanAI:
    """
    AI service for diet plan generation - REFACTORED ARCHITECTURE
    
    RESPONSIBILITIES (LIMITED):
    1. Generate meal ideas and ingredient suggestions using LLM
    2. Provide rough portion estimates (NOT nutrition calculations)
    3. Ensure meal variety and dietary compliance suggestions
    
    NOT RESPONSIBLE FOR:
    - Nutrition calculations (handled by NutritionEngine)
    - Safety constraint enforcement (handled by validators)
    - Final portion sizing (handled by NutritionEngine auto-correction)
    """
    
    def __init__(self, db_session=None):
        """Initialize diet plan AI service with provider manager integration"""
        self.provider_manager = get_provider_manager()
        self.nutrition_engine = get_nutrition_engine()
        self.nutrition_db = get_nutrition_database()
        self.db_session = db_session
        self._monitoring_service = None
        
        # Log provider manager status
        logger.info(f"DietPlanAI initialized with provider manager")
        logger.info(f"Available providers: {list(self.provider_manager.providers.keys())}")
        
        # Initialize monitoring if database session provided
        if self.db_session:
            from app.services.ai_monitoring import get_monitoring_service
            self._monitoring_service = get_monitoring_service(self.db_session)
    
    def _get_system_prompt(self) -> str:
        """
        Get the OPTIMIZED system prompt for meal ideation only.
        
        CRITICAL: This prompt does NOT ask for nutrition calculations.
        The LLM provides ONLY meal ideas and rough portions.
        """
        return """You are a meal planning assistant for WellnessWay Diet Planner.

ROLE:
Suggest meal names, RAW ingredients, rough portions, and instructions ONLY.

CRITICAL SEPARATION OF CONCERNS:
- LLM: Meal ideas, ingredient selection, rough portions
- Backend: ALL nutrition calculations, validation, safety, scaling

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ABSOLUTE RULES (NON-NEGOTIABLE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. DO NOT include nutrition, calories, macros, or totals
2. Output ONLY meals, ingredients, quantities, and instructions
3. Use ONLY ingredients from the allowed ingredients list provided
4. NEVER invent ingredients
5. NEVER guess nutrition
6. If unsure, choose a safer known ingredient

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INGREDIENT ONTOLOGY RULE (CRITICAL)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ingredients MUST be:
- RAW
- SINGLE-INGREDIENT
- DIRECTLY TRACEABLE to the nutrition database

❌ FORBIDDEN (COMPOSITE / PREPARED FOODS):
- hummus, pesto, guacamole, chutney
- protein scramble, protein bowl, veggie wrap
- curry, stew, salad, sandwich
- sauces, spreads, dips
- any dish-like or prepared food

✅ REQUIRED BEHAVIOR:
If a food is normally prepared, DECOMPOSE it into raw ingredients.

Example:
❌ hummus
✅ chickpeas (dry), tahini, olive oil, lemon juice

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DIET TYPE EXTENSION RULE (CRITICAL)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

If diet_type is "non_vegetarian":

- You may ONLY use meats or fish that appear in the allowed ingredients list
- Allowed meats are RAW only
- Examples of VALID meats:
  - "chicken breast (raw)"
  - "salmon (raw)"
  - "tuna (raw)"
  - "white fish (raw)"

FORBIDDEN:
- cooked, grilled, roasted, marinated meats
- dish names like "chicken curry", "fish fry"
- vague terms like "meat", "fish", "seafood"
- composite or prepared meat foods

If a requested meat is NOT present in the allowed ingredients list:
→ choose the closest listed RAW alternative
→ NEVER invent a new ingredient

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
UNIT RULES (STRICT)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- ONLY allowed unit: "g"
- NEVER use: pc, piece, cup, tbsp, tsp, slice, handful
- Eggs MUST be in grams (e.g. 120g eggs whole)
- Fruits and vegetables MUST be in grams
- If unsure, estimate weight in grams

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MEAL NAMING RULE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- Meal names are DESCRIPTIVE ONLY
- Meal names must NEVER appear as ingredient names
- Ingredients must always be real foods, not dish names

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MEAL VARIETY REQUIREMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- NEVER repeat meal names
- Vary cuisines (Mediterranean, Indian, Asian, Mexican, Italian)
- Vary cooking methods (roasted, stir-fry, baked, raw, steamed)
- Avoid repetitive patterns like:
  - "Greek Yogurt Bowl"
  - "Tofu Bowl"
  - "Lentil Stew"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ENERGY & PROTEIN RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- Protein-only meals are FORBIDDEN
- Meals under 350 kcal are INVALID for main meals
- If protein is high but calories are low, ADD:
  - complex carbs (rice, oats, quinoa, potatoes)
  - OR healthy fats (olive oil, nuts, seeds)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PORTIONS (ROUGH ESTIMATES ONLY)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- Main proteins: 100–200g
- Grains: 50–100g (dry)
- Vegetables: 100–300g
- Nuts/seeds: 20–50g

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
JSON OUTPUT RULES (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- Output VALID minified JSON ONLY
- No markdown, no comments, no explanations
- No trailing commas
- No line breaks inside strings
- All strings must be single-line and escaped
- Must be parseable by json.loads()
- NEVER include nutrition data

If you cannot comply with ALL rules → output {}"""

    def _get_meal_planning_prompt(self, json_context: Dict, plan_type: str, target_date: Optional[str] = None, retry_context: Optional[Dict] = None) -> str:
        """
        Create focused meal planning prompt using JSON context.
        
        This prompt asks ONLY for meal ideas, not nutrition calculations.
        INCLUDES INPUT CONTRACT ENFORCEMENT - only allowed ingredients.
        """
        date_instruction = ""
        if plan_type == "daily" and target_date:
            date_instruction = f"\nGenerate meals for date: {target_date}"
        
        # Add retry constraints if provided
        retry_constraints = ""
        if retry_context:
            avoid_ingredients = retry_context.get('avoid_ingredients', [])
            if avoid_ingredients:
                retry_constraints = f"\nIMPORTANT: Avoid these ingredients that caused issues: {', '.join(avoid_ingredients)}"
                retry_constraints += f"\nUse alternative ingredients from the allowed list instead."
        
        # Get allowed ingredients list from nutrition database (INPUT CONTRACT ENFORCEMENT)
        allowed_ingredients_prompt = self.nutrition_db.get_allowed_ingredients_prompt()
        
        context_summary = f"""
USER CONTEXT:
- Diet Type: {json_context['diet_restrictions']['diet_type']}
- Allergies: {', '.join(json_context['diet_restrictions'].get('allergies', [])) if json_context['diet_restrictions'].get('allergies') else 'None'}
- Foods to Avoid: {', '.join(json_context['diet_restrictions'].get('foods_to_avoid', [])) if json_context['diet_restrictions'].get('foods_to_avoid') else 'None'}
- Meals per Day: {json_context['diet_restrictions']['meals_per_day']}
- Primary Goal: {json_context['goals']['primary_goal']}
- Lifestyle: {json_context.get('preferences', {}).get('lifestyle_constraints', 'None')}

GOAL: Create {plan_type} meal plan with HIGH PROTEIN focus and maximum variety.{retry_constraints}
"""
        
        if plan_type == "weekly":
            format_example = """
{
  "plan_type": "weekly",
  "meals": [
    {
      "day": 1,
      "day_name": "Monday",
      "breakfast": {
        "name": "Creative High-Protein Breakfast Name",
        "ingredients": [
          {"name": "greek yogurt (plain)", "quantity": 150, "unit": "g"},
          {"name": "hemp seeds", "quantity": 20, "unit": "g"}
        ],
        "instructions": "Simple cooking steps focusing on protein preparation"
      },
      "lunch": {
        "name": "Different High-Protein Lunch Name",
        "ingredients": [
          {"name": "tofu (extra-firm)", "quantity": 200, "unit": "g"},
          {"name": "cooked quinoa", "quantity": 80, "unit": "g"}
        ],
        "instructions": "Clear preparation steps"
      },
      "dinner": {
        "name": "Unique High-Protein Dinner Name",
        "ingredients": [
          {"name": "lentils (red, dry)", "quantity": 60, "unit": "g"},
          {"name": "spinach", "quantity": 200, "unit": "g"}
        ],
        "instructions": "Detailed cooking instructions"
      }
    }
  ]
}

CRITICAL WEEKLY REQUIREMENTS:
- 7 completely different days of meals
- No repeated primary protein sources within each day
- No repeated primary carb sources within each day
- Each day should feel like a completely different eating experience"""
        else:
            format_example = """
{
  "plan_type": "daily",
  "date": "YYYY-MM-DD",
  "breakfast": {
    "name": "High-Protein Breakfast Name",
    "ingredients": [
      {"name": "greek yogurt (plain)", "quantity": 150, "unit": "g"},
      {"name": "hemp seeds", "quantity": 20, "unit": "g"}
    ],
    "instructions": "Step-by-step preparation focusing on protein"
  },
  "lunch": {
    "name": "Different High-Protein Lunch Name",
    "ingredients": [
      {"name": "tofu (extra-firm)", "quantity": 200, "unit": "g"},
      {"name": "cooked quinoa", "quantity": 80, "unit": "g"}
    ],
    "instructions": "Clear cooking instructions"
  },
  "dinner": {
    "name": "Unique High-Protein Dinner Name",
    "ingredients": [
      {"name": "lentils (red, dry)", "quantity": 60, "unit": "g"},
      {"name": "spinach", "quantity": 200, "unit": "g"}
    ],
    "instructions": "Detailed preparation steps"
  }
}

CRITICAL DAILY REQUIREMENTS:
- Each meal uses DIFFERENT primary protein sources
- Each meal uses DIFFERENT primary carb sources
- Focus on high-protein, muscle-building nutrition"""
        
        prompt = f"""{context_summary}

{allowed_ingredients_prompt}

Generate a creative {plan_type} meal plan with HIGH PROTEIN focus.{date_instruction}

VARIETY CHALLENGE: Create meals that are completely different from these common patterns:
- Avoid: "Greek Yogurt [X] Bowl/Parfait" 
- Avoid: "Tofu [X] Bowl/Stir-fry"
- Avoid: "Lentil [X] Stew/Curry"
- Use simple creative names: "Protein Scramble", "Veggie Wrap", "Bean Salad"

CREATIVITY SEED: {datetime.now().strftime('%H%M%S')} - Use this to inspire unique meal combinations.

MEAL IDEATION REQUIREMENTS:
1. Suggest creative, appealing meal names
2. Choose ingredients ONLY from the allowed ingredients list above
3. Provide rough portion estimates (backend will calculate exact nutrition)
4. Ensure maximum variety between meals
5. Focus on high-protein ingredients from the allowed list
6. Write clear, practical cooking instructions

DIETARY COMPLIANCE:
- Strictly follow diet type: {json_context['diet_restrictions']['diet_type']}
- Avoid all allergies: {json_context['diet_restrictions'].get('allergies', [])}
- Exclude foods to avoid: {json_context['diet_restrictions'].get('foods_to_avoid', [])}

CRITICAL JSON OUTPUT RULES (MANDATORY):
- Output valid minified JSON only
- No markdown, no comments, no explanations
- No trailing commas
- No line breaks inside strings
- Must be parseable by json.loads()
- Never include nutrition, calories, protein, macros, or totals
- Use EXACT ingredient names from allowed list only
- If any rule is violated -> output is invalid

RESPOND WITH ONLY VALID JSON:
{format_example}

Remember: You suggest meals using ONLY allowed ingredients, the backend calculates nutrition and enforces all constraints."""
        
        return prompt

    async def generate_diet_plan(
        self,
        health_context: str,  # Accept markdown HCD for backward compatibility
        plan_type: str,
        target_date: Optional[str] = None,
        user_id: Optional[UUID] = None,
        health_context_json: Optional[Dict] = None,  # New JSON context parameter
        avoid_ingredients: Optional[List[str]] = None  # Ingredients to avoid in generation
    ) -> Dict[str, Any]:
        """
        Generate a diet plan using the NEW ARCHITECTURE.
        
        PROCESS:
        1. LLM generates meal ideas and rough portions (NO nutrition calculations)
        2. NutritionEngine calculates accurate nutrition from ingredients
        3. Backend validators enforce all safety constraints
        4. Auto-correction applied if needed
        
        Args:
            health_context: Markdown HCD content (for backward compatibility)
            plan_type: Type of plan ('weekly' or 'daily')
            target_date: Optional target date for daily plans
            user_id: Optional user ID for monitoring
            health_context_json: Optional JSON context (preferred for new architecture)
            avoid_ingredients: Optional list of ingredients to avoid (for smart retry logic)
        
        Returns:
            Complete diet plan with accurate nutrition calculations
            
        Raises:
            AIServiceError: If plan generation fails
            AIServiceValidationError: If response validation fails
        """
        request_id = str(uuid4())
        start_time = time.time()
        success = False
        error_message = None
        
        try:
            # Handle backward compatibility: extract JSON from markdown if needed
            if health_context_json is None:
                # For backward compatibility, parse JSON from markdown HCD
                # This is a temporary solution until all callers are updated
                health_context_json = self._extract_json_from_markdown_hcd(health_context)
            
            # Validate health context JSON has all required fields
            self._validate_health_context_json(health_context_json)
            
            # Step 1: Get meal ideas from LLM (NO nutrition calculations)
            # Build retry context with avoid_ingredients if provided
            retry_context = None
            if avoid_ingredients:
                retry_context = {"avoid_ingredients": avoid_ingredients}
            
            meal_ideas = await self._get_meal_ideas_from_llm(
                health_context_json, plan_type, target_date, request_id, retry_context
            )
            
            # Step 2: Convert meal ideas to accurate nutrition using backend engine
            diet_plan = await self._convert_meal_ideas_to_nutrition_plan(
                meal_ideas, health_context_json, plan_type, target_date
            )
            
            # Step 3: REMOVED - Validation now handled by deterministic scaling system
            # The AI service only generates meal ideas - all validation/scaling is in diet_plan_service
            
            success = True
            logger.info(f"Successfully generated {plan_type} diet plan with meal ideas (request_id: {request_id})")
            return diet_plan
            
        except Exception as e:
            error_message = f"Diet plan generation failed: {str(e)}"
            logger.error(error_message)
            
            # TERMINAL FAILURES - Do not retry, propagate immediately
            if isinstance(e, (UnknownIngredientError, IngredientResolutionError, 
                            ZeroCalorieError, NutritionCalculationError)):
                logger.error(f"TERMINAL FAILURE - Ingredient/nutrition error: {str(e)}")
                # Re-raise as-is - these should not be retried
                raise
            
            elif isinstance(e, LLMContractViolationError):
                logger.error("TERMINAL FAILURE - LLM contract violation detected")
                # Re-raise as-is - these should not be retried
                raise
            
            # RETRYABLE FAILURES - Enhanced error handling for provider-aware retry system
            elif isinstance(e, AIServiceRateLimitError):
                logger.warning("All providers are rate limited, falling back to mock data")
                try:
                    return await self._generate_mock_fallback_plan(health_context_json, plan_type, target_date)
                except Exception as fallback_error:
                    logger.error(f"Mock fallback also failed: {fallback_error}")
                    raise AIServiceError(f"All providers rate limited and mock fallback failed: {fallback_error}")
            
            elif isinstance(e, AIServiceProviderError):
                logger.warning("All providers failed, falling back to mock data")
                try:
                    return await self._generate_mock_fallback_plan(health_context_json, plan_type, target_date)
                except Exception as fallback_error:
                    logger.error(f"Mock fallback also failed: {fallback_error}")
                    raise AIServiceError(f"All providers failed and mock fallback failed: {fallback_error}")
            
            # Legacy fallback for rate limit detection in error message
            elif "rate limit" in str(e).lower():
                logger.warning("Rate limit detected in error message, falling back to mock data")
                try:
                    return await self._generate_mock_fallback_plan(health_context_json, plan_type, target_date)
                except Exception as fallback_error:
                    logger.error(f"Mock fallback also failed: {fallback_error}")
            
            # All other errors are treated as retryable AI service errors
            raise AIServiceError(error_message)
        
        finally:
            # Log monitoring data if monitoring is enabled
            if self._monitoring_service:
                self._log_monitoring_data(request_id, user_id, plan_type, success, error_message, start_time)
    
    def _extract_json_from_markdown_hcd(self, markdown_hcd: str) -> Dict:
        """
        Extract JSON context from markdown HCD for backward compatibility.
        
        This is a temporary solution until all callers are updated to use JSON context.
        """
        # For now, create a basic JSON context from markdown parsing
        # In a full implementation, this would parse the markdown more thoroughly
        
        # Basic fallback JSON context with ALL required fields
        return {
            "user": {
                "weight_kg": 70.0,
                "age": 30,
                "gender": "male",
                "activity_level": "moderately_active"
            },
            "goals": {
                "primary_goal": "fat_loss",
                "target_weight_kg": 65.0,
                "timeline_weeks": 8,
                "is_realistic": True
            },
            "diet_restrictions": {
                "diet_type": "vegetarian",
                "allergies": [],  # CRITICAL: Always provide this field
                "foods_to_avoid": [],  # CRITICAL: Always provide this field
                "meals_per_day": 3
            },
            "nutrition_targets": {
                "target_calories": 2000.0,
                "min_protein_g": 70.0,
                "target_protein_g": 95.0,
                "target_carbs_g": 250.0,
                "target_fat_g": 67.0
            },
            "safety_constraints": {
                "min_daily_calories": 1500.0,
                "max_calorie_deficit": 500.0,
                "max_safe_loss_per_week": 1.0
            },
            "preferences": {
                "budget_constraints": "moderate",
                "lifestyle_constraints": "busy schedule"
            }
        }
    
    def _validate_health_context_json(self, health_context_json: Dict) -> None:
        """
        Validate that health context JSON has all required fields.
        
        Args:
            health_context_json: Health context dictionary to validate
            
        Raises:
            AIServiceError: If required fields are missing
        """
        required_fields = {
            'user': ['weight_kg', 'age', 'gender', 'activity_level'],
            'goals': ['primary_goal'],
            'diet_restrictions': ['diet_type', 'meals_per_day'],
            'nutrition_targets': ['target_calories', 'target_protein_g']
        }
        
        missing_fields = []
        
        for section, fields in required_fields.items():
            if section not in health_context_json:
                missing_fields.append(f"Missing section: {section}")
                continue
                
            section_data = health_context_json[section]
            for field in fields:
                if field not in section_data:
                    missing_fields.append(f"Missing field: {section}.{field}")
        
        # Check optional fields and provide defaults
        if 'preferences' not in health_context_json:
            logger.warning("Missing 'preferences' section in health context, using defaults")
            health_context_json['preferences'] = {
                'budget_constraints': 'moderate',
                'lifestyle_constraints': 'busy schedule'
            }
        
        if 'safety_constraints' not in health_context_json:
            logger.warning("Missing 'safety_constraints' section in health context, using defaults")
            health_context_json['safety_constraints'] = {
                'min_daily_calories': 1500.0,
                'max_calorie_deficit': 500.0,
                'max_safe_loss_per_week': 1.0
            }
        
        # Ensure allergies and foods_to_avoid are lists
        diet_restrictions = health_context_json.get('diet_restrictions', {})
        if 'allergies' not in diet_restrictions:
            diet_restrictions['allergies'] = []
        if 'foods_to_avoid' not in diet_restrictions:
            diet_restrictions['foods_to_avoid'] = []
        
        if missing_fields:
            error_msg = f"Health context JSON validation failed: {', '.join(missing_fields)}"
            logger.error(error_msg)
            raise AIServiceError(error_msg)
        
        logger.debug("Health context JSON validation passed")
    
    def _enforce_llm_contract(self, meal_ideas: Dict) -> None:
        """
        CRITICAL: Enforce LLM contract - NO NUTRITION CALCULATIONS ALLOWED
        
        The LLM must ONLY provide meal names, ingredients, and instructions.
        Any nutrition data in the response is a contract violation.
        """
        forbidden_fields = [
            'nutrition', 'calories', 'protein', 'carbohydrates', 'fat', 'fiber', 'sodium',
            'daily_totals', 'weekly_totals', 'macro', 'macros', 'kcal', 'carbs'
        ]
        
        violations = []
        
        def check_dict_for_nutrition(data, path=""):
            """Recursively check dictionary for forbidden nutrition fields"""
            if isinstance(data, dict):
                for key, value in data.items():
                    key_lower = str(key).lower()
                    current_path = f"{path}.{key}" if path else key
                    
                    # Check if key is forbidden
                    if any(forbidden in key_lower for forbidden in forbidden_fields):
                        violations.append(f"Forbidden nutrition field '{key}' found at {current_path}")
                    
                    # Recursively check nested structures
                    check_dict_for_nutrition(value, current_path)
            
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    check_dict_for_nutrition(item, f"{path}[{i}]")
        
        # Check the entire meal ideas structure
        check_dict_for_nutrition(meal_ideas)
        
        if violations:
            violation_summary = "; ".join(violations)
            logger.error(f"LLM CONTRACT VIOLATION: {violation_summary}")
            raise LLMContractViolationError(
                f"LLM attempted nutrition calculation - STRICT CONTRACT VIOLATION. "
                f"Found forbidden fields: {violation_summary}. "
                f"LLM must ONLY provide meal names, ingredients, and instructions."
            )
        
        logger.info("[OK] LLM contract enforced - no nutrition fields detected")
    
    async def _get_meal_ideas_from_llm(
        self, 
        health_context_json: Dict, 
        plan_type: str, 
        target_date: Optional[str],
        request_id: str,
        retry_context: Optional[Dict] = None
    ) -> Dict:
        """Get meal ideas from LLM using provider-aware retry system with hard contract enforcement"""
        
        # Create focused meal planning prompt with retry context
        system_prompt = self._get_system_prompt()
        user_prompt = self._get_meal_planning_prompt(health_context_json, plan_type, target_date, retry_context)
        
        logger.info(f"Getting meal ideas using provider manager (request_id: {request_id})")
        
        # Use provider manager for intelligent retry with token limits
        retry_result = await self.provider_manager.generate_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            preferred_provider=settings.ai.ai_provider if hasattr(settings.ai, 'ai_provider') else None,
            temperature=0.2  # Moderate creativity with reliable JSON structure
        )
        
        # Check if retry was successful
        if not retry_result.success:
            logger.error(f"All providers failed: {retry_result.failure_reason}")
            
            # Classify the failure type for better error handling
            if "rate limit" in retry_result.failure_reason.lower():
                raise AIServiceRateLimitError(
                    f"All providers are rate limited. {retry_result.failure_reason}"
                )
            elif "contract violation" in retry_result.failure_reason.lower():
                raise LLMContractViolationError(
                    f"LLM contract violation across providers. {retry_result.failure_reason}"
                )
            else:
                raise AIServiceProviderError(
                    f"All providers failed. {retry_result.failure_reason}"
                )
        
        # Store usage data for monitoring
        self._last_usage_data = retry_result.usage_data or {}
        self._last_retry_result = retry_result
        
        logger.info(f"Successfully got meal ideas from {retry_result.final_provider} "
                   f"after {len(retry_result.attempts)} attempts in {retry_result.total_time_seconds:.2f}s")
        
        # CRITICAL: Enforce LLM contract using hard schema gate
        logger.debug(f"RAW LLM OUTPUT: {retry_result.content}")
        
        try:
            meal_ideas = enforce_llm_contract(retry_result.content.strip(), request_id)
            
            # ADDITIONAL: Validate ingredient contract (only allowed ingredients)
            self._validate_ingredient_contract(meal_ideas, request_id)
            
            return meal_ideas
        except RetryableLLMError as e:
            logger.warning(f"Retryable LLM error: {str(e)}")
            # Re-raise as AIServiceValidationError to trigger retry
            raise AIServiceValidationError(f"LLM output formatting error: {str(e)}")
        except json.JSONDecodeError as e:
            logger.warning(f"Initial JSON parse failed: {str(e)}")
            
            # SINGLE-SHOT JSON REPAIR - NO LOOPS
            try:
                repaired_content = await self._repair_json_formatting(retry_result.content, request_id)
                meal_ideas = enforce_llm_contract(repaired_content, request_id)
                
                # Validate ingredient contract on repaired content too
                self._validate_ingredient_contract(meal_ideas, request_id)
                
                logger.info(f"JSON repair successful for request {request_id}")
                return meal_ideas
            except (json.JSONDecodeError, LLMContractViolation, RetryableLLMError) as repair_error:
                logger.error(f"JSON repair failed: {repair_error}")
                raise AIServiceValidationError(f"Invalid JSON response from LLM after repair: {str(e)}")
        except LLMContractViolation as e:
            logger.error(f"LLM CONTRACT VIOLATION: {e.message}")
            logger.error(f"Forbidden fields found: {e.forbidden_fields}")
            raise LLMContractViolationError(f"LLM contract violation: {e.message}")
    
    def _validate_ingredient_contract(self, meal_ideas: Dict, request_id: str) -> None:
        """
        Validate that all ingredients in meal ideas exist in the nutrition database.
        
        This enforces the INPUT CONTRACT - LLM must only use known ingredients.
        
        CRITICAL FIX: Use the ingredient normalizer to handle cooking modifiers properly,
        then check if the normalized ingredient exists in the database.
        
        Args:
            meal_ideas: Parsed meal ideas from LLM
            request_id: Request ID for logging
            
        Raises:
            LLMContractViolationError: If unknown ingredients are found
        """
        from .ingredient_normalizer import get_ingredient_normalizer, UnknownIngredientError
        
        normalizer = get_ingredient_normalizer()
        unknown_ingredients = []
        all_ingredients = set()
        
        def extract_ingredients(obj, path=""):
            """Recursively extract ingredient names from meal structure"""
            if isinstance(obj, dict):
                if 'ingredients' in obj and isinstance(obj['ingredients'], list):
                    for ingredient in obj['ingredients']:
                        if isinstance(ingredient, dict) and 'name' in ingredient:
                            raw_name = ingredient['name'].strip().lower()
                            all_ingredients.add(raw_name)
                            
                            try:
                                # CRITICAL FIX: Use the ingredient normalizer to handle cooking modifiers
                                # This is the same normalization path used by the nutrition engine
                                normalization_result = normalizer.normalize(raw_name)
                                
                                if normalization_result.is_resolved:
                                    # Ingredient was successfully normalized
                                    canonical_name = normalization_result.canonical_name
                                    
                                    # Check if the canonical ingredient exists in the database
                                    if self.nutrition_db.validate_food_exists(canonical_name):
                                        # Ingredient is valid
                                        if raw_name != canonical_name:
                                            logger.debug(f"[INGREDIENT_CANONICALIZED] raw=\"{raw_name}\" → canonical=\"{canonical_name}\"")
                                    else:
                                        # Canonical ingredient not found in database
                                        unknown_ingredients.append(raw_name)
                                        logger.debug(f"[CANONICALIZATION_FAILED] raw=\"{raw_name}\" → canonical=\"{canonical_name}\" (not found in database)")
                                else:
                                    # Ingredient could not be resolved
                                    unknown_ingredients.append(raw_name)
                                    logger.debug(f"[NORMALIZATION_FAILED] raw=\"{raw_name}\" could not be normalized")
                                    
                            except UnknownIngredientError:
                                # Ingredient category is completely unknown
                                unknown_ingredients.append(raw_name)
                                logger.debug(f"[UNKNOWN_CATEGORY] raw=\"{raw_name}\" has unknown category")
                
                # Recursively check nested objects
                for key, value in obj.items():
                    extract_ingredients(value, f"{path}.{key}" if path else key)
            
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    extract_ingredients(item, f"{path}[{i}]" if path else f"[{i}]")
        
        # Extract all ingredients from meal ideas
        extract_ingredients(meal_ideas)
        
        if unknown_ingredients:
            logger.error(f"INGREDIENT CONTRACT VIOLATION (request_id: {request_id}): "
                        f"Unknown ingredients found: {unknown_ingredients}")
            logger.error(f"Total ingredients checked: {len(all_ingredients)}")
            logger.error(f"Unknown count: {len(unknown_ingredients)}")
            
            # Log some examples of valid ingredients for debugging
            valid_examples = [ing for ing in all_ingredients if ing not in unknown_ingredients][:5]
            logger.info(f"Valid ingredients found: {valid_examples}")
            
            raise LLMContractViolationError(
                "LLM used forbidden or composite ingredients. "
                f"Unknown ingredients: {unknown_ingredients[:5]}. "
                "Use ONLY raw ingredients from the allowed list. "
                "Composite foods must be decomposed into raw ingredients."
            )
        
        logger.info(f"[OK] Ingredient contract validated (request_id: {request_id}): "
                   f"All {len(all_ingredients)} ingredients are known")
    
    
    async def _convert_meal_ideas_to_nutrition_plan(
        self, 
        meal_ideas: Dict, 
        health_context_json: Dict,
        plan_type: str,
        target_date: Optional[str]
    ) -> Dict:
        """Convert LLM meal ideas to accurate nutrition plan using backend engine"""
        
        # Extract nutrition targets from context
        nutrition_targets = health_context_json['nutrition_targets']
        target_protein_per_meal = nutrition_targets['target_protein_g'] / health_context_json['diet_restrictions']['meals_per_day']
        
        if plan_type == "daily":
            # Process single day
            meals = []
            for meal_type in ['breakfast', 'lunch', 'dinner']:
                if meal_type in meal_ideas:
                    meal_data = meal_ideas[meal_type]
                    
                    # Calculate accurate nutrition using backend engine with resolution
                    meal = await self.nutrition_engine.create_meal_with_resolution(
                        meal_name=meal_data['name'],
                        ingredients_list=meal_data['ingredients'],
                        instructions=meal_data['instructions'],
                        meal_type=meal_type,
                        target_protein_g=target_protein_per_meal
                    )
                    meals.append(meal)
            
            # Create day plan with accurate nutrition
            day_plan = DayPlan(
                date=target_date or meal_ideas.get('date', '2024-01-01'),
                meals=meals
            )
            
            # Convert to API format
            return self._convert_day_plan_to_api_format(day_plan)
        
        else:  # weekly
            days = []
            for day_data in meal_ideas.get('meals', []):
                day_meals = []
                for meal_type in ['breakfast', 'lunch', 'dinner']:
                    if meal_type in day_data:
                        meal_data = day_data[meal_type]
                        
                        # Calculate accurate nutrition with resolution
                        meal = await self.nutrition_engine.create_meal_with_resolution(
                            meal_name=meal_data['name'],
                            ingredients_list=meal_data['ingredients'],
                            instructions=meal_data['instructions'],
                            meal_type=meal_type,
                            target_protein_g=target_protein_per_meal
                        )
                        day_meals.append(meal)
                
                # Create day plan
                day_plan = DayPlan(
                    date=f"2024-01-{day_data.get('day', 1):02d}",
                    meals=day_meals
                )
                days.append(day_plan)
            
            # Convert to API format
            return self._convert_weekly_plan_to_api_format(days)
    
    def _validate_complete_plan(self, diet_plan: Dict, health_context_json: Dict) -> tuple[bool, List[str]]:
        """
        DISABLED: Validation now handled by deterministic scaling system.
        
        The AI service should ONLY generate meal ideas.
        ALL validation and scaling is handled by the diet_plan_service pipeline.
        """
        # Always return valid - let the new pipeline handle validation
        return True, []
    
    async def _auto_correct_plan(self, diet_plan: Dict, health_context_json: Dict, violations: List[str]) -> Dict:
        """
        DISABLED: Auto-correction now handled by deterministic scaling system.
        
        The AI service should ONLY generate meal ideas.
        ALL scaling and correction is handled by the diet_plan_service pipeline.
        """
        # Return plan unchanged - let the new pipeline handle scaling
        return diet_plan
    
    def _convert_day_plan_to_api_format(self, day_plan: DayPlan) -> Dict:
        """Convert DayPlan to API format"""
        daily_nutrition = day_plan.daily_totals
        
        return {
            "plan_type": "daily",
            "date": day_plan.date,
            "day_name": datetime.fromisoformat(day_plan.date).strftime("%A"),
            "meals": [
                {
                    "type": meal.meal_type,
                    "name": meal.name,
                    "ingredients": [
                        {
                            "name": ing.name,
                            "quantity": ing.quantity,
                            "unit": ing.unit,
                            "nutrition": {
                                "calories": round(ing.nutrition.calories, 1),
                                "protein": round(ing.nutrition.protein, 1),
                            } if ing.nutrition else {"calories": 0.0, "protein": 0.0}
                        } for ing in meal.ingredients
                    ],
                    "instructions": meal.instructions,
                    "nutrition": self._get_meal_nutrition_for_api(meal)
                } for meal in day_plan.meals
            ],
            "daily_totals": {
                "calories": round(daily_nutrition.calories, 1),
                "protein": round(daily_nutrition.protein, 1),
                "carbohydrates": round(daily_nutrition.carbohydrates, 1),
                "fat": round(daily_nutrition.fat, 1),
                "fiber": round(daily_nutrition.fiber, 1),
                "sodium": round(daily_nutrition.sodium, 1)
            }
        }
    
    def _get_meal_nutrition_for_api(self, meal) -> Dict:
        """Get meal nutrition using snapshot fallback for API safety"""
        # Use snapshot if available, fallback to live calculation
        nutrition = getattr(meal, "_nutrition_snapshot", meal.nutrition)
        
        # Add debug logging
        logger.debug(
            "[API_CONVERSION] meal=%s snapshot_cal=%s live_cal=%s",
            meal.name,
            getattr(meal, "_nutrition_snapshot", None).calories if hasattr(meal, "_nutrition_snapshot") else None,
            meal.nutrition.calories
        )
        
        return {
            "calories": round(nutrition.calories, 1),
            "protein": round(nutrition.protein, 1),
            "carbohydrates": round(nutrition.carbohydrates, 1),
            "fat": round(nutrition.fat, 1),
            "fiber": round(nutrition.fiber, 1),
            "sodium": round(nutrition.sodium, 1)
        }
    
    def _convert_weekly_plan_to_api_format(self, days: List[DayPlan]) -> Dict:
        """Convert weekly DayPlan list to API format"""
        api_days = []
        weekly_totals = {"calories": 0, "protein": 0, "carbohydrates": 0, "fat": 0, "fiber": 0, "sodium": 0}
        
        for day_plan in days:
            api_day = self._convert_day_plan_to_api_format(day_plan)
            api_days.append(api_day)
            
            # Add to weekly totals
            daily_totals = api_day["daily_totals"]
            for key in weekly_totals:
                weekly_totals[key] += daily_totals[key]
        
        return {
            "plan_type": "weekly",
            "start_date": days[0].date if days else "2024-01-01",
            "days": api_days,
            "weekly_totals": {k: round(v, 1) for k, v in weekly_totals.items()}
        }
    
    async def _repair_json_formatting(self, malformed_json: str, request_id: str) -> str:
        """
        Single-shot JSON repair - NO LOOPS, NO CONTENT CHANGES
        
        Args:
            malformed_json: The malformed JSON from LLM
            request_id: Request ID for logging
            
        Returns:
            Repaired JSON string
        """
        repair_prompt = f"""Fix this JSON formatting.
Do NOT change content.
Output valid JSON only.

{malformed_json}"""

        # Use provider manager for repair call with low temperature
        system_prompt = "You are a JSON formatter. Fix formatting only. Do not change content."
        
        retry_result = await self.provider_manager.generate_with_retry(
            system_prompt=system_prompt,
            user_prompt=repair_prompt,
            preferred_provider=settings.ai.ai_provider if hasattr(settings.ai, 'ai_provider') else None,
            temperature=0.1  # Very low temperature for formatting
        )
        
        if not retry_result.success:
            raise AIServiceValidationError(f"JSON repair failed: {retry_result.failure_reason}")
        
        return retry_result.content.strip()
    
    async def _generate_mock_fallback_plan(self, health_context_json: Dict, plan_type: str, target_date: Optional[str]) -> Dict:
        """Generate mock fallback plan when LLM fails"""
        mock_provider = MockAIProvider()
        mock_response, _ = await mock_provider.generate_completion("", f"Generate {plan_type} plan")
        return json.loads(mock_response)
    
    def _log_monitoring_data(self, request_id: str, user_id: Optional[UUID], plan_type: str, success: bool, error_message: Optional[str], start_time: float):
        """Log monitoring data if monitoring is enabled"""
        if not hasattr(self, '_last_usage_data') and not hasattr(self, '_last_retry_result'):
            return
        
        try:
            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)
            
            from app.services.ai_monitoring import AIUsageMetrics
            
            # Get usage data from retry result if available
            if hasattr(self, '_last_retry_result') and self._last_retry_result:
                retry_result = self._last_retry_result
                usage = retry_result.usage_data or {}
                final_provider = retry_result.final_provider or "unknown"
                total_attempts = len(retry_result.attempts) if retry_result.attempts else 1
            else:
                usage = getattr(self, '_last_usage_data', {})
                final_provider = "unknown"
                total_attempts = 1
            
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)
            total_tokens = prompt_tokens + completion_tokens
            
            cost = self._monitoring_service.calculate_cost(
                model=final_provider,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens
            )
            
            metrics = AIUsageMetrics(
                request_id=request_id,
                user_id=user_id,
                model=final_provider,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost_usd=cost,
                response_time_ms=response_time_ms,
                request_type=f"generate_{plan_type}_plan",
                success=success,
                error_message=error_message,
                timestamp=datetime.utcnow()
            )
            
            # Add retry-specific metadata
            if hasattr(self, '_last_retry_result') and self._last_retry_result:
                metrics.metadata = {
                    "total_attempts": total_attempts,
                    "final_provider": final_provider,
                    "retry_time_seconds": self._last_retry_result.total_time_seconds
                }
            
            self._monitoring_service.log_ai_request(metrics)
            
        except Exception as monitoring_error:
            logger.warning(f"Failed to log AI monitoring data: {monitoring_error}")
    
    def _parse_and_validate_response(
        self,
        response_content: str,
        plan_type: str
    ) -> Dict[str, Any]:
        """
        Parse and validate AI response.
        
        Args:
            response_content: Raw AI response content
            plan_type: Expected plan type
        
        Returns:
            Validated plan data dictionary
            
        Raises:
            AIServiceValidationError: If validation fails
        """
        try:
            # Clean the response content
            cleaned_content = response_content.strip()
            
            # Try to extract JSON if it's embedded in text
            if not cleaned_content.startswith('{'):
                # Look for JSON block in the response
                import re
                json_match = re.search(r'\{.*\}', cleaned_content, re.DOTALL)
                if json_match:
                    cleaned_content = json_match.group(0)
                else:
                    raise AIServiceValidationError("No JSON found in AI response")
            
            # Parse JSON response
            plan_data = json.loads(cleaned_content)
            
            # Validate basic structure
            if not isinstance(plan_data, dict):
                raise AIServiceValidationError("Response must be a JSON object")
            
            if plan_data.get("plan_type") != plan_type:
                raise AIServiceValidationError(f"Plan type mismatch: expected {plan_type}, got {plan_data.get('plan_type')}")
            
            # Validate plan structure based on type
            if plan_type == "weekly":
                self._validate_weekly_plan(plan_data)
            elif plan_type == "daily":
                self._validate_daily_plan(plan_data)
            else:
                raise AIServiceValidationError(f"Unknown plan type: {plan_type}")
            
            return plan_data
            
        except json.JSONDecodeError as e:
            # Log the problematic response for debugging (show more context around the error)
            error_pos = getattr(e, 'pos', 0)
            start_pos = max(0, error_pos - 100)
            end_pos = min(len(response_content), error_pos + 100)
            context = response_content[start_pos:end_pos]
            logger.error(f"JSON parsing failed at position {error_pos}. Context: ...{context}...")
            logger.error(f"Full response length: {len(response_content)} characters")
            
            # Try multiple JSON fixing strategies
            try:
                # Strategy 1: Remove trailing commas before closing brackets/braces
                import re
                fixed_content = re.sub(r',(\s*[}\]])', r'\1', cleaned_content)
                
                # Strategy 2: Try to find the last complete JSON object if truncated
                if not fixed_content.endswith('}'):
                    # Find the last complete object by counting braces
                    brace_count = 0
                    last_complete_pos = -1
                    
                    for i, char in enumerate(fixed_content):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                last_complete_pos = i + 1
                    
                    if last_complete_pos > 0:
                        fixed_content = fixed_content[:last_complete_pos]
                        logger.info(f"Truncated response to last complete JSON object at position {last_complete_pos}")
                
                # Strategy 3: Fix common JSON issues
                fixed_content = re.sub(r',(\s*[}\]])', r'\1', fixed_content)  # Remove trailing commas
                fixed_content = re.sub(r'([}\]])(\s*)([{\[])', r'\1,\2\3', fixed_content)  # Add missing commas between objects
                
                plan_data = json.loads(fixed_content)
                logger.info("Successfully parsed JSON after applying fixes")
                
                # Still validate the fixed data
                if not isinstance(plan_data, dict):
                    raise AIServiceValidationError("Response must be a JSON object")
                
                if plan_data.get("plan_type") != plan_type:
                    raise AIServiceValidationError(f"Plan type mismatch: expected {plan_type}, got {plan_data.get('plan_type')}")
                
                # Validate plan structure based on type
                if plan_type == "weekly":
                    self._validate_weekly_plan(plan_data)
                elif plan_type == "daily":
                    self._validate_daily_plan(plan_data)
                
                return plan_data
                
            except Exception as fix_error:
                logger.error(f"Failed to fix JSON: {fix_error}")
                
                # For weekly plans, fall back to generating a mock plan if AI fails
                if plan_type == "weekly":
                    logger.warning("Weekly plan JSON parsing failed, falling back to mock data")
                    mock_provider = MockAIProvider()
                    # Generate mock data directly without async call
                    mock_data = mock_provider._generate_mock_weekly_plan()
                    return mock_data
                
                raise AIServiceValidationError(f"Invalid JSON format: {str(e)} at position {error_pos}")
                
        except Exception as e:
            logger.error(f"Response validation failed: {str(e)}")
            raise AIServiceValidationError(f"Response validation failed: {str(e)}")
    
    def _validate_weekly_plan(self, plan_data: Dict[str, Any]) -> None:
        """Validate weekly plan structure"""
        required_fields = ["plan_type", "start_date", "days", "weekly_totals"]
        for field in required_fields:
            if field not in plan_data:
                raise AIServiceValidationError(f"Missing required field: {field}")
        
        days = plan_data["days"]
        if not isinstance(days, list) or len(days) != 7:
            raise AIServiceValidationError("Weekly plan must contain exactly 7 days")
        
        # Validate each day and fix daily totals
        for day in days:
            self._validate_day_structure(day)
        
        # CRITICAL FIX: Recalculate weekly totals from corrected daily totals
        calculated_weekly_totals = self._calculate_weekly_totals_from_days(days)
        
        # Update weekly totals with correct calculations
        plan_data["weekly_totals"] = calculated_weekly_totals
        
        logger.info(f"Weekly plan validated and corrected. Total protein: {calculated_weekly_totals['protein']}g")
    
    def _calculate_weekly_totals_from_days(self, days: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate accurate weekly nutrition totals from daily totals.
        """
        totals = {
            "calories": 0.0,
            "protein": 0.0,
            "carbohydrates": 0.0,
            "fat": 0.0,
            "fiber": 0.0,
            "sodium": 0.0
        }
        
        for day in days:
            daily_totals = day.get("daily_totals", {})
            for key in totals:
                value = daily_totals.get(key, 0)
                if isinstance(value, (int, float)):
                    totals[key] += float(value)
        
        # Round to 1 decimal place for consistency
        return {k: round(v, 1) for k, v in totals.items()}
    
    def _validate_daily_plan(self, plan_data: Dict[str, Any]) -> None:
        """Validate daily plan structure"""
        required_fields = ["plan_type", "date", "day_name", "meals", "daily_totals"]
        for field in required_fields:
            if field not in plan_data:
                raise AIServiceValidationError(f"Missing required field: {field}")
        
        self._validate_day_structure(plan_data)
    
    def _validate_day_structure(self, day_data: Dict[str, Any]) -> None:
        """Validate day structure (used for both daily and weekly plans)"""
        required_fields = ["meals", "daily_totals"]
        for field in required_fields:
            if field not in day_data:
                raise AIServiceValidationError(f"Missing required day field: {field}")
        
        meals = day_data["meals"]
        if not isinstance(meals, list) or len(meals) == 0:
            raise AIServiceValidationError("Day must contain at least one meal")
        
        for meal in meals:
            self._validate_meal_structure(meal)
        
        # Validate daily totals structure
        daily_totals = day_data["daily_totals"]
        required_nutrition_fields = ["calories", "protein", "carbohydrates", "fat"]
        for field in required_nutrition_fields:
            if field not in daily_totals:
                raise AIServiceValidationError(f"Missing nutrition field in daily totals: {field}")
        
        # CRITICAL FIX: Recalculate daily totals from actual meal data
        # This fixes AI calculation errors where daily_totals don't match meal totals
        calculated_totals = self._calculate_daily_totals_from_meals(meals)
        
        # Check for significant discrepancies (>10% difference)
        original_protein = daily_totals.get("protein", 0)
        calculated_protein = calculated_totals["protein"]
        
        if abs(original_protein - calculated_protein) > max(original_protein * 0.1, 5):
            logger.warning(f"Daily totals protein mismatch detected: AI claimed {original_protein}g, actual {calculated_protein}g. Using calculated values.")
            
            # Update daily_totals with correct calculations
            day_data["daily_totals"] = calculated_totals
            
        # Validate protein meets minimum requirements (this should catch low-protein plans)
        if calculated_totals["protein"] < 60:  # Minimum reasonable protein for muscle-building focus
            logger.error(f"Critically low protein detected: {calculated_totals['protein']}g. This plan is inadequate for muscle building.")
            raise AIServiceValidationError(f"Plan contains insufficient protein: {calculated_totals['protein']}g (minimum 60g required for muscle-building focus)")
        
        # Validate individual meals have adequate protein (20-40g per meal target)
        for meal in meals:
            meal_protein = meal.get("nutrition", {}).get("protein", 0)
            if meal_protein < 15:  # Minimum 15g per meal
                logger.warning(f"Low protein meal detected: {meal.get('name', 'unknown')} has only {meal_protein}g protein")
    
    def _calculate_daily_totals_from_meals(self, meals: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate accurate daily nutrition totals from individual meals.
        
        This method recalculates totals from actual meal data to fix AI calculation errors.
        """
        totals = {
            "calories": 0.0,
            "protein": 0.0,
            "carbohydrates": 0.0,
            "fat": 0.0,
            "fiber": 0.0,
            "sodium": 0.0
        }
        
        for meal in meals:
            nutrition = meal.get("nutrition", {})
            for key in totals:
                # Handle both integer and float values, default to 0 if missing
                value = nutrition.get(key, 0)
                if isinstance(value, (int, float)):
                    totals[key] += float(value)
                else:
                    logger.warning(f"Invalid nutrition value for {key} in meal {meal.get('name', 'unknown')}: {value}")
        
        # Round to 1 decimal place for consistency
        return {k: round(v, 1) for k, v in totals.items()}
    
    def _validate_meal_structure(self, meal_data: Dict[str, Any]) -> None:
        """Validate meal structure"""
        required_fields = ["type", "name", "ingredients", "instructions", "nutrition"]
        for field in required_fields:
            if field not in meal_data:
                raise AIServiceValidationError(f"Missing required meal field: {field}")
        
        # Validate ingredients
        ingredients = meal_data["ingredients"]
        if not isinstance(ingredients, list) or len(ingredients) == 0:
            raise AIServiceValidationError("Meal must contain at least one ingredient")
        
        for ingredient in ingredients:
            required_ingredient_fields = ["name", "quantity", "unit"]
            for field in required_ingredient_fields:
                if field not in ingredient:
                    raise AIServiceValidationError(f"Missing ingredient field: {field}")
        
        # Validate nutrition
        nutrition = meal_data["nutrition"]
        required_nutrition_fields = ["calories", "protein", "carbohydrates", "fat"]
        for field in required_nutrition_fields:
            if field not in nutrition:
                raise AIServiceValidationError(f"Missing nutrition field in meal: {field}")


# Global AI service instance - lazy initialization
_ai_service_instance = None

def get_ai_service(db_session=None) -> DietPlanAI:
    """Get AI service instance with optional monitoring"""
    # Always create a new instance when db_session is provided for monitoring
    if db_session:
        return DietPlanAI(db_session=db_session)
    
    # Use singleton pattern for instances without monitoring
    global _ai_service_instance
    if _ai_service_instance is None:
        _ai_service_instance = DietPlanAI()
    return _ai_service_instance