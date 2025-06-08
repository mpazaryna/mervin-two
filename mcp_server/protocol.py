"""
MCP Protocol Handler

This module provides a high-level protocol handler that wraps the core server
and provides additional protocol-level functionality.
"""

import json
import logging
from typing import Any, Dict, Optional, Callable

from .server import MCPServer
from .logging_config import get_logger


class MCPProtocolHandler:
    """
    High-level MCP protocol handler.
    
    Provides JSON message parsing, validation, and response formatting
    on top of the core MCPServer functionality.
    """
    
    def __init__(self, server: Optional[MCPServer] = None, debug: bool = False,
                 resource_dir: str = "./resources", prompt_dir: str = "./prompts"):
        """
        Initialize the protocol handler.

        Args:
            server: Optional MCPServer instance (creates new one if None)
            debug: Enable debug mode
            resource_dir: Directory containing resources
            prompt_dir: Directory containing prompt templates
        """
        self.server = server or MCPServer(debug=debug, resource_dir=resource_dir, prompt_dir=prompt_dir)
        self.debug = debug
        self.logger = get_logger("mcp_protocol")

        if debug:
            self.logger.setLevel(logging.DEBUG)

        self.logger.info("MCP Protocol Handler initialized")
    
    def handle_json_message(self, json_message: str) -> str:
        """
        Handle a JSON-encoded MCP message.
        
        Args:
            json_message: JSON string containing the message
            
        Returns:
            JSON string containing the response
        """
        try:
            # Parse JSON
            message_data = json.loads(json_message)
            self.logger.debug(f"Received message: {message_data}")
            
            # Handle the message
            response_data = self.server.handle_message(message_data)
            
            # Convert response to JSON
            response_json = json.dumps(response_data)
            self.logger.debug(f"Sending response: {response_data}")
            
            return response_json
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error: {e}")
            error_response = {
                "type": "error",
                "error": f"Invalid JSON: {str(e)}",
                "code": 400
            }
            return json.dumps(error_response)
        
        except Exception as e:
            self.logger.error(f"Unexpected error in protocol handler: {e}")
            error_response = {
                "type": "error",
                "error": f"Protocol error: {str(e)}",
                "code": 500
            }
            return json.dumps(error_response)
    
    def handle_message_dict(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a message dictionary directly.
        
        Args:
            message_data: Message dictionary
            
        Returns:
            Response dictionary
        """
        return self.server.handle_message(message_data)
    
    def register_tool(self, name: str, function: Callable, description: str,
                     parameters: Dict[str, Any] = None) -> None:
        """
        Register a tool with the underlying server.
        
        Args:
            name: Tool name
            function: Tool function
            description: Tool description
            parameters: Tool parameter schema
        """
        self.server.register_tool(name, function, description, parameters)
    
    def is_initialized(self) -> bool:
        """Check if the server is initialized."""
        return self.server.initialized
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information."""
        return self.server.get_server_info()
    
    def ping(self) -> bool:
        """
        Send a ping to test the server.
        
        Returns:
            True if ping successful, False otherwise
        """
        try:
            ping_message = {"type": "ping", "id": "test_ping"}
            response = self.handle_message_dict(ping_message)
            return response.get("type") == "pong"
        except Exception:
            return False


def create_protocol_handler(debug: bool = False, resource_dir: str = "./resources",
                           prompt_dir: str = "./prompts") -> MCPProtocolHandler:
    """
    Factory function to create a protocol handler.

    Args:
        debug: Enable debug mode
        resource_dir: Directory containing resources
        prompt_dir: Directory containing prompt templates

    Returns:
        Configured protocol handler
    """
    return MCPProtocolHandler(debug=debug, resource_dir=resource_dir, prompt_dir=prompt_dir)
