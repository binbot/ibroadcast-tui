"""Main UI application for iBroadcast TUI."""

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Static, Button, DataTable

from ..api.client import iBroadcastClient
from ..config.settings import settings
from ..data_manager import DataManager

# Audio playback (optional)
try:
    import pygame
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    pygame = None

class iBroadcastTUI(App):
    """Main TUI application for iBroadcast."""
    
    CSS = """
    /* iBroadcast TUI - Clean Terminal Interface */

    Screen {
        background: transparent;
        color: white;
    }

    /* Layout */
    Horizontal {
        height: 100%;
    }

    .sidebar {
        width: 25;
        background: transparent;
        padding: 1;
    }

    .main-content {
        width: 1fr;
        background: transparent;
        padding: 1;
    }

    .player-section {
        width: 30;
        background: transparent;
        padding: 1;
        border-left: solid gray;
    }

    /* Sidebar */
    .sidebar-title {
        color: cyan;
        text-style: bold;
        text-align: center;
        margin-bottom: 1;
    }

    .sidebar-separator {
        color: gray;
        text-align: center;
        margin-bottom: 1;
    }

    .nav-item {
        width: 100%;
        background: transparent;
        text-align: left;
        padding: 0 1;
        margin-bottom: 0;
        height: 1;
    }

    .nav-item:hover {
        background: transparent;
        text-style: bold;
        color: cyan;
    }

    .nav-item:focus {
        background: transparent;
        text-style: bold underline;
        color: cyan;
    }

    /* Content Area - Make it scrollable */
    .content-area {
        height: 1fr;
        border: none;
        background: transparent;
        padding: 0;
        overflow-y: auto;
    }

    /* Welcome screen */
    .welcome {
        color: cyan;
        text-style: bold;
        text-align: center;
        margin: 2 0;
    }

    .welcome-text {
        text-align: center;
        margin: 1 0;
    }

    .connect-btn {
        background: transparent;
        color: cyan;
        text-align: center;
        text-style: bold;
    }

    .connect-btn:hover {
        background: transparent;
        color: white;
        text-style: bold underline;
    }

    /* Player section */
    .player-label {
        color: cyan;
        text-style: bold;
        margin-bottom: 0;
    }

    .player-status {
        color: white;
        text-style: bold;
        margin-bottom: 1;
    }

    .progress-bar {
        color: gray;
        text-align: center;
        margin-bottom: 0;
    }

    .time-display {
        color: white;
        text-align: center;
        margin-bottom: 1;
    }

    .player-controls {
        /* Controls container */
    }

    .player-btn {
        width: 3;
        text-align: center;
    }

    .player-status {
        color: cyan;
        text-style: bold;
        width: 25;
    }

    .player-btn {
        width: 3;
        text-align: center;
        margin: 0 1;
    }

    .progress-bar {
        color: gray;
        text-align: center;
    }

    .time-display {
        color: white;
        width: 10;
        text-align: right;
    }

    /* Footer */
    Footer {
        background: transparent;
        color: gray;
        height: 1;
        text-align: center;
    }

    /* Scrollable content */
    ScrollableContainer {
        scrollbar-background: transparent;
        scrollbar-color: cyan;
        scrollbar-color-active: cyan;
    }

    /* Buttons */
    Button {
        border: none;
        background: transparent;
        color: white;
    }

    Button:hover {
        background: transparent;
        color: cyan;
        text-style: bold;
    }

    Button:focus {
        background: transparent;
        color: cyan;
        text-style: bold underline;
    }

    /* View headers */
    .view-header {
        color: white;
        text-style: bold;
        text-align: center;
        margin-bottom: 1;
    }

    /* DataTable styling */
    DataTable {
        height: 1fr;
        border: none;
        background: transparent;
    }

    DataTable > .datatable--header {
        background: transparent;
        color: cyan;
        text-style: bold;
    }

    DataTable > .datatable--cursor {
        background: cyan;
        color: black;
    }

    DataTable > .datatable--hover {
        background: transparent;
        color: cyan;
        text-style: bold;
    }

    /* Legacy button styles (for navigation) */
    .album-item, .artist-item, .playlist-item, .track-item {
        width: 100%;
        text-align: left;
        padding: 0 1;
        margin-bottom: 0;
        height: 1;
    }

    .album-item:hover, .artist-item:hover, .playlist-item:hover, .track-item:hover {
        background: transparent;
        text-style: bold;
        color: cyan;
    }
    """
    
    def __init__(self) -> None:
        """Initialize the TUI application."""
        super().__init__()
        self.api_client = iBroadcastClient()
        self.data_manager = DataManager()
        self.title = settings.app_name
        self.library_data = None
        self.show_library = False
        self.load_error = None
        self.current_view = "albums"  # Default view

        # DataTable handles scrolling internally - no pagination needed

        # Audio playback state
        self.current_track = None
        self.playback_state = "stopped"  # stopped, playing, paused
        self.audio_initialized = False



    def compose(self) -> ComposeResult:
        """Create the main layout."""
        # Main horizontal layout: sidebar + content + player
        with Horizontal():
            # Left sidebar navigation
            with Vertical(classes="sidebar"):
                yield Static("🎵 iBroadcast", classes="sidebar-title")
                yield Static("─" * 20, classes="sidebar-separator")

                # Navigation items
                yield Button("📀 Albums", id="nav-albums", classes="nav-item")
                yield Button("🎤 Artists", id="nav-artists", classes="nav-item")
                yield Button("📋 Playlists", id="nav-playlists", classes="nav-item")
                yield Button("🎵 Tracks", id="nav-tracks", classes="nav-item")
                yield Button("🔍 Search", id="nav-search", classes="nav-item")

            # Main content area (takes most space)
            with Vertical(classes="main-content"):
                if self.show_library and self.library_data:
                    # Header with item count
                    total_items = self._get_total_items_for_current_view()
                    if self.current_view == "albums":
                        yield Static(f"📀 Albums ({total_items})", classes="view-header")
                    elif self.current_view == "artists":
                        yield Static(f"🎤 Artists ({total_items})", classes="view-header")
                    elif self.current_view == "playlists":
                        yield Static(f"📋 Playlists ({total_items})", classes="view-header")
                    elif self.current_view == "tracks":
                        yield Static(f"🎵 Tracks ({total_items})", classes="view-header")

                    # Single DataTable view for all categories
                    yield from self._create_datatable_view()
                else:
                    # Welcome screen
                    yield Static("🎵 WELCOME TO IBROADCAST TUI 🎵", classes="welcome", id="welcome")
                    yield Static("Configure your credentials in .env file, then click connect.", classes="welcome-text")
                    yield Button("🔗 Connect to iBroadcast", id="connect-btn", classes="connect-btn")

            # Player section on the right
            with Vertical(classes="player-section"):
                yield Static("Now Playing:", classes="player-label")
                yield Static("[Not Playing]", classes="player-status", id="player-status")
                yield Static("─────●─────────", classes="progress-bar", id="progress-bar")
                yield Static("0:00 / 0:00", classes="time-display", id="time-display")

                # Player controls
                with Horizontal(classes="player-controls"):
                    yield Button("⏮", id="player-prev", classes="player-btn")
                    yield Button("⏯", id="player-play", classes="player-btn")
                    yield Button("⏸", id="player-pause", classes="player-btn")
                    yield Button("⏹", id="player-stop", classes="player-btn")
                    yield Button("⏭", id="player-next", classes="player-btn")

        yield Footer()

    def on_mount(self) -> None:
        """Called when the app is mounted."""
        # Disabled auto-loading for now - manual connection works
        pass

    async def load_library_on_mount(self) -> None:
        """Load library data on mount."""
        await self._load_library_async()
    
    def discover_endpoints(self) -> None:
        """Discover and display API endpoints."""
        try:
            self.notify("API endpoint discovery not implemented yet", severity="information")
            self.notify("Library loading works - use 'Connect to iBroadcast' instead", severity="information")
        except Exception as e:
            self.notify(f"Endpoint discovery failed: {e}", severity="error")
    
    async def _load_library_async(self) -> None:
        """Load library data asynchronously."""
        try:
            self.notify("Loading iBroadcast library...", severity="information")

            # Load data asynchronously
            data = await self.data_manager.load_library_async()

            # Store library data
            self.library_data = data

            # Show success with data summary
            if isinstance(data, dict) and data:
                albums_count = len(data.get("albums", {}))
                artists_count = len(data.get("artists", {}))
                tracks_count = len(data.get("tracks", {}))
                playlists_count = len(data.get("playlists", {}))

                self.notify(f"Library loaded! {albums_count} albums, {artists_count} artists, {tracks_count} tracks, {playlists_count} playlists", severity="information")

                # Clear any previous error and show library interface
                self.load_error = None
                self.show_library = True

                # Update UI - views will be created lazily on first access
                self.call_later(self.recompose)
            else:
                self.notify("Connected! No data structure available yet.", severity="information")

        except Exception as e:
            self.notify(f"Failed to load library: {e}", severity="error")

    def _load_library(self) -> None:
        """Legacy synchronous method for backward compatibility."""
        # This will be replaced by the async version
        pass

    def switch_view(self, view: str) -> None:
        """Switch to a different view."""
        self.current_view = view
        # Trigger recompose to show the new DataTable view
        self.call_later(self.recompose)

    def _get_total_items_for_current_view(self) -> int:
        """Get total number of items for current view."""
        if not self.library_data:
            return 0

        if self.current_view == "albums":
            return len(self.library_data.get("albums", {}))
        elif self.current_view == "artists":
            return len(self.library_data.get("artists", {}))
        elif self.current_view == "tracks":
            return len(self.library_data.get("tracks", {}))
        elif self.current_view == "playlists":
            return len(self.library_data.get("playlists", {}))
        return 0



    def _show_library_ui(self) -> None:
        """Manually update the UI to show the library interface."""
        try:
            # Set flags and recompose to show the library interface
            self.show_library = True
            # Use call_later to ensure recompose happens after current compose is done
            self.call_later(self.recompose)
            self.notify("Library interface loaded!", severity="information")

        except Exception as e:
            self.notify(f"UI update failed: {e}", severity="error")

    def _init_audio(self) -> None:
        """Initialize audio playback system."""
        if not AUDIO_AVAILABLE:
            self.notify("Audio playback not available - pygame not installed", severity="warning")
            return

        if not self.audio_initialized:
            try:
                if pygame:
                    pygame.init()
                    pygame.mixer.init()
                    self.audio_initialized = True
            except Exception as e:
                self.notify(f"Failed to initialize audio: {e}", severity="error")

    def play_track(self, track_id: str, track_info: dict = None) -> None:
        """Play a track by ID."""
        if not AUDIO_AVAILABLE:
            self.notify("Audio playback not available", severity="warning")
            return

        self._init_audio()

        try:
            # Get stream URL
            stream_result = self.api_client.get_stream_url(track_id)
            if stream_result["status"] != "success":
                self.notify(f"Failed to get stream: {stream_result['message']}", severity="error")
                return

            stream_url = stream_result["stream_url"]

            # Stop current playback
            if self.playback_state != "stopped" and pygame:
                pygame.mixer.music.stop()

            # Load and play new track
            if pygame:
                pygame.mixer.music.load(stream_url)
                pygame.mixer.music.play()

            self.current_track = track_info or {"id": track_id}
            self.playback_state = "playing"

            track_name = track_info.get("title", "Unknown") if track_info else f"Track {track_id}"
            self.notify(f"Playing: {track_name}", severity="information")

            # Update player status
            self._update_player_status()

        except Exception as e:
            self.notify(f"Failed to play track: {e}", severity="error")

    def pause_track(self) -> None:
        """Pause current track."""
        if not AUDIO_AVAILABLE or not self.audio_initialized:
            return

        if pygame:
            if self.playback_state == "playing":
                pygame.mixer.music.pause()
                self.playback_state = "paused"
                self.notify("Paused", severity="information")
            elif self.playback_state == "paused":
                pygame.mixer.music.unpause()
                self.playback_state = "playing"
                self.notify("Resumed", severity="information")

        self._update_player_status()

    def stop_track(self) -> None:
        """Stop current track."""
        if not AUDIO_AVAILABLE or not self.audio_initialized or not pygame:
            return

        pygame.mixer.music.stop()
        self.playback_state = "stopped"
        self.current_track = None
        self.notify("Stopped", severity="information")
        self._update_player_status()

    def _update_player_status(self) -> None:
        """Update the player status display."""
        try:
            status_widget = self.query_one("#player-status", Static)
            if self.current_track and self.playback_state != "stopped":
                track_name = self.current_track.get("title", "Unknown Track")
                status_text = f"⏯️  {track_name}"
                if self.playback_state == "paused":
                    status_text = f"⏸️  {track_name}"
            else:
                status_text = "⏯️  [Not Playing]"

            status_widget.update(status_text)
        except Exception:
            pass  # Widget might not exist yet

    def play_album(self, album_id: str) -> None:
        """Play the first track from an album."""
        if not self.library_data or "albums" not in self.library_data:
            self.notify("No album data available", severity="error")
            return

        albums = self.library_data["albums"]
        if album_id not in albums:
            self.notify("Album not found", severity="error")
            return

        album_data = albums[album_id]
        if not isinstance(album_data, dict):
            self.notify("Invalid album data", severity="error")
            return

        album_name = album_data.get("title", "Unknown Album")

        # For now, we'll just show a message since we don't have track_ids in the dict format
        # In a full implementation, we'd need to query tracks by album_id
        self.notify(f"Album playback not fully implemented yet. Album: {album_name}", severity="warning")

        # TODO: Implement proper album track lookup and playback
        # track_info = {
        #     "title": f"{album_name} - Track 1",
        #     "album": album_name,
        #     "track_id": first_track_id
        # }
        # self.play_track(first_track_id, track_info)

    def _get_albums_text(self) -> str:
        """Get formatted albums text."""
        if not self.library_data or 'albums' not in self.library_data:
            return "No albums data available"

        albums = self.library_data['albums']
        lines = []
        sorted_albums = sorted(albums.items(), key=lambda x: str(x[1][0]).lower() if isinstance(x[1], list) and len(x[1]) > 0 else "")

        for album_id, album_data in sorted_albums:
            if isinstance(album_data, list) and len(album_data) >= 3:
                album_name = album_data[0]
                track_ids = album_data[1] if len(album_data) > 1 else []
                artist_id = album_data[2]
                year = album_data[3] if len(album_data) > 3 else "Unknown"

                artist_name = "Unknown Artist"
                if "artists" in self.library_data:
                    artist_data = self.library_data["artists"].get(str(artist_id))
                    if artist_data and isinstance(artist_data, list) and len(artist_data) > 0:
                        artist_name = artist_data[0]

                tracks_count = len(track_ids) if isinstance(track_ids, list) else 0
                lines.append(f"  {album_name} - {artist_name} ({year}) • {tracks_count} tracks")

        if len(sorted_albums) > 10:
            lines.append(f"  ... and {len(sorted_albums) - 10} more albums")

        return "\n".join(lines)

    def _get_artists_text(self) -> str:
        """Get formatted artists text."""
        if not self.library_data or 'artists' not in self.library_data:
            return "No artists data available"

        artists = self.library_data['artists']
        lines = []
        sorted_artists = sorted(artists.items(), key=lambda x: str(x[1][0]).lower() if isinstance(x[1], list) and len(x[1]) > 0 else "")

        for artist_id, artist_data in sorted_artists:
            if isinstance(artist_data, list) and len(artist_data) >= 2:
                artist_name = artist_data[0]
                track_ids = artist_data[1] if len(artist_data) > 1 else []
                tracks_count = len(track_ids) if isinstance(track_ids, list) else 0
                lines.append(f"  {artist_name} • {tracks_count} tracks")

        if len(sorted_artists) > 10:
            lines.append(f"  ... and {len(sorted_artists) - 10} more artists")

        return "\n".join(lines)

    def _get_playlists_text(self) -> str:
        """Get formatted playlists text."""
        if not self.library_data or 'playlists' not in self.library_data:
            return "No playlists data available"

        playlists = self.library_data['playlists']
        lines = []
        sorted_playlists = sorted(playlists.items(), key=lambda x: str(x[1][0]).lower() if isinstance(x[1], list) and len(x[1]) > 0 else "")

        for playlist_id, playlist_data in sorted_playlists:
            if isinstance(playlist_data, list) and len(playlist_data) >= 2:
                playlist_name = playlist_data[0]
                track_ids = playlist_data[1] if len(playlist_data) > 1 else []
                tracks_count = len(track_ids) if isinstance(track_ids, list) else 0
                lines.append(f"  {playlist_name} • {tracks_count} tracks")

        if len(sorted_playlists) > 10:
            lines.append(f"  ... and {len(sorted_playlists) - 10} more playlists")

        return "\n".join(lines)

    def _get_tracks_text(self) -> str:
        """Get formatted tracks text."""
        if not self.library_data or 'tracks' not in self.library_data:
            return "No tracks data available"

        tracks = self.library_data['tracks']
        lines = []
        sorted_tracks = sorted(tracks.items(), key=lambda x: str(x[1][2]).lower() if isinstance(x[1], list) and len(x[1]) >= 3 else "")

        for track_id, track_data in sorted_tracks:
            if isinstance(track_data, list) and len(track_data) >= 7:
                track_title = track_data[2]
                artist_id = track_data[6]
                album_id = track_data[5]

                artist_name = "Unknown Artist"
                if "artists" in self.library_data:
                    artist_data = self.library_data["artists"].get(str(artist_id))
                    if artist_data and isinstance(artist_data, list) and len(artist_data) > 0:
                        artist_name = artist_data[0]

                album_name = "Unknown Album"
                if "albums" in self.library_data:
                    album_data = self.library_data["albums"].get(str(album_id))
                    if album_data and isinstance(album_data, list) and len(album_data) > 0:
                        album_name = album_data[0]

                lines.append(f"  {track_title} - {artist_name} ({album_name})")

        if len(sorted_tracks) > 15:
            lines.append(f"  ... and {len(sorted_tracks) - 15} more tracks")

        return "\n".join(lines)



    def _create_datatable_view(self) -> ComposeResult:
        """Create DataTable view for current category."""
        if not self.library_data:
            yield Static("No library data available", classes="message")
            return

        # Create DataTable with appropriate columns
        table = DataTable(id="library-table")

        # Add columns based on current view
        if self.current_view == "albums":
            table.add_columns("Title", "Artist", "Year", "Tracks")
        elif self.current_view == "artists":
            table.add_columns("Name", "Tracks")
        elif self.current_view == "playlists":
            table.add_columns("Name", "Tracks", "Description")
        elif self.current_view == "tracks":
            table.add_columns("Title", "Artist", "Album", "Duration")
        else:
            yield Static("View not implemented", classes="message")
            return

        # Prepare and add data rows
        rows_data = self._prepare_view_data()
        if rows_data:
            table.add_rows(rows_data)

        yield table

    def _prepare_view_data(self) -> list:
        """Prepare data rows for the current view."""
        if not self.library_data:
            return []

        if self.current_view == "albums":
            return self._prepare_albums_data()
        elif self.current_view == "artists":
            return self._prepare_artists_data()
        elif self.current_view == "playlists":
            return self._prepare_playlists_data()
        elif self.current_view == "tracks":
            return self._prepare_tracks_data()
        return []

    def _prepare_albums_data(self) -> list:
        """Prepare album data for DataTable."""
        if "albums" not in self.library_data:
            return []

        rows = []
        albums = self.library_data["albums"]

        # Sort by title - handle both dict and list formats
        def get_album_title(item):
            album_id, album_data = item
            if isinstance(album_data, dict):
                return str(album_data.get("title", "")).lower()
            elif isinstance(album_data, list) and len(album_data) > 0:
                return str(album_data[0]).lower()  # title is at index 0
            return ""

        sorted_albums = sorted(albums.items(), key=get_album_title)

        for album_id, album in sorted_albums:
            if isinstance(album, dict):
                # Dict format from cache
                title = album.get("title", "Unknown Album")
                artist_name = self._get_artist_name(album.get("artist_id"))
                year = str(album.get("year", "Unknown"))
                tracks = str(album.get("track_count", 0))
            elif isinstance(album, list) and len(album) >= 7:
                # List format from API
                title = album[0] if album[0] else "Unknown Album"
                artist_id = album[2] if len(album) > 2 else None
                artist_name = self._get_artist_name(artist_id)
                year = str(album[6]) if len(album) > 6 and album[6] else "Unknown"
                track_ids = album[1] if len(album) > 1 and isinstance(album[1], list) else []
                tracks = str(len(track_ids))
            else:
                continue

            rows.append([title, artist_name, year, tracks])

        return rows

    def _prepare_artists_data(self) -> list:
        """Prepare artist data for DataTable."""
        if "artists" not in self.library_data:
            return []

        rows = []
        artists = self.library_data["artists"]

        # Sort by name - handle both dict and list formats
        def get_artist_name(item):
            artist_id, artist_data = item
            if isinstance(artist_data, dict):
                return str(artist_data.get("name", "")).lower()
            elif isinstance(artist_data, list) and len(artist_data) > 0:
                return str(artist_data[0]).lower()  # name is at index 0
            return ""

        sorted_artists = sorted(artists.items(), key=get_artist_name)

        for artist_id, artist in sorted_artists:
            if isinstance(artist, dict):
                # Dict format from cache
                name = artist.get("name", "Unknown Artist")
                tracks_count = artist.get("track_count", 0)
            elif isinstance(artist, list) and len(artist) >= 2:
                # List format from API
                name = artist[0] if artist[0] else "Unknown Artist"
                tracks_count = self._count_artist_tracks(artist_id)  # Fallback to counting
            else:
                continue

            rows.append([name, str(tracks_count)])

        return rows

    def _prepare_playlists_data(self) -> list:
        """Prepare playlist data for DataTable."""
        if "playlists" not in self.library_data:
            return []

        rows = []
        playlists = self.library_data["playlists"]

        # Sort by name - handle both dict and list formats
        def get_playlist_name(item):
            playlist_id, playlist_data = item
            if isinstance(playlist_data, dict):
                return str(playlist_data.get("name", "")).lower()
            elif isinstance(playlist_data, list) and len(playlist_data) > 0:
                return str(playlist_data[0]).lower()  # name is at index 0
            return ""

        sorted_playlists = sorted(playlists.items(), key=get_playlist_name)

        for playlist_id, playlist in sorted_playlists:
            if isinstance(playlist, dict):
                # Dict format from cache
                name = playlist.get("name", "Unknown Playlist")
                tracks = str(playlist.get("track_count", 0))
                description = playlist.get("description", "")
            elif isinstance(playlist, list) and len(playlist) >= 2:
                # List format from API
                name = playlist[0] if playlist[0] else "Unknown Playlist"
                track_ids = playlist[1] if len(playlist) > 1 and isinstance(playlist[1], list) else []
                tracks = str(len(track_ids))
                description = ""  # No description in list format
            else:
                continue

            rows.append([name, tracks, description])

        return rows

    def _prepare_tracks_data(self) -> list:
        """Prepare track data for DataTable."""
        if "tracks" not in self.library_data:
            return []

        rows = []
        tracks = self.library_data["tracks"]

        # Sort by title - handle both dict and list formats
        def get_track_title(item):
            track_id, track_data = item
            if isinstance(track_data, dict):
                return str(track_data.get("title", "")).lower()
            elif isinstance(track_data, list) and len(track_data) > 2:
                return str(track_data[2]).lower()  # title is at index 2
            return ""

        sorted_tracks = sorted(tracks.items(), key=get_track_title)

        for track_id, track in sorted_tracks:
            if isinstance(track, dict):
                # Dict format from cache
                title = track.get("title", "Unknown Track")
                artist_name = self._get_artist_name(track.get("artist_id"))
                album_name = self._get_album_name(track.get("album_id"))
                duration = self._format_duration(track.get("duration", 0))
            elif isinstance(track, list) and len(track) >= 7:
                # List format from API
                title = track[2] if len(track) > 2 and track[2] else "Unknown Track"
                artist_id = track[6] if len(track) > 6 else None
                album_id = track[5] if len(track) > 5 else None
                artist_name = self._get_artist_name(artist_id)
                album_name = self._get_album_name(album_id)
                duration = self._format_duration(track[4] if len(track) > 4 else 0)
            else:
                continue

            rows.append([title, artist_name, album_name, duration])

        return rows

    def _get_artist_name(self, artist_id) -> str:
        """Get artist name from ID."""
        if not artist_id or "artists" not in self.library_data:
            return "Unknown Artist"

        artist = self.library_data["artists"].get(str(artist_id))
        if artist and isinstance(artist, dict):
            return artist.get("name", "Unknown Artist")
        elif artist and isinstance(artist, list) and len(artist) > 0:
            return artist[0] if artist[0] else "Unknown Artist"
        return "Unknown Artist"

    def _get_album_name(self, album_id) -> str:
        """Get album name from ID."""
        if not album_id or "albums" not in self.library_data:
            return "Unknown Album"

        album = self.library_data["albums"].get(str(album_id))
        if album and isinstance(album, dict):
            return album.get("title", "Unknown Album")
        elif album and isinstance(album, list) and len(album) > 0:
            return album[0] if album[0] else "Unknown Album"
        return "Unknown Album"



    def _count_artist_tracks(self, artist_id) -> int:
        """Count tracks by artist (fallback for list format)."""
        if "tracks" not in self.library_data:
            return 0

        return sum(1 for track in self.library_data["tracks"].values()
                  if isinstance(track, (dict, list)) and
                  str(self._get_track_artist_id(track)) == str(artist_id))

    def _get_track_artist_id(self, track) -> str:
        """Get artist ID from track data (handles both dict and list formats)."""
        if isinstance(track, dict):
            return track.get("artist_id", "")
        elif isinstance(track, list) and len(track) > 5:
            return str(track[6])  # artist_id is at index 6 in track list
        return ""

    def _format_duration(self, duration_seconds) -> str:
        """Format duration in seconds to MM:SS."""
        if not duration_seconds:
            return "0:00"

        minutes = int(duration_seconds) // 60
        seconds = int(duration_seconds) % 60
        return f"{minutes}:{seconds:02d}"

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id

        if button_id == "connect-btn":
            await self.connect_to_service()
        elif button_id == "nav-albums":
            self.notify("Switching to Albums view", severity="information")
            self.switch_view("albums")
        elif button_id == "nav-artists":
            self.notify("Switching to Artists view", severity="information")
            self.switch_view("artists")
        elif button_id == "nav-playlists":
            self.notify("Switching to Playlists view", severity="information")
            self.switch_view("playlists")
        elif button_id == "nav-tracks":
            self.notify("Switching to Tracks view", severity="information")
            self.switch_view("tracks")
        elif button_id == "nav-search":
            self.notify("Search not implemented yet", severity="warning")
        # Note: Pagination buttons removed - DataTable handles scrolling internally
        elif button_id.startswith("album-"):
            album_id = button_id[6:]  # Remove "album-" prefix
            self.play_album(album_id)
        elif button_id.startswith("artist-"):
            artist_id = button_id[7:]  # Remove "artist-" prefix
            self.notify(f"Artist playback not implemented yet (ID: {artist_id})", severity="warning")
        elif button_id.startswith("playlist-"):
            playlist_id = button_id[9:]  # Remove "playlist-" prefix
            self.notify(f"Playlist playback not implemented yet (ID: {playlist_id})", severity="warning")
        elif button_id.startswith("track-"):
            track_id = button_id[6:]  # Remove "track-" prefix
            self.play_track(track_id)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle DataTable row selection for playback."""
        row_index = event.cursor_row

        # Get the data for this row
        if self.current_view == "albums":
            self._handle_album_selection(row_index)
        elif self.current_view == "artists":
            self._handle_artist_selection(row_index)
        elif self.current_view == "playlists":
            self._handle_playlist_selection(row_index)
        elif self.current_view == "tracks":
            self._handle_track_selection(row_index)

    def _handle_album_selection(self, row_index: int) -> None:
        """Handle album selection from DataTable."""
        if not self.library_data or "albums" not in self.library_data:
            return

        albums = self.library_data["albums"]
        sorted_albums = sorted(albums.items(),
                              key=lambda x: str(x[1].get("title", "")).lower())

        if row_index < len(sorted_albums):
            album_id, album_data = sorted_albums[row_index]
            self.play_album(album_id)

    def _handle_artist_selection(self, row_index: int) -> None:
        """Handle artist selection from DataTable."""
        if not self.library_data or "artists" not in self.library_data:
            return

        artists = self.library_data["artists"]
        sorted_artists = sorted(artists.items(),
                               key=lambda x: str(x[1].get("name", "")).lower())

        if row_index < len(sorted_artists):
            artist_id, artist_data = sorted_artists[row_index]
            self.notify(f"Artist playback not implemented yet (ID: {artist_id})", severity="warning")

    def _handle_playlist_selection(self, row_index: int) -> None:
        """Handle playlist selection from DataTable."""
        if not self.library_data or "playlists" not in self.library_data:
            return

        playlists = self.library_data["playlists"]
        sorted_playlists = sorted(playlists.items(),
                                 key=lambda x: str(x[1].get("name", "")).lower())

        if row_index < len(sorted_playlists):
            playlist_id, playlist_data = sorted_playlists[row_index]
            self.notify(f"Playlist playback not implemented yet (ID: {playlist_id})", severity="warning")

    def _handle_track_selection(self, row_index: int) -> None:
        """Handle track selection from DataTable."""
        if not self.library_data or "tracks" not in self.library_data:
            return

        tracks = self.library_data["tracks"]
        sorted_tracks = sorted(tracks.items(),
                              key=lambda x: str(x[1].get("title", "")).lower())

        if row_index < len(sorted_tracks):
            track_id, track_data = sorted_tracks[row_index]
            self.play_track(track_id)

    async def connect_to_service(self) -> None:
        """Connect to iBroadcast service."""
        if not settings.validate():
            self.notify("Please configure username and password in .env file", severity="error")
            return

        try:
            # Show authenticating message
            self.notify("Authenticating with iBroadcast...", severity="information")

            # Authenticate (this is already async in the API client)
            result = self.api_client.authenticate()
            if result["status"] == "success":
                self.notify(f"Connected to iBroadcast! {result['message']}", severity="information")
                # Load library asynchronously
                await self._load_library_async()
            else:
                self.notify(f"Authentication failed: {result['message']}", severity="error")
        except Exception as e:
            self.notify(f"Connection failed: {e}", severity="error")