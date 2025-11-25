"""Configuration settings for iBroadcast TUI."""

import os
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application settings and configuration."""
    
    def __init__(self) -> None:
        """Initialize settings from environment variables."""
        self.api_url: str = os.getenv("IBROADCAST_API_URL", "https://api.ibroadcast.com")
        self.library_url: str = os.getenv("IBROADCAST_LIBRARY_URL", "https://library.ibroadcast.com")
        self.username: Optional[str] = os.getenv("IBROADCAST_USERNAME")
        self.password: Optional[str] = os.getenv("IBROADCAST_PASSWORD")

        # App settings
        self.app_name: str = "iBroadcast TUI"
        self.app_version: str = "0.1.0"
        self.debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    def validate(self) -> bool:
        """Validate that required settings are present and not placeholder values."""
        placeholder_values = ["your_username_here", "your_password_here", "", None]
        return (
            self.username not in placeholder_values
            and self.password not in placeholder_values
        )

# Global settings instance
settings = Settings()
