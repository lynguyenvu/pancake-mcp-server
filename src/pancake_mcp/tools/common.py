"""Shared helpers for all MCP tool modules."""

import json
from typing import Any

from pancake_mcp.client import PancakeClient
from pancake_mcp.deps import get_api_key

MAX_PAGE_SIZE = 50


def get_client() -> PancakeClient:
    """Build a PancakeClient from the current request's API key."""
    return PancakeClient(get_api_key())


def fmt(data: Any) -> str:
    """Serialize data to a compact JSON string (UTF-8 safe)."""
    return json.dumps(data, ensure_ascii=False, indent=2)


def clamp_page_size(page_size: int) -> int:
    """Enforce a maximum page_size to avoid upstream overload."""
    return min(page_size, MAX_PAGE_SIZE)
