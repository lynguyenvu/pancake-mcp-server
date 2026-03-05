"""Shared dependency helpers for MCP tool handlers.

Provides:
- get_api_key()      → Pancake POS API key (pos.pages.fm)
- get_access_token() → Pancake Chat API token (pages.fm conversations)

Both default to the Bearer token from the HTTP request.
"""

import os

from fastmcp.server.dependencies import get_http_request


def _bearer_from_request() -> str:
    """Extract Bearer token from the current HTTP request. Returns '' if unavailable."""
    try:
        request = get_http_request()
        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            return auth[7:].strip()
    except RuntimeError:
        # Raised outside an HTTP request context (e.g. stdio mode)
        pass
    return ""


def get_api_key() -> str:
    """Return the Pancake API key for the current request.

    Precedence:
    1. PANCAKE_API_KEY env var (set for single-tenant deployments)
    2. Authorization: Bearer <token> header from the incoming HTTP request

    Raises:
        ValueError: If no API key can be found.
    """
    fixed = os.getenv("PANCAKE_API_KEY", "").strip()
    if fixed:
        return fixed
    key = _bearer_from_request()
    if key:
        return key
    raise ValueError(
        "No Pancake API key found. "
        "Set PANCAKE_API_KEY env var or pass your key as 'Authorization: Bearer <key>'."
    )


def get_access_token() -> str:
    """Return the Pancake Chat API access token for the current request.

    Precedence:
    1. PANCAKE_ACCESS_TOKEN env var (explicit chat token)
    2. PANCAKE_API_KEY env var (fallback — paid API key works for all APIs)
    3. Authorization: Bearer <token> header

    Raises:
        ValueError: If no token can be found.
    """
    token = os.getenv("PANCAKE_ACCESS_TOKEN", "").strip()
    if token:
        return token
    # Fall back to the same key used for POS API
    return get_api_key()
