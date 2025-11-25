"""Token management for iBroadcast OAuth2 authentication."""

import json
import time
from pathlib import Path
from typing import Optional, Dict, Any

from .settings import settings

class TokenManager:
    """Manages OAuth2 token storage and validation."""
    
    def __init__(self) -> None:
        """Initialize token manager."""
        self.token_dir = Path.home() / ".ibroadcast-tui"
        self.token_file = self.token_dir / "token.json"
        self._ensure_token_dir()
    
    def _ensure_token_dir(self) -> None:
        """Ensure token directory exists with proper permissions."""
        try:
            self.token_dir.mkdir(mode=0o700, exist_ok=True)
        except OSError as e:
            raise RuntimeError(f"Failed to create token directory: {e}")
    
    def save_token(self, token_data: Dict[str, Any]) -> None:
        """Save token data to file with secure permissions."""
        try:
            # Add expiration timestamp if not present
            if "expires_in" in token_data and "expires_at" not in token_data:
                token_data["expires_at"] = time.time() + token_data["expires_in"]
            
            # Add username for validation
            token_data["username"] = settings.username
            
            # Write to temporary file first, then move to avoid partial writes
            temp_file = self.token_file.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(token_data, f, indent=2)
            
            # Move temp file to final location and set permissions
            temp_file.replace(self.token_file)
            self.token_file.chmod(0o600)
            
        except OSError as e:
            raise RuntimeError(f"Failed to save token: {e}")
    
    def load_token(self) -> Optional[Dict[str, Any]]:
        """Load token data from file."""
        if not self.token_file.exists():
            return None
        
        try:
            with open(self.token_file, "r", encoding="utf-8") as f:
                token_data = json.load(f)
            
            # Validate token belongs to current user
            if token_data.get("username") != settings.username:
                return None
            
            return token_data
            
        except (OSError, json.JSONDecodeError):
            return None
    
    def is_token_valid(self, token_data: Optional[Dict[str, Any]] = None) -> bool:
        """Check if token is valid and not expired."""
        if token_data is None:
            token_data = self.load_token()
        
        if not token_data:
            return False
        
        # Check if token has expiration
        expires_at = token_data.get("expires_at")
        if expires_at is None:
            return True  # No expiration means valid
        
        # Add 5-minute buffer before expiration
        return time.time() < (expires_at - 300)
    
    def delete_token(self) -> None:
        """Delete stored token file."""
        try:
            if self.token_file.exists():
                self.token_file.unlink()
        except OSError:
            pass  # Ignore deletion errors

# Global token manager instance
token_manager = TokenManager()