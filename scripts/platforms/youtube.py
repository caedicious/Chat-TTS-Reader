"""YouTube Live chat handler using direct HTTP requests."""

import asyncio
import logging
import re
import json
from datetime import datetime
from typing import Optional, Dict, Any

import aiohttp

from .base import BaseChatHandler, ChatMessage

logger = logging.getLogger(__name__)


class YouTubeChatHandler(BaseChatHandler):
    """
    Handler for YouTube Live chat using direct HTTP polling.
    
    This avoids the threading/signal issues with pytchat by using
    pure async HTTP requests to fetch chat messages.
    """
    
    def __init__(self, video_id: str):
        super().__init__("YouTube")
        self.video_id = video_id
        self._session: Optional[aiohttp.ClientSession] = None
        self._continuation: Optional[str] = None
        self._api_key: Optional[str] = None
        self._inner_tube_context: Optional[Dict] = None
        
    async def _get_initial_data(self) -> bool:
        """Fetch the live chat page and extract continuation token."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
            }
            
            # Get the live chat page
            url = f"https://www.youtube.com/live_chat?is_popout=1&v={self.video_id}"
            
            async with self._session.get(url, headers=headers) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch YouTube live chat page: {response.status}")
                    return False
                
                html = await response.text()
            
            # Extract ytInitialData
            match = re.search(r'var ytInitialData\s*=\s*({.+?});</script>', html)
            if not match:
                match = re.search(r'window\["ytInitialData"\]\s*=\s*({.+?});</script>', html)
            
            if not match:
                logger.error("Could not find ytInitialData in YouTube page")
                # Check if stream is live
                if 'is not currently live' in html.lower() or 'chat is disabled' in html.lower():
                    logger.error("Stream may not be live or chat is disabled")
                return False
            
            initial_data = json.loads(match.group(1))
            
            # Extract API key
            api_key_match = re.search(r'"INNERTUBE_API_KEY":\s*"([^"]+)"', html)
            if api_key_match:
                self._api_key = api_key_match.group(1)
            else:
                self._api_key = "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"  # Default public key
            
            # Set up InnerTube context
            self._inner_tube_context = {
                "context": {
                    "client": {
                        "clientName": "WEB",
                        "clientVersion": "2.20240101.00.00"
                    }
                }
            }
            
            # Find continuation token
            try:
                contents = initial_data.get('contents', {})
                live_chat = contents.get('liveChatRenderer', {})
                continuations = live_chat.get('continuations', [])
                
                if continuations:
                    cont_data = continuations[0]
                    if 'invalidationContinuationData' in cont_data:
                        self._continuation = cont_data['invalidationContinuationData']['continuation']
                    elif 'timedContinuationData' in cont_data:
                        self._continuation = cont_data['timedContinuationData']['continuation']
                    elif 'reloadContinuationData' in cont_data:
                        self._continuation = cont_data['reloadContinuationData']['continuation']
                
                if self._continuation:
                    logger.info("YouTube chat continuation token obtained")
                    return True
                else:
                    logger.error("No continuation token found - chat may not be active")
                    return False
                    
            except Exception as e:
                logger.error(f"Error parsing YouTube initial data: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error fetching YouTube initial data: {e}")
            return False
    
    async def _fetch_chat_messages(self) -> list:
        """Fetch new chat messages using the continuation token."""
        if not self._continuation:
            return []
        
        try:
            url = f"https://www.youtube.com/youtubei/v1/live_chat/get_live_chat?key={self._api_key}"
            
            payload = {
                **self._inner_tube_context,
                "continuation": self._continuation
            }
            
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
            
            async with self._session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    logger.warning(f"YouTube chat fetch returned {response.status}")
                    return []
                
                data = await response.json()
            
            messages = []
            
            # Update continuation token
            cont_contents = data.get('continuationContents', {})
            live_chat_cont = cont_contents.get('liveChatContinuation', {})
            continuations = live_chat_cont.get('continuations', [])
            
            if continuations:
                cont_data = continuations[0]
                if 'invalidationContinuationData' in cont_data:
                    self._continuation = cont_data['invalidationContinuationData']['continuation']
                elif 'timedContinuationData' in cont_data:
                    self._continuation = cont_data['timedContinuationData']['continuation']
            
            # Parse chat actions
            actions = live_chat_cont.get('actions', [])
            
            for action in actions:
                try:
                    # Handle different action types
                    if 'addChatItemAction' in action:
                        item = action['addChatItemAction'].get('item', {})
                        
                        # Regular chat message
                        if 'liveChatTextMessageRenderer' in item:
                            renderer = item['liveChatTextMessageRenderer']
                            msg = self._parse_message(renderer)
                            if msg:
                                messages.append(msg)
                        
                        # Super chat/sticker
                        elif 'liveChatPaidMessageRenderer' in item:
                            renderer = item['liveChatPaidMessageRenderer']
                            msg = self._parse_message(renderer)
                            if msg:
                                messages.append(msg)
                                
                except Exception as e:
                    logger.debug(f"Error parsing chat action: {e}")
                    continue
            
            return messages
            
        except Exception as e:
            logger.error(f"Error fetching YouTube chat: {e}")
            return []
    
    def _parse_message(self, renderer: Dict[str, Any]) -> Optional[ChatMessage]:
        """Parse a chat message renderer into a ChatMessage."""
        try:
            # Get author info
            author_name = renderer.get('authorName', {}).get('simpleText', 'Unknown')
            author_channel_id = renderer.get('authorExternalChannelId', '')
            
            # Get message text
            message_runs = renderer.get('message', {}).get('runs', [])
            message_text = ''.join(
                run.get('text', '') for run in message_runs
            )
            
            if not message_text.strip():
                return None
            
            # Get badges
            badges = []
            author_badges = renderer.get('authorBadges', [])
            for badge in author_badges:
                badge_renderer = badge.get('liveChatAuthorBadgeRenderer', {})
                if 'icon' in badge_renderer:
                    badges.append(badge_renderer['icon'].get('iconType', ''))
            
            is_moderator = 'MODERATOR' in badges or 'OWNER' in badges
            is_member = 'MEMBER' in badges or any('member' in b.lower() for b in badges)
            
            return ChatMessage(
                platform="YouTube",
                username=author_name,
                message=message_text,
                timestamp=datetime.now(),
                user_id=author_channel_id,
                is_moderator=is_moderator,
                is_subscriber=is_member,
                badges=badges
            )
            
        except Exception as e:
            logger.debug(f"Error parsing message: {e}")
            return None
        
    async def connect(self) -> bool:
        """Connect to YouTube Live chat."""
        try:
            self._session = aiohttp.ClientSession()
            
            if await self._get_initial_data():
                logger.info(f"Connected to YouTube Live chat: {self.video_id}")
                return True
            else:
                await self._session.close()
                self._session = None
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to YouTube: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from YouTube Live chat."""
        if self._session:
            await self._session.close()
            self._session = None
    
    async def _listen_loop(self):
        """Listen for YouTube Live chat messages."""
        consecutive_empty = 0
        
        while self._running:
            try:
                messages = await self._fetch_chat_messages()
                
                if messages:
                    consecutive_empty = 0
                    for msg in messages:
                        if not self._running:
                            break
                        await self._emit_message(msg)
                else:
                    consecutive_empty += 1
                    
                    # If we've had many empty fetches, check if stream ended
                    if consecutive_empty > 30:
                        logger.warning("No YouTube messages for extended period, checking stream status...")
                        if not await self._get_initial_data():
                            logger.error("YouTube stream may have ended")
                            break
                        consecutive_empty = 0
                
                # Poll interval - YouTube typically updates every 1-5 seconds
                await asyncio.sleep(2)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"YouTube chat error: {e}")
                await asyncio.sleep(5)
        
        logger.info("YouTube chat loop ended")


