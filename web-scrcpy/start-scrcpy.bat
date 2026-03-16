@echo off
chcp 65001 >nul
echo ============================================
echo  web-scrcpy — multi-device panel
echo ============================================

echo Checking ADB...
adb version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] ADB not found in PATH.
    echo Install: winget install Google.PlatformTools
    pause & exit /b 1
)
adb version

echo.
echo Checking scrcpy...
scrcpy --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] scrcpy not found in PATH.
    echo Install: winget install Genymobile.scrcpy
    pause & exit /b 1
)
scrcpy --version

echo.
echo Installing Python dependencies...
pip install -r "%~dp0requirements.txt" --quiet

echo.
echo Starting ADB server...
adb start-server

echo.
echo Starting web-scrcpy on port 5000...
echo Press Ctrl+C to stop.
echo.
cd /d "%~dp0"
python app.py
pause
