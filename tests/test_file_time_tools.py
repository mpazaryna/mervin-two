"""
Test File Reader and Time Tools Implementation
"""

import pytest
import os
import sys
import tempfile
import datetime
from unittest.mock import patch

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.file_tools import file_reader, file_info, list_files, search_files, _validate_file_path
from tools.utilities import time_tool, time_calculator


class TestFileTools:
    """Test file reader and file system tools."""
    
    def test_file_reader_basic(self):
        """Test basic file reading functionality."""
        # Test reading the sample file
        content = file_reader("sample.txt")
        assert isinstance(content, str)
        assert len(content) > 0
        assert "sample text file" in content.lower()
    
    def test_file_reader_json(self):
        """Test reading JSON file."""
        content = file_reader("config.json")
        assert isinstance(content, str)
        assert "MCP Learning Server" in content
        assert "{" in content  # Should be JSON format
    
    def test_file_reader_markdown(self):
        """Test reading markdown file."""
        content = file_reader("README.md")
        assert isinstance(content, str)
        assert "# MCP Learning Server Resources" in content
    
    def test_file_reader_subdirectory(self):
        """Test reading file from subdirectory."""
        content = file_reader("logs/app.log")
        assert isinstance(content, str)
        assert "Server starting up" in content
    
    def test_file_reader_encoding(self):
        """Test file reading with different encodings."""
        content = file_reader("sample.txt", encoding="utf-8")
        assert isinstance(content, str)
        
        # Test with ASCII encoding
        content_ascii = file_reader("sample.txt", encoding="ascii")
        assert isinstance(content_ascii, str)
    
    def test_file_reader_max_size(self):
        """Test file size limits."""
        # Should work with reasonable size limit
        content = file_reader("sample.txt", max_size=10000)
        assert isinstance(content, str)
        
        # Should fail with very small size limit
        with pytest.raises(ValueError, match="File too large"):
            file_reader("sample.txt", max_size=10)
    
    def test_file_reader_not_found(self):
        """Test file not found error."""
        with pytest.raises(ValueError, match="File not found"):
            file_reader("nonexistent.txt")
    
    def test_file_reader_security(self):
        """Test security restrictions."""
        # Should not allow access outside resources directory
        with pytest.raises(ValueError, match="Access denied"):
            file_reader("../README.md")
        
        with pytest.raises(ValueError, match="Access denied"):
            file_reader("/etc/passwd")
        
        with pytest.raises(ValueError, match="Access denied"):
            file_reader("../../etc/passwd")
    
    def test_validate_file_path(self):
        """Test file path validation."""
        # Valid paths
        valid_path = _validate_file_path("sample.txt")
        assert "resources" in valid_path
        assert valid_path.endswith("sample.txt")
        
        # Invalid paths
        with pytest.raises(ValueError):
            _validate_file_path("../outside.txt")
        
        with pytest.raises(ValueError):
            _validate_file_path("/absolute/path.txt")
    
    def test_file_info(self):
        """Test file information retrieval."""
        info = file_info("sample.txt")
        
        assert isinstance(info, dict)
        assert "path" in info
        assert "size" in info
        assert "size_human" in info
        assert "is_file" in info
        assert "is_directory" in info
        assert "created" in info
        assert "modified" in info
        assert "permissions" in info
        
        assert info["path"] == "sample.txt"
        assert info["is_file"] == True
        assert info["is_directory"] == False
        assert info["size"] > 0
        assert isinstance(info["permissions"], dict)
    
    def test_file_info_directory(self):
        """Test file info for directory."""
        info = file_info("logs")
        
        assert info["is_file"] == False
        assert info["is_directory"] == True
        assert info["path"] == "logs"
    
    def test_list_files_root(self):
        """Test listing files in root directory."""
        result = list_files()
        
        assert isinstance(result, dict)
        assert "files" in result
        assert "directories" in result
        assert "total_files" in result
        assert "total_directories" in result
        
        # Check that our test files are listed
        file_names = [f["name"] for f in result["files"]]
        assert "sample.txt" in file_names
        assert "config.json" in file_names
        
        # Check that directories are listed
        dir_names = [d["name"] for d in result["directories"]]
        assert "logs" in dir_names
        assert "docs" in dir_names
    
    def test_list_files_subdirectory(self):
        """Test listing files in subdirectory."""
        result = list_files("logs")
        
        assert result["directory"] == "logs"
        file_names = [f["name"] for f in result["files"]]
        assert "app.log" in file_names
    
    def test_list_files_filter(self):
        """Test listing files with type filter."""
        result = list_files(file_types=[".json"])
        
        file_names = [f["name"] for f in result["files"]]
        assert "config.json" in file_names
        # Should not include non-JSON files
        assert "sample.txt" not in file_names
    
    def test_search_files_filename(self):
        """Test searching files by filename."""
        result = search_files("sample", search_type="filename")
        
        assert isinstance(result, dict)
        assert "matches" in result
        assert "total_matches" in result
        assert result["query"] == "sample"
        
        # Should find sample.txt
        assert result["total_matches"] > 0
        match_files = [m["file"] for m in result["matches"]]
        assert "sample.txt" in match_files
    
    def test_search_files_content(self):
        """Test searching files by content."""
        result = search_files("Server", search_type="content")
        
        assert result["total_matches"] > 0
        # Should find files containing "Server"
        match_files = [m["file"] for m in result["matches"]]
        # config.json contains "MCP Learning Server"
        assert any("config.json" in f for f in match_files)
    
    def test_search_files_case_sensitive(self):
        """Test case sensitive search."""
        # Case insensitive (default)
        result1 = search_files("SERVER", search_type="content", case_sensitive=False)
        
        # Case sensitive
        result2 = search_files("SERVER", search_type="content", case_sensitive=True)
        
        # Case insensitive should find more matches
        assert result1["total_matches"] >= result2["total_matches"]


