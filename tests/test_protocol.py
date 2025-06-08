"""
Test MCP Protocol Implementation
"""

import pytest
import json
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_server.server import MCPServer
from mcp_server.protocol import MCPProtocolHandler, create_protocol_handler
from mcp_server.messages import MessageType, parse_message, create_error_message


class TestMCPMessages:
    """Test MCP message parsing and validation."""
    
    def test_parse_ping_message(self):
        """Test parsing ping message."""
        data = {"type": "ping", "id": "test_1"}
        message = parse_message(data)
        assert message.type == MessageType.PING
        assert message.id == "test_1"
    
    def test_parse_initialize_message(self):
        """Test parsing initialize message."""
        data = {
            "type": "initialize",
            "id": "init_1",
            "params": {"client": "test_client"}
        }
        message = parse_message(data)
        assert message.type == MessageType.INITIALIZE
        assert message.params["client"] == "test_client"
    
    def test_parse_invalid_message(self):
        """Test parsing invalid message."""
        data = {"type": "invalid_type"}
        with pytest.raises(ValueError):
            parse_message(data)
    
    def test_create_error_message(self):
        """Test creating error message."""
        error_msg = create_error_message("Test error", code=400, message_id="err_1")
        assert error_msg.type == MessageType.ERROR
        assert error_msg.error == "Test error"
        assert error_msg.code == 400
        assert error_msg.id == "err_1"


class TestMCPServer:
    """Test MCP server functionality."""
    
    def setup_method(self):
        """Setup test server."""
        self.server = MCPServer(debug=True)
    
    def test_server_initialization(self):
        """Test server initialization."""
        assert not self.server.initialized
        assert len(self.server.tools) == 0
        assert self.server.server_info["name"] == "MCP Learning Server"
    
    def test_ping_pong(self):
        """Test ping/pong mechanism."""
        ping_data = {"type": "ping", "id": "ping_1"}
        response = self.server.handle_message(ping_data)
        
        assert response["type"] == "pong"
        assert response["id"] == "ping_1"
    
    def test_initialize_server(self):
        """Test server initialization."""
        init_data = {
            "type": "initialize",
            "id": "init_1",
            "params": {"client": "test_client"}
        }
        response = self.server.handle_message(init_data)
        
        assert response["type"] == "initialized"
        assert response["id"] == "init_1"
        assert "server" in response["result"]
        assert self.server.initialized
    
    def test_list_tools_before_init(self):
        """Test listing tools before initialization."""
        list_data = {"type": "list_tools", "id": "list_1"}
        response = self.server.handle_message(list_data)
        
        assert response["type"] == "error"
        assert "not initialized" in response["error"]
    
    def test_list_tools_after_init(self):
        """Test listing tools after initialization."""
        # Initialize server first
        init_data = {"type": "initialize", "id": "init_1"}
        self.server.handle_message(init_data)
        
        # List tools
        list_data = {"type": "list_tools", "id": "list_1"}
        response = self.server.handle_message(list_data)
        
        assert response["type"] == "list_tools"
        assert "tools" in response["result"]
        assert isinstance(response["result"]["tools"], list)
    
    def test_register_and_call_tool(self):
        """Test tool registration and calling."""
        # Register a simple tool
        def echo_tool(message: str) -> str:
            return f"Echo: {message}"
        
        self.server.register_tool(
            "echo",
            echo_tool,
            "Echo back the input message",
            {"message": {"type": "string"}}
        )
        
        # Initialize server
        init_data = {"type": "initialize", "id": "init_1"}
        self.server.handle_message(init_data)
        
        # Call the tool
        call_data = {
            "type": "call_tool",
            "id": "call_1",
            "params": {
                "name": "echo",
                "arguments": {"message": "Hello World"}
            }
        }
        response = self.server.handle_message(call_data)
        
        assert response["type"] == "call_tool"
        assert response["result"]["content"] == "Echo: Hello World"
    
    def test_call_unknown_tool(self):
        """Test calling unknown tool."""
        # Initialize server
        init_data = {"type": "initialize", "id": "init_1"}
        self.server.handle_message(init_data)
        
        # Call unknown tool
        call_data = {
            "type": "call_tool",
            "id": "call_1",
            "params": {
                "name": "unknown_tool",
                "arguments": {}
            }
        }
        response = self.server.handle_message(call_data)
        
        assert response["type"] == "error"
        assert "Unknown tool" in response["error"]
    
    def test_malformed_message(self):
        """Test handling malformed message."""
        malformed_data = {"invalid": "message"}
        response = self.server.handle_message(malformed_data)
        
        assert response["type"] == "error"
        assert "parsing error" in response["error"].lower()


class TestMCPProtocolHandler:
    """Test MCP protocol handler."""
    
    def setup_method(self):
        """Setup test protocol handler."""
        self.handler = create_protocol_handler(debug=True)
    
    def test_json_message_handling(self):
        """Test JSON message handling."""
        ping_json = json.dumps({"type": "ping", "id": "ping_1"})
        response_json = self.handler.handle_json_message(ping_json)
        response = json.loads(response_json)
        
        assert response["type"] == "pong"
        assert response["id"] == "ping_1"
    
    def test_invalid_json(self):
        """Test handling invalid JSON."""
        invalid_json = "{'invalid': json}"
        response_json = self.handler.handle_json_message(invalid_json)
        response = json.loads(response_json)
        
        assert response["type"] == "error"
        assert "Invalid JSON" in response["error"]
    
    def test_ping_method(self):
        """Test ping method."""
        assert self.handler.ping()
    
    def test_server_info(self):
        """Test getting server info."""
        info = self.handler.get_server_info()
        assert "server" in info
        assert "initialized" in info
        assert "tools_count" in info


class TestToolRegistration:
    """Test tool registration functionality."""
    
    def setup_method(self):
        """Setup test server."""
        self.server = MCPServer()
    
    def test_register_simple_tool(self):
        """Test registering a simple tool."""
        def add_numbers(a: int, b: int) -> int:
            return a + b
        
        self.server.register_tool(
            "add",
            add_numbers,
            "Add two numbers",
            {
                "a": {"type": "integer"},
                "b": {"type": "integer"}
            }
        )
        
        assert "add" in self.server.tools
        assert "add" in self.server.tool_schemas
        assert self.server.tool_schemas["add"].name == "add"
    
    def test_tool_execution_with_error(self):
        """Test tool execution that raises an error."""
        def error_tool():
            raise ValueError("Tool error")
        
        self.server.register_tool("error_tool", error_tool, "Tool that errors")
        
        # Initialize server
        init_data = {"type": "initialize", "id": "init_1"}
        self.server.handle_message(init_data)
        
        # Call the error tool
        call_data = {
            "type": "call_tool",
            "id": "call_1",
            "params": {
                "name": "error_tool",
                "arguments": {}
            }
        }
        response = self.server.handle_message(call_data)
        
        assert response["type"] == "error"
        assert "Tool execution failed" in response["error"]
