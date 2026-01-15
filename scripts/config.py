"""
Configuration management for Chat TTS Reader.
Handles secure storage of API keys and stream URLs using Windows Credential Manager.
"""

import json
import keyring
import os
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Application identifier for keyring
APP_NAME = "ChatTTSReader"
CONFIG_DIR = Path.home() / ".chat-tts-reader"
CONFIG_FILE = CONFIG_DIR / "config.json"


@dataclass
class YouTubeConfig:
    """YouTube Live configuration."""
    enabled: bool = True
    video_id: str = ""  # The live stream video ID (from URL)
    channel: str = ""  # YouTube channel for auto-detection (@handle or URL)
    channel: str = ""  # Channel handle (@username) for auto-detection
    
    
@dataclass
class KickConfig:
    """Kick.com configuration."""
    enabled: bool = True
    channel_name: str = ""  # Your Kick channel name
    chatroom_id: Optional[int] = None  # Optional: bypass API lookup
    

@dataclass
class TikTokConfig:
    """TikTok Live configuration."""
    enabled: bool = True
    username: str = ""  # Your TikTok username (without @)


@dataclass
class TTSConfig:
    """Text-to-speech configuration."""
    engine: str = "pyttsx3"  # 'pyttsx3' or 'edge-tts'
    voice: str = ""  # Voice name (empty = default)
    rate: int = 175  # Words per minute
    volume: float = 1.0  # 0.0 to 1.0
    edge_voice: str = "en-US-GuyNeural"  # For edge-tts


@dataclass
class FilterConfig:
    """Message filtering configuration."""
    min_length: int = 1
    max_length: int = 500
    ignore_commands: bool = True  # Ignore messages starting with !
    ignore_links: bool = True
    blocked_users: list = field(default_factory=list)
    blocked_words: list = field(default_factory=list)


@dataclass
class AppConfig:
    """Main application configuration."""
    youtube: YouTubeConfig = field(default_factory=YouTubeConfig)
    kick: KickConfig = field(default_factory=KickConfig)
    tiktok: TikTokConfig = field(default_factory=TikTokConfig)
    tts: TTSConfig = field(default_factory=TTSConfig)
    filters: FilterConfig = field(default_factory=FilterConfig)
    announce_platform: bool = True  # Say which platform the message is from
    announce_username: bool = True  # Say who sent the message
    queue_max_size: int = 50  # Max messages in TTS queue


class ConfigManager:
    """Manages application configuration and secure credential storage."""
    
    def __init__(self):
        self.config = AppConfig()
        self._ensure_config_dir()
        
    def _ensure_config_dir(self):
        """Create config directory if it doesn't exist."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
    def load(self) -> AppConfig:
        """Load configuration from file."""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                
                # Reconstruct nested dataclasses
                self.config = AppConfig(
                    youtube=YouTubeConfig(**data.get('youtube', {})),
                    kick=KickConfig(**data.get('kick', {})),
                    tiktok=TikTokConfig(**data.get('tiktok', {})),
                    tts=TTSConfig(**data.get('tts', {})),
                    filters=FilterConfig(**data.get('filters', {})),
                    announce_platform=data.get('announce_platform', True),
                    announce_username=data.get('announce_username', True),
                    queue_max_size=data.get('queue_max_size', 50)
                )
                logger.info("Configuration loaded successfully")
            except Exception as e:
                logger.error(f"Error loading config: {e}")
                self.config = AppConfig()
        return self.config
    
    def save(self):
        """Save configuration to file."""
        try:
            # Convert dataclasses to dicts
            data = {
                'youtube': asdict(self.config.youtube),
                'kick': asdict(self.config.kick),
                'tiktok': asdict(self.config.tiktok),
                'tts': asdict(self.config.tts),
                'filters': asdict(self.config.filters),
                'announce_platform': self.config.announce_platform,
                'announce_username': self.config.announce_username,
                'queue_max_size': self.config.queue_max_size
            }
            
            with open(CONFIG_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            raise
    
    # Secure credential storage using Windows Credential Manager
    
    @staticmethod
    def set_credential(service: str, value: str):
        """Store a credential securely."""
        keyring.set_password(APP_NAME, service, value)
        logger.info(f"Credential '{service}' stored securely")
        
    @staticmethod
    def get_credential(service: str) -> Optional[str]:
        """Retrieve a credential."""
        return keyring.get_password(APP_NAME, service)
    
    @staticmethod
    def delete_credential(service: str):
        """Delete a credential."""
        try:
            keyring.delete_password(APP_NAME, service)
            logger.info(f"Credential '{service}' deleted")
        except keyring.errors.PasswordDeleteError:
            pass  # Credential didn't exist
    
    # Convenience methods for specific credentials
    
    def set_youtube_api_key(self, api_key: str):
        """Store YouTube API key (if using API instead of pytchat)."""
        self.set_credential("youtube_api_key", api_key)
        
    def get_youtube_api_key(self) -> Optional[str]:
        return self.get_credential("youtube_api_key")
    
    def set_kick_auth_token(self, token: str):
        """Store Kick authentication token (optional, for authenticated features)."""
        self.set_credential("kick_auth_token", token)
        
    def get_kick_auth_token(self) -> Optional[str]:
        return self.get_credential("kick_auth_token")


def get_config_manager() -> ConfigManager:
    """Get the singleton config manager instance."""
    if not hasattr(get_config_manager, '_instance'):
        get_config_manager._instance = ConfigManager()
    return get_config_manager._instance
