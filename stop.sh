#!/bin/bash
# Stop script for Pancake MCP Server

echo "🛑 Stopping Pancake MCP Server..."

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running."
    exit 1
fi

# Stop the service
docker compose down

echo "✅ MCP Server stopped!"