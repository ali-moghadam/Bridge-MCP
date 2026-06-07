"""
GitLab Service Module for Bridge-MCP.

Uses the glab CLI (https://gitlab.com/gitlab-org/cli) for all GitLab operations.

Environment variables (read from .env via the main server):
  GITLAB_URL                  GitLab instance base URL (default: https://gitlab.com)
  GITLAB_PERSONAL_ACCESS_TOKEN  Personal access token passed to glab as GITLAB_TOKEN
  GITLAB_VERIFY_SSL           Set to false/0/no to disable SSL verification (default: true)
"""

import json
import logging
import os
import shutil
import subprocess
import urllib.parse
from typing import Any, Sequence

from mcp.types import EmbeddedResource, ImageContent, TextContent, Tool

logger = logging.getLogger("bridge-mcp.gitlab")

# Populated by init_gitlab_client() from environment variables
_gitlab_host: str | None = None   # e.g. "gitlab.mycompany.com"
_gitlab_token: str | None = None  # value of GITLAB_PERSONAL_ACCESS_TOKEN
_gitlab_verify_ssl: bool = True   # value of GITLAB_VERIFY_SSL

_STATUS_EMOJI: dict[str, str] = {
    "success": "✅",
    "failed": "❌",
    "running": "🔄",
    "pending": "⏳",
    "canceled": "🚫",
    "skipped": "⏭️",
    "manual": "🔧",
    "created": "🆕",
    "waiting_for_resource": "⏳",
    "preparing": "🔧",
    "scheduled": "📅",
    "opened": "🟢",
    "closed": "🔴",
    "merged": "🟣",
}


# ── Initialisation ────────────────────────────────────────────────────────────

def init_gitlab_client() -> bool | None:
    """
    Read env vars and verify glab is available.

    Priority:
      1. GITLAB_PERSONAL_ACCESS_TOKEN + GITLAB_URL  → injected into every glab call
      2. Fallback: glab's own stored credentials (`glab auth login`)
    """
    global _gitlab_host, _gitlab_token, _gitlab_verify_ssl

    if not shutil.which("glab"):
        logger.warning("glab CLI not found. Install from: https://gitlab.com/gitlab-org/cli")
        return None

    # Read env vars (load_dotenv() has already been called by the main server)
    gitlab_url = os.getenv("GITLAB_URL", "").strip()
    _gitlab_token = os.getenv("GITLAB_PERSONAL_ACCESS_TOKEN", "").strip() or None
    _gitlab_verify_ssl = os.getenv("GITLAB_VERIFY_SSL", "true").strip().lower() in {"1", "true", "yes", "on"}

    if gitlab_url:
        parsed = urllib.parse.urlparse(gitlab_url)
        _gitlab_host = parsed.hostname  # e.g. "gitlab.mycompany.com"

    if _gitlab_token:
        logger.info(
            "GitLab: using GITLAB_PERSONAL_ACCESS_TOKEN for %s (ssl_verify=%s)",
            _gitlab_host or "gitlab.com",
            _gitlab_verify_ssl,
        )
        return True

    # No token in env — fall back to glab's stored auth
    result = subprocess.run(["glab", "auth", "status"], capture_output=True, text=True)
    if result.returncode != 0:
        logger.warning(
            "No GITLAB_PERSONAL_ACCESS_TOKEN set and glab not authenticated. "
            "Set the env var or run: glab auth login"
        )
        return None

    logger.info("GitLab: using glab stored credentials (ssl_verify=%s)", _gitlab_verify_ssl)
    return True


# ── Helpers ───────────────────────────────────────────────────────────────────

def _run(*args: str) -> subprocess.CompletedProcess:
    """Run a glab command, injecting env-var credentials when available."""
    cmd = ["glab"] + list(args)
    logger.debug("Running: %s", " ".join(cmd))

    env = os.environ.copy()
    if _gitlab_token:
        env["GITLAB_TOKEN"] = _gitlab_token
    if not _gitlab_verify_ssl:
        env["GIT_SSL_NO_VERIFY"] = "true"

    return subprocess.run(cmd, capture_output=True, text=True, env=env)


