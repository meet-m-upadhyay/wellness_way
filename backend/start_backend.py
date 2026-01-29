#!/usr/bin/env python3
"""
Start FastAPI backend with explicit environment configuration
"""
import os
import sys

def start_backend():
    # Set environment variables before importing anything
    os.environ["DATABASE_URL"] = "postgresql+psycopg://wellnessway:password@localhost:5432/wellnessway_db"
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"
    os.environ["ENVIRONMENT"] = "development"
    os.environ["DEBUG"] = "true"
    
    print("🚀 Starting WellnessWay Backend...")
    print(f"Database URL: {os.environ['DATABASE_URL']}")
    print(f"Redis URL: {os.environ['REDIS_URL']}")
    
    # Now import and start uvicorn
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    start_backend()