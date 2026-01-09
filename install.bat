@echo off
setlocal EnableDelayedExpansion

REM ============================================================================
REM   Chat TTS Reader - Installer
REM   Reads YouTube, Kick, and TikTok live chat messages via text-to-speech
REM ============================================================================

title Chat TTS Reader - Installer

REM Colors via powershell for better UX
set "CYAN=[96m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "RESET=[0m"

echo.
echo %CYAN%============================================================================%RESET%
echo %CYAN%                     Chat TTS Reader - Installer                           %RESET%
echo %CYAN%============================================================================%RESET%
echo.
echo   This installer will set up Chat TTS Reader on your system.
echo   It reads live chat messages from YouTube, Kick, and TikTok via TTS.
echo.
echo   The installer will:
echo     1. Check for Python installation
echo     2. Create a virtual environment
echo     3. Install required packages
echo     4. Configure your stream platforms
echo     5. Set up Twitch live detection (optional)
echo     6. Add to Windows startup (optional)
echo.
echo %YELLOW%  Press any key to continue or Ctrl+C to cancel...%RESET%
pause >nul

REM ============================================================================
REM   Step 1: Check Python Installation
REM ============================================================================

echo.
echo %CYAN%[Step 1/6] Checking Python installation...%RESET%
echo.

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo %RED%  ERROR: Python is not installed or not in PATH!%RESET%
    echo.
    echo   Please install Python 3.10 or higher:
    echo     1. Go to https://www.python.org/downloads/
    echo     2. Download Python 3.12 or later
    echo     3. %YELLOW%IMPORTANT: Check "Add Python to PATH" during installation!%RESET%
    echo     4. Restart this installer after installing Python
    echo.
    echo   Alternatively, install via PowerShell:
    echo     winget install Python.Python.3.12
    echo.
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo   %GREEN%Found Python %PYVER%%RESET%

REM Extract major.minor version
for /f "tokens=1,2 delims=." %%a in ("%PYVER%") do (
    set PYMAJOR=%%a
    set PYMINOR=%%b
)

if %PYMAJOR% LSS 3 (
    echo %RED%  ERROR: Python 3.10+ is required. You have Python %PYVER%%RESET%
    pause
    exit /b 1
)

if %PYMAJOR%==3 if %PYMINOR% LSS 10 (
    echo %RED%  ERROR: Python 3.10+ is required. You have Python %PYVER%%RESET%
    pause
    exit /b 1
)

echo   %GREEN%Python version OK!%RESET%

REM ============================================================================
REM   Step 2: Set Installation Directory
REM ============================================================================

echo.
echo %CYAN%[Step 2/6] Setting up installation directory...%RESET%
echo.

set "INSTALL_DIR=%~dp0"
set "INSTALL_DIR=%INSTALL_DIR:~0,-1%"

echo   Installing to: %INSTALL_DIR%
echo.

REM ============================================================================
REM   Step 3: Create Virtual Environment
REM ============================================================================

echo %CYAN%[Step 3/6] Creating virtual environment...%RESET%
echo.

if exist "%INSTALL_DIR%\venv" (
    echo   Virtual environment already exists. Recreating...
    rmdir /s /q "%INSTALL_DIR%\venv" 2>nul
)

python -m venv "%INSTALL_DIR%\venv"
if %ERRORLEVEL% NEQ 0 (
    echo %RED%  ERROR: Failed to create virtual environment!%RESET%
    pause
    exit /b 1
)

echo   %GREEN%Virtual environment created!%RESET%

REM ============================================================================
REM   Step 4: Install Dependencies
REM ============================================================================

echo.
echo %CYAN%[Step 4/6] Installing dependencies...%RESET%
echo   This may take a few minutes...
echo.

call "%INSTALL_DIR%\venv\Scripts\activate.bat"

python -m pip install --upgrade pip >nul 2>nul

pip install -r "%INSTALL_DIR%\requirements.txt"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo %YELLOW%  WARNING: Some packages may have failed to install.%RESET%
    echo   The application may still work. Continuing...
    echo.
)

echo.
echo   %GREEN%Dependencies installed!%RESET%

REM ============================================================================
REM   Step 5: Configure Platforms
REM ============================================================================

