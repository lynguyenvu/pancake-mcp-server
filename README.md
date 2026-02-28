# Pancake POS MCP Server

Kết nối Claude với [Pancake](https://pancake.biz) thông qua MCP — cho phép Claude quản lý đơn hàng, kho, vận chuyển, tin nhắn khách hàng và nhiều hơn nữa.

> **Pancake** là nền tảng quản lý bán hàng đa kênh phổ biến tại Việt Nam (Facebook, Website, TikTok Shop, Zalo...).

---

## Tính năng

- **25 MCP tools** — đơn hàng, kho, vận chuyển, hội thoại/inbox, địa chỉ Việt Nam
- **2 chế độ kết nối** — Local (stdio) cho Claude Desktop, Remote (HTTP) cho Claude.ai
- **Bảo mật** — stdio mode: API key không rời máy bạn
- **Docker ready** — deploy 1 lệnh

---

## 25 công cụ MCP

| Module | Công cụ |
|--------|---------|
| 🏪 Shop | `get_shops`, `get_payment_methods` |
| 🗺️ Địa lý VN | `get_provinces`, `get_districts`, `get_communes` |
| 📦 Đơn hàng | `search_orders`, `get_order`, `create_order`, `update_order`, `get_order_tags`, `get_order_sources`, `get_active_promotions` |
| 🏭 Kho hàng | `list_warehouses`, `create_warehouse`, `update_warehouse`, `get_inventory_history` |
| 🚚 Vận chuyển | `arrange_shipment`, `get_tracking_url`, `list_return_orders`, `create_return_order` |
| 💬 Hội thoại | `list_conversations`, `get_conversation`, `get_messages`, `send_message`, `update_conversation` |

---

## Yêu cầu

- Python 3.10+
- Tài khoản Pancake với quyền truy cập API
- Claude Desktop (cho stdio mode) hoặc Claude.ai Pro/Team (cho remote mode)

---

## Cài đặt

### 1. Clone và cài package

```bash
git clone https://github.com/lynguyenvu/pancake-mcp-server.git
cd pancake-mcp-server
pip install -e .
```

### 2. Lấy Pancake API key

1. Đăng nhập tại [pancake.biz](https://pancake.biz)
2. Vào **Cài đặt → Nâng cao → Kết nối bên thứ 3 → Webhook/API**
3. Tạo hoặc copy API key

> **Lưu ý về Chat/Inbox API:** Nếu muốn dùng các tool hội thoại (`list_conversations`, `send_message`...), bạn có thể cần token riêng từ **Pancake → Settings → API** (mục Pages.fm). Nếu không set, server sẽ dùng chung API key POS.

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

Thêm block sau (giữ nguyên các mục đã có):

```json
{
  "mcpServers": {
    "pancake": {
      "command": "pancake-mcp-stdio",
      "env": {
        "PANCAKE_API_KEY": "your_pancake_api_key_here"
      }
    }
  }
}
```

> Nếu có cả Chat token riêng:
> ```json
> "env": {
>   "PANCAKE_API_KEY": "your_pos_api_key",
>   "PANCAKE_ACCESS_TOKEN": "your_chat_token"
> }
> ```

**Bước 4:** Khởi động lại Claude Desktop

Công cụ Pancake xuất hiện tự động trong Claude ✅

---

### Phương án B — Claude.ai (remote HTTP, dùng custom connector)

Phù hợp cho team nhiều người hoặc khi không dùng Claude Desktop.

**Bước 1:** Tạo file `.env`

```bash
cp .env.example .env
# Chỉnh sửa .env nếu cần
```

**Bước 2:** Chạy server

```bash
# Docker (khuyến nghị cho production)
docker compose up -d

# Hoặc trực tiếp
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

## Đóng góp & hỗ trợ

Tạo [Issue](https://github.com/lynguyenvu/pancake-mcp-server/issues) nếu gặp lỗi hoặc có đề xuất tính năng mới.
