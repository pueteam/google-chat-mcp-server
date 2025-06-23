"""Webhook and event handling tools for Google Chat."""

import logging
from typing import Any, Dict, List, Optional

from mcp.types import Tool
from googleapiclient.errors import HttpError

from .base import BaseTool

logger = logging.getLogger(__name__)


class WebhookTools(BaseTool):
    """Tools for managing Google Chat webhooks and events."""
    
    def get_tools(self) -> List[Tool]:
        """Return list of webhook-related tools."""
        return [
            Tool(
                name="send_webhook_message",
                description="Send a message to a Google Chat space via incoming webhook",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "webhook_url": {
                            "type": "string",
                            "description": "Incoming webhook URL for the space"
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
                    "required": ["webhook_url"]
                }
            ),
            Tool(
                name="create_card_message",
                description="Create a rich card message for Google Chat",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Card title"
                        },
                        "subtitle": {
                            "type": "string",
                            "description": "Card subtitle"
                        },
                        "text": {
                            "type": "string",
                            "description": "Card text content"
                        },
                        "image_url": {
                            "type": "string",
                            "description": "URL of image to include in card"
                        },
                        "buttons": {
                            "type": "array",
                            "description": "Action buttons for the card",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "text": {"type": "string"},
                                    "url": {"type": "string"},
                                    "action": {"type": "string"}
                                },
                                "required": ["text"]
                            }
                        },
                        "color": {
                            "type": "string",
                            "description": "Accent color for the card (hex color code)",
                            "pattern": "^#[0-9A-Fa-f]{6}$"
                        }
                    },
                    "required": ["title"]
                }
            ),
            Tool(
                name="parse_webhook_event",
                description="Parse an incoming webhook event from Google Chat",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "event_data": {
                            "type": "object",
                            "description": "Raw event data from Google Chat webhook"
                        }
                    },
                    "required": ["event_data"]
                }
            ),
            Tool(
                name="validate_webhook_signature",
                description="Validate the signature of an incoming webhook request",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "request_body": {
                            "type": "string",
                            "description": "Raw request body from webhook"
                        },
                        "signature": {
                            "type": "string",
                            "description": "X-Goog-Chat-Request-Signature header value"
                        },
                        "timestamp": {
                            "type": "string",
                            "description": "X-Goog-Chat-Request-Timestamp header value"
                        },
                        "webhook_secret": {
                            "type": "string",
                            "description": "Secret key for webhook validation"
                        }
                    },
                    "required": ["request_body", "signature", "timestamp", "webhook_secret"]
                }
            ),
            Tool(
                name="create_interactive_card",
                description="Create an interactive card with buttons and actions",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Card title"
                        },
                        "sections": {
                            "type": "array",
                            "description": "Card sections with content",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "header": {"type": "string"},
                                    "widgets": {
                                        "type": "array",
                                        "items": {"type": "object"}
                                    }
                                }
                            }
                        },
                        "actions": {
                            "type": "array",
                            "description": "Interactive actions for the card",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "action_id": {"type": "string"},
                                    "button_text": {"type": "string"},
                                    "parameters": {"type": "object"}
                                },
                                "required": ["action_id", "button_text"]
                            }
                        }
                    },
                    "required": ["title"]
                }
            )
        ]
    
    def get_tool_names(self) -> List[str]:
        """Return list of tool names."""
        return [
            "send_webhook_message",
            "create_card_message",
            "parse_webhook_event",
            "validate_webhook_signature",
            "create_interactive_card"
        ]
    
    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a webhook tool."""
        # Note: Most webhook tools don't require API authentication
        # as they work with webhook URLs or process incoming data
        
        if tool_name == "send_webhook_message":
            return await self.send_webhook_message(arguments)
        elif tool_name == "create_card_message":
            return await self.create_card_message(arguments)
        elif tool_name == "parse_webhook_event":
            return await self.parse_webhook_event(arguments)
        elif tool_name == "validate_webhook_signature":
            return await self.validate_webhook_signature(arguments)
        elif tool_name == "create_interactive_card":
            return await self.create_interactive_card(arguments)
        else:
            raise ValueError(f"Unknown webhook tool: {tool_name}")
    
    async def send_webhook_message(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Send a message via incoming webhook."""
        try:
            import aiohttp
            
            webhook_url = args["webhook_url"]
            
            # Build message body
            message_body = {}
            
            if "text" in args:
                message_body["text"] = args["text"]
            
            if "cards" in args:
                message_body["cards"] = args["cards"]
            
            if "thread" in args:
                message_body["thread"] = {"name": args["thread"]}
            
            # Send via webhook
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=message_body) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Webhook message sent successfully")
                        return {
                            "success": True,
                            "message": "Message sent via webhook",
                            "response": result
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Webhook request failed: {response.status} - {error_text}")
                        return {
                            "error": f"Webhook request failed: {response.status}",
                            "details": error_text
                        }
            
        except Exception as e:
            logger.error(f"Error sending webhook message: {e}")
            return {"error": str(e)}
    
    async def create_card_message(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a rich card message structure."""
        try:
            title = args["title"]
            subtitle = args.get("subtitle")
            text = args.get("text")
            image_url = args.get("image_url")
            buttons = args.get("buttons", [])
            color = args.get("color")
            
            # Build card structure
            card = {
                "header": {
                    "title": title
                }
            }
            
            if subtitle:
                card["header"]["subtitle"] = subtitle
            
            if image_url:
                card["header"]["imageUrl"] = image_url
            
            if color:
                card["header"]["imageStyle"] = "IMAGE"
            
            # Add sections
            sections = []
            
            if text:
                sections.append({
                    "widgets": [
                        {
                            "textParagraph": {
                                "text": text
                            }
                        }
                    ]
                })
            
            # Add buttons
            if buttons:
                button_widgets = []
                for button in buttons:
                    widget = {
                        "buttons": [
                            {
                                "textButton": {
                                    "text": button["text"]
                                }
                            }
                        ]
                    }
                    
                    if "url" in button:
                        widget["buttons"][0]["textButton"]["onClick"] = {
                            "openLink": {
                                "url": button["url"]
                            }
                        }
                    elif "action" in button:
                        widget["buttons"][0]["textButton"]["onClick"] = {
                            "action": {
                                "actionMethodName": button["action"]
                            }
                        }
                    
                    button_widgets.append(widget)
                
                if button_widgets:
                    sections.append({
                        "widgets": button_widgets
                    })
            
            if sections:
                card["sections"] = sections
            
            logger.info(f"Created card message with title: {title}")
            return {
                "success": True,
                "card": card,
                "cards": [card]  # Format for direct use in messages
            }
            
        except Exception as e:
            logger.error(f"Error creating card message: {e}")
            return {"error": str(e)}
    
    async def parse_webhook_event(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Parse an incoming webhook event."""
        try:
            event_data = args["event_data"]
            
            # Extract common event fields
            event_type = event_data.get("type", "UNKNOWN")
            event_time = event_data.get("eventTime")
            space = event_data.get("space", {})
            user = event_data.get("user", {})
            message = event_data.get("message", {})
            
            parsed_event = {
                "event_type": event_type,
                "event_time": event_time,
                "space": {
                    "name": space.get("name"),
                    "display_name": space.get("displayName"),
                    "type": space.get("type")
                },
                "user": {
                    "name": user.get("name"),
                    "display_name": user.get("displayName"),
                    "email": user.get("email"),
                    "type": user.get("type")
                }
            }
            
            # Parse message-specific data
            if message:
                parsed_event["message"] = {
                    "name": message.get("name"),
                    "text": message.get("text"),
                    "create_time": message.get("createTime"),
                    "sender": message.get("sender", {}),
                    "thread": message.get("thread", {}),
                    "annotations": message.get("annotations", [])
                }
            
            # Parse action-specific data for interactive cards
            if "action" in event_data:
                action = event_data["action"]
                parsed_event["action"] = {
                    "action_method_name": action.get("actionMethodName"),
                    "parameters": action.get("parameters", [])
                }
            
            logger.info(f"Parsed webhook event of type: {event_type}")
            return {
                "success": True,
                "parsed_event": parsed_event,
                "original_event": event_data
            }
            
        except Exception as e:
            logger.error(f"Error parsing webhook event: {e}")
            return {"error": str(e)}
    
    async def validate_webhook_signature(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Validate webhook signature for security."""
        try:
            import hmac
            import hashlib
            import base64
            
            request_body = args["request_body"]
            signature = args["signature"]
            timestamp = args["timestamp"]
            webhook_secret = args["webhook_secret"]
            
            # Create the string to sign
            string_to_sign = f"{timestamp}.{request_body}"
            
            # Calculate expected signature
            expected_signature = hmac.new(
                webhook_secret.encode(),
                string_to_sign.encode(),
                hashlib.sha256
            ).digest()
            
            expected_signature_b64 = base64.b64encode(expected_signature).decode()
            
            # Extract signature from header (format: "t=timestamp,v1=signature")
            signature_parts = {}
            for part in signature.split(","):
                if "=" in part:
                    key, value = part.split("=", 1)
                    signature_parts[key] = value
            
            provided_signature = signature_parts.get("v1", "")
            
            # Compare signatures
            is_valid = hmac.compare_digest(expected_signature_b64, provided_signature)
            
            # Also check timestamp to prevent replay attacks (optional)
            import time
            current_time = int(time.time())
            request_time = int(timestamp)
            time_diff = abs(current_time - request_time)
            
            # Allow 5 minutes tolerance
            is_recent = time_diff <= 300
            
            logger.info(f"Webhook signature validation: valid={is_valid}, recent={is_recent}")
            return {
                "success": True,
                "is_valid": is_valid,
                "is_recent": is_recent,
                "time_difference_seconds": time_diff,
                "signature_valid": is_valid and is_recent
            }
            
        except Exception as e:
            logger.error(f"Error validating webhook signature: {e}")
            return {"error": str(e)}
    
    async def create_interactive_card(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create an interactive card with actions."""
        try:
            title = args["title"]
            sections = args.get("sections", [])
            actions = args.get("actions", [])
            
            # Build interactive card structure
            card = {
                "header": {
                    "title": title
                },
                "sections": []
            }
            
            # Add provided sections
            for section in sections:
                card_section = {}
                if "header" in section:
                    card_section["header"] = section["header"]
                
                if "widgets" in section:
                    card_section["widgets"] = section["widgets"]
                
                card["sections"].append(card_section)
            
            # Add action buttons as a separate section
            if actions:
                action_widgets = []
                for action in actions:
                    action_widget = {
                        "buttons": [
                            {
                                "textButton": {
                                    "text": action["button_text"],
                                    "onClick": {
                                        "action": {
                                            "actionMethodName": action["action_id"]
                                        }
                                    }
                                }
                            }
                        ]
                    }
                    
                    # Add parameters if provided
                    if "parameters" in action:
                        action_widget["buttons"][0]["textButton"]["onClick"]["action"]["parameters"] = [
                            {"key": k, "value": v} for k, v in action["parameters"].items()
                        ]
                    
                    action_widgets.append(action_widget)
                
                card["sections"].append({
                    "widgets": action_widgets
                })
            
            logger.info(f"Created interactive card with title: {title}")
            return {
                "success": True,
                "card": card,
                "cards": [card]  # Format for direct use in messages
            }
            
        except Exception as e:
            logger.error(f"Error creating interactive card: {e}")
            return {"error": str(e)}