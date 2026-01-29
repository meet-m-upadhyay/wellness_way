#!/usr/bin/env python3
"""
Run Alembic migrations with explicit database URL
"""
import os
import subprocess
import sys

def run_migrations():
    # Set the database URL explicitly
    os.environ["DATABASE_URL"] = "postgresql://wellnessway:password@localhost:5432/wellnessway_db"
    
    print("Setting DATABASE_URL to localhost...")
    print(f"DATABASE_URL: {os.environ['DATABASE_URL']}")
    
    # Run alembic upgrade
    try:
        result = subprocess.run([
            sys.executable, "-m", "alembic", "upgrade", "head"
        ], check=True, capture_output=True, text=True)
        
        print("✅ Migration successful!")
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
            
    except subprocess.CalledProcessError as e:
        print("❌ Migration failed!")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False
    
    return True

if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)