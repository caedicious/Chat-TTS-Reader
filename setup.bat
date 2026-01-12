@echo off
title Chat TTS Reader - Setup Wizard
cd /d "%~dp0"

echo.
echo ========================================
echo   Chat TTS Reader - Setup Wizard
echo ========================================
echo.

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo.
    echo Please install Python 3.10+ from:
    echo   https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

REM Run setup
python setup.py

pause
