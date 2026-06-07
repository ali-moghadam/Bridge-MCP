"""
Confluence Service Module for Bridge-MCP.

This module provides Confluence-specific functionality including:
- Confluence client initialization
- Tool definitions
- Tool handlers
"""

import os
import logging
from typing import Any, Sequence, Optional

try:
    from atlassian import Confluence
    CONFLUENCE_AVAILABLE = True
except ImportError:
    CONFLUENCE_AVAILABLE = False
    Confluence = None  # type: ignore
    logger_temp = logging.getLogger("bridge-mcp.confluence")
    logger_temp.warning("atlassian-python-api not installed. Run: pip install atlassian-python-api")

from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

logger = logging.getLogger("bridge-mcp.confluence")

# Module-level Confluence client
confluence_client: Optional[Any] = None


def init_confluence_client() -> Optional[Any]:
    """Initialize the Confluence client using PAT or username+token."""
    global confluence_client

    if not CONFLUENCE_AVAILABLE:
        logger.error("atlassian-python-api library not available")
        return None

    confluence_url = os.getenv("CONFLUENCE_URL")
    confluence_token = os.getenv("CONFLUENCE_API_TOKEN")
    confluence_username = os.getenv("CONFLUENCE_USERNAME")
    confluence_verify_ssl = os.getenv("CONFLUENCE_VERIFY_SSL", "true").strip().lower() in {"1", "true", "yes", "on"}

    if not confluence_url:
        logger.warning("CONFLUENCE_URL not found. Confluence features will be disabled.")
        return None

    if not confluence_token:
        logger.warning("CONFLUENCE_API_TOKEN not found. Confluence features will be disabled.")
        return None

    try:
        if confluence_username:
            # Cloud or basic auth: username + API token
            client = Confluence(
                url=confluence_url,
                username=confluence_username,
                password=confluence_token,
                verify_ssl=confluence_verify_ssl,
            )
        else:
            # Self-hosted with PAT (like Jira/GitLab)
            client = Confluence(
                url=confluence_url,
                token=confluence_token,
                verify_ssl=confluence_verify_ssl,
            )

        # Test connection
        spaces = client.get_all_spaces(start=0, limit=1)
        if spaces is None:
            raise Exception("Failed to retrieve spaces - check credentials")

        confluence_client = client
        auth_mode = "basic auth" if confluence_username else "PAT"
        logger.info(f"Successfully connected to Confluence at {confluence_url} with {auth_mode} (verify_ssl={confluence_verify_ssl})")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to Confluence: {e}")
        return None


def get_confluence_tools() -> list[Tool]:
    """Return the list of Confluence tools available."""
    return [
        Tool(
            name="get_confluence_page",
            description="Get a Confluence page by its ID. Returns the page title, body content, metadata, and labels.",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "The numeric page ID",
                    },
                    "expand": {
                        "type": "string",
                        "description": "Comma-separated fields to expand (default: body.storage,version,space,ancestors)",
                        "default": "body.storage,version,space,ancestors",
                    },
                },
                "required": ["page_id"],
            },
        ),
        Tool(
            name="search_confluence_pages",
            description="Search Confluence pages using CQL (Confluence Query Language). Examples: 'text ~ \"search term\"', 'space = DEV AND type = page', 'label = architecture'",
            inputSchema={
                "type": "object",
                "properties": {
                    "cql": {
                        "type": "string",
                        "description": "CQL query string (e.g., 'space = DEV AND text ~ \"API docs\"')",
                    },
                    "max_results": {
                        "type": "number",
                        "description": "Maximum number of results to return (default: 25)",
                        "default": 25,
                    },
                },
                "required": ["cql"],
            },
        ),
        Tool(
            name="get_space",
            description="Get details about a Confluence space by its key",
            inputSchema={
                "type": "object",
                "properties": {
                    "space_key": {
                        "type": "string",
                        "description": "The space key (e.g., 'DEV', 'TEAM')",
                    },
                },
                "required": ["space_key"],
            },
        ),
        Tool(
            name="list_spaces",
            description="List all available Confluence spaces",
            inputSchema={
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "number",
                        "description": "Maximum number of spaces to return (default: 50)",
                        "default": 50,
                    },
                    "space_type": {
                        "type": "string",
                        "description": "Filter by space type: 'global' or 'personal'",
                        "enum": ["global", "personal"],
                    },
                },
            },
        ),
        Tool(
            name="get_page_children",
            description="Get child pages of a specific Confluence page",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "The parent page ID",
                    },
                    "max_results": {
                        "type": "number",
                        "description": "Maximum number of children to return (default: 25)",
                        "default": 25,
                    },
                },
                "required": ["page_id"],
            },
        ),
        Tool(
            name="get_page_attachments",
            description="Get attachments of a specific Confluence page",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "The page ID",
                    },
                },
                "required": ["page_id"],
            },
        ),
        Tool(
            name="get_page_comments",
            description="Get comments on a specific Confluence page",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "The page ID",
                    },
                },
                "required": ["page_id"],
            },
        ),
    ]


