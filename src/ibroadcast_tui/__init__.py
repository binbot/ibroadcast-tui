"""iBroadcast TUI - A terminal user interface for iBroadcast music service."""

from .ui.app import iBroadcastTUI
from .config.settings import settings
from .config.token_manager import token_manager
from .api.client import iBroadcastClient

__version__ = "0.1.0"
__all__ = ["iBroadcastTUI", "settings", "token_manager", "iBroadcastClient"]
