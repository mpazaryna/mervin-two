"""
Tests for Resource Management System

This module contains unit tests for the resource management functionality
of the MCP Learning Server.
"""

import os
import json
import tempfile
import pytest
from unittest.mock import patch, mock_open

from mcp_server.resources import ResourceManager, ResourceInfo
from mcp_server.server import MCPServer


class TestResourceInfo:
    """Test ResourceInfo class."""
    
    def test_resource_info_creation(self):
        """Test creating a ResourceInfo object."""
        resource = ResourceInfo(
            resource_id="test_resource",
            path="test/path.md",
            title="Test Resource",
            description="A test resource",
            mime_type="text/markdown",
            tags=["test", "example"]
        )
        
        assert resource.resource_id == "test_resource"
        assert resource.path == "test/path.md"
        assert resource.title == "Test Resource"
        assert resource.description == "A test resource"
        assert resource.mime_type == "text/markdown"
        assert resource.tags == ["test", "example"]
    
    def test_resource_info_to_dict(self):
        """Test converting ResourceInfo to dictionary."""
        resource = ResourceInfo(
            resource_id="test_resource",
            path="test/path.md",
            title="Test Resource",
            description="A test resource"
        )
        
        result = resource.to_dict()
        
        assert result["id"] == "test_resource"
        assert result["path"] == "test/path.md"
        assert result["title"] == "Test Resource"
        assert result["description"] == "A test resource"
        assert result["mime_type"] == "text/plain"
        assert result["tags"] == []
        assert "created_at" in result


