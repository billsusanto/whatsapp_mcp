"""
Netlify MCP Server Configuration

Creates Netlify MCP server config for Claude Agent SDK
Using Netlify's official MCP server (no CLI required)
"""

import os
from typing import Dict, Any, Optional


def create_netlify_mcp_config(token: Optional[str] = None) -> Dict[str, Any]:
    """
    Create Netlify MCP server configuration using stdio transport

    This uses Netlify's official @netlify/mcp package, which means:
    - No Netlify CLI installation required
    - Works on Render and other cloud platforms
    - Direct MCP protocol communication with Netlify API
    - Handles authentication via Personal Access Token

    Args:
        token: Netlify Personal Access Token
               If None, reads from NETLIFY_PERSONAL_ACCESS_TOKEN env var

    Returns:
        MCP server configuration dict for ClaudeAgentOptions

    Raises:
        ValueError: If no Netlify token is available
    """
    netlify_token = token or os.getenv("NETLIFY_PERSONAL_ACCESS_TOKEN")

    if not netlify_token:
        raise ValueError(
            "Netlify token not found. Set NETLIFY_PERSONAL_ACCESS_TOKEN environment variable "
            "or pass token parameter.\n"
            "Get your token from: Netlify Dashboard → User Settings → OAuth → New access token"
        )

    # Return Netlify MCP server config as dict
    # Using Netlify's official @netlify/mcp package with stdio transport
    # See: https://github.com/netlify/netlify-mcp

    # Netlify MCP server using npx with stdio transport
    # This matches the format expected by Claude Agent SDK
    # Include GitHub token for repo linking capabilities
    env_vars = {
        "NETLIFY_PERSONAL_ACCESS_TOKEN": netlify_token
    }

    # Add GitHub token if available (needed for GitHub repo linking)
    github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
    if github_token:
        env_vars["GITHUB_TOKEN"] = github_token
        print("  ✓ GitHub token included for repo linking")

    config = {
        "command": "npx",
        "args": [
            "-y",
            "@netlify/mcp"
        ],
        "env": env_vars
    }

    print(f"✅ Netlify MCP configured (stdio transport)")

    return config


def validate_netlify_token(token: str) -> bool:
    """
    Validate that a Netlify token is valid

    Args:
        token: Netlify Personal Access Token

    Returns:
        True if token is valid, False otherwise
    """
    import requests

    try:
        response = requests.get(
            "https://api.netlify.com/api/v1/user",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Failed to validate Netlify token: {e}")
        return False


def get_netlify_user_info(token: str) -> Optional[Dict[str, Any]]:
    """
    Get Netlify user information for a token

    Args:
        token: Netlify Personal Access Token

    Returns:
        User info dict with 'id', 'email', 'full_name', etc.
        None if token is invalid
    """
    import requests

    try:
        response = requests.get(
            "https://api.netlify.com/api/v1/user",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Netlify API error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Failed to get Netlify user info: {e}")
        return None