echo.
echo %CYAN%[Step 5/6] Configuring stream platforms...%RESET%
echo.
echo   You'll now set up which platforms to read chat from.
echo   You can skip platforms you don't use.
echo.
echo %YELLOW%  Press any key to start configuration...%RESET%
pause >nul
echo.

python "%INSTALL_DIR%\configure.py"

REM ============================================================================
REM   Step 6: Twitch Live Detection Setup
REM ============================================================================

echo.
echo %CYAN%[Step 6/6] Twitch Live Detection (Optional)%RESET%
echo.
echo   This feature will automatically start the TTS reader when you go live.
echo   It requires a free Twitch Developer application.
echo.

set /p SETUP_TWITCH="  Set up Twitch live detection? (Y/n): "
if /i "%SETUP_TWITCH%"=="" set SETUP_TWITCH=Y
if /i "%SETUP_TWITCH%"=="Y" (
    echo.
    python "%INSTALL_DIR%\wait_for_live.py" --setup
)

REM ============================================================================
REM   Optional: Add to Startup
REM ============================================================================

echo.
echo %CYAN%============================================================================%RESET%
echo %CYAN%                        Startup Configuration                              %RESET%
echo %CYAN%============================================================================%RESET%
echo.
echo   Would you like Chat TTS Reader to start automatically with Windows?
echo.
echo   Options:
echo     1. Yes, wait for Twitch live then start (recommended for streamers)
echo     2. Yes, start immediately on boot
echo     3. No, I'll start it manually
echo.

set /p STARTUP_CHOICE="  Enter choice (1/2/3) [1]: "
if "%STARTUP_CHOICE%"=="" set STARTUP_CHOICE=1

if "%STARTUP_CHOICE%"=="1" (
    echo.
    echo   Creating startup shortcut (wait for live^)...
    
    REM Create startup batch file
    (
        echo @echo off
        echo title Chat TTS Reader - Waiting for Live
        echo timeout /t 10 /nobreak ^>nul
        echo cd /d "%INSTALL_DIR%"
        echo call venv\Scripts\activate.bat
        echo python wait_for_live.py
        echo if %%ERRORLEVEL%% NEQ 0 pause
    ) > "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\ChatTTS-Startup.bat"
    
    echo   %GREEN%Added to startup! Will wait for Twitch live before starting.%RESET%
)

if "%STARTUP_CHOICE%"=="2" (
    echo.
    echo   Creating startup shortcut (immediate^)...
    
    REM Create startup batch file
    (
        echo @echo off
        echo title Chat TTS Reader
        echo timeout /t 10 /nobreak ^>nul
        echo cd /d "%INSTALL_DIR%"
        echo call venv\Scripts\activate.bat
        echo python main.py
        echo if %%ERRORLEVEL%% NEQ 0 pause
    ) > "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\ChatTTS-Startup.bat"
    
    echo   %GREEN%Added to startup! Will start immediately on boot.%RESET%
)

if "%STARTUP_CHOICE%"=="3" (
    echo.
    echo   %GREEN%OK, no startup shortcut created.%RESET%
    echo   You can run the app manually with: start-chat-tts.bat
)

REM ============================================================================
REM   Installation Complete
REM ============================================================================

echo.
echo %GREEN%============================================================================%RESET%
echo %GREEN%                     Installation Complete!                                %RESET%
echo %GREEN%============================================================================%RESET%
echo.
echo   Chat TTS Reader has been installed successfully!
echo.
echo   %CYAN%To start manually:%RESET%
echo     Double-click: start-chat-tts.bat
echo.
echo   %CYAN%To reconfigure platforms:%RESET%
echo     Double-click: configure.bat
echo.
echo   %CYAN%To test audio:%RESET%
echo     Double-click: test-audio.bat
echo.
echo   %CYAN%To uninstall:%RESET%
echo     Double-click: uninstall.bat
echo.
echo   %YELLOW%NOTE: YouTube/TikTok/Kick chat only works when you're actually live!%RESET%
echo.
echo %CYAN%============================================================================%RESET%
echo.

set /p START_NOW="  Would you like to test it now? (y/N): "
if /i "%START_NOW%"=="Y" (
    echo.
    echo   Starting Chat TTS Reader...
    python "%INSTALL_DIR%\main.py"
)

echo.
echo   Thanks for installing Chat TTS Reader!
echo.
pause
