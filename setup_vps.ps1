# Quick setup script for VPS deployment
# Run this after cloning the repository

Write-Host "=== Telegram Score Bot - VPS Setup ===" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-Not $isAdmin) {
    Write-Host "WARNING: Not running as Administrator. Some features may not work." -ForegroundColor Yellow
    Write-Host "Right-click PowerShell and 'Run as Administrator' for full functionality." -ForegroundColor Yellow
    Write-Host ""
}

$ProjectPath = "C:\bao_cao_tinh_hinh_hoc"

# Step 1: Check Python
Write-Host "Step 1: Checking Python installation..." -ForegroundColor Green
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  Found: $pythonVersion" -ForegroundColor Cyan
} catch {
    Write-Host "  ERROR: Python not found!" -ForegroundColor Red
    Write-Host "  Please install Python from https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Step 2: Check if we're in the right directory
Write-Host ""
Write-Host "Step 2: Checking project location..." -ForegroundColor Green
$currentPath = Get-Location
if ($currentPath -ne $ProjectPath) {
    Write-Host "  Current location: $currentPath" -ForegroundColor Yellow
    Write-Host "  Expected location: $ProjectPath" -ForegroundColor Yellow
    Write-Host "  Please run this script from $ProjectPath" -ForegroundColor Yellow
    exit 1
}
Write-Host "  Location OK: $currentPath" -ForegroundColor Cyan

# Step 3: Create virtual environment
Write-Host ""
Write-Host "Step 3: Setting up virtual environment..." -ForegroundColor Green
if (Test-Path ".venv") {
    Write-Host "  Virtual environment already exists" -ForegroundColor Cyan
} else {
    Write-Host "  Creating virtual environment..." -ForegroundColor Cyan
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
    Write-Host "  Virtual environment created successfully" -ForegroundColor Green
}

# Step 4: Install dependencies
Write-Host ""
Write-Host "Step 4: Installing dependencies..." -ForegroundColor Green
& ".venv\Scripts\pip.exe" install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Failed to install dependencies" -ForegroundColor Red
    exit 1
}
Write-Host "  Dependencies installed successfully" -ForegroundColor Green

# Step 5: Check configuration files
Write-Host ""
Write-Host "Step 5: Checking configuration files..." -ForegroundColor Green

# Check .env file
if (-Not (Test-Path ".env")) {
    Write-Host "  WARNING: .env file not found!" -ForegroundColor Yellow
    Write-Host "  Creating .env template..." -ForegroundColor Cyan
    
    $envTemplate = @"
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Google Sheets Configuration
GOOGLE_SHEET_ID=your_sheet_id_here
"@
    Set-Content -Path ".env" -Value $envTemplate -Encoding UTF8
    Write-Host "  .env template created. Please edit it with your actual values." -ForegroundColor Yellow
} else {
    Write-Host "  .env file found" -ForegroundColor Cyan
}

# Check credentials.json
if (-Not (Test-Path "credentials.json")) {
    Write-Host "  WARNING: credentials.json not found!" -ForegroundColor Yellow
    Write-Host "  Please copy your Google Service Account credentials.json file to this directory" -ForegroundColor Yellow
} else {
    Write-Host "  credentials.json file found" -ForegroundColor Cyan
}

# Step 6: Create logs directory
Write-Host ""
Write-Host "Step 6: Creating logs directory..." -ForegroundColor Green
if (-Not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
    Write-Host "  Logs directory created" -ForegroundColor Cyan
} else {
    Write-Host "  Logs directory already exists" -ForegroundColor Cyan
}

# Summary
Write-Host ""
Write-Host "=== Setup Summary ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Setup completed!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Edit .env file with your bot token and sheet ID" -ForegroundColor White
Write-Host "2. Copy credentials.json to project directory" -ForegroundColor White
Write-Host "3. Test the bot: python main.py" -ForegroundColor White
Write-Host "4. Install as service: .\setup_service.ps1 -Action install" -ForegroundColor White
Write-Host ""
Write-Host "For more information, see DEPLOYMENT.md" -ForegroundColor Cyan
