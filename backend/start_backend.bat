@echo off
echo 🚀 Starting AutoRFP Backend API Server...
echo.

REM Change to backend directory
cd /d "%~dp0"

REM Set environment variable to fix OpenMP duplicate library warning
set KMP_DUPLICATE_LIB_OK=TRUE

REM Test imports first
echo 🧪 Testing imports...
python test_imports.py
echo.

REM Start the server
echo 🌐 Starting FastAPI server on http://localhost:8000
echo 📚 API Documentation: http://localhost:8000/docs
echo 🔄 Auto-reload enabled for development
echo.
echo Press Ctrl+C to stop the server
echo.

python -m uvicorn main:app --reload --port 8000 --host 127.0.0.1

pause