class TestResourceManager:
    """Test ResourceManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.resource_manager = ResourceManager(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_resource_manager_initialization(self):
        """Test ResourceManager initialization."""
        assert self.resource_manager.resource_dir == self.temp_dir
        assert isinstance(self.resource_manager.resources, dict)
        assert isinstance(self.resource_manager.cache, dict)
        assert self.resource_manager.max_cache_size == 100
    
    def test_load_resource_index_missing_file(self):
        """Test loading resources when index.json doesn't exist."""
        # ResourceManager should handle missing index gracefully
        assert len(self.resource_manager.resources) == 0
    
    def test_load_resource_index_valid_file(self):
        """Test loading resources from valid index.json."""
        # Create test index file
        index_data = {
            "test_resource": {
                "path": "test.md",
                "title": "Test Resource",
                "description": "A test resource",
                "mime_type": "text/markdown",
                "tags": ["test"]
            }
        }
        
        index_path = os.path.join(self.temp_dir, "index.json")
        with open(index_path, 'w') as f:
            json.dump(index_data, f)
        
        # Reload the resource manager
        self.resource_manager._load_resource_index()
        
        assert "test_resource" in self.resource_manager.resources
        resource = self.resource_manager.resources["test_resource"]
        assert resource.resource_id == "test_resource"
        assert resource.path == "test.md"
        assert resource.title == "Test Resource"
    
    def test_validate_resource_path_valid(self):
        """Test path validation with valid path."""
        valid_path = self.resource_manager._validate_resource_path("test.md")
        expected_path = os.path.join(self.temp_dir, "test.md")
        assert valid_path == expected_path
    
    def test_validate_resource_path_traversal_attack(self):
        """Test path validation prevents directory traversal."""
        with pytest.raises(ValueError, match="Access denied"):
            self.resource_manager._validate_resource_path("../../../etc/passwd")
    
    def test_get_resource_not_found(self):
        """Test getting a resource that doesn't exist."""
        with pytest.raises(ValueError, match="Resource not found"):
            self.resource_manager.get_resource("nonexistent")
    
    def test_get_resource_success(self):
        """Test successfully getting a resource."""
        # Create test resource
        test_content = "# Test Resource\n\nThis is a test."
        test_file = os.path.join(self.temp_dir, "test.md")
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        # Add to index
        self.resource_manager.resources["test_resource"] = ResourceInfo(
            resource_id="test_resource",
            path="test.md",
            title="Test Resource",
            description="A test resource"
        )
        
        # Get resource
        content = self.resource_manager.get_resource("test_resource")
        assert content == test_content
    
    def test_get_resource_caching(self):
        """Test resource caching functionality."""
        # Create test resource
        test_content = "# Test Resource\n\nThis is a test."
        test_file = os.path.join(self.temp_dir, "test.md")
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        # Add to index
        self.resource_manager.resources["test_resource"] = ResourceInfo(
            resource_id="test_resource",
            path="test.md",
            title="Test Resource",
            description="A test resource"
        )
        
        # First call should read from file
        content1 = self.resource_manager.get_resource("test_resource")
        assert "test_resource" in self.resource_manager.cache
        
        # Second call should use cache
        content2 = self.resource_manager.get_resource("test_resource")
        assert content1 == content2
    
    def test_list_resources(self):
        """Test listing all resources."""
        # Add test resources
        self.resource_manager.resources["resource1"] = ResourceInfo(
            resource_id="resource1",
            path="test1.md",
            title="Resource 1",
            description="First resource"
        )
        self.resource_manager.resources["resource2"] = ResourceInfo(
            resource_id="resource2",
            path="test2.md",
            title="Resource 2",
            description="Second resource"
        )
        
        resources = self.resource_manager.list_resources()
        assert len(resources) == 2
        
        resource_ids = [r["id"] for r in resources]
        assert "resource1" in resource_ids
        assert "resource2" in resource_ids
    
    def test_search_resources_by_query(self):
        """Test searching resources by query string."""
        # Add test resources
        self.resource_manager.resources["mcp_guide"] = ResourceInfo(
            resource_id="mcp_guide",
            path="mcp.md",
            title="MCP Guide",
            description="Guide to Model Context Protocol"
        )
        self.resource_manager.resources["api_docs"] = ResourceInfo(
            resource_id="api_docs",
            path="api.md",
            title="API Documentation",
            description="Complete API reference"
        )
        
        # Search by title
        results = self.resource_manager.search_resources(query="MCP")
        assert len(results) == 1
        assert results[0]["id"] == "mcp_guide"
        
        # Search by description
        results = self.resource_manager.search_resources(query="API")
        assert len(results) == 1
        assert results[0]["id"] == "api_docs"
    
    def test_search_resources_by_tags(self):
        """Test searching resources by tags."""
        # Add test resources
        self.resource_manager.resources["tutorial"] = ResourceInfo(
            resource_id="tutorial",
            path="tutorial.md",
            title="Tutorial",
            description="Getting started tutorial",
            tags=["tutorial", "beginner"]
        )
        self.resource_manager.resources["advanced"] = ResourceInfo(
            resource_id="advanced",
            path="advanced.md",
            title="Advanced Guide",
            description="Advanced concepts",
            tags=["advanced", "expert"]
        )
        
        # Search by tag
        results = self.resource_manager.search_resources(tags=["tutorial"])
        assert len(results) == 1
        assert results[0]["id"] == "tutorial"
        
        results = self.resource_manager.search_resources(tags=["advanced"])
        assert len(results) == 1
        assert results[0]["id"] == "advanced"
    
    def test_clear_cache(self):
        """Test clearing the resource cache."""
        # Add something to cache
        self.resource_manager.cache["test"] = "content"
        self.resource_manager.cache_timestamps["test"] = 123456789
        
        assert len(self.resource_manager.cache) == 1
        
        self.resource_manager.clear_cache()
        
        assert len(self.resource_manager.cache) == 0
        assert len(self.resource_manager.cache_timestamps) == 0
    
    def test_get_cache_stats(self):
        """Test getting cache statistics."""
        # Add test resources
        self.resource_manager.resources["resource1"] = ResourceInfo(
            resource_id="resource1",
            path="test1.md",
            title="Resource 1",
            description="First resource"
        )
        
        # Add to cache
        self.resource_manager.cache["resource1"] = "content"
        
        stats = self.resource_manager.get_cache_stats()
        
        assert stats["cached_resources"] == 1
        assert stats["max_cache_size"] == 100
        assert stats["total_resources"] == 1
        assert stats["cache_usage_percent"] == 1.0


class TestMCPServerResourceIntegration:
    """Test resource integration with MCP Server."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.server = MCPServer(debug=True, resource_dir=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_server_has_resource_manager(self):
        """Test that server has resource manager."""
        assert hasattr(self.server, 'resource_manager')
        assert isinstance(self.server.resource_manager, ResourceManager)
    
    def test_server_capabilities_include_resources(self):
        """Test that server capabilities include resources."""
        # Initialize server
        init_message = {
            "type": "initialize",
            "id": "1",
            "params": {"protocolVersion": "2024-11-05", "capabilities": {}}
        }
        
        response = self.server.handle_message(init_message)
        
        assert response["result"]["capabilities"]["resources"] is True
