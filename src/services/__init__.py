"""
Services package for Bridge-MCP.

This package contains service modules for different integrations:
- jira_service: Jira integration tools
- gitlab_service: GitLab integration tools (coming soon)
- confluence_service: Confluence integration tools (coming soon)
"""

from .jira_service import (
    init_jira_client,
    get_jira_tools,
    handle_jira_tool_call,
)

__all__ = [
    "init_jira_client",
    "get_jira_tools",
    "handle_jira_tool_call",
]

