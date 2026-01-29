#!/usr/bin/env python3
"""
Debug API dependency injection
"""

from app.database.connection import get_db
from app.services.user_service import UserService
from uuid import UUID

def test_user_service():
    print("🔍 Testing UserService...")
    
    try:
        # Get database session
        db_gen = get_db()
        db = next(db_gen)
        print(f"✅ Database session: {type(db)}")
        
        # Create user service
        user_service = UserService(db)
        print(f"✅ UserService created: {type(user_service)}")
        print(f"✅ UserService.db: {type(user_service.db)}")
        
        # Test query
        user_id = UUID("eb9dd374-5e74-4492-baeb-ee703f014c4f")
        print(f"🔍 Testing query for user: {user_id}")
        
        # Direct query test
        from app.models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        print(f"✅ Direct query result: {user.name if user else 'None'}")
        
        # Service method test
        import asyncio
        async def test_service():
            result = await user_service.get_user_profile(user_id)
            return result
        
        result = asyncio.run(test_service())
        print(f"✅ Service method result: {result.name if result else 'None'}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_user_service()