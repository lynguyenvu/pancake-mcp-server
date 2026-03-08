"""Async HTTP client for the Pancake Chat/Inbox API.

Base URL: https://pages.fm/api/v1 (user API with access_token)
Public API: https://pages.fm/api/public_api/v1 (page API with page_access_token)

This API manages multi-channel conversations and messages (Facebook, Zalo,
TikTok Shop, Website) — separate from the POS order management API.
"""

import os
from typing import Any

from pancake_mcp.client import BasePancakeClient

PANCAKE_CHAT_BASE_URL = os.getenv("PANCAKE_CHAT_BASE_URL", "https://pages.fm/api/v1")
PANCAKE_PUBLIC_API_URL = os.getenv("PANCAKE_PUBLIC_API_URL", "https://pages.fm/api/public_api/v1")


class PancakeChatClient(BasePancakeClient):
    """Async client for Pancake Chat/Inbox API."""

    def __init__(self, access_token: str) -> None:
        super().__init__(
            base_url=PANCAKE_CHAT_BASE_URL,
            auth_param="access_token",
            auth_value=access_token,
        )
        self._access_token = access_token

    # ------------------------------------------------------------------
    # Pages
    # ------------------------------------------------------------------

    async def list_pages(self) -> Any:
        """List all connected pages (Facebook, Zalo, TikTok, Website)."""
        return await self._get("/pages")

    async def generate_page_access_token(self, page_id: str) -> Any:
        """Generate page_access_token for public API calls.

        Use this token for send_message API (requires page_access_token, not access_token).
        """
        return await self._post(f"/pages/{page_id}/generate_page_access_token", {})

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

    async def send_message(self, page_id: str, conversation_id: str, payload: dict[str, Any], page_access_token: str | None = None) -> Any:
        """Send a message or reply in a conversation.

        Args:
            page_id: Pancake page ID
            conversation_id: Conversation ID
            payload: Message payload (must include 'action' and 'message')
            page_access_token: Required for public API. Generate via generate_page_access_token().

        Note: Send message requires page_access_token (not access_token).
        Use generate_page_access_token() first, then pass the token here.
        """
        if page_access_token:
            # Use public API with page_access_token
            async with self._http.__class__(
                base_url=PANCAKE_PUBLIC_API_URL,
                timeout=self._http.timeout,
                headers={"Content-Type": "application/json"},
            ) as public_client:
                resp = await public_client.post(
                    f"/pages/{page_id}/conversations/{conversation_id}/messages",
                    json=payload,
                    params={"page_access_token": page_access_token},
                )
                return self._handle(resp)
        else:
            # Fallback to user API (may not work for send_message)
            return await self._post(
                f"/pages/{page_id}/conversations/{conversation_id}/messages", payload
            )

    # ------------------------------------------------------------------
    # Customers
    # ------------------------------------------------------------------

    async def get_customer(self, page_id: str, psid: str) -> Any:
        """Get customer profile and interaction history by PSID."""
        return await self._get(f"/pages/{page_id}/conversations", {"psid": psid})
