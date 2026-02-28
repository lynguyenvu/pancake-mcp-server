# Code Reviewer Agent Memory

## Project: pancake-mcp-server

### Architecture
- Remote MCP server (FastMCP + Starlette) proxying Pancake POS API
- Auth: Bearer token pass-through as `api_key` query param
- Transport: Streamable HTTP at `/mcp`, health at `/health`
- Tools split into 4 modules: shop, orders, inventory, shipping

### Confirmed Patterns
- Each tool handler uses `async with _client() as c:` to ensure httpx cleanup
- `_params()` strips None values from query strings — intentional, test covers it
- `if val is not None:` (not `if val:`) pattern for payload building — preserves False/0/"" — needs comment to prevent accidental refactor
- Tool annotations (`readOnlyHint`, `destructiveHint`, `idempotentHint`) correctly differentiated per operation type

### Recurring Issues Found
- `_client()` + `_fmt()` defined 3-4 times across tool modules — extract to `tools/_common.py`
- `except Exception: pass` in deps.py masks unexpected errors — narrow to `RuntimeError`
- `httpx.TimeoutException` not caught in tools or client — propagates as raw traceback to Claude
- `resp.json()` on success path in `_handle` not wrapped — can raise `JSONDecodeError` on HTML/empty body
- `page_size` has no upper-bound enforcement despite docstring claiming "max 50"

### Test Coverage Gaps
- Tool handlers not directly tested (only client layer tested)
- Fixture `client` not cleaned up in test_client.py — low risk since all tests use `async with`

### Score Reference
- 2026-02-28 review: 8.0/10 — no critical issues, good patterns, DRY + error handling gaps
