"""Async HTTP client for the Pancake Chat/Inbox API.

Base URL: https://pages.fm/api/v1
Auth: access_token query param (same key as POS API or set PANCAKE_ACCESS_TOKEN)

This API manages Facebook/multi-channel conversations and messages —
separate from the POS order management API.
"""

import os
from typing import Any

import httpx

from pancake_mcp.client import PancakeAPIError

PANCAKE_CHAT_BASE_URL = os.getenv("PANCAKE_CHAT_BASE_URL", "https://pages.fm/api/v1")
DEFAULT_TIMEOUT = 30.0


class PancakeChatClient:
    """Async client for Pancake Chat/Inbox API."""

    def __init__(self, access_token: str) -> None:
        self._token = access_token
        self._http = httpx.AsyncClient(
            base_url=PANCAKE_CHAT_BASE_URL,
            timeout=DEFAULT_TIMEOUT,
            headers={"Content-Type": "application/json"},
        )

    async def __aenter__(self) -> "PancakeChatClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self._http.aclose()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _params(self, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {"access_token": self._token}
        if extra:
            params.update({k: v for k, v in extra.items() if v is not None})
        return params

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        resp = await self._http.get(path, params=self._params(params))
        return self._handle(resp)

    async def _post(self, path: str, body: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
        resp = await self._http.post(path, json=body, params=self._params(params))
        return self._handle(resp)

    async def _put(self, path: str, body: dict[str, Any]) -> Any:
        resp = await self._http.put(path, json=body, params=self._params())
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

    # ------------------------------------------------------------------
    # Conversations
    # ------------------------------------------------------------------

    async def list_conversations(self, page_id: str, **filters: Any) -> Any:
        """List conversations for a Facebook page."""
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
