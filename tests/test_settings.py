"""Tests for configuration settings."""

import os
from unittest.mock import patch

from ibroadcast_tui.config.settings import Settings

class TestSettings:
    """Test cases for settings configuration."""
    
    def test_default_settings(self) -> None:
        """Test default settings values."""
        test_settings = Settings()
        assert test_settings.api_url == "https://api.ibroadcast.com"
        assert test_settings.app_name == "iBroadcast TUI"
        assert test_settings.debug is False
    
    @patch.dict(os.environ, {
        'IBROADCAST_API_URL': 'https://test.api.com',
        'DEBUG': 'true'
    })
    def test_environment_override(self) -> None:
        """Test that environment variables override defaults."""
        test_settings = Settings()
        assert test_settings.api_url == 'https://test.api.com'
        assert test_settings.debug is True
    
    @patch.dict(os.environ, {}, clear=True)
    def test_validate_missing_credentials(self) -> None:
        """Test validation with missing credentials."""
        test_settings = Settings()
        # Manually set to None to simulate missing environment variables
        test_settings.client_id = None
        test_settings.client_secret = None
        assert test_settings.validate() is False
    
    @patch.dict(os.environ, {
        'IBROADCAST_USERNAME': 'test@example.com',
        'IBROADCAST_PASSWORD': 'test_password'
    })
    def test_validate_with_credentials(self) -> None:
        """Test validation with all credentials present."""
        test_settings = Settings()
        assert test_settings.validate() is True