async def handle_confluence_tool_call(
    name: str,
    arguments: Any
) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls for Confluence operations."""

    if confluence_client is None:
        return [TextContent(
            type="text",
            text="Error: Confluence client not initialized. Please check your credentials."
        )]

    try:
        if name == "get_confluence_page":
            page_id = arguments.get("page_id")
            if not page_id:
                return [TextContent(type="text", text="Error: page_id is required")]

            expand = arguments.get("expand", "body.storage,version,space,ancestors")
            page = confluence_client.get_page_by_id(page_id, expand=expand)

            if not page:
                return [TextContent(type="text", text=f"Page {page_id} not found")]

            title = page.get("title", "Untitled")
            space_key = page.get("space", {}).get("key", "N/A")
            space_name = page.get("space", {}).get("name", "N/A")
            version = page.get("version", {}).get("number", "N/A")
            version_by = page.get("version", {}).get("by", {}).get("displayName", "N/A")
            version_when = page.get("version", {}).get("when", "N/A")

            body = page.get("body", {}).get("storage", {}).get("value", "No content")

            # Build ancestor path
            ancestors = page.get("ancestors", [])
            ancestor_path = " > ".join(a.get("title", "?") for a in ancestors)

            base_url = os.getenv("CONFLUENCE_URL", "").rstrip("/")
            page_link = page.get("_links", {}).get("webui", "")
            url = f"{base_url}{page_link}" if page_link else "N/A"

            # Get labels
            labels = confluence_client.get_page_labels(page_id)
            label_names = [l.get("name", "") for l in labels.get("results", [])] if isinstance(labels, dict) else []

            result = f"""# {title}

**Space:** {space_name} ({space_key})
**Page ID:** {page_id}
**URL:** {url}
**Version:** {version} (by {version_by}, {version_when})
"""
            if ancestor_path:
                result += f"**Path:** {ancestor_path} > {title}\n"
            if label_names:
                result += f"**Labels:** {', '.join(label_names)}\n"

            result += f"\n## Content\n\n{body}\n"

            return [TextContent(type="text", text=result)]

        elif name == "search_confluence_pages":
            cql = arguments.get("cql")
            if not cql:
                return [TextContent(type="text", text="Error: cql query is required")]

            max_results = int(arguments.get("max_results", 25))
            search_results = confluence_client.cql(cql, limit=max_results)

            results_list = search_results.get("results", [])
            if not results_list:
                return [TextContent(type="text", text=f"No pages found for query: {cql}")]

            total_size = search_results.get("totalSize", len(results_list))
            base_url = os.getenv("CONFLUENCE_URL", "").rstrip("/")

            result = f"# Search Results ({len(results_list)} of {total_size})\n\n"
            result += f"**Query:** {cql}\n\n"

            for item in results_list:
                content = item.get("content", item)
                title = item.get("title", content.get("title", "Untitled"))
                content_id = content.get("id", "N/A")
                content_type = content.get("type", "N/A")
                space = content.get("space", {})
                space_key = space.get("key", "N/A") if space else "N/A"
                web_link = item.get("url", content.get("_links", {}).get("webui", ""))
                url = f"{base_url}{web_link}" if web_link and not web_link.startswith("http") else web_link

                result += f"## {title}\n"
                result += f"- **ID:** {content_id}\n"
                result += f"- **Type:** {content_type}\n"
                result += f"- **Space:** {space_key}\n"
                if url:
                    result += f"- **URL:** {url}\n"
                result += "\n"

            return [TextContent(type="text", text=result)]

        elif name == "get_space":
            space_key = arguments.get("space_key")
            if not space_key:
                return [TextContent(type="text", text="Error: space_key is required")]

            space = confluence_client.get_space(space_key, expand="description.plain,homepage")

            if not space:
                return [TextContent(type="text", text=f"Space '{space_key}' not found")]

            name_val = space.get("name", "N/A")
            key = space.get("key", "N/A")
            space_type = space.get("type", "N/A")
            description = space.get("description", {}).get("plain", {}).get("value", "No description")
            homepage = space.get("homepage", {})
            homepage_title = homepage.get("title", "N/A") if homepage else "N/A"
            homepage_id = homepage.get("id", "N/A") if homepage else "N/A"

            base_url = os.getenv("CONFLUENCE_URL", "").rstrip("/")
            space_link = space.get("_links", {}).get("webui", "")
            url = f"{base_url}{space_link}" if space_link else "N/A"

            result = f"""# Space: {name_val}

