"""
Utility Tools

Provides basic utility tools for the MCP Learning Server including
echo, time, and other helpful utilities for demonstration and testing.
"""

import datetime
import json
import random
import string
from typing import Any, Dict, List, Optional

from .registry import tool


@tool(
    name="echo",
    description="Echo back the input message",
    parameter_schema={
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "Message to echo back"
            },
            "repeat": {
                "type": "integer",
                "minimum": 1,
                "maximum": 10,
                "default": 1,
                "description": "Number of times to repeat the message"
            },
            "prefix": {
                "type": "string",
                "default": "",
                "description": "Prefix to add to each echo"
            },
            "suffix": {
                "type": "string", 
                "default": "",
                "description": "Suffix to add to each echo"
            }
        },
        "required": ["message"]
    },
    return_schema={
        "type": "string",
        "description": "The echoed message"
    },
    examples=[
        {"message": "Hello World", "result": "Hello World"},
        {"message": "Test", "repeat": 3, "result": "Test\nTest\nTest"},
        {"message": "Hi", "prefix": "Echo: ", "result": "Echo: Hi"}
    ],
    category="utility"
)
def echo(message: str, repeat: int = 1, prefix: str = "", suffix: str = "") -> str:
    """
    Echo back the input message with optional modifications.
    
    Args:
        message: Message to echo
        repeat: Number of times to repeat
        prefix: Prefix to add
        suffix: Suffix to add
        
    Returns:
        The echoed message
    """
    if repeat < 1 or repeat > 10:
        raise ValueError("Repeat count must be between 1 and 10")
    
    echoed_messages = []
    for _ in range(repeat):
        echoed_messages.append(f"{prefix}{message}{suffix}")
    
    return "\n".join(echoed_messages)


@tool(
    name="time",
    description="Get current timestamp in various formats",
    parameter_schema={
        "type": "object",
        "properties": {
            "format": {
                "type": "string",
                "enum": ["iso", "unix", "human", "custom", "utc", "local"],
                "default": "iso",
                "description": "Time format to return"
            },
            "custom_format": {
                "type": "string",
                "description": "Custom strftime format (required when format='custom')"
            },
            "timezone": {
                "type": "string",
                "enum": ["local", "utc"],
                "default": "local",
                "description": "Timezone to use for timestamp"
            }
        }
    },
    return_schema={
        "type": "string",
        "description": "Current timestamp in requested format"
    },
    examples=[
        {"format": "iso", "result": "2023-12-07T10:30:00.123456"},
        {"format": "unix", "result": "1701944200"},
        {"format": "human", "result": "2023-12-07 10:30:00"},
        {"format": "custom", "custom_format": "%A, %B %d, %Y", "result": "Thursday, December 07, 2023"},
        {"format": "utc", "result": "2023-12-07T18:30:00.123456Z"}
    ],
    category="time"
)
def time_tool(format: str = "iso", custom_format: str = None, timezone: str = "local") -> str:
    """
    Get current timestamp in various formats.

    Args:
        format: Time format to return
        custom_format: Custom strftime format
        timezone: Timezone to use

    Returns:
        Current timestamp in requested format

    Raises:
        ValueError: For invalid format or missing custom_format
    """
    # Get current time in appropriate timezone
    if timezone == "utc":
        now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    else:  # local
        now = datetime.datetime.now()

    if format == "iso":
        return now.isoformat()
    elif format == "unix":
        return str(int(now.timestamp()))
    elif format == "human":
        return now.strftime("%Y-%m-%d %H:%M:%S")
    elif format == "utc":
        utc_now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        return utc_now.isoformat() + "Z"
    elif format == "local":
        local_now = datetime.datetime.now()
        return local_now.isoformat()
    elif format == "custom":
        if not custom_format:
            raise ValueError("custom_format is required when format='custom'")
        try:
            return now.strftime(custom_format)
        except ValueError as e:
            raise ValueError(f"Invalid custom format: {str(e)}")
    else:
        raise ValueError(f"Unknown time format: {format}")


