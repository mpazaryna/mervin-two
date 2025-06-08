"""
Tests for Prompt Management System

This module contains unit tests for the prompt management functionality
of the MCP Learning Server.
"""

import os
import json
import tempfile
import pytest
from unittest.mock import patch, mock_open

from mcp_server.prompts import PromptManager, PromptInfo
from mcp_server.server import MCPServer


class TestPromptInfo:
    """Test PromptInfo class."""
    
    def test_prompt_info_creation(self):
        """Test creating a PromptInfo object."""
        prompt = PromptInfo(
            prompt_id="test_prompt",
            title="Test Prompt",
            description="A test prompt",
            template="Hello {{name}}!",
            parameters=[{"name": "name", "type": "string", "required": True}],
            examples=[{"name": "World", "result": "Hello World!"}],
            tags=["test", "example"]
        )
        
        assert prompt.prompt_id == "test_prompt"
        assert prompt.title == "Test Prompt"
        assert prompt.description == "A test prompt"
        assert prompt.template == "Hello {{name}}!"
        assert len(prompt.parameters) == 1
        assert len(prompt.examples) == 1
        assert prompt.tags == ["test", "example"]
    
    def test_prompt_info_to_dict(self):
        """Test converting PromptInfo to dictionary."""
        prompt = PromptInfo(
            prompt_id="test_prompt",
            title="Test Prompt",
            description="A test prompt",
            template="Hello {{name}}!"
        )
        
        result = prompt.to_dict()
        
        assert result["id"] == "test_prompt"
        assert result["title"] == "Test Prompt"
        assert result["description"] == "A test prompt"
        assert result["parameters"] == []
        assert result["examples"] == []
        assert result["tags"] == []
        assert "created_at" in result


