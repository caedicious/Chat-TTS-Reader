"""
Chat TTS Reader - Configuration Utility
Configure platforms, TTS, filters, Twitch, and startup.
"""

import sys
import os
import webbrowser

# Add scripts directory to path
scripts_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, scripts_dir)

from colorama import init as colorama_init, Fore, Style
colorama_init()

from config import (
    get_config_manager,
    YouTubeConfig,
    KickConfig,
    TikTokConfig,
    TTSConfig,
    FilterConfig
)
from platforms.youtube import extract_video_id


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    print(f"\n{Fore.CYAN}╔══════════════════════════════════════════════╗{Style.RESET_ALL}")
    print(f"{Fore.CYAN}║       Chat TTS Reader - Configuration        ║{Style.RESET_ALL}")
    print(f"{Fore.CYAN}╚══════════════════════════════════════════════╝{Style.RESET_ALL}\n")


def get_input(prompt: str, default: str = "") -> str:
    """Get user input with optional default."""
    if default:
        display = f"{prompt} [{Fore.GREEN}{default}{Style.RESET_ALL}]: "
    else:
        display = f"{prompt}: "
    
    value = input(display).strip()
    return value if value else default


def get_choice(prompt: str, valid_options: list, default: str = "") -> str:
    """Get user input and validate against valid options."""
    while True:
        value = get_input(prompt, default)
        if value in valid_options:
            return value
        print(f"{Fore.RED}  Invalid choice. Please enter one of: {', '.join(valid_options)}{Style.RESET_ALL}")


def get_bool(prompt: str, default: bool = True) -> bool:
    """Get yes/no input with validation."""
    default_str = "Y/n" if default else "y/N"
    while True:
        value = input(f"{prompt} [{default_str}]: ").strip().lower()
        if not value:
            return default
        if value in ('y', 'yes'):
            return True
        if value in ('n', 'no'):
            return False
        print(f"{Fore.RED}  Please enter 'y' or 'n'{Style.RESET_ALL}")


def get_int(prompt: str, default: int, min_val: int = None, max_val: int = None) -> int:
    """Get integer input with validation."""
    while True:
        value = get_input(prompt, str(default))
        try:
            num = int(value)
            if min_val is not None and num < min_val:
                print(f"{Fore.RED}  Must be at least {min_val}{Style.RESET_ALL}")
                continue
            if max_val is not None and num > max_val:
                print(f"{Fore.RED}  Must be at most {max_val}{Style.RESET_ALL}")
                continue
            return num
        except ValueError:
            print(f"{Fore.RED}  Please enter a number{Style.RESET_ALL}")


