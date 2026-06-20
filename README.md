# Bridge-MCP

A unified Model Context Protocol (MCP) server connecting AI assistants to **Jira**, **GitLab**, and **Confluence** — issues, merge requests, pipelines, and docs from one server.

- **Jira** — issues, JQL search, comments, attachments, inline media
- **GitLab** — projects, MRs, issues, pipelines, repo, releases (via your instance's native GitLab MCP endpoint, GitLab 18.x+)
- **Confluence** — pages, spaces, search, child pages, attachments, comments

Works with self-hosted / private / VPN instances; per-service SSL toggle and Personal Access Token auth.

---

## Use it (hosted)

The server runs in the cluster and is reached by URL ([how to deploy](#deployment)).

- **URL:** `https://bridge-mcp-baly-internal.apps.private.okd4.teh-1.snappcloud.io/mcp`
- **Auth:** header `Authorization: Bearer <token>`
- Requires VPN (e.g. FortiClient) for private instances.

> All callers share the server-side identity — every request uses the deployer's Jira/GitLab/Confluence tokens.

**Claude Code**
```bash
claude mcp add --transport http bridge-mcp <url> --header "Authorization: Bearer <token>"
```

**Claude Desktop** (bridge the URL with `mcp-remote`)
```json
{ "mcpServers": { "bridge-mcp": {
  "command": "npx",
  "args": ["-y", "mcp-remote", "<url>", "--header", "Authorization: Bearer <token>"]
}}}
```

**VS Code / Cursor / Copilot**
```json
{ "servers": { "bridge-mcp": {
  "type": "http", "url": "<url>", "headers": { "Authorization": "Bearer <token>" }
}}}
```

**Gemini CLI** (`~/.gemini/settings.json`)
```json
{ "mcpServers": { "bridge-mcp": {
  "httpUrl": "<url>", "headers": { "Authorization": "Bearer <token>" }
}}}
```

**Codex CLI** (`~/.codex/config.toml`)
```toml
[mcp_servers.bridge-mcp]
url = "<url>"
http_headers = { Authorization = "Bearer <token>" }
```

Confirm tools loaded: `/mcp` in-session, or your client's tools panel.

---

## Usage

Ask in plain language — the assistant picks the tool:

- "Show Jira issue PROJ-1234 and its comments."
- "Search Jira for open bugs assigned to me in PAY."
- "Why did the latest pipeline on `main` fail? Show the failing job log."
- "Show the diff and notes for merge request !57."
- "Find Confluence pages about the deployment runbook."

---

## Tools

- **Jira (5):** `get_jira_issue`, `search_jira_issues`, `get_issue_comments`, `get_issue_attachments`, `get_issue_media`
- **GitLab:** dynamic — provided by your instance's MCP endpoint (projects, MRs, issues, pipelines/jobs, repo, releases/tags, members, labels). Run `/mcp` to see your set.
- **Confluence (7):** `get_confluence_page`, `search_confluence_pages`, `get_space`, `list_spaces`, `get_page_children`, `get_page_attachments`, `get_page_comments`

Full parameter docs: [TOOLS.md](TOOLS.md).

---

## Deployment

Container serving streamable-HTTP (`src/http_server.py`, port `8080`, endpoint `/mcp`, health `/healthz` `/readyz`). Deployed to OKD namespace `baly-internal` via Helm + GitLab CI.

1. **Setup** — push repo to the internal GitLab (with OKD runners); set masked CI/CD vars: `BUILDER_TOKEN`, `BRIDGE_MCP_AUTH_TOKEN`, `JIRA_PAT`, `GITLAB_PAT`, `CONFLUENCE_TOKEN`. Service URLs live in `helm/bridge-mcp/values-staging.yaml`.
2. **Deploy** — run pipeline jobs in order: `push:staging` → `helm_publish:staging` → `deploy:staging`. Tokens injected via `--set-string` (no secret committed).
3. **Result** — the OpenShift Route publishes the [URL above](#use-it-hosted).

Container env vars: `BRIDGE_MCP_AUTH_TOKEN` (gates `/mcp`), `JIRA_*`, `GITLAB_*`, `CONFLUENCE_*`, `PORT`. Empty token = that service disabled.

---

## Local development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in the services you use
python test_connectivity.py   # check reachability
```

Tokens: Jira → Settings → Personal Access Tokens · GitLab → Access Tokens (`api`, `read_api`, `read_repository`) · Confluence → Atlassian API Tokens. Self-signed certs: set `*_VERIFY_SSL=false`.

Run over **stdio** (local MCP clients launch this automatically):
```json
{ "mcpServers": { "bridge-mcp": {
  "command": "/path/to/bridge-mcp/.venv/bin/python",
  "args": ["/path/to/bridge-mcp/src/bridge_mcp_server.py"]
}}}
```
Claude Code shortcut: `claude mcp add bridge-mcp -- /path/to/.venv/bin/python /path/to/src/bridge_mcp_server.py`.

Run over **HTTP** locally: `BRIDGE_MCP_AUTH_TOKEN=secret PORT=8080 PYTHONPATH=src python src/http_server.py`.

---

## Troubleshooting

- **Service disabled / no tools** — credentials set? GitLab needs `<GITLAB_URL>/api/v4/mcp` reachable + GitLab 18.x+.
- **401 / connection failed** — VPN connected, token valid, `Authorization: Bearer` header present (hosted).
- **SSL error** — set `*_VERIFY_SSL=false`.

## License
MIT
