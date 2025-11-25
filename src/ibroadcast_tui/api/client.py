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
        self.client_id: Optional[str] = settings.client_id
        self.client_secret: Optional[str] = settings.client_secret
        self.access_token: Optional[str] = None
        
        # Build headers dynamically
        headers = {
            "User-Agent": f"{settings.app_name} 0.1.0",
        }
        
        self.client = httpx.Client(base_url=self.base_url, headers=headers)
        
        # Try to load existing token
        self._load_stored_token()
    
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
    
    def _request_access_token(self) -> Dict[str, Any]:
        """Request new access token from OAuth2 endpoint."""
        if not self.client_id or not self.client_secret:
            return {"status": "error", "message": "Missing client credentials"}
        
        try:
            # OAuth2 client credentials grant
            data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
            }
            
            response = self.client.post("/oauth/token", data=data, headers=headers)
            response.raise_for_status()
            
            token_data = response.json()
            
            # Store token for future use
            token_manager.save_token(token_data)
            self.access_token = token_data.get("access_token")
            self._update_auth_headers()
            
            return {"status": "success", "message": "Authentication successful"}
            
        except httpx.HTTPStatusError as e:
            error_msg = "Authentication failed"
            if e.response.status_code == 401:
                error_msg = "Invalid client credentials"
            elif e.response.status_code == 429:
                error_msg = "Rate limit exceeded"
            
            return {"status": "error", "message": error_msg}
        except Exception as e:
            return {"status": "error", "message": f"Authentication failed: {e}"}
    
    def authenticate(self) -> Dict[str, Any]:
        """Authenticate with the iBroadcast API using OAuth2 client credentials."""
        # Check if we have a valid stored token
        if token_manager.is_token_valid():
            return {"status": "success", "message": "Using stored token"}
        
        # Request new token
        return self._request_access_token()
    
    def _discover_api_endpoints(self) -> Dict[str, Any]:
        """Discover available API endpoints by testing common patterns."""
        if not self.access_token:
            return {"status": "error", "message": "Authentication required"}
        
        discovered_endpoints = {}
        
        # Test common endpoint patterns
        common_endpoints = [
            "/library",
            "/v1/library", 
            "/api/library",
            "/tracks",
            "/v1/tracks",
            "/api/tracks",
            "/user/library",
            "/v1/user/library",
            "/albums",
            "/v1/albums",
            "/playlists",
            "/v1/playlists"
        ]
        
        for endpoint in common_endpoints:
            try:
                response = self.client.get(endpoint)
                if response.status_code != 404:
                    discovered_endpoints[endpoint] = {
                        "status_code": response.status_code,
                        "available": response.status_code == 200
                    }
            except Exception:
                discovered_endpoints[endpoint] = {"available": False}
        
        return {"status": "success", "endpoints": discovered_endpoints}
    
    def get_library(self) -> Dict[str, Any]:
        """Get user's music library."""
        # Ensure we have a valid token
        if not token_manager.is_token_valid():
            auth_result = self.authenticate()
            if auth_result["status"] != "success":
                return {"status": "error", "message": "Authentication required"}
        
        try:
            # First, try to discover available endpoints
            discovery = self._discover_api_endpoints()
            if discovery["status"] == "success":
                # Find working library endpoint
                for endpoint, info in discovery["endpoints"].items():
                    if info.get("available") and "library" in endpoint:
                        response = self.client.get(endpoint)
                        response.raise_for_status()
                        library_data = response.json()
                        return {"status": "success", "data": library_data, "endpoint": endpoint}
            
            # Fallback to common patterns if discovery fails
            fallback_endpoints = ["/v1/library", "/library", "/user/library"]
            for endpoint in fallback_endpoints:
                try:
                    response = self.client.get(endpoint)
                    if response.status_code == 200:
                        library_data = response.json()
                        return {"status": "success", "data": library_data, "endpoint": endpoint}
                except httpx.HTTPStatusError as e:
                    if e.response.status_code != 404:
                        continue  # Try next endpoint
                except Exception:
                    continue
            
            return {"status": "error", "message": "No working library endpoint found", "discovered": discovery}
            
        except Exception as e:
            return {"status": "error", "message": f"Failed to fetch library: {e}"}
    
    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()
