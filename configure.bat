@echo off
REM ============================================================================
REM   Chat TTS Reader - Configuration
REM ============================================================================

title Chat TTS Reader - Configuration

cd /d "%~dp0"

if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run install.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
python configure.py

pause
