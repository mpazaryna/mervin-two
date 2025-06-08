"""
MCP Protocol Message Types and Schemas

This module defines the message types and validation schemas for the MCP protocol.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum


class MessageType(str, Enum):
    """Enumeration of MCP message types."""
    # Core protocol messages
    PING = "ping"
    PONG = "pong"
    INITIALIZE = "initialize"
    INITIALIZED = "initialized"
    
    # Tool-related messages
    LIST_TOOLS = "list_tools"
    CALL_TOOL = "call_tool"
    
    # Resource-related messages
    LIST_RESOURCES = "list_resources"
    READ_RESOURCE = "read_resource"
    
    # Prompt-related messages
    LIST_PROMPTS = "list_prompts"
    GET_PROMPT = "get_prompt"
    
    # Error and notification messages
    ERROR = "error"
    NOTIFICATION = "notification"


class BaseMessage(BaseModel):
    """Base class for all MCP messages."""
    model_config = ConfigDict(use_enum_values=True)

    type: MessageType
    id: Optional[str] = None


class PingMessage(BaseMessage):
    """Ping message for connection health checks."""
    type: MessageType = MessageType.PING


class PongMessage(BaseMessage):
    """Pong response to ping message."""
    type: MessageType = MessageType.PONG


class InitializeMessage(BaseMessage):
    """Initialize message to start MCP session."""
    type: MessageType = MessageType.INITIALIZE
    params: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('params')
    @classmethod
    def validate_params(cls, v):
        """Validate initialization parameters."""
        if not isinstance(v, dict):
            raise ValueError("params must be a dictionary")
        return v


class InitializedMessage(BaseMessage):
    """Response to initialize message."""
    type: MessageType = MessageType.INITIALIZED
    result: Dict[str, Any] = Field(default_factory=dict)


class ToolInfo(BaseModel):
    """Information about a tool."""
    name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ListToolsMessage(BaseMessage):
    """Message to list available tools."""
    type: MessageType = MessageType.LIST_TOOLS


class ListToolsResponse(BaseMessage):
    """Response with list of available tools."""
    type: MessageType = MessageType.LIST_TOOLS
    result: Dict[str, List[ToolInfo]] = Field(default_factory=lambda: {"tools": []})


class CallToolMessage(BaseMessage):
    """Message to call a specific tool."""
    type: MessageType = MessageType.CALL_TOOL
    params: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('params')
    @classmethod
    def validate_tool_params(cls, v):
        """Validate tool call parameters."""
        if not isinstance(v, dict):
            raise ValueError("params must be a dictionary")
        if 'name' not in v:
            raise ValueError("Tool name is required in params")
        return v


class CallToolResponse(BaseMessage):
    """Response from tool call."""
    type: MessageType = MessageType.CALL_TOOL
    result: Dict[str, Any] = Field(default_factory=dict)


class ResourceInfo(BaseModel):
    """Information about a resource."""
    id: str
    path: str
    title: str
    description: str
    mime_type: str = "text/plain"
    tags: List[str] = Field(default_factory=list)


class ListResourcesMessage(BaseMessage):
    """Message to list available resources."""
    type: MessageType = MessageType.LIST_RESOURCES


class ListResourcesResponse(BaseMessage):
    """Response with list of available resources."""
    type: MessageType = MessageType.LIST_RESOURCES
    result: Dict[str, List[ResourceInfo]] = Field(default_factory=lambda: {"resources": []})


class ReadResourceMessage(BaseMessage):
    """Message to read a specific resource."""
    type: MessageType = MessageType.READ_RESOURCE
    params: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('params')
    @classmethod
    def validate_resource_params(cls, v):
        """Validate resource read parameters."""
        if not isinstance(v, dict):
            raise ValueError("params must be a dictionary")
        if 'id' not in v:
            raise ValueError("Resource ID is required in params")
        return v


class ReadResourceResponse(BaseMessage):
    """Response from resource read."""
    type: MessageType = MessageType.READ_RESOURCE
    result: Dict[str, Any] = Field(default_factory=dict)


class PromptInfo(BaseModel):
    """Information about a prompt."""
    id: str
    title: str
    description: str
    parameters: List[Dict[str, Any]] = Field(default_factory=list)
    examples: List[Dict[str, Any]] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class ListPromptsMessage(BaseMessage):
    """Message to list available prompts."""
    type: MessageType = MessageType.LIST_PROMPTS


class ListPromptsResponse(BaseMessage):
    """Response with list of available prompts."""
    type: MessageType = MessageType.LIST_PROMPTS
    result: Dict[str, List[PromptInfo]] = Field(default_factory=lambda: {"prompts": []})


class GetPromptMessage(BaseMessage):
    """Message to get a specific prompt."""
    type: MessageType = MessageType.GET_PROMPT
    params: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('params')
    @classmethod
    def validate_prompt_params(cls, v):
        """Validate prompt get parameters."""
        if not isinstance(v, dict):
            raise ValueError("params must be a dictionary")
        if 'id' not in v:
            raise ValueError("Prompt ID is required in params")
        return v


class GetPromptResponse(BaseMessage):
    """Response from prompt get."""
    type: MessageType = MessageType.GET_PROMPT
    result: Dict[str, Any] = Field(default_factory=dict)


class ErrorMessage(BaseMessage):
    """Error message for protocol errors."""
    type: MessageType = MessageType.ERROR
    error: str
    code: Optional[int] = None
    data: Optional[Dict[str, Any]] = None


class NotificationMessage(BaseMessage):
    """Notification message for events."""
    type: MessageType = MessageType.NOTIFICATION
    method: str
    params: Optional[Dict[str, Any]] = None


# Union type for all possible messages
MCPMessage = Union[
    PingMessage,
    PongMessage,
    InitializeMessage,
    InitializedMessage,
    ListToolsMessage,
    ListToolsResponse,
    CallToolMessage,
    CallToolResponse,
    ListResourcesMessage,
    ListResourcesResponse,
    ReadResourceMessage,
    ReadResourceResponse,
    ListPromptsMessage,
    ListPromptsResponse,
    GetPromptMessage,
    GetPromptResponse,
    ErrorMessage,
    NotificationMessage
]


def parse_message(data: Dict[str, Any]) -> MCPMessage:
    """
    Parse a raw message dictionary into the appropriate message type.
    
    Args:
        data: Raw message data
        
    Returns:
        Parsed message object
        
    Raises:
        ValueError: If message type is unknown or validation fails
    """
    message_type = data.get('type')
    
    if not message_type:
        raise ValueError("Message type is required")
    
    # Map message types to their corresponding classes
    message_classes = {
        MessageType.PING: PingMessage,
        MessageType.PONG: PongMessage,
        MessageType.INITIALIZE: InitializeMessage,
        MessageType.INITIALIZED: InitializedMessage,
        MessageType.LIST_TOOLS: ListToolsMessage,
        MessageType.CALL_TOOL: CallToolMessage,
        MessageType.LIST_RESOURCES: ListResourcesMessage,
        MessageType.READ_RESOURCE: ReadResourceMessage,
        MessageType.LIST_PROMPTS: ListPromptsMessage,
        MessageType.GET_PROMPT: GetPromptMessage,
        MessageType.ERROR: ErrorMessage,
        MessageType.NOTIFICATION: NotificationMessage,
    }
    
    message_class = message_classes.get(MessageType(message_type))
    if not message_class:
        raise ValueError(f"Unknown message type: {message_type}")
    
    try:
        return message_class(**data)
    except Exception as e:
        raise ValueError(f"Failed to parse message: {str(e)}")


def create_error_message(error: str, code: Optional[int] = None, 
                        message_id: Optional[str] = None) -> ErrorMessage:
    """
    Create an error message.
    
    Args:
        error: Error description
        code: Optional error code
        message_id: Optional message ID for correlation
        
    Returns:
        Error message object
    """
    return ErrorMessage(
        id=message_id,
        error=error,
        code=code
    )
