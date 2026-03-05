"""MCP tools for warehouse and inventory management."""

from typing import Any

from pancake_mcp.tools.common import build_payload, call_api, clamp_page_size, get_client


def register_inventory_tools(mcp: Any) -> None:
    """Register warehouse and inventory tools onto the FastMCP instance."""

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    async def list_warehouses(shop_id: str) -> str:
        """List all warehouses configured for a shop.

        Args:
            shop_id: Shop ID from get_shops.

        Returns:
            JSON list of warehouses with id, name, address, and status.
        """
        return await call_api(get_client, lambda c: c.list_warehouses(shop_id))

    @mcp.tool(annotations={"destructiveHint": False, "openWorldHint": True})
    async def create_warehouse(
        shop_id: str,
        name: str,
        address: str | None = None,
        province_id: str | None = None,
        district_id: str | None = None,
        commune_id: str | None = None,
        phone: str | None = None,
    ) -> str:
        """Create a new warehouse for a shop.

        Args:
            shop_id: Shop ID from get_shops.
            name: Warehouse name (required).
            address: Street address of warehouse.
            province_id: Province ID from get_provinces.
            district_id: District ID from get_districts.
            commune_id: Commune ID from get_communes.
            phone: Contact phone number for this warehouse.

        Returns:
            JSON with created warehouse details including the new warehouse_id.
        """
        payload = build_payload(
            {"name": name},
            address=address, province_id=province_id, district_id=district_id,
            commune_id=commune_id, phone=phone,
        )
        return await call_api(get_client, lambda c: c.create_warehouse(shop_id, payload))

    @mcp.tool(annotations={"idempotentHint": False, "openWorldHint": True})
    async def update_warehouse(
        shop_id: str,
        warehouse_id: str,
        name: str | None = None,
        address: str | None = None,
        province_id: str | None = None,
        district_id: str | None = None,
        commune_id: str | None = None,
        phone: str | None = None,
        is_active: bool | None = None,
    ) -> str:
        """Update warehouse details. Only provide fields to change.

        Args:
            shop_id: Shop ID from get_shops.
            warehouse_id: Warehouse ID to update.
            name: New warehouse name.
            address: Updated street address.
            province_id: Updated province.
            district_id: Updated district.
            commune_id: Updated commune.
            phone: Updated contact phone.
            is_active: Set warehouse active (true) or inactive (false).

        Returns:
            JSON with updated warehouse details.
        """
        payload = build_payload(
            {},
            name=name, address=address, province_id=province_id,
            district_id=district_id, commune_id=commune_id,
            phone=phone, is_active=is_active,
        )

        if not payload:
            return "Error: Provide at least one field to update."

        return await call_api(get_client, lambda c: c.update_warehouse(shop_id, warehouse_id, payload))

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    async def get_inventory_history(
        shop_id: str,
        warehouse_id: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> str:
        """Get stock movement history (imports and exports) for a shop.

        Args:
            shop_id: Shop ID from get_shops.
            warehouse_id: Filter by specific warehouse ID (optional).
            from_date: Start date filter in YYYY-MM-DD format.
            to_date: End date filter in YYYY-MM-DD format.
            page: Page number (default 1).
            page_size: Results per page (default 20).

        Returns:
            JSON list of inventory transactions with quantity changes and timestamps.
        """
        return await call_api(
            get_client,
            lambda c: c.get_inventory_history(
                shop_id,
                warehouse_id=warehouse_id,
                from_date=from_date,
                to_date=to_date,
                page=page,
                page_size=clamp_page_size(page_size),
            ),
        )
