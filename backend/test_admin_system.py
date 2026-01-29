#!/usr/bin/env python3
"""
Test script to verify admin system functionality
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.services.auth_service import auth_service
from app.models.user import User


async def test_admin_system():
    """Test the admin system functionality"""
    
    print("🔧 Testing Admin System...")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Test 1: Check if admin email gets admin privileges
        print("\n1. Testing admin email assignment...")
        
        # Simulate Google OAuth data for admin user
        admin_google_info = {
            'google_id': 'test_admin_123',
            'email': 'meetupadhyaykgp@gmail.com',
            'name': 'Admin User',
            'picture': '',
            'email_verified': True
        }
        
        # Create or get admin user
        admin_user = auth_service.get_or_create_user_from_google(admin_google_info, db)
        
        print(f"   ✓ Admin user created/found: {admin_user.email}")
        print(f"   ✓ Admin status: {admin_user.is_admin}")
        
        if admin_user.is_admin:
            print("   ✅ Admin privileges correctly assigned!")
        else:
            print("   ❌ Admin privileges NOT assigned!")
            return False
        
        # Test 2: Check if non-admin email doesn't get admin privileges
        print("\n2. Testing non-admin email...")
        
        regular_google_info = {
            'google_id': 'test_regular_456',
            'email': 'regular.user@example.com',
            'name': 'Regular User',
            'picture': '',
            'email_verified': True
        }
        
        regular_user = auth_service.get_or_create_user_from_google(regular_google_info, db)
        
        print(f"   ✓ Regular user created/found: {regular_user.email}")
        print(f"   ✓ Admin status: {regular_user.is_admin}")
        
        if not regular_user.is_admin:
            print("   ✅ Regular user correctly has no admin privileges!")
        else:
            print("   ❌ Regular user incorrectly has admin privileges!")
            return False
        
        # Test 3: Check database admin field
        print("\n3. Testing database admin field...")
        
        # Query users directly from database
        admin_from_db = db.query(User).filter(User.email == 'meetupadhyaykgp@gmail.com').first()
        regular_from_db = db.query(User).filter(User.email == 'regular.user@example.com').first()
        
        if admin_from_db and admin_from_db.is_admin:
            print("   ✅ Admin user has is_admin=True in database!")
        else:
            print("   ❌ Admin user missing or incorrect in database!")
            return False
            
        if regular_from_db and not regular_from_db.is_admin:
            print("   ✅ Regular user has is_admin=False in database!")
        else:
            print("   ❌ Regular user missing or incorrect in database!")
            return False
        
        print("\n🎉 All admin system tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = asyncio.run(test_admin_system())
    if success:
        print("\n✅ Admin system is working correctly!")
        sys.exit(0)
    else:
        print("\n❌ Admin system has issues!")
        sys.exit(1)