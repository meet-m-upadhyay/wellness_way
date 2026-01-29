import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text
from app.core.config import settings

try:
    engine = create_engine("postgresql+psycopg://wellnessway:password@localhost:5432/wellnessway_db")
    
    with engine.connect() as conn:
        print(" Current Users in Database:")
        print("=" * 50)
        
        result = conn.execute(text("""
            SELECT id, name, age, gender, activity_level, 
                   TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI') as created 
            FROM users 
            ORDER BY created_at DESC
        """))
        
        for row in result:
            print(f"ID: {row[0]}")
            print(f"Name: {row[1]} ({row[2]}y, {row[3]}, {row[4]})")
            print(f"Created: {row[5]}")
            print("-" * 30)
            
        print(f"\n Total users: {conn.execute(text('SELECT COUNT(*) FROM users')).scalar()}")
        print(f" Total diet plans: {conn.execute(text('SELECT COUNT(*) FROM diet_plans')).scalar()}")
        print(f" Total health contexts: {conn.execute(text('SELECT COUNT(*) FROM health_context_documents')).scalar()}")
        
except Exception as e:
    print(f"Error: {e}")
