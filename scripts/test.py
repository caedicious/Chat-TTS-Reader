"""
Chat TTS Reader - Connection & Audio Test
Tests all configured platforms and TTS audio output.
"""

import asyncio
import sys
import os

# Add scripts directory to path
scripts_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, scripts_dir)

from colorama import init as colorama_init, Fore, Style
colorama_init()


def print_header(title: str):
    print(f"\n{Fore.CYAN}{'═' * 50}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  {title}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'═' * 50}{Style.RESET_ALL}\n")


def print_result(name: str, success: bool, message: str = ""):
    if success:
        print(f"  {Fore.GREEN}✓{Style.RESET_ALL} {name}: {Fore.GREEN}OK{Style.RESET_ALL}")
    else:
        print(f"  {Fore.RED}✗{Style.RESET_ALL} {name}: {Fore.RED}FAILED{Style.RESET_ALL}")
    if message:
        print(f"    {Fore.YELLOW}{message}{Style.RESET_ALL}")


async def test_youtube(config) -> bool:
    """Test YouTube connection."""
    if not config.youtube.enabled:
        print(f"  {Fore.YELLOW}─{Style.RESET_ALL} YouTube: {Fore.YELLOW}Disabled{Style.RESET_ALL}")
        return True
    
    from platforms.youtube import get_live_video_id_sync, extract_video_id
    
    video_id = None
    source = ""
    
    # Try video ID first
    if config.youtube.video_id:
        video_id = extract_video_id(config.youtube.video_id)
        source = f"video ID: {video_id}"
    
    # Try channel auto-detect
    if not video_id and config.youtube.channel:
        print(f"    Checking channel {config.youtube.channel}...")
        video_id = get_live_video_id_sync(config.youtube.channel)
        if video_id:
            source = f"auto-detected from {config.youtube.channel}"
    
    if video_id:
        # Try to connect
        from platforms.youtube import YouTubeChatHandler
        handler = YouTubeChatHandler(video_id)
        
        try:
            success = await handler.connect()
            await handler.disconnect()
            print_result("YouTube", success, source if success else "Could not connect to chat")
            return success
        except Exception as e:
            print_result("YouTube", False, str(e))
            return False
    else:
        if config.youtube.channel:
            print_result("YouTube", False, f"No live stream found for {config.youtube.channel}")
        else:
            print_result("YouTube", False, "No video ID or channel configured")
        return False


async def test_kick(config) -> bool:
    """Test Kick connection."""
    if not config.kick.enabled or not config.kick.channel_name:
        print(f"  {Fore.YELLOW}─{Style.RESET_ALL} Kick: {Fore.YELLOW}Disabled{Style.RESET_ALL}")
        return True
    
    from platforms.kick import KickChatHandler
    
    handler = KickChatHandler(
        config.kick.channel_name,
        chatroom_id=config.kick.chatroom_id
    )
    
    try:
        success = await handler.connect()
        await handler.disconnect()
        
        if success:
            msg = f"chatroom {handler._chatroom_id}" if handler._chatroom_id else "connected"
            print_result("Kick", True, msg)
        else:
            print_result("Kick", False, "Could not connect (may be blocked by Cloudflare)")
        return success
    except Exception as e:
        print_result("Kick", False, str(e))
        return False


async def test_tiktok(config) -> bool:
    """Test TikTok connection."""
    if not config.tiktok.enabled or not config.tiktok.username:
        print(f"  {Fore.YELLOW}─{Style.RESET_ALL} TikTok: {Fore.YELLOW}Disabled{Style.RESET_ALL}")
        return True
    
    # TikTok only works when live, so we just check the config
    print(f"  {Fore.YELLOW}─{Style.RESET_ALL} TikTok: {Fore.YELLOW}@{config.tiktok.username} (only works when live){Style.RESET_ALL}")
    return True


