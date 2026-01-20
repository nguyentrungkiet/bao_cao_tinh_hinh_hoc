# Script to install bot as Windows Service using NSSM
# Run this script with Administrator privileges
# Download NSSM from: https://nssm.cc/download

param(
    [Parameter(Mandatory=$false)]
    [string]$Action = "install"
)

$ServiceName = "TelegramScoreBot"
$ProjectPath = "C:\bao_cao_tinh_hinh_hoc"
$PythonExe = Join-Path $ProjectPath ".venv\Scripts\python.exe"
$MainScript = Join-Path $ProjectPath "main.py"
$NssmPath = Join-Path $ProjectPath "nssm.exe"
$LogPath = Join-Path $ProjectPath "logs"

# Create logs directory if not exists
if (-Not (Test-Path $LogPath)) {
    New-Item -ItemType Directory -Path $LogPath | Out-Null
}

# Check if NSSM exists
if (-Not (Test-Path $NssmPath)) {
    Write-Host "ERROR: NSSM not found at $NssmPath" -ForegroundColor Red
    Write-Host "Please download NSSM from https://nssm.cc/download" -ForegroundColor Yellow
    Write-Host "Extract nssm.exe (win64 version) to $ProjectPath" -ForegroundColor Yellow
    exit 1
}

switch ($Action.ToLower()) {
    "install" {
        Write-Host "Installing $ServiceName service..." -ForegroundColor Green
        
        # Remove service if exists
        $existing = & $NssmPath status $ServiceName 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Service already exists. Removing..." -ForegroundColor Yellow
            & $NssmPath stop $ServiceName
            & $NssmPath remove $ServiceName confirm
        }
        
        # Install service
        & $NssmPath install $ServiceName $PythonExe $MainScript
        & $NssmPath set $ServiceName AppDirectory $ProjectPath
        & $NssmPath set $ServiceName DisplayName "Telegram Score Bot"
        & $NssmPath set $ServiceName Description "Bot quản lý điểm học sinh qua Telegram"
        & $NssmPath set $ServiceName Start SERVICE_AUTO_START
        
        # Configure logging
        & $NssmPath set $ServiceName AppStdout "$LogPath\output.log"
        & $NssmPath set $ServiceName AppStderr "$LogPath\error.log"
        & $NssmPath set $ServiceName AppRotateFiles 1
        & $NssmPath set $ServiceName AppRotateOnline 1
        & $NssmPath set $ServiceName AppRotateBytes 10485760  # 10MB
        
        # Configure restart on failure
        & $NssmPath set $ServiceName AppExit Default Restart
        & $NssmPath set $ServiceName AppRestartDelay 5000  # 5 seconds
        
        Write-Host "Service installed successfully!" -ForegroundColor Green
        Write-Host "Starting service..." -ForegroundColor Cyan
        & $NssmPath start $ServiceName
        
        Start-Sleep -Seconds 2
        $status = & $NssmPath status $ServiceName
        Write-Host "Service status: $status" -ForegroundColor Cyan
    }
    
    "uninstall" {
        Write-Host "Uninstalling $ServiceName service..." -ForegroundColor Yellow
        & $NssmPath stop $ServiceName
        & $NssmPath remove $ServiceName confirm
        Write-Host "Service uninstalled!" -ForegroundColor Green
    }
    
    "start" {
        Write-Host "Starting $ServiceName service..." -ForegroundColor Green
        & $NssmPath start $ServiceName
        Start-Sleep -Seconds 2
        $status = & $NssmPath status $ServiceName
        Write-Host "Service status: $status" -ForegroundColor Cyan
    }
    
    "stop" {
        Write-Host "Stopping $ServiceName service..." -ForegroundColor Yellow
        & $NssmPath stop $ServiceName
        Start-Sleep -Seconds 2
        $status = & $NssmPath status $ServiceName
        Write-Host "Service status: $status" -ForegroundColor Cyan
    }
    
    "restart" {
        Write-Host "Restarting $ServiceName service..." -ForegroundColor Cyan
        & $NssmPath restart $ServiceName
        Start-Sleep -Seconds 2
        $status = & $NssmPath status $ServiceName
        Write-Host "Service status: $status" -ForegroundColor Cyan
    }
    
    "status" {
        $status = & $NssmPath status $ServiceName
        Write-Host "Service status: $status" -ForegroundColor Cyan
    }
    
    default {
        Write-Host "Usage: .\setup_service.ps1 -Action [install|uninstall|start|stop|restart|status]" -ForegroundColor Yellow
        Write-Host "Default action is 'install'" -ForegroundColor Yellow
    }
}
