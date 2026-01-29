#!/usr/bin/env python3
"""
Setup script for OpenAI API key configuration
"""

import os
import sys
from pathlib import Path

#!/usr/bin/env python3
"""
Setup script for AI provider configuration
"""

import os
import sys
from pathlib import Path

def setup_ai_provider():
    """Interactive setup for AI provider"""
    
    print("🤖 WellnessWay Diet Planner - AI Provider Setup")
    print("=" * 60)
    print()
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found!")
        print("Please copy .env.example to .env first:")
        print("cp .env.example .env")
        return False
    
    print("Choose your AI provider:")
    print()
    print("1. 🆓 Mock AI (Free - for testing)")
    print("   - Generates realistic fake meal plans")
    print("   - No API key needed")
    print("   - Perfect for development and testing")
    print()
    print("2. 🚀 Groq (Free - recommended)")
    print("   - 14,400 requests/day free")
    print("   - Very fast inference")
    print("   - Uses Llama 3.1 model")
    print("   - Get free key: https://console.groq.com/")
    print()
    print("3. 🏠 Ollama (Free - local)")
    print("   - Completely free, runs on your computer")
    print("   - No internet required after setup")
    print("   - Install: https://ollama.ai/")
    print()
    print("4. 🤗 Hugging Face (Free tier)")
    print("   - Free tier available")
    print("   - Large model selection")
    print("   - Get free key: https://huggingface.co/settings/tokens")
    print()
    print("5. 💰 OpenAI (Paid)")
    print("   - High quality but costs money")
    print("   - Uses GPT-4")
    print("   - Get key: https://platform.openai.com/api-keys")
    print()
    
    choice = input("Enter your choice (1-5): ").strip()
    
    # Read current .env file
    with open(env_file, 'r') as f:
        content = f.read()
    
    if choice == "1":
        # Mock AI
        updated_content = content.replace('AI_PROVIDER=mock', 'AI_PROVIDER=mock')
        print("✅ Mock AI provider configured!")
        print("No API key needed - you can start testing immediately!")
        
    elif choice == "2":
        # Groq
        api_key = input("Enter your Groq API key (or press Enter to skip): ").strip()
        if api_key:
            updated_content = content.replace('AI_PROVIDER=mock', 'AI_PROVIDER=groq')
            updated_content = updated_content.replace('GROQ_API_KEY=your-groq-api-key-here', f'GROQ_API_KEY={api_key}')
            print("✅ Groq AI provider configured!")
        else:
            print("⚠️ Skipping Groq setup. Get your free API key from https://console.groq.com/")
            return False
            
    elif choice == "3":
        # Ollama
        base_url = input("Enter Ollama base URL (default: http://localhost:11434): ").strip()
        if not base_url:
            base_url = "http://localhost:11434"
        
        model = input("Enter Ollama model (default: llama3.1): ").strip()
        if not model:
            model = "llama3.1"
            
        updated_content = content.replace('AI_PROVIDER=mock', 'AI_PROVIDER=ollama')
        updated_content = updated_content.replace('OLLAMA_BASE_URL=http://localhost:11434', f'OLLAMA_BASE_URL={base_url}')
        updated_content = updated_content.replace('OLLAMA_MODEL=llama3.1', f'OLLAMA_MODEL={model}')
        
        print("✅ Ollama AI provider configured!")
        print("Make sure Ollama is running: ollama serve")
        print(f"And the model is installed: ollama pull {model}")
        
    elif choice == "4":
        # Hugging Face
        api_key = input("Enter your Hugging Face API key (or press Enter to skip): ").strip()
        if api_key:
            model = input("Enter HF model (default: microsoft/DialoGPT-large): ").strip()
            if not model:
                model = "microsoft/DialoGPT-large"
                
            updated_content = content.replace('AI_PROVIDER=mock', 'AI_PROVIDER=huggingface')
            updated_content = updated_content.replace('HUGGINGFACE_API_KEY=your-huggingface-api-key-here', f'HUGGINGFACE_API_KEY={api_key}')
            updated_content = updated_content.replace('HUGGINGFACE_MODEL=microsoft/DialoGPT-large', f'HUGGINGFACE_MODEL={model}')
            print("✅ Hugging Face AI provider configured!")
        else:
            print("⚠️ Skipping Hugging Face setup. Get your free API key from https://huggingface.co/settings/tokens")
            return False
            
    elif choice == "5":
        # OpenAI
        api_key = input("Enter your OpenAI API key: ").strip()
        if not api_key.startswith('sk-'):
            print("❌ Invalid API key format. OpenAI keys start with 'sk-'")
            return False
            
        updated_content = content.replace('AI_PROVIDER=mock', 'AI_PROVIDER=openai')
        updated_content = updated_content.replace('OPENAI_API_KEY=your-openai-api-key-here', f'OPENAI_API_KEY={api_key}')
        print("✅ OpenAI provider configured!")
        
    else:
        print("❌ Invalid choice. Using Mock AI provider.")
        updated_content = content
    
    # Write back to .env file
    with open(env_file, 'w') as f:
        f.write(updated_content)
    
    print()
    print("Next steps:")
    print("1. Start the backend: cd backend && python -m uvicorn app.main:app --reload")
    print("2. Start the frontend: cd frontend && npm start")
    print("3. Test the complete flow from profile creation to meal generation")
    print()
    
    return True

def test_openai_connection():
    """Test OpenAI connection"""
    try:
        import asyncio
        import sys
        sys.path.append('backend')
        
        from app.core.config import settings
        from app.services.ai_service import get_ai_service
        
        async def test_connection():
            try:
                ai_service = get_ai_service()
                
                # Simple test prompt
                test_hcd = """
# Health Context Document

## User Profile
- Name: Test User
- Age: 30
- Gender: male
- Height: 175 cm
- Weight: 70 kg
- Activity Level: moderately_active

## Health Goals
- Primary Goal: maintenance
- Target Weight: 70 kg

## Diet Preferences
- Diet Type: non_vegetarian
- Allergies: none
- Foods to Avoid: none
- Meals per Day: 3

## Calculated Metrics
- BMR: 1680 calories
- TDEE: 2604 calories
- Min Daily Calories: 1680
- Max Calorie Deficit: 500
- Min Protein: 56g
"""
                
                print("🧪 Testing OpenAI connection...")
                result = await ai_service.generate_diet_plan(
                    health_context=test_hcd,
                    plan_type="daily"
                )
                
                print("✅ OpenAI connection successful!")
                print(f"Generated plan type: {result.get('plan_type')}")
                print(f"Number of meals: {len(result.get('meals', []))}")
                return True
                
            except Exception as e:
                print(f"❌ OpenAI connection failed: {str(e)}")
                return False
        
        return asyncio.run(test_connection())
        
    except ImportError as e:
        print(f"⚠️  Cannot test connection - missing dependencies: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print()
    
    # Setup AI provider
    if setup_ai_provider():
        print()
        test_choice = input("Would you like to test the AI connection? (y/n): ").strip().lower()
        if test_choice == 'y':
            test_openai_connection()
    
    print()
    print("🎉 Setup complete! Your WellnessWay Diet Planner is ready to use.")