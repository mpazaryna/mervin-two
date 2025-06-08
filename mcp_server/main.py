"""
Main entry point for MCP Learning Server

This module provides the main entry point and command-line interface
for the MCP Learning Server.
"""

import argparse
import sys
import logging
import signal
import os
from typing import Optional

from .protocol import create_protocol_handler
from .stdio_transport import StdioTransport, SimpleStdioTransport
from .logging_config import setup_logger
from .config import MCPServerConfig
from .metrics import PerformanceMetrics
from .hot_reload import create_hot_reload_manager


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
        "--config",
        help="Path to configuration file"
    )

    parser.add_argument(
        "--hot-reload",
        action="store_true",
        help="Enable hot reload for development"
    )

    parser.add_argument(
        "--metrics-enabled",
        action="store_true",
        help="Enable performance metrics collection"
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

    args = parser.parse_args()

    # Create configuration
    try:
        config = MCPServerConfig(config_file=args.config, args=args)
    except Exception as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    # Setup logging
    logger = setup_logger("mcp_main", config.log_level)

    logger.info("Starting MCP Learning Server")
    logger.info(f"Debug mode: {config.debug}")
    logger.info(f"Log level: {config.log_level}")
    logger.info(f"Simple transport: {config.use_simple_transport}")

    # Global state for cleanup
    metrics = None
    hot_reload_manager = None
    transport = None

    def signal_handler(signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down...")

        if hot_reload_manager:
            hot_reload_manager.stop()

        if metrics:
            logger.info("Final metrics:")
            final_metrics = metrics.get_basic_metrics()
            for key, value in final_metrics.items():
                logger.info(f"  {key}: {value}")

        sys.exit(0)

    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Initialize metrics if enabled
        if config.metrics_enabled:
            metrics = PerformanceMetrics()
            logger.info("Performance metrics enabled")

        # Create protocol handler with configuration
        handler = create_protocol_handler(
            debug=config.debug,
            resource_dir=config.resource_dir,
            prompt_dir=config.prompts_dir
        )

        # Integrate metrics with server if available
        if metrics and hasattr(handler, 'server'):
            handler.server.metrics = metrics

        # Initialize hot reload if enabled
        if config.hot_reload:
            hot_reload_manager = create_hot_reload_manager(config)
            if hot_reload_manager:
                # Register reload callbacks
                if hasattr(handler, 'server'):
                    hot_reload_manager.register_callback(
                        "resources",
                        lambda path, change: handler.server.resource_manager.reload_index()
                    )
                    hot_reload_manager.register_callback(
                        "prompts",
                        lambda path, change: handler.server.prompt_manager.reload_prompts()
                    )

                hot_reload_manager.start()
                logger.info("Hot reload enabled")
            else:
                logger.warning("Hot reload requested but could not be initialized")

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
        if config.use_simple_transport:
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
        if config.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        # Cleanup
        if hot_reload_manager:
            hot_reload_manager.stop()

        if metrics:
            logger.info("Final server metrics:")
            final_metrics = metrics.get_basic_metrics()
            for key, value in final_metrics.items():
                logger.info(f"  {key}: {value}")

        logger.info("MCP Learning Server stopped")


if __name__ == "__main__":
    main()
