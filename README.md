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

The server includes several educational tools:

### Calculator
- **Purpose**: Demonstrate basic arithmetic operations
- **Parameters**: operation (add/subtract/multiply/divide), a (number), b (number)
- **Example**: Perform calculations through MCP client

### Echo
- **Purpose**: Simple input/output demonstration
- **Parameters**: message (string)
- **Example**: Echo back any text message

### File Reader
- **Purpose**: Read local text files securely
- **Parameters**: file_path (string, relative to resources directory)
- **Security**: Restricted to files within the resources directory

### Time
- **Purpose**: Get current timestamp in various formats
- **Parameters**: format (iso/unix/human, default: iso)
- **Example**: Get current time in different formats

## Configuration

The server supports configuration through:

1. **Command line arguments**
2. **Configuration files** (JSON format)
3. **Environment variables**

### Example Configuration

```json
{
  "debug": false,
  "hot_reload": false,
  "log_level": "INFO",
  "resource_dir": "./resources",
  "tools_dir": "./tools",
  "prompts_dir": "./prompts"
}
```

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

1. **Virtual environment not activated**
   - Make sure to activate the virtual environment before running commands
   - Check that your prompt shows `(venv)` prefix

2. **Missing dependencies**
   - Run `pip install -r requirements.txt` in the activated virtual environment

3. **Permission errors**
   - Ensure you have write permissions in the project directory
   - Check file permissions for the resources directory

4. **Port conflicts**
   - The server uses stdio transport, so no port conflicts should occur
   - If using custom transport, check for port availability

### Getting Help

- Check the task files in `.taskmaster/tasks/` for detailed implementation notes
- Review the PRD document for project requirements
- Examine the example tools for implementation patterns

## Contributing

This is an educational project. To contribute:

1. Follow the existing code style
2. Add tests for new functionality
3. Update documentation as needed
4. Use the Task Master workflow for development

## License

This project is for educational purposes. See LICENSE file for details.