"""
AEGIS Platform Launcher Script
Starts the Uvicorn ASGI server hosting the FastAPI backend and built React dashboard.
"""

import uvicorn
import sys
import os

# Add root directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

if __name__ == '__main__':
    print("=" * 70)
    port = int(os.environ.get("PORT", 8000))
    print(f"  Starting unified backend & dashboard on http://0.0.0.0:{port}")
    uvicorn.run(
        "engine.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )
