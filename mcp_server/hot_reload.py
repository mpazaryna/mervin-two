"""
Hot Reload System

This module provides hot reload functionality for the MCP Learning Server,
allowing dynamic reloading of tools, resources, and prompts without
server restart.
"""

import os
import time
import threading
import importlib
import sys
from typing import Dict, Set, Callable, Optional, Any
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent

from .logging_config import get_logger


class HotReloadHandler(FileSystemEventHandler):
    """File system event handler for hot reload functionality."""
    
    def __init__(self, reload_callback: Callable[[str, str], None]):
        """
        Initialize hot reload handler.
        
        Args:
            reload_callback: Callback function for reload events
        """
        super().__init__()
        self.reload_callback = reload_callback
        self.logger = get_logger("hot_reload_handler")
        
        # Debounce settings
        self.last_reload_time: Dict[str, float] = {}
        self.debounce_delay = 0.5  # seconds
    
    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory:
            self._handle_file_change(event.src_path, "modified")
    
    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory:
            self._handle_file_change(event.src_path, "created")
    
    def on_deleted(self, event):
        """Handle file deletion events."""
        if not event.is_directory:
            self._handle_file_change(event.src_path, "deleted")
    
    def _handle_file_change(self, file_path: str, change_type: str):
        """
        Handle file change with debouncing.
        
        Args:
            file_path: Path to the changed file
            change_type: Type of change (modified, created, deleted)
        """
        current_time = time.time()
        
        # Debounce rapid file changes
        if file_path in self.last_reload_time:
            if current_time - self.last_reload_time[file_path] < self.debounce_delay:
                return
        
        self.last_reload_time[file_path] = current_time
        
        # Only process relevant file types
        if self._should_reload_file(file_path):
            self.logger.info(f"File {change_type}: {file_path}")
            self.reload_callback(file_path, change_type)
    
    def _should_reload_file(self, file_path: str) -> bool:
        """
        Check if file should trigger a reload.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file should trigger reload
        """
        # Skip temporary files and hidden files
        filename = os.path.basename(file_path)
        if filename.startswith('.') or filename.endswith('.tmp') or filename.endswith('.swp'):
            return False
        
        # Only reload specific file types
        reload_extensions = {'.py', '.json', '.md', '.txt', '.csv'}
        file_ext = Path(file_path).suffix.lower()
        
        return file_ext in reload_extensions


class HotReloadManager:
    """
    Hot reload manager for MCP Learning Server.
    
    Monitors file system changes and triggers appropriate reload actions
    for tools, resources, and prompts.
    """
    
    def __init__(self, config: Any):
        """
        Initialize hot reload manager.
        
        Args:
            config: Server configuration object
        """
        self.config = config
        self.logger = get_logger("hot_reload_manager")
        
        # File system observer
        self.observer: Optional[Observer] = None
        self.handler: Optional[HotReloadHandler] = None
        
        # Reload callbacks
        self.reload_callbacks: Dict[str, Callable[[str, str], None]] = {}
        
        # Watched directories
        self.watched_dirs: Set[str] = set()
        
        # Thread safety
        self._lock = threading.Lock()
        
        # State tracking
        self.is_running = False
        self.reload_count = 0
        
        self.logger.info("Hot reload manager initialized")
    
    def register_callback(self, name: str, callback: Callable[[str, str], None]) -> None:
        """
        Register a reload callback.
        
        Args:
            name: Name of the callback
            callback: Callback function that takes (file_path, change_type)
        """
        with self._lock:
            self.reload_callbacks[name] = callback
            self.logger.debug(f"Registered reload callback: {name}")
    
    def unregister_callback(self, name: str) -> None:
        """
        Unregister a reload callback.
        
        Args:
            name: Name of the callback to remove
        """
        with self._lock:
            if name in self.reload_callbacks:
                del self.reload_callbacks[name]
                self.logger.debug(f"Unregistered reload callback: {name}")
    
    def add_watch_directory(self, directory: str) -> None:
        """
        Add a directory to watch for changes.
        
        Args:
            directory: Directory path to watch
        """
        if not os.path.exists(directory):
            self.logger.warning(f"Watch directory does not exist: {directory}")
            return
        
        abs_dir = os.path.abspath(directory)
        
        with self._lock:
            self.watched_dirs.add(abs_dir)
            self.logger.info(f"Added watch directory: {abs_dir}")
            
            # If observer is running, add the watch immediately
            if self.observer and self.observer.is_alive():
                self.observer.schedule(self.handler, abs_dir, recursive=True)
    
    def remove_watch_directory(self, directory: str) -> None:
        """
        Remove a directory from watching.
        
        Args:
            directory: Directory path to stop watching
        """
        abs_dir = os.path.abspath(directory)
        
        with self._lock:
            if abs_dir in self.watched_dirs:
                self.watched_dirs.remove(abs_dir)
                self.logger.info(f"Removed watch directory: {abs_dir}")
    
    def start(self) -> None:
        """Start the hot reload system."""
        if self.is_running:
            self.logger.warning("Hot reload manager is already running")
            return
        
        try:
            # Create file system observer
            self.observer = Observer()
            self.handler = HotReloadHandler(self._handle_file_change)
            
            # Add default watch directories
            default_dirs = [
                self.config.tools_dir,
                self.config.resource_dir,
                self.config.prompts_dir
            ]
            
            for directory in default_dirs:
                self.add_watch_directory(directory)
            
            # Schedule watches
            with self._lock:
                for watch_dir in self.watched_dirs:
                    if os.path.exists(watch_dir):
                        self.observer.schedule(self.handler, watch_dir, recursive=True)
                        self.logger.debug(f"Watching directory: {watch_dir}")
            
            # Start observer
            self.observer.start()
            self.is_running = True
            
            self.logger.info(f"Hot reload started, watching {len(self.watched_dirs)} directories")
            
        except Exception as e:
            self.logger.error(f"Failed to start hot reload: {e}")
            self.stop()
            raise
    
    def stop(self) -> None:
        """Stop the hot reload system."""
        if not self.is_running:
            return
        
        try:
            if self.observer:
                self.observer.stop()
                self.observer.join(timeout=5.0)
                
                if self.observer.is_alive():
                    self.logger.warning("Observer thread did not stop gracefully")
            
            self.observer = None
            self.handler = None
            self.is_running = False
            
            self.logger.info("Hot reload stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping hot reload: {e}")
    
    def _handle_file_change(self, file_path: str, change_type: str) -> None:
        """
        Handle file change events.
        
        Args:
            file_path: Path to the changed file
            change_type: Type of change (modified, created, deleted)
        """
        try:
            with self._lock:
                self.reload_count += 1
                
                # Determine which callbacks to trigger based on file path
                triggered_callbacks = []
                
                for callback_name, callback in self.reload_callbacks.items():
                    if self._should_trigger_callback(callback_name, file_path):
                        triggered_callbacks.append((callback_name, callback))
                
                # Execute callbacks
                for callback_name, callback in triggered_callbacks:
                    try:
                        callback(file_path, change_type)
                        self.logger.debug(f"Executed reload callback: {callback_name}")
                    except Exception as e:
                        self.logger.error(f"Error in reload callback {callback_name}: {e}")
                
                if triggered_callbacks:
                    self.logger.info(f"Processed file change: {file_path} ({change_type}) - "
                                   f"triggered {len(triggered_callbacks)} callbacks")
                
        except Exception as e:
            self.logger.error(f"Error handling file change {file_path}: {e}")
    
    def _should_trigger_callback(self, callback_name: str, file_path: str) -> bool:
        """
        Determine if a callback should be triggered for a file change.
        
        Args:
            callback_name: Name of the callback
            file_path: Path to the changed file
            
        Returns:
            True if callback should be triggered
        """
        abs_path = os.path.abspath(file_path)
        
        # Map callback names to directory patterns
        callback_patterns = {
            "tools": self.config.tools_dir,
            "resources": self.config.resource_dir,
            "prompts": self.config.prompts_dir,
            "config": self.config.config_dir if hasattr(self.config, 'config_dir') else None
        }
        
        # Check if file is in relevant directory
        for pattern_name, pattern_dir in callback_patterns.items():
            if pattern_dir and callback_name.startswith(pattern_name):
                abs_pattern_dir = os.path.abspath(pattern_dir)
                if abs_path.startswith(abs_pattern_dir):
                    return True
        
        # Default: trigger all callbacks for unmatched files
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get hot reload status information.
        
        Returns:
            Dictionary with status information
        """
        with self._lock:
            return {
                "is_running": self.is_running,
                "watched_directories": list(self.watched_dirs),
                "registered_callbacks": list(self.reload_callbacks.keys()),
                "reload_count": self.reload_count,
                "observer_alive": self.observer.is_alive() if self.observer else False
            }
    
    def force_reload(self, component: str = None) -> None:
        """
        Force a reload of specified component or all components.
        
        Args:
            component: Component to reload (tools, resources, prompts) or None for all
        """
        try:
            with self._lock:
                if component:
                    if component in self.reload_callbacks:
                        callback = self.reload_callbacks[component]
                        callback("", "force_reload")
                        self.logger.info(f"Force reloaded component: {component}")
                    else:
                        self.logger.warning(f"Unknown component for force reload: {component}")
                else:
                    # Reload all components
                    for callback_name, callback in self.reload_callbacks.items():
                        try:
                            callback("", "force_reload")
                            self.logger.debug(f"Force reloaded: {callback_name}")
                        except Exception as e:
                            self.logger.error(f"Error force reloading {callback_name}: {e}")
                    
                    self.logger.info("Force reloaded all components")
                
                self.reload_count += 1
                
        except Exception as e:
            self.logger.error(f"Error during force reload: {e}")


def create_hot_reload_manager(config: Any) -> Optional[HotReloadManager]:
    """
    Create hot reload manager if hot reload is enabled.
    
    Args:
        config: Server configuration
        
    Returns:
        HotReloadManager instance or None if disabled
    """
    if not config.hot_reload:
        return None
    
    try:
        return HotReloadManager(config)
    except ImportError:
        logger = get_logger("hot_reload")
        logger.warning("Hot reload requires 'watchdog' package. Install with: pip install watchdog")
        return None
    except Exception as e:
        logger = get_logger("hot_reload")
        logger.error(f"Failed to create hot reload manager: {e}")
        return None
