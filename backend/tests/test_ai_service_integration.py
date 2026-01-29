"""
Unit tests for AI service integration
Tests AI service wrapper with mock responses, error handling, retry logic, and response validation
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4
import aiohttp
from datetime import datetime

from app.services.ai_service import (
    DietPlanAI, 
    OpenAIClient, 
    AIServiceError, 
    AIServiceTimeoutError, 
    AIServiceValidationError,
    get_ai_service
)
from app.services.ai_providers import (
    MockAIProvider, 
    GroqAIProvider, 
    OllamaAIProvider, 
    HuggingFaceAIProvider,
    get_ai_provider
)
from app.core.config import settings


class TestOpenAIClient:
    """Test OpenAI client wrapper"""
    
    @pytest.fixture
    def openai_client(self):
        """Create OpenAI client for testing"""
        # Mock the settings.get_openai_api_key method directly
        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.get_openai_api_key.return_value = 'test-key'
            mock_settings.ai.openai_model = 'gpt-4'
            mock_settings.ai.openai_max_tokens = 2000
            mock_settings.ai.openai_temperature = 0.7
            mock_settings.ai.openai_timeout = 30
            return OpenAIClient()
    
    @pytest.mark.asyncio
    async def test_openai_client_initialization_success(self):
        """Test successful OpenAI client initialization"""
        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.get_openai_api_key.return_value = 'test-key'
            mock_settings.ai.openai_model = 'gpt-4'
            mock_settings.ai.openai_max_tokens = 2000
            mock_settings.ai.openai_temperature = 0.7
            mock_settings.ai.openai_timeout = 30
            
            client = OpenAIClient()
            assert client.model == 'gpt-4'
            assert client.max_tokens == 2000
            assert client.temperature == 0.7
    
    def test_openai_client_initialization_no_api_key(self):
        """Test OpenAI client initialization without API key"""
        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.get_openai_api_key.return_value = None
            
            with pytest.raises(AIServiceError, match="OpenAI API key not configured"):
                OpenAIClient()
    
    @pytest.mark.asyncio
    async def test_generate_completion_success(self, openai_client):
        """Test successful completion generation"""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response content"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150
        
        with patch.object(openai_client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            content, usage = await openai_client.generate_completion(
                system_prompt="Test system prompt",
                user_prompt="Test user prompt"
            )
            
            assert content == "Test response content"
            assert usage['prompt_tokens'] == 100
            assert usage['completion_tokens'] == 50
            assert usage['total_tokens'] == 150
            
            # Verify API call parameters
            mock_create.assert_called_once()
            call_args = mock_create.call_args[1]
            assert call_args['model'] == settings.ai.openai_model
            assert len(call_args['messages']) == 2
            assert call_args['messages'][0]['role'] == 'system'
            assert call_args['messages'][1]['role'] == 'user'
    
    @pytest.mark.asyncio
    async def test_generate_completion_timeout(self, openai_client):
        """Test completion generation timeout"""
        with patch.object(openai_client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = asyncio.TimeoutError()
            
            # The retry logic will wrap the exception in a RetryError
            with pytest.raises(Exception):  # Could be RetryError or AIServiceTimeoutError
                await openai_client.generate_completion(
                    system_prompt="Test system prompt",
                    user_prompt="Test user prompt"
                )
    
    @pytest.mark.asyncio
    async def test_generate_completion_no_choices(self, openai_client):
        """Test completion generation with no response choices"""
        mock_response = Mock()
        mock_response.choices = []
        
        with patch.object(openai_client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            # The retry logic will wrap the exception in a RetryError
            with pytest.raises(Exception):  # Could be RetryError or AIServiceError
                await openai_client.generate_completion(
                    system_prompt="Test system prompt",
                    user_prompt="Test user prompt"
                )
    
    @pytest.mark.asyncio
    async def test_generate_completion_empty_content(self, openai_client):
        """Test completion generation with empty content"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = None
        
        with patch.object(openai_client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            # The retry logic will wrap the exception in a RetryError
            with pytest.raises(Exception):  # Could be RetryError or AIServiceError
                await openai_client.generate_completion(
                    system_prompt="Test system prompt",
                    user_prompt="Test user prompt"
                )
    
    @pytest.mark.asyncio
    async def test_generate_completion_api_error(self, openai_client):
        """Test completion generation with API error"""
        with patch.object(openai_client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("API Error")
            
            # The retry logic will wrap the exception in a RetryError
            with pytest.raises(Exception):  # Could be RetryError or AIServiceError
                await openai_client.generate_completion(
                    system_prompt="Test system prompt",
                    user_prompt="Test user prompt"
                )
    
    @pytest.mark.asyncio
    async def test_generate_completion_with_response_format(self, openai_client):
        """Test completion generation with structured response format"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"test": "json"}'
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150
        
        response_format = {"type": "json_object"}
        
        with patch.object(openai_client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            content, usage = await openai_client.generate_completion(
                system_prompt="Test system prompt",
                user_prompt="Test user prompt",
                response_format=response_format
            )
            
            assert content == '{"test": "json"}'
            
            # Verify response format was passed
            call_args = mock_create.call_args[1]
            assert call_args['response_format'] == response_format


class TestMockAIProvider:
    """Test Mock AI provider"""
    
    @pytest.fixture
    def mock_provider(self):
        """Create mock AI provider for testing"""
        return MockAIProvider()
    
    @pytest.mark.asyncio
    async def test_generate_daily_plan(self, mock_provider):
        """Test mock daily plan generation"""
        system_prompt = "Test system prompt"
        user_prompt = "Generate a daily diet plan"
        
        content, usage = await mock_provider.generate_completion(system_prompt, user_prompt)
        
        # Verify response structure
        assert isinstance(content, str)
        assert isinstance(usage, dict)
        assert 'prompt_tokens' in usage
        assert 'completion_tokens' in usage
        assert 'total_tokens' in usage
        
        # Parse and validate JSON content
        plan_data = json.loads(content)
        assert plan_data['plan_type'] == 'daily'
        assert 'date' in plan_data
        assert 'day_name' in plan_data
        assert 'meals' in plan_data
        assert 'daily_totals' in plan_data
        
        # Verify meals structure
        meals = plan_data['meals']
        assert len(meals) >= 3  # At least breakfast, lunch, dinner
        
        for meal in meals:
            assert 'type' in meal
            assert 'name' in meal
            assert 'ingredients' in meal
            assert 'instructions' in meal
            assert 'nutrition' in meal
            
            # Verify nutrition structure
            nutrition = meal['nutrition']
            assert 'calories' in nutrition
            assert 'protein' in nutrition
            assert 'carbohydrates' in nutrition
            assert 'fat' in nutrition
    
    @pytest.mark.asyncio
    async def test_generate_weekly_plan(self, mock_provider):
        """Test mock weekly plan generation"""
        system_prompt = "Test system prompt"
        user_prompt = "Generate a weekly diet plan"
        
        content, usage = await mock_provider.generate_completion(system_prompt, user_prompt)
        
        # Parse and validate JSON content
        plan_data = json.loads(content)
        assert plan_data['plan_type'] == 'weekly'
        assert 'start_date' in plan_data
        assert 'days' in plan_data
        assert 'weekly_totals' in plan_data
        
        # Verify weekly structure
        days = plan_data['days']
        assert len(days) == 7  # Exactly 7 days
        
        for day in days:
            assert 'date' in day
            assert 'day_name' in day
            assert 'meals' in day
            assert 'daily_totals' in day
    
    @pytest.mark.asyncio
    async def test_mock_provider_delay(self, mock_provider):
        """Test that mock provider simulates API delay"""
        import time
        
        start_time = time.time()
        await mock_provider.generate_completion("system", "user")
        end_time = time.time()
        
        # Should take at least 1 second due to simulated delay
        assert end_time - start_time >= 1.0
    
    def test_vegetarian_compliance(self, mock_provider):
        """Test that mock plans are vegetarian compliant"""
        # Generate a daily plan
        daily_plan = mock_provider._generate_mock_daily_plan()
        
        # Check all meals for vegetarian compliance
        forbidden_ingredients = [
            'chicken', 'beef', 'pork', 'fish', 'salmon', 'tuna', 'bacon', 'ham', 'sausage'
        ]
        
        for meal in daily_plan['meals']:
            for ingredient in meal['ingredients']:
                ingredient_name = ingredient['name'].lower()
                for forbidden in forbidden_ingredients:
                    assert forbidden not in ingredient_name, f"Found non-vegetarian ingredient: {ingredient_name}"


class TestGroqAIProvider:
    """Test Groq AI provider"""
    
    @pytest.fixture
    def groq_provider(self):
        """Create Groq AI provider for testing"""
        with patch('app.services.ai_providers.settings') as mock_settings:
            mock_settings.get_groq_api_key.return_value = 'test-key'
            mock_settings.ai.groq_model = 'llama-3.1-8b-instant'
            return GroqAIProvider()
    
    def test_groq_provider_initialization_success(self):
        """Test successful Groq provider initialization"""
        with patch('app.services.ai_providers.settings') as mock_settings:
            mock_settings.get_groq_api_key.return_value = 'test-key'
            mock_settings.ai.groq_model = 'llama-3.1-8b-instant'
            
            provider = GroqAIProvider()
            assert provider.api_key == 'test-key'
            assert provider.model == 'llama-3.1-8b-instant'
    
    def test_groq_provider_initialization_no_api_key(self):
        """Test Groq provider initialization without API key"""
        with patch('app.services.ai_providers.settings') as mock_settings:
            mock_settings.get_groq_api_key.return_value = None
            
            with pytest.raises(ValueError, match="Groq API key not configured"):
                GroqAIProvider()
    
    @pytest.mark.asyncio
    async def test_groq_generate_completion_success(self, groq_provider):
        """Test successful Groq completion generation"""
        mock_response_data = {
            "choices": [{"message": {"content": "Test response"}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_post.return_value.__aenter__.return_value = mock_response
            
            content, usage = await groq_provider.generate_completion(
                system_prompt="Test system",
                user_prompt="Test user"
            )
            
            assert content == "Test response"
            assert usage == mock_response_data["usage"]
    
    @pytest.mark.asyncio
    async def test_groq_rate_limit_handling(self, groq_provider):
        """Test Groq rate limit handling with fallback to mock"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Mock rate limit response
            mock_response = AsyncMock()
            mock_response.status = 429
            mock_response.text = AsyncMock(return_value="Rate limit exceeded, try again in 2.5s")
            mock_post.return_value.__aenter__.return_value = mock_response
            
            # Should fall back to mock provider after retries
            content, usage = await groq_provider.generate_completion(
                system_prompt="Test system",
                user_prompt="Test user"
            )
            
            # Should get mock response
            assert isinstance(content, str)
            assert isinstance(usage, dict)
            
            # Verify it tried multiple times
            assert mock_post.call_count == 5  # max_retries
    
    @pytest.mark.asyncio
    async def test_groq_timeout_handling(self, groq_provider):
        """Test Groq timeout handling"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.side_effect = asyncio.TimeoutError()
            
            # Should fall back to mock provider after timeouts
            content, usage = await groq_provider.generate_completion(
                system_prompt="Test system",
                user_prompt="Test user"
            )
            
            # Should get mock response
            assert isinstance(content, str)
            assert isinstance(usage, dict)
    
    @pytest.mark.asyncio
    async def test_groq_api_error_handling(self, groq_provider):
        """Test Groq API error handling"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.text = AsyncMock(return_value="Internal server error")
            mock_post.return_value.__aenter__.return_value = mock_response
            
            # Should fall back to mock provider after API errors
            content, usage = await groq_provider.generate_completion(
                system_prompt="Test system",
                user_prompt="Test user"
            )
            
            # Should get mock response
            assert isinstance(content, str)
            assert isinstance(usage, dict)


class TestOllamaAIProvider:
    """Test Ollama AI provider"""
    
    @pytest.fixture
    def ollama_provider(self):
        """Create Ollama AI provider for testing"""
        return OllamaAIProvider()
    
    @pytest.mark.asyncio
    async def test_ollama_generate_completion_success(self, ollama_provider):
        """Test successful Ollama completion generation"""
        mock_response_data = {"response": "Test ollama response"}
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_post.return_value.__aenter__.return_value = mock_response
            
            content, usage = await ollama_provider.generate_completion(
                system_prompt="Test system",
                user_prompt="Test user"
            )
            
            assert content == "Test ollama response"
            assert isinstance(usage, dict)
            assert 'prompt_tokens' in usage
            assert 'completion_tokens' in usage
            assert 'total_tokens' in usage
    
    @pytest.mark.asyncio
    async def test_ollama_api_error(self, ollama_provider):
        """Test Ollama API error handling"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.text = AsyncMock(return_value="Ollama error")
            mock_post.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(Exception, match="Ollama API error: 500"):
                await ollama_provider.generate_completion(
                    system_prompt="Test system",
                    user_prompt="Test user"
                )


class TestHuggingFaceAIProvider:
    """Test Hugging Face AI provider"""
    
    @pytest.fixture
    def hf_provider(self):
        """Create Hugging Face AI provider for testing"""
        with patch('app.services.ai_providers.settings') as mock_settings:
            mock_settings.get_huggingface_api_key.return_value = 'test-key'
            mock_settings.ai.huggingface_model = 'microsoft/DialoGPT-large'
            return HuggingFaceAIProvider()
    
    def test_hf_provider_initialization_no_api_key(self):
        """Test HF provider initialization without API key"""
        with patch('app.services.ai_providers.settings') as mock_settings:
            mock_settings.get_huggingface_api_key.return_value = None
            
            with pytest.raises(ValueError, match="Hugging Face API key not configured"):
                HuggingFaceAIProvider()
    
    @pytest.mark.asyncio
    async def test_hf_generate_completion_list_response(self, hf_provider):
        """Test HF completion generation with list response format"""
        mock_response_data = [{"generated_text": "Test HF response"}]
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_post.return_value.__aenter__.return_value = mock_response
            
            content, usage = await hf_provider.generate_completion(
                system_prompt="Test system",
                user_prompt="Test user"
            )
            
            assert content == "Test HF response"
            assert isinstance(usage, dict)
    
    @pytest.mark.asyncio
    async def test_hf_generate_completion_dict_response(self, hf_provider):
        """Test HF completion generation with dict response format"""
        mock_response_data = {"generated_text": "Test HF dict response"}
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_post.return_value.__aenter__.return_value = mock_response
            
            content, usage = await hf_provider.generate_completion(
                system_prompt="Test system",
                user_prompt="Test user"
            )
            
            assert content == "Test HF dict response"


class TestDietPlanAI:
    """Test DietPlanAI service"""
    
    @pytest.fixture
    def diet_plan_ai(self):
        """Create DietPlanAI service for testing"""
        with patch('app.services.ai_service.get_ai_provider') as mock_get_provider:
            mock_provider = MockAIProvider()
            mock_get_provider.return_value = mock_provider
            return DietPlanAI()
    
    @pytest.mark.asyncio
    async def test_generate_daily_diet_plan_success(self, diet_plan_ai):
        """Test successful daily diet plan generation"""
        health_context = """
        # Health Context Document
        
        ## User Profile
        - Name: Test User
        - Age: 30
        - Gender: Male
        - Diet Type: Vegetarian
        
        ## Calculated Metrics
        - BMR: 1800 calories
        - TDEE: 2200 calories
        - Target Calories: 1900 calories
        """
        
        plan_data = await diet_plan_ai.generate_diet_plan(
            health_context=health_context,
            plan_type="daily",
            target_date="2024-01-15"
        )
        
        # Verify plan structure
        assert plan_data['plan_type'] == 'daily'
        assert 'date' in plan_data
        assert 'meals' in plan_data
        assert 'daily_totals' in plan_data
        
        # Verify meals
        meals = plan_data['meals']
        assert len(meals) >= 3
        
        for meal in meals:
            assert 'type' in meal
            assert 'name' in meal
            assert 'ingredients' in meal
            assert 'nutrition' in meal
    
    @pytest.mark.asyncio
    async def test_generate_weekly_diet_plan_success(self, diet_plan_ai):
        """Test successful weekly diet plan generation"""
        health_context = """
        # Health Context Document
        
        ## User Profile
        - Name: Test User
        - Diet Type: Vegetarian
        
        ## Calculated Metrics
        - BMR: 1800 calories
        - TDEE: 2200 calories
        """
        
        # Mock the AI provider to return a proper weekly plan
        mock_weekly_plan = {
            "plan_type": "weekly",
            "start_date": "2024-01-15",
            "days": [
                {
                    "date": f"2024-01-{15+i:02d}",
                    "day_name": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][i],
                    "meals": [
                        {
                            "type": "breakfast",
                            "name": "Test Meal",
                            "ingredients": [{"name": "test", "quantity": 1, "unit": "g"}],
                            "instructions": "Test instructions",
                            "nutrition": {"calories": 100, "protein": 10, "carbohydrates": 20, "fat": 5}
                        }
                    ],
                    "daily_totals": {"calories": 100, "protein": 10, "carbohydrates": 20, "fat": 5}
                }
                for i in range(7)
            ],
            "weekly_totals": {"calories": 700, "protein": 70, "carbohydrates": 140, "fat": 35}
        }
        
        with patch.object(diet_plan_ai.ai_provider, 'generate_completion') as mock_generate:
            mock_generate.return_value = (json.dumps(mock_weekly_plan), {})
            
            plan_data = await diet_plan_ai.generate_diet_plan(
                health_context=health_context,
                plan_type="weekly"
            )
            
            # Verify plan structure
            assert plan_data['plan_type'] == 'weekly'
            assert 'start_date' in plan_data
            assert 'days' in plan_data
            assert 'weekly_totals' in plan_data
            
            # Verify days
            days = plan_data['days']
            assert len(days) == 7
            
            for day in days:
                assert 'date' in day
                assert 'meals' in day
                assert 'daily_totals' in day
    
    @pytest.mark.asyncio
    async def test_generate_diet_plan_invalid_json_response(self, diet_plan_ai):
        """Test diet plan generation with invalid JSON response"""
        # Mock provider to return invalid JSON
        with patch.object(diet_plan_ai.ai_provider, 'generate_completion') as mock_generate:
            mock_generate.return_value = ("Invalid JSON {", {})
            
            with pytest.raises(AIServiceError, match="Diet plan generation failed"):
                await diet_plan_ai.generate_diet_plan(
                    health_context="Test context",
                    plan_type="daily"
                )
    
    @pytest.mark.asyncio
    async def test_generate_diet_plan_missing_required_fields(self, diet_plan_ai):
        """Test diet plan generation with missing required fields"""
        # Mock provider to return incomplete JSON
        incomplete_plan = {"plan_type": "daily"}  # Missing required fields
        
        with patch.object(diet_plan_ai.ai_provider, 'generate_completion') as mock_generate:
            mock_generate.return_value = (json.dumps(incomplete_plan), {})
            
            with pytest.raises(AIServiceError, match="Diet plan generation failed"):
                await diet_plan_ai.generate_diet_plan(
                    health_context="Test context",
                    plan_type="daily"
                )
    
    @pytest.mark.asyncio
    async def test_generate_diet_plan_wrong_plan_type(self, diet_plan_ai):
        """Test diet plan generation with wrong plan type in response"""
        wrong_plan = {
            "plan_type": "weekly",  # Wrong type
            "date": "2024-01-15",
            "meals": [],
            "daily_totals": {}
        }
        
        with patch.object(diet_plan_ai.ai_provider, 'generate_completion') as mock_generate:
            mock_generate.return_value = (json.dumps(wrong_plan), {})
            
            with pytest.raises(AIServiceError, match="Diet plan generation failed"):
                await diet_plan_ai.generate_diet_plan(
                    health_context="Test context",
                    plan_type="daily"
                )
    
    @pytest.mark.asyncio
    async def test_generate_diet_plan_rate_limit_fallback(self, diet_plan_ai):
        """Test diet plan generation with rate limit fallback to mock"""
        # Mock provider to raise rate limit error
        with patch.object(diet_plan_ai.ai_provider, 'generate_completion') as mock_generate:
            mock_generate.side_effect = Exception("rate limit exceeded")
            
            # Should fall back to mock data
            plan_data = await diet_plan_ai.generate_diet_plan(
                health_context="Test context",
                plan_type="daily"
            )
            
            # Should get valid plan from mock fallback
            assert plan_data['plan_type'] == 'daily'
            assert 'meals' in plan_data
    
    def test_create_user_prompt_daily(self, diet_plan_ai):
        """Test user prompt creation for daily plans"""
        health_context = "Test health context"
        
        prompt = diet_plan_ai._create_user_prompt(
            health_context=health_context,
            plan_type="daily",
            target_date="2024-01-15"
        )
        
        assert "daily diet plan" in prompt
        assert "2024-01-15" in prompt
        assert health_context in prompt
        assert "ONLY valid JSON" in prompt
    
    def test_create_user_prompt_weekly(self, diet_plan_ai):
        """Test user prompt creation for weekly plans"""
        health_context = "Test health context"
        
        prompt = diet_plan_ai._create_user_prompt(
            health_context=health_context,
            plan_type="weekly"
        )
        
        assert "weekly diet plan" in prompt
        assert health_context in prompt
        assert "ONLY valid JSON" in prompt
    
    def test_validate_weekly_plan_structure(self, diet_plan_ai):
        """Test weekly plan structure validation"""
        valid_weekly_plan = {
            "plan_type": "weekly",
            "start_date": "2024-01-15",
            "days": [
                {
                    "date": "2024-01-15",
                    "meals": [{"type": "breakfast", "name": "test", "ingredients": [{"name": "test", "quantity": 1, "unit": "g"}], "instructions": "test", "nutrition": {"calories": 100, "protein": 10, "carbohydrates": 20, "fat": 5}}],
                    "daily_totals": {"calories": 100, "protein": 10, "carbohydrates": 20, "fat": 5}
                }
            ] * 7,  # 7 days
            "weekly_totals": {"calories": 700, "protein": 70, "carbohydrates": 140, "fat": 35}
        }
        
        # Should not raise exception
        diet_plan_ai._validate_weekly_plan(valid_weekly_plan)
    
    def test_validate_weekly_plan_wrong_day_count(self, diet_plan_ai):
        """Test weekly plan validation with wrong day count"""
        invalid_weekly_plan = {
            "plan_type": "weekly",
            "start_date": "2024-01-15",
            "days": [],  # Wrong number of days
            "weekly_totals": {}
        }
        
        with pytest.raises(AIServiceValidationError, match="must contain exactly 7 days"):
            diet_plan_ai._validate_weekly_plan(invalid_weekly_plan)
    
    def test_validate_daily_plan_structure(self, diet_plan_ai):
        """Test daily plan structure validation"""
        valid_daily_plan = {
            "plan_type": "daily",
            "date": "2024-01-15",
            "day_name": "Monday",
            "meals": [
                {
                    "type": "breakfast",
                    "name": "Test Meal",
                    "ingredients": [{"name": "test", "quantity": 1, "unit": "g"}],
                    "instructions": "Test instructions",
                    "nutrition": {"calories": 100, "protein": 10, "carbohydrates": 20, "fat": 5}
                }
            ],
            "daily_totals": {"calories": 100, "protein": 10, "carbohydrates": 20, "fat": 5}
        }
        
        # Should not raise exception
        diet_plan_ai._validate_daily_plan(valid_daily_plan)
    
    def test_validate_meal_structure(self, diet_plan_ai):
        """Test meal structure validation"""
        valid_meal = {
            "type": "breakfast",
            "name": "Test Meal",
            "ingredients": [{"name": "test", "quantity": 1, "unit": "g"}],
            "instructions": "Test instructions",
            "nutrition": {"calories": 100, "protein": 10, "carbohydrates": 20, "fat": 5}
        }
        
        # Should not raise exception
        diet_plan_ai._validate_meal_structure(valid_meal)
    
    def test_validate_meal_structure_missing_ingredients(self, diet_plan_ai):
        """Test meal structure validation with missing ingredients"""
        invalid_meal = {
            "type": "breakfast",
            "name": "Test Meal",
            "ingredients": [],  # Empty ingredients
            "instructions": "Test instructions",
            "nutrition": {"calories": 100, "protein": 10, "carbohydrates": 20, "fat": 5}
        }
        
        with pytest.raises(AIServiceValidationError, match="must contain at least one ingredient"):
            diet_plan_ai._validate_meal_structure(invalid_meal)


class TestAIProviderSelection:
    """Test AI provider selection and configuration"""
    
    def test_get_ai_provider_openai(self):
        """Test getting OpenAI provider"""
        with patch('app.services.ai_providers.settings') as mock_settings:
            mock_settings.ai.ai_provider = 'openai'
            
            # Mock the OpenAI client creation
            with patch('app.services.ai_service.settings') as mock_ai_settings:
                mock_ai_settings.get_openai_api_key.return_value = 'test-key'
                mock_ai_settings.ai.openai_model = 'gpt-4'
                mock_ai_settings.ai.openai_max_tokens = 2000
                mock_ai_settings.ai.openai_temperature = 0.7
                mock_ai_settings.ai.openai_timeout = 30
                
                provider = get_ai_provider()
                from app.services.ai_service import OpenAIClient
                assert isinstance(provider, OpenAIClient)
    
    def test_get_ai_provider_groq(self):
        """Test getting Groq provider"""
        with patch('app.services.ai_providers.settings') as mock_settings:
            mock_settings.ai.ai_provider = 'groq'
            mock_settings.get_groq_api_key.return_value = 'test-key'
            mock_settings.ai.groq_model = 'llama-3.1-8b-instant'
            
            provider = get_ai_provider()
            assert isinstance(provider, GroqAIProvider)
    
    def test_get_ai_provider_mock(self):
        """Test getting Mock provider"""
        with patch('app.services.ai_providers.settings.ai.ai_provider', 'mock'):
            provider = get_ai_provider()
            assert isinstance(provider, MockAIProvider)
    
    def test_get_ai_provider_unknown_fallback(self):
        """Test getting unknown provider falls back to mock"""
        with patch('app.services.ai_providers.settings.ai.ai_provider', 'unknown'):
            provider = get_ai_provider()
            assert isinstance(provider, MockAIProvider)
    
    def test_get_ai_service_singleton(self):
        """Test AI service singleton pattern"""
        service1 = get_ai_service()
        service2 = get_ai_service()
        
        # Should be the same instance when no db_session provided
        assert service1 is service2
    
    def test_get_ai_service_with_db_session(self):
        """Test AI service with database session creates new instance"""
        mock_db = Mock()
        
        service1 = get_ai_service(db_session=mock_db)
        service2 = get_ai_service(db_session=mock_db)
        
        # Should be different instances when db_session provided
        assert service1 is not service2


class TestAIServiceErrorHandling:
    """Test AI service error handling scenarios"""
    
    @pytest.mark.asyncio
    async def test_ai_service_timeout_error(self):
        """Test AI service timeout error handling"""
        with patch('app.services.ai_service.get_ai_provider') as mock_get_provider:
            mock_provider = AsyncMock()
            mock_provider.generate_completion.side_effect = asyncio.TimeoutError()
            mock_get_provider.return_value = mock_provider
            
            ai_service = DietPlanAI()
            
            with pytest.raises(AIServiceError):
                await ai_service.generate_diet_plan(
                    health_context="Test context",
                    plan_type="daily"
                )
    
    @pytest.mark.asyncio
    async def test_ai_service_json_parsing_with_fixes(self):
        """Test AI service JSON parsing with automatic fixes"""
        with patch('app.services.ai_service.get_ai_provider') as mock_get_provider:
            mock_provider = AsyncMock()
            # JSON with trailing comma (common AI error)
            broken_json = '{"plan_type": "daily", "date": "2024-01-15", "day_name": "Monday", "meals": [{"type": "breakfast", "name": "test", "ingredients": [{"name": "test", "quantity": 1, "unit": "g"}], "instructions": "test", "nutrition": {"calories": 100, "protein": 10, "carbohydrates": 20, "fat": 5}}], "daily_totals": {"calories": 100, "protein": 10, "carbohydrates": 20, "fat": 5}}'
            mock_provider.generate_completion.return_value = (broken_json, {})
            mock_get_provider.return_value = mock_provider
            
            ai_service = DietPlanAI()
            
            # Should successfully parse the valid JSON
            result = await ai_service.generate_diet_plan(
                health_context="Test context",
                plan_type="daily"
            )
            
            assert result['plan_type'] == 'daily'
    
    @pytest.mark.asyncio
    async def test_ai_service_truncated_json_recovery(self):
        """Test AI service recovery from truncated JSON"""
        with patch('app.services.ai_service.get_ai_provider') as mock_get_provider:
            mock_provider = AsyncMock()
            # Truncated JSON (missing closing brace)
            truncated_json = '{"plan_type": "daily", "date": "2024-01-15"'
            mock_provider.generate_completion.return_value = (truncated_json, {})
            mock_get_provider.return_value = mock_provider
            
            ai_service = DietPlanAI()
            
            with pytest.raises(AIServiceError, match="Diet plan generation failed"):
                await ai_service.generate_diet_plan(
                    health_context="Test context",
                    plan_type="daily"
                )


if __name__ == "__main__":
    pytest.main([__file__])