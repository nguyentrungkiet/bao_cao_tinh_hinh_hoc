# PowerShell script to start Telegram Score Bot
# Run with: powershell -ExecutionPolicy Bypass -File start_bot.ps1

$ProjectPath = "C:\bao_cao_tinh_hinh_hoc"
$VenvPath = Join-Path $ProjectPath ".venv\Scripts\python.exe"
$MainScript = Join-Path $ProjectPath "main.py"

Write-Host "Starting Telegram Score Bot..." -ForegroundColor Green
Write-Host "Project path: $ProjectPath" -ForegroundColor Cyan

# Change to project directory
Set-Location $ProjectPath

# Check if virtual environment exists
if (-Not (Test-Path $VenvPath)) {
    Write-Host "Virtual environment not found. Creating..." -ForegroundColor Yellow
    python -m venv .venv
}

# Check if requirements are installed
Write-Host "Checking dependencies..." -ForegroundColor Cyan
& $VenvPath -m pip list | Out-Null

# Start the bot
Write-Host "Starting bot..." -ForegroundColor Green
& $VenvPath $MainScript

# If script exits, wait and restart
Write-Host "Bot stopped. Restarting in 10 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 10
& $MyInvocation.MyCommand.Path
