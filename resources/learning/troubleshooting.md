# Troubleshooting Guide

Common issues and solutions for the MCP Learning Server.

## Connection Issues

### Server Won't Start

**Symptoms:**
- Server exits immediately
- "Module not found" errors
- Permission denied errors

**Solutions:**

1. **Check Python Environment**
   ```bash
   # Verify Python version (3.8+ required)
   python --version
   
   # Activate virtual environment
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Check Working Directory**
   ```bash
   # Ensure you're in the project root
   ls -la
   # Should see: mcp_server/, tools/, resources/, requirements.txt
   
   # Run from correct directory
   python -m mcp_server
   ```

3. **Check File Permissions**
   ```bash
   # Fix permissions if needed
   chmod +x mcp_server/main.py
   chmod -R 755 resources/
   ```

### Client Connection Failed

**Symptoms:**
- Claude Desktop shows "Connection failed"
- Timeout errors
- "Server not responding" messages

**Solutions:**

1. **Verify Configuration**
   ```json
   {
     "mcpServers": {
       "mcp-learning-server": {
         "command": "python",
         "args": ["-m", "mcp_server"],
         "cwd": "/correct/path/to/project"
       }
     }
   }
   ```

2. **Check Server Logs**
   ```bash
   # Run with debug mode
   python -m mcp_server --debug --log-level DEBUG
   ```

3. **Test Server Manually**
   ```bash
   # Test stdio communication
   echo '{"jsonrpc": "2.0", "id": 1, "method": "ping"}' | python -m mcp_server
   ```

## Tool Issues

### Tool Not Found

**Symptoms:**
- "Unknown tool" errors
- Tool not listed in available tools

**Solutions:**

1. **Check Tool Registration**
   ```python
   # Verify tool is properly decorated
   from tools.registry import tool
   
   @tool(name="my_tool", description="My tool")
   def my_tool():
       pass
   ```

2. **Check Import Errors**
   ```bash
   # Test tool import
   python -c "from tools.my_module import my_tool; print('OK')"
   ```

3. **Verify Tool Loading**
   ```bash
   # Check server startup logs
   python -m mcp_server --debug 2>&1 | grep "Registered tool"
   ```

### Tool Execution Errors

**Symptoms:**
- Tool calls return errors
- Unexpected results
- Timeout errors

**Solutions:**

1. **Check Parameter Validation**
   ```python
   # Add input validation
   def my_tool(param: str) -> str:
       if not param:
           raise ValueError("Parameter cannot be empty")
       return process(param)
   ```

2. **Add Error Handling**
   ```python
   def my_tool(file_path: str) -> str:
       try:
           with open(file_path, 'r') as f:
               return f.read()
       except FileNotFoundError:
           raise ValueError(f"File not found: {file_path}")
       except PermissionError:
           raise ValueError(f"Permission denied: {file_path}")
   ```

3. **Check Resource Access**
   ```python
   # Ensure files are in resources directory
   import os
   resource_path = os.path.join("./resources", file_path)
   if not os.path.exists(resource_path):
       raise ValueError(f"Resource not found: {file_path}")
   ```

## Resource Issues

### Resource Not Found

**Symptoms:**
- "Resource not found" errors
- Empty resource lists

**Solutions:**

1. **Check Resource Index**
   ```bash
   # Verify index.json exists and is valid
   cat resources/index.json | python -m json.tool
   ```

2. **Verify File Paths**
   ```json
   {
     "my_resource": {
       "path": "learning/my_file.md",  // Relative to resources/
       "title": "My Resource"
     }
   }
   ```

3. **Check File Existence**
   ```bash
   # Verify resource files exist
   ls -la resources/learning/my_file.md
   ```

### Resource Loading Errors

**Symptoms:**
- "Error loading resource" messages
- Partial content loading

**Solutions:**

1. **Check File Encoding**
   ```bash
   # Verify file encoding
   file resources/learning/my_file.md
   
   # Convert if needed
   iconv -f ISO-8859-1 -t UTF-8 input.txt > output.txt
   ```

2. **Check File Size**
   ```bash
   # Check if file exceeds size limit
   ls -lh resources/learning/my_file.md
   
   # Default limit is 10MB
   ```

3. **Verify Permissions**
   ```bash
   # Check read permissions
   ls -la resources/learning/my_file.md
   chmod 644 resources/learning/my_file.md
   ```

## Performance Issues

### Slow Response Times

**Symptoms:**
- Long delays in tool responses
- Timeout errors
- High CPU/memory usage

**Solutions:**

1. **Enable Caching**
   ```python
   # Use resource caching
   resource_manager = ResourceManager()
   content = resource_manager.get_resource("my_resource", use_cache=True)
   ```

2. **Optimize Tool Code**
   ```python
   # Use efficient algorithms
   from functools import lru_cache
   
   @lru_cache(maxsize=128)
   def expensive_operation(input_data):
       # Cached expensive operation
       pass
   ```

3. **Monitor Resource Usage**
   ```bash
   # Monitor server performance
   python -m mcp_server --debug --metrics-enabled
   ```

### Memory Issues

**Symptoms:**
- Out of memory errors
- Server crashes
- Slow performance

**Solutions:**

1. **Limit Resource Cache**
   ```python
   # Reduce cache size
   resource_manager = ResourceManager()
   resource_manager.max_cache_size = 50
   ```

2. **Process Large Files in Chunks**
   ```python
   def read_large_file(file_path: str) -> str:
       chunks = []
       with open(file_path, 'r') as f:
           while True:
               chunk = f.read(8192)  # 8KB chunks
               if not chunk:
                   break
               chunks.append(chunk)
       return ''.join(chunks)
   ```

3. **Clear Cache Periodically**
   ```python
   # Clear cache when needed
   resource_manager.clear_cache()
   ```

## Configuration Issues

### Invalid Configuration

**Symptoms:**
- Server fails to start
- Configuration errors in logs
- Features not working

**Solutions:**

1. **Validate JSON Syntax**
   ```bash
   # Check configuration file
   python -m json.tool config.json
   ```

2. **Use Example Configuration**
   ```bash
   # Copy example config
   cp config.json.example config.json
   # Edit as needed
   ```

3. **Check Required Fields**
   ```json
   {
     "debug": false,
     "log_level": "INFO",
     "resource_dir": "./resources",
     "server": {
       "name": "MCP Learning Server",
       "version": "0.1.0"
     }
   }
   ```

### Environment Variables

**Symptoms:**
- Configuration not taking effect
- Default values being used

**Solutions:**

1. **Set Environment Variables**
   ```bash
   export MCP_DEBUG=true
   export MCP_LOG_LEVEL=DEBUG
   export MCP_CONFIG_FILE=custom_config.json
   ```

2. **Check Variable Names**
   ```bash
   # List all MCP-related variables
   env | grep MCP
   ```

## Debugging Techniques

### Enable Debug Logging

```bash
# Maximum verbosity
python -m mcp_server --debug --log-level DEBUG

