$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONUTF8 = "1"

# Find proper python executable on Windows
$PYTHON = "python"
$userPython = "$env:LOCALAPPDATA\Python\bin\python.exe"
if (Test-Path $userPython) {
    $PYTHON = $userPython
} else {
    $pyCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pyCmd -or $pyCmd.Source -match "WindowsApps") {
        $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
        if ($pyLauncher) { $PYTHON = "py" }
    }
}

# Ensure logs directory exists
$LOGS = Join-Path $ROOT "logs"
if (-not (Test-Path $LOGS)) {
    New-Item -ItemType Directory -Path $LOGS -Force | Out-Null
}

# Free busy port for mail server
$conn = Get-NetTCPConnection -LocalPort 25 -ErrorAction SilentlyContinue
if ($conn) {
    Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
}

# Start Discord bot in foreground
Write-Host "[*] Starting Discord bot..." -ForegroundColor Cyan
Start-Process $PYTHON "`"$ROOT\bot.py`"" -NoNewWindow -Wait