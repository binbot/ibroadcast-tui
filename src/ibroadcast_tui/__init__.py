"""iBroadcast TUI - A terminal user interface for iBroadcast music service."""

from .ui.app import iBroadcastTUI
from .config.settings import settings
from .api.client import iBroadcastClient

__version__ = "0.1.0"
__all__ = ["iBroadcastTUI", "settings", "iBroadcastClient"]
