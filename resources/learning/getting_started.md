# Getting Started with MCP Learning Server

This guide will walk you through setting up and using the MCP Learning Server from scratch.

## Prerequisites

Before you begin, ensure you have:

- **Python 3.8+** installed on your system
- **Claude Desktop** application (for testing MCP integration)
- **Git** (for cloning the repository)
- **Terminal/Command Prompt** access

## Step 1: Installation

### Clone the Repository

```bash
git clone <repository-url>
cd mcp-learning-server
```

### Set Up Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Verify activation (you should see (venv) in your prompt)
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: First Run

### Test the Server

```bash
# Start the server in debug mode
python -m mcp_server --debug

# You should see output like:
# 2024-06-08 17:30:45,123 - mcp_app - INFO - Initializing MCP Learning Server
# 2024-06-08 17:30:45,124 - mcp_app - INFO - Registered 8 tools: calculator, echo, file_reader, time, ...
# 2024-06-08 17:30:45,125 - mcp_app - INFO - Starting transport layer...
```

### Verify Tools Are Loaded

The server should show registered tools:
- Calculator tools (calculator, advanced_calculator)
- File tools (file_reader, file_info, list_files)
- Time tools (time, time_calculator)
- Utility tools (echo, random_generator, text_processor, json_formatter)

## Step 3: Configure Claude Desktop

### Locate Configuration File

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### Add Server Configuration

Create or edit the configuration file:

```json
{
  "mcpServers": {
    "mcp-learning-server": {
      "command": "python",
      "args": ["-m", "mcp_server"],
      "cwd": "/absolute/path/to/your/mcp-learning-server",
      "env": {
        "PYTHONPATH": "/absolute/path/to/your/mcp-learning-server"
      }
    }
  }
}
```

**Important**: Replace `/absolute/path/to/your/mcp-learning-server` with the actual path to your project directory.

### Restart Claude Desktop

Close and reopen Claude Desktop to load the new configuration.

## Step 4: Test the Integration

### Basic Tool Testing

In Claude Desktop, try these commands:

1. **List available tools**:
   ```
   What tools are available to you?
   ```

2. **Test calculator**:
   ```
   Calculate 15 + 27
   ```

3. **Test echo tool**:
   ```
   Echo "Hello MCP!" three times
   ```

4. **Test time tool**:
   ```
   What's the current time in human-readable format?
   ```

5. **Test file reader**:
   ```
   Read the contents of sample.txt
   ```

### Expected Results

- Claude should list all available tools
- Calculator should return `42`
- Echo should repeat the message three times
- Time should return current timestamp
- File reader should return the contents of the sample file

## Step 5: Explore Resources

### Available Resources

The server provides educational resources:

```
What resources are available?
```

### Read Learning Materials

```
Show me the MCP overview resource
```

### Explore Examples

```
Show me an example client configuration
```

## Step 6: Development Mode

### Enable Hot Reload

For development, enable hot reload:

```bash
python -m mcp_server --debug --hot-reload
```

This allows you to:
- Modify tools without restarting the server
- Update resources and see changes immediately
- Develop new features with faster iteration

### Enable Metrics

Track performance with metrics:

```bash
python -m mcp_server --debug --metrics
```

## Step 7: Create Your First Custom Tool

### 1. Create Tool File

Create `tools/my_tools.py`:

```python
from tools.registry import tool

@tool(
    name="word_count",
    description="Count words in a text",
    parameter_schema={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Text to count words in"
            }
        },
        "required": ["text"]
    },
    return_schema={
        "type": "integer",
        "description": "Number of words"
    },
    examples=[
        {"text": "Hello world", "result": 2}
    ],
    category="text"
)
def word_count(text: str) -> int:
    """Count the number of words in the given text."""
    return len(text.split())
```

### 2. Register the Tool

Add to `tools/__init__.py`:

```python
# Import your new tool module
from . import my_tools
```

### 3. Test Your Tool

Restart the server and test in Claude Desktop:

```
Count the words in "The quick brown fox jumps over the lazy dog"
```

## Step 8: Next Steps

### Learn More

1. **Read the guides**:
   - [Tool Development Guide](tool_development.md)
   - [MCP Overview](mcp_overview.md)
   - [API Documentation](../docs/api.md)

2. **Explore examples**:
   - Check existing tools in `tools/` directory
   - Review configuration examples in `resources/examples/`

3. **Experiment**:
   - Create more complex tools
   - Add custom resources
   - Try different configurations

### Common Next Steps

- **Add file processing tools** for your specific use case
- **Create API integration tools** to connect external services
- **Build data analysis tools** for working with CSV/JSON data
- **Develop workflow automation tools** for repetitive tasks

## Troubleshooting

### Server Won't Start

1. Check virtual environment is activated
2. Verify all dependencies are installed
3. Check Python version (3.8+ required)

### Claude Desktop Can't Connect

1. Verify configuration file path
2. Check absolute paths in configuration
3. Restart Claude Desktop after changes
4. Test server manually first

### Tools Not Working

1. Check tool registration in `tools/__init__.py`
2. Verify tool syntax and imports
3. Check server logs for errors
4. Test tools individually

## Getting Help

- 📚 Check the [learning resources](.) for detailed guides
- 🔧 Review existing tool implementations for patterns
- 🐛 Enable debug mode for detailed error information
- 💬 Join the [MCP community](https://github.com/modelcontextprotocol) for support

Congratulations! You now have a working MCP Learning Server. Start experimenting with tools and building your own MCP integrations!
