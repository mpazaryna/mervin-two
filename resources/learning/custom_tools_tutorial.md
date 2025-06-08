# Tutorial: Creating Custom Tools

This hands-on tutorial will guide you through creating custom tools for the MCP Learning Server, from simple utilities to advanced integrations.

## Prerequisites

- MCP Learning Server set up and running
- Basic Python knowledge
- Text editor or IDE

## Tutorial 1: Simple Text Tool

Let's create a tool that reverses text.

### Step 1: Create the Tool File

Create `tools/text_tools.py`:

```python
from tools.registry import tool

@tool(
    name="reverse_text",
    description="Reverse the order of characters in text",
    parameter_schema={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Text to reverse"
            }
        },
        "required": ["text"]
    },
    return_schema={
        "type": "string",
        "description": "Reversed text"
    },
    examples=[
        {"text": "hello", "result": "olleh"},
        {"text": "MCP Learning", "result": "gninraeL PCM"}
    ],
    category="text"
)
def reverse_text(text: str) -> str:
    """Reverse the characters in the given text."""
    return text[::-1]
```

### Step 2: Register the Tool

Add to `tools/__init__.py`:

```python
from . import text_tools
```

### Step 3: Test the Tool

1. Restart the server (or use hot reload)
2. In Claude Desktop: "Reverse the text 'Hello World'"
3. Expected result: "dlroW olleH"

## Tutorial 2: Data Processing Tool

Create a tool that analyzes CSV data.

### Step 1: Create the Tool

Add to `tools/text_tools.py`:

```python
import csv
import io
from typing import Dict, List, Any

@tool(
    name="csv_analyzer",
    description="Analyze CSV data and provide statistics",
    parameter_schema={
        "type": "object",
        "properties": {
            "csv_data": {
                "type": "string",
                "description": "CSV data as string"
            },
            "delimiter": {
                "type": "string",
                "default": ",",
                "description": "CSV delimiter"
            }
        },
        "required": ["csv_data"]
    },
    return_schema={
        "type": "object",
        "description": "CSV analysis results"
    },
    examples=[
        {
            "csv_data": "name,age\nAlice,25\nBob,30",
            "result": {
                "rows": 2,
                "columns": 2,
                "headers": ["name", "age"]
            }
        }
    ],
    category="data"
)
def csv_analyzer(csv_data: str, delimiter: str = ",") -> Dict[str, Any]:
    """Analyze CSV data and return statistics."""
    try:
        # Parse CSV
        reader = csv.reader(io.StringIO(csv_data), delimiter=delimiter)
        rows = list(reader)
        
        if not rows:
            return {"error": "No data found"}
        
        headers = rows[0]
        data_rows = rows[1:]
        
        # Basic statistics
        result = {
            "total_rows": len(rows),
            "data_rows": len(data_rows),
            "columns": len(headers),
            "headers": headers,
            "sample_data": data_rows[:3] if data_rows else []
        }
        
        # Column analysis
        if data_rows:
            column_stats = {}
            for i, header in enumerate(headers):
                values = [row[i] if i < len(row) else "" for row in data_rows]
                column_stats[header] = {
                    "non_empty": sum(1 for v in values if v.strip()),
                    "unique_values": len(set(values)),
                    "sample_values": list(set(values))[:5]
                }
            result["column_analysis"] = column_stats
        
        return result
        
    except Exception as e:
        return {"error": f"CSV parsing error: {str(e)}"}
```

### Step 2: Test with Real Data

1. Create a test CSV file in `resources/data.csv`
2. In Claude Desktop: "Read data.csv and analyze it"
3. The server will read the file and analyze its structure

## Tutorial 3: API Integration Tool

Create a tool that fetches data from an external API.

### Step 1: Add Dependencies

Add to `requirements.txt`:
```
requests>=2.28.0
```

Install: `pip install requests`

### Step 2: Create the API Tool

Create `tools/api_tools.py`:

