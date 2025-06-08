"""
Main entry point for MCP Learning Server

This module provides the main entry point and command-line interface
for the MCP Learning Server.
"""

import argparse
import sys
import logging
from typing import Optional

from .protocol import create_protocol_handler
from .stdio_transport import StdioTransport, SimpleStdioTransport
from .logging_config import setup_logger


def setup_tools_integration(handler, categories=None):
    """
    Setup tools integration with the protocol handler.

    Args:
        handler: Protocol handler to register tools with
        categories: List of tool categories to register (None for all)
    """
    from tools.integration import setup_tools, create_tool_info_tool

    # Setup tool integration
    integrator = setup_tools(handler, categories)

    # Create meta-tool for tool information
    create_tool_info_tool(integrator)

    return integrator


def main():
    """Main entry point for the MCP Learning Server."""
    parser = argparse.ArgumentParser(
        description="MCP Learning Server - Educational MCP server implementation"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with verbose logging"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level"
    )
    
    parser.add_argument(
        "--simple",
        action="store_true",
        help="Use simple synchronous transport instead of threaded transport"
    )
    
    parser.add_argument(
        "--no-tools",
        action="store_true",
        help="Don't register any tools (for testing)"
    )

    parser.add_argument(
        "--categories",
        nargs="*",
        help="Specific tool categories to register (default: all)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = "DEBUG" if args.debug else args.log_level
    logger = setup_logger("mcp_main", log_level)
    
    logger.info("Starting MCP Learning Server")
    logger.info(f"Debug mode: {args.debug}")
    logger.info(f"Log level: {log_level}")
    logger.info(f"Simple transport: {args.simple}")
    
    try:
        # Create protocol handler
        handler = create_protocol_handler(debug=args.debug)
        
        # Register tools unless disabled
        if not args.no_tools:
            integrator = setup_tools_integration(handler, args.categories)
            registered_tools = integrator.get_registered_tools()
            logger.info(f"Registered {len(registered_tools)} tools: {', '.join(registered_tools)}")

            # Log categories summary
            categories_summary = integrator.get_categories_summary()
            for category, info in categories_summary.items():
                logger.info(f"Category '{category}': {info['registered_tools']}/{info['total_tools']} tools registered")
        
        # Create and start transport
        if args.simple:
            logger.info("Using simple stdio transport")
            transport = SimpleStdioTransport(handler.handle_message_dict)
        else:
            logger.info("Using threaded stdio transport")
            transport = StdioTransport(handler.handle_message_dict)
        
        logger.info("Starting transport layer...")
        transport.start()
        
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        logger.info("MCP Learning Server stopped")


if __name__ == "__main__":
    main()
