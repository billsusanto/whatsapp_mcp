"""
PostgreSQL MCP Helper
Utilities for integrating pgsql-mcp-server with agents
"""

import os
from typing import Dict, Optional


def get_postgres_mcp_config() -> Optional[Dict]:
    """
    Get PostgreSQL MCP server configuration if enabled

    Returns:
        MCP server config dict or None if disabled
    """
    # Check if PostgreSQL MCP is enabled
    if not os.getenv('ENABLE_PGSQL_MCP', 'false').lower() == 'true':
        return None

    # Check if DATABASE_URL is configured
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("⚠️  PostgreSQL MCP enabled but DATABASE_URL not set")
        return None

    # Return pgsql-mcp-server configuration
    return {
        'command': 'pgsql-mcp-server',
        'args': [],
        'env': {
            'DATABASE_URL': database_url
        }
    }


def add_postgres_mcp_to_servers(mcp_servers: Dict) -> Dict:
    """
    Add PostgreSQL MCP server to existing MCP servers dict

    Args:
        mcp_servers: Existing MCP servers dict

    Returns:
        Updated MCP servers dict with PostgreSQL if enabled
    """
    postgres_config = get_postgres_mcp_config()

    if postgres_config:
        mcp_servers = mcp_servers.copy()  # Don't modify original
        mcp_servers['postgres'] = postgres_config
        print(f"✅ PostgreSQL MCP enabled for database access")
    else:
        print(f"ℹ️  PostgreSQL MCP disabled (set ENABLE_PGSQL_MCP=true to enable)")

    return mcp_servers


def is_postgres_mcp_enabled() -> bool:
    """
    Check if PostgreSQL MCP is enabled and configured

    Returns:
        True if PostgreSQL MCP is available
    """
    return (
        os.getenv('ENABLE_PGSQL_MCP', 'false').lower() == 'true'
        and os.getenv('DATABASE_URL') is not None
    )
