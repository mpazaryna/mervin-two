"""
Tool Integration Module

This module provides integration between the tool registry and the MCP server,
allowing tools to be automatically registered and executed through the MCP protocol.
"""

from typing import Dict, Any, List
from mcp_server.protocol import MCPProtocolHandler
from mcp_server.logging_config import get_logger

from .registry import registry


class ToolIntegrator:
    """
    Integrates tools with MCP protocol handler.
    
    Automatically registers tools from the registry with the MCP server
    and provides tool execution capabilities.
    """
    
    def __init__(self, protocol_handler: MCPProtocolHandler):
        """
        Initialize the tool integrator.
        
        Args:
            protocol_handler: MCP protocol handler to integrate with
        """
        self.protocol_handler = protocol_handler
        self.logger = get_logger("tool_integrator")
        self.registered_tools: Dict[str, str] = {}  # tool_name -> registry_name mapping
        
        self.logger.info("Tool integrator initialized")
    
    def register_all_tools(self):
        """Register all tools from the registry with the MCP server."""
        tools = registry.list_tools()
        
        for tool_info in tools:
            self._register_single_tool(tool_info)
        
        self.logger.info(f"Registered {len(tools)} tools with MCP server")
    
    def register_tools_by_category(self, category: str):
        """
        Register tools from a specific category.
        
        Args:
            category: Category name to register
        """
        categories = registry.list_categories()
        if category not in categories:
            self.logger.warning(f"Category not found: {category}")
            return
        
        tool_names = categories[category]
        registered_count = 0
        
        for tool_name in tool_names:
            tool_def = registry.get_tool(tool_name)
            if tool_def:
                tool_info = {
                    "name": tool_def.name,
                    "description": tool_def.description,
                    "parameters": tool_def.parameter_schema,
                    "category": tool_def.category,
                    "examples": tool_def.examples
                }
                self._register_single_tool(tool_info)
                registered_count += 1
        
        self.logger.info(f"Registered {registered_count} tools from category: {category}")
    
    def _register_single_tool(self, tool_info: Dict[str, Any]):
        """
        Register a single tool with the MCP server.
        
        Args:
            tool_info: Tool information dictionary
        """
        tool_name = tool_info["name"]
        
        # Create wrapper function for MCP execution
        def tool_wrapper(**kwargs) -> Any:
            return self._execute_tool(tool_name, kwargs)
        
        # Register with MCP protocol handler
        self.protocol_handler.register_tool(
            name=tool_name,
            function=tool_wrapper,
            description=tool_info["description"],
            parameters=tool_info["parameters"]
        )
        
        # Track registration
        self.registered_tools[tool_name] = tool_name
        
        self.logger.debug(f"Registered tool: {tool_name}")
    
    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute a tool through the registry.
        
        Args:
            tool_name: Name of tool to execute
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        try:
            result = registry.execute_tool(tool_name, arguments)
            self.logger.debug(f"Tool {tool_name} executed successfully")
            return result
        except Exception as e:
            self.logger.error(f"Tool {tool_name} execution failed: {e}")
            raise
    
    def get_registered_tools(self) -> List[str]:
        """Get list of registered tool names."""
        return list(self.registered_tools.keys())
    
    def get_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """
        Get information about a registered tool.
        
        Args:
            tool_name: Name of tool
            
        Returns:
            Tool information dictionary
        """
        if tool_name not in self.registered_tools:
            return {}
        
        tool_def = registry.get_tool(tool_name)
        if not tool_def:
            return {}
        
        return {
            "name": tool_def.name,
            "description": tool_def.description,
            "parameters": tool_def.parameter_schema,
            "return_schema": tool_def.return_schema,
            "examples": tool_def.examples,
            "category": tool_def.category,
            "help": registry.get_tool_help(tool_name)
        }
    
    def get_categories_summary(self) -> Dict[str, Dict[str, Any]]:
        """
        Get summary of tools by category.
        
        Returns:
            Dictionary with category information
        """
        categories = registry.list_categories()
        summary = {}
        
        for category, tool_names in categories.items():
            registered_tools = [name for name in tool_names if name in self.registered_tools]
            summary[category] = {
                "total_tools": len(tool_names),
                "registered_tools": len(registered_tools),
                "tools": registered_tools
            }
        
        return summary


def setup_tools(protocol_handler: MCPProtocolHandler, 
               categories: List[str] = None) -> ToolIntegrator:
    """
    Setup tools with MCP protocol handler.
    
    Args:
        protocol_handler: MCP protocol handler
        categories: List of categories to register (None for all)
        
    Returns:
        Configured tool integrator
    """
    # Import all tool modules to trigger registration
    import tools.calculator
    import tools.utilities
    
    # Create integrator
    integrator = ToolIntegrator(protocol_handler)
    
    # Register tools
    if categories is None:
        integrator.register_all_tools()
    else:
        for category in categories:
            integrator.register_tools_by_category(category)
    
    return integrator


def create_tool_info_tool(integrator: ToolIntegrator) -> None:
    """
    Create a meta-tool that provides information about available tools.
    
    Args:
        integrator: Tool integrator instance
    """
    def tool_info(tool_name: str = None, category: str = None) -> Dict[str, Any]:
        """
        Get information about available tools.
        
        Args:
            tool_name: Specific tool to get info for
            category: Category to list tools for
            
        Returns:
            Tool information
        """
        if tool_name:
            return integrator.get_tool_info(tool_name)
        elif category:
            categories = integrator.get_categories_summary()
            return categories.get(category, {})
        else:
            return {
                "registered_tools": integrator.get_registered_tools(),
                "categories": integrator.get_categories_summary(),
                "total_tools": len(integrator.get_registered_tools())
            }
    
    # Register the meta-tool
    integrator.protocol_handler.register_tool(
        name="tool_info",
        function=tool_info,
        description="Get information about available tools and categories",
        parameters={
            "type": "object",
            "properties": {
                "tool_name": {
                    "type": "string",
                    "description": "Specific tool to get information for"
                },
                "category": {
                    "type": "string",
                    "description": "Category to list tools for"
                }
            }
        }
    )
