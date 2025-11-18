#!/usr/bin/env python3
"""Quick test to verify all tools are registered correctly."""

import asyncio
from dotenv import load_dotenv
load_dotenv()

import sys
sys.path.insert(0, 'src')

from bridge_mcp_server import initialize_services, list_tools

async def main():
    # Initialize services
    initialize_services()

    # Get tools
    tools = await list_tools()

    print(f"\n{'='*60}")
    print(f"Total Tools Available: {len(tools)}")
    print(f"{'='*60}\n")

    # Group by service
    jira_tools = [t for t in tools if 'jira' in t.name or 'issue' in t.name]
    gitlab_tools = [t for t in tools if 'gitlab' in t.name or 'merge' in t.name or 'pipeline' in t.name]

    print("JIRA TOOLS:")
    for tool in jira_tools:
        print(f"  ✓ {tool.name}")

    print(f"\nGITLAB TOOLS:")
    for tool in gitlab_tools:
        print(f"  ✓ {tool.name}")

    print(f"\n{'='*60}")
    print(f"Summary: {len(jira_tools)} Jira tools, {len(gitlab_tools)} GitLab tools")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    asyncio.run(main())

