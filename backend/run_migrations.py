#!/usr/bin/env python3
"""
Run Alembic migrations with explicit database URL
"""
import os
import subprocess
import sys
from dotenv import load_dotenv

def run_migrations():
    # Load environment variables from .env file
    load_dotenv()
    
    # Get DATABASE_URL from environment
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        print("❌ ERROR: DATABASE_URL not found in .env file!")
        print("Please set DATABASE_URL in backend/.env")
        return False
    
    # Set it in environment for Alembic
    os.environ["DATABASE_URL"] = db_url
    
    # Mask password in output
    display_url = db_url.split('@')[0].split(':')[0] + ":***@" + db_url.split('@')[1] if '@' in db_url else db_url
    print(f"🔌 Connecting to: {display_url}")
    print(f"📍 Target: {db_url.split('@')[1] if '@' in db_url else 'unknown'}")
    
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