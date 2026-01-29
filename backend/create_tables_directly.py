#!/usr/bin/env python3
"""
Create database tables directly using SQLAlchemy
"""
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_tables():
    # Use the database URL from .env with the correct driver
    database_url = "postgresql+psycopg://wellnessway:password@localhost:5432/wellnessway_db"
    print(f"Connecting to: {database_url}")
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()
            print(f"✅ Connected to PostgreSQL: {version[0]}")
        
        # Import models to register them with Base.metadata
        from app.database.connection import Base
        from app.models.user import User, HealthGoals, DietPreferences
        from app.models.health_context import HealthContextDocument
        from app.models.diet_plan import DietPlan
        
        print("Creating all tables...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("✅ All tables created successfully!")
        
        # List created tables
        with engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = result.fetchall()
            print(f"Created tables: {[table[0] for table in tables]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = create_tables()
    if success:
        print("\n🎉 Database setup complete! You can now start your FastAPI backend.")
    else:
        print("\n💥 Database setup failed.")