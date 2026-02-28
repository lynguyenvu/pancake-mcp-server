# Code Review: pancake-mcp-server

**Date:** 2026-02-28
**Reviewer:** code-reviewer agent
**Score: 8.0 / 10**

---

## Scope

- Files: `client.py`, `deps.py`, `server.py`, `tools/shop.py`, `tools/orders.py`, `tools/inventory.py`, `tools/shipping.py`, `tests/test_client.py`, `tests/test_server.py`
- LOC: ~700 (src) + ~140 (tests)
- Focus: full codebase

---

## Overall Assessment

Clean, well-structured codebase. Good separation of concerns, consistent patterns, clear tool descriptions for Claude. No critical security bugs. Main issues are: DRY violation across tool modules, silent exception swallowing in `deps.py`, missing input validation on pagination/page_size, no rate-limit/timeout retry, and `_fmt` / `_client` defined 3 times.

---

## Critical Issues

None.

---

## High Priority

### H1 — `_client()` and `_fmt()` duplicated in 3 tool modules (DRY violation)

`shop.py`, `orders.py`, `inventory.py`, `shipping.py` each define their own identical `_client()` and (except shop) `_fmt()`. `shop.py` also has `_fmt` but with an inline `import json` inside it.

Impact: future changes (e.g. adding a retry wrapper, logging) must be applied 4 times; easy to diverge.

Fix: extract to `pancake_mcp/tools/_common.py`:
```python
# tools/_common.py
import json
from typing import Any
from pancake_mcp.client import PancakeClient
from pancake_mcp.deps import get_api_key

def _client() -> PancakeClient:
    return PancakeClient(get_api_key())

def _fmt(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)
```
Then each tool module does `from pancake_mcp.tools._common import _client, _fmt`.

---

### H2 — Silent `except Exception: pass` in `deps.py` (line 34)

```python
try:
    request = get_http_request()
    auth = request.headers.get("authorization", "")
    ...
except Exception:
    pass
```

If `get_http_request()` raises an unexpected error (e.g. framework bug, wrong transport), it is silently swallowed and the code falls through to raise the generic `ValueError` with a misleading message about missing API key.

Fix: narrow the except or at minimum log the exception:
```python
except RuntimeError:
    # get_http_request() raises RuntimeError outside request context
    pass
```
Or log at DEBUG level to aid diagnostics without exposing data.

---

### H3 — No validation on `page_size` parameter

`search_orders`, `get_inventory_history`, `list_return_orders` accept `page_size: int = 20` with no upper bound enforcement. Docstring says "max 50" for `search_orders` but nothing prevents `page_size=10000` being sent to the API. If Pancake API doesn't enforce it, this could cause large payloads or DoS-style abuse.

Fix: add guard at tool level:
```python
if page_size > 50:
    return "Error: page_size max is 50."
```

---

## Medium Priority

### M1 — `update_warehouse` bug: `is_active=False` skipped silently

```python
for key, val in [...("is_active", is_active)]:
    if val is not None:
        payload[key] = val
```

`is_active=False` is falsy but not `None`, so this works correctly for bool. However the pattern `if val is not None` is correct here. This is fine — but worth a comment so the next developer doesn't "fix" it to `if val`:

```python
# Use `is not None` (not truthiness) so False/0/"" are included
if val is not None:
    payload[key] = val
```

### M2 — `json` import inside function body in `shop.py`

`_fmt` in `shop.py` does `import json` inside the function body (line 120-121). Works but unconventional; should be module-level. Moot if H1 is fixed.

### M3 — No `httpx.TimeoutException` handling

`client.py` sets a 30s timeout but tool handlers only catch `PancakeAPIError`. A network timeout raises `httpx.TimeoutException` which propagates uncaught through all tool handlers, resulting in an unformatted traceback returned to Claude.

Fix: add to each tool handler (or better, in `client._get/_post/_put`):
```python
except httpx.TimeoutException:
    raise PancakeAPIError(504, "Request timed out")
```
Or catch in tools:
```python
except (PancakeAPIError, httpx.TimeoutException) as e:
    return f"Error: {e}"
```

### M4 — `_handle` calls `resp.json()` even on success without try/except

```python
@staticmethod
def _handle(resp: httpx.Response) -> Any:
    if resp.status_code >= 400:
        ...
    return resp.json()   # can raise json.JSONDecodeError if API returns HTML/empty body
```

If Pancake API returns a 200 with empty body or HTML (e.g. maintenance page), this raises `json.JSONDecodeError` uncaught. Same fix as M3 — wrap or handle in caller.

### M5 — `server.py`: health endpoint has no version/timestamp

Minor but useful for ops: `/health` returns static JSON. Adding `version` from package metadata or a `timestamp` field makes it much more useful for uptime probes:

