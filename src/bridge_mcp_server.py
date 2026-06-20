#!/usr/bin/env python3
"""
Bridge-MCP - A unified Model Context Protocol server for enterprise integrations.

This server provides tools to integrate with:
- Jira (issue tracking and project management)
- GitLab (source control and CI/CD) - Coming soon
- Confluence (documentation and knowledge base) - Coming soon

Each service is modular and can be enabled/disabled independently via environment variables.
"""

import os
import sys
import logging
from typing import Any, Sequence
from dotenv import load_dotenv

from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
from mcp.server.stdio import stdio_server

# Import service modules
from services.jira_service import (
    init_jira_client,
    get_jira_tools,
    handle_jira_tool_call,
)
from services.gitlab_service import (
    init_gitlab_client,
    get_gitlab_tools,
    handle_gitlab_tool_call,
)
from services.confluence_service import (
    init_confluence_client,
    get_confluence_tools,
    handle_confluence_tool_call,
)

# Load environment variables from the project-root .env by absolute path.
# MCP hosts (Claude, Copilot) launch this server from an arbitrary working
# directory, so a bare load_dotenv() (which searches cwd) would miss the file
# and the tokens would appear unset. Resolve relative to this file instead.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("bridge-mcp")

# Initialize MCP server
app = Server("bridge-mcp")

# Track which services are enabled
enabled_services: dict[str, bool] = {}


def initialize_services() -> None:
    """Initialize all available services."""
    global enabled_services

    logger.info("Initializing Bridge-MCP services...")

    # Initialize Jira
    jira_client = init_jira_client()
    enabled_services["jira"] = jira_client is not None
    if enabled_services["jira"]:
        logger.info("✓ Jira service enabled")
    else:
        logger.info("✗ Jira service disabled (credentials not found)")

    # Initialize GitLab
    gitlab_client = init_gitlab_client()
    enabled_services["gitlab"] = gitlab_client is not None
    if enabled_services["gitlab"]:
        logger.info("✓ GitLab service enabled")
    else:
        logger.info("✗ GitLab service disabled (not implemented or credentials not found)")

    # Initialize Confluence
    confluence_client = init_confluence_client()
    enabled_services["confluence"] = confluence_client is not None
    if enabled_services["confluence"]:
        logger.info("✓ Confluence service enabled")
    else:
        logger.info("✗ Confluence service disabled (not implemented or credentials not found)")

    # Log summary
    enabled_count = sum(enabled_services.values())
    logger.info(f"Bridge-MCP initialized with {enabled_count}/{len(enabled_services)} service(s) enabled")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools from all enabled services."""
    tools: list[Tool] = []

    # Add Jira tools if enabled
    if enabled_services.get("jira", False):
        tools.extend(get_jira_tools())

    # Add GitLab tools if enabled
    if enabled_services.get("gitlab", False):
        tools.extend(get_gitlab_tools())

    # Add Confluence tools if enabled
    if enabled_services.get("confluence", False):
        tools.extend(get_confluence_tools())

    return tools


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Route tool calls to the appropriate service handler."""

    # Jira tools
    jira_tools = {"get_jira_issue", "search_jira_issues", "get_issue_comments",
                  "get_issue_attachments", "get_issue_media"}
    if name in jira_tools:
        if not enabled_services.get("jira", False):
            return [TextContent(
                type="text",
                text="Error: Jira service is not enabled. Please check your JIRA_PERSONAL_ACCESS_TOKEN."
            )]
        return await handle_jira_tool_call(name, arguments)

    # GitLab tools
    gitlab_tools = {
        # Projects
        "get_gitlab_project", "list_gitlab_projects",
        # Merge Requests
        "get_merge_request", "list_merge_requests", "list_mr_notes", "create_mr_note",
        # Issues
        "get_gitlab_issue", "list_gitlab_issues", "create_gitlab_issue",
        "list_issue_notes", "create_issue_note",
        # Pipelines & CI
        "list_pipelines", "get_pipeline", "retry_pipeline", "cancel_pipeline",
        "list_pipeline_jobs", "get_job_log",
        # Repository
        "list_branches", "get_branch", "list_commits", "get_commit",
        "list_repository_tree", "get_file",
        # Releases & Tags
        "list_releases", "get_release", "list_tags",
        # Members & Labels
        "list_project_members", "list_labels",
    }
    if name in gitlab_tools:
        if not enabled_services.get("gitlab", False):
            return [TextContent(
                type="text",
                text="Error: GitLab service is not enabled. Run: glab auth login"
            )]
        return await handle_gitlab_tool_call(name, arguments)

    # Confluence tools (when implemented)
    confluence_tools = {"get_confluence_page", "search_confluence_pages", "get_space",
                       "list_spaces", "get_page_children", "get_page_attachments", "get_page_comments"}
    if name in confluence_tools:
        if not enabled_services.get("confluence", False):
            return [TextContent(
                type="text",
                text="Error: Confluence service is not enabled or not yet implemented."
            )]
        return await handle_confluence_tool_call(name, arguments)

    # Unknown tool
    return [TextContent(
        type="text",
        text=f"Error: Unknown tool '{name}'. Available services: {', '.join(k for k, v in enabled_services.items() if v)}"
    )]


async def main() -> None:
    """Main entry point for the Bridge-MCP server."""
    try:
        # Initialize all services
        initialize_services()

        # Check if at least one service is enabled
        if not any(enabled_services.values()):
            logger.error("No services are enabled. Please configure at least one service.")
            logger.error("Required environment variables:")
            logger.error("  Jira: JIRA_URL, JIRA_PERSONAL_ACCESS_TOKEN")
            logger.error("  GitLab: GITLAB_URL, GITLAB_PERSONAL_ACCESS_TOKEN")
            logger.error("  Confluence: CONFLUENCE_URL, CONFLUENCE_API_TOKEN, CONFLUENCE_USERNAME")
            sys.exit(1)

        # Run the server
        async with stdio_server() as (read_stream, write_stream):
            logger.info("Bridge-MCP Server starting...")
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

