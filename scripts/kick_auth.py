"""
Kick Authentication Module
Handles browser-based login to capture session cookies.
Uses undetected-chromedriver to bypass Cloudflare/bot detection.
"""

import json
import logging
import os
import time
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# Cookie storage
def _get_cookie_file() -> str:
    """Get path to cookie storage file."""
    config_dir = os.path.join(os.path.expanduser("~"), ".chat-tts-reader")
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "kick_cookies.json")


def get_stored_cookies() -> Optional[Dict]:
    """Retrieve stored Kick cookies from file."""
    try:
        cookie_file = _get_cookie_file()
        if os.path.exists(cookie_file):
            with open(cookie_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.debug(f"Could not retrieve stored cookies: {e}")
    return None


def store_cookies(cookies: Dict):
    """Store Kick cookies to file."""
    try:
        cookie_file = _get_cookie_file()
        with open(cookie_file, 'w') as f:
            json.dump(cookies, f)
        logger.info(f"Kick cookies stored to {cookie_file}")
    except Exception as e:
        logger.error(f"Could not store cookies: {e}")


def clear_cookies():
    """Clear stored Kick cookies."""
    try:
        cookie_file = _get_cookie_file()
        if os.path.exists(cookie_file):
            os.remove(cookie_file)
            logger.info("Kick cookies cleared")
    except Exception as e:
        logger.debug(f"Could not clear cookies: {e}")


def browser_login(timeout: int = 300) -> Optional[Dict]:
    """
    Open a browser window for the user to log into Kick.
    Uses undetected-chromedriver to bypass bot detection.
    
    Args:
        timeout: Maximum time to wait for login (seconds)
    
    Returns:
        Dictionary of cookies if successful, None otherwise
    """
    try:
        import undetected_chromedriver as uc
    except ImportError:
        logger.error("undetected-chromedriver not installed.")
        print("\n  Error: undetected-chromedriver not installed.")
        print("  Run: pip install undetected-chromedriver")
        return None
    
    print("\n" + "=" * 60)
    print("  Kick Login")
    print("=" * 60)
    print("""
  A browser window will open to Kick's website.
  
  1. Click "Log In" on Kick
  2. Log in with your account
  3. Once logged in, return here and press Enter
  
  The browser will stay open until you confirm login.
  
  Press Enter to open the browser...""")
    input()
    
    driver = None
    try:
        print("\n  Starting browser (this may take a moment)...")
        
        # Configure undetected Chrome
        options = uc.ChromeOptions()
        options.add_argument("--window-size=1280,900")
        
        # Create driver - undetected_chromedriver handles anti-detection
        driver = uc.Chrome(options=options, use_subprocess=True)
        
        # Navigate to Kick
        print("  Opening Kick...")
        driver.get("https://kick.com/")
        
        print("\n" + "-" * 60)
        print("  Browser opened! Please:")
        print("    1. Click 'Log In' on Kick")
        print("    2. Log in with your account")
        print("    3. Wait until you see your dashboard/homepage")
        print("    4. Come back here and press Enter")
        print("-" * 60)
        
        input("\n  Press Enter after you've logged in...")
        
        # Collect cookies
        cookies = driver.get_cookies()
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        
        # Check if we got authentication cookies
        if 'kick_session' in cookie_dict or len(cookie_dict) > 5:
            print(f"\n  ✓ Login successful!")
            print(f"  Captured {len(cookie_dict)} cookies")
            
            # Store cookies
            store_cookies(cookie_dict)
            
            return cookie_dict
        else:
            print("\n  ⚠ Could not detect login cookies.")
            print("  Make sure you're fully logged in, then try again.")
            return None
            
    except Exception as e:
        logger.error(f"Browser login failed: {e}")
        print(f"\n  ✗ Error: {e}")
        return None
        
    finally:
        if driver:
            try:
                print("\n  Closing browser...")
                driver.quit()
            except:
                pass


def get_cookies_for_requests() -> Dict[str, str]:
    """
    Get cookies formatted for use with requests/aiohttp.
    Returns empty dict if no cookies stored.
    """
    cookies = get_stored_cookies()
    return cookies if cookies else {}


def test_cookies() -> bool:
    """Test if stored cookies are still valid."""
    import asyncio
    import aiohttp
    
    cookies = get_stored_cookies()
    if not cookies:
        return False
    
    async def check():
        try:
            async with aiohttp.ClientSession(cookies=cookies) as session:
                async with session.get("https://kick.com/api/v1/user") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('id'):
                            return True
        except:
            pass
        return False
    
    try:
        return asyncio.run(check())
    except:
        return False


def interactive_login():
    """Interactive login flow for use in configure.py"""
    print("\n" + "=" * 60)
    print("  Kick Authentication")
    print("=" * 60)
    
    # Check for existing cookies
    existing = get_stored_cookies()
    if existing:
        print("\n  You have existing Kick credentials stored.")
        print("\n  Options:")
        print("    1. Test existing login")
        print("    2. Login again (refresh)")
        print("    3. Clear stored login")
        print("    4. Cancel")
        
        choice = input("\n  Choice [1]: ").strip() or "1"
        
        if choice == "1":
            print("\n  Testing stored credentials...")
            if test_cookies():
                print("  ✓ Credentials are valid!")
                return True
            else:
                print("  ✗ Credentials expired or invalid.")
                print("  Please login again.")
                return browser_login() is not None
                
        elif choice == "2":
            return browser_login() is not None
            
        elif choice == "3":
            clear_cookies()
            print("  ✓ Credentials cleared.")
            return False
            
        else:
            return True
    else:
        print("\n  No Kick credentials stored.")
        print("  Would you like to log in now?")
        
        choice = input("\n  Login to Kick? (Y/n): ").strip().lower()
        if choice != 'n':
            return browser_login() is not None
        return False


if __name__ == "__main__":
    # Test the login flow
    logging.basicConfig(level=logging.INFO)
    interactive_login()
