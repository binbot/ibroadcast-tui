"""Data manager for efficient library loading and caching."""

import asyncio
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor

from .database import SessionLocal, Artist, Album, Track, Playlist, PlaylistTrack
from sqlalchemy import func
from .api.client import iBroadcastClient

class DataManager:
    """Manages library data with caching and efficient loading."""

    def __init__(self):
        self.api_client = iBroadcastClient()
        self.executor = ThreadPoolExecutor(max_workers=4)

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
        with SessionLocal() as db:
            return db.query(Artist).count() > 0

    def _load_cached_library(self) -> Dict[str, Any]:
        """Load library data from cache."""
        with SessionLocal() as db:
            # Create mappings from database IDs to iBroadcast IDs
            artist_ib_map = {artist.id: artist.ibroadcast_id for artist in db.query(Artist).all()}
            album_ib_map = {album.id: album.ibroadcast_id for album in db.query(Album).all()}

            # Load artists with track counts
            artists = {}
            # Pre-compute track counts for all artists
            from sqlalchemy import func
            track_counts = db.query(Track.artist_id, func.count(Track.id)).group_by(Track.artist_id).all()
            track_count_map = {artist_id: count for artist_id, count in track_counts}

            for artist in db.query(Artist).all():
                artists[artist.ibroadcast_id] = {
                    "id": artist.ibroadcast_id,
                    "name": artist.name,
                    "track_count": track_count_map.get(artist.id, 0)
                }

            # Load albums
            albums = {}
            for album in db.query(Album).all():
                albums[album.ibroadcast_id] = {
                    "id": album.ibroadcast_id,
                    "title": album.title,
                    "artist_id": artist_ib_map.get(album.artist_id),  # Convert to iBroadcast ID
                    "year": album.year,
                    "track_count": album.track_count
                }

            # Load tracks
            tracks = {}
            for track in db.query(Track).all():
                tracks[track.ibroadcast_id] = {
                    "id": track.ibroadcast_id,
                    "title": track.title,
                    "artist_id": artist_ib_map.get(track.artist_id),  # Convert to iBroadcast ID
                    "album_id": album_ib_map.get(track.album_id),    # Convert to iBroadcast ID
                    "duration": track.duration,
                    "track_number": track.track_number,
                    "year": track.year
                }

            # Load playlists
            playlists = {}
            for playlist in db.query(Playlist).all():
                playlists[playlist.ibroadcast_id] = {
                    "id": playlist.ibroadcast_id,
                    "name": playlist.name,
                    "description": playlist.description,
                    "track_count": playlist.track_count
                }

            return {
                "artists": artists,
                "albums": albums,
                "tracks": tracks,
                "playlists": playlists
            }

    def _cache_library_data(self, data: Dict[str, Any]) -> None:
        """Cache library data to database."""
        with SessionLocal() as db:
            try:
                # Clear existing data
                db.query(PlaylistTrack).delete()
                db.query(Playlist).delete()
                db.query(Track).delete()
                db.query(Album).delete()
                db.query(Artist).delete()

                # Cache artists
                artists_map = {}
                for artist_id, artist_data in data.get("artists", {}).items():
                    if isinstance(artist_data, list) and len(artist_data) >= 1:
                        artist = Artist(
                            ibroadcast_id=artist_id,
                            name=artist_data[0]  # Artist name is at index 0
                        )
                        db.add(artist)
                        artists_map[artist_id] = artist

                db.flush()  # Get IDs

                # Cache albums
                albums_map = {}
                for album_id, album_data in data.get("albums", {}).items():
                    if isinstance(album_data, list) and len(album_data) >= 4:
                        artist_id = str(album_data[2])  # Artist ID at index 2
                        if artist_id in artists_map:
                            album = Album(
                                ibroadcast_id=album_id,
                                title=album_data[0],  # Title at index 0
                                artist_id=artists_map[artist_id].id,
                                year=album_data[6] if len(album_data) > 6 else None,  # Year at index 6
                                track_count=len(album_data[1]) if len(album_data) > 1 else 0  # Track count from track_ids array
                            )
                            db.add(album)
                            albums_map[album_id] = album

                db.flush()



                # Cache tracks
                for track_id, track_data in data.get("tracks", {}).items():
                    if isinstance(track_data, list) and len(track_data) >= 7:
                        artist_id = str(track_data[6])  # Artist ID at index 6
                        album_id = str(track_data[5])   # Album ID at index 5

                        # Use track's artist if it exists, otherwise use album's artist
                        if artist_id in artists_map:
                            final_artist_db_id = artists_map[artist_id].id
                        elif album_id in albums_map:
                            # Use the album's artist as fallback
                            final_artist_db_id = albums_map[album_id].artist_id
                        else:
                            continue  # Skip tracks with no valid artist

                        if album_id in albums_map:
                            track = Track(
                                ibroadcast_id=track_id,
                                title=track_data[2],  # Title at index 2
                                artist_id=final_artist_db_id,
                                album_id=albums_map[album_id].id,
                                duration=None,  # Not available in current API
                                track_number=track_data[0] if len(track_data) > 0 else None,  # Track number at index 0
                                year=track_data[1] if len(track_data) > 1 else None  # Year at index 1
                            )
                            db.add(track)

                # Cache playlists
                for playlist_id, playlist_data in data.get("playlists", {}).items():
                    if isinstance(playlist_data, list) and len(playlist_data) >= 2:
                        playlist = Playlist(
                            ibroadcast_id=playlist_id,
                            name=playlist_data[0],  # Name at index 0
                            track_count=len(playlist_data[1]) if len(playlist_data) > 1 else 0  # Track count from track_ids array
                        )
                        db.add(playlist)

                db.commit()

            except Exception as e:
                db.rollback()
                raise e

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
        with SessionLocal() as db:
            # Search tracks by title
            tracks = db.query(Track).join(Artist).join(Album).filter(
                Track.title.ilike(f"%{query}%")
            ).limit(limit).all()

            results = []
            for track in tracks:
                results.append({
                    "id": track.ibroadcast_id,
                    "title": track.title,
                    "artist": track.artist.name,
                    "album": track.album.title,
                    "year": track.year
                })

            return results

    def close(self):
        """Close the data manager."""
        self.executor.shutdown(wait=True)