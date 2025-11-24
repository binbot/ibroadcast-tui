"""Tests for API client."""

from unittest.mock import Mock, patch

from ibroadcast_tui.api.client import iBroadcastClient

class TestiBroadcastClient:
    """Test cases for the API client."""
    
    @patch('ibroadcast_tui.api.client.httpx.Client')
    def test_client_initialization(self, mock_client: Mock) -> None:
        """Test that the client initializes correctly."""
        client = iBroadcastClient()
        assert client.base_url == "https://api.ibroadcast.com"
        mock_client.assert_called_once()
    
    def test_authenticate_placeholder(self) -> None:
        """Test authentication placeholder."""
        client = iBroadcastClient()
        result = client.authenticate()
        assert result["status"] == "error"
        assert "Missing client credentials" in result["message"]
    
    def test_get_library_placeholder(self) -> None:
        """Test library fetching placeholder."""
        client = iBroadcastClient()
        result = client.get_library()
        assert result["status"] == "error"
        assert "Not authenticated" in result["message"]
