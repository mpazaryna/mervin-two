# MCP Learning Server

A simple Python-based Model Context Protocol (MCP) server designed to help users learn MCP fundamentals through hands-on implementation and experimentation.

## Features

- **Educational Focus**: Designed specifically for learning MCP concepts
- **Basic MCP Protocol**: Core protocol implementation with message handling
- **Example Tools**: Calculator, echo, file reader, and time tools
- **Resource Management**: Sample resources and interactive prompts
- **Development Features**: Hot reload, debug mode, and configuration support
- **Comprehensive Testing**: Unit tests and integration examples

## Project Structure

```
mcp-learning-server/
├── mcp_server/          # Main package
│   ├── __init__.py
│   └── logging_config.py
├── tools/               # Tool implementations
│   └── __init__.py
├── resources/           # Static resources
│   └── sample.txt
├── tests/               # Unit tests
│   └── __init__.py
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── .gitignore          # Git ignore patterns
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Setup Steps

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd mcp-learning-server
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # Create virtual environment
   python -m venv venv

   # Activate virtual environment
   # On macOS/Linux:
   source venv/bin/activate

   # On Windows:
   venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Server Startup

```bash
# Activate virtual environment first
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Start the MCP server
python -m mcp_server
```

### Development Mode

```bash
# Start with debug mode
python -m mcp_server --debug

# Start with hot reload
python -m mcp_server --hot-reload

# Custom configuration
python -m mcp_server --config config.json
```

## Available Tools

The server includes several educational tools organized by category:

### 📊 Calculator Tools
- **calculator**: Basic arithmetic operations (add, subtract, multiply, divide, power, sqrt, abs)
- **advanced_calculator**: Advanced math functions (sin, cos, tan, log, factorial, gcd, lcm)

### 📁 File Tools
- **file_reader**: Read content from text files in the resources directory
- **file_info**: Get file metadata (size, dates, permissions)
- **list_files**: List files and directories with filtering options

### ⏰ Time Tools
- **time**: Get current timestamp in various formats (ISO, Unix, human-readable)
- **time_calculator**: Perform date/time calculations (add days, time differences)

### 🔧 Utility Tools
- **echo**: Echo back messages with optional modifications (repeat, prefix, suffix)
- **random_generator**: Generate random numbers, strings, and UUIDs
- **text_processor**: Text transformations (uppercase, lowercase, reverse, word count)
- **json_formatter**: Format, validate, and manipulate JSON data

### 📋 Example Usage

```bash
# Start the server
python -m mcp_server --debug

# Example tool calls (via MCP client like Claude Desktop):
# calculator(operation="add", a=5, b=3) → 8
# file_reader(file_path="sample.txt") → file content
# time(format="human") → "2024-06-08 17:30:45"
# echo(message="Hello", repeat=3) → "Hello\nHello\nHello"
```

## Configuration

The server supports flexible configuration through multiple sources (in order of precedence):

1. **Command line arguments** (highest priority)
2. **Configuration files** (JSON format)
3. **Environment variables**
4. **Default values** (lowest priority)

### Command Line Options

```bash
python -m mcp_server [OPTIONS]

Options:
  --config CONFIG              Path to configuration file
  --debug                      Enable debug mode with verbose logging
  --hot-reload                 Enable hot reload for development
  --log-level LEVEL           Set logging level (DEBUG, INFO, WARNING, ERROR)
  --metrics                   Enable performance metrics collection
  --simple                    Use simple synchronous transport
  --resource-dir DIR          Directory containing resources
  --tools-dir DIR             Directory containing tools
  --prompts-dir DIR           Directory containing prompts
  --test-mode                 Enable test mode
  -h, --help                  Show help message
