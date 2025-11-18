"""
GitLab Service Module for Bridge-MCP.

This module provides GitLab-specific functionality including:
- GitLab client initialization
- Tool definitions
- Tool handlers
"""

import os
import logging
from typing import Any, Sequence, Optional, cast

try:
    import gitlab
    from gitlab.exceptions import GitlabError, GitlabAuthenticationError
    GITLAB_AVAILABLE = True
except ImportError:
    GITLAB_AVAILABLE = False
    # Define dummy classes for type checking when gitlab is not installed
    gitlab = None  # type: ignore
    GitlabError = Exception  # type: ignore
    GitlabAuthenticationError = Exception  # type: ignore
    logger_temp = logging.getLogger("bridge-mcp.gitlab")
    logger_temp.warning("python-gitlab not installed. Run: pip install python-gitlab")

from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

logger = logging.getLogger("bridge-mcp.gitlab")

# Module-level GitLab client
gitlab_client: Optional[Any] = None


def init_gitlab_client() -> Optional[Any]:
    """Initialize the GitLab client using Personal Access Token."""
    global gitlab_client

    if not GITLAB_AVAILABLE:
        logger.error("python-gitlab library not available")
        return None

    # Read configuration from environment (after load_dotenv() has been called)
    gitlab_url = os.getenv("GITLAB_URL", "https://gitlab.com")
    gitlab_token = os.getenv("GITLAB_PERSONAL_ACCESS_TOKEN")
    gitlab_verify_ssl = os.getenv("GITLAB_VERIFY_SSL", "true").strip().lower() in {"1", "true", "yes", "on"}

    if not gitlab_token:
        logger.warning("GitLab Personal Access Token not found. GitLab features will be disabled.")
        return None

    try:
        gl = gitlab.Gitlab(
            url=gitlab_url,
            private_token=gitlab_token,
            ssl_verify=gitlab_verify_ssl
        )
        # Test authentication
        gl.auth()
        gitlab_client = gl
        logger.info(f"Successfully connected to GitLab at {gitlab_url} (verify_ssl={gitlab_verify_ssl})")
        return gl
    except GitlabAuthenticationError as e:
        logger.error(f"GitLab authentication failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to connect to GitLab: {e}")
        return None


def format_project_details(project: Any) -> dict[str, Any]:
    """Format GitLab project details into a structured dictionary."""
    try:
        return {
            "id": project.id,
            "name": project.name,
            "path": project.path,
            "path_with_namespace": project.path_with_namespace,
            "description": getattr(project, 'description', 'No description'),
            "web_url": project.web_url,
            "default_branch": getattr(project, 'default_branch', 'main'),
            "visibility": getattr(project, 'visibility', 'private'),
            "created_at": getattr(project, 'created_at', 'N/A'),
            "last_activity_at": getattr(project, 'last_activity_at', 'N/A'),
            "star_count": getattr(project, 'star_count', 0),
            "forks_count": getattr(project, 'forks_count', 0),
        }
    except Exception as e:
        logger.error(f"Error formatting project details: {e}")
        return {"error": str(e)}


def format_merge_request(mr: Any) -> dict[str, Any]:
    """Format merge request details."""
    try:
        return {
            "id": mr.id,
            "iid": mr.iid,
            "title": mr.title,
            "description": getattr(mr, 'description', 'No description'),
            "state": mr.state,
            "web_url": mr.web_url,
            "source_branch": mr.source_branch,
            "target_branch": mr.target_branch,
            "author": mr.author.get('name', 'Unknown') if isinstance(mr.author, dict) else getattr(mr.author, 'name', 'Unknown'),
            "assignee": mr.assignee.get('name', 'Unassigned') if mr.assignee and isinstance(mr.assignee, dict) else 'Unassigned',
            "created_at": mr.created_at,
            "updated_at": mr.updated_at,
            "merged_at": getattr(mr, 'merged_at', None),
            "draft": getattr(mr, 'draft', False) or getattr(mr, 'work_in_progress', False),
            "upvotes": getattr(mr, 'upvotes', 0),
            "downvotes": getattr(mr, 'downvotes', 0),
        }
    except Exception as e:
        logger.error(f"Error formatting merge request: {e}")
        return {"error": str(e)}


def format_pipeline(pipeline: Any) -> dict[str, Any]:
    """Format pipeline details."""
    try:
        return {
            "id": pipeline.id,
            "status": pipeline.status,
            "ref": pipeline.ref,
            "sha": pipeline.sha[:8],
            "web_url": pipeline.web_url,
            "created_at": pipeline.created_at,
            "updated_at": pipeline.updated_at,
        }
    except Exception as e:
        logger.error(f"Error formatting pipeline: {e}")
        return {"error": str(e)}


