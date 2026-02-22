#!/usr/bin/env python3
"""
Test the complete profile API endpoint
"""

import requests
import json

def test_complete_profile_api():
    # Test user ID with completed profile
    user_id = "bb0582c4-0d56-4405-9594-b4e62efa7d9e"
    
    # API endpoint
    url = f"http://localhost:8000/api/v1/users/complete-profile/{user_id}"
    
    try:
        response = requests.get(url, headers={"Content-Type": "application/json"})
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n=== Complete Profile Data ===")
            print(json.dumps(data, indent=2))
            
            # Verify structure
            required_keys = ['profile', 'goals', 'preferences']
            for key in required_keys:
                if key in data:
                    print(f"✓ {key} section found")
                else:
                    print(f"✗ {key} section missing")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_complete_profile_api()