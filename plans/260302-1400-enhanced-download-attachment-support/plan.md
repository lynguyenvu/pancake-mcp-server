# Plan: Enhance download_attachment to Support Local Machine Mounting

## Context
The Pancake MCP server currently has a `download_attachment` function in `src/pancake_mcp/tools/attachments.py` that downloads attachments to a local directory within the container. The user wants to enhance this functionality to support mounting directories from the local machine, allowing downloaded files to be saved directly to the host system.

## Current Implementation Analysis
- The `download_attachment` function (lines 93-178 in `src/pancake_mcp/tools/attachments.py`) currently saves files to a configurable directory within the container (default: `./downloads`)
- The function creates the download directory with `Path(download_dir).mkdir(parents=True, exist_ok=True)`
- Files are saved using standard Python file operations (`with open(file_path, 'wb') as f`)
- Currently supports relative paths like `./downloads` but has no mechanism to ensure the path is within allowed boundaries

## Requirements
- Modify the `download_attachment` function to support saving to mounted directories from the local machine
- Maintain security by preventing path traversal attacks
- Allow users to specify paths that map to mounted volumes
- Preserve existing functionality for backward compatibility

## Implementation Approach

### Enhanced Path Validation and Mount Support (Recommended)
- Add comprehensive path validation to prevent directory traversal (e.g., `../../../etc/passwd`)
- Allow configurable base directories for downloads via environment variables
- Implement filename sanitization to prevent security issues
- Add directory write permission checks
- Maintain backward compatibility with default `./downloads` directory
- Support Docker volume mounts by defining allowed paths

## Critical Files to Modify
- `pancake-mcp-server/src/pancake_mcp/tools/attachments.py` - Main implementation (download_attachment function)
- Potentially `docker-compose.yml` or `docker-compose.prod.yml` - For volume configuration examples in documentation

## Implementation Steps
1. Add path validation and sanitization utilities to prevent directory traversal
2. Add configuration function to get allowed download directories
3. Update the `download_attachment` function with enhanced security measures:
   - Validate download directory against allowed paths
   - Check directory write permissions
   - Sanitize filenames to prevent path traversal
   - Maintain all existing functionality
4. Add documentation for mounting volumes in Docker configuration
5. Test the functionality with various scenarios

## Security Considerations
- Prevent directory traversal attacks using path resolution and validation
- Validate that the download path is within allowed directories
- Sanitize filenames to remove dangerous characters
- Check directory write permissions before attempting to save
- Add appropriate error handling for invalid paths

## Verification
- ✅ Test with various path inputs to ensure security
- ✅ Verify that mounted volumes work correctly
- ✅ Test backward compatibility with existing usage
- ✅ Confirm that the function still returns proper JSON response format
- ✅ Test with Docker volume mounts to ensure they work as expected

## Status
✅ IMPLEMENTATION COMPLETE

All requirements have been successfully implemented with proper security measures and documentation.