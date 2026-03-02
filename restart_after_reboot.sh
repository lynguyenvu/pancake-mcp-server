#!/bin/bash

echo "🔄 Restarting Pancake MCP Server after reboot..."

# Navigate to the correct directory
cd /cowork_mcp/pancake-mcp-server || { echo "❌ Cannot find pancake-mcp-server directory"; exit 1; }

echo "🐳 Starting Docker containers..."
docker compose up -d

# Wait for the server to be ready
echo "⏳ Waiting for server to be ready..."
sleep 10

# Check if the server is running
if docker compose ps | grep -q "healthy"; then
    echo "✅ Server is running and healthy"

    # Check if ngrok is available and start tunnel if needed
    if command -v ngrok &> /dev/null; then
        echo "🔗 Starting Ngrok tunnel..."

        # Kill any existing ngrok processes
        pkill ngrok 2>/dev/null

        # Start ngrok in background
        ngrok http 8000 > /dev/null 2>&1 &

        # Wait a bit for ngrok to start
        sleep 5

        # Get the ngrok URL
        NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])" 2>/dev/null)

        if [ ! -z "$NGROK_URL" ]; then
            echo "🌐 Ngrok tunnel is ready: $NGROK_URL"
            echo ""
            echo "📋 To connect to Claude AI, use this MCP Server URL:"
            echo "   $NGROK_URL/mcp"
            echo ""
            echo "🔐 Authentication: Use your Pancake API key as Bearer token"
        else
            echo "⚠️  Ngrok tunnel may still be starting, please check http://localhost:4040"
        fi
    else
        echo "💡 Ngrok not found. Install it with: brew install ngrok (macOS) or download from https://ngrok.com"
        echo "💡 For production, consider using a reverse proxy with SSL instead of ngrok"
    fi

else
    echo "❌ Server failed to start. Check with: docker compose logs"
    exit 1
fi

echo ""
echo "🎉 Restart completed!"
echo "📊 Check status: docker compose ps"
echo "📖 View logs: docker compose logs -f"
echo "🛑 Stop server: ./stop.sh"