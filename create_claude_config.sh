#!/bin/bash

echo "🔧 Tạo file cấu hình Claude Desktop cho Pancake MCP Server"

# Xác định đường dẫn file config theo hệ điều hành
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CONFIG_DIR="$HOME/Library/Application Support/Claude"
    CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"
elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    # Windows
    CONFIG_DIR="$APPDATA/Claude"
    CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"
    # Convert Windows path to Unix path for bash
    CONFIG_FILE=$(cygpath -u "$APPDATA/Claude/claude_desktop_config.json" 2>/dev/null || echo "$APPDATA/Claude/claude_desktop_config.json")
else
    # Linux
    CONFIG_DIR="$HOME/.config/Claude"
    CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"
fi

echo "📁 Thư mục config: $CONFIG_DIR"
echo "📄 File config: $CONFIG_FILE"

# Tạo thư mục nếu chưa tồn tại
mkdir -p "$CONFIG_DIR"

# Tạo file config mặc định
cat > "$CONFIG_FILE" << 'EOF'
{
  "mcpServers": {
    "pancake": {
      "command": "pancake-mcp-stdio",
      "env": {
        "PANCAKE_API_KEY": "",
        "PANCAKE_ACCESS_TOKEN": ""
      }
    }
  }
}
EOF

echo "✅ File cấu hình đã được tạo tại: $CONFIG_FILE"
echo ""
echo "💡 Bước tiếp theo:"
echo "1. Mở file $CONFIG_FILE"
echo "2. Điền API keys vào các trường tương ứng"
echo "3. Lưu file và khởi động lại Claude Desktop"
echo ""
echo "📋 API keys có thể lấy từ:"
echo "   - PANCAKE_API_KEY: https://pancake.biz → Cài đặt → Nâng cao → Webhook/API"
echo "   - PANCAKE_ACCESS_TOKEN: https://pancake.biz → Cài đặt → API"