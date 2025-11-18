#!/usr/bin/env python3
"""
Test MCP service connections (GitLab, Jira, Confluence).

This script tests authentication for all services configured in bridge_mcp_server.py
by attempting to connect and checking for 401 errors.
"""

import os
import sys
from typing import Tuple
from dotenv import load_dotenv

# Safe import of requests at module level
try:
    import requests  # type: ignore
except Exception:
    requests = None  # type: ignore

# Load environment variables
load_dotenv()


def print_header(text: str):
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")


def mask_token(token: str | None, show: int = 4) -> str:
    if not token:
        return "NOT SET"
    if len(token) <= show:
        return "*" * len(token)
    return f"{'*' * (len(token) - show)}{token[-show:]}"


def test_gitlab_connection() -> Tuple[bool, str]:
    """Test GitLab connection using GITLAB_URL and GITLAB_PERSONAL_ACCESS_TOKEN"""
    print_header("Testing GitLab Connection")

    url = os.getenv("GITLAB_URL", "https://gitlab.com")
    token = os.getenv("GITLAB_PERSONAL_ACCESS_TOKEN")

    print(f"📍 GitLab URL: {url}")
    print(f"🔑 Token: {mask_token(token)}")

    if not token:
        return False, "❌ FAILURE: GITLAB_PERSONAL_ACCESS_TOKEN not set"

    if requests is None:
        return False, "❌ FAILURE: requests library not installed"

    try:
        # Test authentication with /api/v4/user endpoint
        response = requests.get(
            f"{url.rstrip('/')}/api/v4/user",
            headers={"PRIVATE-TOKEN": token},
            timeout=10
        )

        if response.status_code == 401:
            return False, "❌ FAILURE: Authentication failed (401 Unauthorized)"
        elif response.status_code == 200:
            try:
                user_data = response.json()
            except Exception:
                return False, "❌ FAILURE: Non-JSON response from GitLab API"
            username = user_data.get("username", "Unknown")
            return True, f"✅ SUCCESS: Connected as {username}"
        else:
            return False, f"❌ FAILURE: Unexpected status code {response.status_code}"

    except requests.exceptions.Timeout:
        return False, f"❌ FAILURE: Connection timeout to {url}"
    except requests.exceptions.ConnectionError:
        return False, f"❌ FAILURE: Cannot reach {url}"
    except Exception as e:
        return False, f"❌ FAILURE: {str(e)}"


def test_jira_connection() -> Tuple[bool, str]:
    """Test Jira connection using JIRA_URL and JIRA_PERSONAL_ACCESS_TOKEN"""
    print_header("Testing Jira Connection")

    url = os.getenv("JIRA_URL")
    token = os.getenv("JIRA_PERSONAL_ACCESS_TOKEN")
    verify_ssl = os.getenv("JIRA_VERIFY_SSL", "true").strip().lower() in {"1", "true", "yes", "on"}

    print(f"📍 Jira URL: {url or 'NOT SET'}")
    print(f"🔑 Token: {mask_token(token)}")

    if not url:
        return False, "❌ FAILURE: JIRA_URL not set"
    if not token:
        return False, "❌ FAILURE: JIRA_PERSONAL_ACCESS_TOKEN not set"

    if requests is None:
        return False, "❌ FAILURE: requests library not installed"

    # Check for placeholder values
    if "your-jira-instance" in (url or "").lower() or "your_jira" in (token or "").lower():
        return False, "❌ FAILURE: Using placeholder values from .env.example"

    # Suggest HTTPS if using HTTP
    if url and url.startswith("http://"):
        print(f"\n  ⚠️ Note: Using HTTP. Your server may redirect to HTTPS.")
        print(f"  Consider updating JIRA_URL to: {url.replace('http://', 'https://')}")

    try:
        def get_json(endpoint: str, name: str) -> Tuple[bool, str]:
            full_url = f"{url.rstrip('/')}{endpoint}"
            print(f"\n  Testing {name}: {endpoint}")

            try:
                response = requests.get(
                    full_url,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/json",
                    },
                    timeout=10,
                    allow_redirects=True,  # Follow http->https redirects
                    verify=verify_ssl,
                )
            except requests.exceptions.SSLError as e:
                return False, f"  SSL error: {e} (set JIRA_VERIFY_SSL=false to skip verification)"

            status = response.status_code

            # Check if we were redirected (protocol upgrade is OK, but login redirect is not)
            if response.history:
                original_url = response.history[0].url
                final_url = response.url
                print(f"  Redirected: {original_url} -> {final_url}")

                # Detect redirects to login pages (common auth failure pattern)
                if any(pattern in final_url.lower() for pattern in ['/login', '/auth', '/sso', '/signin']):
                    return False, f"  Redirected to login page: {final_url} (authentication failed)"

                # HTTP to HTTPS redirect is fine, just note it
                if original_url.startswith('http://') and final_url.startswith('https://'):
                    print(f"  Note: Server upgraded HTTP to HTTPS")

            print(f"  Status: {status}")


            content_type = response.headers.get("Content-Type", "").lower()
            if status == 401:
                return False, f"  401 Unauthorized: {response.text[:200]}"
            if status != 200:
                return False, f"  Unexpected status {status}: {response.text[:200]}"
            if "application/json" not in content_type:
                snippet = response.text[:120].replace("\n", " ")
                return False, f"  Non-JSON response (Content-Type: {content_type or 'unknown'}). Body starts: {snippet}"

            try:
                data = response.json()
            except Exception as e:
                snippet = response.text[:120].replace("\n", " ")
                return False, f"  JSON parse error: {e}. Body starts: {snippet}"

            # Basic sanity checks for expected fields
            if endpoint.endswith("/myself") and not any(k in data for k in ("displayName", "name", "accountId")):
                return False, "  JSON does not look like a user object"
            if endpoint.endswith("/serverInfo") and not any(k in data for k in ("serverTitle", "version")):
                return False, "  JSON does not look like serverInfo"

            # Success message
            if 'displayName' in data:
                return True, f"✅ SUCCESS: Connected as {data.get('displayName', 'Unknown')} (using {name})"
            if 'serverTitle' in data:
                return True, f"✅ SUCCESS: Connected to {data.get('serverTitle', 'Unknown')} (using {name})"
            return True, f"✅ SUCCESS: Connected (using {name})"

        # Try authenticated endpoints only (serverInfo is often public and doesn't verify auth)
        print("\n🔍 Testing Jira endpoints...")
        endpoints = [
            ("/rest/api/3/myself", "API v3"),
            ("/rest/api/2/myself", "API v2"),
        ]

        errors: list[str] = []
        for endpoint, name in endpoints:
            ok, msg = get_json(endpoint, name)
            if not ok:
                print(f"  {msg}")
                errors.append(f"{name}: {msg}")
            else:
                print(f"  {msg}")
                return True, msg

        # If we reach here, all authenticated endpoints failed
        return False, "❌ FAILURE: Authentication failed - all endpoints denied access.\n  " + "\n  ".join(errors)

    except requests.exceptions.Timeout:
        return False, f"❌ FAILURE: Connection timeout to {url}"
    except requests.exceptions.ConnectionError as e:
        return False, f"❌ FAILURE: Cannot reach {url} - {str(e)}"
    except Exception as e:
        return False, f"❌ FAILURE: {str(e)}"


