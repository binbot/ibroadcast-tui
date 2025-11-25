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
    
    def test_authenticate_missing_credentials(self) -> None:
        """Test authentication with missing credentials."""
        # Create client with missing credentials
        client = iBroadcastClient()
        client.username = None
        client.password = None
        result = client._login()
        assert result["status"] == "error"
        assert "Missing username or password" in result["message"]
    
    @patch('ibroadcast_tui.api.client.httpx')
    def test_login_success(self, mock_httpx: Mock) -> None:
        """Test successful login."""
        # Mock successful login response
        mock_response = Mock()
        mock_response.json.return_value = {
            "user": {
                "id": "12345",
                "token": "test_token"
            }
        }
        mock_response.raise_for_status.return_value = None

        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_response
        mock_httpx.Client.return_value = mock_client_instance

        client = iBroadcastClient()
        client.username = "test@example.com"
        client.password = "test_password"

        result = client._login()

        assert result["status"] == "success"
        assert client.user_id == "12345"
        assert client.token == "test_token"
