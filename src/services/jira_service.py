"""
Jira Service Module for Bridge-MCP.

This module provides all Jira-specific functionality including:
- Jira client initialization
- Tool definitions
- Tool handlers
"""

import os
import logging
import base64
import requests
from typing import Any, Sequence, Optional, cast

from jira import JIRA
from jira.exceptions import JIRAError

from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

logger = logging.getLogger("bridge-mcp.jira")

# Jira configuration from environment (PAT-only auth)
JIRA_URL = os.getenv("JIRA_URL")
JIRA_PERSONAL_ACCESS_TOKEN = os.getenv("JIRA_PERSONAL_ACCESS_TOKEN")
JIRA_VERIFY_SSL = os.getenv("JIRA_VERIFY_SSL", "true").strip().lower() in {"1", "true", "yes", "on"}

# Module-level Jira client
jira_client: Optional[JIRA] = None


def init_jira_client() -> Optional[JIRA]:
    """Initialize the Jira client using Personal Access Token (PAT)."""
    global jira_client

    if not JIRA_PERSONAL_ACCESS_TOKEN:
        logger.warning("Jira Personal Access Token not found in environment variables. Jira features will be disabled.")
        return None

    try:
        client = JIRA(
            server=JIRA_URL,
            token_auth=JIRA_PERSONAL_ACCESS_TOKEN,
            options={'verify': JIRA_VERIFY_SSL}
        )
        # Simple call to ensure auth is valid
        _ = client.server_info()
        jira_client = client
        logger.info(f"Successfully connected to Jira at {JIRA_URL} with PAT auth (verify_ssl={JIRA_VERIFY_SSL})")
        return client
    except JIRAError as e:
        logger.error(f"Failed to connect to Jira: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error connecting to Jira: {e}")
        return None


def format_issue_details(issue) -> dict[str, Any]:
    """Format Jira issue details into a structured dictionary."""
    try:
        fields = issue.fields

        # Basic issue information
        issue_data = {
            "key": issue.key,
            "id": issue.id,
            "url": f"{JIRA_URL}/browse/{issue.key}",
            "summary": fields.summary,
            "description": fields.description or "No description",
            "status": fields.status.name,
            "priority": fields.priority.name if fields.priority else "None",
            "type": fields.issuetype.name,
            "created": fields.created,
            "updated": fields.updated,
        }

        # Reporter and Assignee
        if fields.reporter:
            issue_data["reporter"] = {
                "name": fields.reporter.displayName,
                "email": getattr(fields.reporter, 'emailAddress', 'N/A')
            }

        if fields.assignee:
            issue_data["assignee"] = {
                "name": fields.assignee.displayName,
                "email": getattr(fields.assignee, 'emailAddress', 'N/A')
            }

        # Project information
        if fields.project:
            issue_data["project"] = {
                "key": fields.project.key,
                "name": fields.project.name
            }

        # Components
        if fields.components:
            issue_data["components"] = [comp.name for comp in fields.components]

        # Labels
        if fields.labels:
            issue_data["labels"] = fields.labels

        # Fix versions
        if fields.fixVersions:
            issue_data["fix_versions"] = [v.name for v in fields.fixVersions]

        # Resolution
        if fields.resolution:
            issue_data["resolution"] = fields.resolution.name

        # Custom fields that might be useful
        if hasattr(fields, 'duedate') and fields.duedate:
            issue_data["due_date"] = fields.duedate

        return issue_data
    except Exception as e:
        logger.error(f"Error formatting issue details: {e}")
        return {"error": str(e)}


def get_issue_comments(issue_key: str) -> list[dict[str, Any]]:
    """Get all comments for a specific issue."""
    if jira_client is None:
        logger.error("Jira client not initialized")
        return []
    client = cast(JIRA, jira_client)
    try:
        issue = client.issue(issue_key, expand='comments')
        comments: list[dict[str, Any]] = []
        for comment in issue.fields.comment.comments:
            comments.append({
                "id": comment.id,
                "author": comment.author.displayName,
                "body": comment.body,
                "created": comment.created,
                "updated": comment.updated
            })
        return comments
    except JIRAError as e:
        logger.error(f"Error getting comments for {issue_key}: {e}")
        return []


