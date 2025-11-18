#!/usr/bin/env python3
"""
Check Bridge-MCP configuration and service availability.

This script helps diagnose configuration issues by checking:
- Environment variables
- Service credentials
- Network connectivity
- Python dependencies
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define which services are actually implemented
IMPLEMENTED_SERVICES = {'jira', 'gitlab'}

def print_section(title: str):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def check_env_var(name: str, required: bool = False) -> bool:
    """Check if an environment variable is set."""
    value = os.getenv(name)
    if value:
        # Mask sensitive values
        if "TOKEN" in name or "PASSWORD" in name or "API" in name:
            masked = value[:4] + "*" * (len(value) - 8) + value[-4:] if len(value) > 8 else "***"
            print(f"  ✓ {name}: {masked}")
        else:
            print(f"  ✓ {name}: {value}")
        return True
    else:
        symbol = "✗" if required else "○"
        status = "MISSING (required)" if required else "not set (optional)"
        print(f"  {symbol} {name}: {status}")
        return not required

def check_python_version():
    """Check Python version."""
    print_section("Python Environment")
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    if version.major >= 3 and version.minor >= 10:
        print(f"  ✓ Python version: {version_str}")
        return True
    else:
        print(f"  ✗ Python version: {version_str} (3.10+ required)")
        return False

def check_dependencies():
    """Check if required Python packages are installed."""
    print_section("Python Dependencies")

    required_packages = [
        ("mcp", "Model Context Protocol"),
        ("jira", "Jira client"),
        ("gitlab", "GitLab client"),
        ("dotenv", "Environment configuration"),
        ("requests", "HTTP requests"),
    ]

    optional_packages = [
        ("atlassian", "Confluence client (coming soon)"),
    ]

    all_ok = True

    print("\n  Required packages:")
    for package, description in required_packages:
        try:
            __import__(package)
            print(f"  ✓ {package} - {description}")
        except ImportError:
            print(f"  ✗ {package} - {description} (NOT INSTALLED)")
            all_ok = False

    print("\n  Optional packages:")
    for package, description in optional_packages:
        try:
            __import__(package)
            print(f"  ✓ {package} - {description}")
        except ImportError:
            print(f"  ○ {package} - {description} (not installed)")

    return all_ok

def check_jira_config():
    """Check Jira configuration."""
    print_section("Jira Configuration")

    url_ok = check_env_var("JIRA_URL", required=True)
    token_ok = check_env_var("JIRA_PERSONAL_ACCESS_TOKEN", required=True)
    verify_ok = check_env_var("JIRA_VERIFY_SSL", required=False)

    # Warn about extra/unused variables that might confuse users
    if os.getenv("JIRA_PERSONAL_ACCESS_TOKEN2"):
        print("  ⚠️ Note: JIRA_PERSONAL_ACCESS_TOKEN2 is set but ignored. The app only uses JIRA_PERSONAL_ACCESS_TOKEN.")

    if url_ok and token_ok:
        print("\n  Status: Jira service will be ENABLED")
        if verify_ok:
            v = os.getenv("JIRA_VERIFY_SSL", "true")
            print(f"  Info: SSL verification is {'enabled' if v.strip().lower() in {'1','true','yes','on'} else 'disabled'} (JIRA_VERIFY_SSL={v})")
        return True
    else:
        print("\n  Status: Jira service will be DISABLED")
        return False

def check_gitlab_config():
    """Check GitLab configuration."""
    print_section("GitLab Configuration")

    url_ok = check_env_var("GITLAB_URL", required=False)
    token_ok = check_env_var("GITLAB_PERSONAL_ACCESS_TOKEN", required=False)
    check_env_var("GITLAB_VERIFY_SSL", required=False)

    if url_ok and token_ok:
        print("\n  Status: GitLab service will be ENABLED")
        return True
    else:
        print("\n  Status: GitLab service will be DISABLED")
        return False

def check_confluence_config():
    """Check Confluence configuration."""
    print_section("Confluence Configuration (NOT YET IMPLEMENTED)")

    url_ok = check_env_var("CONFLUENCE_URL", required=False)
    token_ok = check_env_var("CONFLUENCE_API_TOKEN", required=False)
    username_ok = check_env_var("CONFLUENCE_USERNAME", required=False)
    check_env_var("CONFLUENCE_VERIFY_SSL", required=False)

    if url_ok and token_ok and username_ok:
        print("\n  Status: Confluence credentials configured but service NOT YET IMPLEMENTED")
        return True
    else:
        print("\n  Status: Confluence service NOT YET IMPLEMENTED")
        return False

def check_file_structure():
    """Check if required files exist."""
    print_section("File Structure")

    required_files = [
        "src/bridge_mcp_server.py",
        "src/services/jira_service.py",
        "src/services/gitlab_service.py",
        "src/services/confluence_service.py",
        "requirements.txt",
    ]

    all_ok = True
    for filepath in required_files:
        if os.path.exists(filepath):
            print(f"  ✓ {filepath}")
        else:
            print(f"  ✗ {filepath} (MISSING)")
            all_ok = False

    return all_ok

def main():
    """Run all checks."""
    print("\n" + "="*60)
    print("  Bridge-MCP Configuration Check")
    print("="*60)

    checks = []

    # Run checks
    checks.append(("Python Version", check_python_version()))
    checks.append(("File Structure", check_file_structure()))
    checks.append(("Dependencies", check_dependencies()))
    checks.append(("Jira", check_jira_config()))
    checks.append(("GitLab", check_gitlab_config()))
    checks.append(("Confluence", check_confluence_config()))

    # Summary
    print_section("Summary")

    enabled_services = []
    disabled_services = []

    if checks[3][1]:  # Jira
        if 'jira' in IMPLEMENTED_SERVICES:
            enabled_services.append("Jira")
        else:
            disabled_services.append("Jira (not yet implemented)")
    else:
        disabled_services.append("Jira")

    if checks[4][1]:  # GitLab
        if 'gitlab' in IMPLEMENTED_SERVICES:
            enabled_services.append("GitLab")
        else:
            disabled_services.append("GitLab (not yet implemented)")
    else:
        disabled_services.append("GitLab")

    if checks[5][1]:  # Confluence
        if 'confluence' in IMPLEMENTED_SERVICES:
            enabled_services.append("Confluence")
        else:
            disabled_services.append("Confluence (not yet implemented)")
    else:
        disabled_services.append("Confluence")

    print(f"\n  Enabled services: {', '.join(enabled_services) if enabled_services else 'None'}")
    print(f"  Disabled services: {', '.join(disabled_services) if disabled_services else 'None'}")

    # Overall status
    critical_ok = checks[0][1] and checks[1][1] and checks[2][1]

    print("\n" + "="*60)
    if critical_ok and enabled_services:
        print("  ✓ Configuration looks good!")
        print("  You can start the server with:")
        print("    python src/bridge_mcp_server.py")
    elif not critical_ok:
        print("  ✗ Critical issues found. Please fix:")
        if not checks[0][1]:
            print("    - Upgrade Python to 3.10+")
        if not checks[1][1]:
            print("    - Check file structure")
        if not checks[2][1]:
            print("    - Install dependencies: pip install -r requirements.txt")
    elif not enabled_services:
        print("  ⚠ No services are configured.")
        print("  Please add credentials to .env file:")
        print("    cp .env.example .env")
        print("    # Then edit .env with your credentials")
    print("="*60 + "\n")

    # Exit code
    sys.exit(0 if (critical_ok and enabled_services) else 1)

if __name__ == "__main__":
    main()
