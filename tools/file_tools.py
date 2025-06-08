"""
File Reader and File System Tools

Provides secure file reading capabilities and file system utilities
for the MCP Learning Server. All file operations are restricted to
the resources directory for security.
"""

import os
import stat
import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from .registry import tool


# Base directory for file operations (security boundary)
RESOURCES_DIR = os.path.abspath("./resources")


def _validate_file_path(file_path: str) -> str:
    """
    Validate and normalize file path for security.
    
    Args:
        file_path: Relative file path
        
    Returns:
        Absolute path within resources directory
        
    Raises:
        ValueError: If path is outside resources directory
    """
    # Normalize the path and make it absolute
    abs_path = os.path.abspath(os.path.join(RESOURCES_DIR, file_path))
    
    # Security check - ensure path is within resources directory
    if not abs_path.startswith(RESOURCES_DIR):
        raise ValueError(f"Access denied: Cannot access files outside resources directory")
    
    return abs_path


@tool(
    name="file_reader",
    description="Read content from local text files in the resources directory",
    parameter_schema={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Relative path to file within resources directory"
            },
            "encoding": {
                "type": "string",
                "default": "utf-8",
                "enum": ["utf-8", "ascii", "latin-1"],
                "description": "Text encoding to use when reading file"
            },
            "max_size": {
                "type": "integer",
                "default": 1048576,
                "minimum": 1,
                "maximum": 10485760,
                "description": "Maximum file size to read in bytes (default: 1MB, max: 10MB)"
            }
        },
        "required": ["file_path"]
    },
    return_schema={
        "type": "string",
        "description": "Content of the file"
    },
    examples=[
        {"file_path": "sample.txt", "result": "File content here..."},
        {"file_path": "data/config.json", "encoding": "utf-8", "result": "JSON content..."}
    ],
    category="file"
)
def file_reader(file_path: str, encoding: str = "utf-8", max_size: int = 1048576) -> str:
    """
    Read content from a text file in the resources directory.
    
    Args:
        file_path: Relative path to file within resources directory
        encoding: Text encoding to use
        max_size: Maximum file size to read in bytes
        
    Returns:
        Content of the file
        
    Raises:
        ValueError: For various file access errors
    """
    try:
        abs_path = _validate_file_path(file_path)
        
        # Check if file exists
        if not os.path.isfile(abs_path):
            raise ValueError(f"File not found: {file_path}")
        
        # Check file size
        file_size = os.path.getsize(abs_path)
        if file_size > max_size:
            raise ValueError(f"File too large: {file_size} bytes (max: {max_size} bytes)")
        
        # Read the file
        with open(abs_path, 'r', encoding=encoding) as file:
            content = file.read()
        
        return content
        
    except FileNotFoundError:
        raise ValueError(f"File not found: {file_path}")
    except PermissionError:
        raise ValueError(f"Permission denied: {file_path}")
    except UnicodeDecodeError as e:
        raise ValueError(f"Encoding error reading {file_path}: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error reading file {file_path}: {str(e)}")


@tool(
    name="file_info",
    description="Get information about a file in the resources directory",
    parameter_schema={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Relative path to file within resources directory"
            }
        },
        "required": ["file_path"]
    },
    return_schema={
        "type": "object",
        "description": "File information including size, dates, and permissions"
    },
    examples=[
        {"file_path": "sample.txt", "result": {"size": 1024, "modified": "2023-12-07T10:30:00"}}
    ],
    category="file"
)
def file_info(file_path: str) -> Dict[str, Any]:
    """
    Get information about a file.
    
    Args:
        file_path: Relative path to file within resources directory
        
    Returns:
        Dictionary with file information
        
    Raises:
        ValueError: If file not found or access denied
    """
    try:
        abs_path = _validate_file_path(file_path)
        
        if not os.path.exists(abs_path):
            raise ValueError(f"File not found: {file_path}")
        
        stat_info = os.stat(abs_path)
        
        return {
            "path": file_path,
            "absolute_path": abs_path,
            "size": stat_info.st_size,
            "size_human": _format_file_size(stat_info.st_size),
            "is_file": os.path.isfile(abs_path),
            "is_directory": os.path.isdir(abs_path),
            "created": datetime.datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
            "modified": datetime.datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
            "accessed": datetime.datetime.fromtimestamp(stat_info.st_atime).isoformat(),
            "permissions": {
                "readable": os.access(abs_path, os.R_OK),
                "writable": os.access(abs_path, os.W_OK),
                "executable": os.access(abs_path, os.X_OK),
                "mode": oct(stat_info.st_mode)
            }
        }
        
    except Exception as e:
        raise ValueError(f"Error getting file info for {file_path}: {str(e)}")


