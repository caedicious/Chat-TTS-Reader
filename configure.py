"""
Chat TTS Reader - Configuration Utility
Interactive setup for stream URLs and settings.
"""

import sys
from colorama import init as colorama_init, Fore, Style

from config import (
    ConfigManager, 
    get_config_manager,
    YouTubeConfig,
    KickConfig,
    TikTokConfig,
    TTSConfig,
    FilterConfig
)
from platforms.youtube import extract_video_id

colorama_init()


def print_header():
    """Print application header."""
    print(f"\n{Fore.CYAN}╔══════════════════════════════════════════════╗{Style.RESET_ALL}")
    print(f"{Fore.CYAN}║       Chat TTS Reader - Configuration        ║{Style.RESET_ALL}")
    print(f"{Fore.CYAN}╚══════════════════════════════════════════════╝{Style.RESET_ALL}\n")


def print_section(title: str):
    """Print a section header."""
    print(f"\n{Fore.YELLOW}── {title} ──{Style.RESET_ALL}\n")


def get_input(prompt: str, default: str = "", required: bool = False) -> str:
    """Get user input with optional default value."""
    if default:
        display_prompt = f"{prompt} [{Fore.GREEN}{default}{Style.RESET_ALL}]: "
    else:
        display_prompt = f"{prompt}: "
    
    while True:
        value = input(display_prompt).strip()
        
        if not value and default:
            return default
        
        if not value and required:
            print(f"{Fore.RED}This field is required.{Style.RESET_ALL}")
            continue
            
        return value


def get_bool(prompt: str, default: bool = True) -> bool:
    """Get yes/no input."""
    default_str = "Y/n" if default else "y/N"
    value = input(f"{prompt} [{default_str}]: ").strip().lower()
    
    if not value:
        return default
    
    return value in ('y', 'yes', '1', 'true')


def get_int(prompt: str, default: int, min_val: int = None, max_val: int = None) -> int:
    """Get integer input with validation."""
    while True:
        value = get_input(prompt, str(default))
        try:
            num = int(value)
            if min_val is not None and num < min_val:
                print(f"{Fore.RED}Value must be at least {min_val}.{Style.RESET_ALL}")
                continue
            if max_val is not None and num > max_val:
                print(f"{Fore.RED}Value must be at most {max_val}.{Style.RESET_ALL}")
                continue
            return num
        except ValueError:
            print(f"{Fore.RED}Please enter a valid number.{Style.RESET_ALL}")


def get_float(prompt: str, default: float, min_val: float = None, max_val: float = None) -> float:
    """Get float input with validation."""
    while True:
        value = get_input(prompt, str(default))
        try:
            num = float(value)
            if min_val is not None and num < min_val:
                print(f"{Fore.RED}Value must be at least {min_val}.{Style.RESET_ALL}")
                continue
            if max_val is not None and num > max_val:
                print(f"{Fore.RED}Value must be at most {max_val}.{Style.RESET_ALL}")
                continue
            return num
        except ValueError:
            print(f"{Fore.RED}Please enter a valid number.{Style.RESET_ALL}")


def configure_youtube(config_manager: ConfigManager) -> YouTubeConfig:
    """Configure YouTube settings."""
    print_section("YouTube Live")
    
    config = config_manager.config.youtube
    
    enabled = get_bool("Enable YouTube chat?", config.enabled)
    
    if not enabled:
        return YouTubeConfig(enabled=False)
    
    print(f"\n{Fore.CYAN}Enter your YouTube Live stream URL or video ID.{Style.RESET_ALL}")
    print("Examples:")
    print("  - https://www.youtube.com/watch?v=VIDEO_ID")
    print("  - https://youtu.be/VIDEO_ID")
    print("  - VIDEO_ID")
    
    while True:
        video_url = get_input("YouTube URL/ID", config.video_id)
        
        if not video_url:
            if get_bool("Skip YouTube configuration?", False):
                return YouTubeConfig(enabled=False)
            continue
        
        video_id = extract_video_id(video_url)
        if video_id:
            print(f"{Fore.GREEN}✓ Video ID: {video_id}{Style.RESET_ALL}")
            return YouTubeConfig(enabled=True, video_id=video_id)
        else:
            print(f"{Fore.RED}Could not extract video ID. Please check the URL.{Style.RESET_ALL}")