def test_confluence_connection() -> Tuple[bool, str]:
    """Test Confluence connection using CONFLUENCE_URL, CONFLUENCE_USERNAME, and CONFLUENCE_API_TOKEN"""
    print_header("Testing Confluence Connection")

    url = os.getenv("CONFLUENCE_URL")
    username = os.getenv("CONFLUENCE_USERNAME")
    token = os.getenv("CONFLUENCE_API_TOKEN")

    print(f"📍 Confluence URL: {url or 'NOT SET'}")
    print(f"👤 Username: {username or 'NOT SET'}")
    print(f"🔑 Token: {mask_token(token)}")

    if not url:
        return False, "❌ FAILURE: CONFLUENCE_URL not set"
    if not username:
        return False, "❌ FAILURE: CONFLUENCE_USERNAME not set"
    if not token:
        return False, "❌ FAILURE: CONFLUENCE_API_TOKEN not set"

    if requests is None:
        return False, "❌ FAILURE: requests library not installed"

    # Check for placeholder values
    if "your-confluence-instance" in (url or "").lower() or "your_confluence" in (token or "").lower():
        return False, "❌ FAILURE: Using placeholder values from .env.example"

    try:
        from requests.auth import HTTPBasicAuth

        # Test authentication with /rest/api/user/current endpoint
        response = requests.get(
            f"{url.rstrip('/')}/rest/api/user/current",
            auth=HTTPBasicAuth(username, token),
            timeout=10
        )

        if response.status_code == 401:
            return False, "❌ FAILURE: Authentication failed (401 Unauthorized)"
        elif response.status_code == 200:
            try:
                user_data = response.json()
            except Exception:
                return False, "❌ FAILURE: Non-JSON response from Confluence API"
            display_name = user_data.get("displayName", username)
            return True, f"✅ SUCCESS: Connected as {display_name}"
        else:
            return False, f"❌ FAILURE: Unexpected status code {response.status_code}"

    except requests.exceptions.Timeout:
        return False, f"❌ FAILURE: Connection timeout to {url}"
    except requests.exceptions.ConnectionError:
        return False, f"❌ FAILURE: Cannot reach {url}"
    except Exception as e:
        return False, f"❌ FAILURE: {str(e)}"


def main():
    print_header("Bridge-MCP Services Connection Test")
    print("Testing all services configured in bridge_mcp_server.py")
    print("Checking authentication status for: GitLab, Jira, Confluence\n")

    results = []

    # Test GitLab
    gitlab_ok, gitlab_msg = test_gitlab_connection()
    print(f"\n{gitlab_msg}\n")
    results.append(("GitLab", gitlab_ok, gitlab_msg))

    # Test Jira
    jira_ok, jira_msg = test_jira_connection()
    print(f"\n{jira_msg}\n")
    results.append(("Jira", jira_ok, jira_msg))

    # Test Confluence
    confluence_ok, confluence_msg = test_confluence_connection()
    print(f"\n{confluence_msg}\n")
    results.append(("Confluence", confluence_ok, confluence_msg))

    # Summary
    print_header("Test Summary")
    for service, ok, msg in results:
        status = "✅ SUCCESS" if ok else "❌ FAILURE"
        print(f"{service:12} {status}")

    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)

    print(f"\nResult: {passed}/{total} services connected successfully")

    if passed == total:
        print("\n✨ All services are properly configured!")
        sys.exit(0)
    elif passed > 0:
        print("\n⚠️  Some services failed. Check the configuration above.")
        sys.exit(1)
    else:
        print("\n❌ All services failed. Please check your .env configuration.")
        print("   Copy .env.example to .env and fill in your credentials.")
        sys.exit(1)


if __name__ == "__main__":
    main()
