#!/usr/bin/env python3
"""
Check Health Context Document content to see dietary restrictions
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text
from uuid import UUID

try:
    engine = create_engine("postgresql+psycopg://wellnessway:password@localhost:5432/wellnessway_db")
    
    with engine.connect() as conn:
        print("🔍 Health Context Documents:")
        print("=" * 50)
        
        # Get the test user's HCD
        user_id = "f53f6cb3-4b52-47ca-9cdb-bb61ece32610"
        
        result = conn.execute(text("""
            SELECT id, user_id, version, is_active, content,
                   TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI') as created 
            FROM health_context_documents 
            WHERE user_id = :user_id
            ORDER BY version DESC
        """), {"user_id": user_id})
        
        for row in result:
            print(f"HCD ID: {row[0]}")
            print(f"User ID: {row[1]}")
            print(f"Version: {row[2]} (Active: {row[3]})")
            print(f"Created: {row[5]}")
            print(f"Content Preview:")
            print("-" * 30)
            content = row[4][:1000] + "..." if len(row[4]) > 1000 else row[4]
            print(content)
            print("=" * 50)
            
        # Also check user details
        print("\n👤 User Details:")
        print("=" * 30)
        
        result = conn.execute(text("""
            SELECT name, age, gender, activity_level, dietary_restrictions, allergies
            FROM users 
            WHERE id = :user_id
        """), {"user_id": user_id})
        
        user = result.fetchone()
        if user:
            print(f"Name: {user[0]}")
            print(f"Age: {user[1]}")
            print(f"Gender: {user[2]}")
            print(f"Activity Level: {user[3]}")
            print(f"Dietary Restrictions: {user[4]}")
            print(f"Allergies: {user[5]}")
        else:
            print("User not found")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()