```

### Configuration File Example

Create a `config.json` file:

```json
{
  "debug": false,
  "hot_reload": true,
  "log_level": "INFO",
  "metrics_enabled": true,
  "resource_dir": "./resources",
  "tools_dir": "./tools",
  "prompts_dir": "./prompts",
  "server_name": "My MCP Server",
  "max_file_size": 10485760,
  "cache_size": 100,
  "restrict_file_access": true,
  "allowed_file_extensions": [".txt", ".md", ".json", ".csv", ".log"]
}
```

### Environment Variables

```bash
export MCP_DEBUG=true
export MCP_LOG_LEVEL=DEBUG
export MCP_HOT_RELOAD=true
export MCP_METRICS_ENABLED=true
export MCP_RESOURCE_DIR=./my_resources
```

## Connecting to Claude Desktop

To use the MCP Learning Server with Claude Desktop:

### 1. Configure Claude Desktop

Edit your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add the server configuration:

```json
{
  "mcpServers": {
    "mcp-learning-server": {
      "command": "python",
      "args": ["-m", "mcp_server"],
      "cwd": "/path/to/your/mcp-learning-server",
      "env": {
        "PYTHONPATH": "/path/to/your/mcp-learning-server"
      }
    }
  }
}
```

### 2. Development Configuration

For development with debug mode:

```json
{
  "mcpServers": {
    "mcp-learning-server-dev": {
      "command": "python",
      "args": ["-m", "mcp_server", "--debug", "--hot-reload"],
      "cwd": "/path/to/your/mcp-learning-server",
      "env": {
        "PYTHONPATH": "/path/to/your/mcp-learning-server",
        "MCP_DEBUG": "true"
      }
    }
  }
}
```

### 3. Restart Claude Desktop

After updating the configuration, restart Claude Desktop to load the new server.

### 4. Test the Connection

In Claude Desktop, try asking:
- "What tools are available?"
- "Calculate 15 + 27"
- "What's the current time?"
- "Read the sample.txt file"

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=mcp_server

# Run specific test file
pytest tests/test_specific.py
```

### Code Quality

```bash
# Format code
black mcp_server/ tools/ tests/

# Lint code
flake8 mcp_server/ tools/ tests/

# Type checking
mypy mcp_server/
```

## Task Management

This project uses Task Master for development workflow:

```bash
# View current tasks
task-master list

# Get next task to work on
task-master next

# Mark task as complete
task-master set-status --id=<task-id> --status=done
```

## Troubleshooting

### Common Issues

#### 1. Server Won't Start

**Problem**: `ModuleNotFoundError` or import errors
```bash
# Solution: Ensure virtual environment is activated and dependencies installed
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

**Problem**: `Permission denied` errors
```bash
# Solution: Check file permissions
chmod +x venv/bin/activate
chmod -R 755 resources/
```

#### 2. Claude Desktop Connection Issues

**Problem**: Server not appearing in Claude Desktop
- Verify the configuration file path is correct
- Check that the `cwd` path points to your project directory
- Ensure Python is in your PATH
- Restart Claude Desktop after configuration changes

**Problem**: "Server failed to start" error
```bash
# Test the server manually first
python -m mcp_server --debug

# Check for error messages in the output
```

#### 3. Tool Execution Errors

**Problem**: File not found errors
- Ensure files exist in the `resources/` directory
- Check file paths are relative to the resources directory
- Verify file permissions allow reading

**Problem**: "Tool not found" errors
- Check that tools are properly registered
- Verify the tool name spelling
- Restart the server to reload tools

#### 4. Performance Issues

**Problem**: Slow response times
```bash
# Enable metrics to diagnose
python -m mcp_server --metrics --debug

# Check for large files or complex operations
```

**Problem**: Memory usage
- Check file size limits in configuration
- Monitor resource usage with metrics
- Consider enabling caching for frequently accessed resources

### Debug Mode

Enable debug mode for detailed logging:

```bash
python -m mcp_server --debug --log-level DEBUG
```

This will show:
- Detailed message flow
- Tool execution timing
- Resource access patterns
- Error stack traces

### Documentation

For comprehensive documentation, see **[DOCUMENTATION.md](DOCUMENTATION.md)** which provides:

- 📚 **[Getting Started Guide](resources/learning/getting_started.md)** - Step-by-step setup
- 🛠️ **[Custom Tools Tutorial](resources/learning/custom_tools_tutorial.md)** - Hands-on tool creation
- 📖 **[API Documentation](resources/docs/api.md)** - Complete tool specifications
- 🔧 **[Tool Development Guide](resources/learning/tool_development.md)** - Advanced development
- ⚙️ **[Claude Desktop Configurations](resources/examples/claude_desktop_configs.md)** - Client setup examples
- 🐛 **[Troubleshooting Guide](resources/learning/troubleshooting.md)** - Problem solving

## Getting Help

- 📚 Check **[DOCUMENTATION.md](DOCUMENTATION.md)** for complete documentation index
- 🚀 New users: Start with the [Getting Started Guide](resources/learning/getting_started.md)
- 🔧 Developers: See the [Tool Development Guide](resources/learning/tool_development.md)
- 🐛 Issues: Check the [Troubleshooting Guide](resources/learning/troubleshooting.md)
- 💬 Community: Join the [MCP community](https://github.com/modelcontextprotocol) for support

## Contributing

This is an educational project. To contribute:

1. Follow the existing code style
2. Add tests for new functionality
3. Update documentation as needed
4. Use the Task Master workflow for development

## License

This project is for educational purposes. See LICENSE file for details.