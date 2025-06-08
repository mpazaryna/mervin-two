"""
Test Stdio Transport Implementation
"""

import pytest
import json
import sys
import os
import threading
import time
from io import StringIO
from unittest.mock import patch, MagicMock

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_server.stdio_transport import StdioTransport, SimpleStdioTransport
from mcp_server.protocol import MCPProtocolHandler


class TestStdioTransport:
    """Test the threaded stdio transport implementation."""
    
    def setup_method(self):
        """Setup test transport."""
        self.handler = MCPProtocolHandler(debug=True)
        self.transport = StdioTransport(self.handler.handle_message_dict)
    
    def test_transport_initialization(self):
        """Test transport initialization."""
        assert not self.transport.running
        assert not self.transport.shutdown_requested
        assert self.transport.input_queue.qsize() == 0
        assert self.transport.output_queue.qsize() == 0
    
    def test_signal_handlers_setup(self):
        """Test that signal handlers are properly set up."""
        # This is hard to test directly, but we can verify the transport
        # has the signal handling method
        assert hasattr(self.transport, '_setup_signal_handlers')
    
    def test_send_message(self):
        """Test sending a message through the transport."""
        test_message = {"type": "ping", "id": "test_1"}
        self.transport.send_message(test_message)
        
        # Check that message was queued
        assert self.transport.output_queue.qsize() == 1
        
        # Get the queued message
        queued_message = self.transport.output_queue.get()
        parsed_message = json.loads(queued_message)
        
        assert parsed_message["type"] == "ping"
        assert parsed_message["id"] == "test_1"
    
    def test_process_message(self):
        """Test message processing."""
        ping_message = '{"type": "ping", "id": "test_ping"}'
        
        # Process the message
        self.transport._process_message(ping_message)
        
        # Check that response was queued
        assert self.transport.output_queue.qsize() == 1
        
        # Get and verify response
        response_json = self.transport.output_queue.get()
        response = json.loads(response_json)
        
        assert response["type"] == "pong"
        assert response["id"] == "test_ping"
    
    def test_process_invalid_json(self):
        """Test processing invalid JSON."""
        invalid_message = '{"invalid": json}'
        
        # Process the invalid message
        self.transport._process_message(invalid_message)
        
        # Check that error response was queued
        assert self.transport.output_queue.qsize() == 1
        
        # Get and verify error response
        response_json = self.transport.output_queue.get()
        response = json.loads(response_json)
        
        assert response["type"] == "error"
        assert "Invalid JSON" in response["error"]
        assert response["code"] == 400
    
    def test_get_stats(self):
        """Test getting transport statistics."""
        stats = self.transport.get_stats()
        
        assert "running" in stats
        assert "shutdown_requested" in stats
        assert "input_queue_size" in stats
        assert "output_queue_size" in stats
        assert "threads_alive" in stats
        
        assert stats["running"] == False
        assert stats["shutdown_requested"] == False
        assert stats["input_queue_size"] == 0
        assert stats["output_queue_size"] == 0
    
    def test_is_running(self):
        """Test is_running method."""
        assert not self.transport.is_running()
        
        # Simulate running state
        self.transport.running = True
        assert self.transport.is_running()
        
        # Simulate shutdown requested
        self.transport.shutdown_requested = True
        assert not self.transport.is_running()


