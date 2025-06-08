"""
MCP Learning Server

A simple Python-based Model Context Protocol (MCP) server designed to help users
learn MCP fundamentals through hands-on implementation and experimentation.
"""

__version__ = "0.1.0"
__author__ = "MCP Learning Project"
__description__ = "Educational MCP server implementation"

# Import main components for easy access
from .server import MCPServer
from .protocol import MCPProtocolHandler, create_protocol_handler
from .messages import MessageType, parse_message, create_error_message
from .logging_config import setup_logger, get_logger
from .stdio_transport import StdioTransport, SimpleStdioTransport

__all__ = [
    "MCPServer",
    "MCPProtocolHandler",
    "create_protocol_handler",
    "MessageType",
    "parse_message",
    "create_error_message",
    "setup_logger",
    "get_logger",
    "StdioTransport",
    "SimpleStdioTransport"
]
