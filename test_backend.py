#!/usr/bin/env python3
"""
Test script to verify backend functionality
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append('backend')

async def test_backend():
    """Test backend components"""
    
    print("🧪 WellnessWay Diet Planner - Backend Test")
    print("=" * 50)
    
    try:
        # Test configuration
        print("1. Testing configuration...")
        from app.core.config import settings
        print(f"   ✅ Environment: {settings.environment}")
        print(f"   ✅ API Host: {settings.api_host}:{settings.api_port}")
        print(f"   ✅ Database URL: {settings.database.url[:50]}...")
        
        # Test database connection
        print("\n2. Testing database connection...")
        from app.database.connection import SessionLocal
        from sqlalchemy import text
        
        db = SessionLocal()
        result = db.execute(text("SELECT 1"))
        db.close()
        print("   ✅ Database connection successful")
        
        # Test business logic
        print("\n3. Testing business logic...")
        from app.services.health_calculations import calculate_bmr, calculate_tdee
        
        bmr = calculate_bmr(70, 175, 30, "male")
        tdee = calculate_tdee(bmr, "moderately_active")
        print(f"   ✅ BMR calculation: {bmr} calories")
        print(f"   ✅ TDEE calculation: {tdee} calories")
        
        # Test Health Context Document generation
        print("\n4. Testing HCD generation...")
        from app.services.health_calculations import generate_health_context_document
        
        # Create test user data
        test_profile = {
            "name": "Test User",
            "age": 30,
            "gender": "male",
            "height_cm": 175,
            "weight_kg": 70,
            "activity_level": "moderately_active"
        }
        
        test_goals = {
            "primary_goal": "maintenance",
            "target_weight_kg": 70
        }
        
        test_preferences = {
            "diet_type": "non_vegetarian",
            "allergies": [],
            "foods_to_avoid": [],
            "meals_per_day": 3
        }
        
        hcd_content = generate_health_context_document(
            test_profile, test_goals, test_preferences
        )
        print("   ✅ HCD generation successful")
        print(f"   📄 HCD length: {len(hcd_content)} characters")
        
        # Test AI configuration
        print("\n5. Testing AI configuration...")
        ai_provider = settings.ai.ai_provider
        print(f"   ✅ AI Provider: {ai_provider}")
        
        if ai_provider == "openai":
            openai_key = settings.get_openai_api_key()
            if openai_key and openai_key != "your-openai-api-key-here":
                print("   ✅ OpenAI API key configured")
            else:
                print("   ⚠️  OpenAI API key not configured")
        elif ai_provider == "groq":
            groq_key = settings.ai.groq_api_key.get_secret_value() if settings.ai.groq_api_key else None
            if groq_key and groq_key != "your-groq-api-key-here":
                print("   ✅ Groq API key configured")
            else:
                print("   ⚠️  Groq API key not configured")
        elif ai_provider == "huggingface":
            hf_key = settings.ai.huggingface_api_key.get_secret_value() if settings.ai.huggingface_api_key else None
            if hf_key and hf_key != "your-huggingface-api-key-here":
                print("   ✅ Hugging Face API key configured")
                print(f"   📝 Model: {settings.ai.huggingface_model}")
            else:
                print("   ⚠️  Hugging Face API key not configured")
        elif ai_provider == "ollama":
            print(f"   ✅ Ollama configured: {settings.ai.ollama_base_url}")
            print(f"   📝 Model: {settings.ai.ollama_model}")
        elif ai_provider == "mock":
            print("   ✅ Mock AI provider configured (no API key needed)")
        
        # Test AI service initialization
        from app.services.ai_service import get_ai_service
        ai_service = get_ai_service()
        print("   ✅ AI service initialized")
        
        print("\n🎉 Backend test completed successfully!")
        print("\nNext steps:")
        print("1. Configure AI provider if needed: python setup_ai.py")
        print("2. Start backend: cd backend && python -m uvicorn app.main:app --reload")
        print("3. Start frontend: cd frontend && npm start")
        print("4. Test complete flow at http://localhost:3000")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Backend test failed: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Make sure you're in the project root directory")
        print("2. Check if the database is running: docker-compose up -d")
        print("3. Install backend dependencies: cd backend && pip install -r requirements.txt")
        print("4. Configure AI provider: python setup_ai.py")
        return False

if __name__ == "__main__":
    asyncio.run(test_backend())