@tool(
    name="list_files",
    description="List files and directories in the resources directory",
    parameter_schema={
        "type": "object",
        "properties": {
            "directory": {
                "type": "string",
                "default": "",
                "description": "Subdirectory within resources to list (empty for root)"
            },
            "include_hidden": {
                "type": "boolean",
                "default": False,
                "description": "Include hidden files (starting with .)"
            },
            "file_types": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Filter by file extensions (e.g., ['.txt', '.json'])"
            }
        }
    },
    return_schema={
        "type": "object",
        "description": "List of files and directories with their information"
    },
    examples=[
        {"directory": "", "result": {"files": ["sample.txt"], "directories": ["data"]}},
        {"directory": "data", "file_types": [".json"], "result": {"files": ["config.json"]}}
    ],
    category="file"
)
def list_files(directory: str = "", include_hidden: bool = False, 
               file_types: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    List files and directories in the resources directory.
    
    Args:
        directory: Subdirectory to list (relative to resources)
        include_hidden: Include hidden files
        file_types: Filter by file extensions
        
    Returns:
        Dictionary with files and directories lists
        
    Raises:
        ValueError: If directory not found or access denied
    """
    try:
        abs_path = _validate_file_path(directory)
        
        if not os.path.isdir(abs_path):
            raise ValueError(f"Directory not found: {directory}")
        
        files = []
        directories = []
        
        for item in os.listdir(abs_path):
            # Skip hidden files unless requested
            if not include_hidden and item.startswith('.'):
                continue
            
            item_path = os.path.join(abs_path, item)
            relative_path = os.path.join(directory, item) if directory else item
            
            if os.path.isfile(item_path):
                # Apply file type filter if specified
                if file_types:
                    file_ext = os.path.splitext(item)[1].lower()
                    if file_ext not in [ext.lower() for ext in file_types]:
                        continue
                
                stat_info = os.stat(item_path)
                files.append({
                    "name": item,
                    "path": relative_path,
                    "size": stat_info.st_size,
                    "size_human": _format_file_size(stat_info.st_size),
                    "modified": datetime.datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                    "extension": os.path.splitext(item)[1]
                })
            elif os.path.isdir(item_path):
                directories.append({
                    "name": item,
                    "path": relative_path
                })
        
        # Sort files and directories by name
        files.sort(key=lambda x: x["name"])
        directories.sort(key=lambda x: x["name"])
        
        return {
            "directory": directory or ".",
            "files": files,
            "directories": directories,
            "total_files": len(files),
            "total_directories": len(directories)
        }
        
    except Exception as e:
        raise ValueError(f"Error listing directory {directory}: {str(e)}")


@tool(
    name="search_files",
    description="Search for files by name or content in the resources directory",
    parameter_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query (filename pattern or content text)"
            },
            "search_type": {
                "type": "string",
                "enum": ["filename", "content", "both"],
                "default": "filename",
                "description": "Type of search to perform"
            },
            "case_sensitive": {
                "type": "boolean",
                "default": False,
                "description": "Whether search should be case sensitive"
            },
            "file_types": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Limit search to specific file extensions"
            }
        },
        "required": ["query"]
    },
    return_schema={
        "type": "object",
        "description": "Search results with matching files"
    },
    examples=[
        {"query": "sample", "search_type": "filename", "result": {"matches": ["sample.txt"]}},
        {"query": "hello", "search_type": "content", "result": {"matches": ["greeting.txt"]}}
    ],
    category="file"
)
def search_files(query: str, search_type: str = "filename", case_sensitive: bool = False,
                file_types: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Search for files by name or content.
    
    Args:
        query: Search query
        search_type: Type of search (filename, content, or both)
        case_sensitive: Whether search is case sensitive
        file_types: File extensions to search
        
    Returns:
        Dictionary with search results
        
    Raises:
        ValueError: For search errors
    """
    try:
        matches = []
        search_query = query if case_sensitive else query.lower()
        
        # Walk through all files in resources directory
        for root, dirs, files in os.walk(RESOURCES_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, RESOURCES_DIR)
                
                # Apply file type filter
                if file_types:
                    file_ext = os.path.splitext(file)[1].lower()
                    if file_ext not in [ext.lower() for ext in file_types]:
                        continue
                
                match_info = {
                    "file": relative_path,
                    "match_type": [],
                    "size": os.path.getsize(file_path)
                }
                
                # Filename search
                if search_type in ["filename", "both"]:
                    filename = file if case_sensitive else file.lower()
                    if search_query in filename:
                        match_info["match_type"].append("filename")
                
                # Content search
                if search_type in ["content", "both"]:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if not case_sensitive:
                                content = content.lower()
                            if search_query in content:
                                match_info["match_type"].append("content")
                    except (UnicodeDecodeError, PermissionError):
                        # Skip files that can't be read as text
                        pass
                
                # Add to matches if any match found
                if match_info["match_type"]:
                    matches.append(match_info)
        
        return {
            "query": query,
            "search_type": search_type,
            "case_sensitive": case_sensitive,
            "matches": matches,
            "total_matches": len(matches)
        }
        
    except Exception as e:
        raise ValueError(f"Error searching files: {str(e)}")


def _format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"