```python
import importlib.metadata
VERSION = importlib.metadata.version("pancake-mcp-server")

async def _health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "server": "pancake-pos-mcp", "version": VERSION})
```

---

## Low Priority

### L1 — `test_server.py` comment says "19 expected tools" but `expected` set has 20

```python
"""Verify all 19 expected tools are registered on the MCP instance."""
expected = {
    "get_shops", "get_payment_methods",
    "get_provinces", "get_districts", "get_communes",   # 5
    "search_orders", "get_order", "create_order", "update_order",
    "get_order_tags", "get_order_sources", "get_active_promotions",   # 7
    "list_warehouses", "create_warehouse", "update_warehouse", "get_inventory_history",  # 4
    "arrange_shipment", "get_tracking_url", "list_return_orders", "create_return_order",  # 4
}
```
Total = 20. Comment says 19. Fix the comment.

### L2 — `test_client.py` fixture `client` not cleaned up

The `client` pytest fixture creates a `PancakeClient` but never calls `__aenter__`/`__aexit__`. Tests that use `async with client` are fine (they close the httpx client). But if a test were to use `client` without `async with`, the underlying `httpx.AsyncClient` would leak. Fixture could use `yield` + cleanup, but given current tests all use `async with`, low risk.

### L3 — `page_size` doc inconsistency

`search_orders` says "max 50" in docstring; `get_inventory_history` and `list_return_orders` say nothing about max. Standardize.

### L4 — `country_code` not validated in `get_provinces`

Passes user string directly to API. No format check (e.g. 2-letter ISO). Low risk given it goes to a read-only endpoint.

---

## Edge Cases Found by Analysis

1. **Empty `items` JSON array in `create_order`**: `json.loads("[]")` succeeds and sends `items: []` to Pancake API. The API will likely reject it, but the error message returned will be the API's, not a friendly pre-validation message.

2. **Concurrent requests share no state** — good. Each tool call creates a fresh `PancakeClient`. No cross-request contamination risk.

3. **`PANCAKE_API_BASE_URL` env override** is read at module import time (line 12 of `client.py`). If changed after import, it won't take effect. Acceptable for production but can surprise during testing.

4. **Bearer token with extra whitespace**: `auth[7:].strip()` handles trailing spaces correctly. Good.

5. **`refund_amount: float`** in `create_return_order` — floating-point currency is generally a code smell; Pancake API may expect integer VND. Not fixable without API docs confirmation, but worth noting.

---

## Positive Observations

- Consistent `async with _client() as c:` pattern ensures `httpx.AsyncClient` is always closed.
- `_params()` cleanly handles `None`-filtering for all query params.
- Tool annotations (`readOnlyHint`, `destructiveHint`, etc.) are correctly set and differentiated.
- Tool docstrings are high quality — clear descriptions, typed args, cross-references to other tools (e.g. "get from get_shops").
- `server.py` instructions text is well-crafted for Claude's system prompt.
- Test for `None` param exclusion (`test_none_params_excluded`) catches a real behavioral requirement.
- No secrets or API keys hardcoded anywhere.
- `page_size=20` default is sensible; not too large.

---

## Recommended Actions (Priority Order)

1. **(H1)** Extract `_client()` + `_fmt()` into `tools/_common.py` — eliminates 3x duplication.
2. **(H3)** Add `page_size` upper-bound guard in `search_orders`, `get_inventory_history`, `list_return_orders`.
3. **(M3)** Catch `httpx.TimeoutException` — either in `client._handle` or in all tool handlers.
4. **(M4)** Wrap `resp.json()` on success path in try/except in `_handle`.
5. **(H2)** Narrow `except Exception` in `deps.py` to `RuntimeError` (or log it).
6. **(M1)** Add comment on `if val is not None` pattern to prevent well-meaning refactor bug.
7. **(L1)** Fix "19" → "20" in `test_server.py` docstring.

---

## Metrics

- Type coverage: ~90% (all public APIs typed; some `Any` used appropriately for JSON return values)
- Test coverage: ~65% (client happy-path + error path + param filtering; tools not directly tested)
- Linting issues: 1 (inline `import json` in `shop._fmt`)
- Security issues: 0 critical

---

## Unresolved Questions

1. Does Pancake API actually enforce `page_size` max? If not, should the server enforce it?
2. Does `refund_amount` expect integer (VND paise) or float? API docs needed.
3. Is there a rate-limit on Pancake API? If so, should the client implement retry with backoff?
4. Should `/health` be protected or is it intentionally public? (Relevant if deployed behind an authenticated reverse proxy.)
5. `test_all_tools_registered` counts 20 tools but `get_active_promotions` has `readOnlyHint: True` annotation — is this semantically correct for a POST that queries promotions? Yes it is — it's a read operation via POST. Confirmed OK.
