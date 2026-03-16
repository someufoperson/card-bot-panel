@echo off
echo ============================================
echo  web-scrcpy - multi-device panel
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
echo Looking for Python...
py --version >nul 2>&1
if not errorlevel 1 (
    set PY=py
    goto :python_found
)
python --version >nul 2>&1
if not errorlevel 1 (
    set PY=python
    goto :python_found
)
echo [ERROR] Python 3 not found.
echo Install: winget install Python.Python.3.13
pause & exit /b 1

:python_found
%PY% --version

echo.
echo Installing Python dependencies...
%PY% -m pip install -r "%~dp0requirements.txt" --quiet

echo.
echo Starting ADB server...
adb start-server

echo.
echo Starting web-scrcpy on port 5000...
echo Press Ctrl+C to stop.
echo.
cd /d "%~dp0"
%PY% app.py
pause
