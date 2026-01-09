# Building Chat TTS Reader

This document explains how to compile Chat TTS Reader into a standalone Windows application.

## Quick Start (No Compilation)

If you just want to use the app without compiling:
1. Run `install.bat`
2. Follow the prompts

This uses Python directly (requires Python 3.10+ installed).

---

## Building Compiled Executables

### Prerequisites

1. **Python 3.10+** - [Download](https://python.org/downloads)
2. **Inno Setup 6** (optional, for installer) - [Download](https://jrsoftware.org/isdownload.php)

### Build Steps

#### Option 1: PowerShell (Recommended)

```powershell
cd build
.\build.ps1
```

#### Option 2: Batch File

```cmd
cd build
build.bat
```

### Build Outputs

After building:

- **Portable Version**: `build/dist/ChatTTSReader-Final/`
  - Can be copied anywhere and run directly
  - No installation required

- **Windows Installer**: `build/installer_output/ChatTTSReader-Setup-x.x.x.exe`
  - Professional installer with Start Menu shortcuts
  - Auto-start options
  - Proper uninstaller

---

## Build Options

### PowerShell Script Options

```powershell
# Full build (executables + installer)
.\build.ps1

# Skip PyInstaller (only rebuild installer)
.\build.ps1 -SkipPyInstaller

# Skip installer (only build executables)
.\build.ps1 -SkipInstaller

# Clean build artifacts
.\build.ps1 -Clean
```

---

## Project Structure

```
Chat-TTS-Reader/
├── main.py              # Main application
├── configure.py         # Configuration wizard
├── audio_test.py        # Audio testing utility
├── wait_for_live.py     # Twitch live detection
├── config.py            # Configuration management
├── tts_engine.py        # TTS engine abstraction
├── requirements.txt     # Python dependencies
├── platforms/           # Chat platform handlers
│   ├── youtube.py
│   ├── kick.py
│   ├── tiktok.py
│   └── base.py
├── assets/              # Icons and resources
│   └── icon.ico         # (add your own icon here)
└── build/               # Build scripts
    ├── build.ps1        # PowerShell build script
    ├── build.bat        # Batch build script
    ├── installer.iss    # Inno Setup script
    ├── LICENSE.txt
    └── INSTALL_INFO.txt
```

---

## Custom Icon

To use a custom icon:
1. Create a 256x256 (or multi-size) `.ico` file
2. Save it as `assets/icon.ico`
3. Rebuild

---

## Troubleshooting

### PyInstaller Issues

**"Module not found" errors:**
- Add missing modules to `--hidden-import` in the build script

**Large executable size:**
- This is normal - PyInstaller bundles Python and all dependencies
- Typical size: 50-100 MB

### Inno Setup Issues

**"ISCC not found":**
- Install Inno Setup 6 from https://jrsoftware.org/isdownload.php
- Or add it to your PATH

---

## Release Checklist

1. Update version in `VERSION` file
2. Update version in `build/installer.iss`
3. Run full build: `.\build.ps1`
4. Test the portable version
5. Test the installer
6. Create GitHub release with:
   - `ChatTTSReader-Setup-x.x.x.exe` (installer)
   - `ChatTTSReader-Portable-x.x.x.zip` (zipped portable folder)
