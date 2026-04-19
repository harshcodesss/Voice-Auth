"""
Run the FastAPI server.

Usage:
    python run.py
    # or
    uvicorn src.app:app --reload --host 0.0.0.0 --port 8000
"""

import uvicorn
from src.config.settings import settings

if __name__ == "__main__":
    uvicorn.run(
        "src.app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )
