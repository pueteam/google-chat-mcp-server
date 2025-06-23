"""Base class for Google Chat MCP tools."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from mcp.types import Tool

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """Base class for all Google Chat MCP tools."""
    
    def __init__(self, auth, default_space: str = None):
        """Initialize the tool with authentication."""
        self.auth = auth
        self.default_space = default_space
    
    @abstractmethod
    def get_tools(self) -> List[Tool]:
        """Return list of tools provided by this module."""
        pass
    
    @abstractmethod
    def get_tool_names(self) -> List[str]:
        """Return list of tool names."""
        pass
    
    @abstractmethod
    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool with given arguments."""
        pass
    
    async def _ensure_authenticated(self):
        """Ensure authentication is valid."""
        await self.auth.ensure_authenticated()
    
    def _get_service(self):
        """Get authenticated Google Chat service."""
        return self.auth.get_service()
    
    def _validate_space(self, space: str = None) -> str:
        """Validate and return space name."""
        if space:
            return space
        if self.default_space:
            return self.default_space
        raise ValueError("No space specified and no default space configured")
    
    def _handle_api_error(self, e: Exception, operation: str) -> Dict[str, Any]:
        """Handle Google API errors consistently."""
        logger.error(f"Error during {operation}: {e}")
        
        if hasattr(e, 'resp') and hasattr(e.resp, 'status'):
            status = e.resp.status
            if status == 403:
                return {
                    "error": "Permission denied. Check your authentication and API permissions.",
                    "status": status
                }
            elif status == 404:
                return {
                    "error": "Resource not found. Check the space/message ID.",
                    "status": status
                }
            elif status == 429:
                return {
                    "error": "Rate limit exceeded. Please try again later.",
                    "status": status
                }
        
        return {
            "error": f"API error during {operation}: {str(e)}",
            "type": type(e).__name__
        }