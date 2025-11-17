# MCP Jira Server

A Model Context Protocol (MCP) server that provides read-only access to Jira issues in a private Jira instance (designed for VPN environments like FortiClient).

## Features
- Fetch Jira issue details by key (e.g., BAL-7437)
- Search for Jira issues using JQL
- Get issue comments
- Get issue attachments

## Requirements
- Python 3.10+
- FortiClient VPN connected (or otherwise routable to your Jira)
- Jira Personal Access Token (PAT) with read permissions

## Installation
```bash
# (optional) create a venv
python -m venv .venv
source .venv/bin/activate

# install dependencies
pip install -r requirements.txt
```

## Configuration
Create or update `.env` in the project root:
```env
JIRA_URL=https://your-jira-instance.com
JIRA_PERSONAL_ACCESS_TOKEN=your_pat_here
JIRA_VERIFY_SSL=true
```
Security note:
- Do not commit `.env` to version control.
- Uses a Personal Access Token; username/password are not used.

## Run tests
```bash
source .venv/bin/activate
python test_connection.py
```

## Run the MCP server
```bash
source .venv/bin/activate
python src/mcp_jira_server.py
```

## Using with Claude Desktop / GitHub Copilot

📖 **See [COPILOT_SETUP.md](COPILOT_SETUP.md) for detailed setup instructions and usage examples.**

### Claude Desktop Setup

Quick setup for Claude Desktop on macOS - edit `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "jira": {
      "command": "python",
      "args": ["/path/to/MCP-Jira/src/mcp_jira_server.py"],
      "env": {
        "JIRA_URL": "https://your-jira-instance.com",
        "JIRA_PERSONAL_ACCESS_TOKEN": "${env:JIRA_PERSONAL_ACCESS_TOKEN}",
        "JIRA_VERIFY_SSL": "true"
      }
    }
  }
}
```
Tip: You can also set `JIRA_PERSONAL_ACCESS_TOKEN` globally in your shell profile instead of the Claude config.

### GitHub Copilot Setup (JetBrains IDEs)

For GitHub Copilot in JetBrains IDEs (IntelliJ, PyCharm, etc.), edit `~/.config/github-copilot/intellij/mcp.json`:
```json
{
  "servers": {
    "jira": {
      "type": "stdio",
      "command": "/path/to/your/.venv/bin/python3",
      "args": [
        "/path/to/your/MCP-Jira/src/mcp_jira_server.py"
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

**Important**: Replace `/path/to/your/.venv/bin/python3` with the actual path to your Python virtual environment, and `/path/to/your/MCP-Jira/src/mcp_jira_server.py` with the actual path to the server script.

Example with actual paths (replace with your own):
```json
{
  "servers": {
    "jira": {
      "type": "stdio",
      "command": "/Users/YOUR_USERNAME/path/to/MCP-Jira/.venv/bin/python3",
      "args": [
        "/Users/YOUR_USERNAME/path/to/MCP-Jira/src/mcp_jira_server.py"
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

After configuring, restart your JetBrains IDE and you can use GitHub Copilot to interact with Jira issues directly in your editor.

## Available Tools
1. get_jira_issue — Get details of a specific issue by key
2. search_jira_issues — Search issues via JQL
3. get_issue_comments — List comments on an issue
4. get_issue_attachments — List attachments on an issue

## Troubleshooting
- 401 Unauthorized: PAT invalid or expired → generate a new PAT and update `.env`.
- SSL errors: set `JIRA_VERIFY_SSL=false` in `.env` (use only if necessary).
- Network errors: ensure FortiClient VPN is connected and your Jira instance is reachable.

## License
MIT
