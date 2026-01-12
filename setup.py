"""
Chat TTS Reader - Complete Setup Wizard
One-stop setup for everything: dependencies, platforms, startup, and more.
"""

import subprocess
import sys
import os
import json
import shutil
import winreg
from pathlib import Path

# App constants
APP_NAME = "Chat TTS Reader"
APP_DIR = Path(__file__).parent.resolve()
CONFIG_DIR = Path.home() / ".chat-tts-reader"
CONFIG_FILE = CONFIG_DIR / "config.json"
STARTUP_DIR = Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header(title: str):
    clear_screen()
    print("\n" + "=" * 60)
    print(f"  {APP_NAME} - {title}")
    print("=" * 60 + "\n")


def print_section(title: str):
    print(f"\n── {title} ──\n")


def get_input(prompt: str, default: str = "") -> str:
    if default:
        value = input(f"  {prompt} [{default}]: ").strip()
        return value if value else default
    return input(f"  {prompt}: ").strip()


def get_bool(prompt: str, default: bool = True) -> bool:
    default_str = "Y/n" if default else "y/N"
    value = input(f"  {prompt} [{default_str}]: ").strip().lower()
    if not value:
        return default
    return value in ('y', 'yes', '1', 'true')


def get_int(prompt: str, default: int, min_val: int = None, max_val: int = None) -> int:
    while True:
        value = get_input(prompt, str(default))
        try:
            num = int(value)
            if min_val is not None and num < min_val:
                print(f"    Value must be at least {min_val}.")
                continue
            if max_val is not None and num > max_val:
                print(f"    Value must be at most {max_val}.")
                continue
            return num
        except ValueError:
            print("    Please enter a valid number.")


def get_float(prompt: str, default: float, min_val: float = None, max_val: float = None) -> float:
    while True:
        value = get_input(prompt, str(default))
        try:
            num = float(value)
            if min_val is not None and num < min_val:
                print(f"    Value must be at least {min_val}.")
                continue
            if max_val is not None and num > max_val:
                print(f"    Value must be at most {max_val}.")
                continue
            return num
        except ValueError:
            print("    Please enter a valid number.")


def run_command(cmd: list, description: str = "", capture: bool = False):
    """Run a command and optionally capture output."""
    if description:
        print(f"  {description}...")
    try:
        if capture:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0, result.stdout, result.stderr
        else:
            result = subprocess.run(cmd)
            return result.returncode == 0, "", ""
    except Exception as e:
        return False, "", str(e)


# ============================================================
# STEP 1: Dependencies
# ============================================================
def install_dependencies():
    print_header("Step 1: Installing Dependencies")
    
    print("  This will install all required Python packages.")
    print("  This may take a few minutes on first run.\n")
    
    if not get_bool("Install/update dependencies?", True):
        return True
    
    requirements_file = APP_DIR / "requirements.txt"
    if not requirements_file.exists():
        print("  ERROR: requirements.txt not found!")
        return False
    
    print("\n  Installing packages...\n")
    
    # Install main requirements
    success, _, _ = run_command(
        [sys.executable, "-m", "pip", "install", "-r", str(requirements_file), "--quiet"],
        "Installing core packages"
    )
    
    if not success:
        # Try with --user flag
        success, _, _ = run_command(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_file), "--user", "--quiet"],
            "Retrying with --user flag"
        )
    
    # Install setuptools for Python 3.12+ compatibility
    run_command(
        [sys.executable, "-m", "pip", "install", "setuptools", "--quiet"],
        "Installing setuptools"
    )
    
    if success:
        print("\n  ✓ Dependencies installed successfully!")
    else:
        print("\n  ⚠ Some packages may have failed. The app might still work.")
    
    input("\n  Press Enter to continue...")
    return True


# ============================================================
# STEP 2: Platform Configuration
# ============================================================
def load_config() -> dict:
    """Load existing config or create default."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    
    return {
        "youtube": {"enabled": False, "video_id": "", "channel": ""},
        "kick": {"enabled": False, "channel_name": "", "chatroom_id": None},
        "tiktok": {"enabled": False, "username": ""},
        "tts": {
            "engine": "edge-tts",
            "voice": "",
            "rate": 150,
            "volume": 1.0,
            "edge_voice": "en-US-GuyNeural"
        },
        "filters": {
            "min_length": 2,
            "max_length": 200,
            "ignore_commands": True,
            "ignore_links": True,
            "blocked_users": [],
            "blocked_words": []
        },
        "announce_platform": True,
        "announce_username": True,
        "queue_max_size": 10
    }


def save_config(config: dict):
    """Save config to file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


