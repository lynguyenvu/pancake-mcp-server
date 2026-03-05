"""MCP tools for shipping, tracking, and return orders."""

from typing import Any

from pancake_mcp.tools.common import (
    build_payload, call_api, clamp_page_size, get_client, parse_json_param,
)


def register_shipping_tools(mcp: Any) -> None:
    """Register shipping and return order tools onto the FastMCP instance."""

    @mcp.tool(annotations={"idempotentHint": False, "openWorldHint": True})
    async def arrange_shipment(
        shop_id: str,
        order_id: str,
        carrier_code: str | None = None,
        warehouse_id: str | None = None,
        note: str | None = None,
    ) -> str:
        """Prepare an order for shipping — hands off to a delivery carrier.

        Call this after confirming an order to create the shipment with the carrier.

        Args:
            shop_id: Shop ID from get_shops.
            order_id: Order ID to ship.
            carrier_code: Delivery carrier code (e.g. "ghn", "ghtk", "viettelpost").
            warehouse_id: Source warehouse ID from list_warehouses.
            note: Shipping note for the carrier.

        Returns:
            JSON with shipment details and carrier tracking code.
        """
        payload = build_payload(
            {"order_id": order_id},
            carrier_code=carrier_code, warehouse_id=warehouse_id, note=note,
        )
        return await call_api(get_client, lambda c: c.arrange_shipment(shop_id, payload))

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    async def get_tracking_url(shop_id: str, order_id: str) -> str:
        """Get a tracking URL so the customer can monitor their delivery.

        Args:
            shop_id: Shop ID from get_shops.
            order_id: Order ID to get tracking for.

        Returns:
            JSON with tracking_url and current delivery status.
        """
        return await call_api(
            get_client,
            lambda c: c.get_tracking_url(shop_id, {"order_id": order_id}),
        )

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    async def list_return_orders(
        shop_id: str,
        page: int = 1,
        page_size: int = 20,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> str:
        """List return/exchange orders for a shop.

        Args:
            shop_id: Shop ID from get_shops.
            page: Page number (default 1).
            page_size: Results per page (default 20).
            from_date: Filter returns from this date (YYYY-MM-DD).
            to_date: Filter returns up to this date (YYYY-MM-DD).

        Returns:
            JSON with list of return orders and pagination info.
        """
        return await call_api(
            get_client,
            lambda c: c.list_return_orders(
                shop_id,
                page=page,
                page_size=clamp_page_size(page_size),
                from_date=from_date,
                to_date=to_date,
            ),
        )

    @mcp.tool(annotations={"destructiveHint": False, "openWorldHint": True})
    async def create_return_order(
        shop_id: str,
        original_order_id: str,
        reason: str,
        items: str,
        refund_amount: float | None = None,
        note: str | None = None,
    ) -> str:
        """Process a product return linked to an original order.

        Args:
            shop_id: Shop ID from get_shops.
            original_order_id: The order being returned.
            reason: Return reason (e.g. "defective", "wrong_item", "customer_changed_mind").
            items: JSON string array of returned items with product_id and quantity.
                   Example: '[{"product_id": "123", "quantity": 1}]'
            refund_amount: Refund amount in VND (optional, defaults to item value).
            note: Internal note for this return.

        Returns:
            JSON with created return order details including return_id.
        """
        return_items, err = parse_json_param(items, "items")
        if err:
            return err

        payload = build_payload(
            {"original_order_id": original_order_id, "reason": reason, "items": return_items},
            refund_amount=refund_amount, note=note,
        )

        return await call_api(get_client, lambda c: c.create_return_order(shop_id, payload))
