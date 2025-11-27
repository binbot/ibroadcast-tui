"""Simple JSON-based data manager for library caching."""

import asyncio
import json
import os
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .api.client import iBroadcastClient

class DataManager:
    """Manages library data with simple JSON caching."""

    def __init__(self):
        self.api_client = iBroadcastClient()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.cache_dir = Path.home() / ".ibroadcast_tui"
        self.cache_file = self.cache_dir / "library_cache.json"

    async def load_library_async(self) -> Dict[str, Any]:
        """Load library data asynchronously with caching."""
        # Check if we have cached data
        if self._has_cached_data():
            # Load from cache in background
            loop = asyncio.get_event_loop()
            cached_data = await loop.run_in_executor(self.executor, self._load_cached_library)
            return cached_data

        # No cache, load from API
        return await self._load_from_api_async()

    async def _load_from_api_async(self) -> Dict[str, Any]:
        """Load data from API asynchronously."""
        loop = asyncio.get_event_loop()

        # Load from API in thread pool
        api_data = await loop.run_in_executor(self.executor, self._load_from_api_sync)

        # Cache the data
        await loop.run_in_executor(self.executor, self._cache_library_data, api_data)

        return api_data

    def _load_from_api_sync(self) -> Dict[str, Any]:
        """Load data from API synchronously."""
        result = self.api_client.get_library()
        if result["status"] == "success":
            return result["data"]
        raise Exception(f"Failed to load library: {result.get('message', 'Unknown error')}")

    def _has_cached_data(self) -> bool:
        """Check if we have cached data."""
        return self.cache_file.exists() and self.cache_file.stat().st_size > 0

    def _load_cached_library(self) -> Dict[str, Any]:
        """Load library data from JSON cache."""
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _cache_library_data(self, data: Dict[str, Any]) -> None:
        """Cache library data to JSON file with pre-computed track counts."""
        try:
            # Ensure cache directory exists
            self.cache_dir.mkdir(exist_ok=True)

            # Pre-compute track counts for artists
            processed_data = self._preprocess_data(data)

            # Write to cache file
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            # Don't fail if caching fails, just log
            print(f"Warning: Failed to cache data: {e}")

    def _preprocess_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Preprocess data to add track counts and normalize formats."""
        processed = dict(data)  # Copy the data

        # Pre-compute track counts for artists
        if "tracks" in data and "artists" in data:
            track_counts = self._compute_track_counts(data["tracks"])
            processed["artists"] = self._add_track_counts_to_artists(data["artists"], track_counts)

        return processed

    def _compute_track_counts(self, tracks: Dict[str, Any]) -> Dict[str, int]:
        """Compute track counts for each artist."""
        track_counts = {}

        for track_data in tracks.values():
            artist_id = None
            if isinstance(track_data, list) and len(track_data) >= 7:
                artist_id = str(track_data[6])  # Artist ID at index 6
            elif isinstance(track_data, dict):
                artist_id = track_data.get("artist_id")

            if artist_id:
                track_counts[artist_id] = track_counts.get(artist_id, 0) + 1

        return track_counts

    def _add_track_counts_to_artists(self, artists: Dict[str, Any], track_counts: Dict[str, int]) -> Dict[str, Any]:
        """Add track counts to artist data."""
        processed_artists = {}

        for artist_id, artist_data in artists.items():
            if isinstance(artist_data, list):
                # List format: [name, ...]
                processed_artists[artist_id] = {
                    "id": artist_id,
                    "name": artist_data[0] if artist_data else "Unknown Artist",
                    "track_count": track_counts.get(artist_id, 0)
                }
            elif isinstance(artist_data, dict):
                # Dict format: already has structure
                processed_artists[artist_id] = dict(artist_data)
                processed_artists[artist_id]["track_count"] = track_counts.get(artist_id, 0)
            else:
                # Fallback
                processed_artists[artist_id] = {
                    "id": artist_id,
                    "name": "Unknown Artist",
                    "track_count": track_counts.get(artist_id, 0)
                }

        return processed_artists

    async def search_tracks(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search tracks by title, artist, or album."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._search_tracks_sync,
            query,
            limit
        )

    def _search_tracks_sync(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search tracks synchronously."""
        if not self._has_cached_data():
            return []

        try:
            data = self._load_cached_library()
            tracks = data.get("tracks", {})
            artists = data.get("artists", {})
            albums = data.get("albums", {})

            results = []
            query_lower = query.lower()

            for track_id, track_data in tracks.items():
                if len(results) >= limit:
                    break

                # Extract track info
                if isinstance(track_data, list) and len(track_data) >= 3:
                    title = str(track_data[2])  # Title at index 2
                    artist_id = str(track_data[6]) if len(track_data) > 6 else None
                    album_id = str(track_data[5]) if len(track_data) > 5 else None
                elif isinstance(track_data, dict):
                    title = track_data.get("title", "")
                    artist_id = track_data.get("artist_id")
                    album_id = track_data.get("album_id")
                else:
                    continue

                # Check if query matches
                if query_lower in title.lower():
                    # Get artist and album names
                    artist_name = "Unknown Artist"
                    if artist_id and artist_id in artists:
                        artist_data = artists[artist_id]
                        if isinstance(artist_data, dict):
                            artist_name = artist_data.get("name", "Unknown Artist")
                        elif isinstance(artist_data, list) and artist_data:
                            artist_name = artist_data[0]

                    album_name = "Unknown Album"
                    if album_id and album_id in albums:
                        album_data = albums[album_id]
                        if isinstance(album_data, dict):
                            album_name = album_data.get("title", "Unknown Album")
                        elif isinstance(album_data, list) and album_data:
                            album_name = album_data[0]

                    results.append({
                        "id": track_id,
                        "title": title,
                        "artist": artist_name,
                        "album": album_name,
                        "year": None  # Not easily available in current format
                    })

            return results

        except Exception as e:
            print(f"Search error: {e}")
            return []

    def clear_cache(self) -> None:
        """Clear the cache file."""
        if self.cache_file.exists():
            self.cache_file.unlink()

    def close(self):
        """Close the data manager."""
        self.executor.shutdown(wait=True)

    async def get_albums_rows_async(self, library_data: Dict[str, Any]) -> List[List[str]]:
        """Get album rows for DataTable asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._prepare_albums_data_sync,
            library_data
        )

    async def get_artists_rows_async(self, library_data: Dict[str, Any]) -> List[List[str]]:
        """Get artist rows for DataTable asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._prepare_artists_data_sync,
            library_data
        )

    async def get_playlists_rows_async(self, library_data: Dict[str, Any]) -> List[List[str]]:
        """Get playlist rows for DataTable asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._prepare_playlists_data_sync,
            library_data
        )

    async def get_tracks_rows_async(self, library_data: Dict[str, Any]) -> List[List[str]]:
        """Get track rows for DataTable asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._prepare_tracks_data_sync,
            library_data
        )

    def _prepare_albums_data_sync(self, library_data: Dict[str, Any]) -> List[List[str]]:
        """Prepare album data for DataTable."""
        if "albums" not in library_data:
            return []

        rows = []
        albums = library_data["albums"]

        # Sort by title
        def get_album_title(item):
            album_id, album_data = item
            if isinstance(album_data, dict):
                return str(album_data.get("title", "")).lower()
            elif isinstance(album_data, list) and len(album_data) > 0:
                return str(album_data[0]).lower()
            return ""

        sorted_albums = sorted(albums.items(), key=get_album_title)

        for album_id, album in sorted_albums:
            if isinstance(album, dict):
                title = album.get("title", "Unknown Album")
                artist_name = self._get_artist_name(library_data, album.get("artist_id"))
                year = str(album.get("year", "Unknown"))
                tracks = str(album.get("track_count", 0))
            elif isinstance(album, list) and len(album) >= 7:
                title = album[0] if album[0] else "Unknown Album"
                artist_id = album[2] if len(album) > 2 else None
                artist_name = self._get_artist_name(library_data, artist_id)
                year = str(album[6]) if len(album) > 6 and album[6] else "Unknown"
                track_ids = album[1] if len(album) > 1 and isinstance(album[1], list) else []
                tracks = str(len(track_ids))
            else:
                continue

            rows.append([title, artist_name, year, tracks])

        return rows

    def _prepare_artists_data_sync(self, library_data: Dict[str, Any]) -> List[List[str]]:
        """Prepare artist data for DataTable."""
        if "artists" not in library_data:
            return []

        rows = []
        artists = library_data["artists"]

        def get_artist_name(item):
            artist_id, artist_data = item
            if isinstance(artist_data, dict):
                return str(artist_data.get("name", "")).lower()
            elif isinstance(artist_data, list) and len(artist_data) > 0:
                return str(artist_data[0]).lower()
            return ""

        sorted_artists = sorted(artists.items(), key=get_artist_name)

        for artist_id, artist in sorted_artists:
            if isinstance(artist, dict):
                name = artist.get("name", "Unknown Artist")
                tracks_count = artist.get("track_count", 0)
            elif isinstance(artist, list) and len(artist) >= 2:
                name = artist[0] if artist[0] else "Unknown Artist"
                tracks_count = self._count_artist_tracks(library_data, artist_id)
            else:
                continue

            rows.append([name, str(tracks_count)])

        return rows

    def _prepare_playlists_data_sync(self, library_data: Dict[str, Any]) -> List[List[str]]:
        """Prepare playlist data for DataTable."""
        if "playlists" not in library_data:
            return []

        rows = []
        playlists = library_data["playlists"]

        def get_playlist_name(item):
            playlist_id, playlist_data = item
            if isinstance(playlist_data, dict):
                return str(playlist_data.get("name", "")).lower()
            elif isinstance(playlist_data, list) and len(playlist_data) > 0:
                return str(playlist_data[0]).lower()
            return ""

        sorted_playlists = sorted(playlists.items(), key=get_playlist_name)

        for playlist_id, playlist in sorted_playlists:
            if isinstance(playlist, dict):
                name = playlist.get("name", "Unknown Playlist")
                tracks = str(playlist.get("track_count", 0))
                description = playlist.get("description", "")
            elif isinstance(playlist, list) and len(playlist) >= 2:
                name = playlist[0] if playlist[0] else "Unknown Playlist"
                track_ids = playlist[1] if len(playlist) > 1 and isinstance(playlist[1], list) else []
                tracks = str(len(track_ids))
                description = ""
            else:
                continue

            rows.append([name, tracks, description])

        return rows

    def _prepare_tracks_data_sync(self, library_data: Dict[str, Any]) -> List[List[str]]:
        """Prepare track data for DataTable."""
        if "tracks" not in library_data:
            return []

        rows = []
        tracks = library_data["tracks"]

        def get_track_title(item):
            track_id, track_data = item
            if isinstance(track_data, dict):
                return str(track_data.get("title", "")).lower()
            elif isinstance(track_data, list) and len(track_data) > 2:
                return str(track_data[2]).lower()
            return ""

        sorted_tracks = sorted(tracks.items(), key=get_track_title)

        for track_id, track in sorted_tracks:
            if isinstance(track, dict):
                title = track.get("title", "Unknown Track")
                artist_name = self._get_artist_name(library_data, track.get("artist_id"))
                album_name = self._get_album_name(library_data, track.get("album_id"))
                duration = self._format_duration(track.get("duration", 0))
            elif isinstance(track, list) and len(track) >= 7:
                title = track[2] if len(track) > 2 and track[2] else "Unknown Track"
                artist_id = track[6] if len(track) > 6 else None
                album_id = track[5] if len(track) > 5 else None
                artist_name = self._get_artist_name(library_data, artist_id)
                album_name = self._get_album_name(library_data, album_id)
                duration = self._format_duration(track[4] if len(track) > 4 else 0)
            else:
                continue

            rows.append([title, artist_name, album_name, duration])

        return rows

    def _get_artist_name(self, library_data: Dict[str, Any], artist_id) -> str:
        """Get artist name from ID."""
        if not artist_id or "artists" not in library_data:
            return "Unknown Artist"

        artist = library_data["artists"].get(str(artist_id))
        if artist and isinstance(artist, dict):
            return artist.get("name", "Unknown Artist")
        elif artist and isinstance(artist, list) and len(artist) > 0:
            return artist[0] if artist[0] else "Unknown Artist"
        return "Unknown Artist"

    def _get_album_name(self, library_data: Dict[str, Any], album_id) -> str:
        """Get album name from ID."""
        if not album_id or "albums" not in library_data:
            return "Unknown Album"

        album = library_data["albums"].get(str(album_id))
        if album and isinstance(album, dict):
            return album.get("title", "Unknown Album")
        elif album and isinstance(album, list) and len(album) > 0:
            return album[0] if album[0] else "Unknown Album"
        return "Unknown Album"

    def _count_artist_tracks(self, library_data: Dict[str, Any], artist_id) -> int:
        """Count tracks by artist."""
        if "tracks" not in library_data:
            return 0

        return sum(1 for track in library_data["tracks"].values()
                  if isinstance(track, (dict, list)) and
                  str(self._get_track_artist_id(track)) == str(artist_id))

    def _get_track_artist_id(self, track) -> str:
        """Get artist ID from track data."""
        if isinstance(track, dict):
            return track.get("artist_id", "")
        elif isinstance(track, list) and len(track) > 5:
            return str(track[6])
        return ""

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