"""Tests for main application."""

from unittest.mock import Mock, patch

from ibroadcast_tui.main import iBroadcastApp

class TestiBroadcastApp:
    """Test cases for the main application."""
    
    def test_app_creation(self) -> None:
        """Test that the app can be created."""
        app = iBroadcastApp()
        assert app.title == "iBroadcast TUI"
    
    @patch('ibroadcast_tui.main.iBroadcastApp.run')
    def test_main_execution(self, mock_run: Mock) -> None:
        """Test that the main execution works."""
        app = iBroadcastApp()
        app.run()
        mock_run.assert_called_once()
