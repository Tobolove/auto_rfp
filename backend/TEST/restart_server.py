#!/usr/bin/env python3
"""
Script to restart the backend server with reference document endpoints
"""
import subprocess
import sys
import os

def restart_server():
    """Restart the FastAPI server"""
    print("🔄 Restarting FastAPI server with reference document endpoints...")
    
    # Change to backend directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        # Start the server
        cmd = [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--port", "8000", "--host", "0.0.0.0"]
        print(f"▶️ Starting server with command: {' '.join(cmd)}")
        
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n⏹️ Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

if __name__ == "__main__":
    restart_server()