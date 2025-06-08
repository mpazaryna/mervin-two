"""
Tests for Development Features

This module contains unit tests for the development features
of the MCP Learning Server including configuration, metrics, and hot reload.
"""

import os
import json
import tempfile
import pytest
import time
from unittest.mock import patch, MagicMock

from mcp_server.config import MCPServerConfig
from mcp_server.metrics import PerformanceMetrics, MetricsContext
from mcp_server.hot_reload import HotReloadManager


class TestMCPServerConfig:
    """Test MCPServerConfig class."""
    
    def test_default_configuration(self):
        """Test default configuration values."""
        config = MCPServerConfig()
        
        assert config.debug is False
        assert config.hot_reload is False
        assert config.log_level == "INFO"
        assert config.metrics_enabled is False
        assert config.resource_dir == "./resources"
        assert config.tools_dir == "./tools"
        assert config.prompts_dir == "./prompts"
        assert config.server_name == "MCP Learning Server"
        assert config.server_version == "0.1.0"
        assert config.max_file_size == 10 * 1024 * 1024
        assert config.cache_size == 100
    
    def test_environment_variable_loading(self):
        """Test loading configuration from environment variables."""
        with patch.dict(os.environ, {
            'MCP_DEBUG': 'true',
            'MCP_LOG_LEVEL': 'DEBUG',
            'MCP_METRICS_ENABLED': 'true',
            'MCP_CACHE_SIZE': '50'
        }):
            config = MCPServerConfig()
            
            assert config.debug is True
            assert config.log_level == "DEBUG"
            assert config.metrics_enabled is True
            assert config.cache_size == 50
    
    def test_config_file_loading(self):
        """Test loading configuration from JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "debug": True,
                "log_level": "DEBUG",
                "metrics_enabled": True,
                "cache_size": 200,
                "server": {
                    "name": "Test Server"
                }
            }
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            config = MCPServerConfig(config_file=config_file)
            
            assert config.debug is True
            assert config.log_level == "DEBUG"
            assert config.metrics_enabled is True
            assert config.cache_size == 200
            assert config.server_name == "Test Server"
        finally:
            os.unlink(config_file)
    
    def test_command_line_args_override(self):
        """Test command line arguments override other sources."""
        # Create mock args with only the attributes we want to test
        args = MagicMock()
        args.debug = True
        args.hot_reload = True
        args.log_level = "ERROR"
        args.metrics_enabled = True
        args.simple = True
        args.test_mode = True

        # Set attributes that don't exist to None
        args.resource_dir = None
        args.tools_dir = None
        args.prompts_dir = None

        config = MCPServerConfig(args=args)

        assert config.debug is True
        assert config.hot_reload is True
        assert config.log_level == "ERROR"
        assert config.metrics_enabled is True
        assert config.use_simple_transport is True
        assert config.test_mode is True
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Test invalid log level
        args = MagicMock()
        args.log_level = "INVALID"
        
        with pytest.raises(ValueError, match="Invalid log level"):
            MCPServerConfig(args=args)
    
    def test_config_to_dict(self):
        """Test converting configuration to dictionary."""
        config = MCPServerConfig()
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert "debug" in config_dict
        assert "log_level" in config_dict
        assert "server_name" in config_dict
        assert "logger" not in config_dict  # Should exclude logger
    
    def test_is_development_mode(self):
        """Test development mode detection."""
        # Normal mode
        config = MCPServerConfig()
        assert config.is_development_mode() is False
        
        # Debug mode
        config.debug = True
        assert config.is_development_mode() is True
        
        # Hot reload mode
        config.debug = False
        config.hot_reload = True
        assert config.is_development_mode() is True
        
        # Test mode
        config.hot_reload = False
        config.test_mode = True
        assert config.is_development_mode() is True


class TestPerformanceMetrics:
    """Test PerformanceMetrics class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.metrics = PerformanceMetrics(max_history=10)
    
    def test_metrics_initialization(self):
        """Test metrics initialization."""
        assert self.metrics.request_count == 0
        assert self.metrics.error_count == 0
        assert len(self.metrics.response_times) == 0
        assert len(self.metrics.active_requests) == 0
    
    def test_request_tracking(self):
        """Test request tracking."""
        # Start request
        self.metrics.start_request("req1", "test_request")
        
        assert self.metrics.request_count == 1
        assert self.metrics.requests_by_type["test_request"] == 1
        assert "req1" in self.metrics.active_requests
        
        # End request
        response_time = self.metrics.end_request("req1", success=True)
        
        assert response_time is not None
        assert response_time > 0
        assert "req1" not in self.metrics.active_requests
        assert len(self.metrics.response_times) == 1
    
    def test_error_tracking(self):
        """Test error tracking."""
        self.metrics.record_error("ValueError", "test_request")
        
        assert self.metrics.error_count == 1
        assert self.metrics.errors_by_type["ValueError"] == 1
        assert self.metrics.errors_by_type["test_request_ValueError"] == 1
    
    def test_tool_call_tracking(self):
        """Test tool call tracking."""
        self.metrics.record_tool_call("test_tool", response_time=0.5, success=True)
        
        assert self.metrics.tool_calls["test_tool"] == 1
        assert self.metrics.tool_response_times["test_tool"] == [0.5]
        assert self.metrics.tool_errors["test_tool"] == 0
        
        # Test failed tool call
        self.metrics.record_tool_call("test_tool", response_time=1.0, success=False)
        
        assert self.metrics.tool_calls["test_tool"] == 2
        assert self.metrics.tool_errors["test_tool"] == 1
    
    def test_resource_tracking(self):
        """Test resource request tracking."""
        # Cache miss
        self.metrics.record_resource_request("resource1", cache_hit=False)
        
        assert self.metrics.resource_requests["resource1"] == 1
        assert self.metrics.resource_cache_misses == 1
        assert self.metrics.resource_cache_hits == 0
        
        # Cache hit
        self.metrics.record_resource_request("resource1", cache_hit=True)
        
        assert self.metrics.resource_requests["resource1"] == 2
        assert self.metrics.resource_cache_hits == 1
    
    def test_prompt_tracking(self):
        """Test prompt request tracking."""
        self.metrics.record_prompt_request("prompt1", render_time=0.1)
        
        assert self.metrics.prompt_requests["prompt1"] == 1
        assert self.metrics.prompt_render_times == [0.1]
    
    def test_basic_metrics(self):
        """Test basic metrics calculation."""
        # Add some test data
        self.metrics.start_request("req1", "test")
        time.sleep(0.01)  # Small delay
        self.metrics.end_request("req1", success=True)
        
        self.metrics.record_error("TestError", "test")
        
        basic_metrics = self.metrics.get_basic_metrics()
        
        assert basic_metrics["request_count"] == 1
        assert basic_metrics["error_count"] == 1
        assert basic_metrics["error_rate"] == 1.0
        assert basic_metrics["active_requests"] == 0
        assert basic_metrics["average_response_time"] > 0
        assert basic_metrics["uptime_seconds"] > 0
    
    def test_detailed_metrics(self):
        """Test detailed metrics calculation."""
        # Add test data
        self.metrics.record_tool_call("tool1", 0.5, True)
        self.metrics.record_resource_request("res1", False)
        self.metrics.record_prompt_request("prompt1", 0.1)
        
        detailed_metrics = self.metrics.get_detailed_metrics()
        
        assert "tool_metrics" in detailed_metrics
        assert "resource_metrics" in detailed_metrics
        assert "prompt_metrics" in detailed_metrics
        assert "response_time_percentiles" in detailed_metrics
        
        # Check tool metrics
        tool_metrics = detailed_metrics["tool_metrics"]["tool1"]
        assert tool_metrics["calls"] == 1
        assert tool_metrics["errors"] == 0
        assert tool_metrics["average_response_time"] == 0.5
    
    def test_metrics_context(self):
        """Test metrics context manager."""
        with MetricsContext(self.metrics, "req1", "test_request") as ctx:
            time.sleep(0.01)
        
        assert self.metrics.request_count == 1
        assert len(self.metrics.response_times) == 1
        
        # Test with error
        with pytest.raises(ValueError):
            with MetricsContext(self.metrics, "req2", "test_request") as ctx:
                raise ValueError("Test error")
        
        assert self.metrics.request_count == 2
        assert self.metrics.error_count == 1
    
    def test_metrics_reset(self):
        """Test metrics reset functionality."""
        # Add some data
        self.metrics.start_request("req1", "test")
        self.metrics.record_error("TestError")
        self.metrics.record_tool_call("tool1", 0.5)
        
        # Reset
        self.metrics.reset_metrics()
        
        assert self.metrics.request_count == 0
        assert self.metrics.error_count == 0
        assert len(self.metrics.response_times) == 0
        assert len(self.metrics.tool_calls) == 0


