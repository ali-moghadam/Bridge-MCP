# Bridge-MCP

A unified Model Context Protocol (MCP) server that provides seamless integration with enterprise tools including Jira, GitLab, and Confluence. Access your project management, code repositories, and documentation from a single interface.

## Overview

Bridge-MCP is designed to work in private/VPN environments (like FortiClient), making it easy to connect AI assistants like Claude and GitHub Copilot to your enterprise tools.

### Supported Integrations

#### Jira (Available Now)
- Fetch issue details by key
- Search issues using JQL
- Get issue comments and attachments
- View inline images from issues

#### GitLab (Coming Soon)
- Repository management
- Merge request tracking
- Pipeline status

#### Confluence (Coming Soon)
- Page content retrieval
- Space browsing
- Documentation search

## Architecture

Bridge-MCP uses a modular architecture where each service (Jira, GitLab, Confluence) is implemented as a separate module:

```
src/
├── bridge_mcp_server.py       # Main unified MCP server
└── services/
    ├── jira_service.py        # Jira integration (available now)
    ├── gitlab_service.py      # GitLab integration (coming soon)
    └── confluence_service.py  # Confluence integration (coming soon)
```

**Benefits:**
- **Modular**: Each service is independent and can be enabled/disabled
- **Scalable**: Easy to add new services
- **Maintainable**: Changes to one service don't affect others
- **Flexible**: Use one service or all three simultaneously

## Requirements
- Python 3.10+
- VPN connection (FortiClient or similar) if accessing private instances
- Authentication credentials for the services you want to use:
  - Jira: Personal Access Token (PAT) with read permissions
  - GitLab: Personal Access Token (coming soon)
  - Confluence: API Token (coming soon)

## Installation
```bash
# (optional) create a venv
python -m venv .venv
source .venv/bin/activate

# install dependencies
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root with your service credentials. You can copy the template:

```bash
cp .env.example .env
# Then edit .env with your actual credentials
```

Each service is optional - configure only the services you want to use:

### Jira Configuration
```env
JIRA_URL=https://your-jira-instance.com
JIRA_PERSONAL_ACCESS_TOKEN=your_pat_here
JIRA_VERIFY_SSL=true
```

### GitLab Configuration (Coming Soon)
```env
GITLAB_URL=https://your-gitlab-instance.com
GITLAB_PERSONAL_ACCESS_TOKEN=your_token_here
GITLAB_VERIFY_SSL=true
```

### Confluence Configuration (Coming Soon)
```env
CONFLUENCE_URL=https://your-confluence-instance.com
CONFLUENCE_API_TOKEN=your_token_here
CONFLUENCE_VERIFY_SSL=true
```

**Security Note:**
- Do not commit `.env` to version control
- All integrations use token-based authentication (no username/password)

## Usage

### Check Configuration
Before starting the server, verify your configuration:
```bash
python check_config.py
```

This will check:
- Python version and dependencies
- Environment variables and credentials
- Which services will be enabled
- File structure integrity

### Run Connection Tests
```bash
source .venv/bin/activate
python test_connection.py  # Test Jira connection (if available)
```

### Run the MCP Server
```bash
source .venv/bin/activate
python src/bridge_mcp_server.py
```

The server will start and wait for MCP client connections (Claude Desktop, GitHub Copilot, etc.)

**Note:** The server will automatically detect and enable services based on available credentials in your `.env` file. You can use one, two, or all three services simultaneously.

## Integration with AI Assistants

### Claude Desktop Setup

Configure Claude Desktop on macOS by editing `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "bridge-mcp": {
      "command": "python",
      "args": ["/path/to/Bridge-MCP/src/bridge_mcp_server.py"],
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

**Tips:**
- Replace `/path/to/Bridge-MCP` with your actual installation path
- You can set `JIRA_PERSONAL_ACCESS_TOKEN` globally in your shell profile instead of the config
- Restart Claude Desktop after configuration changes

### GitHub Copilot Setup (JetBrains IDEs)

For GitHub Copilot in JetBrains IDEs (IntelliJ, PyCharm, etc.), edit `~/.config/github-copilot/intellij/mcp.json`:
```json
{
  "servers": {
    "bridge-mcp": {
      "type": "stdio",
      "command": "/path/to/Bridge-MCP/.venv/bin/python3",
      "args": [
        "/path/to/Bridge-MCP/src/bridge_mcp_server.py"
      ],
      "env": {
        "JIRA_URL": "https://your-jira-instance.com",
        "JIRA_PERSONAL_ACCESS_TOKEN": "your_personal_access_token_here",
        "JIRA_VERIFY_SSL": "true",
        "GITLAB_URL": "https://gitlab.com",
        "GITLAB_PERSONAL_ACCESS_TOKEN": "your_gitlab_token_here",
        "CONFLUENCE_URL": "https://your-confluence-instance.com",
        "CONFLUENCE_API_TOKEN": "your_confluence_token_here",
        "CONFLUENCE_USERNAME": "your_email@company.com"
      }
    }
  }
}
```

**Example with actual paths** (macOS):
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
        "JIRA_PERSONAL_ACCESS_TOKEN": "your_personal_access_token_here",
        "JIRA_VERIFY_SSL": "true"
      }
    }
  }
}
```

After configuring, restart your JetBrains IDE to use Bridge-MCP with GitHub Copilot.

## Available Tools

### Jira Tools
1. **get_jira_issue** — Get detailed information about a specific issue
2. **search_jira_issues** — Search issues using JQL queries
3. **get_issue_comments** — Retrieve all comments on an issue
4. **get_issue_attachments** — List all attachments metadata
5. **get_issue_media** — Download and display inline images from issues

### GitLab Tools (Coming Soon)
- Repository information
- Merge request details
- Pipeline status

### Confluence Tools (Coming Soon)
- Page content retrieval
- Space navigation
- Document search

## Troubleshooting

### Common Issues

**401 Unauthorized**
- Your authentication token is invalid or expired
- Generate a new token and update `.env`

**SSL Certificate Errors**
- Set `*_VERIFY_SSL=false` in `.env` (use only if necessary for self-signed certificates)
- Example: `JIRA_VERIFY_SSL=false`

**Network Connection Errors**
- Ensure your VPN (FortiClient or similar) is connected
- Verify the service URLs are correct in `.env`
- Check that you can access the services in your web browser

**Server Not Starting**
- Verify all required dependencies are installed: `pip install -r requirements.txt`
- Check that your Python version is 3.10 or higher: `python --version`
- Ensure `.env` file has correct configuration

### Getting Help
- Check the logs for detailed error messages
- Verify your credentials work by accessing the web interfaces directly
- See [TOOLS.md](TOOLS.md) for detailed documentation on available tools

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
