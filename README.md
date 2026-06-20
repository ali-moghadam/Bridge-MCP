# Bridge-MCP

A unified Model Context Protocol (MCP) server that connects AI assistants to your enterprise tools: **Jira**, **GitLab**, and **Confluence**. Browse issues, merge requests, pipelines, and documentation from a single MCP server.

- **Jira** — issues, JQL search, comments, attachments, inline media
- **GitLab** — projects, merge requests, issues, pipelines, jobs, branches, commits, files, releases, tags, members, labels (two backends: native **GitLab MCP** endpoint or the **`glab` CLI**)
- **Confluence** — pages, spaces, search, child pages, attachments, comments

Works with self-hosted / private / VPN instances (e.g. behind FortiClient), with per-service SSL-verification toggles and Personal Access Token auth.

---

## Requirements

- **Python 3.10+**
- **GitLab backend** (GitLab service only) — pick one via `GITLAB_BACKEND`:
  - `mcp` (default) — connects to your instance's native MCP endpoint (`<GITLAB_URL>/api/v4/mcp`). No extra binary. Tools are exposed dynamically from the instance.
  - `glab` — the [`glab` CLI](https://gitlab.com/gitlab-org/cli) on your `PATH`. The service shells out to `glab`.
  - If the selected backend fails to initialize, GitLab tools are disabled (Jira/Confluence still work). No automatic fallback between backends.

---

## Quick Start

### 1. Install dependencies

```bash
cd /path/to/bridge-mcp
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The default `mcp` backend needs no extra binary. To use the `glab` backend, install the `glab` binary on your `PATH`:

```bash
# macOS
brew install glab
# verify
glab --version
```

### 2. Configure credentials

Copy `.env.example` to `.env` and fill in only the services you use (all are optional):

```env
# --- Jira ---
JIRA_URL=https://your-jira-instance.com
JIRA_PERSONAL_ACCESS_TOKEN=your_jira_pat
JIRA_VERIFY_SSL=true

# --- GitLab ---
GITLAB_BACKEND=mcp                  # mcp (default, native GitLab MCP endpoint) | glab (CLI)
GITLAB_URL=https://your-gitlab-instance.com
GITLAB_PERSONAL_ACCESS_TOKEN=glpat-xxxxx
GITLAB_VERIFY_SSL=true

# --- Confluence ---
CONFLUENCE_URL=https://your-confluence-instance.com
CONFLUENCE_API_TOKEN=your_confluence_api_token
CONFLUENCE_USERNAME=you@company.com
CONFLUENCE_VERIFY_SSL=true
```

**Getting tokens:**
- **Jira**: Settings → Personal Access Tokens
- **GitLab**: User Settings → Access Tokens (scopes: `api`, `read_api`, `read_repository`). The token is used as a Bearer token for the `mcp` backend, and as `GITLAB_TOKEN` for the `glab` backend. With the `glab` backend you may instead run `glab auth login` and omit the token — it falls back to `glab`'s stored credentials.
- **Confluence**: Atlassian Account → Security → API Tokens

> Self-signed certs / private instances: set the relevant `*_VERIFY_SSL=false`.

### 3. Verify setup

```bash
python check_config.py
```

Check that each service is actually reachable with your tokens:

```bash
python test_connectivity.py
```

> The server loads credentials from the project-root `.env` by absolute path, so it works regardless of the working directory your AI assistant launches it from. If you prefer not to use `.env`, pass the same variables via the `env` block of your MCP client config.

Optionally start the server manually (Ctrl+C to stop — your AI assistant launches it automatically):

```bash
python src/bridge_mcp_server.py
```

---

## Add Bridge-MCP to your AI assistant

Credentials are read from `.env` automatically, so the MCP config below only needs the command + path. Replace `/path/to/bridge-mcp` with your absolute path and use the venv's Python (e.g. `/path/to/bridge-mcp/.venv/bin/python`).

### Claude Code (CLI)

**Option A — `claude mcp add` (recommended):**

```bash
claude mcp add bridge-mcp \
  -- /path/to/bridge-mcp/.venv/bin/python \
     /path/to/bridge-mcp/src/bridge_mcp_server.py
```

Scope flags: `-s local` (default, this project only), `-s user` (all your projects), `-s project` (shared `.mcp.json`, committed to the repo).

To pass credentials inline instead of using `.env`, add `-e KEY=value` for each variable.

**Option B — edit JSON manually** (`~/.claude.json`, inside the relevant project block, or a project `.mcp.json`):

```json
{
  "mcpServers": {
    "bridge-mcp": {
      "type": "stdio",
      "command": "/path/to/bridge-mcp/.venv/bin/python",
      "args": ["/path/to/bridge-mcp/src/bridge_mcp_server.py"]
    }
  }
}
```

Verify: `claude mcp list` (expect `bridge-mcp ✓ connected`) or `/mcp` in-session.

### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "bridge-mcp": {
      "command": "/path/to/bridge-mcp/.venv/bin/python",
      "args": ["/path/to/bridge-mcp/src/bridge_mcp_server.py"]
    }
  }
}
```

Restart Claude Desktop.

### GitHub Copilot — JetBrains

Edit `~/.config/github-copilot/intellij/mcp.json`:

```json
{
  "servers": {
    "bridge-mcp": {
      "type": "stdio",
      "command": "/path/to/bridge-mcp/.venv/bin/python",
      "args": ["/path/to/bridge-mcp/src/bridge_mcp_server.py"]
    }
  }
}
```

Restart the IDE.

### GitHub Copilot — VS Code

Add to workspace `.vscode/mcp.json` or user `settings.json` under `"mcp.servers"`:

```json
{
  "servers": {
    "bridge-mcp": {
      "type": "stdio",
      "command": "/path/to/bridge-mcp/.venv/bin/python",
      "args": ["/path/to/bridge-mcp/src/bridge_mcp_server.py"]
    }
  }
}
```

### Gemini CLI

Add to `~/.gemini/settings.json` (global) or `.gemini/settings.json` (project), under `"mcpServers"`:

```json
{
  "mcpServers": {
    "bridge-mcp": {
      "command": "/path/to/bridge-mcp/.venv/bin/python",
      "args": ["/path/to/bridge-mcp/src/bridge_mcp_server.py"]
    }
  }
}
```

Verify with `/mcp` in-session.

### Codex CLI

Edit `~/.codex/config.toml`:

```toml
[mcp_servers.bridge-mcp]
command = "/path/to/bridge-mcp/.venv/bin/python"
args = ["/path/to/bridge-mcp/src/bridge_mcp_server.py"]
```

### Cursor / Windsurf / Cline / other MCP clients

Any MCP-compatible client uses the same stdio launch. Point `command` at the venv Python and `args` at `src/bridge_mcp_server.py`.
- **Cursor:** `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (project), under `"mcpServers"`.
- **Windsurf:** `~/.codeium/windsurf/mcp_config.json`, under `"mcpServers"`.
- **Cline (VS Code):** `cline_mcp_settings.json`, under `"mcpServers"`.

> **Tip:** if your client does not load the project `.env`, pass credentials via an `"env": { ... }` block in the JSON instead.

---

## Usage

Once connected, ask your AI assistant in plain language — it picks the right tool. Examples:

**Jira**
- "Show me Jira issue PROJ-1234 and its comments."
- "Search Jira for open bugs assigned to me in the PAY project."
- "Download the screenshots attached to PROJ-1234."

**GitLab**
- "List open merge requests in group/my-repo."
- "Why did the latest pipeline on `main` fail? Show the failing job log."
- "Show the diff and notes for merge request !57."
- "Open an issue in group/my-repo titled 'Flaky login test'."

**Confluence**
- "Find Confluence pages about the deployment runbook."
- "Summarize the 'Onboarding' page and list its child pages."

To confirm tools are loaded: run `/mcp` in-session (Claude Code, Gemini CLI) or check your client's MCP/tools panel.

---

## Available Tools

### Jira (5)
| Tool | Description |
|---|---|
| `get_jira_issue` | Get details of a specific issue |
| `search_jira_issues` | Search issues with JQL |
| `get_issue_comments` | Get all comments on an issue |
| `get_issue_attachments` | List attachment metadata |
| `get_issue_media` | Download and display inline images |

### GitLab
With the **`glab` backend**, the 28 tools below are exposed. With the default **`mcp` backend**, tools are provided dynamically by your GitLab instance's MCP endpoint, so the exact set and names depend on your instance/version.

glab backend tools:
Projects: `get_gitlab_project`, `list_gitlab_projects`
Merge requests: `get_merge_request`, `list_merge_requests`, `list_mr_notes`, `create_mr_note`
Issues: `get_gitlab_issue`, `list_gitlab_issues`, `create_gitlab_issue`, `list_issue_notes`, `create_issue_note`
Pipelines/jobs: `list_pipelines`, `get_pipeline`, `retry_pipeline`, `cancel_pipeline`, `list_pipeline_jobs`, `get_job_log`
Repository: `list_branches`, `get_branch`, `list_commits`, `get_commit`, `list_repository_tree`, `get_file`
Releases/tags: `list_releases`, `get_release`, `list_tags`
Project: `list_project_members`, `list_labels`

### Confluence (7)
| Tool | Description |
|---|---|
| `get_confluence_page` | Get page content |
| `search_confluence_pages` | Search pages (CQL/text) |
| `get_space` | Get space details |
| `list_spaces` | List all spaces |
| `get_page_children` | Get child pages |
| `get_page_attachments` | List page attachments |
| `get_page_comments` | Get page comments |

See [TOOLS.md](TOOLS.md) for full parameter docs.

---

## Troubleshooting

**"No tools available" / service disabled**
- Ensure `.env` exists in the project root and the relevant credentials are set.
- GitLab (`mcp` backend): confirm `<GITLAB_URL>/api/v4/mcp` is reachable and `GITLAB_PERSONAL_ACCESS_TOKEN` is valid.
- GitLab (`glab` backend): confirm `glab --version` works and you are authenticated (`glab auth status` or a valid `GITLAB_PERSONAL_ACCESS_TOKEN`).
- Python 3.10+: `python --version`. Dependencies: `pip install -r requirements.txt`.

**401 Unauthorized / connection failed**
- Connect your VPN (private instances), verify tokens, confirm browser access.

**SSL certificate error**
- Set `JIRA_VERIFY_SSL=false` / `GITLAB_VERIFY_SSL=false` / `CONFLUENCE_VERIFY_SSL=false`.

**Wrong Python**
- Use the venv interpreter (`/path/to/bridge-mcp/.venv/bin/python`), not the system/anaconda one, so installed deps are visible.

---

## License
MIT
</content>
</invoke>