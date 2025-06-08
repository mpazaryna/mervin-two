"""
Tool Registry and Registration System

This module provides the tool registration system and decorators
for creating MCP tools in a clean and organized way.
"""

import functools
import inspect
from typing import Any, Dict, List, Callable, Optional, Union
from dataclasses import dataclass

from mcp_server.logging_config import get_logger


@dataclass
class ToolDefinition:
    """Definition of a tool with its metadata."""
    name: str
    function: Callable
    description: str
    parameter_schema: Dict[str, Any]
    return_schema: Dict[str, Any]
    examples: List[Dict[str, Any]]
    category: str


class ToolRegistry:
    """
    Registry for managing MCP tools.
    
    Provides registration, discovery, and execution of tools
    with proper validation and error handling.
    """
    
    def __init__(self):
        """Initialize the tool registry."""
        self.tools: Dict[str, ToolDefinition] = {}
        self.categories: Dict[str, List[str]] = {}
        self.logger = get_logger("tool_registry")
        
        self.logger.info("Tool registry initialized")
    
    def register(self, 
                name: str,
                description: str,
                parameter_schema: Optional[Dict[str, Any]] = None,
                return_schema: Optional[Dict[str, Any]] = None,
                examples: Optional[List[Dict[str, Any]]] = None,
                category: str = "general") -> Callable:
        """
        Decorator to register a tool.
        
        Args:
            name: Tool name
            description: Tool description
            parameter_schema: JSON schema for parameters
            return_schema: JSON schema for return value
            examples: Example usage
            category: Tool category
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            # Generate parameter schema from function signature if not provided
            if parameter_schema is None:
                generated_schema = self._generate_parameter_schema(func)
            else:
                generated_schema = parameter_schema
            
            # Create tool definition
            tool_def = ToolDefinition(
                name=name,
                function=func,
                description=description,
                parameter_schema=generated_schema,
                return_schema=return_schema or {"type": "any"},
                examples=examples or [],
                category=category
            )
            
            # Register the tool
            self.tools[name] = tool_def
            
            # Add to category
            if category not in self.categories:
                self.categories[category] = []
            self.categories[category].append(name)
            
            self.logger.info(f"Registered tool: {name} in category: {category}")
            
            return func
        
        return decorator
    
    def _generate_parameter_schema(self, func: Callable) -> Dict[str, Any]:
        """
        Generate parameter schema from function signature.
        
        Args:
            func: Function to analyze
            
        Returns:
            JSON schema for parameters
        """
        sig = inspect.signature(func)
        properties = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            # Skip self parameter
            if param_name == 'self':
                continue
            
            # Determine type from annotation
            param_type = "string"  # default
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_type = "integer"
                elif param.annotation == float:
                    param_type = "number"
                elif param.annotation == bool:
                    param_type = "boolean"
                elif param.annotation == str:
                    param_type = "string"
            
            properties[param_name] = {"type": param_type}
            
            # Add to required if no default value
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
        
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool by name."""
        return self.tools.get(name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameter_schema,
                "category": tool.category,
                "examples": tool.examples
            }
            for tool in self.tools.values()
        ]
    
    def list_categories(self) -> Dict[str, List[str]]:
        """List tools by category."""
        return self.categories.copy()
    
    def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute a tool with given arguments.
        
        Args:
            name: Tool name
            arguments: Tool arguments
            
        Returns:
            Tool result
            
        Raises:
            ValueError: If tool not found or execution fails
        """
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")
        
        try:
            # Validate arguments against schema
            self._validate_arguments(tool, arguments)
            
            # Execute the tool
            result = tool.function(**arguments)
            
            self.logger.debug(f"Tool {name} executed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Tool {name} execution failed: {e}")
            raise ValueError(f"Tool execution failed: {str(e)}")
    
    def _validate_arguments(self, tool: ToolDefinition, arguments: Dict[str, Any]):
        """
        Validate arguments against tool schema.
        
        Args:
            tool: Tool definition
            arguments: Arguments to validate
            
        Raises:
            ValueError: If validation fails
        """
        schema = tool.parameter_schema
        
        # Check required parameters
        required = schema.get("required", [])
        for param in required:
            if param not in arguments:
                raise ValueError(f"Missing required parameter: {param}")
        
        # Basic type checking
        properties = schema.get("properties", {})
        for param, value in arguments.items():
            if param in properties:
                expected_type = properties[param].get("type")
                if not self._check_type(value, expected_type):
                    raise ValueError(f"Parameter {param} has wrong type. Expected {expected_type}")
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type."""
        if expected_type == "string":
            return isinstance(value, str)
        elif expected_type == "integer":
            return isinstance(value, int)
        elif expected_type == "number":
            return isinstance(value, (int, float))
        elif expected_type == "boolean":
            return isinstance(value, bool)
        elif expected_type == "any":
            return True
        return True  # Default to true for unknown types
    
    def get_tool_help(self, name: str) -> Optional[str]:
        """Get help text for a tool."""
        tool = self.get_tool(name)
        if not tool:
            return None
        
        help_text = f"Tool: {tool.name}\n"
        help_text += f"Description: {tool.description}\n"
        help_text += f"Category: {tool.category}\n\n"
        
        # Parameters
        if tool.parameter_schema.get("properties"):
            help_text += "Parameters:\n"
            for param, schema in tool.parameter_schema["properties"].items():
                param_type = schema.get("type", "any")
                required = param in tool.parameter_schema.get("required", [])
                req_text = " (required)" if required else " (optional)"
                help_text += f"  - {param}: {param_type}{req_text}\n"
        
        # Examples
        if tool.examples:
            help_text += "\nExamples:\n"
            for i, example in enumerate(tool.examples, 1):
                help_text += f"  {i}. {example}\n"
        
        return help_text


# Global registry instance
registry = ToolRegistry()

# Convenience decorator
def tool(name: str, 
         description: str,
         parameter_schema: Optional[Dict[str, Any]] = None,
         return_schema: Optional[Dict[str, Any]] = None,
         examples: Optional[List[Dict[str, Any]]] = None,
         category: str = "general") -> Callable:
    """
    Convenience decorator for tool registration.
    
    Args:
        name: Tool name
        description: Tool description
        parameter_schema: JSON schema for parameters
        return_schema: JSON schema for return value
        examples: Example usage
        category: Tool category
        
    Returns:
        Decorator function
    """
    return registry.register(name, description, parameter_schema, return_schema, examples, category)
