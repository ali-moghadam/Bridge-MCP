#!/bin/bash

# Setup script for Bridge-MCP

echo "Setting up Bridge-MCP..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.8 or later."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file from example if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env 2>/dev/null || touch .env
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env file and add your service credentials:"
    echo "   For Jira:"
    echo "   - JIRA_URL (your Jira instance URL)"
    echo "   - JIRA_PERSONAL_ACCESS_TOKEN"
    echo ""
    echo "   For GitLab (coming soon):"
    echo "   - GITLAB_URL"
    echo "   - GITLAB_PERSONAL_ACCESS_TOKEN"
    echo ""
    echo "   For Confluence (coming soon):"
    echo "   - CONFLUENCE_URL"
    echo "   - CONFLUENCE_API_TOKEN"
fi

echo ""
echo "✅ Bridge-MCP setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your service credentials"
echo "2. Connect to your VPN (FortiClient or similar) if needed"
echo "3. Run the server: python src/bridge_mcp_server.py"
echo "4. Configure Claude Desktop or GitHub Copilot (see README.md)"
echo ""

