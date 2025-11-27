"""Tests for DataManager."""

import pytest
import asyncio
from ibroadcast_tui.data_manager import DataManager

@pytest.fixture
def sample_library_data():
    return {
        "albums": {
            "1": {"title": "Album A", "artist_id": "10", "year": 2020, "track_count": 5},
            "2": ["Album B", [101, 102], 11, 0, 0, 0, 2021],
        },
        "artists": {
            "10": {"name": "Artist X", "track_count": 5},
            "11": ["Artist Y", [101, 102]],
        },
        "playlists": {
            "20": {"name": "Playlist 1", "track_count": 10, "description": "Desc"},
        },
        "tracks": {
            "100": {"title": "Track 1", "artist_id": "10", "album_id": "1", "duration": 180},
            "101": [0, 0, "Track 2", 0, 200, "2", "11"],
        }
    }

@pytest.mark.asyncio
async def test_get_albums_rows_async(sample_library_data):
    dm = DataManager()
    rows = await dm.get_albums_rows_async(sample_library_data)
    
    assert len(rows) == 2
    # Sorted by title
    assert rows[0][0] == "Album A"
    assert rows[1][0] == "Album B"
    
    # Check artist resolution
    assert rows[0][1] == "Artist X"
    assert rows[1][1] == "Artist Y"
    
    dm.close()

@pytest.mark.asyncio
async def test_get_artists_rows_async(sample_library_data):
    dm = DataManager()
    rows = await dm.get_artists_rows_async(sample_library_data)
    
    assert len(rows) == 2
    assert rows[0][0] == "Artist X"
    assert rows[1][0] == "Artist Y"
    
    dm.close()

@pytest.mark.asyncio
async def test_get_tracks_rows_async(sample_library_data):
    dm = DataManager()
    rows = await dm.get_tracks_rows_async(sample_library_data)
    
    assert len(rows) == 2
    assert rows[0][0] == "Track 1"
    assert rows[1][0] == "Track 2"
    
    # Check duration formatting (index 4)
    assert rows[0][4] == "3:00"
    assert rows[1][4] == "3:20"
    
    dm.close()
