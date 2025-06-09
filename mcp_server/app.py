"""
MCP Learning Server Application

This module provides the main application class that integrates all components
and provides the complete MCP server functionality.
"""

import signal
import sys
import logging
import threading
from typing import Optional, Dict, Any, Callable
from datetime import datetime

from .config import MCPServerConfig
from .protocol import MCPProtocolHandler, create_protocol_handler
from .stdio_transport import StdioTransport, SimpleStdioTransport
from .metrics import PerformanceMetrics
from .logging_config import setup_logger, get_logger
from .hot_reload import create_hot_reload_manager


class MCPLearningServer:
    """
    Main MCP Learning Server application.
    
    Integrates all components (protocol handlers, transport, tools, resources, prompts)
    and provides complete MCP server functionality with lifecycle management.
    """
    
    def __init__(self, config: Optional[MCPServerConfig] = None):
        """
        Initialize the MCP Learning Server.
        
        Args:
            config: Server configuration (uses defaults if None)
        """
        self.config = config or MCPServerConfig()
        self.logger = None
        self.metrics = None
        self.protocol_handler = None
        self.transport = None
        self.hot_reload_manager = None
        self.tools_integrator = None
        
        # Server state
        self.running = False
        self.shutdown_requested = False
        self.start_time = None
        
        # Thread safety
        self._shutdown_lock = threading.Lock()
        
        # Initialize the server
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize all server components."""
        # Setup logging first
        self._setup_logging()
        
        self.logger.info("Initializing MCP Learning Server")
        self.logger.info(f"Configuration: debug={self.config.debug}, "
                        f"hot_reload={self.config.hot_reload}, "
                        f"metrics={self.config.metrics_enabled}")
        
        # Initialize metrics if enabled
        if self.config.metrics_enabled:
            self.metrics = PerformanceMetrics()
            self.logger.info("Performance metrics enabled")
        
        # Create protocol handler
        self.protocol_handler = create_protocol_handler(
            debug=self.config.debug,
            resource_dir=self.config.resource_dir,
            prompt_dir=self.config.prompts_dir
        )
        
        # Setup tools integration
        self._setup_tools()
        
        # Create transport layer
        self._create_transport()
        
        # Setup hot reload if enabled
        if self.config.hot_reload:
            self._setup_hot_reload()
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        self.logger.info("MCP Learning Server initialized successfully")
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        setup_logger(
            level=self.config.log_level,
            format_string=self.config.log_format,
            log_file=self.config.log_file,
            log_max_size=self.config.log_max_size,
            log_backup_count=self.config.log_backup_count
        )
        self.logger = get_logger("mcp_app")
    
    def _setup_tools(self) -> None:
        """Setup tools integration."""
        try:
            from tools.integration import setup_tools
            
            # Setup tool integration
            self.tools_integrator = setup_tools(self.protocol_handler)
            
            # Get registered tools info
            registered_tools = self.tools_integrator.get_registered_tools()
            categories_summary = self.tools_integrator.get_categories_summary()
            
            self.logger.info(f"Registered {len(registered_tools)} tools: {', '.join(registered_tools)}")
            
            # Log categories summary
            for category, info in categories_summary.items():
                self.logger.info(f"Category '{category}': {info['registered_tools']}/{info['total_tools']} tools")
                
        except ImportError as e:
            self.logger.warning(f"Could not import tools integration: {e}")
            self.tools_integrator = None
        except Exception as e:
            self.logger.error(f"Error setting up tools: {e}")
            self.tools_integrator = None
    
    def _create_transport(self) -> None:
        """Create the transport layer."""
        # Create message handler that includes metrics
        message_handler = self._create_message_handler()
        
        # Choose transport type based on configuration
        if self.config.use_simple_transport:
            self.transport = SimpleStdioTransport(message_handler)
            self.logger.info("Using simple stdio transport")
        else:
            self.transport = StdioTransport(message_handler)
            self.logger.info("Using threaded stdio transport")
    
    def _create_message_handler(self) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
        """Create a message handler that includes metrics tracking."""
        def handle_message_with_metrics(message: Dict[str, Any]) -> Dict[str, Any]:
            start_time = datetime.now()
            
            # Record request if metrics enabled
            if self.metrics:
                self.metrics.record_request()
                message_type = message.get('type', 'unknown')
                self.metrics.record_request_by_type(message_type)
            
            try:
                # Handle the message
                response = self.protocol_handler.handle_message_dict(message)
                
                # Record response time if metrics enabled
                if self.metrics:
                    response_time = (datetime.now() - start_time).total_seconds() * 1000
                    self.metrics.record_response_time(response_time)
                
                return response
                
            except Exception as e:
                # Record error if metrics enabled
                if self.metrics:
                    self.metrics.record_error()
                    error_type = type(e).__name__
                    self.metrics.record_error_by_type(error_type)
                
                self.logger.error(f"Error handling message: {e}")
                
                # Return error response
                return {
                    "type": "error",
                    "error": str(e),
                    "code": 500
                }
        
        return handle_message_with_metrics
    
    def _setup_hot_reload(self) -> None:
        """Setup hot reload functionality."""
        try:
            self.hot_reload_manager = create_hot_reload_manager(self.config)
            
            if self.hot_reload_manager and self.protocol_handler:
                # Register reload callbacks
                if hasattr(self.protocol_handler, 'server'):
                    server = self.protocol_handler.server
                    
                    # Resource reload callback
                    if hasattr(server, 'resource_manager'):
                        self.hot_reload_manager.register_callback(
                            "resources",
                            lambda path, change: server.resource_manager.reload_index()
                        )
                    
                    # Prompt reload callback
                    if hasattr(server, 'prompt_manager'):
                        self.hot_reload_manager.register_callback(
                            "prompts", 
                            lambda path, change: server.prompt_manager.reload_prompts()
                        )
                
                self.logger.info("Hot reload configured")
            else:
                self.logger.warning("Hot reload requested but could not be initialized")
                
        except Exception as e:
            self.logger.error(f"Error setting up hot reload: {e}")
            self.hot_reload_manager = None
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            signal_name = signal.Signals(signum).name
            self.logger.info(f"Received {signal_name}, initiating graceful shutdown...")
            self.shutdown()
        
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # On Unix systems, also handle SIGHUP
        if hasattr(signal, 'SIGHUP'):
            signal.signal(signal.SIGHUP, signal_handler)
    
    def start(self) -> None:
        """Start the MCP Learning Server."""
        with self._shutdown_lock:
            if self.running:
                self.logger.warning("Server is already running")
                return
            
            self.running = True
            self.shutdown_requested = False
            self.start_time = datetime.now()
        
        self.logger.info("Starting MCP Learning Server")
        
        try:
            # Start hot reload if enabled
            if self.hot_reload_manager:
                self.hot_reload_manager.start()
                self.logger.info("Hot reload started")
            
            # Start the transport layer
            self.logger.info("Starting transport layer...")
            self.transport.start()
            
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        except Exception as e:
            self.logger.error(f"Error in server main loop: {e}")
        finally:
            self.shutdown()
    
    def shutdown(self) -> None:
        """Shutdown the MCP Learning Server gracefully."""
        with self._shutdown_lock:
            if self.shutdown_requested:
                return
            
            self.shutdown_requested = True
        
        self.logger.info("Shutting down MCP Learning Server...")
        
        try:
            # Stop hot reload
            if self.hot_reload_manager:
                self.hot_reload_manager.stop()
                self.logger.info("Hot reload stopped")
            
            # Stop transport
            if self.transport:
                self.transport.stop()
                self.logger.info("Transport stopped")
            
            # Log final metrics if enabled
            if self.metrics and self.start_time:
                uptime = datetime.now() - self.start_time
                final_metrics = self.metrics.get_basic_metrics()
                self.logger.info(f"Server uptime: {uptime}")
                self.logger.info(f"Final metrics: {final_metrics}")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
        finally:
            self.running = False
            self.logger.info("MCP Learning Server shutdown complete")
    
    def is_running(self) -> bool:
        """Check if the server is running."""
        return self.running and not self.shutdown_requested
    
    def get_status(self) -> Dict[str, Any]:
        """Get server status information."""
        status = {
            "running": self.is_running(),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            "config": {
                "debug": self.config.debug,
                "hot_reload": self.config.hot_reload,
                "metrics_enabled": self.config.metrics_enabled,
                "log_level": self.config.log_level
            }
        }
        
        # Add metrics if available
        if self.metrics:
            status["metrics"] = self.metrics.get_basic_metrics()
        
        # Add tools info if available
        if self.tools_integrator:
            status["tools"] = {
                "registered_tools": self.tools_integrator.get_registered_tools(),
                "categories": self.tools_integrator.get_categories_summary()
            }
        
        return status