def format_issue(issue: Any) -> dict[str, Any]:
    """Format GitLab issue details."""
    try:
        return {
            "id": issue.id,
            "iid": issue.iid,
            "title": issue.title,
            "description": getattr(issue, 'description', 'No description'),
            "state": issue.state,
            "web_url": issue.web_url,
            "author": issue.author.get('name', 'Unknown') if isinstance(issue.author, dict) else getattr(issue.author, 'name', 'Unknown'),
            "assignee": issue.assignee.get('name', 'Unassigned') if issue.assignee and isinstance(issue.assignee, dict) else 'Unassigned',
            "created_at": issue.created_at,
            "updated_at": issue.updated_at,
            "labels": getattr(issue, 'labels', []),
        }
    except Exception as e:
        logger.error(f"Error formatting issue: {e}")
        return {"error": str(e)}


def get_gitlab_tools() -> list[Tool]:
    """Return the list of GitLab tools available."""
    return [
        Tool(
            name="get_gitlab_project",
            description="Get detailed information about a GitLab project by its ID or path (e.g., 'group/project')",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The project ID (numeric) or path (e.g., 'group/project', 'username/repo')",
                    }
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="list_gitlab_projects",
            description="List GitLab projects accessible to the authenticated user",
            inputSchema={
                "type": "object",
                "properties": {
                    "owned": {
                        "type": "boolean",
                        "description": "List only owned projects (default: false)",
                        "default": False,
                    },
                    "search": {
                        "type": "string",
                        "description": "Search projects by name (optional)",
                    },
                    "max_results": {
                        "type": "number",
                        "description": "Maximum number of projects to return (default: 20)",
                        "default": 20,
                    }
                },
            },
        ),
        Tool(
            name="get_merge_request",
            description="Get detailed information about a specific merge request",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The project ID or path",
                    },
                    "mr_iid": {
                        "type": "number",
                        "description": "The merge request IID (internal ID shown in GitLab UI)",
                    }
                },
                "required": ["project_id", "mr_iid"],
            },
        ),
        Tool(
            name="list_merge_requests",
            description="List merge requests for a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The project ID or path",
                    },
                    "state": {
                        "type": "string",
                        "description": "Filter by state: 'opened', 'closed', 'merged', or 'all' (default: 'opened')",
                        "default": "opened",
                    },
                    "max_results": {
                        "type": "number",
                        "description": "Maximum number of MRs to return (default: 20)",
                        "default": 20,
                    }
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="list_pipelines",
            description="List CI/CD pipelines for a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The project ID or path",
                    },
                    "ref": {
                        "type": "string",
                        "description": "Filter by git ref (branch/tag name, optional)",
                    },
                    "status": {
                        "type": "string",
                        "description": "Filter by status: 'running', 'pending', 'success', 'failed', 'canceled' (optional)",
                    },
                    "max_results": {
                        "type": "number",
                        "description": "Maximum number of pipelines to return (default: 20)",
                        "default": 20,
                    }
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="get_pipeline",
            description="Get detailed information about a specific pipeline",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The project ID or path",
                    },
                    "pipeline_id": {
                        "type": "number",
                        "description": "The pipeline ID",
                    }
                },
                "required": ["project_id", "pipeline_id"],
            },
        ),
        Tool(
            name="list_gitlab_issues",
            description="List issues for a GitLab project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The project ID or path",
                    },
                    "state": {
                        "type": "string",
                        "description": "Filter by state: 'opened' or 'closed' (default: 'opened')",
                        "default": "opened",
                    },
                    "max_results": {
                        "type": "number",
                        "description": "Maximum number of issues to return (default: 20)",
                        "default": 20,
                    }
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="get_gitlab_issue",
            description="Get detailed information about a specific GitLab issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The project ID or path",
                    },
                    "issue_iid": {
                        "type": "number",
                        "description": "The issue IID (internal ID shown in GitLab UI)",
                    }
                },
                "required": ["project_id", "issue_iid"],
            },
        ),
    ]


async def handle_gitlab_tool_call(
    name: str,
    arguments: Any
) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls for GitLab operations."""

    if not GITLAB_AVAILABLE:
        return [TextContent(
            type="text",
            text="Error: python-gitlab library not installed. Run: pip install python-gitlab"
        )]

    if gitlab_client is None:
        return [TextContent(
            type="text",
            text="Error: GitLab client not initialized. Please check your GITLAB_PERSONAL_ACCESS_TOKEN."
        )]

    gl = cast(Any, gitlab_client)

    try:
        if name == "get_gitlab_project":
            project_id = arguments.get("project_id")
            if not project_id:
                return [TextContent(type="text", text="Error: project_id is required")]

            try:
                project = gl.projects.get(project_id)
                details = format_project_details(project)

                result = f"""# {details['name']}
**Path:** {details['path_with_namespace']}
**URL:** {details['web_url']}

## Description
{details['description']}

