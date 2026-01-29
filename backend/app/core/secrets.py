"""
Secure API key management for WellnessWay Diet Planner
"""

import base64
import os
from typing import Optional
from cryptography.fernet import Fernet
from pathlib import Path

class SecureKeyManager:
    """Manages API keys with encryption and runtime input options"""
    
    def __init__(self):
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for API keys"""
        key_file = Path(".kiro/secrets/encryption.key")
        
        if key_file.exists():
            return key_file.read_bytes()
        else:
            # Create directory if it doesn't exist
            key_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate new key
            key = Fernet.generate_key()
            key_file.write_bytes(key)
            
            # Set restrictive permissions (Unix-like systems)
            try:
                os.chmod(key_file, 0o600)
            except:
                pass  # Windows doesn't support chmod
            
            return key
    
    def encode_key(self, api_key: str) -> str:
        """Encode an API key for storage"""
        encrypted = self.cipher.encrypt(api_key.encode())
        return base64.b64encode(encrypted).decode()
    
    def decode_key(self, encoded_key: str) -> str:
        """Decode an API key from storage"""
        try:
            encrypted = base64.b64decode(encoded_key.encode())
            return self.cipher.decrypt(encrypted).decode()
        except Exception:
            # If decoding fails, assume it's a plain text key
            return encoded_key
    
    def get_api_key(self, provider: str, encoded_key: Optional[str] = None, 
                   prompt_if_missing: bool = True) -> Optional[str]:
        """
        Get API key for a provider with multiple fallback options:
        1. Use provided encoded_key (decode it)
        2. Check environment variables
        3. Prompt user for input (if enabled)
        """
        
        # Option 1: Use provided encoded key
        if encoded_key and encoded_key not in ["your-encoded-key-here", ""]:
            try:
                return self.decode_key(encoded_key)
            except Exception:
                pass
        
        # Option 2: Check environment variables
        env_key = os.getenv(f"{provider.upper()}_API_KEY")
        if env_key and env_key not in [f"your-{provider}-api-key-here", ""]:
            return env_key
        
        # Option 3: Prompt user (if enabled and running interactively)
        if prompt_if_missing and os.isatty(0):  # Check if running in terminal
            try:
                key = input(f"Enter your {provider.title()} API key: ").strip()
                if key:
                    return key
            except (KeyboardInterrupt, EOFError):
                pass
        
        return None

# Global instance
key_manager = SecureKeyManager()

def get_secure_api_key(provider: str, encoded_key: Optional[str] = None) -> Optional[str]:
    """Convenience function to get API key securely"""
    return key_manager.get_api_key(provider, encoded_key, prompt_if_missing=False)

def encode_api_key(api_key: str) -> str:
    """Convenience function to encode API key"""
    return key_manager.encode_key(api_key)