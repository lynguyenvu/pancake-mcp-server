@echo off
REM Installation script for Pancake MCP Server on Windows

echo 🚀 Installing Pancake MCP Server for Windows...

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 🐳 Docker not found. Installing Docker Desktop...
    echo Please download and install Docker Desktop from: https://www.docker.com/products/docker-desktop
    echo After installation, please run this script again.
    pause
    exit /b 1
)

REM Check if Docker daemon is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ Docker is installed but not running. Please start Docker Desktop first.
    echo After starting Docker Desktop, please run this script again.
    pause
    exit /b 1
)

echo ✅ Docker is installed and running

REM Check if we're in the correct directory
if not exist "docker-compose.yml" (
    echo 📁 Cloning Pancake MCP Server repository...
    if exist "pancake-mcp-server" (
        echo 🔄 Updating existing repository...
        cd pancake-mcp-server
        git pull
    ) else (
        git clone https://github.com/lynguyenvu/pancake-mcp-server.git .
        cd pancake-mcp-server
    )
) else (
    echo ✅ Found existing docker-compose.yml, using current directory
)

REM Create .env file if it doesn't exist
if not exist ".env" (
    if exist ".env.example" (
        echo 📋 Creating .env file from example...
        copy .env.example .env
        echo 💡 Please edit .env file to add your API keys before starting
    ) else (
        echo 📋 Creating default .env file...
        (
            echo MCP_HOST=0.0.0.0
            echo MCP_PORT=8000
            echo PANCAKE_API_BASE_URL=https://pos.pages.fm/api/v1
            echo REM Add your API keys:
            echo REM PANCAKE_API_KEY=your_pos_api_key_here
            echo REM PANCAKE_ACCESS_TOKEN=your_chat_token_here
        ) > .env
    )
)

REM Build and start the server
echo 🏗️ Building and starting MCP server...
docker-compose up --build -d

REM Wait for server to start
echo ⏳ Waiting for server to start...
timeout /t 10 /nobreak >nul

REM Check if server is running
docker-compose ps | findstr "Up" >nul
if %errorlevel% equ 0 (
    echo ✅ MCP Server is running successfully!
    echo 🌐 Access at: http://localhost:8000
    echo 📋 Check logs: docker-compose logs -f
    echo.
    echo 🔐 To connect with Claude:
    echo    1. Get your Pancake API keys from: https://pancake.biz
    echo    2. Add them to the .env file
    echo    3. Use Custom Connector in Claude.ai with URL: http://localhost:8000/mcp
) else (
    echo ❌ Something went wrong. Check logs:
    docker-compose logs
)

pause