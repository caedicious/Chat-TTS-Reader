"""
Chat TTS Reader - Twitch Live Launcher
Waits until you're live on Twitch, then starts the TTS reader.

First-time setup:
1. Go to https://dev.twitch.tv/console/apps
2. Register a new application (any name, OAuth redirect: http://localhost)
3. Copy your Client ID
4. Run: python wait_for_live.py --setup
"""

import asyncio
import argparse
import logging
import sys
import os
import time
from datetime import datetime

import aiohttp
import keyring

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

APP_NAME = "ChatTTSReader"
TWITCH_CLIENT_ID_KEY = "twitch_client_id"
TWITCH_USERNAME_KEY = "twitch_username"


def get_credentials():
    """Get stored Twitch credentials."""
    client_id = keyring.get_password(APP_NAME, TWITCH_CLIENT_ID_KEY)
    username = keyring.get_password(APP_NAME, TWITCH_USERNAME_KEY)
    return client_id, username


def set_credentials(client_id: str, username: str):
    """Store Twitch credentials securely."""
    keyring.set_password(APP_NAME, TWITCH_CLIENT_ID_KEY, client_id)
    keyring.set_password(APP_NAME, TWITCH_USERNAME_KEY, username)


def setup_credentials():
    """Interactive setup for Twitch credentials."""
    print("\n" + "=" * 50)
    print("  Twitch Live Checker - Setup")
    print("=" * 50)
    print("""
To check if you're live, we need a Twitch Client ID.

1. Go to: https://dev.twitch.tv/console/apps
2. Click 'Register Your Application'
3. Name: anything (e.g., 'ChatTTSReader')
4. OAuth Redirect URL: http://localhost
5. Category: Chat Bot
6. Click 'Create'
7. Click 'Manage' on your new app
8. Copy the 'Client ID'
""")
    
    client_id = input("Paste your Client ID: ").strip()
    if not client_id:
        print("No Client ID provided. Exiting.")
        return False
    
    username = input("Your Twitch username: ").strip().lower()
    if not username:
        print("No username provided. Exiting.")
        return False
    
    set_credentials(client_id, username)
    print(f"\n✓ Credentials saved for: {username}")
    return True


async def get_app_access_token(client_id: str) -> str:
    """Get a Twitch app access token (client credentials flow)."""
    # For just checking if someone is live, we can use client credentials
    # This doesn't require user authorization
    
    # Actually, Twitch Helix API allows checking streams with just Client-ID
    # if we also provide a valid token. Let's get an app token.
    
    # Note: For simplicity, we'll try without a token first (some endpoints work)
    # If that fails, we'd need client_secret which complicates things.
    
    # Alternative: Use the unauthenticated check via Twitch's public pages
    return None


async def check_if_live_api(client_id: str, username: str) -> bool:
    """Check if user is live using Twitch API."""
    try:
        headers = {
            'Client-ID': client_id,
        }
        
        # Try to get an app access token first
        # For client credentials, we'd need client_secret
        # Let's try the simpler approach of checking the stream without auth
        # (This may not work without OAuth, so we have a fallback)
        
        async with aiohttp.ClientSession() as session:
            # Method 1: Try Helix API (may require OAuth)
            url = f"https://api.twitch.tv/helix/streams?user_login={username}"
            
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    streams = data.get('data', [])
                    return len(streams) > 0 and streams[0].get('type') == 'live'
                elif response.status == 401:
                    # Need OAuth - fall back to scraping method
                    return await check_if_live_scrape(username)
                else:
                    logger.warning(f"Twitch API returned {response.status}")
                    return await check_if_live_scrape(username)
                    
    except Exception as e:
        logger.error(f"API check failed: {e}")
        return await check_if_live_scrape(username)