def _proj(project_id: str) -> str:
    """URL-encode a project path/ID for use in API endpoints."""
    return urllib.parse.quote(str(project_id), safe="")


def _api(endpoint: str, method: str = "GET", fields: dict[str, Any] | None = None, raw: bool = False) -> Any:
    """
    Call the GitLab REST API via `glab api`.

    - `fields` are passed as -F key=value (query params for GET, body for writes).
    - Set `raw=True` to return plain text instead of parsed JSON.
    """
    args = ["api", "-X", method]
    if _gitlab_host:
        args += ["--hostname", _gitlab_host]
    args.append(endpoint)
    for k, v in (fields or {}).items():
        args += ["-F", f"{k}={v}"]
    result = _run(*args)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"glab api failed: {endpoint}")
    if raw:
        return result.stdout
    return json.loads(result.stdout)


def _ok(text: str) -> list[TextContent]:
    return [TextContent(type="text", text=text)]


def _err(msg: str) -> list[TextContent]:
    return [TextContent(type="text", text=f"Error: {msg}")]


def _status(s: str) -> str:
    return f"{_STATUS_EMOJI.get(s, '❓')} {s}"


# ── Tool definitions ──────────────────────────────────────────────────────────

def get_gitlab_tools() -> list[Tool]:
    """Return all GitLab tools."""
    return [
        # ── Projects ─────────────────────────────────────────────────────────
        Tool(
            name="get_gitlab_project",
            description="Get detailed information about a GitLab project by ID or path (e.g. 'group/project')",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Numeric project ID or path like 'group/repo'"},
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
                    "owned": {"type": "boolean", "description": "Only owned projects (default false)", "default": False},
                    "search": {"type": "string", "description": "Filter by name"},
                    "max_results": {"type": "number", "description": "Max results (default 20)", "default": 20},
                },
            },
        ),
        # ── Merge Requests ────────────────────────────────────────────────────
        Tool(
            name="get_merge_request",
            description="Get detailed information about a specific merge request",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "mr_iid": {"type": "number", "description": "MR internal ID (shown in GitLab UI)"},
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
                    "project_id": {"type": "string"},
                    "state": {
                        "type": "string",
                        "description": "Filter: 'opened', 'closed', 'merged', 'all' (default: 'opened')",
                        "default": "opened",
                    },
                    "max_results": {"type": "number", "default": 20},
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="list_mr_notes",
            description="List all comments/notes on a merge request",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "mr_iid": {"type": "number"},
                },
                "required": ["project_id", "mr_iid"],
            },
        ),
        Tool(
            name="create_mr_note",
            description="Post a comment on a merge request",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "mr_iid": {"type": "number"},
                    "body": {"type": "string", "description": "Comment text"},
                },
                "required": ["project_id", "mr_iid", "body"],
            },
        ),
        # ── Issues ────────────────────────────────────────────────────────────
        Tool(
            name="get_gitlab_issue",
            description="Get detailed information about a specific GitLab issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "issue_iid": {"type": "number"},
                },
                "required": ["project_id", "issue_iid"],
            },
        ),
        Tool(
            name="list_gitlab_issues",
            description="List issues for a GitLab project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "state": {"type": "string", "description": "'opened' or 'closed' (default: 'opened')", "default": "opened"},
                    "max_results": {"type": "number", "default": 20},
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="create_gitlab_issue",
            description="Create a new issue in a GitLab project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "labels": {"type": "string", "description": "Comma-separated label names"},
                    "assignee_ids": {"type": "string", "description": "Comma-separated user IDs to assign"},
                },
                "required": ["project_id", "title"],
            },
        ),
        Tool(
            name="list_issue_notes",
            description="List all comments/notes on an issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "issue_iid": {"type": "number"},
                },
                "required": ["project_id", "issue_iid"],
            },
        ),
        Tool(
            name="create_issue_note",
            description="Post a comment on an issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "issue_iid": {"type": "number"},
                    "body": {"type": "string"},
                },
                "required": ["project_id", "issue_iid", "body"],
            },
        ),
        # ── Pipelines & CI ────────────────────────────────────────────────────
        Tool(
            name="list_pipelines",
            description="List CI/CD pipelines for a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "ref": {"type": "string", "description": "Filter by branch/tag"},
                    "status": {
                        "type": "string",
                        "description": "Filter by status: 'running', 'pending', 'success', 'failed', 'canceled'",
                    },
                    "max_results": {"type": "number", "default": 20},
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="get_pipeline",
            description="Get detailed information about a specific pipeline including its jobs",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "pipeline_id": {"type": "number"},
                },
                "required": ["project_id", "pipeline_id"],
            },
        ),
        Tool(
            name="retry_pipeline",
            description="Retry a failed/canceled pipeline",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "pipeline_id": {"type": "number"},
                },
                "required": ["project_id", "pipeline_id"],
            },
        ),
        Tool(
            name="cancel_pipeline",
            description="Cancel a running pipeline",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "pipeline_id": {"type": "number"},
                },
                "required": ["project_id", "pipeline_id"],
            },
        ),
        Tool(
            name="list_pipeline_jobs",
            description="List all jobs in a pipeline",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "pipeline_id": {"type": "number"},
                },
                "required": ["project_id", "pipeline_id"],
            },
        ),
        Tool(
            name="get_job_log",
            description="Get the trace/log output of a CI job",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "job_id": {"type": "number"},
                },
                "required": ["project_id", "job_id"],
            },
        ),
        # ── Repository ────────────────────────────────────────────────────────
        Tool(
            name="list_branches",
            description="List branches in a repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "search": {"type": "string", "description": "Filter branch names"},
                    "max_results": {"type": "number", "default": 50},
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="get_branch",
            description="Get information about a specific branch including latest commit",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "branch": {"type": "string"},
                },
                "required": ["project_id", "branch"],
            },
        ),
        Tool(
            name="list_commits",
            description="List commits in a repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "ref": {"type": "string", "description": "Branch, tag, or commit SHA (default: default branch)"},
                    "path": {"type": "string", "description": "Filter commits touching a specific file path"},
                    "max_results": {"type": "number", "default": 20},
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="get_commit",
            description="Get details of a specific commit including diff stats",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "sha": {"type": "string", "description": "Commit SHA"},
                },
                "required": ["project_id", "sha"],
            },
        ),
        Tool(
            name="list_repository_tree",
            description="List files and directories at a path in the repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "path": {"type": "string", "description": "Directory path (default: root)"},
                    "ref": {"type": "string", "description": "Branch/tag/commit"},
                    "recursive": {"type": "boolean", "description": "List recursively (default false)", "default": False},
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="get_file",
            description="Get the raw contents of a file from the repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "file_path": {"type": "string", "description": "Path to file (e.g. 'src/main.py')"},
                    "ref": {"type": "string", "description": "Branch/tag/commit (default: HEAD)"},
                },
                "required": ["project_id", "file_path"],
            },
        ),
        # ── Releases & Tags ───────────────────────────────────────────────────
        Tool(
            name="list_releases",
            description="List releases for a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "max_results": {"type": "number", "default": 20},
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="get_release",
            description="Get details of a specific release",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "tag": {"type": "string", "description": "Tag name of the release"},
                },
                "required": ["project_id", "tag"],
            },
        ),
        Tool(
            name="list_tags",
            description="List tags in a repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "search": {"type": "string", "description": "Filter tag names"},
                    "max_results": {"type": "number", "default": 20},
                },
                "required": ["project_id"],
            },
        ),
        # ── Members & Labels ──────────────────────────────────────────────────
        Tool(
            name="list_project_members",
            description="List members of a GitLab project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "query": {"type": "string", "description": "Filter by name or username"},
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="list_labels",
            description="List labels defined in a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                },
                "required": ["project_id"],
            },
        ),
    ]


