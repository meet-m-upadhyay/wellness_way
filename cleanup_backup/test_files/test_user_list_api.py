#!/usr/bin/env python3
"""
Test script to verify the user list API endpoint works
"""

import requests
import json

def test_user_list_api():
    """Test the /users/profiles endpoint"""
    
    base_url = "http://localhost:8000/api/v1"
    
    try:
        # Test the new endpoint
        response = requests.get(f"{base_url}/users/profiles?limit=10")
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            users = response.json()
            print(f"\n✅ SUCCESS: Found {len(users)} users")
            
            for i, user in enumerate(users[:3]):  # Show first 3 users
                print(f"\nUser {i+1}:")
                print(f"  ID: {user.get('id')}")
                print(f"  Name: {user.get('name')}")
                print(f"  Age: {user.get('age')}")
                print(f"  Gender: {user.get('gender')}")
                print(f"  Activity Level: {user.get('activity_level')}")
            
            if len(users) > 3:
                print(f"\n... and {len(users) - 3} more users")
                
        else:
            print(f"❌ FAILED: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Make sure the backend server is running on localhost:8000")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    print("🧪 Testing User List API Endpoint")
    print("=" * 40)
    test_user_list_api()