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
    
    @patch('ibroadcast_tui.api.client.token_manager')
    def test_authenticate_missing_credentials(self, mock_token_manager: Mock) -> None:
        """Test authentication with missing credentials."""
        # Mock token manager to avoid file operations
        mock_token_manager.is_token_valid.return_value = False
        
        # Create client with missing credentials
        client = iBroadcastClient()
        client.client_id = None
        client.client_secret = None
        result = client._request_access_token()
        assert result["status"] == "error"
        assert "Missing client credentials" in result["message"]
    
    @patch('ibroadcast_tui.api.client.httpx.Client')
    @patch('ibroadcast_tui.api.client.token_manager')
    def test_token_request_success(self, mock_token_manager: Mock, mock_client: Mock) -> None:
        """Test successful token request."""
        # Mock successful token response
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "expires_in": 3600
        }
        mock_response.raise_for_status.return_value = None
        
        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value = mock_client_instance
        
        # Mock token manager to avoid file operations
        mock_token_manager.save_token.return_value = None
        mock_token_manager.is_token_valid.return_value = False
        
        # Mock headers to avoid assignment issues
        mock_client_instance.headers = {}
        
        client = iBroadcastClient()
        client.client_id = "test_client"
        client.client_secret = "test_secret"
        
        result = client._request_access_token()
        
        assert result["status"] == "success"
        assert client.access_token == "test_access_token"
    
    def test_token_request_missing_credentials(self) -> None:
        """Test token request with missing credentials."""
        client = iBroadcastClient()
        client.client_id = None
        client.client_secret = None
        
        result = client._request_access_token()
        
        assert result["status"] == "error"
        assert "Missing client credentials" in result["message"]
