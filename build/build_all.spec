# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Chat TTS Reader - All Components

from pathlib import Path
import sys

block_cipher = None
SPEC_DIR = Path(SPECPATH).parent  # Go up from build/ to main dir

# Common hidden imports
COMMON_IMPORTS = [
    'keyring',
    'keyring.backends',
    'keyring.backends.Windows',
    'colorama',
]

TTS_IMPORTS = [
    'pyttsx3',
    'pyttsx3.drivers',
    'pyttsx3.drivers.sapi5',
    'edge_tts',
    'pygame',
    'pygame.mixer',
    'pygame._sdl2',
    'pygame._sdl2.audio',
]

NETWORK_IMPORTS = [
    'aiohttp',
    'websockets',
    'brotli',
    'nest_asyncio',
    'certifi',
    'charset_normalizer',
    'multidict',
    'yarl',
    'async_timeout',
    'aiosignal',
    'frozenlist',
]

# ============================================================================
# Main Application
# ============================================================================
main_a = Analysis(
    [str(SPEC_DIR / 'main.py')],
    pathex=[str(SPEC_DIR)],
    binaries=[],
    datas=[
        (str(SPEC_DIR / 'platforms'), 'platforms'),
        (str(SPEC_DIR / 'config.py'), '.'),
        (str(SPEC_DIR / 'tts_engine.py'), '.'),
    ],
    hiddenimports=COMMON_IMPORTS + TTS_IMPORTS + NETWORK_IMPORTS,
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas'],
    cipher=block_cipher,
    noarchive=False,
)

main_pyz = PYZ(main_a.pure, main_a.zipped_data, cipher=block_cipher)

main_exe = EXE(
    main_pyz,
    main_a.scripts,
    [],
    exclude_binaries=True,
    name='ChatTTSReader',
    debug=False,
    strip=False,
    upx=True,
    console=True,
    icon=str(SPEC_DIR / 'assets' / 'icon.ico') if (SPEC_DIR / 'assets' / 'icon.ico').exists() else None,
)

# ============================================================================
# Configuration Tool
# ============================================================================
config_a = Analysis(
    [str(SPEC_DIR / 'configure.py')],
    pathex=[str(SPEC_DIR)],
    binaries=[],
    datas=[
        (str(SPEC_DIR / 'config.py'), '.'),
        (str(SPEC_DIR / 'platforms' / 'youtube.py'), 'platforms'),
        (str(SPEC_DIR / 'platforms' / '__init__.py'), 'platforms'),
    ],
    hiddenimports=COMMON_IMPORTS,
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas'],
    cipher=block_cipher,
    noarchive=False,
)

config_pyz = PYZ(config_a.pure, config_a.zipped_data, cipher=block_cipher)

config_exe = EXE(
    config_pyz,
    config_a.scripts,
    [],
    exclude_binaries=True,
    name='Configure',
    debug=False,
    strip=False,
    upx=True,
    console=True,
    icon=str(SPEC_DIR / 'assets' / 'icon.ico') if (SPEC_DIR / 'assets' / 'icon.ico').exists() else None,
)

# ============================================================================
# Audio Test Tool
# ============================================================================
audio_a = Analysis(
    [str(SPEC_DIR / 'audio_test.py')],
    pathex=[str(SPEC_DIR)],
    binaries=[],
    datas=[
        (str(SPEC_DIR / 'tts_engine.py'), '.'),
    ],
    hiddenimports=COMMON_IMPORTS + TTS_IMPORTS,
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas'],
    cipher=block_cipher,
    noarchive=False,
)

audio_pyz = PYZ(audio_a.pure, audio_a.zipped_data, cipher=block_cipher)

audio_exe = EXE(
    audio_pyz,
    audio_a.scripts,
    [],
    exclude_binaries=True,
    name='AudioTest',
    debug=False,
    strip=False,
    upx=True,
    console=True,
    icon=str(SPEC_DIR / 'assets' / 'icon.ico') if (SPEC_DIR / 'assets' / 'icon.ico').exists() else None,
)

# ============================================================================
# Wait For Live Tool
# ============================================================================
live_a = Analysis(
    [str(SPEC_DIR / 'wait_for_live.py')],
    pathex=[str(SPEC_DIR)],
    binaries=[],
    datas=[
        (str(SPEC_DIR / 'main.py'), '.'),
        (str(SPEC_DIR / 'config.py'), '.'),
        (str(SPEC_DIR / 'tts_engine.py'), '.'),
        (str(SPEC_DIR / 'platforms'), 'platforms'),
    ],
    hiddenimports=COMMON_IMPORTS + TTS_IMPORTS + NETWORK_IMPORTS,
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas'],
    cipher=block_cipher,
    noarchive=False,
)

live_pyz = PYZ(live_a.pure, live_a.zipped_data, cipher=block_cipher)

live_exe = EXE(
    live_pyz,
    live_a.scripts,
    [],
    exclude_binaries=True,
    name='WaitForLive',
    debug=False,
    strip=False,
    upx=True,
    console=True,
    icon=str(SPEC_DIR / 'assets' / 'icon.ico') if (SPEC_DIR / 'assets' / 'icon.ico').exists() else None,
)

# ============================================================================
# Collect All
# ============================================================================
coll = COLLECT(
    main_exe,
    main_a.binaries,
    main_a.zipfiles,
    main_a.datas,
    config_exe,
    config_a.binaries,
    config_a.zipfiles,
    config_a.datas,
    audio_exe,
    audio_a.binaries,
    audio_a.zipfiles,
    audio_a.datas,
    live_exe,
    live_a.binaries,
    live_a.zipfiles,
    live_a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ChatTTSReader',
)