def configure_kick(config_manager: ConfigManager) -> KickConfig:
    """Configure Kick settings."""
    print_section("Kick.com")
    
    config = config_manager.config.kick
    
    # Check for stored credentials
    try:
        from kick_auth import get_stored_cookies
        has_cookies = bool(get_stored_cookies())
        if has_cookies:
            print(f"{Fore.GREEN}✓ Kick login credentials found{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}⚠ No Kick login - may get blocked by Cloudflare{Style.RESET_ALL}")
            print(f"  Tip: Select 'Login to Kick' from the main menu for better reliability")
    except ImportError:
        has_cookies = False
    
    enabled = get_bool("\nEnable Kick chat?", config.enabled)
    
    if not enabled:
        return KickConfig(enabled=False)
    
    print(f"\n{Fore.CYAN}Enter your Kick channel name (username).{Style.RESET_ALL}")
    
    channel_name = get_input("Kick channel name", config.channel_name)
    
    if not channel_name:
        return KickConfig(enabled=False)
    
    # Clean up channel name
    channel_name = channel_name.lower().strip()
    if channel_name.startswith('https://'):
        # Extract from URL
        parts = channel_name.replace('https://kick.com/', '').split('/')
        channel_name = parts[0] if parts else channel_name
    
    print(f"{Fore.GREEN}✓ Channel: {channel_name}{Style.RESET_ALL}")
    return KickConfig(enabled=True, channel_name=channel_name)


def configure_tiktok(config_manager: ConfigManager) -> TikTokConfig:
    """Configure TikTok settings."""
    print_section("TikTok Live")
    
    config = config_manager.config.tiktok
    
    enabled = get_bool("Enable TikTok chat?", config.enabled)
    
    if not enabled:
        return TikTokConfig(enabled=False)
    
    print(f"\n{Fore.CYAN}Enter your TikTok username (with or without @).{Style.RESET_ALL}")
    
    username = get_input("TikTok username", config.username)
    
    if not username:
        return TikTokConfig(enabled=False)
    
    # Clean up username
    username = username.lstrip('@').strip()
    
    print(f"{Fore.GREEN}✓ Username: @{username}{Style.RESET_ALL}")
    return TikTokConfig(enabled=True, username=username)


def configure_tts(config_manager: ConfigManager) -> TTSConfig:
    """Configure TTS settings."""
    print_section("Text-to-Speech Settings")
    
    config = config_manager.config.tts
    
    print("Available TTS engines:")
    print(f"  1. {Fore.CYAN}pyttsx3{Style.RESET_ALL} - Windows SAPI voices (faster, works offline)")
    print(f"  2. {Fore.CYAN}edge-tts{Style.RESET_ALL} - Microsoft Edge neural voices (better quality, requires internet)")
    
    engine_choice = get_input("Choose engine (1 or 2)", "1" if config.engine == "pyttsx3" else "2")
    engine = "pyttsx3" if engine_choice == "1" else "edge-tts"
    
    rate = get_int("Speech rate (words per minute)", config.rate, 50, 400)
    volume = get_float("Volume (0.0 to 1.0)", config.volume, 0.0, 1.0)
    
    voice = ""
    edge_voice = config.edge_voice
    
    if engine == "pyttsx3":
        print(f"\n{Fore.CYAN}Available voices will be shown when the app starts.{Style.RESET_ALL}")
        print("Leave blank for default voice, or enter a partial name to match.")
        voice = get_input("Voice name (partial match)", config.voice)
    else:
        print(f"\n{Fore.CYAN}Popular Edge TTS voices:{Style.RESET_ALL}")
        print("  - en-US-GuyNeural (male, US)")
        print("  - en-US-JennyNeural (female, US)")
        print("  - en-US-AriaNeural (female, US)")
        print("  - en-GB-RyanNeural (male, UK)")
        print("  - en-AU-WilliamNeural (male, Australian)")
        edge_voice = get_input("Edge voice name", config.edge_voice)
    
    return TTSConfig(
        engine=engine,
        voice=voice,
        rate=rate,
        volume=volume,
        edge_voice=edge_voice
    )


def configure_filters(config_manager: ConfigManager) -> FilterConfig:
    """Configure message filter settings."""
    print_section("Message Filters")
    
    config = config_manager.config.filters
    
    min_length = get_int("Minimum message length", config.min_length, 0, 1000)
    max_length = get_int("Maximum message length", config.max_length, 1, 10000)
    ignore_commands = get_bool("Ignore commands (messages starting with !)?", config.ignore_commands)
    ignore_links = get_bool("Ignore messages with links?", config.ignore_links)
    
    # Blocked users
    print(f"\n{Fore.CYAN}Blocked users (comma-separated, or leave blank):{Style.RESET_ALL}")
    current_blocked = ", ".join(config.blocked_users) if config.blocked_users else ""
    blocked_users_str = get_input("Blocked users", current_blocked)
    blocked_users = [u.strip() for u in blocked_users_str.split(",") if u.strip()]
    
    # Blocked words
    print(f"\n{Fore.CYAN}Blocked words (comma-separated, or leave blank):{Style.RESET_ALL}")
    current_words = ", ".join(config.blocked_words) if config.blocked_words else ""
    blocked_words_str = get_input("Blocked words", current_words)
    blocked_words = [w.strip() for w in blocked_words_str.split(",") if w.strip()]
    
    return FilterConfig(
        min_length=min_length,
        max_length=max_length,
        ignore_commands=ignore_commands,
        ignore_links=ignore_links,
        blocked_users=blocked_users,
        blocked_words=blocked_words
    )


