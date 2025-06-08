"""
Resource Management System

This module provides resource management capabilities for the MCP Learning Server,
including resource registration, loading, caching, and serving educational content.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

from .logging_config import get_logger


class ResourceInfo:
    """Information about a resource."""
    
    def __init__(self, resource_id: str, path: str, title: str, 
                 description: str, mime_type: str = "text/plain", 
                 tags: List[str] = None):
        """
        Initialize resource info.
        
        Args:
            resource_id: Unique identifier for the resource
            path: Relative path to the resource file
            title: Human-readable title
            description: Description of the resource
            mime_type: MIME type of the resource
            tags: Optional tags for categorization
        """
        self.resource_id = resource_id
        self.path = path
        self.title = title
        self.description = description
        self.mime_type = mime_type
        self.tags = tags or []
        self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.resource_id,
            "path": self.path,
            "title": self.title,
            "description": self.description,
            "mime_type": self.mime_type,
            "tags": self.tags,
            "created_at": self.created_at
        }


class ResourceManager:
    """
    Resource management system for MCP Learning Server.
    
    Handles resource registration, loading, caching, and serving of educational
    content and example configurations.
    """
    
    def __init__(self, resource_dir: str = "./resources"):
        """
        Initialize the resource manager.
        
        Args:
            resource_dir: Base directory for resources
        """
        self.resource_dir = os.path.abspath(resource_dir)
        self.logger = get_logger("resource_manager")
        
        # Resource registry and cache
        self.resources: Dict[str, ResourceInfo] = {}
        self.cache: Dict[str, str] = {}
        self.cache_timestamps: Dict[str, float] = {}
        
        # Configuration
        self.max_cache_size = 100  # Maximum number of cached resources
        self.max_file_size = 10 * 1024 * 1024  # 10MB max file size
        
        # Load resources from index
        self._load_resource_index()
        
        self.logger.info(f"ResourceManager initialized with {len(self.resources)} resources")
    
    def _load_resource_index(self) -> None:
        """Load resource definitions from index.json file."""
        index_path = os.path.join(self.resource_dir, "index.json")
        
        try:
            if os.path.exists(index_path):
                with open(index_path, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
                
                # Parse resource definitions
                for resource_id, resource_data in index_data.items():
                    resource_info = ResourceInfo(
                        resource_id=resource_id,
                        path=resource_data["path"],
                        title=resource_data.get("title", resource_id),
                        description=resource_data.get("description", ""),
                        mime_type=resource_data.get("mime_type", "text/plain"),
                        tags=resource_data.get("tags", [])
                    )
                    self.resources[resource_id] = resource_info
                
                self.logger.info(f"Loaded {len(self.resources)} resources from index")
            else:
                self.logger.warning(f"Resource index not found at {index_path}")
                
        except Exception as e:
            self.logger.error(f"Failed to load resource index: {e}")
            self.resources = {}
    
    def _validate_resource_path(self, resource_path: str) -> str:
        """
        Validate and normalize resource file path for security.
        
        Args:
            resource_path: Relative path to resource file
            
        Returns:
            Absolute path within resources directory
            
        Raises:
            ValueError: If path is outside resources directory
        """
        # Normalize the path and make it absolute
        abs_path = os.path.abspath(os.path.join(self.resource_dir, resource_path))
        
        # Security check - ensure path is within resources directory
        if not abs_path.startswith(self.resource_dir):
            raise ValueError(f"Access denied: Cannot access files outside resources directory")
        
        return abs_path
    
    def get_resource(self, resource_id: str, use_cache: bool = True) -> str:
        """
        Get resource content by ID.
        
        Args:
            resource_id: Unique identifier for the resource
            use_cache: Whether to use cached content if available
            
        Returns:
            Resource content as string
            
        Raises:
            ValueError: If resource not found or cannot be loaded
        """
        if resource_id not in self.resources:
            raise ValueError(f"Resource not found: {resource_id}")
        
        # Check cache first
        if use_cache and resource_id in self.cache:
            self.logger.debug(f"Returning cached resource: {resource_id}")
            return self.cache[resource_id]
        
        # Load resource from file
        resource_info = self.resources[resource_id]
        resource_path = self._validate_resource_path(resource_info.path)
        
        try:
            # Check if file exists
            if not os.path.isfile(resource_path):
                raise ValueError(f"Resource file not found: {resource_info.path}")
            
            # Check file size
            file_size = os.path.getsize(resource_path)
            if file_size > self.max_file_size:
                raise ValueError(f"Resource file too large: {file_size} bytes (max: {self.max_file_size} bytes)")
            
            # Read the file
            with open(resource_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Cache the content
            if use_cache:
                self._cache_resource(resource_id, content)
            
            self.logger.debug(f"Loaded resource: {resource_id}")
            return content
            
        except Exception as e:
            self.logger.error(f"Error loading resource {resource_id}: {e}")
            raise ValueError(f"Error loading resource {resource_id}: {str(e)}")

    def _cache_resource(self, resource_id: str, content: str) -> None:
        """
        Cache resource content with size management.

        Args:
            resource_id: Resource identifier
            content: Resource content to cache
        """
        # Check cache size and evict oldest if necessary
        if len(self.cache) >= self.max_cache_size:
            # Find oldest cached resource
            oldest_id = min(self.cache_timestamps.keys(),
                          key=lambda k: self.cache_timestamps[k])
            del self.cache[oldest_id]
            del self.cache_timestamps[oldest_id]
            self.logger.debug(f"Evicted cached resource: {oldest_id}")

        # Cache the resource
        self.cache[resource_id] = content
        self.cache_timestamps[resource_id] = datetime.now().timestamp()
        self.logger.debug(f"Cached resource: {resource_id}")

    def list_resources(self) -> List[Dict[str, Any]]:
        """
        List all available resources.

        Returns:
            List of resource information dictionaries
        """
        return [resource_info.to_dict() for resource_info in self.resources.values()]

    def get_resource_info(self, resource_id: str) -> ResourceInfo:
        """
        Get resource information without loading content.

        Args:
            resource_id: Unique identifier for the resource

        Returns:
            ResourceInfo object

        Raises:
            ValueError: If resource not found
        """
        if resource_id not in self.resources:
            raise ValueError(f"Resource not found: {resource_id}")

        return self.resources[resource_id]

    def search_resources(self, query: str = None, tags: List[str] = None) -> List[Dict[str, Any]]:
        """
        Search resources by query string or tags.

        Args:
            query: Search query (searches title and description)
            tags: List of tags to filter by

        Returns:
            List of matching resource information dictionaries
        """
        results = []

        for resource_info in self.resources.values():
            # Check tag filter
            if tags and not any(tag in resource_info.tags for tag in tags):
                continue

            # Check query filter
            if query:
                query_lower = query.lower()
                if (query_lower not in resource_info.title.lower() and
                    query_lower not in resource_info.description.lower()):
                    continue

            results.append(resource_info.to_dict())

        return results

    def clear_cache(self) -> None:
        """Clear all cached resources."""
        self.cache.clear()
        self.cache_timestamps.clear()
        self.logger.info("Resource cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "cached_resources": len(self.cache),
            "max_cache_size": self.max_cache_size,
            "cache_usage_percent": (len(self.cache) / self.max_cache_size) * 100,
            "total_resources": len(self.resources)
        }

    def reload_index(self) -> None:
        """Reload the resource index from disk."""
        self.logger.info("Reloading resource index")
        self.resources.clear()
        self.clear_cache()
        self._load_resource_index()
        self.logger.info(f"Resource index reloaded with {len(self.resources)} resources")