class TestSimpleStdioTransport:
    """Test the simple stdio transport implementation."""
    
    def setup_method(self):
        """Setup test transport."""
        self.handler = MCPProtocolHandler(debug=True)
        self.transport = SimpleStdioTransport(self.handler.handle_message_dict)
    
    def test_simple_transport_initialization(self):
        """Test simple transport initialization."""
        assert not self.transport.running
        assert hasattr(self.transport, 'message_handler')
        assert hasattr(self.transport, 'logger')
    
    @patch('sys.stdin')
    @patch('sys.stdout')
    def test_simple_transport_message_handling(self, mock_stdout, mock_stdin):
        """Test simple transport message handling."""
        # Setup mock stdin to return a ping message then EOF
        ping_message = '{"type": "ping", "id": "test_1"}\n'
        mock_stdin.readline.side_effect = [ping_message, '']  # EOF after first message
        
        # Setup mock stdout
        mock_stdout.write = MagicMock()
        mock_stdout.flush = MagicMock()
        
        # Start transport (should process one message then stop)
        self.transport.start()
        
        # Verify stdout was called with pong response
        assert mock_stdout.write.called
        written_data = mock_stdout.write.call_args[0][0]
        
        # Parse the response (remove newline)
        response = json.loads(written_data.strip())
        assert response["type"] == "pong"
        assert response["id"] == "test_1"
    
    @patch('sys.stdin')
    @patch('sys.stdout')
    def test_simple_transport_invalid_json(self, mock_stdout, mock_stdin):
        """Test simple transport handling of invalid JSON."""
        # Setup mock stdin with invalid JSON then EOF
        invalid_message = '{"invalid": json}\n'
        mock_stdin.readline.side_effect = [invalid_message, '']
        
        # Setup mock stdout
        mock_stdout.write = MagicMock()
        mock_stdout.flush = MagicMock()
        
        # Start transport
        self.transport.start()
        
        # Verify error response was written
        assert mock_stdout.write.called
        written_data = mock_stdout.write.call_args[0][0]
        
        # Parse the error response
        response = json.loads(written_data.strip())
        assert response["type"] == "error"
        assert "Invalid JSON" in response["error"]
        assert response["code"] == 400
    
    @patch('sys.stdin')
    @patch('sys.stdout')
    def test_simple_transport_empty_lines(self, mock_stdout, mock_stdin):
        """Test simple transport handling of empty lines."""
        # Setup mock stdin with empty lines and then a valid message
        mock_stdin.readline.side_effect = [
            '\n',  # Empty line
            '   \n',  # Whitespace only
            '{"type": "ping", "id": "test_1"}\n',  # Valid message
            ''  # EOF
        ]
        
        # Setup mock stdout
        mock_stdout.write = MagicMock()
        mock_stdout.flush = MagicMock()
        
        # Start transport
        self.transport.start()
        
        # Should only write response for the valid message
        assert mock_stdout.write.call_count == 1
        written_data = mock_stdout.write.call_args[0][0]
        
        response = json.loads(written_data.strip())
        assert response["type"] == "pong"
        assert response["id"] == "test_1"
    
    def test_stop_method(self):
        """Test the stop method."""
        self.transport.running = True
        self.transport.stop()
        assert not self.transport.running


class TestTransportIntegration:
    """Test transport integration with protocol handler."""
    
    def setup_method(self):
        """Setup integration test."""
        self.handler = MCPProtocolHandler(debug=True)
        
        # Register a test tool
        def echo_tool(message: str) -> str:
            return f"Echo: {message}"
        
        self.handler.register_tool(
            "echo",
            echo_tool,
            "Echo back the input message",
            {"message": {"type": "string"}}
        )
    
    def test_full_message_flow(self):
        """Test complete message flow through transport and handler."""
        transport = SimpleStdioTransport(self.handler.handle_message_dict)
        
        # Test initialization
        init_message = {"type": "initialize", "id": "init_1"}
        response = self.handler.handle_message_dict(init_message)
        
        assert response["type"] == "initialized"
        assert response["id"] == "init_1"
        
        # Test tool listing
        list_message = {"type": "list_tools", "id": "list_1"}
        response = self.handler.handle_message_dict(list_message)
        
        assert response["type"] == "list_tools"
        assert len(response["result"]["tools"]) == 1
        assert response["result"]["tools"][0]["name"] == "echo"
        
        # Test tool calling
        call_message = {
            "type": "call_tool",
            "id": "call_1",
            "params": {
                "name": "echo",
                "arguments": {"message": "Hello World"}
            }
        }
        response = self.handler.handle_message_dict(call_message)
        
        assert response["type"] == "call_tool"
        assert response["result"]["content"] == "Echo: Hello World"