def get_issue_attachments(issue_key: str) -> list[dict[str, Any]]:
    """Get all attachments for a specific issue."""
    if jira_client is None:
        logger.error("Jira client not initialized")
        return []
    client = cast(JIRA, jira_client)
    try:
        issue = client.issue(issue_key, fields='attachment')
        attachments: list[dict[str, Any]] = []
        for attachment in issue.fields.attachment:
            attachments.append({
                "id": attachment.id,
                "filename": attachment.filename,
                "size": attachment.size,
                "mime_type": attachment.mimeType,
                "created": attachment.created,
                "author": attachment.author.displayName,
                "url": attachment.content
            })
        return attachments
    except JIRAError as e:
        logger.error(f"Error getting attachments for {issue_key}: {e}")
        return []


def download_attachment(attachment_url: str) -> Optional[bytes]:
    """Download attachment content from Jira."""
    if not JIRA_PERSONAL_ACCESS_TOKEN:
        logger.error("Cannot download attachment: No PAT token available")
        return None

    try:
        headers = {
            "Authorization": f"Bearer {JIRA_PERSONAL_ACCESS_TOKEN}"
        }
        response = requests.get(
            attachment_url,
            headers=headers,
            verify=JIRA_VERIFY_SSL,
            timeout=30
        )
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        logger.error(f"Error downloading attachment: {e}")
        return None


def get_attachment_media_type(mime_type: str) -> Optional[str]:
    """Map MIME type to MCP media type for images."""
    mime_to_media = {
        "image/png": "image/png",
        "image/jpeg": "image/jpeg",
        "image/jpg": "image/jpeg",
        "image/gif": "image/gif",
        "image/webp": "image/webp",
        "image/svg+xml": "image/svg+xml",
    }
    return mime_to_media.get(mime_type.lower())


def is_supported_media(mime_type: str) -> bool:
    """Check if the attachment is a supported image or video type."""
    supported_types = [
        "image/png", "image/jpeg", "image/jpg", "image/gif",
        "image/webp", "image/svg+xml",
        "video/mp4", "video/quicktime", "video/x-msvideo", "video/webm"
    ]
    return mime_type.lower() in supported_types


def get_jira_tools() -> list[Tool]:
    """Return the list of Jira tools available."""
    return [
        Tool(
            name="get_jira_issue",
            description="Get detailed information about a specific Jira issue by its key (e.g., BAL-7437)",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "The Jira issue key (e.g., BAL-7437, PROJ-123)",
                    }
                },
                "required": ["issue_key"],
            },
        ),
        Tool(
            name="search_jira_issues",
            description="Search for Jira issues using JQL (Jira Query Language)",
            inputSchema={
                "type": "object",
                "properties": {
                    "jql": {
                        "type": "string",
                        "description": "JQL query string (e.g., 'project = BAL AND status = Open')",
                    },
                    "max_results": {
                        "type": "number",
                        "description": "Maximum number of results to return (default: 50)",
                        "default": 50,
                    }
                },
                "required": ["jql"],
            },
        ),
        Tool(
            name="get_issue_comments",
            description="Get all comments for a specific Jira issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "The Jira issue key (e.g., BAL-7437)",
                    }
                },
                "required": ["issue_key"],
            },
        ),
        Tool(
            name="get_issue_attachments",
            description="Get all attachments for a specific Jira issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "The Jira issue key (e.g., BAL-7437)",
                    }
                },
                "required": ["issue_key"],
            },
        ),
        Tool(
            name="get_issue_media",
            description="Download and display images and videos attached to a Jira issue. Returns actual image content that can be displayed inline.",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "The Jira issue key (e.g., BAL-7437)",
                    },
                    "max_files": {
                        "type": "number",
                        "description": "Maximum number of media files to return (default: 10)",
                        "default": 10,
                    }
                },
                "required": ["issue_key"],
            },
        ),
    ]


