#!/usr/bin/env python3
import sys
import os
import traceback

# --- LEVEL 0 DIAGNOSTIC ---
print("🚦 [BOOT] Level 0: Script execution started", flush=True)

try:
    print("🚦 [BOOT] Level 1: Initializing paths", flush=True)
    # Ensure app directory is in path for imports
    app_dir = os.path.dirname(os.path.abspath(__file__))
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)

    print("🚦 [BOOT] Level 2: Loading environment logic", flush=True)
    # Don't load dotenv in production (Cloud Run handles it)
    is_cloud_run = os.environ.get("K_SERVICE") or os.environ.get("PORT") == "8080"
    if not is_cloud_run:
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            print("⚠️ [BOOT] python-dotenv not found, skipping...", flush=True)

    print(f"🚦 [BOOT] Level 3: Port detection (PORT={os.environ.get('PORT')})", flush=True)
    port = int(os.environ.get("PORT", 8080))

    print(f"🚦 [BOOT] Level 4: Environment detection (ENVIRONMENT={os.environ.get('ENVIRONMENT')})", flush=True)
    # Print secret lengths to debug truncation/corruption
    print(f"🚦 [DEBUG] DB_URL len: {len(os.environ.get('DATABASE_URL', ''))}", flush=True)
    print(f"🚦 [DEBUG] CORS len: {len(os.environ.get('CORS_ORIGINS', ''))}", flush=True)

    print("🚦 [BOOT] Level 5: Importing app.main (The Critical Phase)", flush=True)
    import app.main
    
    print("🚦 [BOOT] Level 6: Launching Uvicorn", flush=True)
    import uvicorn
    uvicorn.run(
        app.main.app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        workers=1
    )

except Exception as e:
    print(f"❌ [FATAL] BOOT ERROR: {str(e)}", file=sys.stderr, flush=True)
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
except BaseException as e:
    # Catch everything including SystemExit, KeyboardInterrupt
    print(f"❌ [FATAL] CRITICAL EXIT: {type(e).__name__}", file=sys.stderr, flush=True)
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)