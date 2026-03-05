# Pancake MCP Server

## What This Is

An MCP (Model Context Protocol) server that connects Claude AI with **Pancake POS** — Vietnam's multi-channel e-commerce management platform. Enables Claude to manage orders, inventory, shipping, conversations, and customer communications across Facebook, TikTok Shop, Website, and Zalo.

## Project Structure

```
src/pancake_mcp/
├── server.py           # FastMCP entry point (HTTP + stdio modes)
├── client.py           # BasePancakeClient + PancakeClient (POS API)
├── chat_client.py      # PancakeChatClient (Chat/Inbox API, inherits BasePancakeClient)
├── deps.py             # Auth token extraction (env var → Bearer header fallback)
└── tools/
    ├── common.py       # Shared helpers: get_client(), fmt(), call_api(), build_payload(), parse_json_param()
    ├── shop.py         # 5 tools: shops, payments, geography
    ├── orders.py       # 7 tools: create, search, update orders, tags, promotions
    ├── inventory.py    # 4 tools: warehouses, stock history
    ├── shipping.py     # 4 tools: shipment, tracking, returns
    ├── conversations.py # 5 tools: inbox, messages, send/update
    └── attachments.py  # 5 tools: download, preview, OCR, image analysis
tests/
├── test_client.py      # PancakeClient unit tests (respx mocks)
└── test_server.py      # Server tests
docs/
├── user-guide.md                   # Vietnamese setup guide for Claude Desktop
├── docker-volume-mounting-guide.md # How to mount host dirs for downloads
└── plan-auto-discover-page-id.md   # Future plan: auto-resolve page_id
```

## Key Technologies

- **Python 3.11+**, async throughout
- **FastMCP >=3.1.0** — MCP framework for stdio & HTTP transports
- **httpx** — async HTTP client for Pancake APIs
- **uvicorn** — ASGI server for HTTP mode
- **Pillow, pytesseract** — image processing & OCR
- **aiohttp** — async downloads for attachments
- **pytest + respx** — testing

## External APIs

- **POS API**: `https://pos.pages.fm/api/v1` — auth via `?api_key=` query param
- **Chat API**: `https://pages.fm/api/v1` — auth via `?access_token=` query param

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `PANCAKE_API_KEY` | Yes | POS API key |
| `PANCAKE_ACCESS_TOKEN` | No | Chat API token (falls back to API_KEY) |
| `MCP_HOST` | No | Server host (default: 0.0.0.0) |
| `MCP_PORT` | No | Server port (default: 8000) |
| `ALLOWED_DOWNLOAD_PATHS` | No | Colon-separated allowed download dirs |
| `PANCAKE_PAGE_ID` | No | Page ID for chat tools |

## Entry Points (defined in pyproject.toml)

- `pancake-mcp-stdio` → `server.main_stdio()` — stdio transport (Claude Desktop)
- `pancake-mcp` → `server.main()` — HTTP server via uvicorn

## Running

```bash
# Dev (HTTP)
uvicorn pancake_mcp.server:app --reload --port 8000

# Dev (stdio)
PANCAKE_API_KEY=<key> pancake-mcp-stdio

# Docker
docker compose up --build -d

# Tests
pip install -e ".[dev]"
pytest tests/ -v
```

## Architecture Patterns

- **All I/O is async** — httpx clients, aiohttp for downloads
- **BasePancakeClient** — shared HTTP plumbing (auth, get/post/put, error handling) in `client.py`; `PancakeClient` and `PancakeChatClient` inherit from it, differing only in base URL and auth param name
- **Stateless clients** — new client per request, context manager pattern
- **Tool design** — async functions decorated with `@mcp.tool()`, return JSON strings via `fmt()`
- **Shared tool helpers** (in `common.py`):
  - `call_api(factory, action)` — wraps client creation + error handling in one call
  - `build_payload(required, **optional)` — builds dicts excluding None values
  - `parse_json_param(value, name)` — safe JSON parsing with error message
- **Error handling** — APIs raise `PancakeAPIError`, tools catch and return error messages (no exceptions to caller)
- **Auth precedence** (deps.py): env var → Bearer token header → fallback
- **Security** — path validation (`_is_safe_path`), filename sanitization, permission checks on downloads
- **HTTP app** — Starlette composite ASGI: `/health` endpoint + `/mcp` for MCP transport

## Build & Docker

- Uses `astral/uv` for dependency management and builds
- Base image: `python:3.11-slim` (runtime stage)
- Single `Dockerfile` with multi-stage build
- Single `docker-compose.yml` for dev/local use

## Code Conventions

- Tool modules follow pattern: `register_*_tools(mcp)` function that registers tools
- All tool functions are `async`, snake_case named, no `ctx: Context` parameter (not used)
- JSON outputs use `fmt()` helper for UTF-8 safe serialization
- Page sizes clamped to max 50 via `clamp_page_size()`
- API calls use `call_api()` helper for consistent error handling
- Payload construction uses `build_payload()` to exclude None values
- README and user-facing docs are in Vietnamese