```python
import requests
from typing import Dict, Any, Optional
from tools.registry import tool

@tool(
    name="weather_info",
    description="Get weather information for a city (demo with httpbin)",
    parameter_schema={
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City name"
            },
            "units": {
                "type": "string",
                "enum": ["metric", "imperial"],
                "default": "metric",
                "description": "Temperature units"
            }
        },
        "required": ["city"]
    },
    return_schema={
        "type": "object",
        "description": "Weather information"
    },
    examples=[
        {
            "city": "London",
            "units": "metric",
            "result": {"city": "London", "temperature": "15°C", "status": "demo"}
        }
    ],
    category="api"
)
def weather_info(city: str, units: str = "metric") -> Dict[str, Any]:
    """Get weather information (demo implementation)."""
    try:
        # Demo implementation using httpbin for testing
        # In a real implementation, you'd use a weather API
        response = requests.get(
            "https://httpbin.org/json",
            timeout=10
        )
        
        if response.status_code == 200:
            # Simulate weather data
            temp_symbol = "°C" if units == "metric" else "°F"
            demo_temp = "15" if units == "metric" else "59"
            
            return {
                "city": city,
                "temperature": f"{demo_temp}{temp_symbol}",
                "description": "Demo weather data",
                "units": units,
                "status": "success",
                "note": "This is a demo implementation"
            }
        else:
            return {"error": f"API request failed: {response.status_code}"}
            
    except requests.RequestException as e:
        return {"error": f"Network error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
```

### Step 3: Register and Test

1. Add `from . import api_tools` to `tools/__init__.py`
2. Restart server
3. Test: "What's the weather in Paris?"

## Tutorial 4: File Processing Tool

Create a tool that processes files with different formats.

### Step 1: Create File Processor

Add to `tools/text_tools.py`:

```python
import json
import os
from typing import Dict, Any

@tool(
    name="file_processor",
    description="Process files and extract information",
    parameter_schema={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to file in resources directory"
            },
            "operation": {
                "type": "string",
                "enum": ["info", "preview", "word_count", "line_count"],
                "description": "Operation to perform"
            },
            "lines": {
                "type": "integer",
                "default": 10,
                "description": "Number of lines for preview"
            }
        },
        "required": ["file_path", "operation"]
    },
    return_schema={
        "type": "object",
        "description": "File processing results"
    },
    category="file"
)
def file_processor(file_path: str, operation: str, lines: int = 10) -> Dict[str, Any]:
    """Process files and extract information."""
    try:
        # Validate file path (security)
        base_dir = os.path.abspath("./resources")
        full_path = os.path.abspath(os.path.join(base_dir, file_path))
        
        if not full_path.startswith(base_dir):
            return {"error": "Access denied: file outside resources directory"}
        
        if not os.path.exists(full_path):
            return {"error": f"File not found: {file_path}"}
        
        # File info operation
        if operation == "info":
            stat = os.stat(full_path)
            return {
                "file_path": file_path,
                "size_bytes": stat.st_size,
                "size_human": f"{stat.st_size / 1024:.1f} KB",
                "modified": stat.st_mtime,
                "is_file": os.path.isfile(full_path),
                "extension": os.path.splitext(file_path)[1]
            }
        
        # Read file for other operations
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if operation == "preview":
            lines_list = content.splitlines()
            preview_lines = lines_list[:lines]
            return {
                "file_path": file_path,
                "total_lines": len(lines_list),
                "preview_lines": len(preview_lines),
                "preview": "\n".join(preview_lines),
                "truncated": len(lines_list) > lines
            }
        
        elif operation == "word_count":
            words = len(content.split())
            return {
                "file_path": file_path,
                "word_count": words,
                "character_count": len(content),
                "line_count": len(content.splitlines())
            }
        
        elif operation == "line_count":
            lines_count = len(content.splitlines())
            return {
                "file_path": file_path,
                "line_count": lines_count
            }
        
        else:
            return {"error": f"Unknown operation: {operation}"}
            
    except Exception as e:
        return {"error": f"File processing error: {str(e)}"}
```

