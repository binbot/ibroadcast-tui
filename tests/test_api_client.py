"""Tests for API client."""

from unittest.mock import Mock, patch
import pytest
from ibroadcast_tui.api.client import iBroadcastClient

class TestiBroadcastClient:
    """Test cases for the API client."""
    
    @patch('ibroadcast_tui.api.client.httpx.Client')
    def test_client_initialization(self, mock_client: Mock) -> None:
        """Test that the client initializes correctly."""
        client = iBroadcastClient()
        assert client.base_url == "https://api.ibroadcast.com"
        mock_client.assert_called_once()
    
    @patch('ibroadcast_tui.api.client.httpx.Client')
    @patch('ibroadcast_tui.api.client.token_manager')
    def test_authenticate_success(self, mock_token_manager: Mock, mock_client_cls: Mock) -> None:
        """Test successful authentication."""
        # Mock token manager
        mock_token_manager.load_token.return_value = None
        mock_token_manager.is_token_valid.return_value = False
        
        # Mock client instance
        mock_client = Mock()
        mock_client_cls.return_value = mock_client
        
        # Mock login response
        mock_response = Mock()
        mock_response.json.return_value = {
            "user": {
                "id": "12345",
                "token": "test_token"
            },
            "settings": {
                "streaming_server": "https://streaming.test.com"
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_client.post.return_value = mock_response
        
        client = iBroadcastClient()
        client.username = "testuser"
        client.password = "testpass"
        
        result = client.authenticate()
        
        assert result["status"] == "success"
        assert client.user_id == "12345"
        assert client.token == "test_token"
        assert client.streaming_server == "https://streaming.test.com"
        
    @patch('ibroadcast_tui.api.client.httpx.Client')
    @patch('ibroadcast_tui.api.client.token_manager')
    def test_authenticate_failure(self, mock_token_manager: Mock, mock_client_cls: Mock) -> None:
        """Test authentication failure."""
        # Mock token manager
        mock_token_manager.load_token.return_value = None
        mock_token_manager.is_token_valid.return_value = False
        
        # Mock client instance
        mock_client = Mock()
        mock_client_cls.return_value = mock_client
        
        # Mock login response
        mock_response = Mock()
        mock_response.json.return_value = {
            "result": False,
            "message": "Invalid login"
        }
        mock_response.raise_for_status.return_value = None
        mock_client.post.return_value = mock_response
        
        client = iBroadcastClient()
        client.username = "testuser"
        client.password = "wrongpass"
        
        result = client.authenticate()
        
        assert result["status"] == "error"
        
    @patch('ibroadcast_tui.api.client.httpx.Client')
    def test_get_stream_url_manual(self, mock_client_cls: Mock) -> None:
        """Test manual stream URL construction."""
        client = iBroadcastClient()
        client.user_id = "12345"
        client.token = "test_token"
        client.streaming_server = "https://streaming.test.com"
        
        track_id = "999"
        track_path = "/path/to/track.mp3"
        
        result = client.get_stream_url(track_id, track_path)
        
        assert result["status"] == "success"
        assert "stream_url" in result
        assert "https://streaming.test.com/path/to/track.mp3" in result["stream_url"]
        assert "Signature=test_token" in result["stream_url"]
        assert "Expires=" in result["stream_url"]

