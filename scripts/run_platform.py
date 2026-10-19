"""
AEGIS Platform Launcher Script
Starts the Uvicorn ASGI server hosting the FastAPI backend and built React dashboard.
"""

import sys
import os
import traceback
import uvicorn

# Ensure root directory is on Python path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    print("=" * 70, flush=True)
    print("  AEGIS — AI-Enhanced Guided Investigation & Safe Remediation Platform", flush=True)
    print(f"  Binding to 0.0.0.0:{port} (PORT env={os.environ.get('PORT', 'default:8000')})", flush=True)
    print("=" * 70, flush=True)

    try:
        print("  Importing FastAPI app from engine.main...", flush=True)
        from engine.main import app
        print("  FastAPI app imported successfully! Launching Uvicorn ASGI server...", flush=True)
        sys.stdout.flush()
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info",
            access_log=True
        )
    except BaseException as e:
        print(f"FATAL: Application failed to start: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        sys.exit(1)