**Key:** {key}
**Type:** {space_type}
**URL:** {url}
**Homepage:** {homepage_title} (ID: {homepage_id})

## Description
{description}
"""
            return [TextContent(type="text", text=result)]

        elif name == "list_spaces":
            max_results = int(arguments.get("max_results", 50))
            space_type = arguments.get("space_type")

            kwargs: dict[str, Any] = {"start": 0, "limit": max_results}
            if space_type:
                kwargs["space_type"] = space_type

            spaces_response = confluence_client.get_all_spaces(**kwargs)
            spaces = spaces_response.get("results", []) if isinstance(spaces_response, dict) else []

            if not spaces:
                return [TextContent(type="text", text="No spaces found")]

            result = f"# Confluence Spaces ({len(spaces)} spaces)\n\n"
            if space_type:
                result += f"**Type filter:** {space_type}\n\n"

            for space in spaces:
                s_name = space.get("name", "N/A")
                s_key = space.get("key", "N/A")
                s_type = space.get("type", "N/A")
                result += f"- **{s_name}** ({s_key}) — {s_type}\n"

            return [TextContent(type="text", text=result)]

        elif name == "get_page_children":
            page_id = arguments.get("page_id")
            if not page_id:
                return [TextContent(type="text", text="Error: page_id is required")]

            max_results = int(arguments.get("max_results", 25))
            children = confluence_client.get_page_child_by_type(
                page_id, type="page", start=0, limit=max_results,
                expand="version"
            )

            if not children:
                return [TextContent(type="text", text=f"No child pages found for page {page_id}")]

            result = f"# Child Pages of {page_id} ({len(children)} pages)\n\n"
            for child in children:
                c_title = child.get("title", "Untitled")
                c_id = child.get("id", "N/A")
                c_version = child.get("version", {}).get("number", "N/A")
                result += f"- **{c_title}** (ID: {c_id}, v{c_version})\n"

            return [TextContent(type="text", text=result)]

        elif name == "get_page_attachments":
            page_id = arguments.get("page_id")
            if not page_id:
                return [TextContent(type="text", text="Error: page_id is required")]

            attachments_response = confluence_client.get_attachments_from_content(page_id)
            attachments = attachments_response.get("results", []) if isinstance(attachments_response, dict) else []

            if not attachments:
                return [TextContent(type="text", text=f"No attachments found for page {page_id}")]

            result = f"# Attachments for Page {page_id} ({len(attachments)} files)\n\n"
            base_url = os.getenv("CONFLUENCE_URL", "").rstrip("/")

            for att in attachments:
                title = att.get("title", "N/A")
                media_type = att.get("metadata", {}).get("mediaType", "N/A")
                file_size = att.get("extensions", {}).get("fileSize", "N/A")
                download_link = att.get("_links", {}).get("download", "")
                url = f"{base_url}{download_link}" if download_link else "N/A"

                result += f"## {title}\n"
                result += f"- **Type:** {media_type}\n"
                result += f"- **Size:** {file_size} bytes\n"
                result += f"- **Download:** {url}\n\n"

            return [TextContent(type="text", text=result)]

        elif name == "get_page_comments":
            page_id = arguments.get("page_id")
            if not page_id:
                return [TextContent(type="text", text="Error: page_id is required")]

            comments = confluence_client.get_page_comments(
                page_id, expand="body.storage,version", depth="all"
            )
            comment_list = comments.get("results", []) if isinstance(comments, dict) else []

            if not comment_list:
                return [TextContent(type="text", text=f"No comments found for page {page_id}")]

            result = f"# Comments for Page {page_id} ({len(comment_list)} comments)\n\n"

            for i, comment in enumerate(comment_list, 1):
                author = comment.get("version", {}).get("by", {}).get("displayName", "Unknown")
                created = comment.get("version", {}).get("when", "N/A")
                body = comment.get("body", {}).get("storage", {}).get("value", "No content")

                result += f"## Comment {i}\n"
                result += f"**Author:** {author}\n"
                result += f"**Date:** {created}\n\n"
                result += f"{body}\n\n"
                result += "---\n\n"

            return [TextContent(type="text", text=result)]

        else:
            return [TextContent(type="text", text=f"Unknown Confluence tool: {name}")]

    except Exception as e:
        logger.error(f"Error in Confluence tool {name}: {e}")
        return [TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]
