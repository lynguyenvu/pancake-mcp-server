# Pancake POS MCP Server

Kết nối Claude với [Pancake POS](https://pancake.biz) thông qua MCP — cho phép Claude quản lý đơn hàng, kho, vận chuyển và nhiều hơn.

> **Pancake POS** là nền tảng quản lý bán hàng đa kênh phổ biến tại Việt Nam (Facebook, Website, TikTok Shop).

## 20 công cụ MCP

| Module | Công cụ |
|--------|---------|
| Shop | `get_shops`, `get_payment_methods` |
| Địa lý | `get_provinces`, `get_districts`, `get_communes` |
| Đơn hàng | `search_orders`, `get_order`, `create_order`, `update_order`, `get_order_tags`, `get_order_sources`, `get_active_promotions` |
| Kho | `list_warehouses`, `create_warehouse`, `update_warehouse`, `get_inventory_history` |
| Vận chuyển | `arrange_shipment`, `get_tracking_url`, `list_return_orders`, `create_return_order` |

---

## Cách kết nối với Claude

### Phương án A — Claude Desktop (local, bảo mật nhất) ⭐

API key **không rời máy bạn**, không qua server trung gian.

**Bước 1:** Cài đặt

```bash
git clone https://github.com/lynguyenvu/pancake-mcp-server.git
cd pancake-mcp-server
pip install -e .
```

**Bước 2:** Lấy Pancake API key

Đăng nhập [Pancake](https://pancake.biz) → **Cài đặt → Nâng cao → Kết nối bên thứ 3 → Webhook/API** → Copy API key.

**Bước 3:** Cấu hình Claude Desktop

Mở file config:
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

Thêm vào:

```json
{
  "mcpServers": {
    "pancake": {
      "command": "pancake-mcp-stdio",
      "env": {
        "PANCAKE_API_KEY": "paste_api_key_here"
      }
    }
  }
}
```

**Bước 4:** Khởi động lại Claude Desktop → công cụ xuất hiện tự động ✅

---

### Phương án B — Claude.ai (remote, dùng custom connector)

Phù hợp khi không cài Claude Desktop hoặc dùng cho nhiều người.

**Bước 1:** Deploy server

```bash
# Docker (khuyến nghị)
cp .env.example .env
docker compose up -d

# Hoặc thủ công
pip install -e .
uvicorn pancake_mcp.server:app --host 0.0.0.0 --port 8000
```

Server khởi động tại `http://localhost:8000/mcp`

**Bước 2:** Expose ra public HTTPS (ví dụ dùng [ngrok](https://ngrok.com)):

```bash
ngrok http 8000
# → https://xxxx.ngrok.io
```

**Bước 3:** Thêm vào Claude.ai

Vào **Settings → Connectors → Add custom connector**:
- **MCP Server URL:** `https://xxxx.ngrok.io/mcp`
- **Authentication:** Bearer token → dán Pancake API key của bạn

---

## Ví dụ sử dụng

Sau khi kết nối, bạn có thể chat với Claude:

```
"Lấy danh sách đơn hàng mới trong hôm nay"
"Tạo đơn hàng cho Nguyễn Văn A, SĐT 0901234567, 2 sản phẩm ID abc"
"Kiểm tra trạng thái đơn hàng #12345"
"Danh sách kho hàng của shop"
"Tạo đơn hoàn hàng cho đơn #12345 với lý do sản phẩm lỗi"
```

---

## Bảo mật

| Phương án | API key đi qua đâu | Mức độ bảo mật |
|-----------|-------------------|----------------|
| Local stdio | Chỉ trên máy bạn | ⭐⭐⭐ Cao nhất |
| Self-host | Server của bạn | ⭐⭐ Tốt |
| Remote (hosted) | Server bên thứ 3 | ⭐ Cần tin tưởng provider |

---

## Cấu hình nâng cao (HTTP mode)

Sao chép `.env.example` thành `.env`:

```env
MCP_HOST=0.0.0.0
MCP_PORT=8000

# Single-tenant: khoá cứng API key (bỏ ghi chú để dùng)
# PANCAKE_API_KEY=your_key_here
```

---

## Phát triển

```bash
pip install -e ".[dev]"
python3 -m pytest tests/ -v   # 10/10 tests
```

## Tech stack

- **[FastMCP](https://gofastmcp.com)** — MCP framework (stdio + HTTP)
- **httpx** — async HTTP client
- **uvicorn** — ASGI server
- **Pancake API** — `https://pos.pages.fm/api/v1`
