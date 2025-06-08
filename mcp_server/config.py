"""
Configuration Management System

This module provides configuration management for the MCP Learning Server,
including file-based configuration, command-line argument parsing, and
environment variable support.
"""

import os
import json
import argparse
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from .logging_config import get_logger


class MCPServerConfig:
    """
    Configuration management for MCP Learning Server.
    
    Handles configuration from multiple sources with precedence:
    1. Command line arguments (highest priority)
    2. Configuration file
    3. Environment variables
    4. Default values (lowest priority)
    """
    
    def __init__(self, config_file: Optional[str] = None, args: Optional[argparse.Namespace] = None):
        """
        Initialize configuration.
        
        Args:
            config_file: Path to configuration file
            args: Parsed command line arguments
        """
        self.logger = get_logger("mcp_config")
        
        # Default configuration
        self._set_defaults()
        
        # Load from environment variables
        self._load_from_env()
        
        # Load from config file
        if config_file:
            self._load_from_file(config_file)
        
        # Override with command line arguments
        if args:
            self._load_from_args(args)
        
        # Validate configuration
        self._validate()
        
        self.logger.info(f"Configuration loaded: debug={self.debug}, hot_reload={self.hot_reload}")
    
    def _set_defaults(self) -> None:
        """Set default configuration values."""
        # Core settings
        self.debug = False
        self.hot_reload = False
        self.log_level = "INFO"
        self.metrics_enabled = False
        
        # Directory settings
        self.resource_dir = "./resources"
        self.tools_dir = "./tools"
        self.prompts_dir = "./prompts"
        self.config_dir = "./config"
        
        # Server settings
        self.server_name = "MCP Learning Server"
        self.server_version = "0.1.0"
        self.server_description = "Educational MCP server implementation"
        
        # Performance settings
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.cache_size = 100
        self.request_timeout = 30.0
        
        # Development settings
        self.auto_reload_interval = 1.0  # seconds
        self.enable_profiling = False
        self.test_mode = False
        
        # Transport settings
        self.use_simple_transport = False
        self.enable_compression = False
        
        # Security settings
        self.restrict_file_access = True
        self.allowed_file_extensions = [".txt", ".md", ".json", ".csv", ".log"]
        
        # Logging settings
        self.log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        self.log_file = None
        self.log_max_size = 10 * 1024 * 1024  # 10MB
        self.log_backup_count = 5
    
    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        env_mappings = {
            "MCP_DEBUG": ("debug", bool),
            "MCP_HOT_RELOAD": ("hot_reload", bool),
            "MCP_LOG_LEVEL": ("log_level", str),
            "MCP_METRICS_ENABLED": ("metrics_enabled", bool),
            "MCP_RESOURCE_DIR": ("resource_dir", str),
            "MCP_TOOLS_DIR": ("tools_dir", str),
            "MCP_PROMPTS_DIR": ("prompts_dir", str),
            "MCP_MAX_FILE_SIZE": ("max_file_size", int),
            "MCP_CACHE_SIZE": ("cache_size", int),
            "MCP_TEST_MODE": ("test_mode", bool),
        }
        
        for env_var, (attr_name, attr_type) in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                try:
                    if attr_type == bool:
                        value = env_value.lower() in ("true", "1", "yes", "on")
                    elif attr_type == int:
                        value = int(env_value)
                    else:
                        value = env_value
                    
                    setattr(self, attr_name, value)
                    self.logger.debug(f"Loaded from env {env_var}: {attr_name}={value}")
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"Invalid environment variable {env_var}={env_value}: {e}")
    
    def _load_from_file(self, config_file: str) -> None:
        """
        Load configuration from JSON file.
        
        Args:
            config_file: Path to configuration file
        """
        try:
            config_path = Path(config_file)
            if not config_path.exists():
                self.logger.warning(f"Configuration file not found: {config_file}")
                return
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Flatten nested configuration
            flat_config = self._flatten_config(config_data)
            
            # Apply configuration values
            for key, value in flat_config.items():
                if hasattr(self, key):
                    setattr(self, key, value)
                    self.logger.debug(f"Loaded from file: {key}={value}")
                else:
                    self.logger.warning(f"Unknown configuration key: {key}")
            
            self.logger.info(f"Configuration loaded from {config_file}")
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in configuration file {config_file}: {e}")
            raise ValueError(f"Invalid configuration file: {e}")
        except Exception as e:
            self.logger.error(f"Failed to load configuration file {config_file}: {e}")
            raise
    
    def _flatten_config(self, config_data: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """
        Flatten nested configuration dictionary.
        
        Args:
            config_data: Nested configuration dictionary
            prefix: Prefix for flattened keys
            
        Returns:
            Flattened configuration dictionary
        """
        flat_config = {}
        
        for key, value in config_data.items():
            full_key = f"{prefix}_{key}" if prefix else key
            
            if isinstance(value, dict):
                # Recursively flatten nested dictionaries
                flat_config.update(self._flatten_config(value, full_key))
            else:
                flat_config[full_key] = value
        
        return flat_config
    
    def _load_from_args(self, args: argparse.Namespace) -> None:
        """
        Load configuration from command line arguments.
        
        Args:
            args: Parsed command line arguments
        """
        arg_mappings = {
            "debug": "debug",
            "hot_reload": "hot_reload",
            "log_level": "log_level",
            "metrics_enabled": "metrics_enabled",
            "simple": "use_simple_transport",
            "test_mode": "test_mode",
            "resource_dir": "resource_dir",
            "tools_dir": "tools_dir",
            "prompts_dir": "prompts_dir",
        }
        
        for arg_name, attr_name in arg_mappings.items():
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    setattr(self, attr_name, value)
                    self.logger.debug(f"Loaded from args: {attr_name}={value}")
    
    def _validate(self) -> None:
        """Validate configuration values."""
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_log_levels:
            raise ValueError(f"Invalid log level: {self.log_level}. Must be one of {valid_log_levels}")
        
        # Validate directories
        for dir_attr in ["resource_dir", "tools_dir", "prompts_dir"]:
            dir_path = getattr(self, dir_attr)
            if not isinstance(dir_path, str) or not dir_path:
                raise ValueError(f"Invalid directory path for {dir_attr}: {dir_path}")
        
        # Validate numeric values
        if self.max_file_size <= 0:
            raise ValueError(f"Invalid max_file_size: {self.max_file_size}")
        
        if self.cache_size <= 0:
            raise ValueError(f"Invalid cache_size: {self.cache_size}")
        
        if self.request_timeout <= 0:
            raise ValueError(f"Invalid request_timeout: {self.request_timeout}")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Configuration as dictionary
        """
        config_dict = {}
        for attr_name in dir(self):
            if not attr_name.startswith('_') and not callable(getattr(self, attr_name)):
                if attr_name != 'logger':
                    config_dict[attr_name] = getattr(self, attr_name)
        
        return config_dict
    
    def save_to_file(self, config_file: str) -> None:
        """
        Save current configuration to file.
        
        Args:
            config_file: Path to save configuration
        """
        try:
            config_dict = self.to_dict()
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, sort_keys=True)
            
            self.logger.info(f"Configuration saved to {config_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration to {config_file}: {e}")
            raise
    
    def get_directories(self) -> Dict[str, str]:
        """
        Get all directory configurations.
        
        Returns:
            Dictionary of directory configurations
        """
        return {
            "resource_dir": self.resource_dir,
            "tools_dir": self.tools_dir,
            "prompts_dir": self.prompts_dir,
            "config_dir": self.config_dir
        }
    
    def is_development_mode(self) -> bool:
        """
        Check if server is running in development mode.
        
        Returns:
            True if in development mode
        """
        return self.debug or self.hot_reload or self.test_mode
