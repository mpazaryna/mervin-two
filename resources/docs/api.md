# MCP Learning Server API Documentation

## Overview

The MCP Learning Server provides a comprehensive set of tools for educational purposes, demonstrating the Model Context Protocol (MCP) implementation. This server includes tools for file operations, calculations, time utilities, text processing, and more.

## Protocol Information

- **Protocol Version**: MCP 1.0
- **Transport**: stdio (JSON-RPC 2.0)
- **Message Format**: JSON
- **Capabilities**: tools, resources, prompts

## Server Information

```json
{
  "name": "MCP Learning Server",
  "version": "0.1.0",
  "description": "Educational MCP server implementation",
  "author": "MCP Learning Project"
}
```

## Available Tools

### 📁 File Operations

#### file_reader
Read content from text files in the resources directory.

**Parameters:**
- `file_path` (string, required): Relative path to file within resources directory
- `encoding` (string, optional): Text encoding (default: "utf-8")
  - Supported: "utf-8", "ascii", "latin-1"
- `max_size` (integer, optional): Maximum file size in bytes (default: 1MB, max: 10MB)

**Returns:** String content of the file

**Example:**
```json
{
  "name": "file_reader",
  "arguments": {
    "file_path": "sample.txt",
    "encoding": "utf-8"
  }
}
```

**Security:** File access is restricted to the resources directory. Path traversal attempts are blocked.

#### file_info
Get detailed information about a file including size, modification dates, and permissions.

**Parameters:**
- `file_path` (string, required): Relative path to file within resources directory

**Returns:** Object with file metadata

**Example Response:**
```json
{
  "file_path": "sample.txt",
  "size_bytes": 1024,
  "size_human": "1.0 KB",
  "modified": "2024-06-08T17:30:45Z",
  "extension": ".txt",
  "exists": true
}
```

#### list_files
List files and directories in the resources directory with filtering options.

**Parameters:**
- `directory` (string, optional): Subdirectory to list (default: root)
- `include_hidden` (boolean, optional): Include hidden files (default: false)
- `file_types` (array, optional): Filter by file extensions (e.g., [".txt", ".md"])
- `recursive` (boolean, optional): List files recursively (default: false)

**Returns:** Array of file/directory information

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