class TestPromptManager:
    """Test PromptManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.prompt_manager = PromptManager(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_prompt_manager_initialization(self):
        """Test PromptManager initialization."""
        assert self.prompt_manager.prompt_dir == self.temp_dir
        assert isinstance(self.prompt_manager.prompts, dict)
    
    def test_load_prompts_missing_directory(self):
        """Test loading prompts when directory doesn't exist."""
        # PromptManager should handle missing directory gracefully
        assert len(self.prompt_manager.prompts) == 0
    
    def test_load_prompts_valid_file(self):
        """Test loading prompts from valid JSON file."""
        # Create test prompt file
        prompt_data = {
            "title": "Test Prompt",
            "description": "A test prompt",
            "template": "Hello {{name}}!",
            "parameters": [
                {"name": "name", "type": "string", "required": True}
            ],
            "examples": [
                {"name": "World", "result": "Hello World!"}
            ],
            "tags": ["test"]
        }
        
        prompt_path = os.path.join(self.temp_dir, "test_prompt.json")
        with open(prompt_path, 'w') as f:
            json.dump(prompt_data, f)
        
        # Reload the prompt manager
        self.prompt_manager._load_prompts()
        
        assert "test_prompt" in self.prompt_manager.prompts
        prompt = self.prompt_manager.prompts["test_prompt"]
        assert prompt.prompt_id == "test_prompt"
        assert prompt.title == "Test Prompt"
        assert prompt.template == "Hello {{name}}!"
    
    def test_get_prompt_not_found(self):
        """Test getting a prompt that doesn't exist."""
        with pytest.raises(ValueError, match="Prompt not found"):
            self.prompt_manager.get_prompt("nonexistent")
    
    def test_get_prompt_success(self):
        """Test successfully getting and rendering a prompt."""
        # Add test prompt
        self.prompt_manager.prompts["test_prompt"] = PromptInfo(
            prompt_id="test_prompt",
            title="Test Prompt",
            description="A test prompt",
            template="Hello {{name}}! You are {{age}} years old."
        )
        
        # Get prompt with arguments
        result = self.prompt_manager.get_prompt("test_prompt", {
            "name": "Alice",
            "age": "25"
        })
        
        assert result == "Hello Alice! You are 25 years old."
    
    def test_render_template_basic(self):
        """Test basic template rendering."""
        template = "Hello {{name}}!"
        arguments = {"name": "World"}
        
        result = self.prompt_manager._render_template(template, arguments)
        assert result == "Hello World!"
    
    def test_render_template_missing_argument(self):
        """Test template rendering with missing argument."""
        template = "Hello {{name}}! You are {{age}} years old."
        arguments = {"name": "Alice"}
        
        result = self.prompt_manager._render_template(template, arguments)
        assert result == "Hello Alice! You are {{age}} years old."
    
    def test_render_template_multiple_placeholders(self):
        """Test template rendering with multiple placeholders."""
        template = "{{greeting}} {{name}}! Today is {{day}}."
        arguments = {
            "greeting": "Hello",
            "name": "Alice",
            "day": "Monday"
        }
        
        result = self.prompt_manager._render_template(template, arguments)
        assert result == "Hello Alice! Today is Monday."
    
    def test_list_prompts(self):
        """Test listing all prompts."""
        # Add test prompts
        self.prompt_manager.prompts["prompt1"] = PromptInfo(
            prompt_id="prompt1",
            title="Prompt 1",
            description="First prompt",
            template="Template 1"
        )
        self.prompt_manager.prompts["prompt2"] = PromptInfo(
            prompt_id="prompt2",
            title="Prompt 2",
            description="Second prompt",
            template="Template 2"
        )
        
        prompts = self.prompt_manager.list_prompts()
        assert len(prompts) == 2
        
        prompt_ids = [p["id"] for p in prompts]
        assert "prompt1" in prompt_ids
        assert "prompt2" in prompt_ids
    
    def test_search_prompts_by_query(self):
        """Test searching prompts by query string."""
        # Add test prompts
        self.prompt_manager.prompts["mcp_guide"] = PromptInfo(
            prompt_id="mcp_guide",
            title="MCP Guide",
            description="Guide to Model Context Protocol",
            template="MCP template"
        )
        self.prompt_manager.prompts["api_docs"] = PromptInfo(
            prompt_id="api_docs",
            title="API Documentation",
            description="Complete API reference",
            template="API template"
        )
        
        # Search by title
        results = self.prompt_manager.search_prompts(query="MCP")
        assert len(results) == 1
        assert results[0]["id"] == "mcp_guide"
        
        # Search by description
        results = self.prompt_manager.search_prompts(query="API")
        assert len(results) == 1
        assert results[0]["id"] == "api_docs"
    
    def test_search_prompts_by_tags(self):
        """Test searching prompts by tags."""
        # Add test prompts
        self.prompt_manager.prompts["tutorial"] = PromptInfo(
            prompt_id="tutorial",
            title="Tutorial",
            description="Getting started tutorial",
            template="Tutorial template",
            tags=["tutorial", "beginner"]
        )
        self.prompt_manager.prompts["advanced"] = PromptInfo(
            prompt_id="advanced",
            title="Advanced Guide",
            description="Advanced concepts",
            template="Advanced template",
            tags=["advanced", "expert"]
        )
        
        # Search by tag
        results = self.prompt_manager.search_prompts(tags=["tutorial"])
        assert len(results) == 1
        assert results[0]["id"] == "tutorial"
        
        results = self.prompt_manager.search_prompts(tags=["advanced"])
        assert len(results) == 1
        assert results[0]["id"] == "advanced"
    
    def test_validate_prompt_arguments(self):
        """Test prompt argument validation."""
        # Add test prompt with parameters
        self.prompt_manager.prompts["test_prompt"] = PromptInfo(
            prompt_id="test_prompt",
            title="Test Prompt",
            description="A test prompt",
            template="Hello {{name}}!",
            parameters=[
                {"name": "name", "type": "string", "required": True},
                {"name": "age", "type": "number", "required": False}
            ]
        )
        
        # Valid arguments
        errors = self.prompt_manager.validate_prompt_arguments("test_prompt", {
            "name": "Alice",
            "age": 25
        })
        assert len(errors) == 0
        
        # Missing required parameter
        errors = self.prompt_manager.validate_prompt_arguments("test_prompt", {
            "age": 25
        })
        assert len(errors) == 1
        assert "Required parameter missing: name" in errors
        
        # Wrong type
        errors = self.prompt_manager.validate_prompt_arguments("test_prompt", {
            "name": "Alice",
            "age": "twenty-five"  # Should be number
        })
        assert len(errors) == 1
        assert "Parameter age must be a number" in errors
    
    def test_get_prompt_info(self):
        """Test getting prompt information."""
        # Add test prompt
        prompt_info = PromptInfo(
            prompt_id="test_prompt",
            title="Test Prompt",
            description="A test prompt",
            template="Hello {{name}}!"
        )
        self.prompt_manager.prompts["test_prompt"] = prompt_info
        
        result = self.prompt_manager.get_prompt_info("test_prompt")
        assert result == prompt_info
        
        # Test not found
        with pytest.raises(ValueError, match="Prompt not found"):
            self.prompt_manager.get_prompt_info("nonexistent")


class TestMCPServerPromptIntegration:
    """Test prompt integration with MCP Server."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.server = MCPServer(debug=True, prompt_dir=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_server_has_prompt_manager(self):
        """Test that server has prompt manager."""
        assert hasattr(self.server, 'prompt_manager')
        assert isinstance(self.server.prompt_manager, PromptManager)
    
    def test_server_capabilities_include_prompts(self):
        """Test that server capabilities include prompts."""
        # Initialize server
        init_message = {
            "type": "initialize",
            "id": "1",
            "params": {"protocolVersion": "2024-11-05", "capabilities": {}}
        }
        
        response = self.server.handle_message(init_message)
        
        assert response["result"]["capabilities"]["prompts"] is True
