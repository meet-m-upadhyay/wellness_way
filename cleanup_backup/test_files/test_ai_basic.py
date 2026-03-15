"""
Basic test for AI service functionality
"""

import os
import asyncio
from app.services.ai_service import DietPlanAI, AIServiceError, get_ai_service

async def test_ai_service():
    """Test AI service initialization and basic functionality"""
    
    # Test without API key (should fail gracefully)
    try:
        ai_service = DietPlanAI()
        print("❌ AI service should have failed without API key")
    except AIServiceError as e:
        print(f"✅ AI service correctly failed without API key: {e}")
    
    # Test with mock API key
    os.environ["OPENAI_API_KEY"] = "test-key-123"
    
    # Reload settings to pick up the new environment variable
    from app.core.config import Settings
    import importlib
    import app.core.config
    importlib.reload(app.core.config)
    
    try:
        ai_service = get_ai_service()
        print("✅ AI service initialized successfully with API key")
        
        # Test system prompt generation
        system_prompt = ai_service._get_master_system_prompt()
        assert "SAFETY RULES" in system_prompt
        assert "OUTPUT FORMAT" in system_prompt
        print("✅ System prompt generated correctly")
        
        # Test user prompt creation
        health_context = """
        # Health Context Document
        ## User Profile
        **Name:** Test User
        **Age:** 30 years
        **Gender:** Male
        **Height:** 180 cm
        **Weight:** 75 kg
        """
        
        user_prompt = ai_service._create_user_prompt(health_context, "daily")
        assert "Generate a daily diet plan" in user_prompt
        assert health_context in user_prompt
        print("✅ User prompt created correctly")
        
        print("\n🎉 All AI service tests passed!")
        
    except Exception as e:
        print(f"❌ AI service test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ai_service())