def configure_general(config_manager: ConfigManager):
    """Configure general settings."""
    print_section("General Settings")
    
    announce_platform = get_bool(
        "Announce platform name (e.g., 'YouTube')?",
        config_manager.config.announce_platform
    )
    announce_username = get_bool(
        "Announce username (e.g., 'JohnDoe says')?",
        config_manager.config.announce_username
    )
    queue_max_size = get_int(
        "Maximum TTS queue size",
        config_manager.config.queue_max_size,
        1, 1000
    )
    
    return announce_platform, announce_username, queue_max_size


def show_current_config(config_manager: ConfigManager):
    """Display current configuration."""
    print_section("Current Configuration")
    
    config = config_manager.config
    
    print(f"{Fore.CYAN}YouTube:{Style.RESET_ALL}")
    print(f"  Enabled: {config.youtube.enabled}")
    print(f"  Video ID: {config.youtube.video_id or '(not set)'}")
    
    print(f"\n{Fore.GREEN}Kick:{Style.RESET_ALL}")
    print(f"  Enabled: {config.kick.enabled}")
    print(f"  Channel: {config.kick.channel_name or '(not set)'}")
    
    # Check for Kick login
    try:
        from kick_auth import get_stored_cookies
        has_cookies = bool(get_stored_cookies())
        print(f"  Login: {'✓ Logged in' if has_cookies else '✗ Not logged in'}")
    except ImportError:
        pass
    
    print(f"\n{Fore.MAGENTA}TikTok:{Style.RESET_ALL}")
    print(f"  Enabled: {config.tiktok.enabled}")
    print(f"  Username: {config.tiktok.username or '(not set)'}")
    
    print(f"\n{Fore.YELLOW}TTS:{Style.RESET_ALL}")
    print(f"  Engine: {config.tts.engine}")
    print(f"  Rate: {config.tts.rate} wpm")
    print(f"  Volume: {config.tts.volume}")


def main():
    """Main configuration flow."""
    print_header()
    
    config_manager = get_config_manager()
    config_manager.load()
    
    print("This utility will help you configure Chat TTS Reader.")
    print("Press Enter to accept default values shown in [brackets].")
    
    # Check for quick setup vs full config
    print("\nConfiguration options:")
    print("  1. Quick setup (platforms only)")
    print("  2. Full configuration")
    print("  3. View current configuration")
    print(f"  4. {Fore.GREEN}Login to Kick{Style.RESET_ALL} (browser-based)")
    print("  5. Exit")
    
    choice = get_input("\nSelect option", "1")
    
    if choice == "5":
        return
    
    if choice == "4":
        # Kick login
        try:
            from kick_auth import interactive_login
            interactive_login()
            if get_bool("\nContinue to configure platforms?", True):
                choice = "1"
            else:
                return
        except ImportError as e:
            print(f"{Fore.RED}Error: Could not load Kick auth module: {e}{Style.RESET_ALL}")
            print("Make sure selenium and webdriver-manager are installed:")
            print("  pip install selenium webdriver-manager")
            return
    
    if choice == "3":
        show_current_config(config_manager)
        if get_bool("\nContinue to configure?", True):
            choice = "2"
        else:
            return
    
    # Configure platforms
    config_manager.config.youtube = configure_youtube(config_manager)
    config_manager.config.kick = configure_kick(config_manager)
    config_manager.config.tiktok = configure_tiktok(config_manager)
    
    # Full config includes TTS and filters
    if choice == "2":
        config_manager.config.tts = configure_tts(config_manager)
        config_manager.config.filters = configure_filters(config_manager)
        
        announce_platform, announce_username, queue_max_size = configure_general(config_manager)
        config_manager.config.announce_platform = announce_platform
        config_manager.config.announce_username = announce_username
        config_manager.config.queue_max_size = queue_max_size
    
    # Save configuration
    print_section("Save Configuration")
    
    show_current_config(config_manager)
    
    if get_bool("\nSave this configuration?", True):
        config_manager.save()
        print(f"\n{Fore.GREEN}✓ Configuration saved successfully!{Style.RESET_ALL}")
        print(f"\nYou can now run: {Fore.CYAN}python main.py{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.YELLOW}Configuration not saved.{Style.RESET_ALL}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Configuration cancelled.{Style.RESET_ALL}")
        sys.exit(0)
