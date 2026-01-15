"""Base class for platform chat handlers."""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Callable, Optional, Awaitable

logger = logging.getLogger(__name__)


class ChatMessage:
    """Represents a chat message from any platform. Uses __slots__ for memory efficiency."""
    __slots__ = ('platform', 'username', 'message', 'timestamp', 'user_id', 'is_moderator', 'is_subscriber')
    
    def __init__(self, platform: str, username: str, message: str, timestamp: datetime,
                 user_id: str = "", is_moderator: bool = False, is_subscriber: bool = False, **kwargs):
        self.platform = platform
        self.username = username
        self.message = message
        self.timestamp = timestamp
        self.user_id = user_id
        self.is_moderator = is_moderator
        self.is_subscriber = is_subscriber


# Type alias for message callbacks
MessageCallback = Callable[[ChatMessage], Awaitable[None]]


class BaseChatHandler(ABC):
    """Abstract base class for platform chat handlers."""
    __slots__ = ('platform_name', '_running', '_callback', '_task')
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self._running = False
        self._callback: Optional[MessageCallback] = None
        self._task: Optional[asyncio.Task] = None
        
    def set_callback(self, callback: MessageCallback):
        """Set the callback function for new messages."""
        self._callback = callback
        
    async def _emit_message(self, message: ChatMessage):
        """Emit a message to the registered callback."""
        if self._callback:
            try:
                await self._callback(message)
            except Exception as e:
                logger.error(f"Error in message callback: {e}")
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Connect to the chat platform.
        Returns True if successful, False otherwise.
        """
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Disconnect from the chat platform."""
        pass
    
    @abstractmethod
    async def _listen_loop(self):
        """Main loop for listening to chat messages."""
        pass
    
    async def start(self):
        """Start listening for chat messages."""
        if self._running:
            return
            
        if await self.connect():
            self._running = True
            self._task = asyncio.create_task(self._listen_loop())
    
    async def stop(self):
        """Stop listening for chat messages."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self.disconnect()
    
    @property
    def is_running(self) -> bool:
        """Check if the handler is currently running."""
        return self._running
