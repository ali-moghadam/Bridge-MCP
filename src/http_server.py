#!/usr/bin/env python3
"""
HTTP (streamable-HTTP) entrypoint for Bridge-MCP.

Serves the same MCP server defined in ``bridge_mcp_server.py`` over HTTP so it can
run as an always-on service and be reached by URL, instead of being launched as a
local stdio subprocess. The low-level ``Server`` object (``app``) and its tool
handlers are reused unchanged — this module only adds the transport, a Bearer-token
auth gate, and health endpoints.

Endpoints:
  POST/GET /mcp        MCP streamable-HTTP transport (requires Authorization header
                       when BRIDGE_MCP_AUTH_TOKEN is set)
  GET      /healthz    liveness/startup probe (no auth)
  GET      /readyz     readiness probe (no auth)

Environment:
  BRIDGE_MCP_AUTH_TOKEN  Shared secret. When set, /mcp requires
                         ``Authorization: Bearer <token>``. When unset, /mcp is open
                         (rely on network controls) and a warning is logged.
  PORT                   Listen port (default 8080).
  Plus the per-service credentials read by bridge_mcp_server (JIRA_*, GITLAB_*,
  CONFLUENCE_*), supplied here via the container environment rather than a .env file.
"""

import contextlib
import logging
import os
from collections.abc import AsyncIterator

import uvicorn
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send

from bridge_mcp_server import app, enabled_services, initialize_services

logger = logging.getLogger("bridge-mcp.http")

_AUTH_TOKEN = os.environ.get("BRIDGE_MCP_AUTH_TOKEN") or None

# DNS-rebinding protection is disabled because the server sits behind a trusted
# reverse proxy (OpenShift Route) that rewrites the Host header; access is gated by
# the Bearer token instead.
_session_manager = StreamableHTTPSessionManager(
    app=app,
    json_response=False,
    stateless=True,
    security_settings=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)


def _authorized(scope: Scope) -> bool:
    """True when the request carries the expected Bearer token (or auth is off)."""
    if _AUTH_TOKEN is None:
        return True
    headers = dict(scope.get("headers") or [])
    provided = headers.get(b"authorization", b"").decode()
    return provided == f"Bearer {_AUTH_TOKEN}"


async def handle_mcp(scope: Scope, receive: Receive, send: Send) -> None:
    """ASGI app for /mcp: enforce the token, then delegate to the session manager."""
    if not _authorized(scope):
        response = JSONResponse({"error": "unauthorized"}, status_code=401)
        await response(scope, receive, send)
        return
    await _session_manager.handle_request(scope, receive, send)


async def healthz(_request: Request) -> PlainTextResponse:
    return PlainTextResponse("ok")


async def readyz(_request: Request) -> JSONResponse:
    enabled = [name for name, on in enabled_services.items() if on]
    return JSONResponse({"status": "ready", "services": enabled})


@contextlib.asynccontextmanager
async def lifespan(_app: Starlette) -> AsyncIterator[None]:
    """Initialize services once, and keep the session manager running."""
    await initialize_services()
    if _AUTH_TOKEN is None:
        logger.warning(
            "BRIDGE_MCP_AUTH_TOKEN is not set — /mcp is unauthenticated. "
            "Set it to require a Bearer token."
        )
    async with _session_manager.run():
        logger.info("Bridge-MCP HTTP server ready on /mcp")
        yield


starlette_app = Starlette(
    routes=[
        Route("/healthz", healthz, methods=["GET"]),
        Route("/readyz", readyz, methods=["GET"]),
        Mount("/mcp", app=handle_mcp),
    ],
    lifespan=lifespan,
)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run(starlette_app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
