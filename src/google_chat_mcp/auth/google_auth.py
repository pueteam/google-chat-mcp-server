"""Google authentication for Chat API."""

import logging
import os
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as AuthRequest
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# Google Chat API scopes
SCOPES = [
    'https://www.googleapis.com/auth/chat.messages',
    'https://www.googleapis.com/auth/chat.spaces',
    'https://www.googleapis.com/auth/chat.memberships',
    'https://www.googleapis.com/auth/chat.spaces.readonly',
    'https://www.googleapis.com/auth/chat.messages.readonly',
    'https://www.googleapis.com/auth/chat.memberships.readonly',
]


class GoogleChatAuth:
    """Handles Google Chat API authentication."""
    
    def __init__(
        self,
        service_account_path: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ):
        """Initialize authentication.
        
        Args:
            service_account_path: Path to service account JSON file
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            refresh_token: OAuth2 refresh token
        """
        self.service_account_path = service_account_path
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        
        self.credentials = None
        self.service = None
    
    async def initialize(self):
        """Initialize authentication and create API service."""
        try:
            # Try service account first
            if self.service_account_path and os.path.exists(self.service_account_path):
                logger.info("Using service account authentication")
                self.credentials = service_account.Credentials.from_service_account_file(
                    self.service_account_path,
                    scopes=SCOPES
                )
            # Try OAuth2
            elif self.client_id and self.client_secret and self.refresh_token:
                logger.info("Using OAuth2 authentication")
                self.credentials = Credentials(
                    token=None,
                    refresh_token=self.refresh_token,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    scopes=SCOPES
                )
                # Refresh the token
                auth_request = AuthRequest()
                self.credentials.refresh(auth_request)
            else:
                raise ValueError(
                    "No valid authentication method found. "
                    "Please provide either service account JSON or OAuth2 credentials."
                )
            
            # Create the Chat API service
            self.service = build('chat', 'v1', credentials=self.credentials)
            logger.info("Google Chat API service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Chat authentication: {e}")
            raise
    
    def get_service(self):
        """Get the authenticated Google Chat API service."""
        if not self.service:
            raise RuntimeError("Authentication not initialized. Call initialize() first.")
        return self.service
    
    async def ensure_authenticated(self):
        """Ensure credentials are valid and refresh if needed."""
        if not self.credentials:
            await self.initialize()
            return
        
        # Check if credentials need refresh
        if self.credentials.expired and self.credentials.refresh_token:
            try:
                auth_request = AuthRequest()
                self.credentials.refresh(auth_request)
                logger.debug("Credentials refreshed successfully")
            except Exception as e:
                logger.error(f"Failed to refresh credentials: {e}")
                # Try to re-initialize
                await self.initialize()
    
    async def test_connection(self) -> bool:
        """Test the connection to Google Chat API."""
        try:
            await self.ensure_authenticated()
            service = self.get_service()
            
            # Try to list spaces to test connection
            result = service.spaces().list(pageSize=1).execute()
            logger.info("Google Chat API connection test successful")
            return True
            
        except HttpError as e:
            logger.error(f"Google Chat API connection test failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during connection test: {e}")
            return False