# Log to file
python -m mcp_server --debug 2>&1 | tee server.log
```

### Test Individual Components

```python
# Test resource manager
from mcp_server.resources import ResourceManager
rm = ResourceManager()
print(rm.list_resources())

# Test tool registry
from tools.registry import get_tool_registry
registry = get_tool_registry()
print(list(registry.keys()))
```

### Use MCP Inspector

```bash
# Install MCP Inspector
npm install -g @modelcontextprotocol/inspector

# Connect to server
mcp-inspector python -m mcp_server
```

### Manual Protocol Testing

```bash
# Test ping
echo '{"jsonrpc": "2.0", "id": 1, "method": "ping"}' | python -m mcp_server

# Test initialization
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}}}' | python -m mcp_server

# Test tool listing
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}' | python -m mcp_server
```

## Common Error Messages

### "Module not found: mcp_server"

**Cause:** Python can't find the mcp_server module
**Solution:** 
```bash
# Ensure you're in the project root
cd /path/to/mcp-learning-server
python -m mcp_server
```

### "Resource index not found"

**Cause:** Missing resources/index.json file
**Solution:**
```bash
# Create basic index
echo '{}' > resources/index.json
```

### "Access denied: Cannot access files outside resources directory"

**Cause:** Security restriction preventing file access
**Solution:** Move files to resources/ directory or update paths

### "Tool execution failed: [error]"

**Cause:** Error in tool implementation
**Solution:** Check tool code and add proper error handling

## Getting Help

### Log Analysis

1. **Enable debug logging**
2. **Reproduce the issue**
3. **Check logs for error patterns**
4. **Look for stack traces**

### Community Support

- [GitHub Issues](https://github.com/modelcontextprotocol/spec/issues)
- [Discord Community](https://discord.gg/mcp)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/model-context-protocol)

### Reporting Bugs

Include in your bug report:
1. **Server version and configuration**
2. **Complete error messages and stack traces**
3. **Steps to reproduce**
4. **Environment details (OS, Python version)**
5. **Relevant log output**

### Performance Profiling

```python
# Add profiling to tools
import cProfile
import pstats

def profile_tool():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Your tool code here
    result = my_tool()
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # Top 10 functions
    
    return result
```
