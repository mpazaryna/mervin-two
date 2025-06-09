"""
Test basic setup and imports
"""

import pytest
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mcp_server
from mcp_server.logging_config import setup_logger, get_logger


def test_package_import():
    """Test that the main package can be imported."""
    assert mcp_server.__version__ == "0.1.0"
    assert mcp_server.__author__ == "MCP Learning Project"


def test_logging_setup():
    """Test that logging configuration works."""
    logger = setup_logger("test_logger", "DEBUG")
    assert logger.name == "test_logger"
    assert logger.level == 10  # DEBUG level


def test_logging_setup_with_file():
    """Test that logging configuration works with file logging."""
    import tempfile

    # Test with file logging
    with tempfile.NamedTemporaryFile(delete=False, suffix='.log') as f:
        log_file = f.name

    try:
        logger = setup_logger("test_file_logger", "INFO", log_file=log_file)
        assert logger.name == "test_file_logger"
        assert logger.level == 20  # INFO level

        # Test that we can log to the file
        logger.info("Test message")

        # Check if log file was created and has content
        assert os.path.exists(log_file)
        with open(log_file, 'r') as f:
            content = f.read()
            assert "Test message" in content

    finally:
        # Clean up
        if os.path.exists(log_file):
            os.unlink(log_file)


def test_mcp_server_initialization():
    """Test that MCPLearningServer can be initialized without errors."""
    from mcp_server.config import MCPServerConfig
    from mcp_server.app import MCPLearningServer

    # Create config
    config = MCPServerConfig()
    config.debug = True

    # This should not fail with the log_file parameter error
    server = MCPLearningServer(config)
    assert server is not None
    assert server.config.debug is True

    # Clean shutdown
    server.shutdown()


def test_get_logger():
    """Test getting an existing logger."""
    logger1 = get_logger("test_logger_2")
    logger2 = get_logger("test_logger_2")
    assert logger1 is logger2


def test_project_structure():
    """Test that required directories exist."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    required_dirs = [
        "mcp_server",
        "tools", 
        "resources",
        "tests"
    ]
    
    for dir_name in required_dirs:
        dir_path = os.path.join(project_root, dir_name)
        assert os.path.isdir(dir_path), f"Directory {dir_name} should exist"


def test_required_files():
    """Test that required files exist."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    required_files = [
        "requirements.txt",
        "README.md",
        "setup.py",
        ".gitignore"
    ]
    
    for file_name in required_files:
        file_path = os.path.join(project_root, file_name)
        assert os.path.isfile(file_path), f"File {file_name} should exist"


def test_sample_resource():
    """Test that sample resource file exists and is readable."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sample_file = os.path.join(project_root, "resources", "sample.txt")
    
    assert os.path.isfile(sample_file), "Sample resource file should exist"
    
    with open(sample_file, 'r') as f:
        content = f.read()
        assert len(content) > 0, "Sample file should have content"
        assert "sample text file" in content.lower(), "Sample file should contain expected content"
