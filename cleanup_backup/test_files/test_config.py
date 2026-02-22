#!/usr/bin/env python3
"""
Test configuration loading
"""
from app.core.config import settings

def test_config():
    print("=== Configuration Test ===")
    print(f"Environment: {settings.environment}")
    print(f"Debug: {settings.debug}")
    print(f"Database URL: {settings.database.url}")
    print(f"Redis URL: {settings.cache.redis_url}")
    print(f"AI Provider: {settings.ai.ai_provider}")
    print("=========================")

if __name__ == "__main__":
    test_config()