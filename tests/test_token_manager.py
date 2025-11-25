"""Tests for token manager."""

import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

from ibroadcast_tui.config.token_manager import TokenManager

class TestTokenManager:
    """Test cases for token management."""
    
    def setup_method(self) -> None:
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.token_file = self.temp_dir / "token.json"
    
    def teardown_method(self) -> None:
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('ibroadcast_tui.config.token_manager.Path.home')
    def test_token_manager_initialization(self, mock_home: patch) -> None:
        """Test token manager creates directory correctly."""
        mock_home.return_value = self.temp_dir
        
        token_manager = TokenManager()
        
        assert token_manager.token_dir == self.temp_dir / ".ibroadcast-tui"
        assert token_manager.token_file == token_manager.token_dir / "token.json"
    
    @patch('ibroadcast_tui.config.token_manager.Path.home')
    @patch('ibroadcast_tui.config.token_manager.settings')
    def test_save_and_load_token(self, mock_settings: Mock, mock_home: patch) -> None:
        """Test saving and loading token."""
        mock_home.return_value = self.temp_dir
        mock_settings.username = "test@example.com"

        token_manager = TokenManager()
        token_data = {
            "access_token": "test_token",
            "expires_in": 3600,
            "username": "test@example.com"
        }

        # Save token
        token_manager.save_token(token_data)

        # Load token
        loaded_token = token_manager.load_token()

        assert loaded_token is not None
        assert loaded_token["access_token"] == "test_token"
        assert loaded_token["username"] == "test@example.com"
        assert "expires_at" in loaded_token
    
    @patch('ibroadcast_tui.config.token_manager.Path.home')
    def test_token_validation(self, mock_home: patch) -> None:
        """Test token validation."""
        mock_home.return_value = self.temp_dir
        
        token_manager = TokenManager()
        
        # Test no token
        assert token_manager.is_token_valid() is False
        
        # Test valid token
        token_data = {
            "access_token": "test_token",
            "expires_at": time.time() + 3600,  # Expires in 1 hour
            "username": "test@example.com"
        }
        token_manager.save_token(token_data)
        
        assert token_manager.is_token_valid() is True
        
        # Test expired token
        expired_token = {
            "access_token": "expired_token",
            "expires_at": time.time() - 3600,  # Expired 1 hour ago
            "client_id": "test_client"
        }
        token_manager.save_token(expired_token)
        
        assert token_manager.is_token_valid() is False
    
    @patch('ibroadcast_tui.config.token_manager.Path.home')
    def test_client_id_validation(self, mock_home: patch) -> None:
        """Test token validation with different client IDs."""
        mock_home.return_value = self.temp_dir
        
        token_manager = TokenManager()
        
        # Save token for user1
        token_data = {
            "access_token": "test_token",
            "expires_at": time.time() + 3600,
            "username": "user1@example.com"
        }
        token_manager.save_token(token_data)
        
        # Mock settings to have different username
        with patch('ibroadcast_tui.config.token_manager.settings.username', 'user2@example.com'):
            loaded_token = token_manager.load_token()
            assert loaded_token is None  # Should not load token for different client
    
    @patch('ibroadcast_tui.config.token_manager.Path.home')
    def test_delete_token(self, mock_home: patch) -> None:
        """Test token deletion."""
        mock_home.return_value = self.temp_dir
        
        token_manager = TokenManager()
        token_data = {"access_token": "test_token"}
        token_manager.save_token(token_data)
        
        # Verify token exists
        assert token_manager.load_token() is not None
        
        # Delete token
        token_manager.delete_token()
        
        # Verify token is gone
        assert token_manager.load_token() is None