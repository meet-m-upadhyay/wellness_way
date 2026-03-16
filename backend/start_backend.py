#!/usr/bin/env python3
"""
Start FastAPI backend with explicit environment configuration
"""
import os
import sys
from dotenv import load_dotenv

def start_backend():
    # Load .env file (for local dev mostly)
    load_dotenv()
    
    # Set default environment based on context
    is_cloud_run = os.environ.get("K_SERVICE") or os.environ.get("PORT") == "8080"
    os.environ["ENVIRONMENT"] = os.environ.get("ENVIRONMENT", "production" if is_cloud_run else "development")
    
    # Get port from environment (Cloud Run sets PORT=8080)
    port = int(os.environ.get("PORT", 8080))
    
    print("🚀 Booting WellnessWay Backend...")
    print(f"📍 Target Port: {port}")
    print(f"🌍 Environment: {os.environ.get('ENVIRONMENT')}")
    
    # Start uvicorn immediately
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info",
        workers=1 # Cloud Run works best with single worker per container
    )

if __name__ == "__main__":
    try:
        start_backend()
    except Exception as e:
        import traceback
        import sys
        print(f"❌ CRITICAL STARTUP ERROR: {str(e)}")
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)