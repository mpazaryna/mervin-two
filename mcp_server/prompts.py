"""
Prompt Management System

This module provides prompt management capabilities for the MCP Learning Server,
including prompt registration, template rendering, and serving interactive prompts.
"""

import os
import json
import logging
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

from .logging_config import get_logger


class PromptInfo:
    """Information about a prompt."""
    
    def __init__(self, prompt_id: str, title: str, description: str, 
                 template: str, parameters: List[Dict[str, Any]] = None,
                 examples: List[Dict[str, Any]] = None, tags: List[str] = None):
        """
        Initialize prompt info.
        
        Args:
            prompt_id: Unique identifier for the prompt
            title: Human-readable title
            description: Description of the prompt
            template: Template string with placeholders
            parameters: List of parameter definitions
            examples: List of usage examples
            tags: Optional tags for categorization
        """
        self.prompt_id = prompt_id
        self.title = title
        self.description = description
        self.template = template
        self.parameters = parameters or []
        self.examples = examples or []
        self.tags = tags or []
        self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.prompt_id,
            "title": self.title,
            "description": self.description,
            "parameters": self.parameters,
            "examples": self.examples,
            "tags": self.tags,
            "created_at": self.created_at
        }


class PromptManager:
    """
    Prompt management system for MCP Learning Server.
    
    Handles prompt registration, template rendering, and serving of interactive
    prompts for MCP concept explanations and code examples.
    """
    
    def __init__(self, prompt_dir: str = "./prompts"):
        """
        Initialize the prompt manager.
        
        Args:
            prompt_dir: Base directory for prompt templates
        """
        self.prompt_dir = os.path.abspath(prompt_dir)
        self.logger = get_logger("prompt_manager")
        
        # Prompt registry
        self.prompts: Dict[str, PromptInfo] = {}
        
        # Template rendering configuration
        self.placeholder_pattern = re.compile(r'\{\{(\w+)\}\}')
        
        # Load prompts from directory
        self._load_prompts()
        
        self.logger.info(f"PromptManager initialized with {len(self.prompts)} prompts")
    
    def _load_prompts(self) -> None:
        """Load prompt definitions from JSON files in prompt directory."""
        if not os.path.exists(self.prompt_dir):
            self.logger.warning(f"Prompt directory not found: {self.prompt_dir}")
            return
        
        try:
            for filename in os.listdir(self.prompt_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.prompt_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            prompt_data = json.load(f)
                        
                        # Extract prompt ID from filename
                        prompt_id = os.path.splitext(filename)[0]
                        
                        # Create PromptInfo object
                        prompt_info = PromptInfo(
                            prompt_id=prompt_id,
                            title=prompt_data.get("title", prompt_id),
                            description=prompt_data.get("description", ""),
                            template=prompt_data.get("template", ""),
                            parameters=prompt_data.get("parameters", []),
                            examples=prompt_data.get("examples", []),
                            tags=prompt_data.get("tags", [])
                        )
                        
                        self.prompts[prompt_id] = prompt_info
                        self.logger.debug(f"Loaded prompt: {prompt_id}")
                        
                    except Exception as e:
                        self.logger.error(f"Failed to load prompt {filename}: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error loading prompts from {self.prompt_dir}: {e}")
    
    def get_prompt(self, prompt_id: str, arguments: Dict[str, Any] = None) -> str:
        """
        Get rendered prompt by ID with parameter substitution.
        
        Args:
            prompt_id: Unique identifier for the prompt
            arguments: Dictionary of arguments for template substitution
            
        Returns:
            Rendered prompt string
            
        Raises:
            ValueError: If prompt not found or rendering fails
        """
        if prompt_id not in self.prompts:
            raise ValueError(f"Prompt not found: {prompt_id}")
        
        prompt_info = self.prompts[prompt_id]
        template = prompt_info.template
        arguments = arguments or {}
        
        try:
            # Render template with arguments
            rendered = self._render_template(template, arguments)
            
            self.logger.debug(f"Rendered prompt: {prompt_id}")
            return rendered
            
        except Exception as e:
            self.logger.error(f"Error rendering prompt {prompt_id}: {e}")
            raise ValueError(f"Failed to render prompt {prompt_id}: {str(e)}")
    
    def _render_template(self, template: str, arguments: Dict[str, Any]) -> str:
        """
        Render template string with argument substitution.
        
        Args:
            template: Template string with {{placeholder}} syntax
            arguments: Dictionary of values for substitution
            
        Returns:
            Rendered string
        """
        def replace_placeholder(match):
            placeholder = match.group(1)
            if placeholder in arguments:
                return str(arguments[placeholder])
            else:
                # Keep placeholder if no value provided
                return match.group(0)
        
        return self.placeholder_pattern.sub(replace_placeholder, template)
    
    def list_prompts(self) -> List[Dict[str, Any]]:
        """
        List all available prompts.
        
        Returns:
            List of prompt information dictionaries
        """
        return [prompt_info.to_dict() for prompt_info in self.prompts.values()]
    
    def get_prompt_info(self, prompt_id: str) -> PromptInfo:
        """
        Get prompt information without rendering.
        
        Args:
            prompt_id: Unique identifier for the prompt
            
        Returns:
            PromptInfo object
            
        Raises:
            ValueError: If prompt not found
        """
        if prompt_id not in self.prompts:
            raise ValueError(f"Prompt not found: {prompt_id}")
        
        return self.prompts[prompt_id]
    
    def search_prompts(self, query: str = None, tags: List[str] = None) -> List[Dict[str, Any]]:
        """
        Search prompts by query string or tags.
        
        Args:
            query: Search query (searches title and description)
            tags: List of tags to filter by
            
        Returns:
            List of matching prompt information dictionaries
        """
        results = []
        
        for prompt_info in self.prompts.values():
            # Check tag filter
            if tags and not any(tag in prompt_info.tags for tag in tags):
                continue
            
            # Check query filter
            if query:
                query_lower = query.lower()
                if (query_lower not in prompt_info.title.lower() and 
                    query_lower not in prompt_info.description.lower()):
                    continue
            
            results.append(prompt_info.to_dict())
        
        return results
    
    def validate_prompt_arguments(self, prompt_id: str, arguments: Dict[str, Any]) -> List[str]:
        """
        Validate arguments against prompt parameter definitions.
        
        Args:
            prompt_id: Unique identifier for the prompt
            arguments: Arguments to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        if prompt_id not in self.prompts:
            return [f"Prompt not found: {prompt_id}"]
        
        prompt_info = self.prompts[prompt_id]
        errors = []
        
        # Check required parameters
        for param in prompt_info.parameters:
            param_name = param.get("name")
            param_required = param.get("required", False)
            param_type = param.get("type", "string")
            
            if param_required and param_name not in arguments:
                errors.append(f"Required parameter missing: {param_name}")
                continue
            
            if param_name in arguments:
                value = arguments[param_name]
                
                # Basic type checking
                if param_type == "string" and not isinstance(value, str):
                    errors.append(f"Parameter {param_name} must be a string")
                elif param_type == "number" and not isinstance(value, (int, float)):
                    errors.append(f"Parameter {param_name} must be a number")
                elif param_type == "boolean" and not isinstance(value, bool):
                    errors.append(f"Parameter {param_name} must be a boolean")
                elif param_type == "array" and not isinstance(value, list):
                    errors.append(f"Parameter {param_name} must be an array")
        
        return errors
    
    def reload_prompts(self) -> None:
        """Reload all prompts from disk."""
        self.logger.info("Reloading prompts")
        self.prompts.clear()
        self._load_prompts()
        self.logger.info(f"Prompts reloaded with {len(self.prompts)} prompts")
