@echo off
title Chat TTS Reader - Uninstall
cd /d "%~dp0"

echo.
echo ╔══════════════════════════════════════════════╗
echo ║       Chat TTS Reader - Uninstall            ║
echo ╚══════════════════════════════════════════════╝
echo.
echo This will remove:
echo   - Startup shortcut
echo   - Virtual environment
echo   - Stored credentials
echo   - Configuration files
echo.
echo The application folder will NOT be deleted.
echo.

set /p CONFIRM="Continue? (y/N): "
if /i not "%CONFIRM%"=="y" (
    echo Cancelled.
    pause
    exit /b 0
)

echo.
echo Removing startup shortcut...
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\ChatTTS-Startup.bat" 2>nul
echo   Done.

echo.
echo Removing credentials...
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe -c "import keyring; keyring.delete_password('ChatTTSReader', 'twitch_client_id')" 2>nul
    venv\Scripts\python.exe -c "import keyring; keyring.delete_password('ChatTTSReader', 'twitch_username')" 2>nul
) else (
    python -c "import keyring; keyring.delete_password('ChatTTSReader', 'twitch_client_id')" 2>nul
    python -c "import keyring; keyring.delete_password('ChatTTSReader', 'twitch_username')" 2>nul
)
echo   Done.

echo.
echo Removing virtual environment...
if exist "venv" rmdir /s /q venv
echo   Done.

echo.
echo Removing configuration...
if exist "%USERPROFILE%\.chat-tts-reader" rmdir /s /q "%USERPROFILE%\.chat-tts-reader"
echo   Done.

echo.
echo ════════════════════════════════════════════════
echo   Uninstall Complete!
echo ════════════════════════════════════════════════
echo.
echo Delete this folder to fully remove:
echo   %~dp0
echo.

pause
