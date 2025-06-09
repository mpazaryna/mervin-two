# MCP Test Client

A Python client for testing your MCP Learning Server without needing Claude Desktop. This client communicates directly with the MCP server using the stdio protocol.

## Features

✅ **Full MCP Protocol Support**
- Initialize connection with proper handshake
- Ping/pong for connection testing
- List and call tools
- List and read resources
- Detailed request/response logging

✅ **Two Testing Modes**
- **Auto Mode**: Runs predefined tests automatically
- **Custom Mode**: Interactive testing with manual commands

✅ **Comprehensive Testing**
- Tests all 13 available tools (calculator, echo, time, file tools, etc.)
- Tests all 12 available resources
- Shows detailed JSON request/response messages
- Proper error handling and timeout management

## Quick Start

### 1. Activate Virtual Environment
```bash
cd /Users/mpaz/mervin-two
source venv/bin/activate
```

### 2. Run Auto Tests
```bash
python test_client.py --mode auto
```

### 3. Run Interactive Tests
```bash
python test_client.py --mode custom
```

## Usage Examples

### Auto Mode
Runs a comprehensive test suite automatically:
- ✅ Connection and initialization
- ✅ Ping test
- ✅ List all tools
- ✅ Test calculator operations (15+27=42, 6×7=42, 100÷4=25)
- ✅ Test echo tool with repetition
- ✅ Test time tool with human format
- ✅ List all resources
- ✅ Read and preview resource content

### Custom Mode
Interactive testing with these commands:
- `ping` - Test connection
- `tools` - List available tools
- `call <tool>` - Call a specific tool (prompts for JSON arguments)
- `resources` - List available resources
- `read <resource_id>` - Read a specific resource
- `quit` - Exit

### Example Custom Session
```
🎯 Enter command: ping
✅ Ping successful

🎯 Enter command: call calculator
Enter arguments for calculator (JSON format, or press Enter for empty):
Arguments: {"operation": "add", "a": 50, "b": 25}
✅ Tool call successful (Result: 75.0)

🎯 Enter command: read mcp_overview
✅ Resource read successful
   Resource preview: # Model Context Protocol (MCP) Overview...

🎯 Enter command: quit
```

## What Gets Tested

### Tools (13 total)
1. **calculator** - Basic arithmetic operations
2. **advanced_calculator** - Advanced math (sin, cos, log, etc.)
3. **calculator_help** - Help for calculator operations
4. **echo** - Echo messages with repetition
5. **time** - Current timestamp in various formats
6. **time_calculator** - Date/time calculations
7. **random_generator** - Generate random values
8. **text_processor** - Text transformations
9. **json_formatter** - JSON formatting and validation
10. **file_reader** - Read files from resources directory
11. **file_info** - Get file information
12. **list_files** - List files in resources directory
13. **search_files** - Search files by name or content

### Resources (12 total)
1. **mcp_overview** - MCP protocol introduction
2. **mcp_resources** - Learning materials
3. **client_config_example** - Client configuration examples
4. **server_config_example** - Server configuration examples
5. **tool_development_guide** - Guide for creating tools
6. **api_reference** - Complete API documentation
7. **troubleshooting** - Troubleshooting guide
8. **getting_started** - Setup guide
9. **custom_tools_tutorial** - Custom tools tutorial
10. **claude_desktop_configs** - Claude Desktop setup
11. **sample_data** - Sample CSV data
12. **server_config** - Current server settings

## Benefits Over Claude Desktop

🚀 **Faster Development**
- No need to restart Claude Desktop
- Immediate feedback on changes
- Direct JSON message inspection

🔍 **Better Debugging**
- See exact request/response messages
- Detailed error information
- Connection state visibility

⚡ **More Control**
- Test specific tools in isolation
- Custom argument testing
- Automated test suites

## Command Line Options

```bash
python test_client.py [options]

Options:
  --mode {auto,custom}     Test mode (default: auto)
  --server-cmd COMMAND     Custom server command (default: python -m mcp_server --debug)
```

## Example Output

```
🚀 MCP Test Client
==================
Starting MCP server with command: python -m mcp_server --debug
✅ MCP server started successfully

🔄 Initializing MCP connection...
📤 Sending: {"type": "initialize", "params": {...}}
📥 Received: {"type": "initialized", "result": {...}}
✅ MCP connection initialized successfully

🏓 Sending ping...
✅ Ping successful

🔧 Listing available tools...
✅ Found 13 tools

🧮 Testing Calculator Tool
   15 add 27 = 42.0
   6 multiply 7 = 42.0
   100 divide 4 = 25.0

✅ All tests completed!
```

This test client provides a complete alternative to Claude Desktop for testing your MCP server during development!
