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
    print("  AEGIS — AI-Enhanced Guided Investigation & Safe Remediation Platform")
    print("  Starting unified backend & dashboard on http://localhost:8000")
    from engine.main import testbed
    testbed.start_traffic()

    uvicorn.run(
        "engine.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
