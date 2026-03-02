# Hướng Dẫn Sử Dụng Pancake MCP Server - Dành Cho Người Dùng Cuối

## Tổng Quan

Pancake MCP Server là công cụ giúp kết nối Claude AI với hệ thống bán hàng Pancake POS, cho phép bạn:
- Quản lý đơn hàng, kho, vận chuyển
- Xử lý tin nhắn khách hàng
- Tự động hóa các tác vụ bán hàng

## Yêu Cầu Hệ Thống

- Máy tính có cài Docker
- Tài khoản Pancake POS với quyền API
- Claude Desktop hoặc Claude AI Pro/Team

## Cài Đặt Ban Đầu

### Bước 1: Cài Đặt Tự Động (Khuyên Dùng)

Chạy lệnh sau trong Terminal/Command Prompt:

**Windows:**
```cmd
curl -O https://raw.githubusercontent.com/lynguyenvu/pancake-mcp-server/main/install.bat
./install.bat
```

**macOS/Linux:**
```bash
curl -O https://raw.githubusercontent.com/lynguyenvu/pancake-mcp-server/main/install.sh
chmod +x install.sh
./install.sh
```

### Bước 2: Cấu Hình API Keys

Sau khi cài đặt xong, mở file `.env` trong thư mục `pancake-mcp-server` và điền:

```env
PANCAKE_API_KEY=API_KEY_CỦA_BẠN
PANCAKE_ACCESS_TOKEN=TOKEN_TRUY_CẬP_CỦA_BẠN
```

**Lấy API Key từ Pancake:**
1. Đăng nhập vào [pancake.biz](https://pancake.biz)
2. Vào **Cài đặt → Nâng cao → Kết nối bên thứ 3 → Webhook/API** để lấy `PANCAKE_API_KEY`
3. Vào **Cài đặt → API** để lấy `PANCAKE_ACCESS_TOKEN`

## Kết Nối Với Claude

### Với Claude Desktop (An Toàn Nhất)

Mở file cấu hình của Claude:
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

Thêm đoạn sau vào file (giữ nguyên các cấu hình khác):

```json
{
  "mcpServers": {
    "pancake": {
      "command": "pancake-mcp-stdio",
      "env": {
        "PANCAKE_API_KEY": "API_KEY_CỦA_BẠN",
        "PANCAKE_ACCESS_TOKEN": "TOKEN_CỦA_BẠN"
      }
    }
  }
}
```

Khởi động lại Claude Desktop.

### Với Claude AI (Thông Qua HTTP)

1. Khởi động server:
```bash
cd pancake-mcp-server
./start.sh
```

2. Tạo đường hầm HTTPS (cho Claude AI):
```bash
ngrok http 8000
```

3. Lấy URL từ ngrok (ví dụ: `https://abc123.ngrok-free.app`)

4. Vào Claude AI → **Settings → Connectors → Add custom connector**
   - **MCP Server URL:** `https://abc123.ngrok-free.app/mcp`
   - **Authentication:** Bearer token → điền API key của bạn

## Quản Lý Dịch Vụ

### Khởi Động/Dừng Server

```bash
# Khởi động server
./start.sh

# Dừng server
./stop.sh

# Xem trạng thái
docker compose ps

# Xem log nếu có lỗi
docker compose logs -f
```

### Sau Khi Khởi Động Lại Máy

Mỗi lần khởi động lại máy tính, bạn cần chạy lại các dịch vụ:

```bash
# Cách đơn giản nhất:
./restart_after_reboot.sh

# Hoặc chạy từng bước:
docker compose up -d  # Khởi động lại containers
ngrok http 8000       # Khởi động lại ngrok nếu cần
```

## Sử Dụng Với Claude

Sau khi kết nối thành công, bạn có thể yêu cầu Claude thực hiện các tác vụ như:

```
- Lấy danh sách đơn hàng mới hôm nay
- Tạo đơn hàng mới cho khách hàng Nguyễn Văn A
- Cập nhật trạng thái đơn #12345 thành "đang giao"
- Xem lịch sử chat trong hội thoại ID "conv123"
- Gửi tin nhắn cho khách hàng: "Cảm ơn bạn! Đơn hàng sẽ được giao trong 2-3 ngày"
```

## Giải Quyết Sự Cố

### Server Không Khởi Động Được

1. Kiểm tra Docker có đang chạy không
2. Xem log: `docker compose logs -f`
3. Chắc chắn rằng cổng 8000 không bị chiếm bởi ứng dụng khác

### Không Kết Nối Được Với Claude

1. Kiểm tra lại API keys có đúng không
2. Đảm bảo server đang chạy: `docker compose ps`
3. Với Claude AI, kiểm tra ngrok có đang chạy và URL còn hiệu lực không

### Lỗi ModuleNotFound trong Docker

Chạy lại lệnh sau để rebuild container:
```bash
docker compose build --no-cache
docker compose up -d
```

## Gỡ Cài Đặt

```bash
# Dừng và xóa containers
docker compose down --volumes

# Xóa file cấu hình Claude (nếu có)
# Xóa thư mục pancake-mcp-server
rm -rf pancake-mcp-server/
```

## Hỗ Trợ

Nếu gặp vấn đề, vui lòng tạo issue tại: [GitHub Issues](https://github.com/lynguyenvu/pancake-mcp-server/issues)

---

**Lưu ý:** Đây là phiên bản dành cho người dùng cuối với các script tự động hóa để dễ sử dụng. Tất cả dữ liệu được xử lý cục bộ trên máy bạn, đảm bảo an toàn bảo mật.