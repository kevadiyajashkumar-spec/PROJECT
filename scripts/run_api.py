"""
Script to run the FastAPI server.
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

if __name__ == "__main__":
    # Run FastAPI server
    uvicorn.run(
        "api.api:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
