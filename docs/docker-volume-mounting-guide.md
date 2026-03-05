# Docker Volume Mounting Guide for Pancake MCP Server

## Overview
This guide explains how to configure Docker volume mounts to allow the `download_attachment` function to save files directly to your local machine's filesystem.

## Environment Variable Configuration

The Pancake MCP server supports specifying allowed download paths through the `ALLOWED_DOWNLOAD_PATHS` environment variable. This variable accepts a colon-separated list of directories that are permitted for file downloads.

### Setting ALLOWED_DOWNLOAD_PATHS

In your `.env` file:
```env
ALLOWED_DOWNLOAD_PATHS=/home/user/downloads:/opt/shared:/var/host-data
```

Or when running Docker directly:
```bash
docker run -e ALLOWED_DOWNLOAD_PATHS="/home/user/downloads:/opt/shared" -v /home/user/downloads:/home/user/downloads -v /opt/shared:/opt/shared pancake-mcp-server
```

## Docker Compose Configuration

To mount local directories when using Docker Compose, add volume mounts to your `docker-compose.yml`:

```yaml
version: '3.8'

services:
  pancake-mcp:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PANCAKE_API_KEY=${PANCAKE_API_KEY}
      - PANCAKE_ACCESS_TOKEN=${PANCAKE_ACCESS_TOKEN}
      - ALLOWED_DOWNLOAD_PATHS=/host-downloads:/shared-data
    volumes:
      - /home/user/local-downloads:/host-downloads
      - /opt/shared:/shared-data
      # You can also mount specific directories
      - ./project-downloads:/app/downloads
    command: ["pancake-mcp-http"]
```

## Using with Claude Desktop (stdio mode)

When using Docker volumes with Claude Desktop, update your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "pancake-mcp": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "PANCAKE_API_KEY=your_pos_api_key",
        "-e", "PANCAKE_ACCESS_TOKEN=your_chat_access_token",
        "-e", "ALLOWED_DOWNLOAD_PATHS=/host-downloads",
        "-v", "/home/user/local-downloads:/host-downloads",
        "-e", "PYTHONPATH=/app/src",
        "pancake-mcp-server-pancake-mcp:latest",
        "pancake-mcp-stdio"
      ]
    }
  }
}
```

## Security Considerations

1. **Path Validation**: The server validates that download paths are within allowed directories to prevent directory traversal attacks.

2. **File Sanitization**: All filenames are sanitized to remove potentially dangerous characters and path traversal sequences.

3. **Permission Checks**: The server verifies write permissions on the target directory before attempting to save files.

4. **Safe Paths Only**: Only paths explicitly listed in `ALLOWED_DOWNLOAD_PATHS` are permitted for file downloads.

## Example Usage

Once configured, you can use the `download_attachment` function with mounted paths:

```python
# This will work if /host-downloads is in ALLOWED_DOWNLOAD_PATHS and mounted
result = await download_attachment(
    page_id="page123",
    conversation_id="conv456",
    customer_id="cust789",
    message_index=0,
    attachment_index=0,
    download_dir="/host-downloads"
)

# This will also work for the default downloads directory
result = await download_attachment(
    page_id="page123",
    conversation_id="conv456",
    customer_id="cust789",
    message_index=0,
    attachment_index=0
    # Uses default "./downloads" which maps to container's ./downloads
)
```

## Troubleshooting

### Permission Denied Errors
- Ensure the Docker container has write permissions to the mounted volume
- On Linux, you may need to adjust directory ownership or permissions:
  ```bash
  sudo chown -R $(id -u):$(id -g) /path/to/local/directory
  ```

### Path Not Allowed Error
- Verify that the path is included in the `ALLOWED_DOWNLOAD_PATHS` environment variable
- Make sure the path in your function call matches exactly with the allowed path

### Volume Not Persisting Data
- Ensure you're using the correct volume syntax: `-v /local/path:/container/path`
- Check that the local path exists before starting the container