class TestTimeTools:
    """Test time-related tools."""
    
    def test_time_tool_iso(self):
        """Test ISO time format."""
        result = time_tool("iso")
        assert isinstance(result, str)
        assert "T" in result  # ISO format contains T
        
        # Should be parseable as datetime
        datetime.datetime.fromisoformat(result)
    
    def test_time_tool_unix(self):
        """Test Unix timestamp format."""
        result = time_tool("unix")
        assert isinstance(result, str)
        assert result.isdigit()
        
        # Should be a reasonable timestamp (after 2020)
        timestamp = int(result)
        assert timestamp > 1577836800  # 2020-01-01
    
    def test_time_tool_human(self):
        """Test human-readable format."""
        result = time_tool("human")
        assert isinstance(result, str)
        assert "-" in result  # Date separator
        assert ":" in result  # Time separator
        
        # Should match expected format
        datetime.datetime.strptime(result, "%Y-%m-%d %H:%M:%S")
    
    def test_time_tool_utc(self):
        """Test UTC format."""
        result = time_tool("utc")
        assert isinstance(result, str)
        assert result.endswith("Z")  # UTC indicator
    
    def test_time_tool_custom(self):
        """Test custom format."""
        custom_format = "%Y-%m-%d"
        result = time_tool("custom", custom_format=custom_format)
        assert isinstance(result, str)
        
        # Should match custom format
        datetime.datetime.strptime(result, custom_format)
    
    def test_time_tool_custom_missing_format(self):
        """Test custom format without format string."""
        with pytest.raises(ValueError, match="custom_format is required"):
            time_tool("custom")
    
    def test_time_tool_invalid_format(self):
        """Test invalid time format."""
        with pytest.raises(ValueError, match="Unknown time format"):
            time_tool("invalid")
    
    def test_time_tool_timezone(self):
        """Test timezone parameter."""
        local_time = time_tool("iso", timezone="local")
        utc_time = time_tool("iso", timezone="utc")
        
        assert isinstance(local_time, str)
        assert isinstance(utc_time, str)
        # Times should be different (unless running in UTC)
        # Just verify they're both valid ISO format
        datetime.datetime.fromisoformat(local_time)
        datetime.datetime.fromisoformat(utc_time)
    
    def test_time_calculator_add_days(self):
        """Test adding days to a date."""
        result = time_calculator("add_days", date="2023-12-07", amount=5)
        assert result == "2023-12-12T00:00:00"
    
    def test_time_calculator_subtract_days(self):
        """Test subtracting days from a date."""
        result = time_calculator("subtract_days", date="2023-12-07", amount=2)
        assert result == "2023-12-05T00:00:00"
    
    def test_time_calculator_add_hours(self):
        """Test adding hours to a datetime."""
        result = time_calculator("add_hours", date="2023-12-07T10:00:00", amount=5)
        assert result == "2023-12-07T15:00:00"
    
    def test_time_calculator_days_between(self):
        """Test calculating days between dates."""
        result = time_calculator("days_between", date="2023-12-01", end_date="2023-12-07")
        assert result == 6
    
    def test_time_calculator_format_date(self):
        """Test date formatting."""
        result = time_calculator("format_date", date="2023-12-07", output_format="human")
        assert result == "2023-12-07 00:00:00"
    
    def test_time_calculator_missing_amount(self):
        """Test missing amount parameter."""
        with pytest.raises(ValueError, match="amount is required"):
            time_calculator("add_days", date="2023-12-07")
    
    def test_time_calculator_missing_end_date(self):
        """Test missing end_date parameter."""
        with pytest.raises(ValueError, match="Both date and end_date are required"):
            time_calculator("days_between", date="2023-12-07")
    
    def test_time_calculator_invalid_date(self):
        """Test invalid date format."""
        with pytest.raises(ValueError, match="Invalid date format"):
            time_calculator("add_days", date="invalid-date", amount=1)
    
    def test_time_calculator_unknown_operation(self):
        """Test unknown operation."""
        with pytest.raises(ValueError, match="Unknown operation"):
            time_calculator("invalid_operation", date="2023-12-07")


class TestFileToolsIntegration:
    """Test integration of file tools with the registry."""
    
    def test_tools_registered(self):
        """Test that file tools are registered."""
        from tools.registry import registry
        import tools.file_tools  # Import to trigger registration
        
        tools = registry.list_tools()
        tool_names = [tool["name"] for tool in tools]
        
        assert "file_reader" in tool_names
        assert "file_info" in tool_names
        assert "list_files" in tool_names
        assert "search_files" in tool_names
    
    def test_file_category(self):
        """Test file tools are in correct category."""
        from tools.registry import registry
        
        categories = registry.list_categories()
        assert "file" in categories
        
        file_tools = categories["file"]
        assert "file_reader" in file_tools
        assert "file_info" in file_tools
