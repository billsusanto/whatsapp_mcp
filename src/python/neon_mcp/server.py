"""
Neon MCP Server Configuration

Creates Neon MCP server config for Claude Agent SDK
Using Neon's official MCP server for database access
"""

import os
from typing import Dict, Any, Optional


def create_neon_mcp_config(api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Create Neon MCP server configuration using stdio transport

    This uses Neon's official @neondatabase/mcp-server-neon package, which means:
    - Direct MCP protocol communication with Neon API
    - No additional CLI installation required
    - Works on Render and other cloud platforms
    - Handles authentication via Neon API Key

    Args:
        api_key: Neon API Key
                 If None, reads from NEON_API_KEY env var

    Returns:
        MCP server configuration dict for ClaudeAgentOptions

    Raises:
        ValueError: If no Neon API key is available
    """
    neon_api_key = api_key or os.getenv("NEON_API_KEY")

    if not neon_api_key:
        raise ValueError(
            "Neon API key not found. Set NEON_API_KEY environment variable "
            "or pass api_key parameter.\n"
            "Get your API key from: Neon Console → Account Settings → API Keys"
        )

    # Return Neon MCP server config as dict
    # Using Neon's official @neondatabase/mcp-server-neon package with stdio transport
    # See: https://github.com/neondatabase/mcp-server-neon

    # Neon MCP server using npx with stdio transport
    # This matches the format expected by Claude Agent SDK
    # Note: For MCP server integration (not standalone CLI), pass API key via env var
    # This is the same pattern used by GitHub MCP and Netlify MCP
    config = {
        "command": "npx",
        "args": [
            "-y",
            "@neondatabase/mcp-server-neon"
        ],
        "env": {
            "NEON_API_KEY": neon_api_key
        }
    }

    print(f"✅ Neon MCP configured (stdio transport)")
    print(f"   API Key: {neon_api_key[:15]}..." if neon_api_key else "   API Key: NOT SET")

    return config


def validate_neon_api_key(api_key: str) -> bool:
    """
    Validate that a Neon API key is valid

    Args:
        api_key: Neon API Key

    Returns:
        True if API key is valid, False otherwise
    """
    import requests

    try:
        # Validate by attempting to list projects
        response = requests.get(
            "https://console.neon.tech/api/v2/projects",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json"
            },
            timeout=5
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Failed to validate Neon API key: {e}")
        return False


def get_neon_projects(api_key: str) -> Optional[Dict[str, Any]]:
    """
    Get list of Neon projects for an API key

    Args:
        api_key: Neon API Key

    Returns:
        Projects list dict with project information
        None if API key is invalid
    """
    import requests

    try:
        response = requests.get(
            "https://console.neon.tech/api/v2/projects",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json"
            },
            timeout=5
        )

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Neon API error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Failed to get Neon projects: {e}")
        return None
