# AutoRFP Frontend Starter Script (PowerShell)
# This script starts the Angular development server

Write-Host "🚀 Starting AutoRFP Frontend (Angular)..." -ForegroundColor Green
Write-Host ""

# Change to the script directory (frontend folder)
Set-Location $PSScriptRoot

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
    npm install
    Write-Host ""
}

Write-Host "🌐 Starting Angular development server..." -ForegroundColor Green
Write-Host "   Frontend: http://localhost:4200" -ForegroundColor Cyan
Write-Host "   Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔄 Hot reload enabled for development" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Red
Write-Host ""

# Start Angular dev server
ng serve --port 4200 --open

Write-Host ""
Write-Host "Press any key to continue..." -ForegroundColor Yellow
Read-Host
