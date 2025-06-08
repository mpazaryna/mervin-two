# Claude Desktop Configuration Examples

This document provides various configuration examples for connecting the MCP Learning Server to Claude Desktop.

## Basic Configuration

### Standard Setup

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

### With Virtual Environment

```json
{
  "mcpServers": {
    "mcp-learning-server": {
      "command": "/path/to/your/mcp-learning-server/venv/bin/python",
      "args": ["-m", "mcp_server"],
      "cwd": "/path/to/your/mcp-learning-server"
    }
  }
}
```

## Development Configurations

### Debug Mode

```json
{
  "mcpServers": {
    "mcp-learning-server-debug": {
      "command": "python",
      "args": [
        "-m", "mcp_server",
        "--debug",
        "--log-level", "DEBUG"
      ],
      "cwd": "/path/to/your/mcp-learning-server",
      "env": {
        "PYTHONPATH": "/path/to/your/mcp-learning-server",
        "MCP_DEBUG": "true"
      }
    }
  }
}
```

### Hot Reload for Development

```json
{
  "mcpServers": {
    "mcp-learning-server-dev": {
      "command": "python",
      "args": [
        "-m", "mcp_server",
        "--debug",
        "--hot-reload",
        "--metrics"
      ],
      "cwd": "/path/to/your/mcp-learning-server",
      "env": {
        "PYTHONPATH": "/path/to/your/mcp-learning-server",
        "MCP_DEBUG": "true",
        "MCP_HOT_RELOAD": "true",
        "MCP_METRICS_ENABLED": "true"
      }
    }
  }
}
```

## Custom Configurations

### Custom Config File

```json
{
  "mcpServers": {
    "mcp-learning-server-custom": {
      "command": "python",
      "args": [
        "-m", "mcp_server",
        "--config", "my_config.json"
      ],
      "cwd": "/path/to/your/mcp-learning-server",
      "env": {
        "PYTHONPATH": "/path/to/your/mcp-learning-server"
      }
    }
  }
}
```

### Custom Resource Directory

```json
{
  "mcpServers": {
    "mcp-learning-server-custom-resources": {
      "command": "python",
      "args": [
        "-m", "mcp_server",
        "--resource-dir", "/path/to/custom/resources",
        "--tools-dir", "/path/to/custom/tools"
      ],
      "cwd": "/path/to/your/mcp-learning-server",
      "env": {
        "PYTHONPATH": "/path/to/your/mcp-learning-server"
      }
    }
  }
}
```

## Platform-Specific Examples

### macOS

```json
{
  "mcpServers": {
    "mcp-learning-server": {
      "command": "/usr/local/bin/python3",
      "args": ["-m", "mcp_server"],
      "cwd": "/Users/username/projects/mcp-learning-server",
      "env": {
        "PYTHONPATH": "/Users/username/projects/mcp-learning-server",
        "PATH": "/usr/local/bin:/usr/bin:/bin"
      }
    }
  }
}
```

### Windows

```json
{
  "mcpServers": {
    "mcp-learning-server": {
      "command": "C:\\Python39\\python.exe",
      "args": ["-m", "mcp_server"],
      "cwd": "C:\\Users\\username\\projects\\mcp-learning-server",
      "env": {
        "PYTHONPATH": "C:\\Users\\username\\projects\\mcp-learning-server"
      }
    }
  }
}
```

### Linux

```json
{
  "mcpServers": {
    "mcp-learning-server": {
      "command": "/usr/bin/python3",
      "args": ["-m", "mcp_server"],
      "cwd": "/home/username/projects/mcp-learning-server",
      "env": {
        "PYTHONPATH": "/home/username/projects/mcp-learning-server",
        "PATH": "/usr/local/bin:/usr/bin:/bin"
      }
    }
  }
}
```

## Multiple Server Configurations

### Production and Development

