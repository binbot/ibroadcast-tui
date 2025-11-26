"""API client for iBroadcast service."""

import httpx
from typing import Optional, Dict, Any

from ..config.settings import settings
from ..config.token_manager import token_manager

class iBroadcastClient:
    """HTTP client for interacting with iBroadcast API."""
    
    def __init__(self) -> None:
        """Initialize the API client."""
        self.base_url: str = settings.api_url
        self.library_url: str = settings.library_url
        self.username: Optional[str] = settings.username
        self.password: Optional[str] = settings.password
        self.user_id: Optional[str] = None
        self.token: Optional[str] = None

        # Build headers dynamically
        headers = {
            "User-Agent": f"{settings.app_name} {settings.app_version}",
        }

        self.client = httpx.Client(base_url=self.base_url, headers=headers)

        # Try to load stored session
        self._load_stored_session()
    
    def _load_stored_token(self) -> None:
        """Load and validate stored token."""
        token_data = token_manager.load_token()
        if token_data and token_manager.is_token_valid(token_data):
            self.access_token = token_data.get("access_token")
            self._update_auth_headers()
    
    def _update_auth_headers(self) -> None:
        """Update HTTP client headers with authorization."""
        if self.access_token:
            self.client.headers["Authorization"] = f"Bearer {self.access_token}"
        else:
            self.client.headers.pop("Authorization", None)
    
    def _load_stored_session(self) -> None:
        """Load and validate stored session."""
        # For now, we'll implement session storage later
        # This would load user_id and token from a session file
        pass

    def _login(self) -> Dict[str, Any]:
        """Login to iBroadcast with username and password."""
        if not self.username or not self.password:
            return {"status": "error", "message": "Missing username or password"}

        try:
            # iBroadcast login request (based on existing client)
            login_data = {
                "mode": "status",
                "email_address": self.username,
                "password": self.password,
                "version": settings.app_version,
                "client": settings.app_name.lower().replace(" ", "-"),
                "supported_types": 1,
            }

            response = self.client.post("/s/JSON/status", json=login_data)
            response.raise_for_status()

            status_data = response.json()

            if "user" not in status_data:
                return {"status": "error", "message": "Invalid login credentials"}

            # Store session data
            self.user_id = str(status_data["user"]["id"])
            self.token = status_data["user"]["token"]

            # Store session for future use
            self._save_session()

            return {"status": "success", "message": "Login successful"}

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                return {"status": "error", "message": "Invalid username or password"}
            else:
                return {"status": "error", "message": f"Login failed: HTTP {e.response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": f"Login failed: {e}"}

    def _save_session(self) -> None:
        """Save session data for future use."""
        # For now, we'll implement session persistence later
        # This would save user_id and token to a session file
        pass

    def authenticate(self) -> Dict[str, Any]:
        """Authenticate with iBroadcast API using username/password."""
        # Check if we have a valid stored session
        if self.user_id and self.token:
            return {"status": "success", "message": "Using stored session"}

        # Login with username/password
        return self._login()
    
    def get_library(self) -> Dict[str, Any]:
        """Get user's music library."""
        # Ensure we have a valid token
        if not token_manager.is_token_valid():
            auth_result = self.authenticate()
            if auth_result["status"] != "success":
                return {"status": "error", "message": "Authentication required"}
        
        try:
            # iBroadcast library request (based on existing client)
            library_data = {
                "_token": self.token,
                "_userid": self.user_id,
                "client": settings.app_name.lower().replace(" ", "-"),
                "version": settings.app_version,
                "mode": "library",
                "supported_types": False,
            }

            response = httpx.post(f"{self.library_url}/s/JSON/library", json=library_data, timeout=30.0)
            response.raise_for_status()

            library_response = response.json()

            if "library" in library_response:
                return {"status": "success", "data": library_response["library"]}
            else:
                return {"status": "error", "message": "Invalid library response format"}
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                # Token might be expired, try to refresh
                token_manager.delete_token()
                auth_result = self.authenticate()
                if auth_result["status"] == "success":
                    return self.get_library()  # Retry with new token
            
            return {"status": "error", "message": f"Failed to fetch library: {e.response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to fetch library: {e}"}
    
    def get_stream_url(self, track_id: str) -> Dict[str, Any]:
        """Get streaming URL for a track."""
        # Ensure we have a valid token
        if not token_manager.is_token_valid():
            auth_result = self.authenticate()
            if auth_result["status"] != "success":
                return {"status": "error", "message": "Authentication required"}

        try:
            # iBroadcast stream request
            stream_data = {
                "_token": self.token,
                "_userid": self.user_id,
                "client": settings.app_name.lower().replace(" ", "-"),
                "version": settings.app_version,
                "track_id": track_id,
            }

            response = httpx.post(f"{self.library_url}/s/JSON/stream", json=stream_data, timeout=10.0)
            response.raise_for_status()

            stream_response = response.json()

            if "stream_url" in stream_response:
                return {
                    "status": "success",
                    "stream_url": stream_response["stream_url"],
                    "track_info": stream_response.get("track", {})
                }
            else:
                return {"status": "error", "message": "Invalid stream response format"}

        except httpx.HTTPStatusError as e:
            return {"status": "error", "message": f"Failed to get stream URL: {e.response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to get stream URL: {e}"}

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()
