# Pancake POS MCP Server

Remote MCP server that connects Claude to [Pancake POS](https://pancake.biz) — giving Claude 20 tools to manage orders, inventory, shipping, and more.

## Features

- **20 MCP tools** — orders, warehouses, shipping, returns, geo address data
- **Stateless auth** — user's Pancake API key passed as Bearer token
- **Claude-ready** — works with Claude custom connectors (Streamable HTTP)
- **Docker support** — single container, production-ready

## Tools

| Module | Tools |
|--------|-------|
| Shop | `get_shops`, `get_payment_methods` |
| Geo | `get_provinces`, `get_districts`, `get_communes` |
| Orders | `search_orders`, `get_order`, `create_order`, `update_order`, `get_order_tags`, `get_order_sources`, `get_active_promotions` |
| Inventory | `list_warehouses`, `create_warehouse`, `update_warehouse`, `get_inventory_history` |
| Shipping | `arrange_shipment`, `get_tracking_url`, `list_return_orders`, `create_return_order` |

## Quick Start

### Local

```bash
pip install -e .
uvicorn pancake_mcp.server:app --host 0.0.0.0 --port 8000
```

### Docker

```bash
docker compose up -d
```

Server available at `http://localhost:8000/mcp`

## Connect to Claude

1. Get your Pancake API key: **Settings → Advance → Third-party connection → Webhook/API**
2. Deploy this server with a public HTTPS URL
3. In Claude: **Settings → Connectors → Add custom connector**
   - MCP Server URL: `https://your-domain.com/mcp`
   - Authentication: Bearer token → paste your Pancake API key

## Configuration

Copy `.env.example` to `.env`:

```env
MCP_HOST=0.0.0.0
MCP_PORT=8000

# Single-tenant: set a fixed key (overrides Bearer token)
# PANCAKE_API_KEY=your_key_here
```

## Auth Flow

```
Claude → Bearer: <pancake_api_key>
  → MCP Server extracts token
  → Forwards as api_key to pos.pages.fm/api/v1
```

Multi-tenant by default — each user passes their own key.

## Development

```bash
pip install -e ".[dev]"
python3 -m pytest tests/ -v   # 10/10 tests
```

## Stack

- **FastMCP** — MCP framework with Streamable HTTP transport
- **httpx** — async Pancake API client
- **uvicorn** — ASGI server
- **Pancake API** — `https://pos.pages.fm/api/v1`