def configure_youtube(config: dict) -> dict:
    print_section("YouTube Live")
    
    current = config.get("youtube", {})
    enabled = get_bool("Enable YouTube chat?", current.get("enabled", False))
    
    if not enabled:
        return {"enabled": False, "video_id": "", "channel": ""}
    
    print("\n  YouTube creates a new video ID for each stream.")
    print("  You have two options:\n")
    print("    1. Enter your channel (auto-detects live stream each time)")
    print("    2. Enter a specific video ID (must update for each stream)\n")
    
    choice = get_input("Choose option (1 or 2)", "1")
    
    if choice == "1":
        # Channel-based auto-detection
        print("\n  Enter your YouTube channel handle (e.g., @YourChannel)")
        print("  Or channel URL (e.g., youtube.com/@YourChannel)\n")
        
        channel = get_input("YouTube channel", current.get("channel", ""))
        
        if channel:
            # Normalize
            if not channel.startswith('@') and not 'youtube.com' in channel:
                channel = '@' + channel
            print(f"\n  ✓ Channel: {channel}")
            print("    The app will auto-detect your live stream when you start it.")
            
            # Test it now?
            if get_bool("\n  Test channel detection now?", False):
                print("\n  Checking for live stream...")
                try:
                    import asyncio
                    from platforms.youtube import get_live_stream_from_channel
                    video_id = asyncio.run(get_live_stream_from_channel(channel))
                    if video_id:
                        print(f"  ✓ Found live stream: {video_id}")
                    else:
                        print("  ℹ No live stream found (this is normal if you're not live)")
                except Exception as e:
                    print(f"  ⚠ Error: {e}")
            
            return {"enabled": True, "video_id": "", "channel": channel}
        else:
            return {"enabled": False, "video_id": "", "channel": ""}
    
    else:
        # Video ID based
        print("\n  To get your current stream's video ID:")
        print("    1. Go to YouTube Studio > Go Live")
        print("    2. Copy the ID from the URL: studio.youtube.com/video/XXXXX/livestreaming")
        print("    3. Or from your live stream URL: youtube.com/watch?v=XXXXX\n")
        
        if get_bool("Open YouTube Studio in browser?", True):
            import webbrowser
            webbrowser.open("https://studio.youtube.com/channel/UC/livestreaming")
            print("\n  Browser opened! Copy the video ID from the URL.")
        
        video_input = get_input("\nYouTube Video ID or URL", current.get("video_id", ""))
        
        # Extract video ID from URL
        video_id = video_input
        if video_input:
            import re
            patterns = [
                r'(?:v=|/)([0-9A-Za-z_-]{11})(?:[&?]|$)',
                r'(?:embed/)([0-9A-Za-z_-]{11})',
                r'(?:youtu\.be/)([0-9A-Za-z_-]{11})',
                r'^([0-9A-Za-z_-]{11})$'
            ]
            for pattern in patterns:
                match = re.search(pattern, video_input)
                if match:
                    video_id = match.group(1)
                    break
            
            if video_id:
                print(f"\n  ✓ Video ID: {video_id}")
                print("    ⚠ Remember: You'll need to update this for each new stream!")
        
        return {"enabled": True, "video_id": video_id, "channel": ""}


def configure_kick(config: dict) -> dict:
    print_section("Kick.com")
    
    current = config.get("kick", {})
    enabled = get_bool("Enable Kick chat?", current.get("enabled", False))
    
    if not enabled:
        return {"enabled": False, "channel_name": "", "chatroom_id": None}
    
    print("\n  Enter your Kick channel name (username).")
    channel_name = get_input("Kick channel name", current.get("channel_name", "")).lower().strip()
    
    if not channel_name:
        return {"enabled": False, "channel_name": "", "chatroom_id": None}
    
    # Clean URL if pasted
    if "kick.com" in channel_name:
        channel_name = channel_name.split("kick.com/")[-1].split("/")[0].split("?")[0]
    
    print(f"\n  ✓ Channel: {channel_name}")
    
    # Chatroom ID
    print("\n  Kick requires a chatroom ID to connect reliably.")
    print("  To find it:")
    print("    1. Go to kick.com/" + channel_name + " in your browser")
    print("    2. Press F12 to open DevTools")
    print("    3. Go to Network tab, refresh the page")
    print("    4. Filter by 'channel' and find the API response")
    print("    5. Look for 'chatroom' -> 'id' (a number like 2517589)\n")
    
    chatroom_id = current.get("chatroom_id")
    chatroom_input = get_input("Chatroom ID (or press Enter to skip)", str(chatroom_id) if chatroom_id else "")
    
    if chatroom_input:
        try:
            chatroom_id = int(chatroom_input)
            print(f"  ✓ Chatroom ID: {chatroom_id}")
        except ValueError:
            print("  ⚠ Invalid number, skipping chatroom ID")
            chatroom_id = None
    
    # Kick login option
    print("\n  Kick may block API requests without authentication.")
    if get_bool("Would you like to login to Kick via browser?", False):
        try:
            from kick_auth import browser_login
            browser_login()
        except ImportError:
            print("  ⚠ Kick auth module not available. Skipping login.")
        except Exception as e:
            print(f"  ⚠ Login failed: {e}")
    
    return {
        "enabled": True,
        "channel_name": channel_name,
        "chatroom_id": chatroom_id
    }


