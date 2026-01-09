@echo off
REM ============================================================================
REM   Chat TTS Reader - Twitch Setup
REM ============================================================================

title Chat TTS Reader - Twitch Setup

cd /d "%~dp0"

if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run install.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
python wait_for_live.py --setup

pause
