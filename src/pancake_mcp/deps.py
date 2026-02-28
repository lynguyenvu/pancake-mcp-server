"""Shared dependency helpers for MCP tool handlers.

Provides get_api_key() to extract the Pancake API key from:
1. PANCAKE_API_KEY env var (single-tenant / fixed deployment)
2. Authorization: Bearer <token> header (multi-tenant / per-user)
"""

import os

from fastmcp.server.dependencies import get_http_request


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

    try:
        request = get_http_request()
        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            key = auth[7:].strip()
            if key:
                return key
    except RuntimeError:
        # get_http_request() raises RuntimeError outside an HTTP request context
        pass

    raise ValueError(
        "No Pancake API key found. "
        "Set PANCAKE_API_KEY env var or pass your key as 'Authorization: Bearer <key>'."
    )
