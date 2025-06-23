"""Message management tools for Google Chat."""

import logging
from typing import Any, Dict, List, Optional

from mcp.types import Tool
from googleapiclient.errors import HttpError

from .base import BaseTool

logger = logging.getLogger(__name__)


class MessageTools(BaseTool):
    """Tools for managing Google Chat messages."""
    
    def get_tools(self) -> List[Tool]:
        """Return list of message-related tools."""
        return [
            Tool(
                name="send_message",
                description="Send a message to a Google Chat space",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "space": {
                            "type": "string",
                            "description": "Space name (e.g., 'spaces/AAAA1234567') or leave empty for default space"
                        },
                        "text": {
                            "type": "string",
                            "description": "Plain text message to send"
                        },
                        "cards": {
                            "type": "array",
                            "description": "Card messages (rich content)",
                            "items": {"type": "object"}
                        },
                        "thread": {
                            "type": "string",
                            "description": "Thread key to reply to (optional)"
                        }
                    },
                    "required": ["text"]
                }
            ),
            Tool(
                name="list_messages",
                description="List messages in a Google Chat space",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "space": {
                            "type": "string",
                            "description": "Space name (e.g., 'spaces/AAAA1234567') or leave empty for default space"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of messages to return (default: 25, max: 100)",
                            "minimum": 1,
                            "maximum": 100,
                            "default": 25
                        },
                        "order_by": {
                            "type": "string",
                            "description": "Order messages by (create_time desc or create_time)",
                            "enum": ["create_time desc", "create_time"],
                            "default": "create_time desc"
                        }
                    }
                }
            ),
            Tool(
                name="get_message",
                description="Get a specific message by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Full message name (e.g., 'spaces/AAAA1234567/messages/xyz')"
                        }
                    },
                    "required": ["message"]
                }
            ),
            Tool(
                name="update_message",
                description="Update an existing message",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Full message name (e.g., 'spaces/AAAA1234567/messages/xyz')"
                        },
                        "text": {
                            "type": "string",
                            "description": "New text content"
                        },
                        "cards": {
                            "type": "array",
                            "description": "New card content",
                            "items": {"type": "object"}
                        },
                        "update_mask": {
                            "type": "string",
                            "description": "Fields to update (default: 'text,cards')",
                            "default": "text,cards"
                        }
                    },
                    "required": ["message"]
                }
            ),
            Tool(
                name="delete_message",
                description="Delete a message",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Full message name (e.g., 'spaces/AAAA1234567/messages/xyz')"
                        }
                    },
                    "required": ["message"]
                }
            )
        ]
    
    def get_tool_names(self) -> List[str]:
        """Return list of tool names."""
        return [
            "send_message",
            "list_messages", 
            "get_message",
            "update_message",
            "delete_message"
        ]
    
    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a message tool."""
        await self._ensure_authenticated()
        
        if tool_name == "send_message":
            return await self.send_message(arguments)
        elif tool_name == "list_messages":
            return await self.list_messages(arguments)
        elif tool_name == "get_message":
            return await self.get_message(arguments)
        elif tool_name == "update_message":
            return await self.update_message(arguments)
        elif tool_name == "delete_message":
            return await self.delete_message(arguments)
        else:
            raise ValueError(f"Unknown message tool: {tool_name}")
    
    async def send_message(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Send a message to a space."""
        try:
            service = self._get_service()
            space = self._validate_space(args.get("space"))
            
            # Build message body
            message_body = {}
            
            if "text" in args:
                message_body["text"] = args["text"]
            
            if "cards" in args:
                message_body["cards"] = args["cards"]
            
            # Add thread if specified
            if "thread" in args:
                message_body["thread"] = {"name": args["thread"]}
            
            # Send the message
            result = service.spaces().messages().create(
                parent=space,
                body=message_body
            ).execute()
            
            logger.info(f"Message sent successfully to {space}")
            return {
                "success": True,
                "message": result,
                "message_id": result.get("name"),
                "space": space
            }
            
        except HttpError as e:
            return self._handle_api_error(e, "send_message")
        except Exception as e:
            logger.error(f"Unexpected error sending message: {e}")
            return {"error": str(e)}
    
    async def list_messages(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List messages in a space."""
        try:
            service = self._get_service()
            space = self._validate_space(args.get("space"))
            limit = args.get("limit", 25)
            order_by = args.get("order_by", "create_time desc")
            
            result = service.spaces().messages().list(
                parent=space,
                pageSize=min(limit, 100),
                orderBy=order_by
            ).execute()
            
            messages = result.get("messages", [])
            logger.info(f"Retrieved {len(messages)} messages from {space}")
            
            return {
                "success": True,
                "messages": messages,
                "count": len(messages),
                "space": space
            }
            
        except HttpError as e:
            return self._handle_api_error(e, "list_messages")
        except Exception as e:
            logger.error(f"Unexpected error listing messages: {e}")
            return {"error": str(e)}
    
    async def get_message(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific message."""
        try:
            service = self._get_service()
            message_name = args["message"]
            
            result = service.spaces().messages().get(
                name=message_name
            ).execute()
            
            logger.info(f"Retrieved message {message_name}")
            return {
                "success": True,
                "message": result
            }
            
        except HttpError as e:
            return self._handle_api_error(e, "get_message")
        except Exception as e:
            logger.error(f"Unexpected error getting message: {e}")
            return {"error": str(e)}
    
    async def update_message(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing message."""
        try:
            service = self._get_service()
            message_name = args["message"]
            update_mask = args.get("update_mask", "text,cards")
            
            # Build update body
            message_body = {}
            if "text" in args:
                message_body["text"] = args["text"]
            if "cards" in args:
                message_body["cards"] = args["cards"]
            
            result = service.spaces().messages().patch(
                name=message_name,
                updateMask=update_mask,
                body=message_body
            ).execute()
            
            logger.info(f"Updated message {message_name}")
            return {
                "success": True,
                "message": result
            }
            
        except HttpError as e:
            return self._handle_api_error(e, "update_message")
        except Exception as e:
            logger.error(f"Unexpected error updating message: {e}")
            return {"error": str(e)}
    
    async def delete_message(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a message."""
        try:
            service = self._get_service()
            message_name = args["message"]
            
            service.spaces().messages().delete(
                name=message_name
            ).execute()
            
            logger.info(f"Deleted message {message_name}")
            return {
                "success": True,
                "message": f"Message {message_name} deleted successfully"
            }
            
        except HttpError as e:
            return self._handle_api_error(e, "delete_message")
        except Exception as e:
            logger.error(f"Unexpected error deleting message: {e}")
            return {"error": str(e)}