## Details
- **Default Branch:** {details['default_branch']}
- **Visibility:** {details['visibility']}
- **Created:** {details['created_at']}
- **Last Activity:** {details['last_activity_at']}
- **Stars:** {details['star_count']}
- **Forks:** {details['forks_count']}
"""
                return [TextContent(type="text", text=result)]
            except GitlabError as e:
                return [TextContent(type="text", text=f"Error fetching project: {str(e)}")]

        elif name == "list_gitlab_projects":
            owned = arguments.get("owned", False)
            search = arguments.get("search")
            max_results = arguments.get("max_results", 20)

            try:
                params = {"per_page": max_results}
                if owned:
                    params["owned"] = True
                if search:
                    params["search"] = search

                projects = gl.projects.list(**params)

                if not projects:
                    return [TextContent(type="text", text="No projects found")]

                result = f"# GitLab Projects ({len(projects)} found)\n\n"
                for project in projects:
                    result += f"## {project.name}\n"
                    result += f"- **Path:** {project.path_with_namespace}\n"
                    result += f"- **URL:** {project.web_url}\n"
                    result += f"- **Stars:** {getattr(project, 'star_count', 0)}\n\n"

                return [TextContent(type="text", text=result)]
            except GitlabError as e:
                return [TextContent(type="text", text=f"Error listing projects: {str(e)}")]

        elif name == "get_merge_request":
            project_id = arguments.get("project_id")
            mr_iid = arguments.get("mr_iid")

            if not project_id or not mr_iid:
                return [TextContent(type="text", text="Error: project_id and mr_iid are required")]

            try:
                project = gl.projects.get(project_id)
                mr = project.mergerequests.get(mr_iid)
                details = format_merge_request(mr)

                result = f"""# MR !{details['iid']}: {details['title']}
**Status:** {details['state']} {'(Draft)' if details['draft'] else ''}
**URL:** {details['web_url']}

## Description
{details['description']}

## Details
- **Author:** {details['author']}
- **Assignee:** {details['assignee']}
- **Source:** {details['source_branch']} → **Target:** {details['target_branch']}
- **Created:** {details['created_at']}
- **Updated:** {details['updated_at']}
{f"- **Merged:** {details['merged_at']}" if details['merged_at'] else ""}
- **Upvotes:** {details['upvotes']} | **Downvotes:** {details['downvotes']}
"""
                return [TextContent(type="text", text=result)]
            except GitlabError as e:
                return [TextContent(type="text", text=f"Error fetching merge request: {str(e)}")]

        elif name == "list_merge_requests":
            project_id = arguments.get("project_id")
            state = arguments.get("state", "opened")
            max_results = arguments.get("max_results", 20)

            if not project_id:
                return [TextContent(type="text", text="Error: project_id is required")]

            try:
                project = gl.projects.get(project_id)
                params = {"state": state, "per_page": max_results}
                mrs = project.mergerequests.list(**params)

                if not mrs:
                    return [TextContent(type="text", text=f"No merge requests found with state '{state}'")]

                result = f"# Merge Requests ({len(mrs)} found)\n"
                result += f"**Project:** {project.name}\n"
                result += f"**Filter:** {state}\n\n"

                for mr in mrs:
                    draft_marker = " [Draft]" if (getattr(mr, 'draft', False) or getattr(mr, 'work_in_progress', False)) else ""
                    result += f"## !{mr.iid}: {mr.title}{draft_marker}\n"
                    result += f"- **Status:** {mr.state}\n"
                    result += f"- **Author:** {mr.author.get('name', 'Unknown') if isinstance(mr.author, dict) else 'Unknown'}\n"
                    result += f"- **Branch:** {mr.source_branch} → {mr.target_branch}\n"
                    result += f"- **URL:** {mr.web_url}\n\n"

                return [TextContent(type="text", text=result)]
            except GitlabError as e:
                return [TextContent(type="text", text=f"Error listing merge requests: {str(e)}")]

        elif name == "list_pipelines":
            project_id = arguments.get("project_id")
            ref = arguments.get("ref")
            status = arguments.get("status")
            max_results = arguments.get("max_results", 20)

            if not project_id:
                return [TextContent(type="text", text="Error: project_id is required")]

            try:
                project = gl.projects.get(project_id)
                params = {"per_page": max_results}
                if ref:
                    params["ref"] = ref
                if status:
                    params["status"] = status

                pipelines = project.pipelines.list(**params)

                if not pipelines:
                    return [TextContent(type="text", text="No pipelines found")]

                result = f"# Pipelines ({len(pipelines)} found)\n"
                result += f"**Project:** {project.name}\n"
                if ref:
                    result += f"**Ref:** {ref}\n"
                if status:
                    result += f"**Status:** {status}\n"
                result += "\n"

                for pipeline in pipelines:
                    status_emoji = {
                        "success": "✅",
                        "failed": "❌",
                        "running": "🔄",
                        "pending": "⏳",
                        "canceled": "🚫"
                    }.get(pipeline.status, "❓")

                    result += f"## Pipeline #{pipeline.id} {status_emoji}\n"
                    result += f"- **Status:** {pipeline.status}\n"
                    result += f"- **Ref:** {pipeline.ref}\n"
                    result += f"- **SHA:** {pipeline.sha[:8]}\n"
                    result += f"- **Created:** {pipeline.created_at}\n"
                    result += f"- **URL:** {pipeline.web_url}\n\n"

                return [TextContent(type="text", text=result)]
            except GitlabError as e:
                return [TextContent(type="text", text=f"Error listing pipelines: {str(e)}")]

        elif name == "get_pipeline":
            project_id = arguments.get("project_id")
            pipeline_id = arguments.get("pipeline_id")

            if not project_id or not pipeline_id:
                return [TextContent(type="text", text="Error: project_id and pipeline_id are required")]

            try:
                project = gl.projects.get(project_id)
                pipeline = project.pipelines.get(pipeline_id)

                status_emoji = {
                    "success": "✅",
                    "failed": "❌",
                    "running": "🔄",
                    "pending": "⏳",
                    "canceled": "🚫"
                }.get(pipeline.status, "❓")

                result = f"""# Pipeline #{pipeline.id} {status_emoji}
