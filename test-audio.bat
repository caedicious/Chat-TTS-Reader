@echo off
REM ============================================================================
REM   Chat TTS Reader - Audio Test
REM ============================================================================

title Chat TTS Reader - Audio Test

cd /d "%~dp0"

if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run install.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
python audio_test.py

pause
