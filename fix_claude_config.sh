#!/bin/bash

echo "🔧 Tạo lại file cấu hình Claude Desktop đúng cú pháp JSON"

# Xác định đường dẫn file config theo hệ điều hành
CONFIG_DIR=""
CONFIG_FILE=""

if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CONFIG_DIR="$HOME/Library/Application Support/Claude"
    CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"
elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    # Windows
    if [ -d "$APPDATA/Claude" ]; then
        CONFIG_DIR="$APPDATA/Claude"
        CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"
    else
        echo "⚠️ Không tìm thấy thư mục Claude trên Windows"
        exit 1
    fi
else
    # Linux
    CONFIG_DIR="$HOME/.config/Claude"
    CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"
fi

echo "📁 Thư mục config: $CONFIG_DIR"
echo "📄 File config: $CONFIG_FILE"

# Tạo thư mục nếu chưa tồn tại
mkdir -p "$CONFIG_DIR"

# Sao lưu file cũ nếu tồn tại
if [ -f "$CONFIG_FILE" ]; then
    echo "💾 Đang sao lưu file cũ..."
    cp "$CONFIG_FILE" "${CONFIG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
fi

# Tạo file config mới với cú pháp JSON đúng
cat > "$CONFIG_FILE" << 'EOL'
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
EOL

# Kiểm tra cú pháp JSON
if command -v jq >/dev/null 2>&1; then
    if jq empty "$CONFIG_FILE" 2>/dev/null; then
        echo "✅ File JSON hợp lệ"
    else
        echo "❌ Lỗi cú pháp JSON trong file"
        cat "$CONFIG_FILE"
        exit 1
    fi
else
    echo "⚠️ jq không được cài đặt, bỏ qua kiểm tra cú pháp JSON"
fi

echo "✅ File cấu hình đã được tạo lại thành công tại: $CONFIG_FILE"
echo ""
echo "💡 Bước tiếp theo:"
echo "1. Mở file $CONFIG_FILE bằng trình soạn thảo văn bản"
echo "2. Thêm API keys vào các trường tương ứng (giữa dấu ngoặc kép)"
echo "3. Lưu file và KHÔNG thêm dấu phẩy thừa vào cuối cùng"
echo "4. Khởi động lại Claude Desktop"
echo ""
echo "📋 API keys có thể lấy từ:"
echo "   - PANCAKE_API_KEY: https://pancake.biz → Cài đặt → Nâng cao → Webhook/API"
echo "   - PANCAKE_ACCESS_TOKEN: https://pancake.biz → Cài đặt → API"
echo ""
echo "📝 Ví dụ đúng:"
echo '   "PANCAKE_API_KEY": "pk_xxxxxxxxxxxxxxxxxxxxxxxx",'
echo '   "PANCAKE_ACCESS_TOKEN": "at_xxxxxxxxxxxxxxxxxxxxxxxx"'
echo "   (không có dấu phẩy sau giá trị cuối cùng trong object)"
EOL