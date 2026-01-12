"""Kick.com chat handler using WebSockets."""

import asyncio
import json
import logging
import re
from datetime import datetime
from typing import Optional, Dict

import aiohttp
import websockets

from .base import BaseChatHandler, ChatMessage

logger = logging.getLogger(__name__)


def get_kick_cookies() -> Dict[str, str]:
    """Get stored Kick cookies."""
    try:
        from kick_auth import get_stored_cookies
        return get_stored_cookies() or {}
    except ImportError:
        return {}


class KickChatHandler(BaseChatHandler):
    """
    Handler for Kick.com chat using WebSockets.
    
    Kick uses Pusher for their WebSocket connections.
    This handler can use authenticated cookies if available.
    """
    
    # Kick's Pusher WebSocket endpoint
    PUSHER_URL = "wss://ws-us2.pusher.com/app/32cbd69e4b950bf97679?protocol=7&client=js&version=7.6.0&flash=false"
    
    def __init__(self, channel_name: str, chatroom_id: Optional[int] = None):
        """
        Initialize Kick chat handler.
        
        Args:
            channel_name: The Kick channel name (username)
            chatroom_id: Optional chatroom ID (skips API lookup if provided)
        """
        super().__init__("Kick")
        self.channel_name = channel_name.lower()
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._channel_id: Optional[int] = None
        self._chatroom_id: Optional[int] = chatroom_id
        self._cookies: Dict[str, str] = {}
        
    async def _get_channel_info(self) -> bool:
        """Fetch channel and chatroom IDs from Kick."""
        
        # If chatroom_id was provided, skip the lookup
        if self._chatroom_id:
            logger.info(f"Using provided chatroom ID: {self._chatroom_id}")
            return True
        
        # Get stored cookies for authenticated requests
        self._cookies = get_kick_cookies()
        has_cookies = bool(self._cookies)
        
        if has_cookies:
            logger.info("Using stored Kick credentials for API requests")
        
        # Build cookie header string
        cookie_header = "; ".join([f"{k}={v}" for k, v in self._cookies.items()]) if has_cookies else ""
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://kick.com/',
            'Origin': 'https://kick.com',
            'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }
        
        if cookie_header:
            headers['Cookie'] = cookie_header
        
        try:
            async with aiohttp.ClientSession() as session:
                # Try v2 API first (more common)
                url = f"https://kick.com/api/v2/channels/{self.channel_name}"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        self._channel_id = data.get('id')
                        self._chatroom_id = data.get('chatroom', {}).get('id')
                        if self._chatroom_id:
                            logger.info(f"Kick channel info (v2): id={self._channel_id}, chatroom={self._chatroom_id}")
                            return True
                    elif response.status == 403:
                        logger.warning(f"Kick API returned 403 (blocked)")
                        if not has_cookies:
                            logger.info("Try logging in to Kick: run kick_auth.py")
                    else:
                        logger.warning(f"Kick API v2 returned {response.status}")
                
                # Try v1 API
                url = f"https://kick.com/api/v1/channels/{self.channel_name}"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        self._channel_id = data.get('id')
                        self._chatroom_id = data.get('chatroom', {}).get('id')
                        if self._chatroom_id:
                            logger.info(f"Kick channel info (v1): id={self._channel_id}, chatroom={self._chatroom_id}")
                            return True
                
                # Method 3: Scrape the main page for embedded data
                url = f"https://kick.com/{self.channel_name}"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        # Look for chatroom ID in the page
                        match = re.search(r'"chatroom":\s*\{"id":\s*(\d+)', html)
                        if match:
                            self._chatroom_id = int(match.group(1))
                            logger.info(f"Kick chatroom ID from page: {self._chatroom_id}")
                            return True
                        
                        # Alternative pattern
                        match = re.search(r'chatrooms\.(\d+)\.v2', html)
                        if match:
                            self._chatroom_id = int(match.group(1))
                            logger.info(f"Kick chatroom ID from pattern: {self._chatroom_id}")
                            return True
                
                logger.error("Could not find Kick chatroom ID")
                return False
                
        except Exception as e:
            logger.error(f"Error fetching Kick channel info: {e}")
            return False
    
    async def connect(self) -> bool:
        """Connect to Kick chat via WebSocket."""
        try:
            # First get channel info
            if not await self._get_channel_info():
                logger.error(f"Failed to get Kick channel info for {self.channel_name}")
                logger.info("Kick may be blocking requests. Try again later or check the channel name.")
                return False
            
            # Connect to Pusher WebSocket
            self._ws = await websockets.connect(
                self.PUSHER_URL,
                ping_interval=30,
                ping_timeout=10,
                origin='https://kick.com',
                user_agent_header='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            # Wait for connection established message
            response = await self._ws.recv()
            data = json.loads(response)
            
            if data.get('event') == 'pusher:connection_established':
                logger.info("Kick WebSocket connection established")
                
                # Subscribe to the chatroom channel
                subscribe_msg = json.dumps({
                    "event": "pusher:subscribe",
                    "data": {
                        "auth": "",
                        "channel": f"chatrooms.{self._chatroom_id}.v2"
                    }
                })
                await self._ws.send(subscribe_msg)
                
                # Wait for subscription confirmation
                response = await self._ws.recv()
                data = json.loads(response)
                
                if data.get('event') == 'pusher_internal:subscription_succeeded':
                    logger.info(f"Subscribed to Kick chatroom: {self._chatroom_id}")
                    return True
                else:
                    logger.warning(f"Unexpected subscription response: {data}")
                    return True  # Continue anyway, might still work
            else:
                logger.error(f"Unexpected connection response: {data}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to Kick: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from Kick chat."""
        if self._ws:
            try:
                await self._ws.close()
            except Exception as e:
                logger.error(f"Error disconnecting from Kick: {e}")
            self._ws = None
    
    async def _listen_loop(self):
        """Listen for Kick chat messages."""
        while self._running and self._ws:
            try:
                raw_message = await asyncio.wait_for(self._ws.recv(), timeout=60)
                data = json.loads(raw_message)
                
                event = data.get('event', '')
                
                # Handle chat messages
                if event == 'App\\Events\\ChatMessageEvent':
                    try:
                        message_data = json.loads(data.get('data', '{}'))
                        
                        sender = message_data.get('sender', {})
                        content = message_data.get('content', '')
                        
                        # Create chat message
                        message = ChatMessage(
                            platform="Kick",
                            username=sender.get('username', 'Unknown'),
                            message=content,
                            timestamp=datetime.now(),
                            user_id=str(sender.get('id', '')),
                            is_moderator=sender.get('is_moderator', False) or sender.get('is_broadcaster', False),
                            is_subscriber=sender.get('is_subscriber', False),
                            badges=sender.get('identity', {}).get('badges', [])
                        )
                        
                        await self._emit_message(message)
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse Kick message data: {e}")
                
                # Handle pusher ping/pong
                elif event == 'pusher:ping':
                    await self._ws.send(json.dumps({"event": "pusher:pong", "data": {}}))
                
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                try:
                    await self._ws.send(json.dumps({"event": "pusher:ping", "data": {}}))
                except Exception:
                    pass
            except asyncio.CancelledError:
                break
            except websockets.ConnectionClosed:
                logger.warning("Kick WebSocket connection closed, attempting reconnect...")
                if self._running:
                    await asyncio.sleep(5)
                    if await self.connect():
                        continue
                break
            except Exception as e:
                logger.error(f"Kick chat error: {e}")
                await asyncio.sleep(2)
        
        logger.info("Kick chat loop ended")
