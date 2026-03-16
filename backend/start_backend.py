#!/usr/bin/env python3
"""
Start FastAPI backend with explicit environment configuration
"""
import os
import sys
from dotenv import load_dotenv

def start_backend():
    import sys
    import os
    
    # Force line buffering
    print("🚦 [STARTUP] Phase 1: Initializing entry point...", flush=True)
    
    # Ensure app directory is in path
    app_dir = os.path.dirname(os.path.abspath(__file__))
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)
        
    try:
        # Load .env file (for local dev mostly)
        from dotenv import load_dotenv
        load_dotenv()
        
        # Set default environment based on context
        is_cloud_run = os.environ.get("K_SERVICE") or os.environ.get("PORT") == "8080"
        env = os.environ.get("ENVIRONMENT", "production" if is_cloud_run else "development")
        os.environ["ENVIRONMENT"] = env
        
        # Get port from environment (Cloud Run sets PORT=8080)
        port_raw = os.environ.get("PORT", "8080")
        port = int(port_raw)
        
        print(f"🚦 [STARTUP] Phase 2: Environment={env}, Port={port}", flush=True)
        
        # CRITICAL: Import the app object directly here (forcing any validation errors to show)
        print("🚦 [STARTUP] Phase 3: Importing app.main:app...", flush=True)
        from app.main import app
        print("🚦 [STARTUP] Phase 3.5: app.main:app imported successfully!", flush=True)
        
        # Start uvicorn with the app object directly
        import uvicorn
        print("🚦 [STARTUP] Phase 4: Launching uvicorn...", flush=True)
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            reload=False,
            log_level="info",
            workers=1,
            loop="asyncio"
        )
    except Exception as e:
        import traceback
        print(f"❌ [CRITICAL] STARTUP ERROR: {str(e)}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    start_backend()