@tool(
    name="time_calculator",
    description="Perform calculations with dates and times",
    parameter_schema={
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["add_days", "subtract_days", "add_hours", "subtract_hours", "days_between", "format_date"],
                "description": "Time calculation operation to perform"
            },
            "date": {
                "type": "string",
                "description": "Date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)"
            },
            "amount": {
                "type": "number",
                "description": "Amount to add/subtract (for add/subtract operations)"
            },
            "end_date": {
                "type": "string",
                "description": "End date for days_between operation"
            },
            "output_format": {
                "type": "string",
                "default": "iso",
                "description": "Output format for result"
            }
        },
        "required": ["operation"]
    },
    return_schema={
        "type": ["string", "number"],
        "description": "Result of time calculation"
    },
    examples=[
        {"operation": "add_days", "date": "2023-12-07", "amount": 5, "result": "2023-12-12"},
        {"operation": "days_between", "date": "2023-12-01", "end_date": "2023-12-07", "result": 6}
    ],
    category="time"
)
def time_calculator(operation: str, date: str = None, amount: float = None,
                   end_date: str = None, output_format: str = "iso") -> Any:
    """
    Perform calculations with dates and times.

    Args:
        operation: Time calculation operation
        date: Input date
        amount: Amount for add/subtract operations
        end_date: End date for between operations
        output_format: Output format

    Returns:
        Result of time calculation

    Raises:
        ValueError: For invalid operations or date formats
    """
    try:
        if operation in ["add_days", "subtract_days", "add_hours", "subtract_hours", "format_date"]:
            if not date:
                date = datetime.datetime.now().isoformat()

            # Parse input date
            try:
                if 'T' in date:
                    dt = datetime.datetime.fromisoformat(date.replace('Z', '+00:00'))
                else:
                    dt = datetime.datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                raise ValueError(f"Invalid date format: {date}")

            if operation == "add_days":
                if amount is None:
                    raise ValueError("amount is required for add_days operation")
                result_dt = dt + datetime.timedelta(days=amount)
            elif operation == "subtract_days":
                if amount is None:
                    raise ValueError("amount is required for subtract_days operation")
                result_dt = dt - datetime.timedelta(days=amount)
            elif operation == "add_hours":
                if amount is None:
                    raise ValueError("amount is required for add_hours operation")
                result_dt = dt + datetime.timedelta(hours=amount)
            elif operation == "subtract_hours":
                if amount is None:
                    raise ValueError("amount is required for subtract_hours operation")
                result_dt = dt - datetime.timedelta(hours=amount)
            elif operation == "format_date":
                result_dt = dt

            # Format output
            if output_format == "iso":
                return result_dt.isoformat()
            elif output_format == "human":
                return result_dt.strftime("%Y-%m-%d %H:%M:%S")
            elif output_format == "date_only":
                return result_dt.strftime("%Y-%m-%d")
            else:
                return result_dt.strftime(output_format)

        elif operation == "days_between":
            if not date or not end_date:
                raise ValueError("Both date and end_date are required for days_between operation")

            # Parse dates
            try:
                if 'T' in date:
                    start_dt = datetime.datetime.fromisoformat(date.replace('Z', '+00:00'))
                else:
                    start_dt = datetime.datetime.strptime(date, "%Y-%m-%d")

                if 'T' in end_date:
                    end_dt = datetime.datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                else:
                    end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError as e:
                raise ValueError(f"Invalid date format: {str(e)}")

            # Calculate difference
            diff = end_dt - start_dt
            return diff.days

        else:
            raise ValueError(f"Unknown operation: {operation}")

    except Exception as e:
        raise ValueError(f"Time calculation error: {str(e)}")


