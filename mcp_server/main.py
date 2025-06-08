"""
Main entry point for MCP Learning Server

This module provides the main entry point and command-line interface
for the MCP Learning Server.
"""

import argparse
import sys
import logging
import os
from typing import Optional

from .app import MCPLearningServer
from .config import MCPServerConfig
from .logging_config import setup_logger


def create_argument_parser() -> argparse.ArgumentParser:
    """
    Create and configure the command-line argument parser.

    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description="MCP Learning Server - Educational MCP server implementation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m mcp_server                    # Start with default settings
  python -m mcp_server --debug           # Start in debug mode
  python -m mcp_server --hot-reload      # Enable hot reload
  python -m mcp_server --config config.json  # Use custom config file
        """
    )

    # Core configuration options
    parser.add_argument(
        "--config",
        help="Path to configuration file"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with verbose logging"
    )

    parser.add_argument(
        "--hot-reload",
        action="store_true",
        help="Enable hot reload for tools and resources"
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set logging level"
    )

    parser.add_argument(
        "--metrics",
        action="store_true",
        help="Enable performance metrics collection"
    )

    parser.add_argument(
        "--simple",
        action="store_true",
        help="Use simple synchronous transport instead of threaded transport"
    )

    parser.add_argument(
        "--resource-dir",
        help="Directory containing resources"
    )

    parser.add_argument(
        "--tools-dir",
        help="Directory containing tools"
    )

    parser.add_argument(
        "--prompts-dir",
        help="Directory containing prompts"
    )

    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Enable test mode"
    )

    return parser


def main():
    """Main entry point for the MCP Learning Server."""
    # Create argument parser and parse arguments
    parser = create_argument_parser()
    args = parser.parse_args()

    # Create configuration
    try:
        config = MCPServerConfig(config_file=args.config, args=args)
    except Exception as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    # Create and start the MCP Learning Server
    try:
        server = MCPLearningServer(config)
        server.start()
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt, shutting down gracefully...")
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        if config.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)




if __name__ == "__main__":
    main()
