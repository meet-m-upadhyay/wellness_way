#!/usr/bin/env python3
"""
Test database connection
"""

from app.database.connection import engine, get_db
from sqlalchemy import text

def test_connection():
    print("🔍 Testing database connection...")
    
    try:
        # Test engine connection
        with engine.connect() as conn:
            result = conn.execute(text('SELECT 1')).scalar()
            print(f"✅ Engine connection successful: {result}")
        
        # Test session
        db_gen = get_db()
        db = next(db_gen)
        print(f"✅ Session created: {type(db)}")
        
        # Test query
        result = db.execute(text('SELECT COUNT(*) FROM users')).scalar()
        print(f"✅ Users count: {result}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_connection()