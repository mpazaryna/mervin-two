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
    ListResourcesMessage, ListResourcesResponse, ReadResourceMessage, ReadResourceResponse,
    ListPromptsMessage, ListPromptsResponse, GetPromptMessage, GetPromptResponse,
    ToolInfo, ResourceInfo, PromptInfo, ErrorMessage
)
from .logging_config import get_logger
from .resources import ResourceManager
from .prompts import PromptManager


class MCPServer:
    """
    Core MCP server implementation.
    
    Handles MCP protocol messages, manages tools, resources, and prompts,
    and provides the main message processing interface.
    """
    
    def __init__(self, debug: bool = False, resource_dir: str = "./resources",
                 prompt_dir: str = "./prompts", metrics=None):
        """
        Initialize the MCP server.

        Args:
            debug: Enable debug mode for verbose logging
            resource_dir: Directory containing resources
            prompt_dir: Directory containing prompt templates
            metrics: Optional metrics collection instance
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

        # Tool registry
        self.tools: Dict[str, Callable] = {}
        self.tool_schemas: Dict[str, ToolInfo] = {}

        # Initialize resource and prompt managers
        self.resource_manager = ResourceManager(resource_dir)
        self.prompt_manager = PromptManager(prompt_dir)

        # Optional metrics collection
        self.metrics = metrics

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
        message_type = raw_message.get("type", "unknown")
        message_id = raw_message.get("id", "unknown")

        # Start metrics tracking if available
        if self.metrics:
            self.metrics.start_request(message_id, message_type)

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
            elif message.type == MessageType.LIST_RESOURCES:
                response = self._handle_list_resources(message)
            elif message.type == MessageType.READ_RESOURCE:
                response = self._handle_read_resource(message)
            elif message.type == MessageType.LIST_PROMPTS:
                response = self._handle_list_prompts(message)
            elif message.type == MessageType.GET_PROMPT:
                response = self._handle_get_prompt(message)
            else:
                response = create_error_message(
                    f"Unknown message type: {message.type}",
                    code=400,
                    message_id=message_id
                )

            # Ensure response has the same ID as the request
            if message_id and hasattr(response, 'id'):
                response.id = message_id

            # End metrics tracking (success)
            if self.metrics:
                self.metrics.end_request(message_id, success=True)

            return response.model_dump()

        except ValueError as e:
            self.logger.error(f"Message parsing error: {e}")

            # End metrics tracking (failure)
            if self.metrics:
                self.metrics.end_request(message_id, success=False)
                self.metrics.record_error("ValueError", message_type)

            return create_error_message(
                f"Message parsing error: {str(e)}",
                code=400
            ).model_dump()
        except Exception as e:
            self.logger.error(f"Unexpected error handling message: {e}")

            # End metrics tracking (failure)
            if self.metrics:
                self.metrics.end_request(message_id, success=False)
                self.metrics.record_error(type(e).__name__, message_type)

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
                "resources": True,   # Implemented in Task 6
                "prompts": True      # Now implemented in Task 7!
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

        import time
        start_time = time.time()

        try:
            # Call the tool function
            tool_function = self.tools[tool_name]
            result = tool_function(**tool_args)

            # Record metrics
            if self.metrics:
                response_time = time.time() - start_time
                self.metrics.record_tool_call(tool_name, response_time, success=True)

            self.logger.debug(f"Tool {tool_name} executed successfully")
            return CallToolResponse(
                id=message.id,
                result={"content": result}
            )

        except Exception as e:
            # Record metrics for failed tool call
            if self.metrics:
                response_time = time.time() - start_time
                self.metrics.record_tool_call(tool_name, response_time, success=False)

            self.logger.error(f"Tool execution error: {e}")
            raise ValueError(f"Tool execution failed: {str(e)}")

    def _handle_list_resources(self, message: ListResourcesMessage) -> ListResourcesResponse:
        """Handle list resources message."""
        self.logger.debug("Handling list_resources message")

        if not self.initialized:
            raise ValueError("Server not initialized")

        try:
            resources_list = self.resource_manager.list_resources()
            result = {"resources": resources_list}

            self.logger.debug(f"Returning {len(resources_list)} resources")
            return ListResourcesResponse(id=message.id, result=result)

        except Exception as e:
            self.logger.error(f"Error listing resources: {e}")
            raise ValueError(f"Failed to list resources: {str(e)}")

    def _handle_read_resource(self, message: ReadResourceMessage) -> ReadResourceResponse:
        """Handle read resource message."""
        self.logger.debug("Handling read_resource message")

        if not self.initialized:
            raise ValueError("Server not initialized")

        resource_id = message.params.get('id')
        if not resource_id:
            raise ValueError("Resource ID is required")

        try:
            # Check if resource is cached
            cache_hit = resource_id in self.resource_manager.cache

            # Get resource content
            content = self.resource_manager.get_resource(resource_id)

            # Record metrics
            if self.metrics:
                self.metrics.record_resource_request(resource_id, cache_hit)

            # Get resource info for metadata
            resource_info = self.resource_manager.get_resource_info(resource_id)

            result = {
                "content": content,
                "metadata": {
                    "id": resource_info.resource_id,
                    "title": resource_info.title,
                    "description": resource_info.description,
                    "mime_type": resource_info.mime_type,
                    "tags": resource_info.tags
                }
            }

            self.logger.debug(f"Resource {resource_id} read successfully")
            return ReadResourceResponse(id=message.id, result=result)

        except Exception as e:
            self.logger.error(f"Error reading resource {resource_id}: {e}")
            raise ValueError(f"Failed to read resource {resource_id}: {str(e)}")

    def _handle_list_prompts(self, message: ListPromptsMessage) -> ListPromptsResponse:
        """Handle list prompts message."""
        self.logger.debug("Handling list_prompts message")

        if not self.initialized:
            raise ValueError("Server not initialized")

        try:
            prompts_list = self.prompt_manager.list_prompts()
            result = {"prompts": prompts_list}

            self.logger.debug(f"Returning {len(prompts_list)} prompts")
            return ListPromptsResponse(id=message.id, result=result)

        except Exception as e:
            self.logger.error(f"Error listing prompts: {e}")
            raise ValueError(f"Failed to list prompts: {str(e)}")

    def _handle_get_prompt(self, message: GetPromptMessage) -> GetPromptResponse:
        """Handle get prompt message."""
        self.logger.debug("Handling get_prompt message")

        if not self.initialized:
            raise ValueError("Server not initialized")

        prompt_id = message.params.get('id')
        arguments = message.params.get('arguments', {})

        if not prompt_id:
            raise ValueError("Prompt ID is required")

        import time
        start_time = time.time()

        try:
            # Validate arguments if provided
            if arguments:
                validation_errors = self.prompt_manager.validate_prompt_arguments(prompt_id, arguments)
                if validation_errors:
                    raise ValueError(f"Invalid arguments: {'; '.join(validation_errors)}")

            # Get rendered prompt
            rendered_prompt = self.prompt_manager.get_prompt(prompt_id, arguments)

            # Record metrics
            if self.metrics:
                render_time = time.time() - start_time
                self.metrics.record_prompt_request(prompt_id, render_time)

            # Get prompt info for metadata
            prompt_info = self.prompt_manager.get_prompt_info(prompt_id)

            result = {
                "content": rendered_prompt,
                "metadata": {
                    "id": prompt_info.prompt_id,
                    "title": prompt_info.title,
                    "description": prompt_info.description,
                    "parameters": prompt_info.parameters,
                    "examples": prompt_info.examples,
                    "tags": prompt_info.tags
                }
            }

            self.logger.debug(f"Prompt {prompt_id} rendered successfully")
            return GetPromptResponse(id=message.id, result=result)

        except Exception as e:
            self.logger.error(f"Error getting prompt {prompt_id}: {e}")
            raise ValueError(f"Failed to get prompt {prompt_id}: {str(e)}")

    def get_server_info(self) -> Dict[str, Any]:
        """Get server information."""
        return {
            "server": self.server_info,
            "initialized": self.initialized,
            "tools_count": len(self.tools),
            "resources_count": len(self.resource_manager.resources),
            "prompts_count": len(self.prompt_manager.prompts),
            "resource_cache_stats": self.resource_manager.get_cache_stats()
        }
