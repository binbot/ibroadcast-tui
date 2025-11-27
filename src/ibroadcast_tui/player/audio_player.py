
"""Audio player implementation using miniaudio."""

import logging
import threading
import time
from typing import Optional, Dict, Any, Callable
import miniaudio
import httpx

logger = logging.getLogger(__name__)

class StreamSource:
    """Wrapper for generator to satisfy miniaudio requirements."""
    def __init__(self, generator):
        self.generator = generator
        self.buffer = b""
        self.error_in_readcallback = None

    def read(self, size):
        while len(self.buffer) < size:
            try:
                chunk = next(self.generator)
                self.buffer += chunk
            except StopIteration:
                break
        
        data = self.buffer[:size]
        self.buffer = self.buffer[size:]
        return data

    def seek(self, offset, origin):
        return 0

    def tell(self):
        return 0

class AudioPlayer:
    """Audio player wrapper around miniaudio."""

    def __init__(self, on_track_end: Optional[Callable] = None):
        """Initialize the audio player."""
        logger.info("Initializing AudioPlayer")
        self.on_track_end = on_track_end
        self.current_track: Optional[Dict[str, Any]] = None
        self._is_initialized = True
        
        # Playback state
        self._playback_thread = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set() # Start unpaused (set means true/active/not-blocked? wait, Event.wait() blocks if clear. So set() means go.)
        
        self.state = "stopped"
        self.position = 0.0
        self.duration = 0.0
        self.volume = 100
        logger.info("AudioPlayer initialized")

    @property
    def is_available(self) -> bool:
        """Check if audio playback is available."""
        return True

    def play(self, url: str, track_info: dict) -> bool:
        """Start playback of a URL."""
        logger.info(f"AudioPlayer.play called for URL: {url}")
        try:
            self.stop()
            
            self.current_track = track_info
            self._stop_event.clear()
            self._pause_event.set() # Ensure playback starts unpaused
            self.state = "playing"
            self.position = 0.0
            
            logger.info("Starting playback thread")
            self._playback_thread = threading.Thread(target=self._playback_loop, args=(url,))
            self._playback_thread.daemon = True
            self._playback_thread.start()
            
            return True
        except Exception as e:
            logger.error(f"Failed to start playback: {e}", exc_info=True)
            self.state = "error"
            return False

    def _playback_loop(self, url: str):
        """Internal playback loop."""
        logger.debug(f"Playback loop started for URL: {url}")
        try:
            with httpx.stream("GET", url) as response:
                if response.status_code != 200:
                    logger.error(f"Failed to stream: {response.status_code} for URL: {url}")
                    self.state = "error"
                    return

                def audio_stream():
                    for chunk in response.iter_bytes(chunk_size=4096):
                        if self._stop_event.is_set():
                            break
                        yield chunk

                stream_source = StreamSource(audio_stream())
                
                try:
                    decoder = miniaudio.stream_any(stream_source, source_format=miniaudio.FileFormat.MP3)
                    next(decoder) # Prime
                except Exception as e:
                    logging.error(f"Decoder init failed: {e}")
                    self.state = "error"
                    return

                def playback_callback_gen():
                    required_frames = yield b""
                    while not self._stop_event.is_set():
                        # Handle pausing
                        if not self._pause_event.is_set():
                            # If paused, yield silence
                            # We need to calculate silence bytes: frames * channels * 2 (16bit)
                            silence = b"\x00" * (required_frames * 2 * 2)
                            required_frames = yield silence
                            continue

                        try:
                            data = decoder.send(required_frames)
                            # Update position (rough estimate)
                            # 44100 Hz * 2 channels * 2 bytes = 176400 bytes/sec
                            # This is very rough and depends on sample rate
                            self.position += len(data) / 176400.0
                            required_frames = yield data
                        except StopIteration:
                            break
                        except Exception as e:
                            logging.error(f"Callback error: {e}")
                            yield b""

                with miniaudio.PlaybackDevice(output_format=miniaudio.SampleFormat.SIGNED16,
                                            nchannels=2,
                                            sample_rate=44100) as device:
                    gen = playback_callback_gen()
                    next(gen)
                    device.start(gen)
                    
                    while not self._stop_event.is_set() and device.running:
                        time.sleep(0.1)
                        if not self._playback_thread.is_alive(): # Should be self? No.
                            pass

                    # If we exited loop naturally (not stopped), track ended
                    if not self._stop_event.is_set():
                        self.state = "stopped"
                        if self.on_track_end:
                            self.on_track_end()

        except Exception as e:
            logging.error(f"Playback error: {e}")
            self.state = "error"
        finally:
            self.state = "stopped"

    def pause(self) -> None:
        """Toggle pause state."""
        if self.state == "playing":
            self._pause_event.clear()
            self.state = "paused"
        elif self.state == "paused":
            self._pause_event.set()
            self.state = "playing"

    def stop(self) -> None:
        """Stop playback."""
        self._stop_event.set()
        if self._playback_thread and self._playback_thread.is_alive():
            self._playback_thread.join(timeout=1.0)
        self.state = "stopped"
        self.current_track = None

    def seek(self, position: float) -> None:
        """Seek to position in seconds."""
        # Not implemented for streaming
        pass

    def set_volume(self, volume: int) -> None:
        """Set volume (0-100)."""
        self.volume = volume

    def get_status(self) -> Dict[str, Any]:
        """Get current player status."""
        return {
            "state": self.state,
            "position": self.position,
            "duration": 0, # Unknown for stream
            "volume": self.volume,
            "track": self.current_track
        }
