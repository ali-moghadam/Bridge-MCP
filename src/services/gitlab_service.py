"""
GitLab Service Module for Bridge-MCP.

Connects to a GitLab instance's native MCP endpoint at
``<GITLAB_URL>/api/v4/mcp`` over streamable HTTP and exposes whatever tools the
instance reports (dynamic passthrough). No external binary required.

Environment variables (read from .env via the main server):
  GITLAB_URL                    GitLab instance base URL (default: https://gitlab.com)
  GITLAB_PERSONAL_ACCESS_TOKEN  Personal access token, sent as a Bearer token
  GITLAB_VERIFY_SSL             Set to false/0/no to disable SSL verification (default: true)

The endpoint requires a recent GitLab (the MCP endpoint is exposed by GitLab
18.x and later). If the endpoint is unreachable or auth fails, the GitLab
service is disabled — Jira/Confluence are unaffected. There is no fallback.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Sequence

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import EmbeddedResource, ImageContent, TextContent, Tool

logger = logging.getLogger("bridge-mcp.gitlab")

# Populated by init_gitlab_client() from environment variables.
_endpoint: str | None = None      # e.g. "https://gitlab.com/api/v4/mcp"
_token: str | None = None         # value of GITLAB_PERSONAL_ACCESS_TOKEN
_verify_ssl: bool = True          # value of GITLAB_VERIFY_SSL

# Cache of the remote instance's tool set, fetched once at init.
_tools: list[Tool] = []
_tool_names: set[str] = set()


def _http_client_factory(
    headers: dict[str, str] | None = None,
    timeout: httpx.Timeout | None = None,
    auth: httpx.Auth | None = None,
) -> httpx.AsyncClient:
    """httpx client factory mirroring the MCP default but honoring _verify_ssl."""
    return httpx.AsyncClient(
        headers=headers,
        timeout=timeout if timeout is not None else httpx.Timeout(30.0),
        auth=auth,
        verify=_verify_ssl,
        follow_redirects=True,
    )


@asynccontextmanager
async def _session() -> AsyncIterator[ClientSession]:
    """Open an initialized MCP client session to the GitLab endpoint."""
    headers = {"Authorization": f"Bearer {_token}"} if _token else None
    async with streamablehttp_client(
        _endpoint,
        headers=headers,
        httpx_client_factory=_http_client_factory,
    ) as (read_stream, write_stream, _get_session_id):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            yield session


# ── Initialisation ────────────────────────────────────────────────────────────

async def init_gitlab_client() -> bool | None:
    """
    Read env vars, connect to the GitLab MCP endpoint, and cache its tool set.

    Returns True on success, or None if the service should be disabled
    (missing credentials, or the endpoint is unreachable/unauthorized).
    """
    global _endpoint, _token, _verify_ssl, _tools, _tool_names

    base_url = os.environ.get("GITLAB_URL", "https://gitlab.com").rstrip("/")
    _token = os.environ.get("GITLAB_PERSONAL_ACCESS_TOKEN") or None
    _verify_ssl = os.environ.get("GITLAB_VERIFY_SSL", "true").lower() not in (
        "false", "0", "no",
    )

    if not _token:
        logger.warning("GITLAB_PERSONAL_ACCESS_TOKEN not set. GitLab service disabled.")
        return None

    _endpoint = f"{base_url}/api/v4/mcp"

    try:
        async with _session() as session:
            result = await session.list_tools()
        _tools = list(result.tools)
        _tool_names = {t.name for t in _tools}
        logger.info(
            "GitLab MCP endpoint reachable at %s (%d tools).",
            _endpoint, len(_tools),
        )
        return True
    except Exception as exc:  # noqa: BLE001 - any failure means disable the service
        logger.warning(
            "GitLab MCP endpoint at %s unreachable (%s). GitLab service disabled.",
            _endpoint, exc,
        )
        _tools = []
        _tool_names = set()
        return None


# ── Tool registry ─────────────────────────────────────────────────────────────

def get_gitlab_tools() -> list[Tool]:
    """Return the tools reported by the GitLab instance (cached at init)."""
    return _tools


def gitlab_tool_names() -> set[str]:
    """Return the set of tool names the active GitLab endpoint exposes.

    The server uses this to route calls, because the names are determined
    dynamically by the instance and cannot be hardcoded.
    """
    return _tool_names


# ── Dispatch ──────────────────────────────────────────────────────────────────

async def handle_gitlab_tool_call(
    name: str,
    arguments: Any,
) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Forward a tool call to the GitLab MCP endpoint and return its content."""
    if name not in _tool_names:
        return [TextContent(type="text", text=f"Error: Unknown GitLab tool '{name}'.")]

    args = arguments if isinstance(arguments, dict) else {}
    try:
        async with _session() as session:
            result = await session.call_tool(name, args)
    except Exception as exc:  # noqa: BLE001
        return [TextContent(type="text", text=f"Error calling GitLab tool '{name}': {exc}")]

    if result.isError:
        text = _content_to_text(result.content) or "unknown error"
        return [TextContent(type="text", text=f"Error from GitLab tool '{name}': {text}")]

    # result.content is already a sequence of MCP content blocks.
    return list(result.content)


def _content_to_text(content: Sequence[Any]) -> str:
    """Flatten any text blocks in a content sequence into a single string."""
    parts = [getattr(b, "text", "") for b in content if getattr(b, "type", None) == "text"]
    return "\n".join(p for p in parts if p)