"""Integration tests for FastMCP server — health endpoint and tool registration."""

import pytest
from starlette.testclient import TestClient

from pancake_mcp.server import app, _mcp


def test_health_endpoint():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["server"] == "pancake-pos-mcp"


@pytest.mark.asyncio
async def test_all_tools_registered():
    """Verify all 25 expected tools are registered on the MCP instance."""
    expected = {
        # shop
        "get_shops", "get_payment_methods",
        "get_provinces", "get_districts", "get_communes",
        # orders
        "search_orders", "get_order", "create_order", "update_order",
        "get_order_tags", "get_order_sources", "get_active_promotions",
        # inventory
        "list_warehouses", "create_warehouse", "update_warehouse", "get_inventory_history",
        # shipping
        "arrange_shipment", "get_tracking_url", "list_return_orders", "create_return_order",
        # conversations
        "list_conversations", "get_conversation", "get_messages",
        "send_message", "update_conversation",
    }
    tools = await _mcp.list_tools()
    registered = {t.name for t in tools}
    missing = expected - registered
    assert not missing, f"Missing tools: {missing}"
    assert len(registered) >= len(expected)
