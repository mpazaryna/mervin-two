# MCP Learning Server Resources

This directory contains sample files for testing the file reader tool and demonstrating various file operations.

## Available Files

### Text Files
- `sample.txt` - Basic text file for testing file reading
- `README.md` - This markdown file with documentation

### Data Files
- `config.json` - JSON configuration file example
- `data.csv` - CSV data file with sample records

### Subdirectories
- `logs/` - Directory containing log files
- `docs/` - Directory with additional documentation

## File Reader Tool Usage

The file reader tool can access any file within this resources directory. Examples:

```
file_reader(file_path="sample.txt")
file_reader(file_path="config.json")
file_reader(file_path="logs/app.log")
```

## Security

All file operations are restricted to this resources directory for security. Attempts to access files outside this directory will be denied.

## File Types Supported

- Text files (.txt)
- JSON files (.json)
- Markdown files (.md)
- CSV files (.csv)
- Log files (.log)
- Any other text-based files

## File Size Limits

- Default maximum file size: 1MB
- Configurable up to 10MB
- Large files will be rejected to prevent memory issues
