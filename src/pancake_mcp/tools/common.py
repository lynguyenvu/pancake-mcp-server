"""Shared helpers for all MCP tool modules."""

import json
from typing import Any, Callable, Awaitable

from pancake_mcp.client import PancakeAPIError, BasePancakeClient, PancakeClient
from pancake_mcp.chat_client import PancakeChatClient
from pancake_mcp.deps import get_access_token, get_api_key

MAX_PAGE_SIZE = 50


def get_client() -> PancakeClient:
    """Build a PancakeClient (POS API) from the current request's API key."""
    return PancakeClient(get_api_key())


def get_chat_client() -> PancakeChatClient:
    """Build a PancakeChatClient (Chat/Inbox API) from the current request's access token."""
    return PancakeChatClient(get_access_token())


def fmt(data: Any) -> str:
    """Serialize data to a compact JSON string (UTF-8 safe)."""
    return json.dumps(data, ensure_ascii=False, indent=2)


def clamp_page_size(page_size: int) -> int:
    """Enforce a maximum page_size to avoid upstream overload."""
    return min(page_size, MAX_PAGE_SIZE)


def build_payload(required: dict[str, Any], **optional: Any) -> dict[str, Any]:
    """Build an API payload from required fields plus optional ones (None values excluded)."""
    payload = dict(required)
    payload.update({k: v for k, v in optional.items() if v is not None})
    return payload


def parse_json_param(value: str, param_name: str) -> tuple[Any, str | None]:
    """Parse a JSON string parameter, returning (parsed_value, None) or (None, error_message)."""
    try:
        return json.loads(value), None
    except json.JSONDecodeError:
        return None, f"Error: '{param_name}' must be a valid JSON string."


async def call_api(
    client_factory: Callable[[], BasePancakeClient],
    action: Callable[[Any], Awaitable[Any]],
) -> str:
    """Execute an API call with standard error handling.

    Usage: return await call_api(get_client, lambda c: c.get_shops())
    """
    try:
        async with client_factory() as client:
            result = await action(client)
        return fmt(result)
    except PancakeAPIError as e:
        return f"Error: {e}"