# ── Tool handler ──────────────────────────────────────────────────────────────

async def handle_gitlab_tool_call(
    name: str, arguments: Any
) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Dispatch a tool call to the appropriate glab-backed handler."""
    try:
        return _dispatch(name, arguments or {})
    except RuntimeError as e:
        return _err(str(e))
    except Exception as e:
        logger.exception("Unexpected error in gitlab tool '%s'", name)
        return _err(str(e))


def _dispatch(name: str, a: dict[str, Any]) -> list[TextContent]:  # noqa: C901
    pid = a.get("project_id", "")
    p = _proj(pid)

    # ── Projects ─────────────────────────────────────────────────────────────
    if name == "get_gitlab_project":
        d = _api(f"projects/{p}")
        return _ok(
            f"# {d['name']}\n"
            f"**Path:** {d['path_with_namespace']}\n"
            f"**URL:** {d['web_url']}\n\n"
            f"## Description\n{d.get('description') or 'No description'}\n\n"
            f"## Details\n"
            f"- **Default Branch:** {d.get('default_branch', 'N/A')}\n"
            f"- **Visibility:** {d.get('visibility', 'N/A')}\n"
            f"- **Created:** {d.get('created_at', 'N/A')}\n"
            f"- **Last Activity:** {d.get('last_activity_at', 'N/A')}\n"
            f"- **Stars:** {d.get('star_count', 0)}\n"
            f"- **Forks:** {d.get('forks_count', 0)}\n"
            f"- **Open Issues:** {d.get('open_issues_count', 0)}\n"
        )

    if name == "list_gitlab_projects":
        fields: dict[str, Any] = {"per_page": a.get("max_results", 20)}
        if a.get("owned"):
            fields["owned"] = "true"
        if a.get("search"):
            fields["search"] = a["search"]
        projects = _api("projects", fields=fields)
        if not projects:
            return _ok("No projects found.")
        lines = [f"# GitLab Projects ({len(projects)} found)\n"]
        for proj in projects:
            lines.append(f"## {proj['name']}")
            lines.append(f"- **Path:** {proj['path_with_namespace']}")
            lines.append(f"- **URL:** {proj['web_url']}")
            lines.append(f"- **Stars:** {proj.get('star_count', 0)}\n")
        return _ok("\n".join(lines))

    # ── Merge Requests ────────────────────────────────────────────────────────
    if name == "get_merge_request":
        iid = a["mr_iid"]
        d = _api(f"projects/{p}/merge_requests/{iid}")
        author = (d.get("author") or {}).get("name", "Unknown")
        assignee = (d.get("assignee") or {}).get("name", "Unassigned")
        draft = d.get("draft") or d.get("work_in_progress", False)
        return _ok(
            f"# MR !{d['iid']}: {d['title']} {'[Draft]' if draft else ''}\n"
            f"**Status:** {_status(d['state'])}\n"
            f"**URL:** {d['web_url']}\n\n"
            f"## Description\n{d.get('description') or 'No description'}\n\n"
            f"## Details\n"
            f"- **Author:** {author}\n"
            f"- **Assignee:** {assignee}\n"
            f"- **Branch:** `{d['source_branch']}` → `{d['target_branch']}`\n"
            f"- **Created:** {d['created_at']}\n"
            f"- **Updated:** {d['updated_at']}\n"
            + (f"- **Merged:** {d['merged_at']}\n" if d.get("merged_at") else "")
            + f"- **Upvotes:** {d.get('upvotes', 0)}  **Downvotes:** {d.get('downvotes', 0)}\n"
        )

    if name == "list_merge_requests":
        state = a.get("state", "opened")
        mrs = _api(f"projects/{p}/merge_requests", fields={"state": state, "per_page": a.get("max_results", 20)})
        if not mrs:
            return _ok(f"No merge requests found (state={state}).")
        lines = [f"# Merge Requests — {pid} ({len(mrs)} found, state={state})\n"]
        for mr in mrs:
            draft = mr.get("draft") or mr.get("work_in_progress", False)
            lines.append(f"## !{mr['iid']}: {mr['title']}{' [Draft]' if draft else ''}")
            lines.append(f"- **Status:** {_status(mr['state'])}")
            lines.append(f"- **Author:** {(mr.get('author') or {}).get('name', 'Unknown')}")
            lines.append(f"- **Branch:** `{mr['source_branch']}` → `{mr['target_branch']}`")
            lines.append(f"- **URL:** {mr['web_url']}\n")
        return _ok("\n".join(lines))

    if name == "list_mr_notes":
        iid = a["mr_iid"]
        notes = _api(f"projects/{p}/merge_requests/{iid}/notes", fields={"per_page": 100})
        if not notes:
            return _ok("No notes found on this merge request.")
        lines = [f"# Notes on MR !{iid} ({len(notes)} total)\n"]
        for n in notes:
            author = (n.get("author") or {}).get("name", "Unknown")
            lines.append(f"**{author}** at {n['created_at']}:")
            lines.append(n["body"])
            lines.append("")
        return _ok("\n".join(lines))

    if name == "create_mr_note":
        iid = a["mr_iid"]
        note = _api(f"projects/{p}/merge_requests/{iid}/notes", method="POST", fields={"body": a["body"]})
        return _ok(f"Comment posted on MR !{iid} (note id={note['id']}).")

    # ── Issues ────────────────────────────────────────────────────────────────
    if name == "get_gitlab_issue":
        iid = a["issue_iid"]
        d = _api(f"projects/{p}/issues/{iid}")
        author = (d.get("author") or {}).get("name", "Unknown")
        assignee = (d.get("assignee") or {}).get("name", "Unassigned")
        labels = ", ".join(d.get("labels") or []) or "None"
        return _ok(
            f"# Issue #{d['iid']}: {d['title']}\n"
            f"**State:** {_status(d['state'])}\n"
            f"**URL:** {d['web_url']}\n\n"
            f"## Description\n{d.get('description') or 'No description'}\n\n"
            f"## Details\n"
            f"- **Author:** {author}\n"
            f"- **Assignee:** {assignee}\n"
            f"- **Labels:** {labels}\n"
            f"- **Created:** {d['created_at']}\n"
            f"- **Updated:** {d['updated_at']}\n"
            + (f"- **Closed:** {d['closed_at']}\n" if d.get("closed_at") else "")
        )

    if name == "list_gitlab_issues":
        state = a.get("state", "opened")
        issues = _api(f"projects/{p}/issues", fields={"state": state, "per_page": a.get("max_results", 20)})
        if not issues:
            return _ok(f"No issues found (state={state}).")
        lines = [f"# Issues — {pid} ({len(issues)} found, state={state})\n"]
        for issue in issues:
            lines.append(f"## #{issue['iid']}: {issue['title']}")
            lines.append(f"- **State:** {_status(issue['state'])}")
            lines.append(f"- **Author:** {(issue.get('author') or {}).get('name', 'Unknown')}")
            if issue.get("assignee"):
                lines.append(f"- **Assignee:** {(issue['assignee'] or {}).get('name', 'Unknown')}")
            if issue.get("labels"):
                lines.append(f"- **Labels:** {', '.join(issue['labels'])}")
            lines.append(f"- **URL:** {issue['web_url']}\n")
        return _ok("\n".join(lines))

    if name == "create_gitlab_issue":
        fields = {"title": a["title"]}
        if a.get("description"):
            fields["description"] = a["description"]
        if a.get("labels"):
            fields["labels"] = a["labels"]
        if a.get("assignee_ids"):
            fields["assignee_ids[]"] = a["assignee_ids"]
        issue = _api(f"projects/{p}/issues", method="POST", fields=fields)
        return _ok(f"Issue #{issue['iid']} created: {issue['title']}\nURL: {issue['web_url']}")

    if name == "list_issue_notes":
        iid = a["issue_iid"]
        notes = _api(f"projects/{p}/issues/{iid}/notes", fields={"per_page": 100})
        if not notes:
            return _ok("No notes found on this issue.")
        lines = [f"# Notes on Issue #{iid} ({len(notes)} total)\n"]
        for n in notes:
            author = (n.get("author") or {}).get("name", "Unknown")
            lines.append(f"**{author}** at {n['created_at']}:")
            lines.append(n["body"])
            lines.append("")
        return _ok("\n".join(lines))

    if name == "create_issue_note":
        iid = a["issue_iid"]
        note = _api(f"projects/{p}/issues/{iid}/notes", method="POST", fields={"body": a["body"]})
        return _ok(f"Comment posted on Issue #{iid} (note id={note['id']}).")

    # ── Pipelines & CI ────────────────────────────────────────────────────────
    if name == "list_pipelines":
        fields = {"per_page": a.get("max_results", 20)}
        if a.get("ref"):
            fields["ref"] = a["ref"]
        if a.get("status"):
            fields["status"] = a["status"]
        pipelines = _api(f"projects/{p}/pipelines", fields=fields)
        if not pipelines:
            return _ok("No pipelines found.")
        lines = [f"# Pipelines — {pid} ({len(pipelines)} found)\n"]
        for pl in pipelines:
            lines.append(f"## Pipeline #{pl['id']} — {_status(pl['status'])}")
            lines.append(f"- **Ref:** {pl['ref']}")
            lines.append(f"- **SHA:** {pl['sha'][:8]}")
            lines.append(f"- **Created:** {pl['created_at']}")
            lines.append(f"- **URL:** {pl['web_url']}\n")
        return _ok("\n".join(lines))

    if name == "get_pipeline":
        pid_val = a["pipeline_id"]
        pl = _api(f"projects/{p}/pipelines/{pid_val}")
        jobs = _api(f"projects/{p}/pipelines/{pid_val}/jobs")
        lines = [
            f"# Pipeline #{pl['id']} — {_status(pl['status'])}",
            f"**Ref:** {pl['ref']}",
            f"**SHA:** {pl['sha'][:8]}",
            f"**URL:** {pl['web_url']}",
            f"**Created:** {pl['created_at']}",
            f"**Updated:** {pl['updated_at']}",
            "",
            "## Jobs",
        ]
        for job in jobs:
            lines.append(f"- **{job['name']}** ({job.get('stage', '?')}) — {_status(job['status'])}  [id={job['id']}]")
        return _ok("\n".join(lines))

    if name == "retry_pipeline":
        pid_val = a["pipeline_id"]
        result = _api(f"projects/{p}/pipelines/{pid_val}/retry", method="POST")
        return _ok(f"Pipeline #{result['id']} retried. New status: {result['status']}")

    if name == "cancel_pipeline":
        pid_val = a["pipeline_id"]
        result = _api(f"projects/{p}/pipelines/{pid_val}/cancel", method="POST")
        return _ok(f"Pipeline #{result['id']} canceled. Status: {result['status']}")

    if name == "list_pipeline_jobs":
        pid_val = a["pipeline_id"]
        jobs = _api(f"projects/{p}/pipelines/{pid_val}/jobs")
        if not jobs:
            return _ok("No jobs found for this pipeline.")
        lines = [f"# Jobs for Pipeline #{pid_val}\n"]
        for job in jobs:
            lines.append(f"## {job['name']} — {_status(job['status'])}")
            lines.append(f"- **Stage:** {job.get('stage', 'N/A')}")
            lines.append(f"- **Job ID:** {job['id']}")
            lines.append(f"- **Created:** {job['created_at']}")
            if job.get("started_at"):
                lines.append(f"- **Started:** {job['started_at']}")
            if job.get("finished_at"):
                lines.append(f"- **Finished:** {job['finished_at']}")
            if job.get("duration"):
                lines.append(f"- **Duration:** {job['duration']:.1f}s")
            lines.append(f"- **URL:** {job['web_url']}\n")
        return _ok("\n".join(lines))

    if name == "get_job_log":
        job_id = a["job_id"]
        log = _api(f"projects/{p}/jobs/{job_id}/trace", raw=True)
        if not log:
            return _ok("No log output available for this job.")
        return _ok(f"# Job {job_id} Log\n\n```\n{log}\n```")

    # ── Repository ────────────────────────────────────────────────────────────
    if name == "list_branches":
        fields = {"per_page": a.get("max_results", 50)}
        if a.get("search"):
            fields["search"] = a["search"]
        branches = _api(f"projects/{p}/repository/branches", fields=fields)
        if not branches:
            return _ok("No branches found.")
        lines = [f"# Branches — {pid} ({len(branches)} found)\n"]
        for b in branches:
            protected = " 🔒" if b.get("protected") else ""
            commit = (b.get("commit") or {})
            lines.append(
                f"- **{b['name']}**{protected}  "
                f"(last commit: `{commit.get('short_id', '?')}` by {commit.get('committer_name', '?')} "
                f"at {commit.get('committed_date', '?')[:10]})"
            )
        return _ok("\n".join(lines))

    if name == "get_branch":
        branch = urllib.parse.quote(a["branch"], safe="")
        b = _api(f"projects/{p}/repository/branches/{branch}")
        commit = b.get("commit") or {}
        return _ok(
            f"# Branch: {b['name']}\n"
            f"- **Protected:** {b.get('protected', False)}\n"
            f"- **Merged:** {b.get('merged', False)}\n\n"
            f"## Latest Commit\n"
            f"- **SHA:** `{commit.get('id', 'N/A')}`\n"
            f"- **Title:** {commit.get('title', 'N/A')}\n"
            f"- **Author:** {commit.get('author_name', 'N/A')}\n"
            f"- **Date:** {commit.get('committed_date', 'N/A')}\n"
        )

    if name == "list_commits":
        fields = {"per_page": a.get("max_results", 20)}
        if a.get("ref"):
            fields["ref_name"] = a["ref"]
        if a.get("path"):
            fields["path"] = a["path"]
        commits = _api(f"projects/{p}/repository/commits", fields=fields)
        if not commits:
            return _ok("No commits found.")
        lines = [f"# Commits — {pid} ({len(commits)} returned)\n"]
        for c in commits:
            lines.append(f"- `{c['short_id']}` **{c['title']}**")
            lines.append(f"  by {c.get('author_name', 'Unknown')} at {c.get('committed_date', 'N/A')[:19]}")
        return _ok("\n".join(lines))

    if name == "get_commit":
        sha = a["sha"]
        c = _api(f"projects/{p}/repository/commits/{sha}")
        stats = c.get("stats") or {}
        return _ok(
            f"# Commit `{c['short_id']}`\n"
            f"**Title:** {c['title']}\n"
            f"**Author:** {c.get('author_name')} <{c.get('author_email')}>\n"
            f"**Date:** {c.get('committed_date', 'N/A')}\n"
            f"**Message:**\n{c.get('message', '')}\n\n"
            f"## Stats\n"
            f"- **Additions:** +{stats.get('additions', 0)}\n"
            f"- **Deletions:** -{stats.get('deletions', 0)}\n"
            f"- **Total:** {stats.get('total', 0)} changes\n"
        )

    if name == "list_repository_tree":
        fields: dict[str, Any] = {}
        if a.get("path"):
            fields["path"] = a["path"]
        if a.get("ref"):
            fields["ref"] = a["ref"]
        if a.get("recursive"):
            fields["recursive"] = "true"
        tree = _api(f"projects/{p}/repository/tree", fields=fields)
        if not tree:
            return _ok("No files found at this path.")
        lines = [f"# Repository Tree — {pid}\n"]
        for item in tree:
            icon = "📁" if item["type"] == "tree" else "📄"
            lines.append(f"{icon} `{item['path']}` ({item['type']})")
        return _ok("\n".join(lines))

    if name == "get_file":
        file_path = urllib.parse.quote(a["file_path"], safe="")
        fields = {}
        if a.get("ref"):
            fields["ref"] = a["ref"]
        content = _api(f"projects/{p}/repository/files/{file_path}/raw", fields=fields, raw=True)
        return _ok(f"# {a['file_path']}\n\n```\n{content}\n```")

    # ── Releases & Tags ───────────────────────────────────────────────────────
    if name == "list_releases":
        releases = _api(f"projects/{p}/releases", fields={"per_page": a.get("max_results", 20)})
        if not releases:
            return _ok("No releases found.")
        lines = [f"# Releases — {pid} ({len(releases)} found)\n"]
        for r in releases:
            lines.append(f"## {r['name']} (`{r['tag_name']}`)")
            lines.append(f"- **Released:** {r.get('released_at', 'N/A')[:10]}")
            if r.get("description"):
                lines.append(f"- **Notes:** {r['description'][:200]}...")
            lines.append(f"- **URL:** {r.get('_links', {}).get('self', 'N/A')}\n")
        return _ok("\n".join(lines))

    if name == "get_release":
        tag = urllib.parse.quote(a["tag"], safe="")
        r = _api(f"projects/{p}/releases/{tag}")
        assets = r.get("assets", {})
        links = assets.get("links", [])
        sources = assets.get("sources", [])
        lines = [
            f"# Release: {r['name']} (`{r['tag_name']}`)",
            f"**Released:** {r.get('released_at', 'N/A')}",
            f"**Author:** {(r.get('author') or {}).get('name', 'Unknown')}",
            "",
            "## Release Notes",
            r.get("description") or "No description.",
        ]
        if links:
            lines += ["", "## Asset Links"]
            for link in links:
                lines.append(f"- [{link['name']}]({link['url']})")
        if sources:
            lines += ["", "## Source Archives"]
            for src in sources:
                lines.append(f"- {src['format']}: {src['url']}")
        return _ok("\n".join(lines))

    if name == "list_tags":
        fields = {"per_page": a.get("max_results", 20)}
        if a.get("search"):
            fields["search"] = a["search"]
        tags = _api(f"projects/{p}/repository/tags", fields=fields)
        if not tags:
            return _ok("No tags found.")
        lines = [f"# Tags — {pid} ({len(tags)} found)\n"]
        for t in tags:
            commit = (t.get("commit") or {})
            lines.append(
                f"- **{t['name']}**  "
                f"(`{commit.get('short_id', '?')}` at {commit.get('committed_date', 'N/A')[:10]})"
                + (f"  ← *has release*" if t.get("release") else "")
            )
        return _ok("\n".join(lines))

    # ── Members & Labels ──────────────────────────────────────────────────────
    if name == "list_project_members":
        fields = {}
        if a.get("query"):
            fields["query"] = a["query"]
        members = _api(f"projects/{p}/members", fields=fields)
        if not members:
            return _ok("No members found.")
        access_levels = {10: "Guest", 20: "Reporter", 30: "Developer", 40: "Maintainer", 50: "Owner"}
        lines = [f"# Members — {pid} ({len(members)} found)\n"]
        for m in members:
            role = access_levels.get(m.get("access_level", 0), str(m.get("access_level", "?")))
            lines.append(f"- **{m['name']}** (@{m['username']}) — {role}")
        return _ok("\n".join(lines))

    if name == "list_labels":
        labels = _api(f"projects/{p}/labels", fields={"per_page": 100})
        if not labels:
            return _ok("No labels found.")
        lines = [f"# Labels — {pid} ({len(labels)} found)\n"]
        for label in labels:
            color = label.get("color", "")
            desc = f" — {label['description']}" if label.get("description") else ""
            lines.append(f"- **{label['name']}** `{color}`{desc}")
        return _ok("\n".join(lines))

    return _err(f"Unknown GitLab tool: {name}")
