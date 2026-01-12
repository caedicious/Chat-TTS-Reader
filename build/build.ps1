<# 
.SYNOPSIS
    Build script for Chat TTS Reader
.DESCRIPTION
    Compiles the Python application and creates a Windows installer
.NOTES
    Requires: Python 3.10+, PyInstaller, Inno Setup
#>

param(
    [switch]$SkipPyInstaller,
    [switch]$SkipInstaller,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BuildDir = $PSScriptRoot
$DistDir = Join-Path $BuildDir "dist"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Chat TTS Reader - Build Script" -ForegroundColor Cyan  
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Clean build
if ($Clean) {
    Write-Host "[Clean] Removing build artifacts..." -ForegroundColor Yellow
    Remove-Item -Path (Join-Path $BuildDir "dist") -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Path (Join-Path $BuildDir "build") -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Path (Join-Path $BuildDir "installer_output") -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Path (Join-Path $BuildDir "*.spec") -Force -ErrorAction SilentlyContinue
    Write-Host "[Clean] Done!" -ForegroundColor Green
    exit 0
}

# Check requirements
Write-Host "[Check] Verifying requirements..." -ForegroundColor Cyan

# Python
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "[ERROR] Python not found! Please install Python 3.10+" -ForegroundColor Red
    exit 1
}
$pyVersion = & python --version
Write-Host "  Found: $pyVersion" -ForegroundColor Gray

# PyInstaller
$pyinstaller = & python -c "import PyInstaller; print(PyInstaller.__version__)" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[Install] Installing PyInstaller..." -ForegroundColor Yellow
    & pip install pyinstaller
}
Write-Host "  PyInstaller: OK" -ForegroundColor Gray

# Inno Setup
$innoSetup = Get-Command iscc -ErrorAction SilentlyContinue
if (-not $innoSetup) {
    $innoPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    if (Test-Path $innoPath) {
        $innoSetup = $innoPath
    } else {
        Write-Host "[WARNING] Inno Setup not found. Installer won't be created." -ForegroundColor Yellow
        Write-Host "  Download from: https://jrsoftware.org/isdownload.php" -ForegroundColor Gray
        $SkipInstaller = $true
    }
}
if (-not $SkipInstaller) {
    Write-Host "  Inno Setup: OK" -ForegroundColor Gray
}

# Install dependencies
Write-Host ""
Write-Host "[Dependencies] Installing Python packages..." -ForegroundColor Cyan
Push-Location $ProjectRoot
& pip install -r requirements.txt --quiet
& pip install pyinstaller --quiet
Pop-Location
Write-Host "  Dependencies installed!" -ForegroundColor Gray

