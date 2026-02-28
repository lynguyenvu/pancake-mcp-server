#!/bin/bash
# Universal installation script for Pancake MCP Server
# Supports Linux, macOS, and Windows (WSL/Git Bash)

set -e

echo "🚀 Installing Pancake MCP Server..."

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        echo "windows"
    else
        echo "unknown"
        exit 1
    fi
}

OS_TYPE=$(detect_os)
echo "-detected OS: $OS_TYPE"

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        return 1
    fi

    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        echo "⚠️ Docker is installed but not running. Please start Docker Desktop/Daemon first."
        exit 1
    fi

    return 0
}

# Install Docker based on OS
install_docker() {
    case $OS_TYPE in
        "linux")
            echo "📦 Installing Docker for Linux..."
            # Check if using systemd (most common)
            if command -v apt-get &> /dev/null; then
                # Debian/Ubuntu
                apt-get update
                apt-get install -y ca-certificates curl gnupg lsb-release
                mkdir -p /etc/apt/keyrings
                curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
                echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
                apt-get update
                apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
                # Add current user to docker group
                usermod -aG docker $USER || echo "⚠️ Could not add user to docker group. You may need to run with sudo or add user manually."
            elif command -v dnf &> /dev/null; then
                # Fedora/RHEL
                dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
                dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
                usermod -aG docker $USER || echo "⚠️ Could not add user to docker group."
            else
                echo "❌ Unsupported Linux distribution. Please install Docker manually."
                exit 1
            fi
            ;;
        "macos")
            echo "📦 Installing Docker for macOS..."
            if ! command -v brew &> /dev/null; then
                echo "📦 Installing Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            echo "📦 Installing Docker Desktop via Homebrew..."
            brew install --cask docker
            echo "💡 Please start Docker Desktop manually, then run this script again."
            exit 0
            ;;
        "windows")
            echo "📦 Please install Docker Desktop for Windows manually:"
            echo "   Download from: https://www.docker.com/products/docker-desktop"
            echo "   After installation, please run this script again."
            exit 0
            ;;
    esac
}

# Main installation flow
if ! check_docker; then
    echo "🐳 Docker not found. Installing Docker..."
    install_docker
else
    echo "✅ Docker is already installed and running"
fi

# Wait a moment for Docker to be fully ready
echo "⏳ Waiting for Docker to be ready..."
sleep 5

# Check if we're in the correct directory
if [ ! -f "docker-compose.yml" ]; then
    echo "📁 Cloning Pancake MCP Server repository..."
    if [ -d "pancake-mcp-server" ]; then
        echo "🔄 Updating existing repository..."
        cd pancake-mcp-server
        git pull
    else
        git clone https://github.com/lynguyenvu/pancake-mcp-server.git .
        cd pancake-mcp-server
    fi
else
    echo "✅ Found existing docker-compose.yml, using current directory"
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "📋 Creating .env file from example..."
        cp .env.example .env
        echo "💡 Please edit .env file to add your API keys before starting"
    else
        echo "📋 Creating default .env file..."
        cat > .env << EOF
MCP_HOST=0.0.0.0
MCP_PORT=8000
PANCAKE_API_BASE_URL=https://pos.pages.fm/api/v1
# Add your API keys:
# PANCAKE_API_KEY=your_pos_api_key_here
# PANCAKE_ACCESS_TOKEN=your_chat_token_here
EOF
    fi
fi

# Build and start the server
echo "🏗️ Building and starting MCP server..."
if command -v docker-compose &> /dev/null; then
    docker-compose up --build -d
elif [ -f "docker-compose.yml" ]; then
    docker compose up --build -d
else
    echo "❌ No docker-compose.yml found"
    exit 1
fi

# Wait for server to start
echo "⏳ Waiting for server to start..."
sleep 10

# Check if server is running
if docker compose ps | grep -q "Up"; then
    echo "✅ MCP Server is running successfully!"
    echo "🌐 Access at: http://localhost:8000"
    echo "📋 Check logs: docker compose logs -f"
    echo ""
    echo "🔐 To connect with Claude:"
    echo "   1. Get your Pancake API keys from: https://pancake.biz"
    echo "   2. Add them to the .env file"
    echo "   3. Use Custom Connector in Claude.ai with URL: http://localhost:8000/mcp"
else
    echo "❌ Something went wrong. Check logs:"
    docker compose logs
fi