import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text

try:
    engine = create_engine("postgresql+psycopg://wellnessway:password@localhost:5432/wellnessway_db")
    
    with engine.connect() as conn:
        # Delete David Rodriguez by name
        result = conn.execute(text("DELETE FROM users WHERE name = 'David Rodriguez'"))
        conn.commit()
        print(f"✅ Deleted {result.rowcount} user(s) named 'David Rodriguez'")
        
except Exception as e:
    print(f"❌ Error: {e}")
