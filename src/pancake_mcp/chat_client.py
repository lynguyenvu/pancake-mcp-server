"""Async HTTP client for the Pancake Chat/Inbox API.

Base URL: https://pages.fm/api/v1
Auth: access_token query param (same key as POS API or set PANCAKE_ACCESS_TOKEN)

This API manages multi-channel conversations and messages (Facebook, Zalo,
TikTok Shop, Website) — separate from the POS order management API.
"""

import os
from typing import Any

from pancake_mcp.client import BasePancakeClient

PANCAKE_CHAT_BASE_URL = os.getenv("PANCAKE_CHAT_BASE_URL", "https://pages.fm/api/v1")


class PancakeChatClient(BasePancakeClient):
    """Async client for Pancake Chat/Inbox API."""

    def __init__(self, access_token: str) -> None:
        super().__init__(
            base_url=PANCAKE_CHAT_BASE_URL,
            auth_param="access_token",
            auth_value=access_token,
        )

    # ------------------------------------------------------------------
    # Conversations
    # ------------------------------------------------------------------

    async def list_conversations(self, page_id: str, **filters: Any) -> Any:
        """List conversations for a Pancake page."""
        return await self._get(f"/pages/{page_id}/conversations", filters)

    async def get_conversation(self, page_id: str, conversation_id: str) -> Any:
        """Get a single conversation with customer info."""
        return await self._get(f"/pages/{page_id}/conversations/{conversation_id}")

    async def update_conversation(self, page_id: str, conversation_id: str, payload: dict[str, Any]) -> Any:
        """Update conversation (assign staff, add tags, change status)."""
        return await self._put(f"/pages/{page_id}/conversations/{conversation_id}", payload)

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------

    async def get_messages(self, page_id: str, conversation_id: str, **params: Any) -> Any:
        """Get messages in a conversation."""
        return await self._get(
            f"/pages/{page_id}/conversations/{conversation_id}/messages", params
        )

    async def send_message(self, page_id: str, conversation_id: str, payload: dict[str, Any]) -> Any:
        """Send a message or reply in a conversation."""
        return await self._post(
            f"/pages/{page_id}/conversations/{conversation_id}/messages", payload
        )

    # ------------------------------------------------------------------
    # Customers
    # ------------------------------------------------------------------

    async def get_customer(self, page_id: str, psid: str) -> Any:
        """Get customer profile and interaction history by PSID."""
        return await self._get(f"/pages/{page_id}/conversations", {"psid": psid})
