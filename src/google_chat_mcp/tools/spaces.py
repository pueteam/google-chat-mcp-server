"""Space management tools for Google Chat."""

import logging
from typing import Any, Dict, List, Optional

from mcp.types import Tool
from googleapiclient.errors import HttpError

from .base import BaseTool

logger = logging.getLogger(__name__)


class SpaceTools(BaseTool):
    """Tools for managing Google Chat spaces."""
    
    def get_tools(self) -> List[Tool]:
        """Return list of space-related tools."""
        return [
            Tool(
                name="list_spaces",
                description="List Google Chat spaces the bot has access to",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of spaces to return (default: 25, max: 100)",
                            "minimum": 1,
                            "maximum": 100,
                            "default": 25
                        },
                        "filter": {
                            "type": "string",
                            "description": "Filter spaces by type (e.g., 'spaceType=SPACE' for group chat, 'spaceType=DIRECT_MESSAGE' for DM)"
                        }
                    }
                }
            ),
            Tool(
                name="get_space",
                description="Get details about a specific Google Chat space",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "space": {
                            "type": "string",
                            "description": "Space name (e.g., 'spaces/AAAA1234567')"
                        }
                    },
                    "required": ["space"]
                }
            ),
            Tool(
                name="create_space",
                description="Create a new Google Chat space (group chat)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "display_name": {
                            "type": "string",
                            "description": "Display name for the new space"
                        },
                        "space_type": {
                            "type": "string",
                            "description": "Type of space to create",
                            "enum": ["SPACE", "GROUP_CHAT"],
                            "default": "SPACE"
                        },
                        "threaded": {
                            "type": "boolean",
                            "description": "Whether the space should support threaded messages",
                            "default": False
                        },
                        "external_user_allowed": {
                            "type": "boolean",
                            "description": "Whether external users can be added to the space",
                            "default": False
                        }
                    },
                    "required": ["display_name"]
                }
            ),
            Tool(
                name="update_space",
                description="Update an existing Google Chat space",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "space": {
                            "type": "string",
                            "description": "Space name (e.g., 'spaces/AAAA1234567')"
                        },
                        "display_name": {
                            "type": "string",
                            "description": "New display name for the space"
                        },
                        "threaded": {
                            "type": "boolean",
                            "description": "Whether the space should support threaded messages"
                        },
                        "external_user_allowed": {
                            "type": "boolean",
                            "description": "Whether external users can be added to the space"
                        },
                        "update_mask": {
                            "type": "string",
                            "description": "Fields to update (default: 'displayName,spaceDetails')",
                            "default": "displayName,spaceDetails"
                        }
                    },
                    "required": ["space"]
                }
            ),
            Tool(
                name="delete_space",
                description="Delete a Google Chat space",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "space": {
                            "type": "string",
                            "description": "Space name (e.g., 'spaces/AAAA1234567')"
                        }
                    },
                    "required": ["space"]
                }
            )
        ]
    
    def get_tool_names(self) -> List[str]:
        """Return list of tool names."""
        return [
            "list_spaces",
            "get_space",
            "create_space",
            "update_space",
            "delete_space"
        ]
    
    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a space tool."""
        await self._ensure_authenticated()
        
        if tool_name == "list_spaces":
            return await self.list_spaces(arguments)
        elif tool_name == "get_space":
            return await self.get_space(arguments)
        elif tool_name == "create_space":
            return await self.create_space(arguments)
        elif tool_name == "update_space":
            return await self.update_space(arguments)
        elif tool_name == "delete_space":
            return await self.delete_space(arguments)
        else:
            raise ValueError(f"Unknown space tool: {tool_name}")
    
    async def list_spaces(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List available spaces."""
        try:
            service = self._get_service()
            limit = args.get("limit", 25)
            filter_query = args.get("filter")
            
            request_params = {
                "pageSize": min(limit, 100)
            }
            
            if filter_query:
                request_params["filter"] = filter_query
            
            result = service.spaces().list(**request_params).execute()
            
            spaces = result.get("spaces", [])
            logger.info(f"Retrieved {len(spaces)} spaces")
            
            return {
                "success": True,
                "spaces": spaces,
                "count": len(spaces)
            }
            
        except HttpError as e:
            return self._handle_api_error(e, "list_spaces")
        except Exception as e:
            logger.error(f"Unexpected error listing spaces: {e}")
            return {"error": str(e)}
    
    async def get_space(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get details about a specific space."""
        try:
            service = self._get_service()
            space_name = args["space"]
            
            result = service.spaces().get(name=space_name).execute()
            
            logger.info(f"Retrieved space details for {space_name}")
            return {
                "success": True,
                "space": result
            }
            
        except HttpError as e:
            return self._handle_api_error(e, "get_space")
        except Exception as e:
            logger.error(f"Unexpected error getting space: {e}")
            return {"error": str(e)}
    
    async def create_space(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new space."""
        try:
            service = self._get_service()
            
            space_body = {
                "displayName": args["display_name"],
                "spaceType": args.get("space_type", "SPACE"),
                "spaceDetails": {
                    "guidelines": f"Space created via MCP server"
                }
            }
            
            # Add threading support if specified
            if "threaded" in args:
                space_body["spaceThreadingState"] = "THREADED_MESSAGES" if args["threaded"] else "UNTHREADED_MESSAGES"
            
            # Add external user setting if specified
            if "external_user_allowed" in args:
                space_body["spaceDetails"]["externalUserAllowed"] = args["external_user_allowed"]
            
            result = service.spaces().create(body=space_body).execute()
            
            logger.info(f"Created new space: {result.get('name')}")
            return {
                "success": True,
                "space": result,
                "space_id": result.get("name")
            }
            
        except HttpError as e:
            return self._handle_api_error(e, "create_space")
        except Exception as e:
            logger.error(f"Unexpected error creating space: {e}")
            return {"error": str(e)}
    
    async def update_space(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing space."""
        try:
            service = self._get_service()
            space_name = args["space"]
            update_mask = args.get("update_mask", "displayName,spaceDetails")
            
            space_body = {}
            
            if "display_name" in args:
                space_body["displayName"] = args["display_name"]
            
            if "threaded" in args:
                space_body["spaceThreadingState"] = "THREADED_MESSAGES" if args["threaded"] else "UNTHREADED_MESSAGES"
            
            if "external_user_allowed" in args:
                space_body["spaceDetails"] = {
                    "externalUserAllowed": args["external_user_allowed"]
                }
            
            result = service.spaces().patch(
                name=space_name,
                updateMask=update_mask,
                body=space_body
            ).execute()
            
            logger.info(f"Updated space {space_name}")
            return {
                "success": True,
                "space": result
            }
            
        except HttpError as e:
            return self._handle_api_error(e, "update_space")
        except Exception as e:
            logger.error(f"Unexpected error updating space: {e}")
            return {"error": str(e)}
    
    async def delete_space(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a space."""
        try:
            service = self._get_service()
            space_name = args["space"]
            
            service.spaces().delete(name=space_name).execute()
            
            logger.info(f"Deleted space {space_name}")
            return {
                "success": True,
                "message": f"Space {space_name} deleted successfully"
            }
            
        except HttpError as e:
            return self._handle_api_error(e, "delete_space")
        except Exception as e:
            logger.error(f"Unexpected error deleting space: {e}")
            return {"error": str(e)}