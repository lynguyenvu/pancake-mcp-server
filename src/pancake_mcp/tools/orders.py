"""MCP tools for order management."""

from typing import Any

from pancake_mcp.tools.common import (
    build_payload, call_api, clamp_page_size, get_client, parse_json_param,
)


def register_order_tools(mcp: Any) -> None:
    """Register order management tools onto the FastMCP instance."""

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    async def search_orders(
        shop_id: str,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
        tags: str | None = None,
        source_id: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        keyword: str | None = None,
    ) -> str:
        """Search and filter orders for a shop.

        Args:
            shop_id: Shop ID from get_shops.
            status: Filter by status e.g. "new", "confirmed", "shipping", "done", "cancelled".
            page: Page number (default 1).
            page_size: Results per page, max 50 (default 20).
            tags: Comma-separated tag names to filter by.
            source_id: Filter by order source ID.
            from_date: Start date filter in YYYY-MM-DD format.
            to_date: End date filter in YYYY-MM-DD format.
            keyword: Search by customer name, phone, or order code.

        Returns:
            JSON with orders list and pagination info (total_entries, total_pages).
        """
        return await call_api(
            get_client,
            lambda c: c.list_orders(
                shop_id,
                status=status,
                page=page,
                page_size=clamp_page_size(page_size),
                tags=tags,
                source_id=source_id,
                from_date=from_date,
                to_date=to_date,
                keyword=keyword,
            ),
        )

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    async def get_order(shop_id: str, order_id: str) -> str:
        """Get full details of a single order including line items, customer, shipping.

        Args:
            shop_id: Shop ID from get_shops.
            order_id: Order ID to retrieve.

        Returns:
            JSON with complete order details.
        """
        return await call_api(get_client, lambda c: c.get_order(shop_id, order_id))

    @mcp.tool(annotations={"destructiveHint": False, "openWorldHint": True})
    async def create_order(
        shop_id: str,
        customer_name: str,
        customer_phone: str,
        items: str,
        address: str | None = None,
        province_id: str | None = None,
        district_id: str | None = None,
        commune_id: str | None = None,
        note: str | None = None,
        source_id: str | None = None,
        payment_method: str | None = None,
    ) -> str:
        """Create a new order in Pancake POS.

        Args:
            shop_id: Shop ID from get_shops.
            customer_name: Full name of the customer.
            customer_phone: Customer phone number.
            items: JSON string array of line items, each with product_id and quantity.
                   Example: '[{"product_id": "123", "quantity": 2}]'
            address: Street address for delivery.
            province_id: Province ID from get_provinces.
            district_id: District ID from get_districts.
            commune_id: Commune ID from get_communes.
            note: Internal note for this order.
            source_id: Order source ID from get_order_sources.
            payment_method: Payment method identifier.

        Returns:
            JSON with created order details including the new order_id.
        """
        line_items, err = parse_json_param(items, "items")
        if err:
            return err

        payload = build_payload(
            {"customer_name": customer_name, "customer_phone": customer_phone, "items": line_items},
            address=address, province_id=province_id, district_id=district_id,
            commune_id=commune_id, note=note, source_id=source_id,
            payment_method=payment_method,
        )

        return await call_api(get_client, lambda c: c.create_order(shop_id, payload))

    @mcp.tool(annotations={"idempotentHint": False, "openWorldHint": True})
    async def update_order(
        shop_id: str,
        order_id: str,
        status: str | None = None,
        note: str | None = None,
        customer_name: str | None = None,
        customer_phone: str | None = None,
        address: str | None = None,
        province_id: str | None = None,
        district_id: str | None = None,
        commune_id: str | None = None,
    ) -> str:
        """Update fields on an existing order.

        Only provide the fields you want to change — unset fields are left unchanged.

        Args:
            shop_id: Shop ID from get_shops.
            order_id: Order ID to update.
            status: New status: "confirmed", "shipping", "done", "cancelled".
            note: Update internal note.
            customer_name: Update customer name.
            customer_phone: Update customer phone.
            address: Update delivery address.
            province_id: Update province.
            district_id: Update district.
            commune_id: Update commune.

        Returns:
            JSON with updated order details.
        """
        payload = build_payload(
            {},
            status=status, note=note, customer_name=customer_name,
            customer_phone=customer_phone, address=address,
            province_id=province_id, district_id=district_id,
            commune_id=commune_id,
        )

        if not payload:
            return "Error: Provide at least one field to update."

        return await call_api(get_client, lambda c: c.update_order(shop_id, order_id, payload))

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    async def get_order_tags(shop_id: str) -> str:
        """List all available order tags for a shop.

        Use tag names when filtering orders with search_orders.

        Args:
            shop_id: Shop ID from get_shops.

        Returns:
            JSON list of tags with id and name.
        """
        return await call_api(get_client, lambda c: c.get_order_tags(shop_id))

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    async def get_order_sources(shop_id: str) -> str:
        """List available order sources (e.g. Facebook, Zalo, Website, Phone).

        Use source_id when creating or filtering orders.

        Args:
            shop_id: Shop ID from get_shops.

        Returns:
            JSON list of order sources with id and name.
        """
        return await call_api(get_client, lambda c: c.get_order_sources(shop_id))

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    async def get_active_promotions(shop_id: str, items: str) -> str:
        """Get currently active promotions applicable to a set of items.

        Args:
            shop_id: Shop ID from get_shops.
            items: JSON string array of items to check promotions for.
                   Example: '[{"product_id": "123", "quantity": 2}]'

        Returns:
            JSON list of applicable promotions with discount details.
        """
        line_items, err = parse_json_param(items, "items")
        if err:
            return err

        return await call_api(
            get_client,
            lambda c: c.get_active_promotions(shop_id, {"items": line_items}),
        )