**Status:** {pipeline.status}
**Ref:** {pipeline.ref}
**SHA:** {pipeline.sha[:8]}
**URL:** {pipeline.web_url}

## Timeline
- **Created:** {pipeline.created_at}
- **Updated:** {pipeline.updated_at}

## Jobs
"""
                # Get jobs for this pipeline
                jobs = pipeline.jobs.list()
                for job in jobs:
                    job_status_emoji = {
                        "success": "✅",
                        "failed": "❌",
                        "running": "🔄",
                        "pending": "⏳",
                        "canceled": "🚫"
                    }.get(job.status, "❓")
                    result += f"- **{job.name}** {job_status_emoji} ({job.status})\n"

                return [TextContent(type="text", text=result)]
            except GitlabError as e:
                return [TextContent(type="text", text=f"Error fetching pipeline: {str(e)}")]

        elif name == "list_gitlab_issues":
            project_id = arguments.get("project_id")
            state = arguments.get("state", "opened")
            max_results = arguments.get("max_results", 20)

            if not project_id:
                return [TextContent(type="text", text="Error: project_id is required")]

            try:
                project = gl.projects.get(project_id)
                params = {"state": state, "per_page": max_results}
                issues = project.issues.list(**params)

                if not issues:
                    return [TextContent(type="text", text=f"No issues found with state '{state}'")]

                result = f"# Issues ({len(issues)} found)\n"
                result += f"**Project:** {project.name}\n"
                result += f"**Filter:** {state}\n\n"

                for issue in issues:
                    result += f"## #{issue.iid}: {issue.title}\n"
                    result += f"- **State:** {issue.state}\n"
                    result += f"- **Author:** {issue.author.get('name', 'Unknown') if isinstance(issue.author, dict) else 'Unknown'}\n"
                    if issue.assignee:
                        assignee_name = issue.assignee.get('name', 'Unknown') if isinstance(issue.assignee, dict) else 'Unknown'
                        result += f"- **Assignee:** {assignee_name}\n"
                    result += f"- **URL:** {issue.web_url}\n\n"

                return [TextContent(type="text", text=result)]
            except GitlabError as e:
                return [TextContent(type="text", text=f"Error listing issues: {str(e)}")]

        elif name == "get_gitlab_issue":
            project_id = arguments.get("project_id")
            issue_iid = arguments.get("issue_iid")

            if not project_id or not issue_iid:
                return [TextContent(type="text", text="Error: project_id and issue_iid are required")]

            try:
                project = gl.projects.get(project_id)
                issue = project.issues.get(issue_iid)
                details = format_issue(issue)

                result = f"""# Issue #{details['iid']}: {details['title']}
**State:** {details['state']}
**URL:** {details['web_url']}

## Description
{details['description']}

## Details
- **Author:** {details['author']}
- **Assignee:** {details['assignee']}
- **Created:** {details['created_at']}
- **Updated:** {details['updated_at']}
"""
                if details['labels']:
                    result += f"- **Labels:** {', '.join(details['labels'])}\n"

                return [TextContent(type="text", text=result)]
            except GitlabError as e:
                return [TextContent(type="text", text=f"Error fetching issue: {str(e)}")]

        else:
            return [TextContent(
                type="text",
                text=f"Unknown GitLab tool: {name}"
            )]

    except Exception as e:
        logger.error(f"Error handling GitLab tool call '{name}': {e}")
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]

