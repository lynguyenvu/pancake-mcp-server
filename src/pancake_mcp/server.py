"""FastMCP server entry point for the Pancake POS MCP integration.

Transport: Streamable HTTP (Claude custom connector compatible)
Auth: Bearer token = user's Pancake API key (stateless pass-through)

Run:
    uvicorn pancake_mcp.server:app --host 0.0.0.0 --port 8000
"""

import os
import logging

from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from pancake_mcp.tools.shop import register_shop_tools
from pancake_mcp.tools.orders import register_order_tools
from pancake_mcp.tools.inventory import register_inventory_tools
from pancake_mcp.tools.shipping import register_shipping_tools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> FastMCP:
    mcp = FastMCP(
        name="pancake-pos",
        instructions=(
            "Tools for managing a Pancake POS shop: orders, warehouses, "
            "shipping, returns, and geographic address data for Vietnam. "
            "Always call get_shops first to obtain the shop_id required by most tools. "
            "Pass your Pancake API key as the Bearer token when connecting."
        ),
    )

    register_shop_tools(mcp)
    register_order_tools(mcp)
    register_inventory_tools(mcp)
    register_shipping_tools(mcp)

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
    import uvicorn
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8000"))
    logger.info("Starting Pancake MCP server on %s:%s", host, port)
    uvicorn.run("pancake_mcp.server:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
