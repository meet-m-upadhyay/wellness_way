#!/usr/bin/env python3
"""
Check System Prompt Changes

Verifies that the calorie density rules are in the system prompt.
"""

from app.services.ai_service import DietPlanAI

def test_system_prompt():
    """Check that system prompt includes calorie density rules"""
    print("Checking system prompt for calorie density rules...")
    
    ai_service = DietPlanAI()
    system_prompt = ai_service._get_system_prompt()
    
    print("System prompt content:")
    print("=" * 50)
    print(system_prompt)
    print("=" * 50)
    
    # Check for key phrases
    required_phrases = [
        "CRITICAL MEAL ENERGY RULES",
        "Each main meal MUST contribute meaningful calories",
        "Protein-only meals are forbidden",
        "Meals under 350 kcal are INVALID",
        "Daily plan must reach calorie target BEFORE scaling"
    ]
    
    missing_phrases = []
    for phrase in required_phrases:
        if phrase not in system_prompt:
            missing_phrases.append(phrase)
        else:
            print(f"✅ Found: {phrase}")
    
    if missing_phrases:
        print(f"❌ Missing phrases: {missing_phrases}")
        return False
    else:
        print("✅ All calorie density rules present in system prompt")
        return True

if __name__ == "__main__":
    success = test_system_prompt()
    if not success:
        exit(1)