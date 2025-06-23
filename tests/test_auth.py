"""Tests for Google Chat authentication."""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from google_chat_mcp.auth import GoogleChatAuth


class TestGoogleChatAuth:
    """Test cases for GoogleChatAuth class."""
    
    def test_init_with_service_account(self):
        """Test initialization with service account."""
        auth = GoogleChatAuth(service_account_path="/path/to/service-account.json")
        assert auth.service_account_path == "/path/to/service-account.json"
        assert auth.client_id is None
        assert auth.client_secret is None
        assert auth.refresh_token is None
    
    def test_init_with_oauth2(self):
        """Test initialization with OAuth2 credentials."""
        auth = GoogleChatAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            refresh_token="test_refresh_token"
        )
        assert auth.service_account_path is None
        assert auth.client_id == "test_client_id"
        assert auth.client_secret == "test_client_secret"
        assert auth.refresh_token == "test_refresh_token"
    
    @patch('google_chat_mcp.auth.google_auth.service_account.Credentials.from_service_account_file')
    @patch('google_chat_mcp.auth.google_auth.build')
    async def test_initialize_with_service_account(self, mock_build, mock_from_file):
        """Test initialization with valid service account file."""
        # Create temporary service account file
        service_account_data = {
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "test-key-id",
            "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n",
            "client_email": "test@test-project.iam.gserviceaccount.com",
            "client_id": "test-client-id",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(service_account_data, f)
            temp_file_path = f.name
        
        try:
            # Mock credentials and service
            mock_credentials = Mock()
            mock_from_file.return_value = mock_credentials
            mock_service = Mock()
            mock_build.return_value = mock_service
            
            # Test initialization
            auth = GoogleChatAuth(service_account_path=temp_file_path)
            await auth.initialize()
            
            # Verify calls
            mock_from_file.assert_called_once()
            mock_build.assert_called_once_with('chat', 'v1', credentials=mock_credentials)
            assert auth.service == mock_service
            
        finally:
            os.unlink(temp_file_path)
    
    @patch('google_chat_mcp.auth.google_auth.Credentials')
    @patch('google_chat_mcp.auth.google_auth.build')
    async def test_initialize_with_oauth2(self, mock_build, mock_credentials_class):
        """Test initialization with OAuth2 credentials."""
        # Mock credentials
        mock_credentials = Mock()
        mock_credentials_class.return_value = mock_credentials
        mock_service = Mock()
        mock_build.return_value = mock_service
        
        # Test initialization
        auth = GoogleChatAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            refresh_token="test_refresh_token"
        )
        await auth.initialize()
        
        # Verify calls
        mock_credentials_class.assert_called_once()
        mock_credentials.refresh.assert_called_once()
        mock_build.assert_called_once_with('chat', 'v1', credentials=mock_credentials)
        assert auth.service == mock_service
    
    async def test_initialize_no_credentials(self):
        """Test initialization without credentials raises error."""
        auth = GoogleChatAuth()
        
        with pytest.raises(ValueError, match="No valid authentication method found"):
            await auth.initialize()
    
    def test_get_service_not_initialized(self):
        """Test get_service before initialization raises error."""
        auth = GoogleChatAuth()
        
        with pytest.raises(RuntimeError, match="Authentication not initialized"):
            auth.get_service()
    
    @patch('google_chat_mcp.auth.google_auth.service_account.Credentials.from_service_account_file')
    @patch('google_chat_mcp.auth.google_auth.build')
    async def test_get_service_after_initialization(self, mock_build, mock_from_file):
        """Test get_service after successful initialization."""
        # Create temporary service account file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"type": "service_account"}, f)
            temp_file_path = f.name
        
        try:
            mock_service = Mock()
            mock_build.return_value = mock_service
            
            auth = GoogleChatAuth(service_account_path=temp_file_path)
            await auth.initialize()
            
            result = auth.get_service()
            assert result == mock_service
            
        finally:
            os.unlink(temp_file_path)
    
    @patch('google_chat_mcp.auth.google_auth.service_account.Credentials.from_service_account_file')
    @patch('google_chat_mcp.auth.google_auth.build')
    async def test_ensure_authenticated_not_expired(self, mock_build, mock_from_file):
        """Test ensure_authenticated with valid credentials."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"type": "service_account"}, f)
            temp_file_path = f.name
        
        try:
            mock_credentials = Mock()
            mock_credentials.expired = False
            mock_from_file.return_value = mock_credentials
            
            auth = GoogleChatAuth(service_account_path=temp_file_path)
            await auth.initialize()
            
            # Should not raise any exception
            await auth.ensure_authenticated()
            
        finally:
            os.unlink(temp_file_path)
    
    @patch('google_chat_mcp.auth.google_auth.service_account.Credentials.from_service_account_file')
    @patch('google_chat_mcp.auth.google_auth.build')
    async def test_test_connection_success(self, mock_build, mock_from_file):
        """Test successful connection test."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"type": "service_account"}, f)
            temp_file_path = f.name
        
        try:
            # Mock service and API call
            mock_service = Mock()
            mock_spaces = Mock()
            mock_list = Mock()
            mock_execute = Mock()
            mock_execute.return_value = {"spaces": []}
            
            mock_list.execute = mock_execute
            mock_spaces.list.return_value = mock_list
            mock_service.spaces.return_value = mock_spaces
            mock_build.return_value = mock_service
            
            auth = GoogleChatAuth(service_account_path=temp_file_path)
            await auth.initialize()
            
            result = await auth.test_connection()
            assert result is True
            
            mock_spaces.list.assert_called_once_with(pageSize=1)
            mock_execute.assert_called_once()
            
        finally:
            os.unlink(temp_file_path)
    
    @patch('google_chat_mcp.auth.google_auth.service_account.Credentials.from_service_account_file')
    @patch('google_chat_mcp.auth.google_auth.build')
    async def test_test_connection_failure(self, mock_build, mock_from_file):
        """Test connection test failure."""
        from googleapiclient.errors import HttpError
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"type": "service_account"}, f)
            temp_file_path = f.name
        
        try:
            # Mock service to raise HttpError
            mock_service = Mock()
            mock_spaces = Mock()
            mock_list = Mock()
            
            # Create a mock HttpError
            mock_resp = Mock()
            mock_resp.status = 403
            mock_error = HttpError(mock_resp, b'Forbidden')
            mock_list.execute.side_effect = mock_error
            
            mock_spaces.list.return_value = mock_list
            mock_service.spaces.return_value = mock_spaces
            mock_build.return_value = mock_service
            
            auth = GoogleChatAuth(service_account_path=temp_file_path)
            await auth.initialize()
            
            result = await auth.test_connection()
            assert result is False
            
        finally:
            os.unlink(temp_file_path)