@tool(
    name="random_generator",
    description="Generate random values of various types",
    parameter_schema={
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "enum": ["integer", "float", "string", "boolean", "uuid"],
                "description": "Type of random value to generate"
            },
            "min_value": {
                "type": "number",
                "description": "Minimum value (for integer/float)"
            },
            "max_value": {
                "type": "number", 
                "description": "Maximum value (for integer/float)"
            },
            "length": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
                "default": 10,
                "description": "Length of string to generate"
            },
            "charset": {
                "type": "string",
                "enum": ["alphanumeric", "letters", "digits", "ascii"],
                "default": "alphanumeric",
                "description": "Character set for string generation"
            }
        },
        "required": ["type"]
    },
    return_schema={
        "type": ["string", "number", "boolean"],
        "description": "Generated random value"
    },
    examples=[
        {"type": "integer", "min_value": 1, "max_value": 100, "result": 42},
        {"type": "string", "length": 8, "charset": "letters", "result": "abcdefgh"},
        {"type": "boolean", "result": True}
    ],
    category="utility"
)
def random_generator(type: str, min_value: float = None, max_value: float = None,
                    length: int = 10, charset: str = "alphanumeric") -> Any:
    """
    Generate random values of various types.
    
    Args:
        type: Type of random value to generate
        min_value: Minimum value (for numbers)
        max_value: Maximum value (for numbers)
        length: Length of string
        charset: Character set for strings
        
    Returns:
        Generated random value
        
    Raises:
        ValueError: For invalid parameters
    """
    if type == "integer":
        min_val = int(min_value) if min_value is not None else 0
        max_val = int(max_value) if max_value is not None else 100
        if min_val > max_val:
            raise ValueError("min_value cannot be greater than max_value")
        return random.randint(min_val, max_val)
    
    elif type == "float":
        min_val = min_value if min_value is not None else 0.0
        max_val = max_value if max_value is not None else 1.0
        if min_val > max_val:
            raise ValueError("min_value cannot be greater than max_value")
        return random.uniform(min_val, max_val)
    
    elif type == "string":
        if length < 1 or length > 100:
            raise ValueError("String length must be between 1 and 100")
        
        if charset == "alphanumeric":
            chars = string.ascii_letters + string.digits
        elif charset == "letters":
            chars = string.ascii_letters
        elif charset == "digits":
            chars = string.digits
        elif charset == "ascii":
            chars = string.ascii_letters + string.digits + string.punctuation
        else:
            raise ValueError(f"Unknown charset: {charset}")
        
        return ''.join(random.choice(chars) for _ in range(length))
    
    elif type == "boolean":
        return random.choice([True, False])
    
    elif type == "uuid":
        import uuid
        return str(uuid.uuid4())
    
    else:
        raise ValueError(f"Unknown random type: {type}")


@tool(
    name="text_processor",
    description="Process text with various transformations",
    parameter_schema={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Text to process"
            },
            "operation": {
                "type": "string",
                "enum": ["uppercase", "lowercase", "title", "reverse", "word_count", "char_count", "trim"],
                "description": "Text processing operation"
            }
        },
        "required": ["text", "operation"]
    },
    return_schema={
        "type": ["string", "integer"],
        "description": "Processed text or count"
    },
    examples=[
        {"text": "hello world", "operation": "uppercase", "result": "HELLO WORLD"},
        {"text": "  hello world  ", "operation": "trim", "result": "hello world"},
        {"text": "hello world", "operation": "word_count", "result": 2}
    ],
    category="utility"
)
def text_processor(text: str, operation: str) -> Any:
    """
    Process text with various transformations.
    
    Args:
        text: Text to process
        operation: Processing operation
        
    Returns:
        Processed text or count
        
    Raises:
        ValueError: For unknown operations
    """
    if operation == "uppercase":
        return text.upper()
    elif operation == "lowercase":
        return text.lower()
    elif operation == "title":
        return text.title()
    elif operation == "reverse":
        return text[::-1]
    elif operation == "word_count":
        return len(text.split())
    elif operation == "char_count":
        return len(text)
    elif operation == "trim":
        return text.strip()
    else:
        raise ValueError(f"Unknown operation: {operation}")


@tool(
    name="json_formatter",
    description="Format and validate JSON data",
    parameter_schema={
        "type": "object",
        "properties": {
            "data": {
                "type": "string",
                "description": "JSON string to format or validate"
            },
            "operation": {
                "type": "string",
                "enum": ["format", "validate", "minify"],
                "default": "format",
                "description": "JSON operation to perform"
            },
            "indent": {
                "type": "integer",
                "minimum": 0,
                "maximum": 8,
                "default": 2,
                "description": "Indentation level for formatting"
            }
        },
        "required": ["data"]
    },
    return_schema={
        "type": ["string", "boolean"],
        "description": "Formatted JSON or validation result"
    },
    examples=[
        {"data": '{"name":"John","age":30}', "operation": "format", "result": "{\n  \"name\": \"John\",\n  \"age\": 30\n}"},
        {"data": '{"valid": true}', "operation": "validate", "result": True}
    ],
    category="utility"
)
def json_formatter(data: str, operation: str = "format", indent: int = 2) -> Any:
    """
    Format and validate JSON data.
    
    Args:
        data: JSON string to process
        operation: Operation to perform
        indent: Indentation level
        
    Returns:
        Formatted JSON or validation result
        
    Raises:
        ValueError: For invalid JSON or operations
    """
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError as e:
        if operation == "validate":
            return False
        else:
            raise ValueError(f"Invalid JSON: {str(e)}")
    
    if operation == "validate":
        return True
    elif operation == "format":
        return json.dumps(parsed, indent=indent, ensure_ascii=False)
    elif operation == "minify":
        return json.dumps(parsed, separators=(',', ':'))
    else:
        raise ValueError(f"Unknown operation: {operation}")
