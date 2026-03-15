import sys
import os
sys.path.append(os.getcwd())
from sqlalchemy import create_engine, text
from app.core.config import get_settings

def add_missing_columns():
    settings = get_settings()
    engine = create_engine(settings.database.url)
    
    with engine.connect() as conn:
        print("Checking/Adding columns to diet_preferences table...")
        
        # Add cuisine column
        try:
            conn.execute(text("ALTER TABLE diet_preferences ADD COLUMN IF NOT EXISTS cuisine VARCHAR(50) DEFAULT 'indian' NOT NULL"))
            print("Added 'cuisine' column successfully.")
        except Exception as e:
            print(f"Error adding 'cuisine' column: {e}")
            
        # Add reuse_ingredients column
        try:
            conn.execute(text("ALTER TABLE diet_preferences ADD COLUMN IF NOT EXISTS reuse_ingredients BOOLEAN DEFAULT FALSE NOT NULL"))
            print("Added 'reuse_ingredients' column successfully.")
        except Exception as e:
            print(f"Error adding 'reuse_ingredients' column: {e}")
            
        conn.commit()
        print("Migration complete!")

if __name__ == "__main__":
    add_missing_columns()
