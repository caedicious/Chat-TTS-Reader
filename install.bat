@echo off
setlocal EnableDelayedExpansion
title Chat TTS Reader - Install

cd /d "%~dp0"

echo.
echo ╔══════════════════════════════════════════════╗
echo ║     Chat TTS Reader - First Time Setup       ║
echo ╚══════════════════════════════════════════════╝
echo.

REM Check Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found!
    echo.
    echo Install Python 3.10+ from https://python.org
    echo Make sure to check "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

python --version
echo.

REM Create virtual environment
echo [1/3] Creating virtual environment...
if exist "venv" (
    echo   Removing old venv...
    rmdir /s /q venv
)
python -m venv venv
if %ERRORLEVEL% NEQ 0 (
    echo   ERROR: Failed to create venv
    pause
    exit /b 1
)
echo   Done!
echo.

REM Install dependencies
echo [2/3] Installing dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo   WARNING: Some packages may have failed
)
echo   Done!
echo.

REM Run configuration
echo [3/3] Configuration...
echo.
python scripts\configure.py

echo.
echo ════════════════════════════════════════════════
echo   Installation Complete!
echo ════════════════════════════════════════════════
echo.
echo   To start: Run.bat
echo   To configure: Configure.bat
echo   To test: Test.bat
echo.

set /p START_NOW="Start now? (y/N): "
if /i "%START_NOW%"=="y" (
    python scripts\run.py
)

pause