async def handle_jira_tool_call(
    name: str,
    arguments: Any
) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls for Jira operations."""

    if jira_client is None:
        return [TextContent(
            type="text",
            text="Error: Jira client not initialized. Please check your JIRA_PERSONAL_ACCESS_TOKEN."
        )]

    client = cast(JIRA, jira_client)

    try:
        if name == "get_jira_issue":
            issue_key = arguments.get("issue_key")
            if not issue_key:
                return [TextContent(type="text", text="Error: issue_key is required")]
            try:
                issue = client.issue(issue_key)
                issue_data = format_issue_details(issue)

                result = f"""# {issue_data['key']}: {issue_data['summary']}

**Status:** {issue_data['status']}
**Priority:** {issue_data['priority']}
**Type:** {issue_data['type']}

**URL:** {issue_data['url']}

## Description
{issue_data['description']}

## Details
- **Created:** {issue_data['created']}
- **Updated:** {issue_data['updated']}
- **Reporter:** {issue_data.get('reporter', {}).get('name', 'N/A')}
- **Assignee:** {issue_data.get('assignee', {}).get('name', 'Unassigned')}
- **Project:** {issue_data.get('project', {}).get('name', 'N/A')} ({issue_data.get('project', {}).get('key', 'N/A')})
"""

                if issue_data.get('components'):
                    result += f"\n**Components:** {', '.join(issue_data['components'])}"

                if issue_data.get('labels'):
                    result += f"\n**Labels:** {', '.join(issue_data['labels'])}"

                if issue_data.get('fix_versions'):
                    result += f"\n**Fix Versions:** {', '.join(issue_data['fix_versions'])}"

                if issue_data.get('resolution'):
                    result += f"\n**Resolution:** {issue_data['resolution']}"

                if issue_data.get('due_date'):
                    result += f"\n**Due Date:** {issue_data['due_date']}"

                return [TextContent(type="text", text=result)]
            except JIRAError as e:
                return [TextContent(
                    type="text",
                    text=f"Error fetching issue {issue_key}: {str(e)}"
                )]

        elif name == "search_jira_issues":
            jql = arguments.get("jql")
            max_results = arguments.get("max_results", 50)
            if not jql:
                return [TextContent(type="text", text="Error: jql query is required")]
            try:
                issues = client.search_issues(jql, maxResults=max_results)

                if not issues:
                    return [TextContent(
                        type="text",
                        text=f"No issues found matching query: {jql}"
                    )]

                result = f"# Search Results ({len(issues)} issues)\n\n"
                result += f"**Query:** {jql}\n\n"

                for issue in issues:
                    fields = issue.fields
                    result += f"## {issue.key}: {fields.summary}\n"
                    result += f"- **Status:** {fields.status.name}\n"
                    result += f"- **Priority:** {fields.priority.name if fields.priority else 'None'}\n"
                    result += f"- **Assignee:** {fields.assignee.displayName if fields.assignee else 'Unassigned'}\n"
                    result += f"- **URL:** {JIRA_URL}/browse/{issue.key}\n\n"

                return [TextContent(type="text", text=result)]
            except JIRAError as e:
                return [TextContent(
                    type="text",
                    text=f"Error searching issues: {str(e)}"
                )]

        elif name == "get_issue_comments":
            issue_key = arguments.get("issue_key")
            if not issue_key:
                return [TextContent(type="text", text="Error: issue_key is required")]

            comments = get_issue_comments(issue_key)

            if not comments:
                return [TextContent(
                    type="text",
                    text=f"No comments found for issue {issue_key}"
                )]

            result = f"# Comments for {issue_key} ({len(comments)} comments)\n\n"

            for i, comment in enumerate(comments, 1):
                result += f"## Comment {i}\n"
                result += f"**Author:** {comment['author']}\n"
                result += f"**Created:** {comment['created']}\n"
                result += f"**Updated:** {comment['updated']}\n\n"
                result += f"{comment['body']}\n\n"
                result += "---\n\n"

            return [TextContent(type="text", text=result)]

        elif name == "get_issue_attachments":
            issue_key = arguments.get("issue_key")
            if not issue_key:
                return [TextContent(type="text", text="Error: issue_key is required")]

            attachments = get_issue_attachments(issue_key)

            if not attachments:
                return [TextContent(
                    type="text",
                    text=f"No attachments found for issue {issue_key}"
                )]

            result = f"# Attachments for {issue_key} ({len(attachments)} files)\n\n"

            for attachment in attachments:
                result += f"## {attachment['filename']}\n"
                result += f"- **Size:** {attachment['size']} bytes\n"
                result += f"- **Type:** {attachment['mime_type']}\n"
                result += f"- **Author:** {attachment['author']}\n"
                result += f"- **Created:** {attachment['created']}\n"
                result += f"- **URL:** {attachment['url']}\n\n"

            return [TextContent(type="text", text=result)]

        elif name == "get_issue_media":
            issue_key = arguments.get("issue_key")
            max_files = arguments.get("max_files", 10)

            if not issue_key:
                return [TextContent(type="text", text="Error: issue_key is required")]

            attachments = get_issue_attachments(issue_key)

            if not attachments:
                return [TextContent(
                    type="text",
                    text=f"No attachments found for issue {issue_key}"
                )]

            # Filter for supported media types
            media_attachments = [a for a in attachments if is_supported_media(a['mime_type'])]

            if not media_attachments:
                return [TextContent(
                    type="text",
                    text=f"No images or videos found for issue {issue_key}. Found {len(attachments)} other attachment(s)."
                )]

            # Limit number of files
            media_attachments = media_attachments[:max_files]

            results: list[TextContent | ImageContent | EmbeddedResource] = []

            # Add summary text
            summary = f"# Media Attachments for {issue_key}\n\n"
            summary += f"Found {len(media_attachments)} image(s)/video(s):\n\n"
            results.append(TextContent(type="text", text=summary))

            # Download and return each media file
            for i, attachment in enumerate(media_attachments, 1):
                filename = attachment['filename']
                mime_type = attachment['mime_type']

                logger.info(f"Downloading {filename} ({mime_type}) from {issue_key}")

                # Download the attachment
                content = download_attachment(attachment['url'])

                if content is None:
                    results.append(TextContent(
                        type="text",
                        text=f"\n⚠️ Failed to download: {filename}\n"
                    ))
                    continue

                # Add file info
                file_info = f"\n## {i}. {filename}\n"
                file_info += f"- **Type:** {mime_type}\n"
                file_info += f"- **Size:** {attachment['size']:,} bytes\n"
                file_info += f"- **Author:** {attachment['author']}\n"
                file_info += f"- **Created:** {attachment['created']}\n\n"
                results.append(TextContent(type="text", text=file_info))

                # For images, return as ImageContent
                if mime_type.startswith("image/"):
                    media_type = get_attachment_media_type(mime_type)
                    if media_type:
                        # Encode as base64
                        base64_data = base64.b64encode(content).decode('utf-8')
                        results.append(ImageContent(
                            type="image",
                            data=base64_data,
                            mimeType=media_type
                        ))
                        logger.info(f"Successfully returned image: {filename}")
                    else:
                        results.append(TextContent(
                            type="text",
                            text=f"⚠️ Unsupported image format: {mime_type}\n"
                        ))
                else:
                    # For videos, provide download info (MCP doesn't support video display yet)
                    results.append(TextContent(
                        type="text",
                        text=f"🎥 Video file (download to view): {attachment['url']}\n"
                    ))

            return results

        else:
            return [TextContent(type="text", text=f"Unknown Jira tool: {name}")]

    except Exception as e:
        logger.error(f"Error in Jira tool {name}: {e}")
        return [TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]

