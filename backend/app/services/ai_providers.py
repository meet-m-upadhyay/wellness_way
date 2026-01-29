"""
AI provider implementations for diet plan generation
"""

import json
import logging
import asyncio
import aiohttp
from typing import Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
from datetime import datetime
import random

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    @abstractmethod
    async def generate_completion(
        self, 
        system_prompt: str, 
        user_prompt: str,
        temperature: Optional[float] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate completion using the AI provider"""
        pass


class MockAIProvider(AIProvider):
    """Mock AI provider for testing without API costs"""
    
    async def generate_completion(
        self, 
        system_prompt: str, 
        user_prompt: str,
        temperature: Optional[float] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate a realistic mock diet plan"""
        
        # Simulate API delay
        await asyncio.sleep(1)
        
        # Determine plan type from prompt
        plan_type = "daily" if "daily" in user_prompt.lower() else "weekly"
        
        if plan_type == "daily":
            mock_plan = self._generate_mock_daily_plan()
        else:
            mock_plan = self._generate_mock_weekly_plan()
        
        usage_data = {
            "prompt_tokens": len(user_prompt.split()),
            "completion_tokens": len(json.dumps(mock_plan).split()),
            "total_tokens": len(user_prompt.split()) + len(json.dumps(mock_plan).split())
        }
        
        return json.dumps(mock_plan, indent=2), usage_data
    
    def _generate_mock_daily_plan(self) -> Dict[str, Any]:
        """Generate a mock daily plan with NO NUTRITION DATA (contract compliant)"""
        return {
            "plan_type": "daily",
            "date": "2024-01-15",
            "day_name": "Monday",
            "meals": [
                {
                    "type": "breakfast",
                    "name": "High-Protein Greek Yogurt Power Bowl",
                    "ingredients": [
                        {"name": "Greek yogurt (plain)", "quantity": 200, "unit": "g"},
                        {"name": "protein powder (vanilla)", "quantity": 30, "unit": "g"},
                        {"name": "mixed berries", "quantity": 100, "unit": "g"},
                        {"name": "almonds (sliced)", "quantity": 20, "unit": "g"},
                        {"name": "chia seeds", "quantity": 10, "unit": "g"},
                        {"name": "honey", "quantity": 15, "unit": "g"}
                    ],
                    "instructions": "1. Mix Greek yogurt with protein powder until smooth\n2. Top with mixed berries, sliced almonds, and chia seeds\n3. Drizzle with honey and mix gently\n4. Let sit 5 minutes for chia seeds to expand"
                },
                {
                    "type": "lunch",
                    "name": "Protein-Packed Lentil and Quinoa Buddha Bowl",
                    "ingredients": [
                        {"name": "cooked red lentils", "quantity": 150, "unit": "g"},
                        {"name": "cooked quinoa", "quantity": 80, "unit": "g"},
                        {"name": "roasted chickpeas", "quantity": 60, "unit": "g"},
                        {"name": "spinach (fresh)", "quantity": 100, "unit": "g"},
                        {"name": "avocado", "quantity": 80, "unit": "g"},
                        {"name": "tahini", "quantity": 20, "unit": "g"},
                        {"name": "lemon juice", "quantity": 15, "unit": "ml"}
                    ],
                    "instructions": "1. Layer spinach in bowl as base\n2. Add warm lentils and quinoa\n3. Top with roasted chickpeas and sliced avocado\n4. Whisk tahini with lemon juice and drizzle over bowl\n5. Season with salt and pepper to taste"
                },
                {
                    "type": "dinner",
                    "name": "Herb-Crusted Baked Tofu with Sweet Potato and Hemp Seeds",
                    "ingredients": [
                        {"name": "extra-firm tofu", "quantity": 200, "unit": "g"},
                        {"name": "roasted sweet potato", "quantity": 150, "unit": "g"},
                        {"name": "steamed broccoli", "quantity": 150, "unit": "g"},
                        {"name": "hemp seeds", "quantity": 20, "unit": "g"},
                        {"name": "nutritional yeast", "quantity": 15, "unit": "g"},
                        {"name": "olive oil", "quantity": 10, "unit": "ml"},
                        {"name": "mixed herbs (dried)", "quantity": 5, "unit": "g"}
                    ],
                    "instructions": "1. Press tofu and cut into cubes, marinate with herbs and olive oil\n2. Bake tofu at 400°F for 25 minutes until golden\n3. Roast sweet potato cubes until tender\n4. Steam broccoli until bright green\n5. Serve tofu over sweet potato and broccoli, sprinkle with hemp seeds and nutritional yeast"
                }
            ]
        }
    
    def _generate_mock_weekly_plan(self) -> Dict[str, Any]:
        """Generate a mock weekly plan with NO NUTRITION DATA (contract compliant)"""
        days = []
        
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        for i, day_name in enumerate(day_names):
            # Generate varied daily plans without nutrition data
            daily_plan = self._generate_varied_daily_plan_no_nutrition(i, day_name)
            days.append(daily_plan)
        
        return {
            "plan_type": "weekly",
            "start_date": "2024-01-15",
            "days": days
        }
    
    def _generate_varied_daily_plan(self, day_index: int, day_name: str) -> Dict[str, Any]:
        """Generate varied daily plans for different days with high protein and strict vegetarian compliance"""
        
        # Different high-protein meal options for variety - ALL VEGETARIAN
        breakfast_options = [
            {
                "name": "High-Protein Greek Yogurt Power Bowl",
                "calories": 520, "protein": 42, "carbs": 45, "fat": 18
            },
            {
                "name": "Protein Smoothie Bowl with Nuts and Seeds",
                "calories": 480, "protein": 38, "carbs": 40, "fat": 22
            },
            {
                "name": "Scrambled Tofu with Nutritional Yeast and Spinach",
                "calories": 450, "protein": 35, "carbs": 25, "fat": 28
            },
            {
                "name": "High-Protein Oatmeal with Protein Powder and Almonds",
                "calories": 500, "protein": 40, "carbs": 50, "fat": 18
            },
            {
                "name": "Cottage Cheese Pancakes with Hemp Seeds",
                "calories": 460, "protein": 36, "carbs": 35, "fat": 20
            },
            {
                "name": "Protein-Rich Chia Pudding with Almond Butter",
                "calories": 490, "protein": 32, "carbs": 38, "fat": 26
            },
            {
                "name": "Quinoa Breakfast Bowl with Greek Yogurt",
                "calories": 510, "protein": 38, "carbs": 48, "fat": 20
            }
        ]
        
        lunch_options = [
            {
                "name": "Protein-Packed Lentil and Quinoa Buddha Bowl",
                "calories": 580, "protein": 32, "carbs": 65, "fat": 22
            },
            {
                "name": "Chickpea and Tempeh Power Salad",
                "calories": 550, "protein": 35, "carbs": 45, "fat": 28
            },
            {
                "name": "Black Bean and Hemp Seed Wrap",
                "calories": 520, "protein": 30, "carbs": 55, "fat": 24
            },
            {
                "name": "Tofu and Edamame Stir-fry with Brown Rice",
                "calories": 560, "protein": 38, "carbs": 50, "fat": 26
            },
            {
                "name": "High-Protein Hummus and Veggie Bowl",
                "calories": 540, "protein": 28, "carbs": 60, "fat": 22
            },
            {
                "name": "Lentil and Cottage Cheese Stuffed Bell Peppers",
                "calories": 500, "protein": 34, "carbs": 45, "fat": 20
            },
            {
                "name": "Protein-Rich Three-Bean Chili with Quinoa",
                "calories": 570, "protein": 36, "carbs": 68, "fat": 18
            }
        ]
        
        dinner_options = [
            {
                "name": "Herb-Crusted Baked Tofu with Sweet Potato and Hemp Seeds",
                "calories": 620, "protein": 38, "carbs": 55, "fat": 28
            },
            {
                "name": "Tempeh and Lentil Curry with Coconut and Cashews",
                "calories": 650, "protein": 42, "carbs": 50, "fat": 32
            },
            {
                "name": "Seitan Stir-fry with Peanut Sauce and Vegetables",
                "calories": 580, "protein": 45, "carbs": 40, "fat": 26
            },
            {
                "name": "High-Protein Bean and Quinoa Stuffed Portobello",
                "calories": 560, "protein": 35, "carbs": 55, "fat": 24
            },
            {
                "name": "Baked Chickpea and Spinach Protein Patties",
                "calories": 540, "protein": 32, "carbs": 50, "fat": 22
            },
            {
                "name": "Protein-Rich Lentil and Walnut Bolognese",
                "calories": 600, "protein": 40, "carbs": 60, "fat": 26
            },
            {
                "name": "Marinated Tofu Steaks with Protein-Rich Sides",
                "calories": 590, "protein": 44, "carbs": 45, "fat": 28
            }
        ]
        
        # Select meals based on day to ensure variety across the week
        breakfast = breakfast_options[day_index % len(breakfast_options)]
        lunch = lunch_options[day_index % len(lunch_options)]
        dinner = dinner_options[day_index % len(dinner_options)]
        
        # Calculate totals
        total_calories = breakfast["calories"] + lunch["calories"] + dinner["calories"]
        total_protein = breakfast["protein"] + lunch["protein"] + dinner["protein"]
        total_carbs = breakfast["carbs"] + lunch["carbs"] + dinner["carbs"]
        total_fat = breakfast["fat"] + lunch["fat"] + dinner["fat"]
        
        return {
            "date": f"2024-01-{15 + day_index:02d}",
            "day_name": day_name,
            "meals": [
                self._create_mock_meal("breakfast", breakfast["name"], breakfast),
                self._create_mock_meal("lunch", lunch["name"], lunch),
                self._create_mock_meal("dinner", dinner["name"], dinner)
            ],
            "daily_totals": {
                "calories": total_calories,
                "protein": total_protein,
                "carbohydrates": total_carbs,
                "fat": total_fat,
                "fiber": random.randint(35, 45),
                "sodium": random.randint(500, 700)
            }
        }
    
    def _generate_varied_daily_plan_no_nutrition(self, day_index: int, day_name: str) -> Dict[str, Any]:
        """Generate varied daily plans for different days with NO NUTRITION DATA (contract compliant)"""
        
        # Different high-protein meal options for variety - ALL VEGETARIAN, NO NUTRITION DATA
        breakfast_options = [
            "High-Protein Greek Yogurt Power Bowl",
            "Protein Smoothie Bowl with Nuts and Seeds",
            "Scrambled Tofu with Nutritional Yeast and Spinach",
            "High-Protein Oatmeal with Protein Powder and Almonds",
            "Cottage Cheese Pancakes with Hemp Seeds",
            "Protein-Rich Chia Pudding with Almond Butter",
            "Quinoa Breakfast Bowl with Greek Yogurt"
        ]
        
        lunch_options = [
            "Protein-Packed Lentil and Quinoa Buddha Bowl",
            "Chickpea and Tempeh Power Salad",
            "Black Bean and Hemp Seed Wrap",
            "Tofu and Edamame Stir-fry with Brown Rice",
            "High-Protein Hummus and Veggie Bowl",
            "Lentil and Cottage Cheese Stuffed Bell Peppers",
            "Protein-Rich Three-Bean Chili with Quinoa"
        ]
        
        dinner_options = [
            "Herb-Crusted Baked Tofu with Sweet Potato and Hemp Seeds",
            "Tempeh and Lentil Curry with Coconut and Cashews",
            "Seitan Stir-fry with Peanut Sauce and Vegetables",
            "High-Protein Bean and Quinoa Stuffed Portobello",
            "Baked Chickpea and Spinach Protein Patties",
            "Protein-Rich Lentil and Walnut Bolognese",
            "Marinated Tofu Steaks with Protein-Rich Sides"
        ]
        
        # Select meals based on day to ensure variety across the week
        breakfast = breakfast_options[day_index % len(breakfast_options)]
        lunch = lunch_options[day_index % len(lunch_options)]
        dinner = dinner_options[day_index % len(dinner_options)]
        
        return {
            "date": f"2024-01-{15 + day_index:02d}",
            "day_name": day_name,
            "meals": [
                self._create_mock_meal_no_nutrition("breakfast", breakfast),
                self._create_mock_meal_no_nutrition("lunch", lunch),
                self._create_mock_meal_no_nutrition("dinner", dinner)
            ]
        }
    
    def _create_mock_meal_no_nutrition(self, meal_type: str, name: str) -> Dict[str, Any]:
        """Create a mock meal with NO NUTRITION DATA (contract compliant)"""
        
        # High-protein vegetarian ingredient lists based on meal type
        ingredients_map = {
            "breakfast": [
                {"name": "greek yogurt (plain)", "quantity": 200, "unit": "g"},
                {"name": "protein powder (vanilla)", "quantity": 30, "unit": "g"},
                {"name": "mixed berries", "quantity": 100, "unit": "g"},
                {"name": "almonds (sliced)", "quantity": 20, "unit": "g"},
                {"name": "chia seeds", "quantity": 10, "unit": "g"}
            ],
            "lunch": [
                {"name": "lentils (red, cooked)", "quantity": 150, "unit": "g"},
                {"name": "cooked quinoa", "quantity": 80, "unit": "g"},
                {"name": "roasted chickpeas", "quantity": 60, "unit": "g"},
                {"name": "tahini", "quantity": 20, "unit": "g"},
                {"name": "hemp seeds", "quantity": 15, "unit": "g"}
            ],
            "dinner": [
                {"name": "tofu (extra-firm)", "quantity": 200, "unit": "g"},
                {"name": "tempeh", "quantity": 100, "unit": "g"},
                {"name": "nutritional yeast", "quantity": 15, "unit": "g"},
                {"name": "mixed vegetables", "quantity": 200, "unit": "g"},
                {"name": "olive oil", "quantity": 10, "unit": "ml"}
            ]
        }
        
        return {
            "type": meal_type,
            "name": name,
            "ingredients": ingredients_map.get(meal_type, []),
            "instructions": f"1. Prepare all high-protein vegetarian ingredients\n2. Focus on protein-rich preparation methods\n3. Combine with vegetables and healthy fats\n4. Ensure complete amino acid profile\n5. Enjoy your muscle-building {name}!"
        }


class GroqAIProvider(AIProvider):
    """Groq AI provider - Fast and free alternative to OpenAI"""
    
    def __init__(self):
        self.api_key = settings.get_groq_api_key()
        self.model = settings.ai.groq_model
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        
        if not self.api_key:
            raise ValueError("Groq API key not configured")
    
    async def generate_completion(
        self, 
        system_prompt: str, 
        user_prompt: str,
        temperature: Optional[float] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate completion using Groq API with enhanced rate limit handling"""
        
        logger.info(f"GroqAIProvider: Making API call with model {self.model}")
        logger.info(f"GroqAIProvider: API key configured: {bool(self.api_key)}")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Use provided temperature or default, with special handling for diet generation
        effective_temperature = temperature if temperature is not None else settings.ai.openai_temperature
        if "diet" in user_prompt.lower() and temperature is None:
            effective_temperature = 0.2  # Lower creativity for structured output
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 4000 if "weekly" in user_prompt.lower() else settings.ai.openai_max_tokens,
            "temperature": effective_temperature
        }
        
        logger.info(f"GroqAIProvider: Sending request to {self.base_url}")
        
        # Enhanced retry logic for rate limits
        max_retries = 5  # Increased retries
        base_delay = 2.0  # Longer base delay
        
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.base_url, 
                        headers=headers, 
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=settings.ai.openai_timeout)
                    ) as response:
                        logger.info(f"GroqAIProvider: Response status: {response.status}")
                        
                        if response.status == 200:
                            result = await response.json()
                            content = result["choices"][0]["message"]["content"]
                            usage_data = result.get("usage", {})
                            
                            logger.info(f"GroqAIProvider: Successfully generated response, tokens used: {usage_data}")
                            return content.strip(), usage_data
                        
                        elif response.status == 429:  # Rate limit
                            error_text = await response.text()
                            logger.warning(f"GroqAIProvider: Rate limit hit (attempt {attempt + 1}/{max_retries}): {error_text}")
                            
                            # Parse retry-after from error message if available
                            import re
                            retry_match = re.search(r'try again in (\d+\.?\d*)s', error_text)
                            if retry_match:
                                retry_after = float(retry_match.group(1)) + 1.0  # Add buffer
                            else:
                                retry_after = base_delay * (2 ** attempt)  # Exponential backoff
                            
                            # Cap maximum wait time
                            retry_after = min(retry_after, 30.0)
                            
                            if attempt < max_retries - 1:
                                logger.info(f"GroqAIProvider: Waiting {retry_after:.1f}s before retry...")
                                await asyncio.sleep(retry_after)
                                continue
                            else:
                                logger.error(f"GroqAIProvider: Rate limit exceeded after {max_retries} attempts")
                                logger.warning("GroqAIProvider: Falling back to mock data due to persistent rate limits")
                                mock_provider = MockAIProvider()
                                return await mock_provider.generate_completion(system_prompt, user_prompt)
                        
                        else:
                            error_text = await response.text()
                            logger.error(f"GroqAIProvider: API error: {response.status} - {error_text}")
                            
                            # For non-rate-limit errors, try a few times then fall back
                            if attempt < 2:  # Only retry twice for other errors
                                await asyncio.sleep(base_delay)
                                continue
                            else:
                                logger.warning("GroqAIProvider: Falling back to mock data due to API errors")
                                mock_provider = MockAIProvider()
                                return await mock_provider.generate_completion(system_prompt, user_prompt)
            
            except asyncio.TimeoutError:
                logger.error(f"GroqAIProvider: Request timeout (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(base_delay * (2 ** attempt))
                    continue
                else:
                    logger.warning("GroqAIProvider: Falling back to mock data due to timeouts")
                    mock_provider = MockAIProvider()
                    return await mock_provider.generate_completion(system_prompt, user_prompt)
            
            except Exception as e:
                if "rate limit" in str(e).lower():
                    # Re-raise rate limit errors to be handled above
                    raise
                logger.error(f"GroqAIProvider: Unexpected error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(base_delay * (2 ** attempt))
                    continue
                else:
                    logger.warning("GroqAIProvider: Falling back to mock data due to unexpected errors")
                    mock_provider = MockAIProvider()
                    return await mock_provider.generate_completion(system_prompt, user_prompt)
        
        # This should never be reached, but just in case
        logger.warning("GroqAIProvider: Exhausted all options, falling back to mock data")
        mock_provider = MockAIProvider()
        return await mock_provider.generate_completion(system_prompt, user_prompt)


class OllamaAIProvider(AIProvider):
    """Ollama local AI provider - Completely free, runs locally"""
    
    def __init__(self):
        self.base_url = settings.ai.ollama_base_url
        self.model = settings.ai.ollama_model
    
    async def generate_completion(
        self, 
        system_prompt: str, 
        user_prompt: str
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate completion using local Ollama"""
        
        # Combine system and user prompts for Ollama
        combined_prompt = f"System: {system_prompt}\n\nUser: {user_prompt}\n\nAssistant:"
        
        payload = {
            "model": self.model,
            "prompt": combined_prompt,
            "stream": False,
            "options": {
                "temperature": settings.ai.openai_temperature,
                "num_predict": settings.ai.openai_max_tokens
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=settings.ai.openai_timeout)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Ollama API error: {response.status} - {error_text}")
                
                result = await response.json()
                content = result.get("response", "")
                
                # Mock usage data for Ollama
                usage_data = {
                    "prompt_tokens": len(combined_prompt.split()),
                    "completion_tokens": len(content.split()),
                    "total_tokens": len(combined_prompt.split()) + len(content.split())
                }
                
                return content.strip(), usage_data


class HuggingFaceAIProvider(AIProvider):
    """Hugging Face AI provider - Using new Inference Providers API"""
    
    def __init__(self):
        self.api_key = settings.get_huggingface_api_key()
        # Use a model that works with the new Inference Providers API
        self.model = "meta-llama/Llama-3.2-1B-Instruct"  # Working model
        self.base_url = "https://router.huggingface.co/v1/chat/completions"
        
        if not self.api_key:
            raise ValueError("Hugging Face API key not configured")
    
    async def generate_completion(
        self, 
        system_prompt: str, 
        user_prompt: str,
        temperature: Optional[float] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate completion using new HuggingFace Inference Providers API"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Use provided temperature or default, with special handling for diet generation
        effective_temperature = temperature if temperature is not None else settings.ai.openai_temperature
        if "diet" in user_prompt.lower() and temperature is None:
            effective_temperature = 0.2  # Lower creativity for structured output
        
        # Use the new OpenAI-compatible chat completions format
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": min(settings.ai.openai_max_tokens, 1000),  # Limit for free tier
            "temperature": effective_temperature,
            "stream": False
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)  # Longer timeout for model loading
                ) as response:
                    response_text = await response.text()
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        # Extract content from OpenAI-compatible response
                        if "choices" in result and len(result["choices"]) > 0:
                            content = result["choices"][0]["message"]["content"]
                            usage_data = result.get("usage", {
                                "prompt_tokens": len(f"{system_prompt} {user_prompt}".split()),
                                "completion_tokens": len(content.split()),
                                "total_tokens": len(f"{system_prompt} {user_prompt}".split()) + len(content.split())
                            })
                            return content.strip(), usage_data
                        else:
                            raise Exception("Invalid response format from HuggingFace API")
                    
                    elif response.status == 503:
                        # Model is loading - this indicates the API key works
                        logger.info("HuggingFace model is loading (503) - API key is valid")
                        raise Exception("Model is loading, please try again in a few minutes (503)")
                    
                    elif response.status == 401:
                        logger.error("HuggingFace API authentication failed - invalid API key")
                        raise Exception("Invalid HuggingFace API key (401)")
                    
                    else:
                        logger.error(f"HuggingFace API error: {response.status} - {response_text}")
                        raise Exception(f"Hugging Face API error: {response.status} - {response_text}")
        
        except Exception as e:
            logger.error(f"HuggingFace API call failed: {e}")
            raise


def get_ai_provider() -> AIProvider:
    """Get the configured AI provider"""
    
    provider_name = settings.ai.ai_provider
    logger.info(f"get_ai_provider: Selecting provider '{provider_name}'")
    
    if provider_name == "openai":
        from app.services.ai_service import OpenAIClient
        logger.info("get_ai_provider: Creating OpenAIClient")
        return OpenAIClient()
    elif provider_name == "groq":
        logger.info("get_ai_provider: Creating GroqAIProvider")
        return GroqAIProvider()
    elif provider_name == "huggingface":
        logger.info("get_ai_provider: Creating HuggingFaceAIProvider")
        return HuggingFaceAIProvider()
    elif provider_name == "ollama":
        logger.info("get_ai_provider: Creating OllamaAIProvider")
        return OllamaAIProvider()
    elif provider_name == "mock":
        logger.info("get_ai_provider: Creating MockAIProvider")
        return MockAIProvider()
    else:
        logger.warning(f"Unknown AI provider: {provider_name}, falling back to mock")
        return MockAIProvider()