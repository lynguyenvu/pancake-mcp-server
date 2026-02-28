"""Unit tests for PancakeClient using respx to mock HTTP calls."""

import pytest
import respx
import httpx

from pancake_mcp.client import PancakeClient, PancakeAPIError

API_KEY = "test-api-key"
BASE = "https://pos.pages.fm/api/v1"


@pytest.fixture
def client():
    return PancakeClient(API_KEY)


@respx.mock
@pytest.mark.asyncio
async def test_get_shops(client):
    respx.get(f"{BASE}/shops").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "shop1", "name": "My Shop"}]})
    )
    async with client:
        result = await client.get_shops()
    assert result["data"][0]["id"] == "shop1"


@respx.mock
@pytest.mark.asyncio
async def test_list_orders_passes_filters(client):
    route = respx.get(f"{BASE}/shops/shop1/orders").mock(
        return_value=httpx.Response(200, json={"data": [], "total_entries": 0})
    )
    async with client:
        await client.list_orders("shop1", status="new", page=2, page_size=10)
    assert route.called
    params = dict(route.calls[0].request.url.params)
    assert params["status"] == "new"
    assert params["page"] == "2"
    assert params["api_key"] == API_KEY


@respx.mock
@pytest.mark.asyncio
async def test_create_order(client):
    respx.post(f"{BASE}/shops/shop1/orders").mock(
        return_value=httpx.Response(201, json={"data": {"id": "order123"}})
    )
    async with client:
        result = await client.create_order("shop1", {"customer_name": "Nam"})
    assert result["data"]["id"] == "order123"


@respx.mock
@pytest.mark.asyncio
async def test_api_error_raises(client):
    respx.get(f"{BASE}/shops").mock(
        return_value=httpx.Response(401, json={"message": "Unauthorized"})
    )
    with pytest.raises(PancakeAPIError) as exc_info:
        async with client:
            await client.get_shops()
    assert exc_info.value.status_code == 401
    assert "Unauthorized" in str(exc_info.value)


@respx.mock
@pytest.mark.asyncio
async def test_get_provinces(client):
    respx.get(f"{BASE}/geo/provinces").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "01", "name": "Hà Nội"}]})
    )
    async with client:
        result = await client.get_provinces("VN")
    assert result["data"][0]["name"] == "Hà Nội"


@respx.mock
@pytest.mark.asyncio
async def test_list_warehouses(client):
    respx.get(f"{BASE}/shops/shop1/warehouses").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "wh1", "name": "Kho 1"}]})
    )
    async with client:
        result = await client.list_warehouses("shop1")
    assert result["data"][0]["id"] == "wh1"


@respx.mock
@pytest.mark.asyncio
async def test_arrange_shipment(client):
    respx.post(f"{BASE}/shops/shop1/orders/arrange_shipment").mock(
        return_value=httpx.Response(200, json={"data": {"tracking_code": "GHN123"}})
    )
    async with client:
        result = await client.arrange_shipment("shop1", {"order_id": "order1"})
    assert result["data"]["tracking_code"] == "GHN123"


@respx.mock
@pytest.mark.asyncio
async def test_none_params_excluded(client):
    route = respx.get(f"{BASE}/shops/shop1/orders").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    async with client:
        await client.list_orders("shop1", status=None, from_date=None)
    params = dict(route.calls[0].request.url.params)
    # None values must not appear in query string
    assert "status" not in params
    assert "from_date" not in params
