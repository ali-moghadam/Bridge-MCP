# GitLab Service: Dual Backend (MCP + glab)

**Date:** 2026-06-20
**Status:** Approved

## Goal

Let the GitLab service run on either of two backends:

- **`mcp`** (default) — proxy to GitLab's native MCP endpoint on the (possibly self-hosted) instance.
- **`glab`** — the existing glab CLI implementation.

The user picks the backend via env var. No automatic fallback between them.

## Backend Selection

New env var:

```
GITLAB_BACKEND=mcp   # mcp (default) | glab
```

Read in `init_gitlab_client()`. Unknown/empty value → treat as `mcp`. The selected
backend is initialized; if its init fails, the GitLab service is disabled with a clear
log message. The other backend is **not** tried (no auto-fallback).

Existing env vars are reused:

- `GITLAB_URL` — instance base URL (default `https://gitlab.com`).
- `GITLAB_PERSONAL_ACCESS_TOKEN` — PAT.
- `GITLAB_VERIFY_SSL` — `true`/`false` (default true).

## Module Layout

Split the current single file into a facade plus two backend modules:

```
src/services/
  gitlab_service.py   # facade: backend selection + public interface
  gitlab_glab.py      # current glab CLI code, moved verbatim
  gitlab_mcp.py       # new: GitLab native MCP client (passthrough)
```

### Public interface (unchanged signatures, owned by facade)

```python
init_gitlab_client() -> bool | None
get_gitlab_tools() -> list[Tool]
gitlab_tool_names() -> set[str]          # NEW — for server routing
async handle_gitlab_tool_call(name, arguments) -> Sequence[...]
```

The facade holds a module-level `_backend` reference (the active backend module or a
small object exposing the same four functions) selected during init, and delegates to it.

`get_gitlab_tools()` and `gitlab_tool_names()` return values cached at init time (sync).

## glab Backend (`gitlab_glab.py`)

The current `gitlab_service.py` contents moved verbatim: static `get_gitlab_tools()`,
`_api()` over `glab api`, full `_dispatch()`. `gitlab_tool_names()` returns the static
set of the ~30 tool names. Behavior identical to today.

## MCP Backend (`gitlab_mcp.py`)

### Endpoint

`<GITLAB_URL>/api/v4/mcp` (strip trailing slash on `GITLAB_URL` before joining),
streamable HTTP transport.

- Auth header: `Authorization: Bearer <GITLAB_PERSONAL_ACCESS_TOKEN>`.
- SSL verification controlled by `GITLAB_VERIFY_SSL`.

### Init

1. Import the MCP client (`mcp.ClientSession`, `mcp.client.streamable_http.streamablehttp_client`).
   Import error → log, return `None` (service disabled).
2. Open the streamable-http connection + `ClientSession`, call `initialize()`.
3. Call `list_tools()`; cache the returned `Tool` list and the set of their names.
4. Any failure (unreachable, auth rejected, no tools) → log clear message, return `None`.

### Tool exposure — dynamic passthrough

- `get_gitlab_tools()` returns the upstream `Tool` list as-is (names + schemas from GitLab).
- `gitlab_tool_names()` returns the cached upstream name set.
- `handle_gitlab_tool_call(name, arguments)` forwards `session.call_tool(name, arguments)`
  verbatim and returns the resulting content blocks unchanged.

### Session lifetime

The `ClientSession` is long-lived (held open for the server's lifetime), because
`list_tools()` at init and `call_tool()` at request time must share one initialized
session. The streamable-http session must run on the **same asyncio loop** that
`stdio_server`/`app.run()` uses.

- Init happens synchronously from `initialize_services()` (which runs before the loop in
  `main()`); the session must therefore be established on the server's event loop.
  Implementation approach: make backend init async and `await` it from an async portion of
  startup, OR establish the session lazily on first use within the running loop and perform
  `list_tools()` there. **Decision:** establish the session during `main()` on the running
  loop, before `app.run()`, and pass the cached tool list/names to the facade. This keeps
  init failures fatal-but-clean and the session on the correct loop.
- On a dropped connection during a `call_tool`, attempt one reconnect + retry; if it still
  fails, return an error content block (do not crash the server).

> Note: this is the one place the existing sync `initialize_services()` flow is adjusted.
> The glab backend remains fully sync; only the mcp backend needs loop-aware setup.

## Server Routing Change (`bridge_mcp_server.py`)

The hardcoded `gitlab_tools` name set (current lines ~133–151) cannot work with dynamic
passthrough names. Replace it:

```python
if name in gitlab_tool_names():
    if not enabled_services.get("gitlab", False):
        return [TextContent(type="text", text="Error: GitLab service is not enabled.")]
    return await handle_gitlab_tool_call(name, arguments)
```

`gitlab_tool_names()` is imported from `services.gitlab_service` and returns the cached set
for whichever backend is active.

## Config / Docs

- `.env.example`: add `GITLAB_BACKEND=mcp` with a comment listing `mcp|glab`.
- `src/services/README.md` and top-level `README.md`: document the two backends and the
  new env var.

## Error Handling

- Backend init failure → service disabled, single clear log line naming the backend and reason.
- mcp `call_tool` transport failure → one reconnect/retry, then error content block.
- Unknown tool name → unchanged (server's existing "Unknown tool" path).

## Testing

- **Backend selection:** `GITLAB_BACKEND=glab` → glab module active; `mcp`/unset → mcp module
  active.
- **mcp init failure:** unreachable endpoint / import error → `init` returns None, service
  disabled, no crash.
- **Passthrough:** `handle_gitlab_tool_call` forwards name + arguments unchanged and returns
  upstream content blocks unchanged (mock `ClientSession`).
- **Routing:** `gitlab_tool_names()` membership drives dispatch for both backends.
- **glab regression:** existing glab dispatch behavior unchanged.

## Out of Scope (YAGNI)

- Auto-fallback between backends.
- Mapping upstream MCP tools onto the fixed ~30 tool names.
- Caching/transforming upstream tool output.
