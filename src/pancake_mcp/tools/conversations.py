"""MCP tools for Pancake inbox — conversations and messages management.

Uses the pages.fm Chat API (separate from POS API).
Requires PANCAKE_ACCESS_TOKEN (or falls back to PANCAKE_API_KEY).
"""

from typing import Any

from pancake_mcp.tools.common import (
    build_payload, call_api, clamp_page_size, get_chat_client,
)


def register_conversation_tools(mcp: Any) -> None:
    """Register conversation and message tools onto the FastMCP instance."""

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    async def list_pages() -> str:
        """List all connected pages/channels (Facebook, Zalo, TikTok Shop, Website).

        Use this tool to discover page_id values needed for other conversation tools.
        Only requires PANCAKE_ACCESS_TOKEN — no PANCAKE_API_KEY needed.

        Returns:
            JSON with categorized pages: activated (connected), expired, etc.
            Each page has: id (use as page_id), name, platform, username.
        """
        return await call_api(get_chat_client, lambda c: c.list_pages())

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    async def list_conversations(
        page_id: str,
        conv_type: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
        keyword: str | None = None,
        tag: str | None = None,
        assigned_to: str | None = None,
    ) -> str:
        """List conversations (inbox threads) for a connected channel page.

        Supports Facebook, Zalo, TikTok Shop, and Website channels.
        Use get_shops to find your shop's linked page_id values.

        Args:
            page_id: Pancake page ID (represents a connected channel).
            conv_type: Filter by type — "INBOX" (DMs), "COMMENT", "COMMENT_LIVESTREAM", "POST".
            status: Filter by status — "open", "closed", "pending".
            page: Page number (default 1).
            page_size: Results per page, max 50 (default 20).
            keyword: Search by customer name or message content.
            tag: Filter by conversation tag name.
            assigned_to: Filter by assigned staff user ID.

        Returns:
            JSON list of conversations with customer info, last message, status, and tags.
        """
        return await call_api(
            get_chat_client,
            lambda c: c.list_conversations(
                page_id,
                type=conv_type,
                status=status,
                page=page,
                page_size=clamp_page_size(page_size),
                keyword=keyword,
                tag=tag,
                assigned_to=assigned_to,
            ),
        )

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    async def get_conversation(page_id: str, conversation_id: str) -> str:
        """Get full details of a single conversation including customer profile.

        Args:
            page_id: Pancake page ID.
            conversation_id: Conversation ID from list_conversations.

        Returns:
            JSON with conversation details, customer info, tags, and assigned staff.
        """
        return await call_api(
            get_chat_client,
            lambda c: c.get_conversation(page_id, conversation_id),
        )

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    async def get_messages(
        page_id: str,
        conversation_id: str,
        customer_id: str | None = None,
        page: int = 1,
        page_size: int = 30,
    ) -> str:
        """Get message history for a conversation.

        Args:
            page_id: Pancake page ID.
            conversation_id: Conversation ID from list_conversations.
            customer_id: Customer ID to authenticate the request (required for some accounts).
            page: Page number (default 1, newest first).
            page_size: Messages per page, max 50 (default 30).

        Returns:
            JSON list of messages with content, sender, timestamp, and attachments.
        """
        params: dict[str, Any] = {"page": page, "page_size": clamp_page_size(page_size)}
        if customer_id:
            params["customer_id"] = customer_id

        return await call_api(
            get_chat_client,
            lambda c: c.get_messages(page_id, conversation_id, **params),
        )

    @mcp.tool(annotations={"destructiveHint": False, "openWorldHint": True})
    async def send_message(
        page_id: str,
        conversation_id: str,
        message: str,
        attachment_url: str | None = None,
    ) -> str:
        """Send a message or reply in a conversation.

        Can reply to both inbox DMs and comments.
        Note: Internally adds 'action: message' to payload (required by Pancake API).

        Args:
            page_id: Pancake page ID.
            conversation_id: Conversation ID from list_conversations.
            message: Text content of the message to send.
            attachment_url: Optional public URL of an image or file to attach.

        Returns:
            JSON with sent message details and delivery status.
        """
        payload = build_payload(
            {"action": "message", "message": message},
            attachment_url=attachment_url,
        )
        return await call_api(
            get_chat_client,
            lambda c: c.send_message(page_id, conversation_id, payload),
        )

    @mcp.tool(annotations={"idempotentHint": False, "openWorldHint": True})
    async def update_conversation(
        page_id: str,
        conversation_id: str,
        status: str | None = None,
        assigned_to: str | None = None,
        tags: str | None = None,
        note: str | None = None,
    ) -> str:
        """Update a conversation — assign staff, add tags, change status.

        Args:
            page_id: Pancake page ID.
            conversation_id: Conversation ID to update.
            status: New status — "open", "closed", "pending".
            assigned_to: Staff user ID to assign this conversation to.
            tags: Comma-separated tag names to apply (replaces existing tags).
            note: Internal note to add to the conversation.

        Returns:
            JSON with updated conversation details.
        """
        payload = build_payload({}, status=status, assigned_to=assigned_to, note=note)
        if tags is not None:
            payload["tags"] = [t.strip() for t in tags.split(",") if t.strip()]

        if not payload:
            return "Error: Provide at least one field to update."

        return await call_api(
            get_chat_client,
            lambda c: c.update_conversation(page_id, conversation_id, payload),
        )