# Build with PyInstaller
if (-not $SkipPyInstaller) {
    Write-Host ""
    Write-Host "[PyInstaller] Building executables..." -ForegroundColor Cyan
    Write-Host "  This may take several minutes..." -ForegroundColor Gray
    
    Push-Location $ProjectRoot
    
    # Build main app
    Write-Host "  Building ChatTTSReader.exe..." -ForegroundColor Gray
    & pyinstaller --clean --noconfirm `
        --name "ChatTTSReader" `
        --console `
        --add-data "platforms;platforms" `
        --add-data "config.py;." `
        --add-data "tts_engine.py;." `
        --add-data "kick_auth.py;." `
        --hidden-import "pyttsx3.drivers.sapi5" `
        --hidden-import "pygame" `
        --hidden-import "keyring.backends.Windows" `
        --hidden-import "edge_tts" `
        --hidden-import "aiohttp" `
        --hidden-import "websockets" `
        --hidden-import "brotli" `
        --hidden-import "nest_asyncio" `
        --distpath "$DistDir" `
        main.py
    
    # Build configure
    Write-Host "  Building Configure.exe..." -ForegroundColor Gray
    & pyinstaller --clean --noconfirm `
        --name "Configure" `
        --console `
        --add-data "config.py;." `
        --add-data "kick_auth.py;." `
        --add-data "platforms/youtube.py;platforms" `
        --add-data "platforms/__init__.py;platforms" `
        --hidden-import "keyring.backends.Windows" `
        --hidden-import "undetected_chromedriver" `
        --distpath "$DistDir" `
        configure.py
    
    # Build Kick Login
    Write-Host "  Building KickLogin.exe..." -ForegroundColor Gray
    & pyinstaller --clean --noconfirm `
        --name "KickLogin" `
        --console `
        --add-data "kick_auth.py;." `
        --hidden-import "keyring.backends.Windows" `
        --hidden-import "undetected_chromedriver" `
        --distpath "$DistDir" `
        -c -y `
        kick_auth.py
    
    # Build audio test
    Write-Host "  Building AudioTest.exe..." -ForegroundColor Gray
    & pyinstaller --clean --noconfirm `
        --name "AudioTest" `
        --console `
        --add-data "tts_engine.py;." `
        --hidden-import "pyttsx3.drivers.sapi5" `
        --hidden-import "pygame" `
        --hidden-import "edge_tts" `
        --distpath "$DistDir" `
        audio_test.py
    
    # Build wait for live
    Write-Host "  Building WaitForLive.exe..." -ForegroundColor Gray
    & pyinstaller --clean --noconfirm `
        --name "WaitForLive" `
        --console `
        --add-data "platforms;platforms" `
        --add-data "config.py;." `
        --add-data "tts_engine.py;." `
        --add-data "main.py;." `
        --hidden-import "pyttsx3.drivers.sapi5" `
        --hidden-import "pygame" `
        --hidden-import "keyring.backends.Windows" `
        --hidden-import "edge_tts" `
        --hidden-import "aiohttp" `
        --hidden-import "websockets" `
        --hidden-import "brotli" `
        --hidden-import "nest_asyncio" `
        --distpath "$DistDir" `
        wait_for_live.py
    
    Pop-Location
    
    # Merge all dist folders into one
    Write-Host "  Merging build outputs..." -ForegroundColor Gray
    $FinalDist = Join-Path $DistDir "ChatTTSReader-Final"
    New-Item -ItemType Directory -Path $FinalDist -Force | Out-Null
    
    # Copy all unique files
    Get-ChildItem -Path "$DistDir\ChatTTSReader" -Recurse | Copy-Item -Destination $FinalDist -Force
    Copy-Item -Path "$DistDir\Configure\Configure.exe" -Destination $FinalDist -Force
    Copy-Item -Path "$DistDir\KickLogin\KickLogin.exe" -Destination $FinalDist -Force
    Copy-Item -Path "$DistDir\AudioTest\AudioTest.exe" -Destination $FinalDist -Force
    Copy-Item -Path "$DistDir\WaitForLive\WaitForLive.exe" -Destination $FinalDist -Force
    
    # Copy additional files
    Copy-Item -Path (Join-Path $ProjectRoot "README.md") -Destination $FinalDist -Force
    Copy-Item -Path (Join-Path $BuildDir "LICENSE.txt") -Destination $FinalDist -Force -ErrorAction SilentlyContinue
    
    Write-Host "  Executables built successfully!" -ForegroundColor Green
}

# Build installer with Inno Setup
if (-not $SkipInstaller) {
    Write-Host ""
    Write-Host "[Inno Setup] Creating installer..." -ForegroundColor Cyan
    
    # Ensure required files exist
    if (-not (Test-Path (Join-Path $BuildDir "LICENSE.txt"))) {
        "MIT License - See README for details" | Out-File (Join-Path $BuildDir "LICENSE.txt")
    }
    if (-not (Test-Path (Join-Path $BuildDir "INSTALL_INFO.txt"))) {
        @"
Chat TTS Reader Installation

This will install Chat TTS Reader on your computer.

Features:
- Read YouTube, Kick, and TikTok live chat via text-to-speech
- Automatic Twitch live detection
- High-quality Microsoft Edge neural voices
- Customizable filters and settings

After installation, run Configure to set up your streaming platforms.
"@ | Out-File (Join-Path $BuildDir "INSTALL_INFO.txt")
    }
    
    # Update installer script paths
    $issContent = Get-Content (Join-Path $BuildDir "installer.iss") -Raw
    $issContent = $issContent -replace 'Source: "dist\\ChatTTSReader\\', "Source: `"$DistDir\ChatTTSReader-Final\"
    $issContent | Out-File (Join-Path $BuildDir "installer_temp.iss") -Encoding UTF8
    
    # Run Inno Setup
    Push-Location $BuildDir
    if ($innoSetup -is [System.Management.Automation.CommandInfo]) {
        & iscc "installer.iss"
    } else {
        & $innoSetup "installer.iss"
    }
    Pop-Location
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Installer created successfully!" -ForegroundColor Green
        $installerPath = Get-ChildItem -Path (Join-Path $BuildDir "installer_output") -Filter "*.exe" | Select-Object -First 1
        Write-Host ""
        Write-Host "  Output: $($installerPath.FullName)" -ForegroundColor White
    } else {
        Write-Host "  Installer creation failed!" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Build Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Outputs:" -ForegroundColor Cyan
Write-Host "  Portable: $DistDir\ChatTTSReader-Final\" -ForegroundColor White
if (-not $SkipInstaller) {
    Write-Host "  Installer: $BuildDir\installer_output\" -ForegroundColor White
}
Write-Host ""
