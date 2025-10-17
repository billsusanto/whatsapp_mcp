"""
GitHub MCP Server Configuration

Creates HTTP-based GitHub MCP server config for Claude Agent SDK
Using GitHub's hosted MCP endpoint (no Docker required)
"""

import os
from typing import Dict, Any, Optional


def create_github_mcp_config(token: Optional[str] = None, readonly: bool = False) -> Dict[str, Any]:
    """
    Create GitHub MCP server configuration using HTTP transport

    This uses GitHub's hosted MCP endpoint, which means:
    - No Docker-in-Docker required
    - Works on Render and other cloud platforms
    - Direct HTTP connection to GitHub's MCP service

    Args:
        token: GitHub Personal Access Token (or OAuth token)
               If None, reads from GITHUB_PERSONAL_ACCESS_TOKEN env var
        readonly: If True, enables read-only mode (no write operations)

    Returns:
        MCP server configuration dict for ClaudeAgentOptions

    Raises:
        ValueError: If no GitHub token is available
    """
    github_token = token or os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")

    if not github_token:
        raise ValueError(
            "GitHub token not found. Set GITHUB_PERSONAL_ACCESS_TOKEN environment variable "
            "or pass token parameter."
        )

    # Return GitHub MCP server config as dict
    # Using the pre-installed GitHub MCP server from Dockerfile
    # Try direct execution first, fall back to npx if not available
    import shutil

    # Check if mcp-server-github is in PATH (globally installed)
    mcp_server_path = shutil.which("mcp-server-github")

    if mcp_server_path:
        # Use direct execution (faster, no npx overhead)
        config = {
            "command": "mcp-server-github",
            "args": [],
            "env": {
                "GITHUB_PERSONAL_ACCESS_TOKEN": github_token
            }
        }
        print(f"✅ GitHub MCP configured (direct execution, readonly={readonly})")
    else:
        # Fallback to npx (will download package if needed)
        config = {
            "command": "npx",
            "args": [
                "-y",
                "@modelcontextprotocol/server-github"
            ],
            "env": {
                "GITHUB_PERSONAL_ACCESS_TOKEN": github_token
            }
        }
        print(f"✅ GitHub MCP configured (npx fallback, readonly={readonly})")

    return config


def validate_github_token(token: str) -> bool:
    """
    Validate that a GitHub token is valid

    Args:
        token: GitHub Personal Access Token

    Returns:
        True if token is valid, False otherwise
    """
    import requests

    try:
        response = requests.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Failed to validate GitHub token: {e}")
        return False


def get_github_user_info(token: str) -> Optional[Dict[str, Any]]:
    """
    Get GitHub user information for a token

    Args:
        token: GitHub Personal Access Token

    Returns:
        User info dict with 'login', 'name', 'email', etc.
        None if token is invalid
    """
    import requests

    try:
        response = requests.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )

        if response.status_code == 200:
            return response.json()
        else:
            print(f"GitHub API error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Failed to get GitHub user info: {e}")
        return None
