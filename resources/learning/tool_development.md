# Tool Development Guide

This guide covers how to create custom tools for the MCP Learning Server, including best practices, examples, and common patterns.

## Tool Basics

### What is a Tool?

A tool is a function that the AI assistant can call to perform specific actions. Tools have:
- A unique name
- A description of what they do
- A parameter schema defining inputs
- A return schema defining outputs
- The actual implementation function

### Tool Registration

Tools are registered using the `@tool` decorator:

```python
from tools.registry import tool

@tool(
    name="my_tool",
    description="Description of what the tool does",
    parameters={
        "param1": {"type": "string", "description": "First parameter"},
        "param2": {"type": "integer", "description": "Second parameter", "default": 0}
    },
    examples=[
        {"param1": "hello", "param2": 5, "result": "Expected output"}
    ],
    category="utility"
)
def my_tool(param1: str, param2: int = 0) -> str:
    """Implementation of the tool."""
    return f"Result: {param1} * {param2}"
```

## Parameter Schemas

### Basic Types

```python
parameters = {
    "text": {"type": "string"},
    "number": {"type": "number"},
    "count": {"type": "integer"},
    "enabled": {"type": "boolean"},
    "items": {"type": "array", "items": {"type": "string"}},
    "config": {"type": "object", "properties": {...}}
}
```

### Advanced Validation

```python
parameters = {
    "email": {
        "type": "string",
        "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        "description": "Valid email address"
    },
    "priority": {
        "type": "string",
        "enum": ["low", "medium", "high"],
        "default": "medium"
    },
    "file_size": {
        "type": "integer",
        "minimum": 1,
        "maximum": 1048576,
        "description": "File size in bytes (1B to 1MB)"
    }
}
```

## Tool Categories

### File Operations

```python
@tool(
    name="read_file",
    description="Read content from a file",
    parameters={
        "file_path": {"type": "string", "description": "Path to file"},
        "encoding": {"type": "string", "default": "utf-8"}
    },
    category="file"
)
def read_file(file_path: str, encoding: str = "utf-8") -> str:
    # Validate file path for security
    validated_path = validate_file_path(file_path)
    
    with open(validated_path, 'r', encoding=encoding) as f:
        return f.read()
```

### Data Processing

```python
@tool(
    name="parse_csv",
    description="Parse CSV data and return structured format",
    parameters={
        "csv_data": {"type": "string", "description": "CSV content"},
        "delimiter": {"type": "string", "default": ","},
        "has_header": {"type": "boolean", "default": True}
    },
    category="data"
)
def parse_csv(csv_data: str, delimiter: str = ",", has_header: bool = True) -> dict:
    import csv
    import io
    
    reader = csv.reader(io.StringIO(csv_data), delimiter=delimiter)
    rows = list(reader)
    
    if has_header and rows:
        headers = rows[0]
        data = [dict(zip(headers, row)) for row in rows[1:]]
        return {"headers": headers, "data": data, "row_count": len(data)}
    else:
        return {"data": rows, "row_count": len(rows)}
```

### API Integration

```python
@tool(
    name="http_request",
    description="Make HTTP requests to external APIs",
    parameters={
        "url": {"type": "string", "description": "Request URL"},
        "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"], "default": "GET"},
        "headers": {"type": "object", "default": {}},
        "data": {"type": "object", "default": {}}
    },
    category="api"
)
def http_request(url: str, method: str = "GET", headers: dict = None, data: dict = None) -> dict:
    import requests
    
    headers = headers or {}
    response = requests.request(method, url, headers=headers, json=data)
    
    return {
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "content": response.text,
        "json": response.json() if response.headers.get('content-type', '').startswith('application/json') else None
    }
```

## Error Handling

### Validation Errors

```python
@tool(name="divide", description="Divide two numbers")
def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Cannot divide by zero")
    
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("Arguments must be numbers")
    
    return a / b
```

### Resource Errors

```python
@tool(name="read_config", description="Read configuration file")
def read_config(config_name: str) -> dict:
    import json
    
    try:
        config_path = validate_config_path(config_name)
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise ValueError(f"Configuration file not found: {config_name}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in configuration file: {e}")
    except PermissionError:
        raise ValueError(f"Permission denied accessing configuration: {config_name}")
```

## Security Best Practices

### Input Validation

```python
def validate_file_path(file_path: str) -> str:
    """Validate file path for security."""
    import os
    
    # Normalize path
    normalized = os.path.normpath(file_path)
    
    # Check for path traversal
    if '..' in normalized or normalized.startswith('/'):
        raise ValueError("Invalid file path: path traversal not allowed")
    
    # Ensure within allowed directory
    base_dir = os.path.abspath("./resources")
    full_path = os.path.abspath(os.path.join(base_dir, normalized))
    
    if not full_path.startswith(base_dir):
        raise ValueError("Access denied: file outside allowed directory")
    
    return full_path
```

### Rate Limiting

