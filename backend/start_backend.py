#!/usr/bin/env python3
"""
Start FastAPI backend with explicit environment configuration
"""
import os
import sys
from dotenv import load_dotenv

def start_backend():
    # Load .env file first
    load_dotenv()
    
    # Get DATABASE_URL from .env (don't override it)
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not found in .env file!")
        sys.exit(1)
    
    # Set other environment variables
    os.environ["REDIS_URL"] = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    os.environ["ENVIRONMENT"] = os.getenv("ENVIRONMENT", "development")
    os.environ["DEBUG"] = os.getenv("DEBUG", "true")

    # Get port from .env or use default 8000
    port = int(os.getenv("PORT", 8000))
    
    # Get port from .env or use default
    port = int(os.getenv("API_PORT", "8000"))
    
    # Mask password for display
    display_url = db_url.split('@')[0].split(':')[0] + ":***@" + db_url.split('@')[1] if '@' in db_url else db_url
    
    print("🚀 Starting WellnessWay Backend...")
    print(f"📍 Database: {display_url}")
    print(f"🔴 Redis: {os.environ['REDIS_URL']}")
    print(f"🔴 Port: {port}")
    
    # Now import and start uvicorn
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    start_backend()