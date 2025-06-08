"""
MCP Server Implementation

This module contains the core MCP server class that handles protocol messages
and manages tools, resources, and prompts.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime

from .messages import (
    MCPMessage, MessageType, parse_message, create_error_message,
    PingMessage, PongMessage, InitializeMessage, InitializedMessage,
    ListToolsMessage, ListToolsResponse, CallToolMessage, CallToolResponse,
    ToolInfo, ErrorMessage
)
from .logging_config import get_logger


class MCPServer:
    """
    Core MCP server implementation.
    
    Handles MCP protocol messages, manages tools, resources, and prompts,
    and provides the main message processing interface.
    """
    
    def __init__(self, debug: bool = False):
        """
        Initialize the MCP server.
        
        Args:
            debug: Enable debug mode for verbose logging
        """
        self.debug = debug
        self.logger = get_logger("mcp_server")
        if debug:
            self.logger.setLevel(logging.DEBUG)
        
        # Server state
        self.initialized = False
        self.server_info = {
            "name": "MCP Learning Server",
            "version": "0.1.0",
            "description": "Educational MCP server implementation"
        }
        
        # Tool, resource, and prompt registries
        self.tools: Dict[str, Callable] = {}
        self.tool_schemas: Dict[str, ToolInfo] = {}
        self.resources: Dict[str, Any] = {}
        self.prompts: Dict[str, Any] = {}
        
        self.logger.info("MCP Server initialized")
    
    def register_tool(self, name: str, function: Callable, description: str, 
                     parameters: Dict[str, Any] = None) -> None:
        """
        Register a tool with the server.
        
        Args:
            name: Tool name
            function: Tool function to call
            description: Tool description
            parameters: Tool parameter schema
        """
        if parameters is None:
            parameters = {}
            
        self.tools[name] = function
        self.tool_schemas[name] = ToolInfo(
            name=name,
            description=description,
            parameters=parameters
        )
        
        self.logger.debug(f"Registered tool: {name}")
    
    def handle_message(self, raw_message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an incoming MCP message.
        
        Args:
            raw_message: Raw message dictionary
            
        Returns:
            Response message dictionary
        """
        try:
            # Parse the message
            message = parse_message(raw_message)
            message_id = message.id
            
            self.logger.debug(f"Handling message type: {message.type}")
            
            # Route message to appropriate handler
            if message.type == MessageType.PING:
                response = self._handle_ping(message)
            elif message.type == MessageType.INITIALIZE:
                response = self._handle_initialize(message)
            elif message.type == MessageType.LIST_TOOLS:
                response = self._handle_list_tools(message)
            elif message.type == MessageType.CALL_TOOL:
                response = self._handle_call_tool(message)
            else:
                response = create_error_message(
                    f"Unknown message type: {message.type}",
                    code=400,
                    message_id=message_id
                )
            
            # Ensure response has the same ID as the request
            if message_id and hasattr(response, 'id'):
                response.id = message_id
            
            return response.model_dump()
            
        except ValueError as e:
            self.logger.error(f"Message parsing error: {e}")
            return create_error_message(
                f"Message parsing error: {str(e)}",
                code=400
            ).model_dump()
        except Exception as e:
            self.logger.error(f"Unexpected error handling message: {e}")
            return create_error_message(
                f"Internal server error: {str(e)}",
                code=500
            ).dict()
    
    def _handle_ping(self, message: PingMessage) -> PongMessage:
        """Handle ping message."""
        self.logger.debug("Handling ping message")
        return PongMessage(id=message.id)
    
    def _handle_initialize(self, message: InitializeMessage) -> InitializedMessage:
        """Handle initialize message."""
        self.logger.debug("Handling initialize message")
        
        # Mark server as initialized
        self.initialized = True
        
        # Prepare initialization response
        result = {
            "server": self.server_info,
            "capabilities": {
                "tools": True,
                "resources": False,  # Will be implemented in later tasks
                "prompts": False     # Will be implemented in later tasks
            },
            "initialized_at": datetime.now().isoformat()
        }
        
        self.logger.info("Server initialized successfully")
        return InitializedMessage(id=message.id, result=result)
    
    def _handle_list_tools(self, message: ListToolsMessage) -> ListToolsResponse:
        """Handle list tools message."""
        self.logger.debug("Handling list_tools message")
        
        if not self.initialized:
            raise ValueError("Server not initialized")
        
        tools_list = list(self.tool_schemas.values())
        result = {"tools": [tool.model_dump() for tool in tools_list]}
        
        self.logger.debug(f"Returning {len(tools_list)} tools")
        return ListToolsResponse(id=message.id, result=result)
    
    def _handle_call_tool(self, message: CallToolMessage) -> CallToolResponse:
        """Handle call tool message."""
        self.logger.debug("Handling call_tool message")
        
        if not self.initialized:
            raise ValueError("Server not initialized")
        
        tool_name = message.params.get('name')
        tool_args = message.params.get('arguments', {})
        
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        try:
            # Call the tool function
            tool_function = self.tools[tool_name]
            result = tool_function(**tool_args)
            
            self.logger.debug(f"Tool {tool_name} executed successfully")
            return CallToolResponse(
                id=message.id,
                result={"content": result}
            )
            
        except Exception as e:
            self.logger.error(f"Tool execution error: {e}")
            raise ValueError(f"Tool execution failed: {str(e)}")
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information."""
        return {
            "server": self.server_info,
            "initialized": self.initialized,
            "tools_count": len(self.tools),
            "resources_count": len(self.resources),
            "prompts_count": len(self.prompts)
        }
