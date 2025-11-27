"""Audio player implementation using python-mpv."""

import logging
from typing import Optional, Dict, Any, Callable

try:
    import mpv
    MPV_AVAILABLE = True
except (ImportError, OSError):
    MPV_AVAILABLE = False
    mpv = None

class AudioPlayer:
    """Audio player wrapper around mpv."""

    def __init__(self, on_track_end: Optional[Callable] = None):
        """Initialize the audio player."""
        self.player = None
        self.on_track_end = on_track_end
        self.current_track: Optional[Dict[str, Any]] = None
        self._is_initialized = False
        
        if MPV_AVAILABLE:
            try:
                # Initialize mpv with minimal options
                self.player = mpv.MPV(input_default_bindings=True, input_vo_keyboard=True, osc=True)
                
                # Set up event callbacks
                @self.player.event_callback('end-file')
                def end_file_callback(event):
                    if event.get('reason') == 0:  # End of file
                        if self.on_track_end:
                            self.on_track_end()
                            
                self._is_initialized = True
            except Exception as e:
                logging.error(f"Failed to initialize mpv: {e}")

    @property
    def is_available(self) -> bool:
        """Check if audio playback is available."""
        return self._is_initialized

    def play(self, url: str, track_info: Dict[str, Any]) -> bool:
        """Play a track from URL."""
        if not self._is_initialized:
            return False

        try:
            self.player.play(url)
            self.current_track = track_info
            return True
        except Exception as e:
            logging.error(f"Failed to play track: {e}")
            return False

    def pause(self) -> None:
        """Toggle pause state."""
        if self._is_initialized:
            self.player.pause = not self.player.pause

    def stop(self) -> None:
        """Stop playback."""
        if self._is_initialized:
            self.player.stop()
            self.current_track = None

    def seek(self, position: float) -> None:
        """Seek to position in seconds."""
        if self._is_initialized:
            self.player.time_pos = position

    def set_volume(self, volume: int) -> None:
        """Set volume (0-100)."""
        if self._is_initialized:
            self.player.volume = max(0, min(100, volume))

    def get_status(self) -> Dict[str, Any]:
        """Get current player status."""
        if not self._is_initialized:
            return {
                "state": "stopped",
                "position": 0,
                "duration": 0,
                "volume": 0,
                "track": None
            }

        try:
            # Determine state
            state = "stopped"
            if self.player.core_idle:
                state = "stopped"
            elif self.player.pause:
                state = "paused"
            else:
                state = "playing"

            return {
                "state": state,
                "position": self.player.time_pos or 0,
                "duration": self.player.duration or 0,
                "volume": self.player.volume or 0,
                "track": self.current_track
            }
        except Exception:
            return {
                "state": "error",
                "position": 0,
                "duration": 0,
                "volume": 0,
                "track": self.current_track
            }