def configure_tiktok(config: dict) -> dict:
    print_section("TikTok Live")
    
    current = config.get("tiktok", {})
    enabled = get_bool("Enable TikTok chat?", current.get("enabled", False))
    
    if not enabled:
        return {"enabled": False, "username": ""}
    
    print("\n  Enter your TikTok username (with or without @).")
    username = get_input("TikTok username", current.get("username", ""))
    username = username.lstrip("@").strip()
    
    if username:
        print(f"\n  ✓ Username: @{username}")
    
    return {"enabled": True, "username": username}


def configure_tts(config: dict) -> dict:
    print_section("Text-to-Speech Settings")
    
    current = config.get("tts", {})
    
    print("  Available TTS engines:")
    print("    1. edge-tts - Microsoft Edge neural voices (recommended)")
    print("    2. pyttsx3  - Windows SAPI voices (offline)\n")
    
    engine_choice = get_input("Choose engine (1 or 2)", "1" if current.get("engine") == "edge-tts" else "2")
    engine = "edge-tts" if engine_choice == "1" else "pyttsx3"
    
    rate = get_int("Speech rate (words per minute)", current.get("rate", 150), 50, 400)
    volume = get_float("Volume (0.0 to 1.0)", current.get("volume", 1.0), 0.0, 1.0)
    
    edge_voice = current.get("edge_voice", "en-US-GuyNeural")
    if engine == "edge-tts":
        print("\n  Popular Edge TTS voices:")
        print("    - en-US-GuyNeural (male, US)")
        print("    - en-US-JennyNeural (female, US)")
        print("    - en-US-AriaNeural (female, US)")
        print("    - en-GB-RyanNeural (male, UK)\n")
        edge_voice = get_input("Edge voice name", edge_voice)
    
    return {
        "engine": engine,
        "voice": current.get("voice", ""),
        "rate": rate,
        "volume": volume,
        "edge_voice": edge_voice
    }


def configure_filters(config: dict) -> dict:
    print_section("Message Filters")
    
    current = config.get("filters", {})
    
    max_length = get_int("Maximum message length", current.get("max_length", 200), 1, 1000)
    ignore_commands = get_bool("Ignore commands (messages starting with !)?", current.get("ignore_commands", True))
    ignore_links = get_bool("Ignore messages with links?", current.get("ignore_links", True))
    
    # Default blocked words
    default_blocked = [
        "kys", "kill yourself", "neck yourself",
        "follow my", "sub to my", "check out my",
        "free vbucks", "free robux"
    ]
    
    print("\n  Would you like to use the default blocked words filter?")
    print("  (Filters common spam and harmful phrases)")
    use_defaults = get_bool("Use default blocked words?", True)
    
    blocked_words = default_blocked if use_defaults else current.get("blocked_words", [])
    
    return {
        "min_length": current.get("min_length", 2),
        "max_length": max_length,
        "ignore_commands": ignore_commands,
        "ignore_links": ignore_links,
        "blocked_users": current.get("blocked_users", []),
        "blocked_words": blocked_words
    }


def configure_announcements(config: dict) -> tuple:
    print_section("Announcement Settings")
    
    print("  When reading messages, announce:")
    announce_platform = get_bool("Platform name (e.g., 'YouTube')?", config.get("announce_platform", True))
    announce_username = get_bool("Username (e.g., 'John says')?", config.get("announce_username", True))
    
    return announce_platform, announce_username


def configure_platforms():
    print_header("Step 2: Platform Configuration")
    
    config = load_config()
    
    print("  Configure which platforms to read chat from.\n")
    
    config["youtube"] = configure_youtube(config)
    config["kick"] = configure_kick(config)
    config["tiktok"] = configure_tiktok(config)
    config["tts"] = configure_tts(config)
    config["filters"] = configure_filters(config)
    
    announce_platform, announce_username = configure_announcements(config)
    config["announce_platform"] = announce_platform
    config["announce_username"] = announce_username
    
    # Save config
    save_config(config)
    print("\n  ✓ Configuration saved!")
    
    input("\n  Press Enter to continue...")
    return config


