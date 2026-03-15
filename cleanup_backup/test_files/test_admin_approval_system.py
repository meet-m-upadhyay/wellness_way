#!/usr/bin/env python3
"""
Test script for the admin approval system
This script tests the complete user journey from registration to approval
"""

import sys
import os
sys.path.append('backend')

from app.services.auth_service import auth_service
from app.database.connection import get_db
from app.models.user import User, RegistrationRequest
from sqlalchemy.orm import Session

def test_admin_approval_system():
    """Test the complete admin approval system workflow"""
    
    print("🧪 Testing Admin Approval System")
    print("=" * 50)
    
    # Get database session
    db: Session = next(get_db())
    
    # Test 1: Admin user creation (should bypass approval)
    print("\n1️⃣ Testing Admin User Creation")
    print("-" * 30)
    
    admin_google_info = {
        'google_id': 'admin-test-123',
        'email': 'meetupadhyaykgp@gmail.com',
        'name': 'Test Admin User'
    }
    
    try:
        # Clean up any existing test data
        existing_admin = db.query(User).filter(User.email == admin_google_info['email']).first()
        if existing_admin:
            db.delete(existing_admin)
            db.commit()
        
        user, is_new = auth_service.get_or_create_user_from_google(admin_google_info, db)
        
        if user and user.is_admin:
            print(f"✅ Admin user created successfully")
            print(f"   Email: {user.email}")
            print(f"   Is Admin: {user.is_admin}")
            print(f"   Approval Status: {user.approval_status}")
        else:
            print("❌ Admin user creation failed")
            return False
            
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return False
    
    # Test 2: Regular user registration (should create pending request)
    print("\n2️⃣ Testing Regular User Registration")
    print("-" * 35)
    
    user_google_info = {
        'google_id': 'user-test-456',
        'email': 'testuser@example.com',
        'name': 'Test Regular User'
    }
    
    try:
        # Clean up any existing test data
        existing_user = db.query(User).filter(User.email == user_google_info['email']).first()
        if existing_user:
            db.delete(existing_user)
            db.commit()
            
        existing_request = db.query(RegistrationRequest).filter(
            RegistrationRequest.email == user_google_info['email']
        ).first()
        if existing_request:
            db.delete(existing_request)
            db.commit()
        
        user, is_new = auth_service.get_or_create_user_from_google(user_google_info, db)
        
        if user is None and is_new:
            print("✅ Registration request created successfully")
            
            # Verify the request exists in database
            request = db.query(RegistrationRequest).filter(
                RegistrationRequest.email == user_google_info['email']
            ).first()
            
            if request:
                print(f"   Email: {request.email}")
                print(f"   Status: {request.status}")
                print(f"   Name: {request.name}")
            else:
                print("❌ Registration request not found in database")
                return False
        else:
            print(f"❌ Unexpected result: user={user}, is_new={is_new}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating registration request: {e}")
        return False
    
    # Test 3: Admin approval process
    print("\n3️⃣ Testing Admin Approval Process")
    print("-" * 32)
    
    try:
        # Get the registration request
        request = db.query(RegistrationRequest).filter(
            RegistrationRequest.email == user_google_info['email']
        ).first()
        
        if not request:
            print("❌ Registration request not found")
            return False
        
        # Approve the request
        request.approve()
        db.commit()
        
        print("✅ Registration request approved")
        print(f"   Status: {request.status}")
        
        # Now try to create user again (should succeed)
        user, is_new = auth_service.get_or_create_user_from_google(user_google_info, db)
        
        if user and user.approval_status == 'approved':
            print("✅ User created after approval")
            print(f"   Email: {user.email}")
            print(f"   Is Admin: {user.is_admin}")
            print(f"   Approval Status: {user.approval_status}")
        else:
            print(f"❌ User creation after approval failed: user={user}")
            return False
            
    except Exception as e:
        print(f"❌ Error in approval process: {e}")
        return False
    
    # Test 4: User status checking
    print("\n4️⃣ Testing User Status Checking")
    print("-" * 30)
    
    try:
        # Test approved user status
        status_info = auth_service.get_user_status(user_google_info['email'], db)
        if status_info['status'] == 'approved':
            print("✅ Approved user status check passed")
            print(f"   Status: {status_info['status']}")
            print(f"   Message: {status_info['message']}")
        else:
            print(f"❌ Unexpected status: {status_info}")
            return False
        
        # Test non-existent user status
        status_info = auth_service.get_user_status('nonexistent@example.com', db)
        if status_info['status'] == 'not_found':
            print("✅ Non-existent user status check passed")
        else:
            print(f"❌ Unexpected status for non-existent user: {status_info}")
            return False
            
    except Exception as e:
        print(f"❌ Error in status checking: {e}")
        return False
    
    # Clean up test data
    print("\n🧹 Cleaning up test data...")
    try:
        # Remove test users and requests
        test_admin = db.query(User).filter(User.email == admin_google_info['email']).first()
        if test_admin:
            db.delete(test_admin)
        
        test_user = db.query(User).filter(User.email == user_google_info['email']).first()
        if test_user:
            db.delete(test_user)
        
        test_request = db.query(RegistrationRequest).filter(
            RegistrationRequest.email == user_google_info['email']
        ).first()
        if test_request:
            db.delete(test_request)
        
        db.commit()
        print("✅ Test data cleaned up")
        
    except Exception as e:
        print(f"⚠️ Warning: Could not clean up test data: {e}")
    
    print("\n🎉 All tests passed! Admin approval system is working correctly.")
    return True

if __name__ == "__main__":
    success = test_admin_approval_system()
    sys.exit(0 if success else 1)