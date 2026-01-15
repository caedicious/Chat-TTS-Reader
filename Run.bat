@echo off
title Chat TTS Reader
cd /d "%~dp0"

REM Use venv if exists, otherwise global Python
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe scripts\run.py
) else (
    python scripts\run.py
)

if %ERRORLEVEL% NEQ 0 pause
