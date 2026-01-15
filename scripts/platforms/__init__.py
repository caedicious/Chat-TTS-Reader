"""Platform chat handlers for Chat TTS Reader."""

from .base import BaseChatHandler, ChatMessage
from .youtube import YouTubeChatHandler
from .kick import KickChatHandler
from .tiktok import TikTokChatHandler

__all__ = [
    'BaseChatHandler',
    'ChatMessage',
    'YouTubeChatHandler',
    'KickChatHandler',
    'TikTokChatHandler'
]
