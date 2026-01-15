@echo off
title Chat TTS Reader - Test
cd /d "%~dp0"

REM Use venv if exists, otherwise global Python
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe scripts\test.py
) else (
    python scripts\test.py
)