class TestHotReloadManager:
    """Test HotReloadManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create mock config
        self.config = MagicMock()
        self.config.tools_dir = "./tools"
        self.config.resource_dir = "./resources"
        self.config.prompts_dir = "./prompts"
        
        self.hot_reload = HotReloadManager(self.config)
    
    def test_hot_reload_initialization(self):
        """Test hot reload manager initialization."""
        assert self.hot_reload.config == self.config
        assert self.hot_reload.is_running is False
        assert len(self.hot_reload.reload_callbacks) == 0
        assert len(self.hot_reload.watched_dirs) == 0
    
    def test_callback_registration(self):
        """Test callback registration and unregistration."""
        callback = MagicMock()
        
        # Register callback
        self.hot_reload.register_callback("test_callback", callback)
        
        assert "test_callback" in self.hot_reload.reload_callbacks
        assert self.hot_reload.reload_callbacks["test_callback"] == callback
        
        # Unregister callback
        self.hot_reload.unregister_callback("test_callback")
        
        assert "test_callback" not in self.hot_reload.reload_callbacks
    
    def test_watch_directory_management(self):
        """Test watch directory management."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Add watch directory
            self.hot_reload.add_watch_directory(temp_dir)
            
            assert temp_dir in self.hot_reload.watched_dirs
            
            # Remove watch directory
            self.hot_reload.remove_watch_directory(temp_dir)
            
            assert temp_dir not in self.hot_reload.watched_dirs
    
    def test_force_reload(self):
        """Test force reload functionality."""
        callback = MagicMock()
        self.hot_reload.register_callback("test_callback", callback)
        
        # Force reload specific component
        self.hot_reload.force_reload("test_callback")
        
        callback.assert_called_once_with("", "force_reload")
        
        # Force reload all components
        callback.reset_mock()
        self.hot_reload.force_reload()
        
        callback.assert_called_once_with("", "force_reload")
    
    def test_get_status(self):
        """Test status information."""
        status = self.hot_reload.get_status()
        
        assert "is_running" in status
        assert "watched_directories" in status
        assert "registered_callbacks" in status
        assert "reload_count" in status
        assert "observer_alive" in status
        
        assert status["is_running"] is False
        assert status["reload_count"] == 0
