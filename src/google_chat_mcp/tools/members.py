"""Member management tools for Google Chat."""

import logging
from typing import Any, Dict, List, Optional

from mcp.types import Tool
from googleapiclient.errors import HttpError

from .base import BaseTool

logger = logging.getLogger(__name__)


class MemberTools(BaseTool):
    """Tools for managing Google Chat space members."""
    
    def get_tools(self) -> List[Tool]:
        """Return list of member-related tools."""
        return [
            Tool(
                name="list_members",
                description="List members in a Google Chat space",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "space": {
                            "type": "string",
                            "description": "Space name (e.g., 'spaces/AAAA1234567') or leave empty for default space"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of members to return (default: 25, max: 100)",
                            "minimum": 1,
                            "maximum": 100,
                            "default": 25
                        },
                        "show_groups": {
                            "type": "boolean",
                            "description": "Whether to include group memberships",
                            "default": False
                        },
                        "show_invited": {
                            "type": "boolean",
                            "description": "Whether to include invited but not joined members",
                            "default": True
                        }
                    }
                }
            ),
            Tool(
                name="get_member",
                description="Get details about a specific member in a space",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "member": {
                            "type": "string",
                            "description": "Full member name (e.g., 'spaces/AAAA1234567/members/xyz')"
                        }
                    },
                    "required": ["member"]
                }
            ),
            Tool(
                name="create_membership",
                description="Add a member to a Google Chat space",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "space": {
                            "type": "string",
                            "description": "Space name (e.g., 'spaces/AAAA1234567') or leave empty for default space"
                        },
                        "user": {
                            "type": "string",
                            "description": "User to add (email address or user ID)"
                        },
                        "role": {
                            "type": "string",
                            "description": "Member role in the space",
                            "enum": ["ROLE_MEMBER", "ROLE_MANAGER"],
                            "default": "ROLE_MEMBER"
                        }
                    },
                    "required": ["user"]
                }
            ),
            Tool(
                name="update_membership",
                description="Update a member's role in a space",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "member": {
                            "type": "string",
                            "description": "Full member name (e.g., 'spaces/AAAA1234567/members/xyz')"
                        },
                        "role": {
                            "type": "string",
                            "description": "New role for the member",
                            "enum": ["ROLE_MEMBER", "ROLE_MANAGER"]
                        },
                        "update_mask": {
                            "type": "string",
                            "description": "Fields to update (default: 'role')",
                            "default": "role"
                        }
                    },
                    "required": ["member", "role"]
                }
            ),
            Tool(
                name="delete_membership",
                description="Remove a member from a Google Chat space",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "member": {
                            "type": "string",
                            "description": "Full member name (e.g., 'spaces/AAAA1234567/members/xyz')"
                        }
                    },
                    "required": ["member"]
                }
            ),
            Tool(
                name="find_direct_message",
                description="Find or create a direct message space with a user",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user": {
                            "type": "string",
                            "description": "User to find DM with (email address or user ID)"
                        }
                    },
                    "required": ["user"]
                }
            )
        ]
    
    def get_tool_names(self) -> List[str]:
        """Return list of tool names."""
        return [
            "list_members",
            "get_member",
            "create_membership",
            "update_membership",
            "delete_membership",
            "find_direct_message"
        ]
    
    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a member tool."""
        await self._ensure_authenticated()
        
        if tool_name == "list_members":
            return await self.list_members(arguments)
        elif tool_name == "get_member":
            return await self.get_member(arguments)
        elif tool_name == "create_membership":
            return await self.create_membership(arguments)
        elif tool_name == "update_membership":
            return await self.update_membership(arguments)
        elif tool_name == "delete_membership":
            return await self.delete_membership(arguments)
        elif tool_name == "find_direct_message":
            return await self.find_direct_message(arguments)
        else:
            raise ValueError(f"Unknown member tool: {tool_name}")
    
    async def list_members(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List members in a space."""
        try:
            service = self._get_service()
            space = self._validate_space(args.get("space"))
            limit = args.get("limit", 25)
            show_groups = args.get("show_groups", False)
            show_invited = args.get("show_invited", True)
            
            request_params = {
                "parent": space,
                "pageSize": min(limit, 100),
                "showGroups": show_groups,
                "showInvited": show_invited
            }
            
            result = service.spaces().members().list(**request_params).execute()
            
            members = result.get("memberships", [])
            logger.info(f"Retrieved {len(members)} members from {space}")
            
            return {
                "success": True,
                "members": members,
                "count": len(members),
                "space": space
            }
            
        except HttpError as e:
            return self._handle_api_error(e, "list_members")
        except Exception as e:
            logger.error(f"Unexpected error listing members: {e}")
            return {"error": str(e)}
    
    async def get_member(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get details about a specific member."""
        try:
            service = self._get_service()
            member_name = args["member"]
            
            result = service.spaces().members().get(name=member_name).execute()
            
            logger.info(f"Retrieved member details for {member_name}")
            return {
                "success": True,
                "member": result
            }
            
        except HttpError as e:
            return self._handle_api_error(e, "get_member")
        except Exception as e:
            logger.error(f"Unexpected error getting member: {e}")
            return {"error": str(e)}
    
    async def create_membership(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Add a member to a space."""
        try:
            service = self._get_service()
            space = self._validate_space(args.get("space"))
            user = args["user"]
            role = args.get("role", "ROLE_MEMBER")
            
            # Format user identifier
            if "@" in user:
                # Email address
                user_id = f"users/{user}"
            elif user.startswith("users/"):
                # Already formatted
                user_id = user
            else:
                # Assume it's a user ID
                user_id = f"users/{user}"
            
            membership_body = {
                "member": {
                    "name": user_id,
                    "type": "HUMAN"
                },
                "role": role
            }
            
            result = service.spaces().members().create(
                parent=space,
                body=membership_body
            ).execute()
            
            logger.info(f"Added member {user} to {space}")
            return {
                "success": True,
                "membership": result,
                "member_id": result.get("name"),
                "space": space
            }
            
        except HttpError as e:
            return self._handle_api_error(e, "create_membership")
        except Exception as e:
            logger.error(f"Unexpected error creating membership: {e}")
            return {"error": str(e)}
    
    async def update_membership(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Update a member's role in a space."""
        try:
            service = self._get_service()
            member_name = args["member"]
            role = args["role"]
            update_mask = args.get("update_mask", "role")
            
            membership_body = {
                "role": role
            }
            
            result = service.spaces().members().patch(
                name=member_name,
                updateMask=update_mask,
                body=membership_body
            ).execute()
            
            logger.info(f"Updated member {member_name} role to {role}")
            return {
                "success": True,
                "membership": result
            }
            
        except HttpError as e:
            return self._handle_api_error(e, "update_membership")
        except Exception as e:
            logger.error(f"Unexpected error updating membership: {e}")
            return {"error": str(e)}
    
    async def delete_membership(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Remove a member from a space."""
        try:
            service = self._get_service()
            member_name = args["member"]
            
            service.spaces().members().delete(name=member_name).execute()
            
            logger.info(f"Removed member {member_name}")
            return {
                "success": True,
                "message": f"Member {member_name} removed successfully"
            }
            
        except HttpError as e:
            return self._handle_api_error(e, "delete_membership")
        except Exception as e:
            logger.error(f"Unexpected error deleting membership: {e}")
            return {"error": str(e)}
    
    async def find_direct_message(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Find or create a direct message space with a user."""
        try:
            service = self._get_service()
            user = args["user"]
            
            # Format user identifier
            if "@" in user:
                # Email address
                user_id = f"users/{user}"
            elif user.startswith("users/"):
                # Already formatted
                user_id = user
            else:
                # Assume it's a user ID
                user_id = f"users/{user}"
            
            # Try to find existing DM space
            spaces_result = service.spaces().list(
                filter=f"spaceType=DIRECT_MESSAGE"
            ).execute()
            
            spaces = spaces_result.get("spaces", [])
            
            # Look for DM with this user
            for space in spaces:
                members_result = service.spaces().members().list(
                    parent=space["name"]
                ).execute()
                
                members = members_result.get("memberships", [])
                user_members = [m for m in members if m.get("member", {}).get("name") == user_id]
                
                if user_members:
                    logger.info(f"Found existing DM space with {user}: {space['name']}")
                    return {
                        "success": True,
                        "space": space,
                        "space_id": space["name"],
                        "existing": True
                    }
            
            # If no existing DM found, create one by sending a message
            # Note: Google Chat automatically creates DM spaces when sending messages
            logger.info(f"No existing DM space found with {user}")
            return {
                "success": False,
                "message": f"No direct message space found with {user}. Send a message to create one.",
                "user": user_id
            }
            
        except HttpError as e:
            return self._handle_api_error(e, "find_direct_message")
        except Exception as e:
            logger.error(f"Unexpected error finding direct message: {e}")
            return {"error": str(e)}