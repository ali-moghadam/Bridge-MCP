# Bridge-MCP

A unified Model Context Protocol (MCP) server that provides seamless integration with enterprise tools including Jira, GitLab, and Confluence. Access your project management, code repositories, and documentation from a single interface.

## What Does It Do?

Bridge-MCP connects AI assistants (Claude, GitHub Copilot) to your enterprise tools:

- **Jira**: Search issues, view details, get comments and attachments
- **GitLab**: Browse projects, merge requests, pipelines, and issues
- **Confluence**: Coming soon

Works with private/VPN instances (like FortiClient).

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Your Credentials

Create a `.env` file in the project root:

```env
# Jira (Optional)
JIRA_URL=https://your-jira-instance.com
JIRA_PERSONAL_ACCESS_TOKEN=your_jira_token

# GitLab (Optional)
GITLAB_URL=https://your-gitlab-instance.com
GITLAB_PERSONAL_ACCESS_TOKEN=your_gitlab_token
```

**Getting Your Tokens:**
- **Jira**: Settings > Personal Access Tokens
- **GitLab**: User Settings > Access Tokens (needs `api`, `read_api`, `read_repository` scopes)

**Note:** Configure only the services you want to use. Both are optional.

### 3. Verify Your Setup

Run the configuration checker to ensure everything is set up correctly:

```bash
python check_config.py
```

This will verify:
- ✓ Python version and dependencies
- ✓ Environment variables are set correctly
- ✓ Which services will be enabled
- ✓ File structure is correct

If you see "✓ Configuration looks good!", you're ready to proceed.

### 4. Verify the Server Works (Optional)

You can optionally verify the server starts correctly:

```bash
python src/bridge_mcp_server.py
```

The server will start and you should see:
```
INFO - Initializing Bridge-MCP services...
INFO - ✓ Jira service enabled
INFO - ✓ GitLab service enabled
INFO - Bridge-MCP initialized with 2/3 service(s) enabled
INFO - Bridge-MCP Server starting...
```

**Press Ctrl+C to stop.** This is just for verification - your AI assistant will automatically start/stop the server when needed. You don't need to keep it running.

### 5. Connect to Your AI Assistant

Now configure your AI assistant to use Bridge-MCP.

**Choose your AI assistant below:**

## Setup for Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "bridge-mcp": {
      "command": "python",
      "args": ["/FULL/PATH/TO/bridge-mcp/src/bridge_mcp_server.py"]
    }
  }
}
```

**Important:** 
- Replace `/FULL/PATH/TO/bridge-mcp` with your actual path (e.g., `/Users/yourname/bridge-mcp`)
- The server will read credentials from your `.env` file automatically
- Restart Claude Desktop after saving

That's it! Claude will now have access to your Jira and GitLab data.

## Setup for GitHub Copilot (JetBrains)

Edit `~/.config/github-copilot/intellij/mcp.json`:

```json
{
  "servers": {
    "bridge-mcp": {
      "type": "stdio",
      "command": "/Users/YOUR_USERNAME/Bridge-MCP/.venv/bin/python3",
      "args": [
        "/Users/YOUR_USERNAME/Bridge-MCP/src/bridge_mcp_server.py"
      ],
      "env": {
        "JIRA_URL": "https://your-jira-instance.com",
        "JIRA_PERSONAL_ACCESS_TOKEN": "${env:JIRA_PERSONAL_ACCESS_TOKEN}",
        "JIRA_VERIFY_SSL": "true",
        "GITLAB_URL": "https://gitlab.com",
        "GITLAB_PERSONAL_ACCESS_TOKEN": "${env:GITLAB_PERSONAL_ACCESS_TOKEN}",
        "CONFLUENCE_URL": "https://your-confluence-instance.com",
        "CONFLUENCE_API_TOKEN": "${env:CONFLUENCE_API_TOKEN}",
        "CONFLUENCE_USERNAME": "${env:CONFLUENCE_USERNAME}"
      }
    }
  }
}
```

**Important:**
- Replace `/FULL/PATH/TO/bridge-mcp` with your actual path (e.g., `/Users/yourname/bridge-mcp`)
- The server will read credentials from your `.env` file automatically
- Restart your IDE after saving

## Available Tools

### Jira Tools
1. **get_jira_issue** — Get detailed information about a specific issue
2. **search_jira_issues** — Search issues using JQL queries
3. **get_issue_comments** — Retrieve all comments on an issue
4. **get_issue_attachments** — List all attachments metadata
5. **get_issue_media** — Download and display inline images from issues

### GitLab Tools
1. **get_gitlab_project** — Get detailed information about a project by ID or path
2. **list_gitlab_projects** — List and search accessible projects
3. **get_merge_request** — Get detailed information about a specific merge request
4. **list_merge_requests** — List merge requests for a project (opened, closed, merged, or all)
5. **list_pipelines** — List CI/CD pipelines for a project with status filtering
6. **get_pipeline** — Get detailed information about a specific pipeline including jobs
7. **list_gitlab_issues** — List issues for a GitLab project
8. **get_gitlab_issue** — Get detailed information about a specific GitLab issue

### Confluence Tools (Coming Soon)
- Page content retrieval
- Space navigation
- Document search

## Troubleshooting

**"Connection failed" or "401 Unauthorized"**
- Check your VPN is connected (for private instances)
- Verify your tokens in `.env` are correct
- Make sure you can access Jira/GitLab in your browser

**"SSL Certificate Error"**
Add to your `.env`:
```env
JIRA_VERIFY_SSL=false
GITLAB_VERIFY_SSL=false
```

**"No tools available"**
- Ensure `.env` file exists in the bridge-mcp directory
- Check you have Python 3.10+ installed: `python --version`
- Verify dependencies are installed: `pip install -r requirements.txt`

**For detailed tool documentation**, see [TOOLS.md](TOOLS.md)

## Extending Bridge-MCP

Want to add support for another service? The modular architecture makes it easy!

### Adding a New Service

1. **Create service module:** `src/services/your_service.py`
2. **Implement three functions:**
   - `init_your_service_client()` - Initialize the client
   - `get_your_service_tools()` - Return list of Tool definitions
   - `handle_your_service_tool_call()` - Handle tool executions
3. **Import in main server:** Add imports to `src/bridge_mcp_server.py`
4. **Register in server:** Add initialization and routing in main server

See existing service modules (e.g., `services/jira_service.py`) as templates.

## Contributing

Contributions are welcome! Please feel free to submit pull requests for:
- Bug fixes
- New features
- Documentation improvements
- Additional service integrations

## License
MIT
