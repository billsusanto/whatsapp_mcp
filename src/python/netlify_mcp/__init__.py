"""
Netlify MCP Server Configuration

Creates Netlify MCP server config for Claude Agent SDK
Using Netlify's official @netlify/mcp package (no CLI required)
"""

from .server import create_netlify_mcp_config

__all__ = ['create_netlify_mcp_config']
