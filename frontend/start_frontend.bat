@echo off
echo 🚀 Starting AutoRFP Frontend (Angular)...
echo.

REM Change to frontend directory
cd /d "%~dp0"

REM Check if node_modules exists
if not exist "node_modules" (
    echo 📦 Installing dependencies...
    npm install
    echo.
)

REM Start the Angular development server
echo 🌐 Starting Angular dev server on http://localhost:4200
echo 📚 Application will open automatically in browser
echo 🔄 Hot reload enabled for development
echo.
echo Press Ctrl+C to stop the server
echo.

ng serve --port 4200 --open

pause
