"""Main UI application for iBroadcast TUI."""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Button, ListView, ListItem, Label
from textual.reactive import reactive

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
    
    /* Retro terminal styling */
    Header {
        background: $primary-darken-2;
        color: $text;
        text-style: bold;
    }
    
    Footer {
        background: $primary-darken-2;
        color: $text-muted;
    }
    
    Button {
        background: $primary;
        color: $text;
        border: solid $primary-lighten-1;
    }
    
    Button:hover {
        background: $primary-lighten-1;
    }
    
    ListView {
        background: $surface;
        color: $text;
        border: solid $primary-darken-1;
    }
    
    ListItem {
        color: $text;
    }
    
    ListItem:hover {
        background: $primary-darken-3;
    }
    
    .header {
        color: $text;
        text-style: bold;
        margin-bottom: 1;
    }
    
    .stat {
        color: $text;
        margin-left: 2;
    }
    
    .placeholder {
        color: $text-muted;
        text-style: italic;
    }
    """
    
    def __init__(self) -> None:
        """Initialize the TUI application."""
        super().__init__()
        self.api_client = iBroadcastClient()
        self.title = settings.app_name
        self.library_data = None
        self.show_library = False
    
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
                
                with Vertical(classes="content", id="content-container"):
                    if self.library_data:
                        # Show music library stats
                        albums = len(self.library_data.get("albums", {}))
                        artists = len(self.library_data.get("artists", {}))
                        tracks = len(self.library_data.get("tracks", {}))
                        playlists = len(self.library_data.get("playlists", {}))

                        yield Static("🎵 iBroadcast Library Loaded!", classes="header")
                        yield Static(f"📀 {albums} albums", classes="stat")
                        yield Static(f"🎤 {artists} artists", classes="stat")
                        yield Static(f"🎵 {tracks} tracks", classes="stat")
                        yield Static(f"📋 {playlists} playlists", classes="stat")
                        yield Static("", classes="spacer")
                        yield Static("🎨 Retro styling and detailed views coming soon!", classes="placeholder")
                    else:
                        # Show welcome screen
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
        print("DEBUG: _load_library called")
        try:
            self.notify("Discovering iBroadcast API endpoints...", severity="information")
            result = self.api_client.get_library()
            print(f"DEBUG: Library result: {result['status']}")

            if result["status"] == "success":
                data = result.get("data", {})
                print(f"DEBUG: Data keys: {list(data.keys()) if data else 'No data'}")
                self.library_data = data
                print(f"DEBUG: Library data set: {bool(self.library_data)}")

                # Try to refresh the screen to show new content
                try:
                    self.screen.refresh()
                except Exception as e:
                    print(f"Screen refresh failed: {e}")
            if result["status"] == "success":
                endpoint = result.get("endpoint", "unknown")
                data = result.get("data", {})
                
                # Store library data
                self.library_data = data
                
                # Show success with data summary
                if isinstance(data, dict) and data:
                    albums_count = len(data.get("albums", {}))
                    artists_count = len(data.get("artists", {}))
                    tracks_count = len(data.get("tracks", {}))
                    playlists_count = len(data.get("playlists", {}))
                    
                    self.notify(f"Library loaded! {albums_count} albums, {artists_count} artists, {tracks_count} tracks, {playlists_count} playlists", severity="information")
                    
                    # Schedule UI update for after screen is ready
                    from textual import events
                    self.post_message(events.Compose())
                else:
                    self.notify(f"Connected! Using endpoint: {endpoint}. No data structure available yet.", severity="information")
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
            return

        # Check if we have stored session data and try to load library
        if self.api_client.user_id and self.api_client.token:
            self.notify("Loading stored session...", severity="information")
            self._load_library()
        elif self.api_client.authenticate()["status"] == "success":
            self.notify("Authenticated successfully!", severity="information")
            self._load_library()