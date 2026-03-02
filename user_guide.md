# Pancake MCP Server — Hướng dẫn cài đặt với Claude Desktop

## 1. Yêu cầu

| Thành phần | Yêu cầu |
|------------|---------|
| Docker Desktop | Đã cài đặt và đang chạy |
| Claude Desktop | Phiên bản 1.1.x trở lên |
| PANCAKE_API_KEY | API key từ tài khoản Pancake POS |
| PANCAKE_ACCESS_TOKEN | Bearer token đăng nhập Pancake |

## 2. Lấy thông tin xác thực

### PANCAKE_API_KEY
Dùng để gọi API quản lý shop (đơn hàng, kho, giao hàng...).

1. Đăng nhập Pancake POS tại pos.pages.fm
2. Vào Cài đặt → Tích hợp API
3. Sao chép giá trị API Key

### PANCAKE_ACCESS_TOKEN
Bắt buộc để đọc tin nhắn và hội thoại từ inbox.

1. Đăng nhập Pancake POS tại pos.pages.fm
2. Mở DevTools trình duyệt (F12) → tab Network
3. Thực hiện bất kỳ thao tác nào (ví dụ: mở đơn hàng)
4. Tìm request bất kỳ đến pos.pages.fm/api → xem header Authorization
5. Sao chép phần sau chữ Bearer (chuỗi JWT dài bắt đầu bằng eyJ...)

⚠️ **Lưu ý**: PANCAKE_ACCESS_TOKEN là JWT có thời hạn. Khi Claude báo lỗi xác thực khi đọc tin nhắn, cần lấy lại token mới và cập nhật vào config.

## 3. Các bước cài đặt

### Bước 1 — Clone source code
```bash
git clone <url-repo-pancake-mcp-server>
cd pancake-mcp-server
```

### Bước 2 — Build Docker image
```bash
docker compose build
```

Kiểm tra image đã được tạo:
```bash
docker images | grep pancake
# Kết quả mong đợi: pancake-mcp-server-pancake-mcp   latest
```

### Bước 3 — Cấu hình Claude Desktop

Mở file config:
```bash
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

Nội dung chuẩn:
```json
{
  "mcpServers": {
    "pancake-mcp": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "PANCAKE_API_KEY=<your_api_key>",
        "-e", "PANCAKE_ACCESS_TOKEN=<your_access_token>",
        "-e", "PYTHONPATH=/app/src",
        "pancake-mcp-server-pancake-mcp:latest",
        "pancake-mcp-stdio"
      ]
    }
  },
  "preferences": {
    "coworkScheduledTasksEnabled": true,
    "sidebarMode": "task",
    "coworkWebSearchEnabled": true
  }
}
```

Giải thích các tham số:

| Tham số | Giải thích |
|---------|------------|
| PANCAKE_API_KEY | API key quản lý shop |
| PANCAKE_ACCESS_TOKEN | Bearer token để đọc tin nhắn, hội thoại |
| PYTHONPATH=/app/src | Bắt buộc — giúp Python tìm module trong container |
| pancake-mcp-stdio | Khởi động server ở chế độ stdio |
| --rm | Tự xóa container sau khi Claude đóng |
| -i | Giữ stdin mở — bắt buộc cho stdio transport |

⚠️ **Thay `<your_api_key>` và `<your_access_token>` bằng giá trị thực. Không giữ dấu `< >`.**

Lưu file: `Ctrl+O` → `Enter` → `Ctrl+X`

### Bước 4 — Khởi động lại Claude Desktop
Quit hoàn toàn (Cmd+Q) rồi mở lại. Các tool Pancake MCP sẽ tự động xuất hiện.

## 4. Kiểm tra hoạt động
Sau khi khởi động lại Claude, thử các câu lệnh sau trong chat:

| Câu lệnh thử | Mục đích kiểm tra |
|--------------|-------------------|
| Lấy danh sách shop | Kiểm tra kết nối cơ bản và PANCAKE_API_KEY |
| Xem đơn hàng mới nhất | Kiểm tra quyền truy cập đơn hàng |
| Đọc tin nhắn inbox | Kiểm tra PANCAKE_ACCESS_TOKEN |

## 5. Xử lý lỗi thường gặp

| Lỗi | Nguyên nhân | Cách fix |
|-----|-------------|----------|
| Claude Desktop không khởi động | JSON config bị lỗi cú pháp | Xóa phần mcpServers, restart, thêm lại. Validate tại jsonlint.com |
| No module named 'pancake_mcp' | Thiếu PYTHONPATH | Thêm -e PYTHONPATH=/app/src vào args |
| docker: not found | Claude không tìm thấy docker | Dùng đường dẫn đầy đủ /usr/local/bin/docker |
| Image not found | Image chưa build hoặc sai tên | Chạy lại docker compose build, kiểm tra tên bằng docker images |
| Server disconnected | Token sai hoặc hết hạn | Lấy lại token mới từ Pancake POS và cập nhật config |

## 6. Lưu ý quan trọng

- Docker Desktop phải chạy trước khi mở Claude Desktop
- Không cần giữ container chạy liên tục — Claude tự khởi/dừng nhờ flag --rm
- Sau khi update code, build lại image và restart Claude Desktop để load phiên bản mới