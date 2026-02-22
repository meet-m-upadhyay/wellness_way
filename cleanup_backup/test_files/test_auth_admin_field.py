#!/usr/bin/env python3
"""
Test script to verify auth endpoint returns admin field
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import get_db
from app.services.auth_service import auth_service
from sqlalchemy.orm import Session


def test_auth_admin_field():
    """Test that auth endpoint returns admin field"""
    
    print("🔧 Testing Auth Admin Field...")
    
    client = TestClient(app)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Create admin user directly in database
        admin_google_info = {
            'google_id': 'test_admin_auth_123',
            'email': 'meetupadhyaykgp@gmail.com',
            'name': 'Admin User',
            'picture': '',
            'email_verified': True
        }
        
        admin_user = auth_service.get_or_create_user_from_google(admin_google_info, db)
        print(f"✓ Admin user created: {admin_user.email}, is_admin: {admin_user.is_admin}")
        
        # Create tokens for the admin user
        tokens = auth_service.create_tokens_for_user(admin_user)
        access_token = tokens["access_token"]
        
        # Test /auth/me endpoint
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        print(f"✓ Auth me endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✓ Response data: {user_data}")
            
            if 'is_admin' in user_data:
                print(f"✅ is_admin field present: {user_data['is_admin']}")
                if user_data['is_admin'] == True:
                    print("✅ Admin field correctly set to True!")
                    return True
                else:
                    print("❌ Admin field is False, should be True!")
                    return False
            else:
                print("❌ is_admin field missing from response!")
                return False
        else:
            print(f"❌ Auth endpoint failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = test_auth_admin_field()
    if success:
        print("\n✅ Auth admin field test passed!")
        sys.exit(0)
    else:
        print("\n❌ Auth admin field test failed!")
        sys.exit(1)