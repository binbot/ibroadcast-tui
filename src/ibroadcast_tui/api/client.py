"""API client for iBroadcast service."""

import httpx
import time
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
        self.streaming_server: str = "https://streaming.ibroadcast.com"

        # Build headers dynamically
        headers = {
            "User-Agent": f"{settings.app_name} {settings.app_version}",
        }

        self.client = httpx.Client(base_url=self.base_url, headers=headers)

        # Try to load stored session
        self._load_stored_session()
    

    
    def _load_stored_session(self) -> None:
        """Load and validate stored session."""
        token_data = token_manager.load_token()
        if token_data and token_manager.is_token_valid(token_data):
            self.token = token_data.get("token")
            self.user_id = token_data.get("user_id")
            if "streaming_server" in token_data:
                self.streaming_server = token_data["streaming_server"]

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
            
            if "settings" in status_data and "streaming_server" in status_data["settings"]:
                self.streaming_server = status_data["settings"]["streaming_server"]

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
        if self.token and self.user_id:
            token_data = {
                "token": self.token,
                "user_id": self.user_id,
                "streaming_server": self.streaming_server,
                "expires_in": 86400 * 30  # 30 days
            }
            token_manager.save_token(token_data)

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
        
        # Reload session from token manager if we don't have it in memory
        if not self.token or not self.user_id:
             self._load_stored_session()
        
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
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Invalid library response: {library_response}")
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
    
    def get_stream_url(self, track_id: str, track_path: str = None) -> Dict[str, Any]:
        """Get streaming URL for a track."""
        # Ensure we have a valid token
        if not token_manager.is_token_valid():
            auth_result = self.authenticate()
            if auth_result["status"] != "success":
                return {"status": "error", "message": "Authentication required"}

        # Reload session from token manager if we don't have it in memory
        if not self.token or not self.user_id:
             self._load_stored_session()

        try:
            # If we have the track path, construct the URL manually
            if track_path:
                client_name = settings.app_name.lower().replace(" ", "-")
                expires = int(time.time() + 3600)  # 1 hour expiration
                stream_url = f"{self.streaming_server}{track_path}?user_id={self.user_id}&Signature={self.token}&Expires={expires}&client={client_name}&version={settings.app_version}&file_id={track_id}"
                return {
                    "status": "success",
                    "stream_url": stream_url,
                    "track_info": {"id": track_id}
                }

            # Fallback to API request (which seems to fail, but keeping for compatibility)
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
