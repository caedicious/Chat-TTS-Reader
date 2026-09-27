<#
.SYNOPSIS
    Build script for Chat TTS Reader
.DESCRIPTION
    Compiles the Python app (scripts/) into five executables with PyInstaller,
    merges them into one portable folder, zips it, and creates the Windows
    installer with Inno Setup. The version comes from the VERSION file at the
    repo root; nothing else needs bumping.
.NOTES
    Requires: Python 3.10+ (the repo's venv is used when present), Inno Setup 6
#>

param(
    [switch]$SkipPyInstaller,
    [switch]$SkipInstaller,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BuildDir = $PSScriptRoot
$ScriptsDir = Join-Path $ProjectRoot "scripts"
$DistDir = Join-Path $BuildDir "dist"
$WorkDir = Join-Path $BuildDir "build"
$OutDir = Join-Path $BuildDir "installer_output"
$FinalDist = Join-Path $DistDir "ChatTTSReader-Final"

# Don't compete with a running stream for CPU
try { (Get-Process -Id $PID).PriorityClass = 'BelowNormal' } catch {}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Chat TTS Reader - Build Script" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

if ($Clean) {
    Write-Host "[Clean] Removing build artifacts..." -ForegroundColor Yellow
    foreach ($d in @($DistDir, $WorkDir, $OutDir)) {
        Remove-Item -Path $d -Recurse -Force -ErrorAction SilentlyContinue
    }
    Write-Host "[Clean] Done!" -ForegroundColor Green
    exit 0
}

# Version: single source of truth
$Version = (Get-Content (Join-Path $ProjectRoot "VERSION") -Raw).Trim()
if ($Version -notmatch '^\d+\.\d+\.\d+$') {
    Write-Host "[ERROR] VERSION must contain x.y.z, found '$Version'" -ForegroundColor Red
    exit 1
}
Write-Host "  Version: $Version" -ForegroundColor Gray

# Python: the repo's venv when it exists (install.bat creates it), else python on PATH
$Python = Join-Path $ProjectRoot "venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $cmd) {
        Write-Host "[ERROR] Python not found! Please install Python 3.10+" -ForegroundColor Red
        exit 1
    }
    $Python = $cmd.Source
}
$pyVersion = & $Python --version
Write-Host "  Python:  $pyVersion ($Python)" -ForegroundColor Gray

