"""Async HTTP clients for Pancake APIs.

BasePancakeClient — shared HTTP plumbing (auth, get/post/put, error handling).
PancakeClient     — POS API (https://pos.pages.fm/api/v1), auth via api_key.
"""

import os
from typing import Any

import httpx

PANCAKE_API_BASE_URL = os.getenv("PANCAKE_API_BASE_URL", "https://pos.pages.fm/api/v1")
DEFAULT_TIMEOUT = 30.0


class PancakeAPIError(Exception):
    """Raised when the Pancake API returns a non-2xx response."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(f"Pancake API error {status_code}: {message}")


class BasePancakeClient:
    """Shared async HTTP client base for all Pancake APIs."""

    def __init__(self, *, base_url: str, auth_param: str, auth_value: str, timeout: float = DEFAULT_TIMEOUT) -> None:
        self._auth_param = auth_param
        self._auth_value = auth_value
        self._http = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            headers={"Content-Type": "application/json"},
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self._http.aclose()

    def _params(self, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        """Build query params, always including the auth credential."""
        params: dict[str, Any] = {self._auth_param: self._auth_value}
        if extra:
            params.update({k: v for k, v in extra.items() if v is not None})
        return params

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        resp = await self._http.get(path, params=self._params(params))
        return self._handle(resp)

    async def _post(self, path: str, body: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
        resp = await self._http.post(path, json=body, params=self._params(params))
        return self._handle(resp)

    async def _put(self, path: str, body: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
        resp = await self._http.put(path, json=body, params=self._params(params))
        return self._handle(resp)

    @staticmethod
    def _handle(resp: httpx.Response) -> Any:
        if resp.status_code >= 400:
            try:
                detail = resp.json().get("message", resp.text)
            except Exception:
                detail = resp.text
            raise PancakeAPIError(resp.status_code, detail)
        try:
            return resp.json()
        except Exception:
            return {"raw": resp.text}


class PancakeClient(BasePancakeClient):
    """Async client for Pancake POS API. One instance per request (stateless)."""

    def __init__(self, api_key: str) -> None:
        super().__init__(
            base_url=PANCAKE_API_BASE_URL,
            auth_param="api_key",
            auth_value=api_key,
        )

    # ------------------------------------------------------------------
    # Shop
    # ------------------------------------------------------------------

    async def get_shops(self) -> Any:
        return await self._get("/shops")

    async def get_payment_methods(self, shop_id: str) -> Any:
        return await self._get(f"/shops/{shop_id}/bank_payments")

    # ------------------------------------------------------------------
    # Geographic data
    # ------------------------------------------------------------------

    async def get_provinces(self, country_code: str = "VN") -> Any:
        return await self._get("/geo/provinces", {"country_code": country_code})

    async def get_districts(self, province_id: str) -> Any:
        return await self._get("/geo/districts", {"province_id": province_id})

    async def get_communes(self, district_id: str) -> Any:
        return await self._get("/geo/communes", {"district_id": district_id})

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------

    async def list_orders(self, shop_id: str, **filters: Any) -> Any:
        return await self._get(f"/shops/{shop_id}/orders", filters)

    async def get_order(self, shop_id: str, order_id: str) -> Any:
        return await self._get(f"/shops/{shop_id}/orders/{order_id}")

    async def create_order(self, shop_id: str, payload: dict[str, Any]) -> Any:
        return await self._post(f"/shops/{shop_id}/orders", payload)

    async def update_order(self, shop_id: str, order_id: str, payload: dict[str, Any]) -> Any:
        return await self._put(f"/shops/{shop_id}/orders/{order_id}", payload)

    async def get_order_tags(self, shop_id: str) -> Any:
        return await self._get(f"/shops/{shop_id}/orders/tags")

    async def get_order_sources(self, shop_id: str) -> Any:
        return await self._get(f"/shops/{shop_id}/order_source")

    async def get_active_promotions(self, shop_id: str, payload: dict[str, Any]) -> Any:
        return await self._post(f"/shops/{shop_id}/orders/get_promotion_advance_active", payload)

    async def arrange_shipment(self, shop_id: str, payload: dict[str, Any]) -> Any:
        return await self._post(f"/shops/{shop_id}/orders/arrange_shipment", payload)

    async def get_tracking_url(self, shop_id: str, payload: dict[str, Any]) -> Any:
        return await self._post(f"/shops/{shop_id}/orders/get_tracking_url", payload)

    # ------------------------------------------------------------------
    # Warehouses & inventory
    # ------------------------------------------------------------------

    async def list_warehouses(self, shop_id: str) -> Any:
        return await self._get(f"/shops/{shop_id}/warehouses")

    async def create_warehouse(self, shop_id: str, payload: dict[str, Any]) -> Any:
        return await self._post(f"/shops/{shop_id}/warehouses", payload)

    async def update_warehouse(self, shop_id: str, warehouse_id: str, payload: dict[str, Any]) -> Any:
        return await self._put(f"/shops/{shop_id}/warehouses/{warehouse_id}", payload)

    async def get_inventory_history(self, shop_id: str, **filters: Any) -> Any:
        return await self._get(f"/shops/{shop_id}/inventory_histories", filters)

    # ------------------------------------------------------------------
    # Return orders
    # ------------------------------------------------------------------

    async def list_return_orders(self, shop_id: str, **filters: Any) -> Any:
        return await self._get(f"/shops/{shop_id}/orders_returned", filters)

    async def create_return_order(self, shop_id: str, payload: dict[str, Any]) -> Any:
        return await self._post(f"/shops/{shop_id}/orders_returned", payload)
