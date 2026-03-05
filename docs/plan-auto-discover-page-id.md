# Plan: Auto-discover page_id from Pancake API

## Problem

Users must manually find their `page_id` by calling the Pancake `/pages` API endpoint outside the MCP server, then pass it to every conversation/attachment tool call. This is a pain point because:

- The `page_id` (e.g. `pzl_860959775789157676`) is an internal ID, different from the `username` shown in URLs (e.g. `pzl_84333103788`)
- There's no tool in the MCP server to discover it
- Users have to use browser DevTools or curl to find it

## Solution

Since the `access_token` already grants access to the `/pages` API endpoint, the MCP server can auto-discover and cache page IDs at runtime.

## Changes

### 1. Add `list_pages()` to Chat API client

**File:** `src/pancake_mcp/chat_client.py`

Add a new method to the `PancakeChatClient` class:

```python
async def list_pages(self) -> Any:
    """List all pages linked to the current account."""
    return await self._get("/pages")
```

### 2. Add page_id resolver helpers

**File:** `src/pancake_mcp/deps.py`

Add a cached helper that calls `/pages` once per session and stores the result:

- `_cached_page_ids: list[dict]` — module-level cache storing `[{id, name, platform}, ...]`
- `async def resolve_page_ids() -> list[dict]` — fetches from API on first call, returns cache on subsequent calls
- `async def get_default_page_id() -> str | None` — if exactly 1 activated page exists, return its `id`; otherwise return `None`

### 3. Add `list_pages` MCP tool

**File:** `src/pancake_mcp/tools/conversations.py`

New tool for Claude to discover available pages:

```
list_pages() -> JSON with activated pages (id, name, platform, username)
```

This replaces the need to call `get_shops` just to find page IDs.

### 4. Add shared page_id resolution helper

**File:** `src/pancake_mcp/tools/common.py`

Add a helper function that tools can call:

```python
async def resolve_page_id(page_id: str | None) -> str:
    """If page_id is provided, return it. Otherwise auto-resolve from API."""
```

If auto-resolve fails (e.g. multiple pages), it returns an error message listing available pages so the user knows what to pass.

### 5. Make `page_id` optional in all conversation & attachment tools

**Files:**
- `src/pancake_mcp/tools/conversations.py` — 5 tools
- `src/pancake_mcp/tools/attachments.py` — 6 tools

For each tool:
- Change `page_id: str` → `page_id: str | None = None`
- At the top of each function, call `resolve_page_id(page_id)`
- If resolution fails (multiple pages, no pages), return a helpful error with the list of available pages

**Result:** Users with a single connected page never need to provide `page_id` at all.

## Files summary

| File | Change |
|------|--------|
| `src/pancake_mcp/chat_client.py` | Add `list_pages()` method |
| `src/pancake_mcp/deps.py` | Add `resolve_page_ids()` + `get_default_page_id()` |
| `src/pancake_mcp/tools/common.py` | Add `resolve_page_id()` shared helper |
| `src/pancake_mcp/tools/conversations.py` | Add `list_pages` tool, make `page_id` optional in 5 tools |
| `src/pancake_mcp/tools/attachments.py` | Make `page_id` optional in 6 tools |

## Verification

1. Run existing tests: `python3 -m pytest tests/ -v`
2. Test with real token: call `list_pages` tool, confirm it returns page data
3. Call `list_conversations` **without** `page_id` and confirm it auto-resolves
4. Test with multiple pages scenario: confirm it returns error listing available pages
