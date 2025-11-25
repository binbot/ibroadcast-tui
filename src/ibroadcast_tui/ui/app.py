"""Main UI application for iBroadcast TUI."""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, Button, ListView, ListItem, Label, TabbedContent, TabPane

from ..api.client import iBroadcastClient
from ..config.settings import settings

class iBroadcastTUI(App):
    """Main TUI application for iBroadcast."""
    
    CSS = """
    Screen {
        layout: vertical;
        background: $surface-darken-3;
    }

    .main-container {
        height: 100%;
    }

    .sidebar {
        width: 25%;
        border-right: solid $primary-darken-1;
        background: $surface-darken-2;
    }

    .content {
        width: 75%;
        background: $surface-darken-3;
    }

    /* Retro terminal color scheme */
    Header {
        background: $success-darken-3;
        color: $text;
        text-style: bold;
        border-bottom: solid $primary;
    }

    Footer {
        background: $surface-darken-2;
        color: $text-muted;
        border-top: solid $primary-darken-1;
    }

    Button {
        background: $primary-darken-1;
        color: $text;
        border: solid $primary;
    }

    Button:hover {
        background: $primary;
        border: solid $primary-lighten-1;
    }

    /* Tab styling */
    TabbedContent {
        background: $surface-darken-3;
    }

    TabPane {
        background: $surface-darken-3;
        padding: 1;
        border: solid $primary-darken-2;
        border-radius: 1;
    }

    /* Content styling */
    .section-header {
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
        border-bottom: solid $primary-darken-1;
    }

    .album-item, .artist-item, .playlist-item, .track-item {
        color: $text;
        margin-left: 1;
        margin-bottom: 0;
    }

    .album-item:hover, .artist-item:hover, .playlist-item:hover, .track-item:hover {
        background: $primary-darken-3;
        color: $text;
    }

    .message {
        color: $text-muted;
        text-style: italic;
    }

    /* Welcome screen */
    .welcome {
        text-align: center;
        padding: 2;
        color: $text;
        text-style: bold;
    }

    /* Status indicators */
    .status-playing {
        color: $success;
        text-style: bold;
    }

    .status-paused {
        color: $warning;
    }

    .status-stopped {
        color: $error;
    }

    /* Scrollable areas */
    ScrollableContainer {
        height: 100%;
        border: solid $primary-darken-2;
        background: $surface-darken-3;
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
                        # Show detailed music library with tabs
                        with TabbedContent():
                            with TabPane("📀 Albums", id="albums-tab"):
                                yield self._create_albums_view()
                            with TabPane("🎤 Artists", id="artists-tab"):
                                yield self._create_artists_view()
                            with TabPane("📋 Playlists", id="playlists-tab"):
                                yield self._create_playlists_view()
                            with TabPane("🎵 Tracks", id="tracks-tab"):
                                yield self._create_tracks_view()
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

    def _create_albums_view(self) -> Static:
        """Create the albums view."""
        if not self.library_data or "albums" not in self.library_data:
            return Static("No albums data available", classes="message")

        albums = self.library_data["albums"]
        if not albums:
            return Static("No albums found", classes="message")

        # Create content as a single multi-line string
        lines = []
        lines.append(f"📀 Albums ({len(albums)})")

        # Sort albums by name (album data is stored as lists)
        def get_album_name(item):
            album_id, album_data = item
            if isinstance(album_data, list) and len(album_data) > 0:
                return str(album_data[0]).lower()
            return ""

        sorted_albums = sorted(albums.items(), key=get_album_name)

        # Display albums (limit for performance)
        for album_id, album_data in sorted_albums[:30]:  # Reduced limit
            if isinstance(album_data, list) and len(album_data) >= 3:
                album_name = album_data[0]
                track_ids = album_data[1] if len(album_data) > 1 else []
                artist_id = album_data[2]
                year = album_data[3] if len(album_data) > 3 else "Unknown"

                # Get artist name
                artist_name = "Unknown Artist"
                if "artists" in self.library_data:
                    artist_data = self.library_data["artists"].get(str(artist_id))
                    if artist_data and isinstance(artist_data, dict):
                        artist_name = artist_data.get("name", "Unknown Artist")

                tracks_count = len(track_ids)
                lines.append(f"  {album_name} - {artist_name} ({year}) • {tracks_count} tracks")

        if len(sorted_albums) > 30:
            lines.append(f"  ... and {len(sorted_albums) - 30} more albums")

        # Create single Static widget with all content
        content = "\n".join(lines)
        return Static(content, classes="albums-content")

    def _create_artists_view(self) -> Static:
        """Create the artists view."""
        if not self.library_data or "artists" not in self.library_data:
            return Static("No artists data available", classes="message")

        artists = self.library_data["artists"]
        if not artists:
            return Static("No artists found", classes="message")

        # Create content as a single multi-line string
        lines = []
        lines.append(f"🎤 Artists ({len(artists)})")

        # Sort artists by name (artist data is stored as lists)
        def get_artist_name(item):
            artist_id, artist_data = item
            if isinstance(artist_data, list) and len(artist_data) > 0:
                return str(artist_data[0]).lower()
            return ""

        sorted_artists = sorted(artists.items(), key=get_artist_name)

        # Display artists (limit for performance)
        for artist_id, artist_data in sorted_artists[:30]:
            if isinstance(artist_data, list) and len(artist_data) >= 2:
                artist_name = artist_data[0]  # Artist name
                track_ids = artist_data[1] if len(artist_data) > 1 else []  # Track IDs
                tracks_count = len(track_ids) if isinstance(track_ids, list) else 0

                lines.append(f"  {artist_name} • {tracks_count} tracks")

        if len(sorted_artists) > 30:
            lines.append(f"  ... and {len(sorted_artists) - 30} more artists")

        # Create single Static widget with all content
        content = "\n".join(lines)
        return Static(content, classes="artists-content")

    def _create_playlists_view(self) -> Static:
        """Create the playlists view."""
        if not self.library_data or "playlists" not in self.library_data:
            return Static("No playlists data available", classes="message")

        playlists = self.library_data["playlists"]
        if not playlists:
            return Static("No playlists found", classes="message")

        # Create content as a single multi-line string
        lines = []
        lines.append(f"📋 Playlists ({len(playlists)})")

        # Sort playlists by name (playlist data is stored as lists)
        def get_playlist_name(item):
            playlist_id, playlist_data = item
            if isinstance(playlist_data, list) and len(playlist_data) > 0:
                return str(playlist_data[0]).lower()
            return ""

        sorted_playlists = sorted(playlists.items(), key=get_playlist_name)

        # Display playlists
        for playlist_id, playlist_data in sorted_playlists:
            if isinstance(playlist_data, list) and len(playlist_data) >= 2:
                playlist_name = playlist_data[0]  # Playlist name
                track_ids = playlist_data[1] if len(playlist_data) > 1 else []  # Track IDs
                tracks_count = len(track_ids) if isinstance(track_ids, list) else 0

                lines.append(f"  {playlist_name} • {tracks_count} tracks")

        # Create single Static widget with all content
        content = "\n".join(lines)
        return Static(content, classes="playlists-content")

    def _create_tracks_view(self) -> Static:
        """Create the tracks view."""
        if not self.library_data or "tracks" not in self.library_data:
            return Static("No tracks data available", classes="message")

        tracks = self.library_data["tracks"]
        if not tracks:
            return Static("No tracks found", classes="message")

        # Create content as a single multi-line string
        lines = []
        lines.append(f"🎵 Tracks ({len(tracks)})")

        # Sort tracks by title (track data is stored as lists)
        def get_track_title(item):
            track_id, track_data = item
            if isinstance(track_data, list) and len(track_data) >= 3:
                return str(track_data[2]).lower()  # Title is at index 2
            return ""

        sorted_tracks = sorted(tracks.items(), key=get_track_title)

        # Display tracks (limit for performance)
        for track_id, track_data in sorted_tracks[:50]:
            if isinstance(track_data, list) and len(track_data) >= 7:
                track_title = track_data[2]  # Title at index 2
                artist_id = track_data[6]    # Artist ID at index 6
                album_id = track_data[5]     # Album ID at index 5

                # Get artist name
                artist_name = "Unknown Artist"
                if "artists" in self.library_data:
                    artist_data = self.library_data["artists"].get(str(artist_id))
                    if artist_data and isinstance(artist_data, list) and len(artist_data) > 0:
                        artist_name = artist_data[0]

                # Get album name
                album_name = "Unknown Album"
                if "albums" in self.library_data:
                    album_data = self.library_data["albums"].get(str(album_id))
                    if album_data and isinstance(album_data, list) and len(album_data) > 0:
                        album_name = album_data[0]

                lines.append(f"  {track_title} - {artist_name} ({album_name})")

        if len(sorted_tracks) > 50:
            lines.append(f"  ... and {len(sorted_tracks) - 50} more tracks")

        # Create single Static widget with all content
        content = "\n".join(lines)
        return Static(content, classes="tracks-content")

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