# ============================================================
# STEP 3: Twitch Live Detection
# ============================================================
def configure_twitch():
    print_header("Step 3: Twitch Live Detection (Optional)")
    
    print("  You can have the app automatically start when you go live on Twitch.")
    print("  This requires a Twitch Client ID.\n")
    
    if not get_bool("Enable Twitch live detection?", False):
        return None, None
    
    print("\n  To get a Twitch Client ID:")
    print("    1. Go to dev.twitch.tv/console/apps")
    print("    2. Click 'Register Your Application'")
    print("    3. Name: 'Chat TTS Reader' (or anything)")
    print("    4. OAuth Redirect URL: http://localhost")
    print("    5. Category: Application Integration")
    print("    6. Click Create, then Manage")
    print("    7. Copy the Client ID\n")
    
    client_id = get_input("Twitch Client ID", "")
    if not client_id:
        print("  ⚠ No Client ID provided, skipping Twitch setup.")
        return None, None
    
    username = get_input("Your Twitch username", "")
    if not username:
        print("  ⚠ No username provided, skipping Twitch setup.")
        return None, None
    
    # Save to keyring
    try:
        import keyring
        keyring.set_password("ChatTTSReader", "twitch_client_id", client_id)
        keyring.set_password("ChatTTSReader", "twitch_username", username)
        print("\n  ✓ Twitch credentials saved!")
    except Exception as e:
        print(f"\n  ⚠ Could not save credentials: {e}")
        return None, None
    
    input("\n  Press Enter to continue...")
    return client_id, username


# ============================================================
# STEP 4: Startup Configuration
# ============================================================
def configure_startup(has_twitch: bool):
    print_header("Step 4: Windows Startup Configuration")
    
    print("  Choose how the app should start:\n")
    print("    1. Don't add to startup (manual start only)")
    print("    2. Start with Windows, wait for Twitch live")
    print("       (You can press ENTER to bypass and start immediately)")
    print("    3. Start with Windows immediately")
    print()
    
    if not has_twitch:
        print("  Note: Option 2 requires Twitch setup (you skipped it).\n")
    
    choice = get_input("Select option", "1")
    
    # Remove existing startup entries
    for name in ["Chat TTS Reader", "ChatTTSReader"]:
        startup_file = STARTUP_DIR / f"{name}.bat"
        if startup_file.exists():
            startup_file.unlink()
    
    if choice == "1":
        print("\n  ✓ No startup entry created.")
        input("\n  Press Enter to continue...")
        return
    
    # Determine which script to run
    if choice == "2" and has_twitch:
        script = "wait_for_live.py"
        description = "Wait for Twitch live, then start"
    else:
        script = "main.py"
        description = "Start immediately"
    
    # Create startup batch file
    startup_content = f'''@echo off
cd /d "{APP_DIR}"
python "{APP_DIR / script}"
'''
    
    startup_file = STARTUP_DIR / "Chat TTS Reader.bat"
    try:
        with open(startup_file, 'w') as f:
            f.write(startup_content)
        print(f"\n  ✓ Startup entry created: {description}")
        print(f"    Location: {startup_file}")
    except Exception as e:
        print(f"\n  ⚠ Could not create startup entry: {e}")
    
    input("\n  Press Enter to continue...")


# ============================================================
# STEP 5: Test & Finish
# ============================================================
def test_and_finish():
    print_header("Step 5: Setup Complete!")
    
    print("  Your Chat TTS Reader is configured!\n")
    print("  Quick commands:")
    print(f"    Start app:      python \"{APP_DIR / 'main.py'}\"")
    print(f"    Reconfigure:    python \"{APP_DIR / 'setup.py'}\"")
    print(f"    Config file:    {CONFIG_FILE}")
    print()
    
    if get_bool("Would you like to test the app now?", True):
        print("\n  Starting Chat TTS Reader...")
        print("  Press Ctrl+C to stop.\n")
        print("=" * 60 + "\n")
        
        try:
            subprocess.run([sys.executable, str(APP_DIR / "main.py")])
        except KeyboardInterrupt:
            pass
    
    print("\n" + "=" * 60)
    print("  Setup complete! Enjoy your Chat TTS Reader!")
    print("=" * 60 + "\n")


# ============================================================
# MAIN SETUP WIZARD
# ============================================================
def main():
    print_header("Welcome!")
    
    print("  This wizard will help you set up Chat TTS Reader.\n")
    print("  You'll configure:")
    print("    1. Install dependencies")
    print("    2. Platform connections (YouTube, Kick, TikTok)")
    print("    3. Twitch live detection (optional)")
    print("    4. Windows startup behavior")
    print("    5. Test and finish\n")
    
    if not get_bool("Ready to begin?", True):
        print("\n  Setup cancelled. Run this script again when ready.")
        return
    
    # Step 1: Dependencies
    install_dependencies()
    
    # Step 2: Platforms
    configure_platforms()
    
    # Step 3: Twitch
    client_id, username = configure_twitch()
    has_twitch = client_id is not None and username is not None
    
    # Step 4: Startup
    configure_startup(has_twitch)
    
    # Step 5: Finish
    test_and_finish()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Setup cancelled.")
        sys.exit(0)
