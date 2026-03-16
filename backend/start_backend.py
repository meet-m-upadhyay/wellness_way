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
    
    # ── LOG ALL ENV VARS (DIAGNOSTIC) ────────────────────────────────
    print("📋 Environment Variables Analysis:")
    for key, value in sorted(os.environ.items()):
        # Mask sensitive values
        if any(secret in key.upper() for secret in ["KEY", "SECRET", "PASSWORD", "URL"]):
            masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
            print(f"   {key}: {masked}")
        else:
            print(f"   {key}: {value}")
    print("────────────────────────────────────────────────────────────")
    
    # Get DATABASE_URL from .env (don't override it)
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not found in .env file!")
        sys.exit(1)
    
    # Set default environment based on context
    # If PORT is 8080 (Cloud Run default) or K_SERVICE is set, we are in production
    is_cloud_run = os.environ.get("K_SERVICE") or os.environ.get("PORT") == "8080"
    
    os.environ["ENVIRONMENT"] = os.environ.get("ENVIRONMENT", "production" if is_cloud_run else "development")
    os.environ["DEBUG"] = os.environ.get("DEBUG", "false" if is_cloud_run else "true")
    os.environ["REDIS_URL"] = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    # Get port from environment (Cloud Run sets PORT=8080)
    # Default to 8000 for local development
    port = int(os.environ.get("PORT", os.getenv("PORT", 8000)))
    
    # Mask password for display
    display_url = db_url.split('@')[0].split(':')[0] + ":***@" + db_url.split('@')[1] if '@' in db_url else db_url
    
    print("🚀 Starting WellnessWay Backend...")
    print(f"📍 Database: {display_url}")
    print(f"🔴 Redis: {os.environ['REDIS_URL']}")
    print(f"🔴 Listening on Port: {port}")
    print(f"🌍 Environment: {os.environ.get('ENVIRONMENT', 'unknown')}")
    
    # Now import and start uvicorn
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
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