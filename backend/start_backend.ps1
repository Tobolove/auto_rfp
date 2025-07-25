# AutoRFP Backend Starter Script (PowerShell)
# This script starts the FastAPI backend server with proper configuration

Write-Host "🚀 Starting AutoRFP Backend API Server..." -ForegroundColor Green
Write-Host ""

# Change to the script directory (backend folder)
Set-Location $PSScriptRoot

# Set environment variable to fix OpenMP duplicate library warning
$env:KMP_DUPLICATE_LIB_OK = "TRUE"

# Test imports first
Write-Host "🧪 Testing Python imports..." -ForegroundColor Yellow
python test_imports.py
Write-Host ""

if ($LASTEXITCODE -eq 0) {
    Write-Host "🌐 Starting FastAPI server..." -ForegroundColor Green
    Write-Host "   Server: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "   Docs:   http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host "   ReDoc:  http://localhost:8000/redoc" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🔄 Auto-reload enabled for development" -ForegroundColor Yellow
    Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Red
    Write-Host ""
    
    # Start the server
    python -m uvicorn main:app --reload --port 8000 --host 127.0.0.1
} else {
    Write-Host "❌ Import test failed. Please check the error messages above." -ForegroundColor Red
    Write-Host ""
    Write-Host "🔧 Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Install dependencies: pip install -r requirements.txt" -ForegroundColor White
    Write-Host "2. Make sure you're in the backend directory" -ForegroundColor White
    Write-Host "3. Check Python environment setup" -ForegroundColor White
}

Write-Host ""
Write-Host "Press any key to continue..."
Read-Host