async def test_twitch() -> bool:
    """Test Twitch live detection."""
    try:
        import keyring
        client_id = keyring.get_password("ChatTTSReader", "twitch_client_id")
        username = keyring.get_password("ChatTTSReader", "twitch_username")
    except:
        client_id = None
        username = None
    
    if not client_id or not username:
        print(f"  {Fore.YELLOW}─{Style.RESET_ALL} Twitch: {Fore.YELLOW}Not configured{Style.RESET_ALL}")
        return True
    
    # Try to check live status
    import aiohttp
    try:
        async with aiohttp.ClientSession() as session:
            headers = {'Client-ID': client_id}
            url = f"https://api.twitch.tv/helix/streams?user_login={username}"
            
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    is_live = len(data.get('data', [])) > 0
                    status = "LIVE" if is_live else "offline"
                    print_result("Twitch", True, f"{username} is {status}")
                    return True
                else:
                    print_result("Twitch", False, f"API returned {response.status}")
                    return False
    except Exception as e:
        print_result("Twitch", False, str(e))
        return False


async def test_tts(config) -> bool:
    """Test TTS audio output."""
    from tts_engine import create_tts_engine, TTSMessage
    
    engine_type = config.tts.engine
    
    try:
        if engine_type == "pyttsx3":
            engine = create_tts_engine(
                "pyttsx3",
                voice=config.tts.voice,
                rate=config.tts.rate,
                volume=config.tts.volume
            )
        else:
            engine = create_tts_engine(
                "edge-tts",
                voice=config.tts.edge_voice,
                rate=config.tts.rate,
                volume=config.tts.volume
            )
        
        print(f"    Playing test audio ({engine_type})...")
        
        message = TTSMessage(text="Chat TTS Reader is working!")
        await engine.speak(message)
        
        print_result("TTS Audio", True, engine_type)
        return True
        
    except Exception as e:
        print_result("TTS Audio", False, str(e))
        return False


async def main():
    print(f"\n{Fore.CYAN}╔══════════════════════════════════════════════╗{Style.RESET_ALL}")
    print(f"{Fore.CYAN}║    Chat TTS Reader - Connection Test         ║{Style.RESET_ALL}")
    print(f"{Fore.CYAN}╚══════════════════════════════════════════════╝{Style.RESET_ALL}")
    
    # Load config
    from config import get_config_manager
    config_manager = get_config_manager()
    config = config_manager.load()
    
    results = {}
    
    # Test platforms
    print_header("Platform Connections")
    
    results['youtube'] = await test_youtube(config)
    results['kick'] = await test_kick(config)
    results['tiktok'] = await test_tiktok(config)
    results['twitch'] = await test_twitch()
    
    # Test TTS
    print_header("Audio Output")
    
    results['tts'] = await test_tts(config)
    
    # Summary
    print_header("Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    if passed == total:
        print(f"  {Fore.GREEN}All {total} tests passed!{Style.RESET_ALL}")
    else:
        print(f"  {Fore.YELLOW}{passed}/{total} tests passed{Style.RESET_ALL}")
        failed = [k for k, v in results.items() if not v]
        print(f"  Failed: {', '.join(failed)}")
    
    print()
    
    # Troubleshooting tips
    if not results.get('kick'):
        print(f"{Fore.YELLOW}Kick troubleshooting:{Style.RESET_ALL}")
        print("  - Run Configure and use Kick browser login")
        print("  - Or set chatroom_id manually in config.json")
        print()
    
    if not results.get('youtube'):
        print(f"{Fore.YELLOW}YouTube troubleshooting:{Style.RESET_ALL}")
        print("  - Make sure your stream is live")
        print("  - Check your channel name or video ID in Configure")
        print()
    
    if not results.get('tts'):
        print(f"{Fore.YELLOW}TTS troubleshooting:{Style.RESET_ALL}")
        print("  - Check Windows Volume Mixer")
        print("  - Try switching TTS engine in Configure")
        print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Cancelled.{Style.RESET_ALL}")
    
    input("\nPress Enter to close...")
