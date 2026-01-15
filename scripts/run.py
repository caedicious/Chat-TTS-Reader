"""
Chat TTS Reader - Main Runner
Waits for Twitch live (with bypass option), then starts reading chat.
Optimized for low CPU usage alongside streaming software.
"""

import asyncio
import sys
import os
import threading

# Set process to low priority (so streaming gets CPU priority)
if sys.platform == 'win32':
    try:
        import ctypes
        BELOW_NORMAL_PRIORITY_CLASS = 0x00004000
        ctypes.windll.kernel32.SetPriorityClass(
            ctypes.windll.kernel32.GetCurrentProcess(),
            BELOW_NORMAL_PRIORITY_CLASS
        )
    except:
        pass

# Add scripts directory to path
scripts_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, scripts_dir)

from colorama import init as colorama_init, Fore, Style
colorama_init()


def print_banner():
    print(f"\n{Fore.CYAN}╔══════════════════════════════════════╗{Style.RESET_ALL}")
    print(f"{Fore.CYAN}║        Chat TTS Reader v1.1.1        ║{Style.RESET_ALL}")
    print(f"{Fore.CYAN}╚══════════════════════════════════════╝{Style.RESET_ALL}\n")


async def check_twitch_live(client_id: str, username: str, session) -> bool:
    """Check if user is live on Twitch. Reuses session for efficiency."""
    try:
        # Try API first
        headers = {'Client-ID': client_id}
        url = f"https://api.twitch.tv/helix/streams?user_login={username}"
        
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                streams = data.get('data', [])
                return len(streams) > 0 and streams[0].get('type') == 'live'
        
        # Fallback to scraping
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        url = f"https://www.twitch.tv/{username}"
        
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                html = await response.text()
                return '"isLiveBroadcast":true' in html or '"stream":{"id":' in html
                    
    except Exception as e:
        print(f"{Fore.YELLOW}  Twitch check error: {e}{Style.RESET_ALL}")
    
    return False


async def wait_for_twitch_or_bypass(client_id: str, username: str, check_interval: int = 60) -> bool:
    """Wait for Twitch live or user bypass. Returns True to start app."""
    import aiohttp
    
    # Set up bypass detection
    bypass_triggered = threading.Event()
    
    def input_listener():
        while not bypass_triggered.is_set():
            try:
                user_input = input()
                if user_input.lower() in ['', 'start', 'go', 's', 'g']:
                    bypass_triggered.set()
                    break
            except EOFError:
                break
    
    input_thread = threading.Thread(target=input_listener, daemon=True)
    input_thread.start()
    
    print(f"  {Fore.YELLOW}Waiting for {username} to go live on Twitch...{Style.RESET_ALL}")
    print(f"  Checking every {check_interval} seconds.")
    print(f"\n  {Fore.GREEN}Press ENTER to start immediately.{Style.RESET_ALL}\n")
    
    from datetime import datetime
    
    # Reuse session for efficiency
    async with aiohttp.ClientSession() as session:
        while True:
            # Check bypass
            if bypass_triggered.is_set():
                print(f"\n  {Fore.GREEN}⚡ Starting immediately!{Style.RESET_ALL}")
                return True
            
            # Check Twitch
            is_live = await check_twitch_live(client_id, username, session)
            
            if is_live:
                print(f"\n  {Fore.GREEN}🔴 {username} is LIVE!{Style.RESET_ALL}")
                bypass_triggered.set()
                print("  Waiting 10 seconds for stream to stabilize...")
                await asyncio.sleep(10)
                return True
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"  [{timestamp}] Not live yet... (press ENTER to start)", end='\r')
            
            # Wait with bypass check
            for _ in range(check_interval):
                if bypass_triggered.is_set():
                    print(f"\n  {Fore.GREEN}⚡ Starting immediately!{Style.RESET_ALL}")
                    return True
                await asyncio.sleep(1)


async def run_tts_reader():
    """Run the main TTS reader."""
    from main import ChatTTSReader
    
    app = ChatTTSReader()
    
    try:
        await app.start()
    except KeyboardInterrupt:
        await app.stop()
    except Exception as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        await app.stop()


async def main():
    print_banner()
    
    # Check for Twitch credentials
    try:
        import keyring
        client_id = keyring.get_password("ChatTTSReader", "twitch_client_id")
        username = keyring.get_password("ChatTTSReader", "twitch_username")
    except:
        client_id = None
        username = None
    
    # If Twitch is configured, wait for live (with bypass option)
    if client_id and username:
        print(f"  Twitch: {Fore.CYAN}{username}{Style.RESET_ALL}")
        await wait_for_twitch_or_bypass(client_id, username)
    else:
        print(f"  {Fore.YELLOW}Twitch not configured - starting immediately.{Style.RESET_ALL}")
        print(f"  (Run Configure to set up Twitch live detection)\n")
    
    # Start TTS reader
    print(f"\n{Fore.CYAN}{'─' * 50}{Style.RESET_ALL}\n")
    await run_tts_reader()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Stopped.{Style.RESET_ALL}")
