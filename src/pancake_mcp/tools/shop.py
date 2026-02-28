"""MCP tools for shop info, payment methods, and geographic data."""

from typing import Any

from fastmcp import Context

from pancake_mcp.client import PancakeAPIError
from pancake_mcp.tools.common import fmt, get_client


def register_shop_tools(mcp: Any) -> None:
    """Register shop and geo tools onto the FastMCP instance."""

    @mcp.tool(
        annotations={"readOnlyHint": True, "openWorldHint": True}
    )
    async def get_shops(ctx: Context) -> str:
        """List all shops linked to the current Pancake account.

        Returns shop IDs, names, and linked Facebook pages. Use the returned
        shop_id values in other tools that require a shop_id parameter.

        Returns:
            JSON with list of shops including id, name, pages.
        """
        try:
            async with get_client() as c:
                result = await c.get_shops()
            return fmt(result)
        except PancakeAPIError as e:
            return f"Error: {e}. Check your API key is valid."

    @mcp.tool(
        annotations={"readOnlyHint": True, "openWorldHint": True}
    )
    async def get_payment_methods(ctx: Context, shop_id: str) -> str:
        """List available bank payment methods configured for a shop.

        Args:
            shop_id: The shop ID (get from get_shops tool).

        Returns:
            JSON list of payment methods with bank name, account number, owner.
        """
        try:
            async with get_client() as c:
                result = await c.get_payment_methods(shop_id)
            return fmt(result)
        except PancakeAPIError as e:
            return f"Error fetching payment methods: {e}"

    @mcp.tool(
        annotations={"readOnlyHint": True, "openWorldHint": True}
    )
    async def get_provinces(ctx: Context, country_code: str = "VN") -> str:
        """List provinces/cities for address input.

        Use this to get province_id values needed for get_districts.

        Args:
            country_code: ISO country code, default "VN" for Vietnam.

        Returns:
            JSON list of provinces with id and name.
        """
        try:
            async with get_client() as c:
                result = await c.get_provinces(country_code)
            return fmt(result)
        except PancakeAPIError as e:
            return f"Error fetching provinces: {e}"

    @mcp.tool(
        annotations={"readOnlyHint": True, "openWorldHint": True}
    )
    async def get_districts(ctx: Context, province_id: str) -> str:
        """List districts within a province for address input.

        Use this to get district_id values needed for get_communes.

        Args:
            province_id: Province ID from get_provinces tool.

        Returns:
            JSON list of districts with id and name.
        """
        try:
            async with get_client() as c:
                result = await c.get_districts(province_id)
            return fmt(result)
        except PancakeAPIError as e:
            return f"Error fetching districts: {e}"

    @mcp.tool(
        annotations={"readOnlyHint": True, "openWorldHint": True}
    )
    async def get_communes(ctx: Context, district_id: str) -> str:
        """List communes/wards within a district for address input.

        Args:
            district_id: District ID from get_districts tool.

        Returns:
            JSON list of communes with id and name.
        """
        try:
            async with get_client() as c:
                result = await c.get_communes(district_id)
            return fmt(result)
        except PancakeAPIError as e:
            return f"Error fetching communes: {e}"