```python
from functools import wraps
from time import time
from collections import defaultdict

def rate_limit(calls_per_minute: int = 60):
    """Decorator to rate limit tool calls."""
    call_times = defaultdict(list)
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time()
            tool_name = func.__name__
            
            # Clean old calls
            call_times[tool_name] = [
                call_time for call_time in call_times[tool_name]
                if now - call_time < 60
            ]
            
            # Check rate limit
            if len(call_times[tool_name]) >= calls_per_minute:
                raise ValueError(f"Rate limit exceeded for {tool_name}")
            
            # Record this call
            call_times[tool_name].append(now)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

@rate_limit(calls_per_minute=10)
@tool(name="expensive_operation", description="Rate-limited operation")
def expensive_operation() -> str:
    return "Operation completed"
```

## Testing Tools

### Unit Tests

```python
import pytest
from tools.my_tools import my_tool

def test_my_tool_basic():
    result = my_tool("hello", 5)
    assert result == "Result: hello * 5"

def test_my_tool_default_param():
    result = my_tool("hello")
    assert result == "Result: hello * 0"

def test_my_tool_error_handling():
    with pytest.raises(ValueError):
        my_tool("", -1)
```

### Integration Tests

```python
def test_tool_registration():
    from tools.registry import get_tool_registry
    
    registry = get_tool_registry()
    assert "my_tool" in registry
    
    tool_info = registry["my_tool"]
    assert tool_info.name == "my_tool"
    assert "param1" in tool_info.parameters

def test_tool_execution():
    from mcp_server.server import MCPServer
    
    server = MCPServer()
    # Tools are auto-registered
    
    result = server.call_tool("my_tool", {"param1": "test", "param2": 3})
    assert result == "Result: test * 3"
```

## Performance Optimization

### Caching

```python
from functools import lru_cache

@tool(name="expensive_calculation", description="Cached calculation")
@lru_cache(maxsize=128)
def expensive_calculation(input_data: str) -> str:
    # Expensive operation here
    import time
    time.sleep(1)  # Simulate expensive operation
    return f"Processed: {input_data}"
```

### Async Operations

```python
import asyncio
from typing import Awaitable

@tool(name="async_operation", description="Asynchronous operation")
def async_operation(url: str) -> str:
    """Wrapper for async operation."""
    return asyncio.run(_async_operation_impl(url))

async def _async_operation_impl(url: str) -> str:
    import aiohttp
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()
```

## Advanced Patterns

### Tool Composition

```python
@tool(name="process_file", description="Read and process file")
def process_file(file_path: str, operation: str) -> str:
    # Use other tools
    content = read_file(file_path)
    
    if operation == "word_count":
        return str(len(content.split()))
    elif operation == "line_count":
        return str(len(content.splitlines()))
    elif operation == "char_count":
        return str(len(content))
    else:
        raise ValueError(f"Unknown operation: {operation}")
```

### Dynamic Tool Generation

```python
def create_math_tool(operation_name: str, operation_func):
    """Factory function to create math tools."""
    
    @tool(
        name=f"math_{operation_name}",
        description=f"Perform {operation_name} operation",
        parameters={
            "a": {"type": "number"},
            "b": {"type": "number"}
        },
        category="math"
    )
    def math_tool(a: float, b: float) -> float:
        return operation_func(a, b)
    
    return math_tool

# Create tools dynamically
import operator
create_math_tool("add", operator.add)
create_math_tool("multiply", operator.mul)
create_math_tool("power", operator.pow)
```

## Debugging Tools

### Logging

```python
import logging

@tool(name="debug_tool", description="Tool with debug logging")
def debug_tool(input_data: str) -> str:
    logger = logging.getLogger("tools.debug_tool")
    
    logger.debug(f"Processing input: {input_data}")
    
    try:
        result = process_data(input_data)
        logger.info(f"Successfully processed data, result length: {len(result)}")
        return result
    except Exception as e:
        logger.error(f"Error processing data: {e}")
        raise
```

### Tool Introspection

```python
@tool(name="tool_info", description="Get information about available tools")
def tool_info(tool_name: str = None) -> dict:
    from tools.registry import get_tool_registry
    
    registry = get_tool_registry()
    
    if tool_name:
        if tool_name not in registry:
            raise ValueError(f"Tool not found: {tool_name}")
        
        tool = registry[tool_name]
        return {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
            "category": getattr(tool, 'category', 'unknown'),
            "examples": getattr(tool, 'examples', [])
        }
    else:
        return {
            "total_tools": len(registry),
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "category": getattr(tool, 'category', 'unknown')
                }
                for tool in registry.values()
            ]
        }
```

## Next Steps

1. **Practice**: Create simple tools and gradually add complexity
2. **Study Examples**: Review existing tools in the `tools/` directory
3. **Test Thoroughly**: Write comprehensive tests for your tools
4. **Document**: Provide clear descriptions and examples
5. **Optimize**: Profile and optimize performance-critical tools
6. **Share**: Contribute useful tools back to the community
