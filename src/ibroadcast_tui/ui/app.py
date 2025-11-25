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
                    yield Button("Discover API Endpoints", id="discover-btn")
        
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "connect-btn":
            self.connect_to_service()
        elif event.button.id == "discover-btn":
            self.discover_endpoints()
    
    def connect_to_service(self) -> None:
        """Connect to iBroadcast service."""
        if not settings.validate():
            self.notify("Please configure username and password in .env file", severity="error")
            return

        try:
            # Show authenticating message
            self.notify("Authenticating with iBroadcast...", severity="information")

            result = self.api_client.authenticate()
            if result["status"] == "success":
                self.notify(f"Connected to iBroadcast! {result['message']}", severity="information")
                # Try to fetch library to show we have real data
                self._load_library()
            else:
                self.notify(f"Authentication failed: {result['message']}", severity="error")
        except Exception as e:
            self.notify(f"Connection failed: {e}", severity="error")
    
    def discover_endpoints(self) -> None:
        """Discover and display API endpoints."""
        try:
            self.notify("Discovering iBroadcast API endpoints...", severity="information")
            result = self.api_client._discover_api_endpoints()
            if result["status"] == "success":
                endpoints = result["endpoints"]
                available_endpoints = [ep for ep, info in endpoints.items() if info.get("available")]
                
                if available_endpoints:
                    self.notify(f"Working endpoints: {', '.join(available_endpoints)}", severity="information")
                else:
                    self.notify("No working endpoints found. Check API credentials.", severity="warning")
                    
                # Show all tested endpoints
                tested_endpoints = list(endpoints.keys())
                self.notify(f"Tested endpoints: {', '.join(tested_endpoints)}", severity="information")
            else:
                self.notify(f"Endpoint discovery failed: {result.get('message', 'Unknown error')}", severity="error")
        except Exception as e:
            self.notify(f"Endpoint discovery failed: {e}", severity="error")
    
    def _load_library(self) -> None:
        """Load and display library information."""
        try:
            self.notify("Discovering iBroadcast API endpoints...", severity="information")
            result = self.api_client.get_library()
            if result["status"] == "success":
                endpoint = result.get("endpoint", "unknown")
                data = result.get("data", {})
                
                # Show success with endpoint info
                if isinstance(data, dict) and data:
                    data_keys = list(data.keys())[:5]  # Show first 5 keys
                    self.notify(f"Connected! Using endpoint: {endpoint}. Data keys: {', '.join(data_keys)}", severity="information")
                else:
                    self.notify(f"Connected! Using endpoint: {endpoint}. No data structure available Yet.", severity="information")
            else:
                message = result.get("message", "Unknown error")
                self.notify(f"Failed to load library: {message}", severity="error")
                
                # Show discovery info if available
                if "discovered" in result:
                    discovery = result["discovered"]
                    if discovery.get("status") == "success":
                        available_endpoints = [ep for ep, info in discovery["endpoints"].items() if info.get("available")]
                        if available_endpoints:
                            self.notify(f"Available endpoints found: {', '.join(available_endpoints)}", severity="information")
                        
        except Exception as e:
            self.notify(f"Library loading failed: {e}", severity="error")
    
    def on_mount(self) -> None:
        """Called when the app starts."""
        if not settings.validate():
            self.notify("Username and password not configured. Check .env file.", severity="warning")