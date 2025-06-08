# MCP Learning Server API Documentation

## Overview

The MCP Learning Server provides a set of tools for educational purposes, demonstrating the Model Context Protocol (MCP) implementation.

## Available Tools

### File Operations

#### file_reader
Read content from text files in the resources directory.

**Parameters:**
- `file_path` (string, required): Relative path to file
- `encoding` (string, optional): Text encoding (default: utf-8)
- `max_size` (integer, optional): Maximum file size in bytes (default: 1MB)

**Example:**
```json
{
  "name": "file_reader",
  "arguments": {
    "file_path": "sample.txt"
  }
}
```

#### file_info
Get information about a file including size, dates, and permissions.

**Parameters:**
- `file_path` (string, required): Relative path to file

#### list_files
List files and directories in the resources directory.

**Parameters:**
- `directory` (string, optional): Subdirectory to list
- `include_hidden` (boolean, optional): Include hidden files
- `file_types` (array, optional): Filter by file extensions

### Calculator Tools

#### calculator
Perform basic arithmetic operations.

**Parameters:**
- `operation` (string, required): Operation type (add, subtract, multiply, divide, power, sqrt, abs)
- `a` (number, required): First number
- `b` (number, optional): Second number (required for binary operations)

#### advanced_calculator
Perform advanced mathematical operations.

**Parameters:**
- `operation` (string, required): Operation type (sin, cos, tan, log, ln, factorial, gcd, lcm)
- `a` (number, required): First number
- `b` (number, optional): Second number (for gcd, lcm)
- `angle_unit` (string, optional): Unit for trigonometric functions (radians, degrees)

### Time Tools

#### time
Get current timestamp in various formats.

**Parameters:**
- `format` (string, optional): Time format (iso, unix, human, custom, utc, local)
- `custom_format` (string, optional): Custom strftime format
- `timezone` (string, optional): Timezone (local, utc)

#### time_calculator
Perform calculations with dates and times.

**Parameters:**
- `operation` (string, required): Time operation (add_days, subtract_days, etc.)
- `date` (string, optional): Input date in ISO format
- `amount` (number, optional): Amount for add/subtract operations
- `end_date` (string, optional): End date for between operations

### Utility Tools

#### echo
Echo back input message with optional modifications.

#### random_generator
Generate random values of various types.

#### text_processor
Process text with various transformations.

#### json_formatter
Format and validate JSON data.

## Error Handling

All tools provide comprehensive error handling with descriptive error messages. Common error scenarios:

- File not found
- Permission denied
- Invalid parameters
- File size limits exceeded
- Invalid date formats
- Division by zero
- Invalid JSON

## Security

- File operations are restricted to the resources directory
- File size limits prevent memory exhaustion
- Path traversal attacks are prevented
- Input validation on all parameters