# Inno Setup
$Iscc = $null
$isccCmd = Get-Command iscc -ErrorAction SilentlyContinue
if ($isccCmd) { $Iscc = $isccCmd.Source } else { $Iscc = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" }
if (-not (Test-Path $Iscc)) {
    Write-Host "[WARNING] Inno Setup not found; the installer won't be created." -ForegroundColor Yellow
    Write-Host "  Download from: https://jrsoftware.org/isdownload.php" -ForegroundColor Gray
    $SkipInstaller = $true
}

if (-not $SkipPyInstaller) {
    Write-Host ""
    Write-Host "[Dependencies] Installing Python packages..." -ForegroundColor Cyan
    & $Python -m pip install --quiet -r (Join-Path $ProjectRoot "requirements.txt")
    if ($LASTEXITCODE -ne 0) { Write-Host "[ERROR] pip install -r requirements.txt failed" -ForegroundColor Red; exit 1 }
    & $Python -m pip install --quiet pyinstaller
    if ($LASTEXITCODE -ne 0) { Write-Host "[ERROR] pip install pyinstaller failed" -ForegroundColor Red; exit 1 }
    $piVersion = & $Python -m PyInstaller --version
    Write-Host "  PyInstaller $piVersion" -ForegroundColor Gray

    Write-Host ""
    Write-Host "[PyInstaller] Building executables (several minutes)..." -ForegroundColor Cyan
    Remove-Item -Path $DistDir -Recurse -Force -ErrorAction SilentlyContinue

    $common = @('--noconfirm', '--clean', '--onedir', '--console', '--log-level', 'WARN',
                '--paths', $ScriptsDir, '--distpath', $DistDir, '--workpath', $WorkDir, '--specpath', $WorkDir)
    $icon = Join-Path $ProjectRoot "assets\icon.ico"
    if (Test-Path $icon) { $common += @('--icon', $icon) }

    $tts = @('--hidden-import', 'pyttsx3.drivers.sapi5', '--hidden-import', 'pygame', '--hidden-import', 'edge_tts')
    $net = @('--hidden-import', 'aiohttp', '--hidden-import', 'websockets', '--hidden-import', 'brotli', '--hidden-import', 'nest_asyncio')
    $keyring = @('--hidden-import', 'keyring.backends.Windows')
    $browser = @('--hidden-import', 'undetected_chromedriver')

    # Executable name, entry script under scripts\, extra PyInstaller arguments
    $targets = @(
        @{ Name = 'ChatTTSReader'; Script = 'main.py';      Extra = $tts + $net + $keyring },
        @{ Name = 'WaitForLive';   Script = 'run.py';       Extra = $tts + $net + $keyring },
        @{ Name = 'Configure';     Script = 'configure.py'; Extra = $keyring + $browser },
        @{ Name = 'KickLogin';     Script = 'kick_auth.py'; Extra = $keyring + $browser },
        @{ Name = 'AudioTest';     Script = 'test.py';      Extra = $tts + $net + $keyring }
    )
    foreach ($t in $targets) {
        Write-Host "  Building $($t.Name).exe from scripts\$($t.Script)..." -ForegroundColor Gray
        $extra = $t.Extra
        & $Python -m PyInstaller $common --name $t.Name $extra (Join-Path $ScriptsDir $t.Script)
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] PyInstaller failed for $($t.Name)" -ForegroundColor Red
            exit 1
        }
    }

    # One portable folder: the five exes plus the union of their _internal folders
    # (same environment, so files they share are identical)
    Write-Host "  Merging into ChatTTSReader-Final..." -ForegroundColor Gray
    New-Item -ItemType Directory -Path $FinalDist -Force | Out-Null
    foreach ($t in $targets) {
        Copy-Item -Path (Join-Path $DistDir "$($t.Name)\*") -Destination $FinalDist -Recurse -Force
    }
    Copy-Item -Path (Join-Path $ProjectRoot "README.md") -Destination $FinalDist -Force
    Copy-Item -Path (Join-Path $BuildDir "LICENSE.txt") -Destination $FinalDist -Force
    Write-Host "  Executables built!" -ForegroundColor Green
}

if (-not (Test-Path (Join-Path $FinalDist "ChatTTSReader.exe"))) {
    Write-Host "[ERROR] $FinalDist has no ChatTTSReader.exe; build the executables first" -ForegroundColor Red
    exit 1
}
New-Item -ItemType Directory -Path $OutDir -Force | Out-Null

Write-Host ""
Write-Host "[Portable] Zipping the portable version..." -ForegroundColor Cyan
$zip = Join-Path $OutDir "ChatTTSReader-Portable-$Version.zip"
Remove-Item -Path $zip -Force -ErrorAction SilentlyContinue
Compress-Archive -Path (Join-Path $FinalDist "*") -DestinationPath $zip -CompressionLevel Optimal
Write-Host "  $zip" -ForegroundColor Gray

if (-not $SkipInstaller) {
    Write-Host ""
    Write-Host "[Inno Setup] Creating installer..." -ForegroundColor Cyan
    Push-Location $BuildDir
    & $Iscc /Q "/DMyAppVersion=$Version" "installer.iss"
    $isccExit = $LASTEXITCODE
    Pop-Location
    if ($isccExit -ne 0) {
        Write-Host "[ERROR] Installer creation failed (ISCC exit code $isccExit)" -ForegroundColor Red
        exit 1
    }
    Write-Host "  $(Join-Path $OutDir "ChatTTSReader-Setup-$Version.exe")" -ForegroundColor Gray
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Build Complete! (v$Version)" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Outputs:" -ForegroundColor Cyan
Write-Host "  Portable folder: $FinalDist" -ForegroundColor White
Write-Host "  Portable zip:    $zip" -ForegroundColor White
if (-not $SkipInstaller) {
    Write-Host "  Installer:       $(Join-Path $OutDir "ChatTTSReader-Setup-$Version.exe")" -ForegroundColor White
}
Write-Host ""