def extract_video_id(url: str) -> Optional[str]:
    """
    Extract video ID from a YouTube URL.
    
    Supports formats:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/live/VIDEO_ID
    - https://studio.youtube.com/video/VIDEO_ID/livestreaming
    """
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/live/)([a-zA-Z0-9_-]{11})',
        r'studio\.youtube\.com/video/([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


async def get_live_stream_from_channel(channel_identifier: str) -> Optional[str]:
    """
    Get the current live stream video ID from a YouTube channel.
    
    Args:
        channel_identifier: Channel URL, handle (@username), or channel ID
        
    Returns:
        Video ID of the current live stream, or None if not live
    """
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
            }
            
            # Normalize channel identifier to URL
            if channel_identifier.startswith('@'):
                channel_url = f"https://www.youtube.com/{channel_identifier}/live"
            elif channel_identifier.startswith('UC'):
                channel_url = f"https://www.youtube.com/channel/{channel_identifier}/live"
            elif 'youtube.com' in channel_identifier:
                # Already a URL, append /live if needed
                channel_url = channel_identifier.rstrip('/')
                if not channel_url.endswith('/live'):
                    channel_url += '/live'
            else:
                # Assume it's a handle without @
                channel_url = f"https://www.youtube.com/@{channel_identifier}/live"
            
            logger.info(f"Checking for live stream at: {channel_url}")
            
            async with session.get(channel_url, headers=headers, allow_redirects=True) as response:
                if response.status != 200:
                    logger.warning(f"Channel page returned {response.status}")
                    return None
                
                html = await response.text()
                
                # Check if redirected to a live video
                final_url = str(response.url)
                video_id = extract_video_id(final_url)
                if video_id:
                    # Verify it's actually live
                    if '"isLive":true' in html or '"isLiveBroadcast":true' in html:
                        logger.info(f"Found live stream: {video_id}")
                        return video_id
                
                # Try to find live video ID in the page
                # Look for canonical URL with video ID
                canonical_match = re.search(r'<link rel="canonical" href="[^"]*[?&]v=([a-zA-Z0-9_-]{11})', html)
                if canonical_match:
                    video_id = canonical_match.group(1)
                    if '"isLive":true' in html or '"isLiveBroadcast":true' in html:
                        logger.info(f"Found live stream from canonical: {video_id}")
                        return video_id
                
                # Look for video ID in ytInitialData
                match = re.search(r'"videoId":\s*"([a-zA-Z0-9_-]{11})"', html)
                if match:
                    video_id = match.group(1)
                    if '"isLive":true' in html or '"isLiveBroadcast":true' in html:
                        logger.info(f"Found live stream from data: {video_id}")
                        return video_id
                
                logger.info("No live stream found for this channel")
                return None
                
    except Exception as e:
        logger.error(f"Error checking channel for live stream: {e}")
        return None


def open_youtube_studio():
    """Open YouTube Studio live streaming page in the default browser."""
    import webbrowser
    webbrowser.open("https://studio.youtube.com/channel/UC/livestreaming")


def get_live_video_id_sync(channel_identifier: str) -> Optional[str]:
    """Synchronous wrapper for get_live_stream_from_channel."""
    try:
        return asyncio.run(get_live_stream_from_channel(channel_identifier))
    except:
        return None
