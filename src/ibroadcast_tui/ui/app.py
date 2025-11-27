"""Main UI application for iBroadcast TUI."""

import asyncio
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Static, Button, DataTable

from ..api.client import iBroadcastClient
from ..config.settings import settings
from ..data_manager import DataManager

from ..player.audio_player import AudioPlayer

class iBroadcastTUI(App):
    """Main TUI application for iBroadcast."""
    
    CSS = """
    /* iBroadcast TUI - Clean Terminal Interface */

    Screen {
        background: transparent;
        color: $text;
    }

    /* Layout */
    Horizontal {
        height: 100%;
    }

    .sidebar {
        width: 25;
        background: transparent;
        padding: 1;
        border-right: vkey $accent;
    }

    .main-content {
        width: 1fr;
        background: transparent;
        padding: 0 1;
        border: round $accent;
        margin: 0 1;
    }

    .player-section {
        width: 30;
        background: transparent;
        padding: 1;
        border: round $accent;
    }

    /* Sidebar */
    .sidebar-title {
        color: $accent;
        text-style: bold;
        text-align: center;
        margin-bottom: 1;
    }

    .sidebar-separator {
        color: $panel-lighten-2;
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
        color: $accent;
    }

    .nav-item:focus {
        background: transparent;
        text-style: bold underline;
        color: $accent;
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
        color: $accent;
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
        color: $accent;
        text-align: center;
        text-style: bold;
        border: wide $accent;
    }

    .connect-btn:hover {
        background: $accent 20%;
        color: $text;
        text-style: bold;
    }

    /* Player section */
    .player-label {
        color: $accent;
        text-style: bold;
        margin-bottom: 0;
    }

    .player-status {
        color: $text;
        text-style: bold;
        margin-bottom: 1;
    }

    .progress-bar {
        color: $text-muted;
        text-align: center;
        margin-bottom: 0;
    }

    .time-display {
        color: $text;
        text-align: center;
        margin-bottom: 1;
    }

    .player-controls {
        /* Controls container */
        align: center middle;
    }

    .player-btn {
        width: 3;
        text-align: center;
        color: $accent;
    }
    
    .player-btn:hover {
        color: $text;
        background: $accent;
    }

    /* Footer */
    Footer {
        background: transparent;
        color: $text-muted;
        height: 1;
        text-align: center;
    }

    /* Scrollable content */
    ScrollableContainer {
        scrollbar-background: transparent;
        scrollbar-color: $accent;
        scrollbar-color-active: $accent-lighten-1;
    }

    /* Buttons */
    Button {
        border: none;
        background: transparent;
        color: $text;
    }

    Button:hover {
        background: transparent;
        color: $accent;
        text-style: bold;
    }

    Button:focus {
        background: transparent;
        color: $accent;
        text-style: bold underline;
    }

    /* View headers */
    .view-header {
        color: $text;
        text-style: bold;
        text-align: center;
        margin-bottom: 1;
        border-bottom: solid $accent;
    }

    /* DataTable styling */
    DataTable {
        height: 1fr;
        border: none;
        background: transparent;
    }

    DataTable > .datatable--header {
        background: transparent;
        color: $accent;
        text-style: bold;
        border-bottom: solid $accent;
    }

    DataTable > .datatable--cursor {
        background: $accent;
        color: $text;
    }

    DataTable > .datatable--hover {
        background: $accent 20%;
        color: $accent;
        text-style: bold;
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
        self.player = AudioPlayer(on_track_end=self.on_track_end)
        self.playback_timer = None



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

        """Called when the app is mounted."""
        # Start playback timer
        self.set_interval(1.0, self.update_player_ui)

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
                self.call_later(self._populate_datatable)
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
        self.call_later(self._populate_datatable)

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

    def on_track_end(self) -> None:
        """Called when a track finishes playing."""
        # TODO: Implement queue handling here
        self.call_later(self.notify, "Track finished", severity="information")
        self.call_later(self._update_player_status)

    def play_track(self, track_id: str, track_info: dict = None) -> None:
        """Play a track by ID."""
        if not self.player.is_available:
            self.notify("Audio playback not available (mpv not found)", severity="warning")
            return

        try:
            # Get stream URL
            stream_result = self.api_client.get_stream_url(track_id)
            if stream_result["status"] != "success":
                self.notify(f"Failed to get stream: {stream_result['message']}", severity="error")
                return

            stream_url = stream_result["stream_url"]
            
            # Update track info if not provided
            if not track_info:
                track_info = {"id": track_id, "title": f"Track {track_id}"}

            # Play
            if self.player.play(stream_url, track_info):
                track_name = track_info.get("title", "Unknown")
                self.notify(f"Playing: {track_name}", severity="information")
                self._update_player_status()
            else:
                self.notify("Failed to start playback", severity="error")

        except Exception as e:
            self.notify(f"Failed to play track: {e}", severity="error")

    def pause_track(self) -> None:
        """Pause/Resume current track."""
        self.player.pause()
        self._update_player_status()

    def stop_track(self) -> None:
        """Stop current track."""
        self.player.stop()
        self._update_player_status()

    def update_player_ui(self) -> None:
        """Update player UI (progress, time)."""
        if not self.player.is_available:
            return
            
        status = self.player.get_status()
        
        # Update progress bar and time
        try:
            position = status["position"]
            duration = status["duration"]
            
            # Format time
            pos_str = self._format_duration(position)
            dur_str = self._format_duration(duration)
            
            time_display = self.query_one("#time-display", Static)
            time_display.update(f"{pos_str} / {dur_str}")
            
            # Update progress bar (simple visual)
            if duration > 0:
                percent = min(1.0, position / duration)
                width = 15  # Width of progress bar in chars
                filled = int(width * percent)
                bar = "─" * filled + "●" + "─" * (width - filled - 1)
                
                progress_bar = self.query_one("#progress-bar", Static)
                progress_bar.update(bar)
                
        except Exception:
            pass

    def _update_player_status(self) -> None:
        """Update the player status display."""
        try:
            status = self.player.get_status()
            state = status["state"]
            track = status["track"]
            
            status_widget = self.query_one("#player-status", Static)
            
            if state != "stopped" and track:
                track_name = track.get("title", "Unknown Track")
                icon = "⏯️" if state == "playing" else "⏸️"
                status_text = f"{icon}  {track_name}"
            else:
                status_text = "⏹️  [Not Playing]"

            status_widget.update(status_text)
        except Exception:
            pass

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
        # Data will be loaded asynchronously via _populate_datatable
        
        yield table

    async def _populate_datatable(self) -> None:
        """Populate DataTable asynchronously with chunked loading."""
        try:
            table = self.query_one("#library-table", DataTable)
        except Exception:
            # Table might not exist yet or anymore
            return

        if not self.library_data:
            return

        # Show loading state
        table.loading = True
        table.clear()

        # Get rows asynchronously
        rows = []
        try:
            if self.current_view == "albums":
                rows = await self.data_manager.get_albums_rows_async(self.library_data)
            elif self.current_view == "artists":
                rows = await self.data_manager.get_artists_rows_async(self.library_data)
            elif self.current_view == "playlists":
                rows = await self.data_manager.get_playlists_rows_async(self.library_data)
            elif self.current_view == "tracks":
                rows = await self.data_manager.get_tracks_rows_async(self.library_data)
        except Exception as e:
            self.notify(f"Failed to load data: {e}", severity="error")
            table.loading = False
            return

        table.loading = False

        # Add rows in chunks to prevent UI freezing
        chunk_size = 50
        for i in range(0, len(rows), chunk_size):
            chunk = rows[i:i+chunk_size]
            table.add_rows(chunk)
            # Yield to event loop to keep UI responsive
            await asyncio.sleep(0.001)


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

    def _format_duration(self, duration_seconds) -> str:
        """Format duration in seconds to MM:SS."""
        if not duration_seconds:
            return "0:00"
        try:
            minutes = int(duration_seconds) // 60
            seconds = int(duration_seconds) % 60
            return f"{minutes}:{seconds:02d}"
        except (ValueError, TypeError):
            return "0:00"