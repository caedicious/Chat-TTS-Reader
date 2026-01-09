@echo off
setlocal EnableDelayedExpansion

REM ============================================================================
REM   Chat TTS Reader - Uninstaller
REM ============================================================================

title Chat TTS Reader - Uninstaller

set "CYAN=[96m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "RESET=[0m"

echo.
echo %CYAN%============================================================================%RESET%
echo %CYAN%                    Chat TTS Reader - Uninstaller                          %RESET%
echo %CYAN%============================================================================%RESET%
echo.
echo   This will remove Chat TTS Reader from your system.
echo.
echo   The following will be removed:
echo     - Startup shortcut (if created)
echo     - Virtual environment
echo     - Stored credentials (Twitch, API keys)
echo.
echo   %YELLOW%The application files in this folder will NOT be deleted.%RESET%
echo   You can delete this folder manually if desired.
echo.

set /p CONFIRM="  Are you sure you want to uninstall? (y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo.
    echo   Uninstall cancelled.
    pause
    exit /b 0
)

echo.
echo   Removing startup shortcut...
if exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\ChatTTS-Startup.bat" (
    del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\ChatTTS-Startup.bat"
    echo   %GREEN%Startup shortcut removed.%RESET%
) else (
    echo   No startup shortcut found.
)

echo.
echo   Removing stored credentials...
cd /d "%~dp0"
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    python -c "import keyring; keyring.delete_password('ChatTTSReader', 'twitch_client_id')" 2>nul
    python -c "import keyring; keyring.delete_password('ChatTTSReader', 'twitch_username')" 2>nul
    python -c "import keyring; keyring.delete_password('ChatTTSReader', 'youtube_api_key')" 2>nul
    python -c "import keyring; keyring.delete_password('ChatTTSReader', 'kick_auth_token')" 2>nul
    echo   %GREEN%Credentials removed.%RESET%
)

echo.
echo   Removing virtual environment...
if exist "%~dp0venv" (
    rmdir /s /q "%~dp0venv"
    echo   %GREEN%Virtual environment removed.%RESET%
) else (
    echo   No virtual environment found.
)

echo.
echo   Removing configuration...
if exist "%USERPROFILE%\.chat-tts-reader" (
    rmdir /s /q "%USERPROFILE%\.chat-tts-reader"
    echo   %GREEN%Configuration removed.%RESET%
) else (
    echo   No configuration found.
)

echo.
echo %GREEN%============================================================================%RESET%
echo %GREEN%                      Uninstall Complete!                                  %RESET%
echo %GREEN%============================================================================%RESET%
echo.
echo   Chat TTS Reader has been uninstalled.
echo.
echo   You can delete this folder to completely remove the application:
echo     %~dp0
echo.
pause
