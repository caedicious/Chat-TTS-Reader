"""TikTok Live chat handler using TikTokLive library."""

import asyncio
import logging
import subprocess
import sys
import threading
from datetime import datetime
from typing import Optional
from queue import Queue, Empty
import json

from .base import BaseChatHandler, ChatMessage

logger = logging.getLogger(__name__)


# Try to install and use nest_asyncio to handle nested event loops
try:
    import nest_asyncio
    nest_asyncio.apply()
    NEST_ASYNCIO_AVAILABLE = True
except ImportError:
    NEST_ASYNCIO_AVAILABLE = False
    logger.warning("nest_asyncio not available - TikTok may have issues")


class TikTokChatHandler(BaseChatHandler):
    """
    Handler for TikTok Live chat using the TikTokLive library.
    
    Uses a subprocess approach to completely isolate the TikTok event loop.
    """
    
    def __init__(self, username: str):
        super().__init__("TikTok")
        self.username = username.lstrip('@')
        self._message_queue: Queue = Queue()
        self._process: Optional[subprocess.Popen] = None
        self._reader_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
    def _create_worker_script(self) -> str:
        """Generate the worker script content."""
        return f'''
import asyncio
import json
import sys

async def main():
    try:
        from TikTokLive import TikTokLiveClient
        from TikTokLive.events import ConnectEvent, CommentEvent, DisconnectEvent
        
        client = TikTokLiveClient(unique_id="@{self.username}")
        
        @client.on(ConnectEvent)
        async def on_connect(event):
            print(json.dumps({{"type": "connected"}}), flush=True)
        
        @client.on(DisconnectEvent)
        async def on_disconnect(event):
            print(json.dumps({{"type": "disconnected"}}), flush=True)
        
        @client.on(CommentEvent)
        async def on_comment(event):
            msg = {{
                "type": "message",
                "username": event.user.nickname or event.user.unique_id,
                "message": event.comment,
                "user_id": str(getattr(event.user, 'user_id', '')),
            }}
            print(json.dumps(msg), flush=True)
        
        await client.run()
        
    except Exception as e:
        print(json.dumps({{"type": "error", "message": str(e)}}), flush=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    def _reader_worker(self):
        """Thread that reads output from the subprocess."""
        if not self._process:
            return
            
        try:
            for line in iter(self._process.stdout.readline, ''):
                if self._stop_event.is_set():
                    break
                    
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    data = json.loads(line)
                    msg_type = data.get('type')
                    
                    if msg_type == 'message':
                        self._message_queue.put(data)
                    elif msg_type == 'connected':
                        logger.info(f"TikTok subprocess connected to @{self.username}")
                    elif msg_type == 'disconnected':
                        logger.info(f"TikTok subprocess disconnected from @{self.username}")
                    elif msg_type == 'error':
                        logger.error(f"TikTok subprocess error: {data.get('message')}")
                        
                except json.JSONDecodeError:
                    # Not JSON, might be a log line
                    if 'not live' in line.lower():
                        logger.warning(f"@{self.username} is not currently live")
                    else:
                        logger.debug(f"TikTok output: {line}")
                        
        except Exception as e:
            logger.error(f"TikTok reader error: {e}")
            
    async def connect(self) -> bool:
        """Start TikTok chat subprocess."""
        try:
            # Write worker script to temp file
            import tempfile
            import os
            
            script_content = self._create_worker_script()
            
            # Create temp script file
            fd, script_path = tempfile.mkstemp(suffix='.py', prefix='tiktok_worker_')
            try:
                os.write(fd, script_content.encode())
            finally:
                os.close(fd)
            
            self._script_path = script_path
            
            # Start subprocess
            self._process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Start reader thread
            self._stop_event.clear()
            self._reader_thread = threading.Thread(target=self._reader_worker, daemon=True)
            self._reader_thread.start()
            
            # Give it a moment to start
            await asyncio.sleep(2)
            
            if self._process.poll() is None:
                logger.info(f"TikTok subprocess started for @{self.username}")
                return True
            else:
                logger.error("TikTok subprocess exited immediately")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start TikTok subprocess: {e}")
            return False
    
    async def disconnect(self):
        """Stop TikTok chat subprocess."""
        self._stop_event.set()
        
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=3)
            except Exception:
                try:
                    self._process.kill()
                except Exception:
                    pass
            self._process = None
        
        # Clean up temp script
        if hasattr(self, '_script_path'):
            try:
                import os
                os.unlink(self._script_path)
            except Exception:
                pass
    
    async def _listen_loop(self):
        """Listen for TikTok messages from the queue."""
        while self._running:
            try:
                # Check if subprocess died
                if self._process and self._process.poll() is not None:
                    logger.warning("TikTok subprocess died, attempting restart...")
                    await asyncio.sleep(5)
                    if await self.connect():
                        continue
                    else:
                        break
                
                # Get messages from queue
                try:
                    msg_data = self._message_queue.get_nowait()
                    
                    message = ChatMessage(
                        platform="TikTok",
                        username=msg_data['username'],
                        message=msg_data['message'],
                        timestamp=datetime.now(),
                        user_id=msg_data.get('user_id', ''),
                        is_moderator=False,
                        is_subscriber=False,
                        badges=[]
                    )
                    
                    await self._emit_message(message)
                    
                except Empty:
                    await asyncio.sleep(0.1)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"TikTok listen error: {e}")
                await asyncio.sleep(1)
        
        logger.info("TikTok chat loop ended")