def get_float(prompt: str, default: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Get float input with validation."""
    while True:
        value = get_input(prompt, str(default))
        try:
            num = float(value)
            if num < min_val or num > max_val:
                print(f"{Fore.RED}  Must be between {min_val} and {max_val}{Style.RESET_ALL}")
                continue
            return num
        except ValueError:
            print(f"{Fore.RED}  Please enter a number{Style.RESET_ALL}")


# ============================================================
# Platform Configuration
# ============================================================

def configure_youtube(current: YouTubeConfig) -> YouTubeConfig:
    """Configure YouTube settings."""
    print(f"\n{Fore.RED}── YouTube ──{Style.RESET_ALL}\n")
    
    enabled = get_bool("Enable YouTube?", current.enabled)
    if not enabled:
        return YouTubeConfig(enabled=False)
    
    print(f"\n{Fore.CYAN}YouTube creates a new video ID each stream.{Style.RESET_ALL}")
    print("Options:")
    print("  1. Enter your channel (auto-detects live stream each time)")
    print("  2. Enter a specific video ID (must update each stream)")
    
    choice = get_choice("\nChoice", ["1", "2"], "1")
    
    if choice == "1":
        print(f"\n{Fore.CYAN}Enter your YouTube channel:{Style.RESET_ALL}")
        print("  Examples: @YourChannel, youtube.com/@YourChannel")
        channel = get_input("Channel", current.channel)
        return YouTubeConfig(enabled=True, channel=channel, video_id="")
    else:
        print(f"\n{Fore.CYAN}To find your video ID:{Style.RESET_ALL}")
        print("  1. Go to YouTube Studio > Go Live")
        print("  2. Copy the video ID from the URL")
        if get_bool("\nOpen YouTube Studio?", False):
            webbrowser.open("https://studio.youtube.com/channel/UC/livestreaming")
        
        video_id = get_input("Video ID", current.video_id)
        extracted = extract_video_id(video_id) if video_id else ""
        if extracted:
            print(f"{Fore.GREEN}  ✓ Video ID: {extracted}{Style.RESET_ALL}")
        return YouTubeConfig(enabled=True, channel="", video_id=extracted or video_id)


def configure_kick(current: KickConfig) -> KickConfig:
    """Configure Kick settings."""
    print(f"\n{Fore.GREEN}── Kick ──{Style.RESET_ALL}\n")
    
    enabled = get_bool("Enable Kick?", current.enabled)
    if not enabled:
        return KickConfig(enabled=False)
    
    channel = get_input("Kick channel name", current.channel_name)
    if not channel:
        return KickConfig(enabled=False)
    
    # Clean channel name
    channel = channel.lower().strip()
    if 'kick.com/' in channel:
        channel = channel.split('kick.com/')[-1].split('/')[0]
    
    print(f"{Fore.GREEN}  ✓ Channel: {channel}{Style.RESET_ALL}")
    
    # Chatroom ID options
    print(f"\n{Fore.CYAN}Chatroom ID options:{Style.RESET_ALL}")
    print("  1. Auto-detect (requires browser login first)")
    print("  2. Enter chatroom ID manually")
    print("  3. Skip (will try auto-detect at runtime)")
    
    kick_choice = get_choice("\nChoice", ["1", "2", "3"], "1")
    
    chatroom_id = current.chatroom_id
    
    if kick_choice == "1":
        print(f"\n{Fore.CYAN}Browser login will open Chrome to authenticate.{Style.RESET_ALL}")
        print(f"{Fore.CYAN}After login, chatroom ID will auto-detect when you run the app.{Style.RESET_ALL}")
        if get_bool("Start browser login?", True):
            try:
                from kick_auth import browser_login
                if browser_login():
                    print(f"{Fore.GREEN}  ✓ Kick login successful!{Style.RESET_ALL}")
                    print(f"{Fore.GREEN}  ✓ Chatroom ID will auto-detect{Style.RESET_ALL}")
                else:
                    print(f"{Fore.YELLOW}  Login cancelled or failed{Style.RESET_ALL}")
            except ImportError:
                print(f"{Fore.RED}  kick_auth.py not found{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}  Error: {e}{Style.RESET_ALL}")
    
    elif kick_choice == "2":
        print(f"\n{Fore.CYAN}To find your chatroom ID:{Style.RESET_ALL}")
        print("  1. Go to your Kick channel in browser")
        print("  2. Open DevTools (F12) > Network tab")
        print("  3. Filter by 'chatroom'")
        print("  4. Look for the 'id' in the JSON response")
        
        chatroom_str = get_input("Chatroom ID", str(chatroom_id) if chatroom_id else "")
        if chatroom_str:
            try:
                chatroom_id = int(chatroom_str)
                print(f"{Fore.GREEN}  ✓ Chatroom ID: {chatroom_id}{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED}  Invalid ID, will try auto-detect{Style.RESET_ALL}")
                chatroom_id = None
    
    else:
        print(f"{Fore.YELLOW}  Will attempt auto-detect at runtime{Style.RESET_ALL}")
        chatroom_id = None
    
    return KickConfig(enabled=True, channel_name=channel, chatroom_id=chatroom_id)


def configure_tiktok(current: TikTokConfig) -> TikTokConfig:
    """Configure TikTok settings."""
    print(f"\n{Fore.MAGENTA}── TikTok ──{Style.RESET_ALL}\n")
    
    enabled = get_bool("Enable TikTok?", current.enabled)
    if not enabled:
        return TikTokConfig(enabled=False)
    
    username = get_input("TikTok username", current.username)
    if not username:
        return TikTokConfig(enabled=False)
    
    username = username.lstrip('@').strip()
    print(f"{Fore.GREEN}  ✓ Username: @{username}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}  Note: TikTok only works when you're live{Style.RESET_ALL}")
    
    return TikTokConfig(enabled=True, username=username)


# ============================================================
# Twitch Configuration
# ============================================================

def configure_twitch():
    """Configure Twitch live detection."""
    print(f"\n{Fore.BLUE}── Twitch Live Detection ──{Style.RESET_ALL}\n")
    
    import keyring
    
    # Check current settings
    current_id = keyring.get_password("ChatTTSReader", "twitch_client_id")
    current_user = keyring.get_password("ChatTTSReader", "twitch_username")
    
    if current_user:
        print(f"  Current: {Fore.CYAN}{current_user}{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN}Twitch live detection waits until you go live,{Style.RESET_ALL}")
    print(f"{Fore.CYAN}then automatically starts the TTS reader.{Style.RESET_ALL}")
    print(f"{Fore.CYAN}(You can always press ENTER to start immediately){Style.RESET_ALL}")
    
    if not get_bool("\nConfigure Twitch?", not current_user):
        return
    
    print(f"\n{Fore.CYAN}To get a Client ID:{Style.RESET_ALL}")
    print("  1. Go to dev.twitch.tv/console/apps")
    print("  2. Register a new application")
    print("  3. Set OAuth Redirect to http://localhost")
    print("  4. Copy the Client ID")
    
    if get_bool("\nOpen Twitch Developer Console?", False):
        webbrowser.open("https://dev.twitch.tv/console/apps")
    
    client_id = get_input("\nClient ID", current_id or "")
    if not client_id:
        print(f"{Fore.YELLOW}  Skipping Twitch setup{Style.RESET_ALL}")
        return
    
    username = get_input("Twitch username", current_user or "")
    if not username:
        print(f"{Fore.YELLOW}  Skipping Twitch setup{Style.RESET_ALL}")
        return
    
    username = username.lower().strip()
    
    keyring.set_password("ChatTTSReader", "twitch_client_id", client_id)
    keyring.set_password("ChatTTSReader", "twitch_username", username)
    
    print(f"{Fore.GREEN}  ✓ Twitch configured: {username}{Style.RESET_ALL}")


# ============================================================
# TTS Configuration
# ============================================================

def configure_tts(current: TTSConfig) -> TTSConfig:
    """Configure TTS settings."""
    print(f"\n{Fore.YELLOW}── Text-to-Speech ──{Style.RESET_ALL}\n")
    
    print("TTS Engines:")
    print("  1. pyttsx3 - Windows SAPI (faster, offline)")
    print("  2. edge-tts - Microsoft Neural (better quality)")
    
    engine_choice = get_choice("Engine", ["1", "2"], "1" if current.engine == "pyttsx3" else "2")
    engine = "pyttsx3" if engine_choice == "1" else "edge-tts"
    
    rate = get_int("Speech rate (50-400)", current.rate, 50, 400)
    volume = get_float("Volume (0.0-1.0)", current.volume, 0.0, 1.0)
    
    voice = current.voice
    edge_voice = current.edge_voice
    
    if engine == "edge-tts":
        print(f"\n{Fore.CYAN}Popular Edge voices:{Style.RESET_ALL}")
        print("  en-US-GuyNeural (male)")
        print("  en-US-JennyNeural (female)")
        print("  en-US-AriaNeural (female)")
        print("  en-GB-RyanNeural (British male)")
        edge_voice = get_input("Voice", current.edge_voice)
    
    return TTSConfig(
        engine=engine,
        voice=voice,
        rate=rate,
        volume=volume,
        edge_voice=edge_voice
    )


# ============================================================
# Filter Configuration
# ============================================================

def configure_filters(current: FilterConfig) -> FilterConfig:
    """Configure message filters."""
    print(f"\n{Fore.YELLOW}── Message Filters ──{Style.RESET_ALL}\n")
    
    min_length = get_int("Min message length", current.min_length, 0, 1000)
    max_length = get_int("Max message length", current.max_length, 1, 10000)
    ignore_commands = get_bool("Ignore ! commands?", current.ignore_commands)
    ignore_links = get_bool("Ignore links?", current.ignore_links)
    
    print(f"\nBlocked users (comma-separated):")
    current_users = ", ".join(current.blocked_users) if current.blocked_users else ""
    blocked_users_str = get_input("Users", current_users)
    blocked_users = [u.strip() for u in blocked_users_str.split(",") if u.strip()]
    
    print(f"\nBlocked words (comma-separated):")
    current_words = ", ".join(current.blocked_words) if current.blocked_words else ""
    blocked_words_str = get_input("Words", current_words)
    blocked_words = [w.strip() for w in blocked_words_str.split(",") if w.strip()]
    
    return FilterConfig(
        min_length=min_length,
        max_length=max_length,
        ignore_commands=ignore_commands,
        ignore_links=ignore_links,
        blocked_users=blocked_users,
        blocked_words=blocked_words
    )


# ============================================================
# Startup Configuration
# ============================================================

def configure_startup():
    """Configure Windows startup."""
    print(f"\n{Fore.YELLOW}── Windows Startup ──{Style.RESET_ALL}\n")
    
    startup_path = os.path.join(
        os.environ.get('APPDATA', ''),
        'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup',
        'ChatTTS-Startup.bat'
    )
    
    current_exists = os.path.exists(startup_path)
    if current_exists:
        print(f"  Currently: {Fore.GREEN}Enabled{Style.RESET_ALL}")
    else:
        print(f"  Currently: {Fore.YELLOW}Disabled{Style.RESET_ALL}")
    
    print("\nOptions:")
    print("  1. Start with Windows (waits for Twitch, ENTER to bypass)")
    print("  2. Don't start with Windows")
    print("  3. Remove startup shortcut")
    
    choice = get_choice("\nChoice", ["1", "2", "3"], "2")
    
    if choice == "1":
        # Create startup batch
        # Get root directory (parent of scripts)
        root_dir = os.path.dirname(scripts_dir)
        with open(startup_path, 'w') as f:
            f.write(f'''@echo off
title Chat TTS Reader
timeout /t 10 /nobreak >nul
cd /d "{root_dir}"
if exist "venv\\Scripts\\python.exe" (
    venv\\Scripts\\python.exe scripts\\run.py
) else (
    python scripts\\run.py
)
''')
        print(f"{Fore.GREEN}  ✓ Added to Windows startup{Style.RESET_ALL}")
    
    elif choice == "3" and current_exists:
        os.remove(startup_path)
        print(f"{Fore.GREEN}  ✓ Removed from startup{Style.RESET_ALL}")
    
    else:
        if current_exists:
            os.remove(startup_path)
        print(f"{Fore.GREEN}  ✓ Won't start with Windows{Style.RESET_ALL}")


# ============================================================
# Main Menu
# ============================================================

def main():
    config_manager = get_config_manager()
    config_manager.load()
    
    while True:
        clear_screen()
        print_header()
        
        print("  1. Configure platforms (YouTube, Kick, TikTok)")
        print("  2. Configure TTS settings")
        print("  3. Configure message filters")
        print("  4. Configure Twitch live detection")
        print("  5. Configure Windows startup")
        print("  6. Kick browser login")
        print("  7. View current configuration")
        print("  8. Save and exit")
        print("  9. Exit without saving")
        
        choice = get_choice("\nChoice", ["1", "2", "3", "4", "5", "6", "7", "8", "9"], "1")
        
        if choice == "1":
            config_manager.config.youtube = configure_youtube(config_manager.config.youtube)
            config_manager.config.kick = configure_kick(config_manager.config.kick)
            config_manager.config.tiktok = configure_tiktok(config_manager.config.tiktok)
        
        elif choice == "2":
            config_manager.config.tts = configure_tts(config_manager.config.tts)
        
        elif choice == "3":
            config_manager.config.filters = configure_filters(config_manager.config.filters)
        
        elif choice == "4":
            configure_twitch()
            input("\nPress Enter to continue...")
        
        elif choice == "5":
            configure_startup()
            input("\nPress Enter to continue...")
        
        elif choice == "6":
            print(f"\n{Fore.CYAN}Starting Kick browser login...{Style.RESET_ALL}")
            try:
                from kick_auth import browser_login
                if browser_login():
                    print(f"{Fore.GREEN}  ✓ Login successful!{Style.RESET_ALL}")
                else:
                    print(f"{Fore.YELLOW}  Login cancelled{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}  Error: {e}{Style.RESET_ALL}")
            input("\nPress Enter to continue...")
        
        elif choice == "7":
            print(f"\n{Fore.CYAN}── Current Configuration ──{Style.RESET_ALL}\n")
            c = config_manager.config
            
            print(f"{Fore.RED}YouTube:{Style.RESET_ALL}")
            print(f"  Enabled: {c.youtube.enabled}")
            if c.youtube.channel:
                print(f"  Channel: {c.youtube.channel}")
            if c.youtube.video_id:
                print(f"  Video ID: {c.youtube.video_id}")
            
            print(f"\n{Fore.GREEN}Kick:{Style.RESET_ALL}")
            print(f"  Enabled: {c.kick.enabled}")
            print(f"  Channel: {c.kick.channel_name or '(not set)'}")
            if c.kick.chatroom_id:
                print(f"  Chatroom ID: {c.kick.chatroom_id}")
            
            print(f"\n{Fore.MAGENTA}TikTok:{Style.RESET_ALL}")
            print(f"  Enabled: {c.tiktok.enabled}")
            print(f"  Username: {c.tiktok.username or '(not set)'}")
            
            print(f"\n{Fore.YELLOW}TTS:{Style.RESET_ALL}")
            print(f"  Engine: {c.tts.engine}")
            print(f"  Rate: {c.tts.rate}")
            print(f"  Volume: {c.tts.volume}")
            
            # Twitch
            try:
                import keyring
                twitch_user = keyring.get_password("ChatTTSReader", "twitch_username")
                print(f"\n{Fore.BLUE}Twitch:{Style.RESET_ALL}")
                print(f"  Username: {twitch_user or '(not set)'}")
            except:
                pass
            
            input("\nPress Enter to continue...")
        
        elif choice == "8":
            config_manager.save()
            print(f"\n{Fore.GREEN}✓ Configuration saved!{Style.RESET_ALL}\n")
            break
        
        elif choice == "9":
            print(f"\n{Fore.YELLOW}Changes not saved.{Style.RESET_ALL}\n")
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Cancelled.{Style.RESET_ALL}")
