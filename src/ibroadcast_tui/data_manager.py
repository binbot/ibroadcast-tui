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