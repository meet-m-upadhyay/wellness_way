#!/usr/bin/env python3
"""
Test FastAPI endpoint directly
"""

import asyncio
from fastapi.testclient import TestClient
from app.main import app

def test_endpoint():
    print("🔍 Testing FastAPI endpoint...")
    
    try:
        with TestClient(app) as client:
            # Test the health endpoint first
            response = client.get("/health")
            print(f"✅ Health endpoint: {response.status_code} - {response.json()}")
            
            # Test the database health endpoint
            response = client.get("/db-health")
            print(f"✅ DB Health endpoint: {response.status_code} - {response.json()}")
            
            # Test the user profile endpoint
            user_id = "eb9dd374-5e74-4492-baeb-ee703f014c4f"
            print(f"🔍 Testing user profile endpoint with ID: {user_id}")
            response = client.get(f"/api/v1/users/profile/{user_id}")
            
            print(f"📊 User profile endpoint: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ Success: {response.json()}")
            else:
                print(f"❌ Error: {response.text}")
                # Try to get more details
                try:
                    error_detail = response.json()
                    print(f"❌ Error detail: {error_detail}")
                except:
                    pass
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_endpoint()