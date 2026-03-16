# web-scrcpy launcher (PowerShell)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " web-scrcpy - multi-device panel"          -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# Check ADB
Write-Host "`nChecking ADB..." -ForegroundColor Yellow
try {
    $adbVer = & adb version 2>&1 | Select-Object -First 1
    Write-Host "OK: $adbVer" -ForegroundColor Green
} catch {
    Write-Host "ERROR: ADB not found. Install: winget install Google.PlatformTools" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check scrcpy
Write-Host "`nChecking scrcpy..." -ForegroundColor Yellow
try {
    $scrcpyVer = & scrcpy --version 2>&1 | Select-Object -First 1
    Write-Host "OK: $scrcpyVer" -ForegroundColor Green
} catch {
    Write-Host "ERROR: scrcpy not found. Install: winget install Genymobile.scrcpy" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Find Python (py launcher -> python -> python3)
Write-Host "`nLooking for Python..." -ForegroundColor Yellow
$py = $null
foreach ($cmd in @("py", "python", "python3")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($LASTEXITCODE -eq 0 -and $ver -match "Python 3") {
            $py = $cmd
            Write-Host "OK: $ver (using '$cmd')" -ForegroundColor Green
            break
        }
    } catch {}
}
if (-not $py) {
    Write-Host "ERROR: Python 3 not found." -ForegroundColor Red
    Write-Host "Install from https://python.org or via: winget install Python.Python.3.13" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Setup venv
$venvDir = "$PSScriptRoot\.venv"
if (-not (Test-Path "$venvDir\Scripts\python.exe")) {
    Write-Host "`nCreating virtual environment..." -ForegroundColor Yellow
    & $py -m venv $venvDir
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create venv" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "OK: venv created at $venvDir" -ForegroundColor Green
} else {
    Write-Host "`nUsing existing venv: $venvDir" -ForegroundColor Green
}
$venvPy = "$venvDir\Scripts\python.exe"

# Install dependencies into venv
Write-Host "`nInstalling Python dependencies into venv..." -ForegroundColor Yellow
& $venvPy -m pip install -r "$PSScriptRoot\requirements.txt" --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: pip install failed, continuing anyway..." -ForegroundColor Yellow
}

# Start ADB server
Write-Host "`nStarting ADB server..." -ForegroundColor Yellow
& adb start-server

# Start web-scrcpy
Write-Host "`nStarting web-scrcpy on port 5000..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop.`n"
& $venvPy "$PSScriptRoot\app.py"
