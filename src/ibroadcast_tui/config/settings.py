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
        self.client_id: Optional[str] = os.getenv("IBROADCAST_CLIENT_ID")
        self.client_secret: Optional[str] = os.getenv("IBROADCAST_CLIENT_SECRET")
        
        # App settings
        self.app_name: str = "iBroadcast TUI"
        self.debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    def validate(self) -> bool:
        """Validate that required settings are present."""
        return bool(self.client_id and self.client_secret)

# Global settings instance
settings = Settings()
