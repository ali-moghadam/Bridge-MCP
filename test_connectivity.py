#!/usr/bin/env python3
"""
Connectivity test for Bridge-MCP services.

Loads your project-root `.env` (same file the server uses) and verifies that
each service — Jira, GitLab, Confluence — can actually be reached and
authenticated with YOUR tokens.

Run it directly:

    python test_connectivity.py

Or under pytest:

    pytest test_connectivity.py -v

Note on tokens: the MCP server reads credentials from the project-root `.env`.
When your AI assistant (Claude, Copilot, ...) launches the server, it may run
from a different working directory, so make sure your `.env` lives next to this
file. If you prefer not to use `.env`, pass the same variables via the `env`
block of your MCP client config instead.
"""

import os
import sys

from dotenv import load_dotenv

# Load the same .env the server loads (project root = this file's directory).
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))

sys.path.insert(0, os.path.join(_PROJECT_ROOT, "src"))

from services.jira_service import init_jira_client
from services.gitlab_service import init_gitlab_client
from services.confluence_service import init_confluence_client


def _reachable(init_fn) -> bool:
    """A service is reachable when its init returns a truthy client/flag."""
    try:
        return bool(init_fn())
    except Exception as e:  # network/auth errors surface as not-reachable
        print(f"    error: {e}")
        return False


# ── pytest entry points ────────────────────────────────────────────────────────

def test_jira_reachable():
    assert _reachable(init_jira_client), "Jira not reachable — check JIRA_URL / JIRA_PERSONAL_ACCESS_TOKEN"


def test_gitlab_reachable():
    assert _reachable(init_gitlab_client), "GitLab not reachable — check GITLAB_BACKEND / GITLAB_URL / GITLAB_PERSONAL_ACCESS_TOKEN"


def test_confluence_reachable():
    assert _reachable(init_confluence_client), "Confluence not reachable — check CONFLUENCE_URL / CONFLUENCE_API_TOKEN / CONFLUENCE_USERNAME"


# ── standalone runner ──────────────────────────────────────────────────────────

def main() -> int:
    checks = [
        ("Jira", init_jira_client),
        ("GitLab", init_gitlab_client),
        ("Confluence", init_confluence_client),
    ]
    print(f"\n{'='*60}\n  Bridge-MCP connectivity check\n{'='*60}")
    results = {}
    for name, fn in checks:
        print(f"\n[{name}]")
        ok = _reachable(fn)
        results[name] = ok
        print(f"  {'✓ reachable' if ok else '✗ NOT reachable'}")

    passed = sum(results.values())
    print(f"\n{'='*60}\n  {passed}/{len(results)} service(s) reachable\n{'='*60}\n")
    # Exit non-zero only if every service failed (likely a config/.env problem).
    return 0 if passed > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