async def check_if_live_scrape(username: str) -> bool:
    """Fallback: Check if user is live by checking their Twitch page."""
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            url = f"https://www.twitch.tv/{username}"
            
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    # Check for live indicators in the page
                    is_live = '"isLiveBroadcast":true' in html or '"stream":{"id":' in html
                    return is_live
                    
    except Exception as e:
        logger.error(f"Scrape check failed: {e}")
    
    return False


async def wait_for_live(client_id: str, username: str, check_interval: int = 30):
    """Wait until the user goes live on Twitch, or user types bypass."""
    import threading
    import queue
    
    # Queue for input from user
    input_queue = queue.Queue()
    bypass_triggered = threading.Event()
    
    def input_listener():
        """Listen for user input in a separate thread."""
        while not bypass_triggered.is_set():
            try:
                user_input = input()
                input_queue.put(user_input)
                if user_input.lower() in ['start', 'go', 's', 'g', '']:
                    bypass_triggered.set()
                    break
            except EOFError:
                break
    
    # Start input listener thread
    input_thread = threading.Thread(target=input_listener, daemon=True)
    input_thread.start()
    
    print(f"\n⏳ Waiting for {username} to go live on Twitch...")
    print(f"   Checking every {check_interval} seconds.")
    print(f"\n   Press ENTER or type 'start' to bypass and start immediately.\n")
    
    while True:
        try:
            # Check if bypass was triggered
            if bypass_triggered.is_set():
                print(f"\n⚡ Bypass activated! Starting immediately...")
                return True
            
            is_live = await check_if_live_api(client_id, username)
            
            if is_live:
                print(f"\n🔴 {username} is LIVE!")
                bypass_triggered.set()  # Stop the input thread
                return True
            else:
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"   [{timestamp}] Not live yet... (Press ENTER to start anyway)", end='\r')
                
                # Wait with small intervals to check for bypass
                for _ in range(check_interval):
                    if bypass_triggered.is_set():
                        print(f"\n⚡ Bypass activated! Starting immediately...")
                        return True
                    await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            print("\n\nCancelled.")
            bypass_triggered.set()
            return False
        except KeyboardInterrupt:
            print("\n\nCancelled.")
            bypass_triggered.set()
            return False


def launch_tts_reader():
    """Launch the main TTS reader application."""
    print("\n🚀 Starting Chat TTS Reader...\n")
    
    # Import and run main
    try:
        from main import main as tts_main
        asyncio.run(tts_main())
    except ImportError:
        # Fallback: run as subprocess
        import subprocess
        subprocess.run([sys.executable, "main.py"])


async def main():
    parser = argparse.ArgumentParser(description="Wait for Twitch live then start TTS Reader")
    parser.add_argument('--setup', action='store_true', help='Set up Twitch credentials')
    parser.add_argument('--check-only', action='store_true', help='Just check if live, don\'t start TTS')
    parser.add_argument('--interval', type=int, default=30, help='Check interval in seconds (default: 30)')
    parser.add_argument('--skip-wait', action='store_true', help='Skip waiting, start TTS immediately')
    args = parser.parse_args()
    
    # Setup mode
    if args.setup:
        setup_credentials()
        return
    
    # Get credentials
    client_id, username = get_credentials()
    
    if not client_id or not username:
        print("Twitch credentials not configured.")
        print("Run: python wait_for_live.py --setup")
        return
    
    print(f"Twitch username: {username}")
    
    # Check only mode
    if args.check_only:
        is_live = await check_if_live_api(client_id, username)
        print(f"Live: {is_live}")
        return
    
    # Skip wait mode
    if args.skip_wait:
        launch_tts_reader()
        return
    
    # Wait for live then launch
    try:
        went_live = await wait_for_live(client_id, username, args.interval)
        
        if went_live:
            # Small delay to let stream fully initialize
            print("Waiting 10 seconds for stream to stabilize...")
            await asyncio.sleep(10)
            launch_tts_reader()
            
    except KeyboardInterrupt:
        print("\nExiting.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
