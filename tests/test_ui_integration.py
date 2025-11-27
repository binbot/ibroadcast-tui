import pytest
from src.ibroadcast_tui.ui.app import iBroadcastTUI
from src.ibroadcast_tui.data_manager import DataManager

def test_app_instantiation():
    """Test that the app can be instantiated."""
    app = iBroadcastTUI()
    assert app.title == "iBroadcast TUI"
    assert isinstance(app.data_manager, DataManager)
    assert app.player is not None

def test_data_manager_metadata():
    """Test that data manager handles year metadata."""
    dm = DataManager()
    
    # Mock data with year
    mock_library = {
        "tracks": {
            "1": [
                "ignored", "ignored", "Title", "ignored", 120, "album_id", "artist_id", "2023"
            ]
        },
        "albums": {},
        "artists": {}
    }
    
    rows = dm._prepare_tracks_data_sync(mock_library)
    assert len(rows) == 1
    # Title, Artist, Album, Year, Duration
    assert rows[0][3] == "2023"
