# Services Directory

This directory contains service modules for Bridge-MCP. Each service is implemented as a separate module with a consistent interface.

## Available Services

### ✅ Jira Service (`jira_service.py`)
**Status:** Fully implemented

**Environment Variables:**
- `JIRA_URL` - Your Jira instance URL
- `JIRA_PERSONAL_ACCESS_TOKEN` - Personal Access Token
- `JIRA_VERIFY_SSL` - SSL verification (default: true)

**Tools:**
- `get_jira_issue` - Get issue details
- `search_jira_issues` - Search using JQL
- `get_issue_comments` - Get issue comments
- `get_issue_attachments` - Get attachment metadata
- `get_issue_media` - Download and display images

### ✅ GitLab Service (`gitlab_service.py`)
**Status:** Fully implemented. Two selectable backends.

`gitlab_service.py` is a thin facade that selects a backend at init and delegates to it:
- `gitlab_mcp.py` — default. MCP client to the instance's native endpoint `<GITLAB_URL>/api/v4/mcp` (streamable HTTP, Bearer auth). Tools are exposed via **dynamic passthrough** — whatever the instance's MCP endpoint reports.
- `gitlab_glab.py` — shells out to the `glab` CLI. Exposes the fixed 28-tool set below.

Backend is chosen by `GITLAB_BACKEND` (`mcp` default | `glab`). No automatic fallback: if the selected backend fails init, the GitLab service is disabled.

The facade exposes `init_gitlab_client()`, `get_gitlab_tools()`, `gitlab_tool_names()`, and `handle_gitlab_tool_call()`. `gitlab_tool_names()` returns the active backend's tool-name set and is what the server uses to route calls (the mcp backend's names are dynamic, so the server cannot hardcode them).

**Environment Variables:**
- `GITLAB_BACKEND` - `mcp` (default) or `glab`
- `GITLAB_URL` - GitLab instance URL (default: https://gitlab.com)
- `GITLAB_PERSONAL_ACCESS_TOKEN` - Personal Access Token (Bearer token for `mcp`; `GITLAB_TOKEN` for `glab`, or use `glab auth login`)
- `GITLAB_VERIFY_SSL` - SSL verification (default: true)

**Tools (`glab` backend, 28):**
- Projects: `get_gitlab_project`, `list_gitlab_projects`
- Merge requests: `get_merge_request`, `list_merge_requests`, `list_mr_notes`, `create_mr_note`
- Issues: `get_gitlab_issue`, `list_gitlab_issues`, `create_gitlab_issue`, `list_issue_notes`, `create_issue_note`
- Pipelines/jobs: `list_pipelines`, `get_pipeline`, `retry_pipeline`, `cancel_pipeline`, `list_pipeline_jobs`, `get_job_log`
- Repository: `list_branches`, `get_branch`, `list_commits`, `get_commit`, `list_repository_tree`, `get_file`
- Releases/tags: `list_releases`, `get_release`, `list_tags`
- Project: `list_project_members`, `list_labels`

### ✅ Confluence Service (`confluence_service.py`)
**Status:** Fully implemented

**Environment Variables:**
- `CONFLUENCE_URL` - Confluence instance URL
- `CONFLUENCE_API_TOKEN` - API token
- `CONFLUENCE_USERNAME` - Username/email
- `CONFLUENCE_VERIFY_SSL` - SSL verification (default: true)

**Tools (7):**
- `get_confluence_page` - Get page content
- `search_confluence_pages` - Search pages
- `get_space` - Get space details
- `list_spaces` - List all spaces
- `get_page_children` - Get child pages
- `get_page_attachments` - List page attachments
- `get_page_comments` - Get page comments

## Adding a New Service

To add a new service integration:

1. **Create the service file:**
   ```bash
   touch src/services/myservice_service.py
   ```

2. **Implement the three required functions:**
   - `init_myservice_client()`
   - `get_myservice_tools()`
   - `handle_myservice_tool_call()`

3. **Export in `__init__.py`:**
   ```python
   from .myservice_service import (
       init_myservice_client,
       get_myservice_tools,
       handle_myservice_tool_call,
   )
   
   __all__ = [
       # ...existing exports...
       "init_myservice_client",
       "get_myservice_tools",
       "handle_myservice_tool_call",
   ]
   ```

4. **Register in main server (`bridge_mcp_server.py`):**
   ```python
   # Import
   from services.myservice_service import (
       init_myservice_client,
       get_myservice_tools,
       handle_myservice_tool_call,
   )
   
   # Initialize in initialize_services()
   myservice_client = init_myservice_client()
   enabled_services["myservice"] = myservice_client is not None
   
   # Add tools in list_tools()
   if enabled_services.get("myservice", False):
       tools.extend(get_myservice_tools())
   
   # Route calls in call_tool()
   myservice_tools = {"tool1", "tool2"}
   if name in myservice_tools:
       return await handle_myservice_tool_call(name, arguments)
   ```

5. **Update `.env.example`:**
   Add environment variables for your service

6. **Update documentation:**
   - Add service to README.md
   - Update this file
   - Add to TOOLS.md

## Best Practices

### Logging
Use the service-specific logger:
```python
logger = logging.getLogger("bridge-mcp.myservice")
```

### Error Handling
Always handle errors gracefully and return TextContent:
```python
try:
    result = do_something()
except SomeError as e:
    logger.error(f"Error: {e}")
    return [TextContent(type="text", text=f"Error: {e}")]
```

### Optional Dependencies
Check for client initialization:
```python
if myservice_client is None:
    return [TextContent(type="text", text="Service not available")]
```

### Environment Variables
Use sensible defaults:
```python
MYSERVICE_URL = os.getenv("MYSERVICE_URL", "https://default-url.com")
MYSERVICE_VERIFY_SSL = os.getenv("MYSERVICE_VERIFY_SSL", "true").lower() in {"true", "1", "yes"}
```

## Testing

Test your service module independently:
```python
# Test client initialization
client = init_myservice_client()
assert client is not None

# Test tool listing
tools = get_myservice_tools()
assert len(tools) > 0

# Test tool execution
import asyncio
result = asyncio.run(handle_myservice_tool_call("tool_name", {"arg": "value"}))
assert len(result) > 0
```

## Dependencies

If your service requires additional Python packages, add them to `requirements.txt`:
```txt
# MyService dependencies
myservice-python-sdk>=1.0.0
```

Then users can install with:
```bash
pip install -r requirements.txt
```

