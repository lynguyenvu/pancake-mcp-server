# Pancake POS MCP Server

Kết nối Claude với [Pancake](https://pancake.biz) thông qua MCP — cho phép Claude quản lý đơn hàng, kho, vận chuyển, tin nhắn khách hàng và nhiều hơn nữa.

> **Pancake** là nền tảng quản lý bán hàng đa kênh phổ biến tại Việt Nam (Facebook, Website, TikTok Shop, Zalo...).

---

## Tính năng

- **30 MCP tools** — đơn hàng, kho, vận chuyển, hội thoại/inbox, đính kèm, địa chỉ Việt Nam
- **2 chế độ kết nối** — Local (stdio) cho Claude Desktop, Remote (HTTP) cho Claude.ai
- **Bảo mật** — stdio mode: API key không rời máy bạn
- **Docker ready** — deploy 1 lệnh

---

## 30 công cụ MCP

| Module | Công cụ |
|--------|---------|
| 🏪 Shop | `get_shops`, `get_payment_methods` |
| 🗺️ Địa lý VN | `get_provinces`, `get_districts`, `get_communes` |
| 📦 Đơn hàng | `search_orders`, `get_order`, `create_order`, `update_order`, `get_order_tags`, `get_order_sources`, `get_active_promotions` |
| 🏭 Kho hàng | `list_warehouses`, `create_warehouse`, `update_warehouse`, `get_inventory_history` |
| 🚚 Vận chuyển | `arrange_shipment`, `get_tracking_url`, `list_return_orders`, `create_return_order` |
| 💬 Hội thoại | `list_conversations`, `get_conversation`, `get_messages`, `send_message`, `update_conversation` |
| 📎 Đính kèm | `list_message_attachment`, `download_attachment`, `preview_attachment_content`, `extract_text_from_image`, `analyze_image_content` |

---

## Yêu cầu

- Python 3.11+
- Tài khoản Pancake với quyền truy cập API
- Claude Desktop (cho stdio mode) hoặc Claude.ai Pro/Team (cho remote mode)

---

## Cài đặt

### Phương pháp 1: Cài đặt với Docker (khuyên dùng)

**Dành cho người dùng Windows muốn chạy trên Docker Desktop mà không cần file `.env`**

#### Bước 1: Clone Repository

Mở Command Prompt hoặc PowerShell và chạy:

```cmd
git clone https://github.com/lynguyenvu/pancake-mcp-server.git
cd pancake-mcp-server
```

#### Bước 2: Build Docker Image

```cmd
docker build -t pancake-mcp-server:latest .
```

#### Bước 3: Cấu Hình Claude Desktop trên Windows

Mở file cấu hình của Claude Desktop trên Windows:

```
%APPDATA%\Claude\claude_desktop_config.json
```

Bạn có thể mở nhanh bằng cách:
1. Nhấn `Win + R`
2. Gõ `%APPDATA%\Claude\claude_desktop_config.json`
3. Nhấn Enter

Thêm cấu hình sau (thay thế `your_pos_api_key_here` và `your_chat_access_token_here` bằng API keys thực tế):

```json
{
  "mcpServers": {
    "pancake-mcp": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "PANCAKE_API_KEY=your_pos_api_key_here",
        "-e", "PANCAKE_ACCESS_TOKEN=your_chat_access_token_here",
        "-e", "PYTHONPATH=/app/src",
        "pancake-mcp-server:latest",
        "pancake-mcp-stdio"
      ]
    }
  }
}
```

Khởi động lại Claude Desktop để áp dụng thay đổi.

> **Lưu ý:** Đảm bảo Docker Desktop đang chạy trên Windows trước khi thực hiện các lệnh. API keys được lưu trực tiếp trong cấu hình Claude Desktop, không cần file `.env`.

### Phương pháp 2: Quick start (nếu đã có Docker)

```bash
# Clone repository
git clone https://github.com/lynguyenvu/pancake-mcp-server.git
cd pancake-mcp-server

# Copy environment file
cp .env.example .env
# Chỉnh sửa .env để thêm API keys

# Chạy server
docker compose up -d
```

**Quản lý server:**
```bash
# Xem logs
docker compose logs -f

# Dừng server
docker compose down

# Khởi động lại
docker compose restart
```

### Phương pháp 3: Cài đặt thủ công (pip)

#### 1. Clone và cài package

```bash
git clone https://github.com/lynguyenvu/pancake-mcp-server.git
cd pancake-mcp-server
pip install -e .
```

**Kiểm tra cài đặt thành công:**

```bash
# 1. Package đã được cài?
pip show pancake-mcp
# → Hiển thị Name, Version, Location... là OK

# 2. Lệnh stdio hoạt động?
pancake-mcp-stdio --help 2>&1 | head -5
# → Hiển thị usage là OK (không cần API key thật để chạy --help)

# 3. Server HTTP khởi động được? (test nhanh rồi Ctrl+C)
PANCAKE_API_KEY=test uvicorn pancake_mcp.server:app --port 8000 &
sleep 2 && curl -s http://localhost:8000/health
# → {"status": "ok", "server": "pancake-pos-mcp"}
kill %1
```

### 2. Lấy API keys

Server dùng **2 loại key riêng biệt** cho 2 API khác nhau:

#### POS API key — đơn hàng, kho, vận chuyển

1. Đăng nhập tại [pancake.biz](https://pancake.biz)
2. Vào **Cài đặt → Nâng cao → Kết nối bên thứ 3 → Webhook/API**
3. Tạo hoặc copy API key → đây là `PANCAKE_API_KEY`

#### Chat/Inbox access token — hội thoại, tin nhắn

Token này **khác hoàn toàn** với POS API key, phải lấy riêng:

1. Đăng nhập tại [pancake.biz](https://pancake.biz)
2. Vào **Cài đặt → API** (hoặc **Settings → API**, mục **Pages.fm / Chat**)
3. Tạo hoặc copy access token → đây là `PANCAKE_ACCESS_TOKEN`

> **Nếu không set `PANCAKE_ACCESS_TOKEN`**, server tự động dùng `PANCAKE_API_KEY` cho cả Chat API (hoạt động được nếu tài khoản có đủ quyền).

#### Lấy Page ID — cần cho các tool hội thoại/tin nhắn

Các tool hội thoại (`list_conversations`, `get_messages`, `send_message`...) yêu cầu `page_id`. Đây là ID nội bộ của Pancake, **không phải** username hiển thị trên URL.

> **Lưu ý:** URL trên Pancake dạng `pancake.vn/pzl_xxxxxxxxxx` chứa **username**, không phải page_id. Hai giá trị này khác nhau.

**Bước 1:** Lấy access token (xem phần Chat/Inbox access token ở trên)

**Bước 2:** Gọi API `/pages` để lấy danh sách page

```bash
curl "https://pages.fm/api/v1/pages?access_token=YOUR_ACCESS_TOKEN"
```

**Bước 3:** Tìm `id` trong kết quả trả về

Kết quả nằm trong `categorized.activated`, mỗi page có:

```json
{
  "id": "pzl_123456789012345678",      ← ĐÂY là page_id (dùng cho API)
  "name": "Tên page của bạn",
  "platform": "personal_zalo",
  "username": "pzl_xxxxxxxxxx"          ← đây là username (hiển thị trên URL)
}
```

Dùng giá trị `id` làm `page_id` khi gọi các tool hội thoại.

---

### Nếu chỉ cần xử lý tin nhắn (Chat/Inbox only)

Bạn **không cần** `PANCAKE_API_KEY` nếu chỉ dùng các tool hội thoại. Cấu hình tối giản:

```env
PANCAKE_ACCESS_TOKEN=your_chat_access_token
```

Hoặc trong Claude Desktop config:

```json
{
  "mcpServers": {
    "pancake": {
      "command": "pancake-mcp-stdio",
      "env": {
        "PANCAKE_ACCESS_TOKEN": "your_chat_access_token"
      }
    }
  }
}
```

> Khi chỉ set `PANCAKE_ACCESS_TOKEN` (không set `PANCAKE_API_KEY`), các tool POS như `search_orders`, `list_warehouses`... sẽ báo lỗi thiếu key — nhưng các tool hội thoại (`list_conversations`, `send_message`, `get_messages`...) hoạt động bình thường.

---

## Kết nối với Claude

### Phương án A — Claude Desktop / Claude Code (stdio, bảo mật nhất) ⭐

API key **không rời máy bạn**, chạy hoàn toàn local.

**Bước 1:** Cài đặt (xem phần trên)

**Bước 2:** Xác nhận lệnh hoạt động

```bash
PANCAKE_API_KEY=test pancake-mcp-stdio --help 2>&1 || echo "OK - lệnh tồn tại"
```

**Bước 3:** Cấu hình Claude Desktop

Mở file config:
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

**Cách 1: Dùng trực tiếp lệnh pancake-mcp-stdio (đơn giản hơn):**
```json
{
  "mcpServers": {
    "pancake": {
      "command": "pancake-mcp-stdio",
      "env": {
        "PANCAKE_API_KEY": "your_pos_api_key",
        "PANCAKE_ACCESS_TOKEN": "your_chat_access_token"
      }
    }
  }
}
```

**Cách 2: Dùng Docker container (được thử nghiệm thực tế):**
```json
{
  "mcpServers": {
    "pancake-mcp": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "PANCAKE_API_KEY=your_pos_api_key",
        "-e", "PANCAKE_ACCESS_TOKEN=your_chat_access_token",
        "-e", "PYTHONPATH=/app/src",
        "pancake-mcp-server:latest",
        "pancake-mcp-stdio"
      ]
    }
  }
}
```

**Bước 4:** Khởi động lại Claude Desktop

Công cụ Pancake xuất hiện tự động trong Claude ✅

### Hướng dẫn chi tiết cài đặt với Claude Desktop

Xem file [docs/user-guide.md](docs/user-guide.md) để có hướng dẫn cài đặt chi tiết theo phương pháp đã được thử nghiệm thực tế.

---

### Phương án B — Claude.ai (remote HTTP, dùng custom connector)

Phù hợp cho team nhiều người hoặc khi không dùng Claude Desktop.

**Bước 1:** Tạo file `.env`

```bash
cp .env.example .env
# Chỉnh sửa .env để thêm API keys
```

**Bước 2:** Chạy server

```bash
# Docker
docker compose up -d

# Hoặc trực tiếp (development)
pip install -e .
uvicorn pancake_mcp.server:app --host 0.0.0.0 --port 8000
```

Kiểm tra server:
```bash
curl http://localhost:8000/health
# → {"status": "ok", "server": "pancake-pos-mcp"}
```

**Bước 3:** Expose public HTTPS

```bash
# Dùng ngrok (dev/test)
ngrok http 8000
# → https://xxxx.ngrok-free.app
```

Hoặc deploy lên VPS với nginx + SSL.

**Bước 4:** Thêm vào Claude.ai

Vào **Settings → Connectors → Add custom connector**:
- **MCP Server URL:** `https://xxxx.ngrok-free.app/mcp`
- **Authentication:** Bearer token → dán Pancake API key của bạn

---

## Ví dụ sử dụng

Sau khi kết nối, chat với Claude:

**Quản lý đơn hàng:**
```
Lấy danh sách đơn hàng mới hôm nay
Tạo đơn cho Nguyễn Văn A, SĐT 0901234567, 2 sản phẩm ID "abc123"
Cập nhật trạng thái đơn #12345 thành "confirmed"
Tạo đơn hoàn cho đơn #12345, lý do: sản phẩm lỗi
```

**Quản lý kho:**
```
Xem danh sách kho hàng
Lịch sử nhập xuất kho từ 01/02 đến hôm nay
```

**Hội thoại & inbox:**
```
Xem các tin nhắn Facebook inbox chưa xử lý của page ID "xxx"
Lịch sử chat trong hội thoại ID "conv123"
Gửi tin nhắn: "Cảm ơn bạn! Đơn hàng sẽ được giao trong 2-3 ngày"
Đóng hội thoại ID "conv123", gắn tag "đã xử lý"
```

**Đính kèm file:**
```
Liệt kê các file đính kèm trong hội thoại ID "conv123"
Tải về file đính kèm từ tin nhắn thứ 5, file thứ 2
Tải về ảnh từ hội thoại của khách hàng
```

**Địa chỉ:**
```
Danh sách tỉnh thành Việt Nam
Quận huyện của TP.HCM
```

---

## Bảo mật

| Phương án | API key lưu ở đâu | Mức bảo mật |
|-----------|-------------------|-------------|
| **Local stdio** | Env var trên máy bạn | ⭐⭐⭐ Cao nhất |
| **Self-host Docker** | Server của bạn | ⭐⭐ Tốt |
| **Remote (hosted)** | Server bên thứ 3 | ⭐ Cần tin tưởng |

---

## Cấu hình `.env`

```env
# Server
MCP_HOST=0.0.0.0
MCP_PORT=8000

# POS API key — đơn hàng, kho, vận chuyển
PANCAKE_API_KEY=

# Chat/Inbox token — hội thoại, tin nhắn (mặc định dùng chung PANCAKE_API_KEY)
PANCAKE_ACCESS_TOKEN=

# API base URLs (không cần thay đổi)
PANCAKE_API_BASE_URL=https://pos.pages.fm/api/v1
PANCAKE_CHAT_BASE_URL=https://pages.fm/api/v1
```

---

## Phát triển

```bash
# Cài đầy đủ (bao gồm dev dependencies)
pip install -e ".[dev]"

# Chạy tests
python3 -m pytest tests/ -v
# 10 passed ✅

# Chạy server local (HTTP mode)
uvicorn pancake_mcp.server:app --reload --port 8000
```

---

## Tech stack

| Thành phần | Mô tả |
|-----------|-------|
| [FastMCP](https://gofastmcp.com) | MCP framework — stdio & HTTP transport |
| [httpx](https://www.python-httpx.org) | Async HTTP client |
| [uvicorn](https://www.uvicorn.org) | ASGI server |
| [Starlette](https://www.starlette.io) | HTTP routing (`/health`) |
| Pancake POS API | `https://pos.pages.fm/api/v1` |
| Pancake Chat API | `https://pages.fm/api/v1` |

---

## Gỡ cài đặt

**1. Xóa package Python:**
```bash
pip uninstall pancake-mcp
```

**2. Xóa config Claude Desktop** — mở file config và xóa block `"pancake"`:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

**3. Xóa thư mục source** (nếu đã clone):
```bash
rm -rf pancake-mcp-server/
```

**4. Nếu dùng Docker:**
```bash
docker compose down --volumes
```

---

## Đóng góp & hỗ trợ

Tạo [Issue](https://github.com/lynguyenvu/pancake-mcp-server/issues) nếu gặp lỗi hoặc có đề xuất tính năng mới.

## Giấy phép

Dự án này được cấp phép theo giấy phép MIT - xem tệp [LICENSE](LICENSE) để biết chi tiết.