## Tutorial 5: Advanced Tool with Validation

Create a tool with comprehensive input validation and error handling.

### Step 1: Create Validation Tool

Create `tools/validation_tools.py`:

```python
import re
from typing import Dict, Any, List
from tools.registry import tool

@tool(
    name="email_validator",
    description="Validate and analyze email addresses",
    parameter_schema={
        "type": "object",
        "properties": {
            "emails": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of email addresses to validate"
            },
            "check_domain": {
                "type": "boolean",
                "default": False,
                "description": "Whether to check domain format"
            }
        },
        "required": ["emails"]
    },
    return_schema={
        "type": "object",
        "description": "Email validation results"
    },
    examples=[
        {
            "emails": ["user@example.com", "invalid-email"],
            "result": {
                "total": 2,
                "valid": 1,
                "invalid": 1,
                "results": [
                    {"email": "user@example.com", "valid": True},
                    {"email": "invalid-email", "valid": False, "reason": "Missing @ symbol"}
                ]
            }
        }
    ],
    category="validation"
)
def email_validator(emails: List[str], check_domain: bool = False) -> Dict[str, Any]:
    """Validate email addresses and provide detailed results."""
    if not emails:
        return {"error": "No emails provided"}
    
    if len(emails) > 100:
        return {"error": "Too many emails (max 100)"}
    
    # Email regex pattern
    email_pattern = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    results = []
    valid_count = 0
    
    for email in emails:
        if not isinstance(email, str):
            results.append({
                "email": str(email),
                "valid": False,
                "reason": "Email must be a string"
            })
            continue
        
        email = email.strip()
        
        if not email:
            results.append({
                "email": email,
                "valid": False,
                "reason": "Empty email"
            })
            continue
        
        if len(email) > 254:
            results.append({
                "email": email,
                "valid": False,
                "reason": "Email too long (max 254 characters)"
            })
            continue
        
        if '@' not in email:
            results.append({
                "email": email,
                "valid": False,
                "reason": "Missing @ symbol"
            })
            continue
        
        if email_pattern.match(email):
            result = {"email": email, "valid": True}
            
            if check_domain:
                domain = email.split('@')[1]
                if '.' not in domain:
                    result["valid"] = False
                    result["reason"] = "Invalid domain format"
                else:
                    result["domain"] = domain
            
            if result["valid"]:
                valid_count += 1
            
            results.append(result)
        else:
            results.append({
                "email": email,
                "valid": False,
                "reason": "Invalid email format"
            })
    
    return {
        "total": len(emails),
        "valid": valid_count,
        "invalid": len(emails) - valid_count,
        "success_rate": f"{(valid_count / len(emails) * 100):.1f}%",
        "results": results
    }
```

### Step 2: Register and Test

1. Add `from . import validation_tools` to `tools/__init__.py`
2. Test: "Validate these emails: user@example.com, invalid-email, test@domain.co.uk"

## Best Practices Summary

1. **Always validate inputs** - Check types, ranges, and formats
2. **Handle errors gracefully** - Return meaningful error messages
3. **Use type hints** - Helps with documentation and debugging
4. **Provide examples** - Makes tools easier to understand and use
5. **Categorize tools** - Organize tools by functionality
6. **Test thoroughly** - Test with valid and invalid inputs
7. **Document clearly** - Write clear descriptions and parameter docs
8. **Consider security** - Validate file paths, limit resource usage
9. **Use appropriate schemas** - Define clear input/output schemas
10. **Follow naming conventions** - Use descriptive, consistent names

## Next Steps

- Explore the existing tools in the `tools/` directory
- Read the [Tool Development Guide](tool_development.md) for advanced patterns
- Check the [API Documentation](../docs/api.md) for complete tool specifications
- Experiment with different tool categories and use cases
