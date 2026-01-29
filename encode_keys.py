#!/usr/bin/env python3
"""
Secure API Key Encoder for WellnessWay Diet Planner
Encodes your existing API keys for secure storage
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append('backend')

def encode_existing_keys():
    """Encode existing API keys from .env file"""
    
    print("🔐 WellnessWay Diet Planner - API Key Encoder")
    print("=" * 60)
    print()
    
    try:
        from app.core.secrets import key_manager
        
        # Read current .env file
        env_file = Path(".env")
        if not env_file.exists():
            print("❌ .env file not found!")
            return False
        
        with open(env_file, 'r') as f:
            content = f.read()
        
        # Extract current keys
        keys_to_encode = {}
        
        # Check for Groq key
        if "GROQ_API_KEY=gsk_" in content:
            start = content.find("GROQ_API_KEY=") + len("GROQ_API_KEY=")
            end = content.find("\n", start)
            groq_key = content[start:end].strip()
            if groq_key.startswith("gsk_"):
                keys_to_encode["groq"] = groq_key
        
        # Check for Hugging Face key
        if "HUGGINGFACE_API_KEY=hf_" in content:
            start = content.find("HUGGINGFACE_API_KEY=") + len("HUGGINGFACE_API_KEY=")
            end = content.find("\n", start)
            hf_key = content[start:end].strip()
            if hf_key.startswith("hf_"):
                keys_to_encode["huggingface"] = hf_key
        
        if not keys_to_encode:
            print("ℹ️  No API keys found to encode in .env file")
            return True
        
        print("Found API keys to encode:")
        for provider in keys_to_encode:
            print(f"  ✅ {provider.title()}")
        print()
        
        choice = input("Encode these keys for secure storage? (y/n): ").strip().lower()
        if choice != 'y':
            print("❌ Encoding cancelled")
            return False
        
        # Encode keys
        encoded_keys = {}
        for provider, key in keys_to_encode.items():
            encoded_keys[provider] = key_manager.encode_key(key)
            print(f"✅ Encoded {provider.title()} API key")
        
        # Update .env file with encoded keys
        updated_content = content
        
        for provider, encoded_key in encoded_keys.items():
            if provider == "groq":
                # Replace plain key with encoded version
                updated_content = updated_content.replace(
                    f"GROQ_API_KEY={keys_to_encode[provider]}",
                    f"GROQ_API_KEY_ENCODED={encoded_key}\n# Original key removed for security"
                )
            elif provider == "huggingface":
                updated_content = updated_content.replace(
                    f"HUGGINGFACE_API_KEY={keys_to_encode[provider]}",
                    f"HUGGINGFACE_API_KEY_ENCODED={encoded_key}\n# Original key removed for security"
                )
        
        # Write updated .env file
        with open(env_file, 'w') as f:
            f.write(updated_content)
        
        print()
        print("🎉 API keys successfully encoded!")
        print()
        print("Security improvements:")
        print("  ✅ Keys are now encrypted with a unique encryption key")
        print("  ✅ Encryption key stored in .kiro/secrets/ (add to .gitignore)")
        print("  ✅ Original plain text keys removed from .env")
        print()
        print("Your keys are now secure! The application will automatically")
        print("decode them when needed.")
        
        return True
        
    except ImportError as e:
        print(f"❌ Cannot import security module: {e}")
        print("Make sure you're in the project root directory")
        return False
    except Exception as e:
        print(f"❌ Encoding failed: {str(e)}")
        return False

if __name__ == "__main__":
    encode_existing_keys()