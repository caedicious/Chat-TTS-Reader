@echo off
title Kick Login - Chat TTS Reader
cd /d "%~dp0"

echo.
echo ========================================
echo   Kick Login - Chat TTS Reader
echo ========================================
echo.

REM Check if running from installed version
if exist "%~dp0venv\Scripts\python.exe" (
    "%~dp0venv\Scripts\python.exe" -c "from kick_auth import interactive_login; interactive_login()"
) else (
    python -c "from kick_auth import interactive_login; interactive_login()"
)

echo.
pause
