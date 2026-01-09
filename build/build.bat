@echo off
setlocal EnableDelayedExpansion

REM ============================================================================
REM   Chat TTS Reader - Build Script
REM   Compiles Python to executables and creates Windows installer
REM ============================================================================

title Chat TTS Reader - Build

set "CYAN=[96m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "RESET=[0m"

echo.
echo %CYAN%============================================%RESET%
echo %CYAN%  Chat TTS Reader - Build Script%RESET%
echo %CYAN%============================================%RESET%
echo.

REM Get directories
set "BUILD_DIR=%~dp0"
set "BUILD_DIR=%BUILD_DIR:~0,-1%"
cd /d "%BUILD_DIR%\.."
set "PROJECT_DIR=%CD%"

echo   Project: %PROJECT_DIR%
echo   Build:   %BUILD_DIR%
echo.

REM Check Python
echo %CYAN%[1/4] Checking Python...%RESET%
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo %RED%  ERROR: Python not found!%RESET%
    pause
    exit /b 1
)
python --version
echo   %GREEN%OK%RESET%

REM Install dependencies
echo.
echo %CYAN%[2/4] Installing dependencies...%RESET%
pip install -r requirements.txt --quiet
pip install pyinstaller --quiet
echo   %GREEN%OK%RESET%

REM Build executables
echo.
echo %CYAN%[3/4] Building executables (this takes a few minutes)...%RESET%

echo   Building ChatTTSReader.exe...
pyinstaller --clean --noconfirm ^
    --name "ChatTTSReader" ^
    --console ^
    --add-data "platforms;platforms" ^
    --add-data "config.py;." ^
    --add-data "tts_engine.py;." ^
    --hidden-import "pyttsx3.drivers.sapi5" ^
    --hidden-import "pygame" ^
    --hidden-import "keyring.backends.Windows" ^
    --hidden-import "edge_tts" ^
    --hidden-import "aiohttp" ^
    --hidden-import "websockets" ^
    --hidden-import "brotli" ^
    --hidden-import "nest_asyncio" ^
    --distpath "%BUILD_DIR%\dist" ^
    main.py

echo   Building Configure.exe...
pyinstaller --clean --noconfirm ^
    --name "Configure" ^
    --console ^
    --add-data "config.py;." ^
    --add-data "platforms\youtube.py;platforms" ^
    --add-data "platforms\__init__.py;platforms" ^
    --hidden-import "keyring.backends.Windows" ^
    --distpath "%BUILD_DIR%\dist" ^
    configure.py

echo   Building AudioTest.exe...
pyinstaller --clean --noconfirm ^
    --name "AudioTest" ^
    --console ^
    --add-data "tts_engine.py;." ^
    --hidden-import "pyttsx3.drivers.sapi5" ^
    --hidden-import "pygame" ^
    --hidden-import "edge_tts" ^
    --distpath "%BUILD_DIR%\dist" ^
    audio_test.py

echo   Building WaitForLive.exe...
pyinstaller --clean --noconfirm ^
    --name "WaitForLive" ^
    --console ^
    --add-data "platforms;platforms" ^
    --add-data "config.py;." ^
    --add-data "tts_engine.py;." ^
    --add-data "main.py;." ^
    --hidden-import "pyttsx3.drivers.sapi5" ^
    --hidden-import "pygame" ^
    --hidden-import "keyring.backends.Windows" ^
    --hidden-import "edge_tts" ^
    --hidden-import "aiohttp" ^
    --hidden-import "websockets" ^
    --hidden-import "brotli" ^
    --hidden-import "nest_asyncio" ^
    --distpath "%BUILD_DIR%\dist" ^
    wait_for_live.py

REM Merge outputs
echo   Merging build outputs...
set "FINAL_DIST=%BUILD_DIR%\dist\ChatTTSReader-Final"
if exist "%FINAL_DIST%" rmdir /s /q "%FINAL_DIST%"
mkdir "%FINAL_DIST%"

xcopy /E /Y /Q "%BUILD_DIR%\dist\ChatTTSReader\*" "%FINAL_DIST%\" >nul
copy /Y "%BUILD_DIR%\dist\Configure\Configure.exe" "%FINAL_DIST%\" >nul
copy /Y "%BUILD_DIR%\dist\AudioTest\AudioTest.exe" "%FINAL_DIST%\" >nul
copy /Y "%BUILD_DIR%\dist\WaitForLive\WaitForLive.exe" "%FINAL_DIST%\" >nul
copy /Y "%PROJECT_DIR%\README.md" "%FINAL_DIST%\" >nul
copy /Y "%BUILD_DIR%\LICENSE.txt" "%FINAL_DIST%\" >nul

echo   %GREEN%Executables built!%RESET%

REM Build installer
echo.
echo %CYAN%[4/4] Creating installer...%RESET%

where iscc >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    set "INNO_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    if not exist "!INNO_PATH!" (
        echo %YELLOW%  Inno Setup not found. Skipping installer.%RESET%
        echo   Download from: https://jrsoftware.org/isdownload.php
        goto :done
    )
    "!INNO_PATH!" "%BUILD_DIR%\installer.iss"
) else (
    iscc "%BUILD_DIR%\installer.iss"
)

if %ERRORLEVEL% EQU 0 (
    echo   %GREEN%Installer created!%RESET%
) else (
    echo   %YELLOW%Installer creation failed.%RESET%
)

:done
echo.
echo %GREEN%============================================%RESET%
echo %GREEN%  Build Complete!%RESET%
echo %GREEN%============================================%RESET%
echo.
echo   Portable version: %BUILD_DIR%\dist\ChatTTSReader-Final\
echo   Installer:        %BUILD_DIR%\installer_output\
echo.
pause
