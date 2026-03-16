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
set VENV=%~dp0.venv
if exist "%VENV%\Scripts\python.exe" (
    echo Using existing venv: %VENV%
) else (
    echo Creating virtual environment...
    %PY% -m venv "%VENV%"
    if errorlevel 1 (
        echo [ERROR] Failed to create venv.
        pause & exit /b 1
    )
)
set VENV_PY=%VENV%\Scripts\python.exe

echo.
echo Installing Python dependencies into venv...
"%VENV_PY%" -m pip install -r "%~dp0requirements.txt" --quiet

echo.
echo Starting ADB server...
adb start-server

echo.
echo Starting web-scrcpy on port 5000...
echo Press Ctrl+C to stop.
echo.
cd /d "%~dp0"
"%VENV_PY%" app.py
pause
