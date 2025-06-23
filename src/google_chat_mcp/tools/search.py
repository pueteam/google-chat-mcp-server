"""Search tools for Google Chat."""

import logging
from typing import Any, Dict, List, Optional

from mcp.types import Tool
from googleapiclient.errors import HttpError

from .base import BaseTool

logger = logging.getLogger(__name__)


class SearchTools(BaseTool):
    """Tools for searching Google Chat content."""
    
    def get_tools(self) -> List[Tool]:
        """Return list of search-related tools."""
        return [
            Tool(
                name="search_messages",
                description="Search for messages across Google Chat spaces",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query (supports text search and filters)"
                        },
                        "space": {
                            "type": "string",
                            "description": "Limit search to specific space (e.g., 'spaces/AAAA1234567')"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results (default: 25, max: 100)",
                            "minimum": 1,
                            "maximum": 100,
                            "default": 25
                        },
                        "order_by": {
                            "type": "string",
                            "description": "Sort order for results",
                            "enum": ["create_time desc", "create_time", "relevance"],
                            "default": "relevance"
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="search_spaces",
                description="Search for Google Chat spaces by name or description",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for space names or descriptions"
                        },
                        "space_type": {
                            "type": "string",
                            "description": "Filter by space type",
                            "enum": ["SPACE", "GROUP_CHAT", "DIRECT_MESSAGE"]
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results (default: 25, max: 100)",
                            "minimum": 1,
                            "maximum": 100,
                            "default": 25
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="search_members",
                description="Search for members across spaces or within a specific space",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for member names or email addresses"
                        },
                        "space": {
                            "type": "string",
                            "description": "Limit search to specific space (e.g., 'spaces/AAAA1234567')"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results (default: 25, max: 100)",
                            "minimum": 1,
                            "maximum": 100,
                            "default": 25
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="get_recent_activity",
                description="Get recent activity across accessible spaces",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "space": {
                            "type": "string",
                            "description": "Limit to specific space (e.g., 'spaces/AAAA1234567')"
                        },
                        "hours": {
                            "type": "integer",
                            "description": "Number of hours to look back (default: 24, max: 168)",
                            "minimum": 1,
                            "maximum": 168,
                            "default": 24
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of activities (default: 50, max: 200)",
                            "minimum": 1,
                            "maximum": 200,
                            "default": 50
                        },
                        "activity_types": {
                            "type": "array",
                            "description": "Types of activities to include",
                            "items": {
                                "type": "string",
                                "enum": ["MESSAGE", "MEMBERSHIP_CHANGE", "SPACE_UPDATE"]
                            },
                            "default": ["MESSAGE"]
                        }
                    }
                }
            )
        ]
    
    def get_tool_names(self) -> List[str]:
        """Return list of tool names."""
        return [
            "search_messages",
            "search_spaces",
            "search_members",
            "get_recent_activity"
        ]
    
    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a search tool."""
        await self._ensure_authenticated()
        
        if tool_name == "search_messages":
            return await self.search_messages(arguments)
        elif tool_name == "search_spaces":
            return await self.search_spaces(arguments)
        elif tool_name == "search_members":
            return await self.search_members(arguments)
        elif tool_name == "get_recent_activity":
            return await self.get_recent_activity(arguments)
        else:
            raise ValueError(f"Unknown search tool: {tool_name}")
    
    async def search_messages(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search for messages using Google Chat's search capabilities."""
        try:
            service = self._get_service()
            query = args["query"]
            limit = args.get("limit", 25)
            order_by = args.get("order_by", "relevance")
            space = args.get("space")
            
            # Build search parameters
            search_params = {
                "pageSize": min(limit, 100),
                "orderBy": order_by
            }
            
            # If space is specified, search within that space only
            if space:
                # Search messages within specific space
                result = service.spaces().messages().list(
                    parent=space,
                    pageSize=min(limit, 100),
                    orderBy=order_by if order_by != "relevance" else "create_time desc",
                    filter=f'text:"{query}"'
                ).execute()
                
                messages = result.get("messages", [])
                # Filter messages that contain the query text (basic text search)
                filtered_messages = [
                    msg for msg in messages 
                    if query.lower() in msg.get("text", "").lower()
                ][:limit]
                
            else:
                # Search across all accessible spaces
                # Note: Google Chat API has limited search capabilities
                # This implements a basic approach by searching recent messages
                spaces_result = service.spaces().list(pageSize=50).execute()
                spaces = spaces_result.get("spaces", [])
                
                all_messages = []
                for space_info in spaces:
                    try:
                        messages_result = service.spaces().messages().list(
                            parent=space_info["name"],
                            pageSize=20,
                            orderBy="create_time desc"
                        ).execute()
                        
                        space_messages = messages_result.get("messages", [])
                        # Add space info to each message
                        for msg in space_messages:
                            msg["_space_info"] = space_info
                        
                        all_messages.extend(space_messages)
                    except HttpError:
                        # Skip spaces we can't access
                        continue
                
                # Filter messages that contain the query text
                filtered_messages = [
                    msg for msg in all_messages 
                    if query.lower() in msg.get("text", "").lower()
                ][:limit]
            
            logger.info(f"Found {len(filtered_messages)} messages matching '{query}'")
            return {
                "success": True,
                "messages": filtered_messages,
                "count": len(filtered_messages),
                "query": query,
                "space": space
            }
            
        except HttpError as e:
            return self._handle_api_error(e, "search_messages")
        except Exception as e:
            logger.error(f"Unexpected error searching messages: {e}")
            return {"error": str(e)}
    
    async def search_spaces(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search for spaces by name or description."""
        try:
            service = self._get_service()
            query = args["query"].lower()
            space_type = args.get("space_type")
            limit = args.get("limit", 25)
            
            # Get all accessible spaces
            filter_params = {}
            if space_type:
                filter_params["filter"] = f"spaceType={space_type}"
            
            result = service.spaces().list(
                pageSize=100,
                **filter_params
            ).execute()
            
            spaces = result.get("spaces", [])
            
            # Filter spaces that match the query
            filtered_spaces = []
            for space in spaces:
                display_name = space.get("displayName", "").lower()
                space_details = space.get("spaceDetails", {})
                description = space_details.get("description", "").lower()
                
                if (query in display_name or 
                    query in description or
                    query in space.get("name", "").lower()):
                    filtered_spaces.append(space)
                    
                    if len(filtered_spaces) >= limit:
                        break
            
            logger.info(f"Found {len(filtered_spaces)} spaces matching '{query}'")
            return {
                "success": True,
                "spaces": filtered_spaces,
                "count": len(filtered_spaces),
                "query": args["query"],
                "space_type": space_type
            }
            
        except HttpError as e:
            return self._handle_api_error(e, "search_spaces")
        except Exception as e:
            logger.error(f"Unexpected error searching spaces: {e}")
            return {"error": str(e)}
    
    async def search_members(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search for members by name or email."""
        try:
            service = self._get_service()
            query = args["query"].lower()
            space = args.get("space")
            limit = args.get("limit", 25)
            
            all_members = []
            
            if space:
                # Search within specific space
                result = service.spaces().members().list(
                    parent=space,
                    pageSize=100
                ).execute()
                
                members = result.get("memberships", [])
                for member in members:
                    member["_space"] = space
                
                all_members.extend(members)
            else:
                # Search across all accessible spaces
                spaces_result = service.spaces().list(pageSize=50).execute()
                spaces = spaces_result.get("spaces", [])
                
                for space_info in spaces:
                    try:
                        members_result = service.spaces().members().list(
                            parent=space_info["name"],
                            pageSize=50
                        ).execute()
                        
                        members = members_result.get("memberships", [])
                        for member in members:
                            member["_space"] = space_info["name"]
                            member["_space_info"] = space_info
                        
                        all_members.extend(members)
                    except HttpError:
                        # Skip spaces we can't access
                        continue
            
            # Filter members that match the query
            filtered_members = []
            for member in all_members:
                member_info = member.get("member", {})
                display_name = member_info.get("displayName", "").lower()
                name = member_info.get("name", "").lower()
                
                if (query in display_name or 
                    query in name or
                    query in str(member_info.get("domainId", "")).lower()):
                    filtered_members.append(member)
                    
                    if len(filtered_members) >= limit:
                        break
            
            logger.info(f"Found {len(filtered_members)} members matching '{query}'")
            return {
                "success": True,
                "members": filtered_members,
                "count": len(filtered_members),
                "query": args["query"],
                "space": space
            }
            
        except HttpError as e:
            return self._handle_api_error(e, "search_members")
        except Exception as e:
            logger.error(f"Unexpected error searching members: {e}")
            return {"error": str(e)}
    
    async def get_recent_activity(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get recent activity across spaces."""
        try:
            service = self._get_service()
            space = args.get("space")
            hours = args.get("hours", 24)
            limit = args.get("limit", 50)
            activity_types = args.get("activity_types", ["MESSAGE"])
            
            # Calculate time threshold
            from datetime import datetime, timedelta, timezone
            time_threshold = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            activities = []
            
            if space:
                # Get activity from specific space
                spaces = [{"name": space}]
            else:
                # Get activity from all accessible spaces
                spaces_result = service.spaces().list(pageSize=50).execute()
                spaces = spaces_result.get("spaces", [])
            
            for space_info in spaces:
                space_name = space_info["name"]
                
                try:
                    # Get recent messages if MESSAGE activity is requested
                    if "MESSAGE" in activity_types:
                        messages_result = service.spaces().messages().list(
                            parent=space_name,
                            pageSize=min(limit, 50),
                            orderBy="create_time desc"
                        ).execute()
                        
                        messages = messages_result.get("messages", [])
                        for msg in messages:
                            # Parse create_time and check if within threshold
                            create_time_str = msg.get("createTime", "")
                            if create_time_str:
                                try:
                                    # Parse RFC3339 timestamp
                                    create_time = datetime.fromisoformat(
                                        create_time_str.replace('Z', '+00:00')
                                    )
                                    
                                    if create_time >= time_threshold:
                                        activities.append({
                                            "type": "MESSAGE",
                                            "timestamp": create_time_str,
                                            "space": space_name,
                                            "space_info": space_info,
                                            "data": msg
                                        })
                                except ValueError:
                                    # Skip messages with invalid timestamps
                                    continue
                    
                    # Note: Google Chat API has limited support for other activity types
                    # In a full implementation, you would add support for:
                    # - MEMBERSHIP_CHANGE: tracking member additions/removals
                    # - SPACE_UPDATE: tracking space setting changes
                    
                except HttpError:
                    # Skip spaces we can't access
                    continue
            
            # Sort activities by timestamp (most recent first)
            activities.sort(key=lambda x: x["timestamp"], reverse=True)
            activities = activities[:limit]
            
            logger.info(f"Found {len(activities)} recent activities")
            return {
                "success": True,
                "activities": activities,
                "count": len(activities),
                "hours": hours,
                "activity_types": activity_types,
                "space": space
            }
            
        except HttpError as e:
            return self._handle_api_error(e, "get_recent_activity")
        except Exception as e:
            logger.error(f"Unexpected error getting recent activity: {e}")
            return {"error": str(e)}