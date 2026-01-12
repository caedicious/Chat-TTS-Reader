"""
Chat TTS Reader - Main Application
Reads chat messages from YouTube, Kick, and TikTok live streams via TTS.
"""

import asyncio
import logging
import re
import signal
import sys
from datetime import datetime
from typing import List, Optional

from colorama import init as colorama_init, Fore, Style

from config import ConfigManager, AppConfig, get_config_manager
from tts_engine import TTSQueue, TTSMessage, create_tts_engine
from platforms import (
    BaseChatHandler,
    ChatMessage,
    YouTubeChatHandler,
    KickChatHandler,
    TikTokChatHandler
)
from platforms.youtube import extract_video_id

# Initialize colorama for Windows color support
colorama_init()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class ChatTTSReader:
    """Main application class that coordinates chat handlers and TTS."""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.config: Optional[AppConfig] = None
        self.tts_queue: Optional[TTSQueue] = None
        self.handlers: List[BaseChatHandler] = []
        self._running = False
        
    def _setup_logging(self):
        """Configure logging based on settings."""
        # Could add file logging, etc. here
        pass
    
    def _create_handlers(self) -> List[BaseChatHandler]:
        """Create chat handlers based on configuration."""
        handlers = []
        
        # YouTube handler
        if self.config.youtube.enabled:
            video_id = None
            
            # First try the configured video ID
            if self.config.youtube.video_id:
                video_id = extract_video_id(self.config.youtube.video_id)
            
            # If no video ID but channel is set, try to auto-detect
            if not video_id and self.config.youtube.channel:
                logger.info(f"Auto-detecting live stream for channel: {self.config.youtube.channel}")
                from platforms.youtube import get_live_video_id_sync
                video_id = get_live_video_id_sync(self.config.youtube.channel)
                if video_id:
                    logger.info(f"Found live stream: {video_id}")
                else:
                    logger.warning(f"No live stream found for channel: {self.config.youtube.channel}")
            
            if video_id:
                handlers.append(YouTubeChatHandler(video_id))
                logger.info(f"YouTube handler configured: {video_id}")
            elif self.config.youtube.video_id:
                logger.warning(f"Invalid YouTube video ID: {self.config.youtube.video_id}")
            elif self.config.youtube.channel:
                logger.warning(f"Could not find live stream for: {self.config.youtube.channel}")
        
        # Kick handler
        if self.config.kick.enabled and self.config.kick.channel_name:
            handlers.append(KickChatHandler(
                self.config.kick.channel_name,
                chatroom_id=self.config.kick.chatroom_id
            ))
            logger.info(f"Kick handler configured: {self.config.kick.channel_name}")
        
        # TikTok handler
        if self.config.tiktok.enabled and self.config.tiktok.username:
            handlers.append(TikTokChatHandler(self.config.tiktok.username))
            logger.info(f"TikTok handler configured: @{self.config.tiktok.username}")
        
        return handlers
    
    def _filter_message(self, message: ChatMessage) -> bool:
        """
        Check if a message should be read.
        Returns True if message should be spoken, False if filtered out.
        """
        filters = self.config.filters
        text = message.message
        
        # Check length
        if len(text) < filters.min_length or len(text) > filters.max_length:
            return False
        
        # Check for commands
        if filters.ignore_commands and text.startswith('!'):
            return False
        
        # Check for links
        if filters.ignore_links:
            url_pattern = r'https?://|www\.'
            if re.search(url_pattern, text, re.IGNORECASE):
                return False
        
        # Check blocked users
        if message.username.lower() in [u.lower() for u in filters.blocked_users]:
            return False
        
        # Check blocked words
        text_lower = text.lower()
        for word in filters.blocked_words:
            if word.lower() in text_lower:
                return False
        
        return True
    
    def _format_tts_text(self, message: ChatMessage) -> str:
        """Format a chat message for TTS."""
        parts = []
        
        if self.config.announce_platform:
            parts.append(message.platform + ",")
        
        if self.config.announce_username:
            # Clean username for TTS
            username = message.username
            # Remove special characters that sound weird
            username = re.sub(r'[_\-\d]+', ' ', username).strip()
            if username:
                parts.append(username + " says,")
        
        # Clean message text
        text = message.message
        # Remove emotes/emojis for cleaner TTS (optional)
        # text = re.sub(r':[a-zA-Z0-9_]+:', '', text)  # Remove :emote: style
        
        parts.append(text)
        
        return " ".join(parts)
    
    async def _on_message(self, message: ChatMessage):
        """Handle incoming chat messages."""
        # Log to console with colors
        platform_colors = {
            "YouTube": Fore.RED,
            "Kick": Fore.GREEN,
            "TikTok": Fore.MAGENTA
        }
        color = platform_colors.get(message.platform, Fore.WHITE)
        
        print(f"{color}[{message.platform}]{Style.RESET_ALL} "
              f"{Fore.CYAN}{message.username}{Style.RESET_ALL}: "
              f"{message.message}")
        
        # Filter check
        if not self._filter_message(message):
            logger.debug(f"Message filtered: {message.message[:50]}")
            return
        
        # Format and queue for TTS
        tts_text = self._format_tts_text(message)
        tts_message = TTSMessage(
            text=tts_text,
            platform=message.platform,
            username=message.username
        )
        
        await self.tts_queue.add(tts_message)
    
    async def start(self):
        """Start the application."""
        print(f"\n{Fore.CYAN}╔══════════════════════════════════════╗{Style.RESET_ALL}")
        print(f"{Fore.CYAN}║     Chat TTS Reader - Starting...    ║{Style.RESET_ALL}")
        print(f"{Fore.CYAN}╚══════════════════════════════════════╝{Style.RESET_ALL}\n")
        
        # Load configuration
        self.config = self.config_manager.load()
        
        # Create TTS engine and queue
        tts_config = self.config.tts
        try:
            engine = create_tts_engine(
                tts_config.engine,
                voice=tts_config.voice if tts_config.engine == "pyttsx3" else tts_config.edge_voice,
                rate=tts_config.rate,
                volume=tts_config.volume
            )
            self.tts_queue = TTSQueue(engine, max_size=self.config.queue_max_size)
            await self.tts_queue.start()
            logger.info(f"TTS engine started: {tts_config.engine}")
        except Exception as e:
            logger.error(f"Failed to start TTS engine: {e}")
            print(f"\n{Fore.YELLOW}TTS engine failed to start. Messages will be displayed but not spoken.{Style.RESET_ALL}")
            print(f"Error: {e}\n")
        
        # Create and start handlers
        self.handlers = self._create_handlers()
        
        if not self.handlers:
            print(f"\n{Fore.YELLOW}No chat platforms configured!{Style.RESET_ALL}")
            print("Run 'python configure.py' to set up your streams.\n")
            return
        
        # Set up message callbacks and start handlers
        for handler in self.handlers:
            handler.set_callback(self._on_message)
            await handler.start()
        
        self._running = True
        
        print(f"\n{Fore.GREEN}✓ Chat TTS Reader is running!{Style.RESET_ALL}")
        print(f"  Press Ctrl+C to stop.\n")
        print(f"{Fore.CYAN}{'─' * 50}{Style.RESET_ALL}\n")
        
        # Keep running until stopped
        try:
            while self._running:
                await asyncio.sleep(1)
                
                # Periodic status (optional)
                # Could add queue status, connection status, etc.
                
        except asyncio.CancelledError:
            pass
    
    async def stop(self):
        """Stop the application gracefully."""
        print(f"\n{Fore.YELLOW}Shutting down...{Style.RESET_ALL}")
        self._running = False
        
        # Stop all handlers
        for handler in self.handlers:
            await handler.stop()
        
        # Stop TTS queue
        if self.tts_queue:
            await self.tts_queue.stop()
        
        print(f"{Fore.GREEN}✓ Chat TTS Reader stopped.{Style.RESET_ALL}\n")


async def main():
    """Main entry point."""
    app = ChatTTSReader()
    
    # Set up signal handlers for graceful shutdown
    loop = asyncio.get_event_loop()
    
    def signal_handler():
        asyncio.create_task(app.stop())
    
    # Handle Ctrl+C
    try:
        if sys.platform != 'win32':
            loop.add_signal_handler(signal.SIGINT, signal_handler)
            loop.add_signal_handler(signal.SIGTERM, signal_handler)
    except NotImplementedError:
        # Windows doesn't support add_signal_handler
        pass
    
    try:
        await app.start()
    except KeyboardInterrupt:
        await app.stop()
    except Exception as e:
        logger.error(f"Application error: {e}")
        await app.stop()
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
