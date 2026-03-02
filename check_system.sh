#!/bin/bash

echo "🔍 Kiểm tra hệ thống Pancake MCP Server"

echo ""
echo "=== 1. Kiểm tra lệnh pancake-mcp-stdio ==="
if command -v pancake-mcp-stdio &> /dev/null; then
    echo "✅ Lệnh pancake-mcp-stdio đã có sẵn"
    pancake-mcp-stdio --help 2>&1 | head -3
else
    echo "❌ Lệnh pancake-mcp-stdio chưa được cài đặt"
    echo "💡 Chạy lệnh sau để cài đặt:"
    echo "   pip install -e ."
    echo ""
fi

echo ""
echo "=== 2. Kiểm tra Docker ==="
if command -v docker &> /dev/null; then
    echo "✅ Docker đã được cài đặt"
    echo "Docker version: $(docker --version)"
else
    echo "❌ Docker chưa được cài đặt"
    echo "💡 Vui lòng cài đặt Docker trước"
    echo ""
    exit 1
fi

echo ""
echo "=== 3. Kiểm tra Docker containers ==="
cd /cowork_mcp/pancake-mcp-server
if [ -f "docker-compose.yml" ]; then
    echo "✅ File docker-compose.yml tồn tại"

    # Kiểm tra container đang chạy
    RUNNING_CONTAINERS=$(docker compose ps -q)
    if [ ! -z "$RUNNING_CONTAINERS" ]; then
        echo "✅ Docker containers đang chạy:"
        docker compose ps
    else
        echo "⚠️  Không có container nào đang chạy"
        echo "💡 Khởi động lại với lệnh:"
        echo "   ./start.sh"
        echo ""

        # Đề xuất khởi động
        read -p "Bạn có muốn khởi động Docker containers ngay không? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            ./start.sh
        fi
    fi
else
    echo "❌ Không tìm thấy file docker-compose.yml"
fi

echo ""
echo "=== 4. Kiểm tra API keys ==="
ENV_FILE=".env"
if [ -f "$ENV_FILE" ]; then
    echo "✅ File .env tồn tại"
    HAS_PANCAKE_API_KEY=$(grep -c "PANCAKE_API_KEY=" "$ENV_FILE" || echo "0")
    HAS_PANCAKE_ACCESS_TOKEN=$(grep -c "PANCAKE_ACCESS_TOKEN=" "$ENV_FILE" || echo "0")

    if [ "$HAS_PANCAKE_API_KEY" -gt 0 ] && [ "$HAS_PANCAKE_ACCESS_TOKEN" -gt 0 ]; then
        echo "✅ Cả hai API key và access token đều đã được thiết lập"
    else
        echo "⚠️  Một hoặc cả hai API key chưa được thiết lập"
        echo "💡 Vui lòng kiểm tra và điền vào file .env"
    fi
else
    echo "⚠️  File .env chưa tồn tại"
    echo "💡 Tạo file .env từ mẫu:"
    echo "   cp .env.example .env"
    echo "   # Sau đó chỉnh sửa .env để thêm API keys"
fi

echo ""
echo "=== 5. Kiểm tra file cấu hình Claude Desktop ==="
CONFIG_FILE=""
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CONFIG_FILE="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    # Windows
    CONFIG_FILE="$APPDATA/Claude/claude_desktop_config.json"
else
    # Linux
    CONFIG_FILE="$HOME/.config/Claude/claude_desktop_config.json"
fi

if [ -f "$CONFIG_FILE" ]; then
    echo "✅ File cấu hình Claude Desktop tồn tại"

    # Kiểm tra cú pháp JSON
    if command -v jq >/dev/null 2>&1; then
        if jq empty "$CONFIG_FILE" 2>/dev/null; then
            echo "✅ Cú pháp JSON hợp lệ"
        else
            echo "❌ Cú pháp JSON không hợp lệ"
            echo "💡 Sử dụng script fix_claude_config.sh để sửa"
        fi
    else
        echo "⚠️ jq không được cài đặt, bỏ qua kiểm tra cú pháp JSON"
    fi
else
    echo "⚠️  File cấu hình Claude Desktop không tồn tại"
    echo "💡 Chạy script để tạo file:"
    echo "   ./fix_claude_config.sh"
fi

echo ""
echo "=== TÓM TẮT ==="
echo "1. Đảm bảo lệnh pancake-mcp-stdio hoạt động"
echo "2. Đảm bảo Docker containers đang chạy"
echo "3. Đảm bảo API keys đã được thiết lập"
echo "4. Đảm bảo cấu hình Claude Desktop hợp lệ"
echo ""
echo "💡 Sau khi khắc phục các lỗi trên, khởi động lại Claude Desktop"