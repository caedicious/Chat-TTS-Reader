@echo off
REM ============================================================================
REM   Chat TTS Reader - Manual Start
REM ============================================================================

title Chat TTS Reader

cd /d "%~dp0"

if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run install.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
python main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Application exited with an error.
    pause
)
