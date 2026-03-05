"""FastMCP server entry point for the Pancake MCP integration.

Two transport modes:
  HTTP (remote)  — uvicorn pancake_mcp.server:app --host 0.0.0.0 --port 8000
                   Auth: Bearer token (API key or access token)
  stdio (local)  — pancake-mcp-stdio
                   Auth: PANCAKE_API_KEY or PANCAKE_ACCESS_TOKEN env var
"""

import asyncio
import logging
import os
import sys

import uvicorn

from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from pancake_mcp.tools.shop import register_shop_tools
from pancake_mcp.tools.orders import register_order_tools
from pancake_mcp.tools.inventory import register_inventory_tools
from pancake_mcp.tools.shipping import register_shipping_tools
from pancake_mcp.tools.conversations import register_conversation_tools
from pancake_mcp.tools.attachments import register_attachment_tools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> FastMCP:
    mcp = FastMCP(
        name="pancake-pos",
        instructions=(
            "Tools for managing a Pancake shop: orders, warehouses, shipping, "
            "returns, conversations, messages, and attachments across multiple "
            "channels (Facebook, Zalo, TikTok Shop, Website). "
            "For POS tools, call get_shops first to obtain the shop_id. "
            "For chat tools, you need the page_id from your connected channels."
        ),
    )

    register_shop_tools(mcp)
    register_order_tools(mcp)
    register_inventory_tools(mcp)
    register_shipping_tools(mcp)
    register_conversation_tools(mcp)
    register_attachment_tools(mcp)

    return mcp


_mcp = create_app()
_mcp_app = _mcp.http_app(path="/mcp")


async def _health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "server": "pancake-pos-mcp"})


# Composite ASGI app: /health + /mcp
app = Starlette(
    routes=[
        Route("/health", _health),
        Mount("/", app=_mcp_app),
    ]
)


def main() -> None:
    """HTTP mode — for Claude custom connectors (remote deployment)."""
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8000"))
    logger.info("Starting Pancake MCP server on %s:%s", host, port)
    uvicorn.run("pancake_mcp.server:app", host=host, port=port, reload=False)


def main_stdio() -> None:
    """Stdio mode — for Claude Desktop (local, credentials never leave machine).

    Requires at least one of PANCAKE_API_KEY or PANCAKE_ACCESS_TOKEN env vars.
    """
    api_key = os.getenv("PANCAKE_API_KEY", "").strip()
    access_token = os.getenv("PANCAKE_ACCESS_TOKEN", "").strip()
    if not api_key and not access_token:
        raise SystemExit(
            "Error: PANCAKE_API_KEY or PANCAKE_ACCESS_TOKEN env var is required for stdio mode.\n"
            "Set it in your Claude Desktop config (see README)."
        )
    # Log to stderr only — stdout is reserved for MCP protocol messages
    logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
    asyncio.run(_mcp.run())  # stdio transport (default)


if __name__ == "__main__":
    main()