```json
{
  "mcpServers": {
    "mcp-learning-server": {
      "command": "python",
      "args": ["-m", "mcp_server"],
      "cwd": "/path/to/mcp-learning-server"
    },
    "mcp-learning-server-dev": {
      "command": "python",
      "args": [
        "-m", "mcp_server",
        "--debug",
        "--hot-reload"
      ],
      "cwd": "/path/to/mcp-learning-server-dev"
    }
  }
}
```

### Different Tool Sets

```json
{
  "mcpServers": {
    "mcp-basic-tools": {
      "command": "python",
      "args": [
        "-m", "mcp_server",
        "--categories", "calculator", "utility"
      ],
      "cwd": "/path/to/mcp-learning-server"
    },
    "mcp-file-tools": {
      "command": "python",
      "args": [
        "-m", "mcp_server",
        "--categories", "file", "data"
      ],
      "cwd": "/path/to/mcp-learning-server"
    }
  }
}
```

## Advanced Configurations

### With Logging

```json
{
  "mcpServers": {
    "mcp-learning-server-logged": {
      "command": "python",
      "args": [
        "-m", "mcp_server",
        "--debug",
        "--log-level", "INFO"
      ],
      "cwd": "/path/to/your/mcp-learning-server",
      "env": {
        "PYTHONPATH": "/path/to/your/mcp-learning-server",
        "MCP_LOG_FILE": "/path/to/logs/mcp_server.log"
      }
    }
  }
}
```

### Performance Monitoring

```json
{
  "mcpServers": {
    "mcp-learning-server-monitored": {
      "command": "python",
      "args": [
        "-m", "mcp_server",
        "--metrics",
        "--debug"
      ],
      "cwd": "/path/to/your/mcp-learning-server",
      "env": {
        "PYTHONPATH": "/path/to/your/mcp-learning-server",
        "MCP_METRICS_ENABLED": "true",
        "MCP_ENABLE_PROFILING": "true"
      }
    }
  }
}
```

## Configuration File Locations

### macOS
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

### Windows
```
%APPDATA%\Claude\claude_desktop_config.json
```

### Linux
```
~/.config/Claude/claude_desktop_config.json
```

## Troubleshooting Configurations

### Test Configuration

```json
{
  "mcpServers": {
    "mcp-learning-server-test": {
      "command": "python",
      "args": [
        "-m", "mcp_server",
        "--debug",
        "--test-mode"
      ],
      "cwd": "/path/to/your/mcp-learning-server",
      "env": {
        "PYTHONPATH": "/path/to/your/mcp-learning-server",
        "MCP_DEBUG": "true",
        "MCP_TEST_MODE": "true"
      }
    }
  }
}
```

### Minimal Configuration (for debugging)

```json
{
  "mcpServers": {
    "mcp-minimal": {
      "command": "python",
      "args": ["-c", "print('Hello from Python')"],
      "cwd": "/path/to/your/mcp-learning-server"
    }
  }
}
```

## Best Practices

1. **Use absolute paths** for `cwd` and `command` to avoid path issues
2. **Set PYTHONPATH** to ensure proper module imports
3. **Use descriptive server names** to distinguish between configurations
4. **Enable debug mode** during development for better error messages
5. **Test configurations** with minimal setups first
6. **Keep production and development** configurations separate
7. **Document custom configurations** for team members
8. **Use environment variables** for sensitive or environment-specific values

## Validation

To validate your configuration:

1. **Test the command manually** in terminal first
2. **Check Claude Desktop logs** for connection errors
3. **Use debug mode** to see detailed error messages
4. **Verify file paths** exist and are accessible
5. **Test with minimal configuration** first, then add complexity

## Common Issues

- **Path not found**: Check `cwd` and `command` paths
- **Module not found**: Ensure `PYTHONPATH` is set correctly
- **Permission denied**: Check file permissions and user access
- **Server won't start**: Test the command manually in terminal
- **Tools not loading**: Check for Python syntax errors in tool files
