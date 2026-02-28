#!/bin/bash
# Quick start script for Pancake MCP Server

echo "🚀 Starting Pancake MCP Server..."

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker Desktop/Daemon first."
    exit 1
fi

# Check for .env file
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "📋 Creating .env from example..."
        cp .env.example .env
        echo "💡 Please edit .env to add your API keys"
    fi
fi

# Start the service
echo "🏗️ Building and starting MCP server..."
docker compose up --build -d

# Wait and check status
echo "⏳ Waiting for server to start..."
sleep 10

if docker compose ps | grep -q "Up"; then
    echo "✅ MCP Server is running!"
    echo "🌐 Access at: http://localhost:8000"
    echo "📋 View logs: docker compose logs -f"
    echo "🛑 Stop server: docker compose down"
else
    echo "❌ Server failed to start. Check logs:"
    docker compose logs
fi