"""
Text-to-Speech engine for Chat TTS Reader.
Supports pyttsx3 (Windows SAPI) and edge-tts (Microsoft Edge voices).
"""

import asyncio
import logging
import queue
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import tempfile
import os

logger = logging.getLogger(__name__)


@dataclass
class TTSMessage:
    """A message to be spoken."""
    text: str
    platform: str = ""
    username: str = ""
    priority: int = 0  # Lower = higher priority


class BaseTTSEngine(ABC):
    """Abstract base class for TTS engines."""
    
    @abstractmethod
    async def speak(self, message: TTSMessage):
        """Speak a message."""
        pass
    
    @abstractmethod
    def stop(self):
        """Stop current speech."""
        pass
    
    @abstractmethod
    def set_rate(self, rate: int):
        """Set speech rate (words per minute)."""
        pass
    
    @abstractmethod
    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)."""
        pass


class Pyttsx3Engine(BaseTTSEngine):
    """TTS engine using pyttsx3 (Windows SAPI voices)."""
    
    def __init__(self, voice: str = "", rate: int = 175, volume: float = 1.0):
        import pyttsx3
        self.engine = pyttsx3.init()
        self._lock = threading.Lock()
        
        # Set voice if specified
        if voice:
            voices = self.engine.getProperty('voices')
            for v in voices:
                if voice.lower() in v.name.lower():
                    self.engine.setProperty('voice', v.id)
                    break
        
        self.set_rate(rate)
        self.set_volume(volume)
        
    def list_voices(self) -> list:
        """List available voices."""
        voices = self.engine.getProperty('voices')
        return [{"id": v.id, "name": v.name} for v in voices]
    
    async def speak(self, message: TTSMessage):
        """Speak a message using pyttsx3."""
        def _speak():
            with self._lock:
                self.engine.say(message.text)
                self.engine.runAndWait()
        
        # Run in thread pool to not block async loop
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _speak)
    
    def stop(self):
        """Stop current speech."""
        with self._lock:
            self.engine.stop()
    
    def set_rate(self, rate: int):
        """Set speech rate."""
        self.engine.setProperty('rate', rate)
    
    def set_volume(self, volume: float):
        """Set volume."""
        self.engine.setProperty('volume', volume)


class EdgeTTSEngine(BaseTTSEngine):
    """TTS engine using edge-tts (Microsoft Edge neural voices)."""
    
    def __init__(self, voice: str = "en-US-GuyNeural", rate: int = 175, volume: float = 1.0, audio_device: str = ""):
        self.voice = voice
        self.rate = rate
        self.volume = volume
        self.audio_device = audio_device
        self._pygame_initialized = False
        self._init_pygame()
        
    def _init_pygame(self):
        """Initialize pygame mixer with optional device selection."""
        try:
            import pygame
            
            # Quit if already initialized (to reinitialize with new device)
            if pygame.mixer.get_init():
                pygame.mixer.quit()
            
            # Set audio device via environment variable if specified
            if self.audio_device:
                os.environ['SDL_AUDIODRIVER'] = 'directsound'  # Windows
                # Note: pygame doesn't directly support device selection by name
                # We'll use the default device but log the requested one
                logger.info(f"Audio device requested: {self.audio_device}")
                logger.info("Note: pygame uses system default. Use Windows Sound settings to change default.")
            
            pygame.mixer.init(frequency=24000, size=-16, channels=1, buffer=2048)
            self._pygame_initialized = True
            logger.info("Pygame mixer initialized for audio playback")
            
        except Exception as e:
            logger.error(f"Failed to initialize pygame mixer: {e}")
            self._pygame_initialized = False
    
    @staticmethod
    def list_audio_devices() -> list:
        """List available audio output devices (Windows)."""
        devices = []
        try:
            # Use PowerShell to get audio devices
            import subprocess
            result = subprocess.run(
                ['powershell', '-c', 'Get-AudioDevice -List | Select-Object Index,Name,Type | ConvertTo-Json'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                import json
                data = json.loads(result.stdout)
                if isinstance(data, list):
                    devices = [d for d in data if d.get('Type') == 'Playback']
                elif isinstance(data, dict):
                    if data.get('Type') == 'Playback':
                        devices = [data]
        except Exception as e:
            logger.debug(f"Could not list audio devices: {e}")
        
        # Fallback: try sounddevice if available
        if not devices:
            try:
                import sounddevice as sd
                device_list = sd.query_devices()
                devices = [{"Index": i, "Name": d['name']} 
                          for i, d in enumerate(device_list) 
                          if d['max_output_channels'] > 0]
            except Exception:
                pass
        
        return devices
        
    @staticmethod
    async def list_voices() -> list:
        """List available edge-tts voices."""
        import edge_tts
        voices = await edge_tts.list_voices()
        return [{"name": v["ShortName"], "gender": v["Gender"], "locale": v["Locale"]} 
                for v in voices]
    
    async def speak(self, message: TTSMessage):
        """Speak a message using edge-tts."""
        import edge_tts
        
        # Convert rate to edge-tts format (percentage adjustment)
        rate_adjustment = ((self.rate - 175) / 175) * 100
        rate_str = f"+{int(rate_adjustment)}%" if rate_adjustment >= 0 else f"{int(rate_adjustment)}%"
        
        # Volume adjustment
        vol_adjustment = int((self.volume - 1.0) * 100)
        vol_str = f"+{vol_adjustment}%" if vol_adjustment >= 0 else f"{vol_adjustment}%"
        
        communicate = edge_tts.Communicate(
            message.text,
            self.voice,
            rate=rate_str,
            volume=vol_str
        )
        
        # Create temp file for audio
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            temp_path = f.name
        
        try:
            await communicate.save(temp_path)
            
            # Play using pygame
            if self._pygame_initialized:
                await self._play_with_pygame(temp_path)
            else:
                # Fallback to ffplay
                await self._play_with_ffplay(temp_path)
                
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except Exception:
                pass
    
    async def _play_with_pygame(self, audio_path: str):
        """Play audio file using pygame."""
        import pygame
        
        def _play():
            try:
                pygame.mixer.music.load(audio_path)
                pygame.mixer.music.set_volume(self.volume)
                pygame.mixer.music.play()
                
                # Wait for playback to finish
                while pygame.mixer.music.get_busy():
                    pygame.time.wait(100)
                    
            except Exception as e:
                logger.error(f"Pygame playback error: {e}")
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _play)
    
    async def _play_with_ffplay(self, audio_path: str):
        """Fallback: play audio using ffplay."""
        try:
            process = await asyncio.create_subprocess_exec(
                'ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet', 
                '-af', f'volume={self.volume}',
                audio_path,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await process.wait()
        except FileNotFoundError:
            logger.error("ffplay not found. Install ffmpeg or use pyttsx3 engine.")
        except Exception as e:
            logger.error(f"ffplay error: {e}")
    
    def stop(self):
        """Stop current speech."""
        try:
            import pygame
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception:
            pass
    
    def set_rate(self, rate: int):
        """Set speech rate."""
        self.rate = rate
    
    def set_volume(self, volume: float):
        """Set volume."""
        self.volume = volume


class TTSQueue:
    """
    Manages a queue of messages to be spoken.
    Ensures messages are spoken in order and handles rate limiting.
    """
    
    def __init__(self, engine: BaseTTSEngine, max_size: int = 50):
        self.engine = engine
        self.max_size = max_size
        self._queue: asyncio.Queue[TTSMessage] = asyncio.Queue(maxsize=max_size)
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
    async def add(self, message: TTSMessage) -> bool:
        """Add a message to the queue. Returns False if queue is full."""
        try:
            self._queue.put_nowait(message)
            return True
        except asyncio.QueueFull:
            logger.warning("TTS queue full, dropping message")
            return False
    
    async def _process_queue(self):
        """Process messages from the queue."""
        while self._running:
            try:
                message = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                try:
                    await self.engine.speak(message)
                except Exception as e:
                    logger.error(f"TTS error: {e}")
                finally:
                    self._queue.task_done()
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
    
    async def start(self):
        """Start processing the queue."""
        self._running = True
        self._task = asyncio.create_task(self._process_queue())
        logger.info("TTS queue started")
    
    async def stop(self):
        """Stop processing the queue."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.engine.stop()
        logger.info("TTS queue stopped")
    
    def clear(self):
        """Clear all pending messages."""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except asyncio.QueueEmpty:
                break
        logger.info("TTS queue cleared")
    
    @property
    def pending_count(self) -> int:
        """Number of messages waiting to be spoken."""
        return self._queue.qsize()


def create_tts_engine(engine_type: str = "pyttsx3", **kwargs) -> BaseTTSEngine:
    """Factory function to create a TTS engine."""
    if engine_type == "pyttsx3":
        return Pyttsx3Engine(**kwargs)
    elif engine_type == "edge-tts":
        return EdgeTTSEngine(**kwargs)
    else:
        raise ValueError(f"Unknown TTS engine: {engine_type}")
