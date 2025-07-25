"""
Startup script for AutoRFP Backend API.
This script ensures proper Python path configuration and handles OpenMP conflicts.
"""

import sys
import os

# Fix OpenMP library conflict
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Add the current directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Now import the FastAPI app
from main import app

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting AutoRFP Backend API...")
    print(f"📁 Working directory: {current_dir}")
    print(f"🐍 Python path includes: {current_dir}")
    
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=[current_dir]
    )
