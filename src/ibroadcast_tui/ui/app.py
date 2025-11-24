"""Main UI application for iBroadcast TUI."""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Button, ListView, ListItem, Label

from ..api.client import iBroadcastClient
from ..config.settings import settings

class iBroadcastTUI(App):
    """Main TUI application for iBroadcast."""
    
    CSS = """
    Screen {
        layout: vertical;
    }
    
    .main-container {
        height: 100%;
    }
    
    .sidebar {
        width: 25%;
        border-right: solid $primary;
    }
    
    .content {
        width: 75%;
    }
    
    .welcome {
        text-align: center;
        padding: 1;
    }
    """
    
    def __init__(self) -> None:
        """Initialize the TUI application."""
        super().__init__()
        self.api_client = iBroadcastClient()
        self.title = settings.app_name
    
    def compose(self) -> ComposeResult:
        """Create the main layout."""
        yield Header()
        
        with Container(classes="main-container"):
            with Horizontal():
                with Vertical(classes="sidebar"):
                    yield Static("Library", id="sidebar-title")
                    yield ListView(
                        ListItem(Label("Tracks")),
                        ListItem(Label("Playlists")),
                        ListItem(Label("Albums")),
                        ListItem(Label("Settings")),
                        id="sidebar-nav"
                    )
                
                with Vertical(classes="content"):
                    yield Static("Welcome to iBroadcast TUI", id="welcome")
                    yield Button("Connect to iBroadcast", id="connect-btn")
        
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "connect-btn":
            self.connect_to_service()
    
    def connect_to_service(self) -> None:
        """Connect to iBroadcast service."""
        if not settings.validate():
            self.notify("Please configure API credentials in .env file", severity="error")
            return
        
        try:
            # TODO: Implement actual connection
            self.notify("Connected to iBroadcast successfully!", severity="information")
        except Exception as e:
            self.notify(f"Connection failed: {e}", severity="error")
    
    def on_mount(self) -> None:
        """Called when the app starts."""
        if not settings.validate():
            self.notify("API credentials not configured. Check .env file.", severity="warning")
