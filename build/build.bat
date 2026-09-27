@echo off
REM Chat TTS Reader - Build
REM The build lives in build.ps1; this just runs it so double-clicking works.
REM Any arguments are passed through (e.g. build.bat -SkipInstaller).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build.ps1" %*
if %ERRORLEVEL% NEQ 0 pause
