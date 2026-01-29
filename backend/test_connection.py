#!/usr/bin/env python3
"""
Simple database connection test
"""
import os
import psycopg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection():
    database_url = os.getenv("DATABASE_URL", "postgresql://wellnessway:password@localhost:5432/wellnessway_db")
    print(f"Testing connection to: {database_url}")
    
    try:
        # Test connection
        conn = psycopg.connect(database_url)
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Connection successful!")
        print(f"PostgreSQL version: {version[0]}")
        
        # List tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public';
        """)
        tables = cursor.fetchall()
        print(f"Tables in database: {[table[0] for table in tables]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_connection()