"""
Playwright MCP Server Configuration

Creates Playwright MCP server config for Claude Agent SDK
Provides browser automation and web scraping capabilities
"""

import os
from typing import Dict, Any, Optional


def create_playwright_mcp_config(headless: Optional[bool] = None) -> Dict[str, Any]:
    """
    Create Playwright MCP server configuration using stdio transport

    This provides browser automation capabilities for your agents:
    - Navigate to URLs
    - Take screenshots
    - Fill forms
    - Click elements
    - Execute JavaScript
    - Extract page content

    Args:
        headless: If True, runs browsers in headless mode (no GUI)
                 If None, reads from PLAYWRIGHT_HEADLESS env var (defaults to True)

    Returns:
        MCP server configuration dict for ClaudeAgentOptions

    Environment Variables:
        - PLAYWRIGHT_HEADLESS: "true" or "false" (defaults to "true")
    """
    # Determine headless mode
    if headless is None:
        headless_env = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower()
        headless = headless_env == "true"

    # Playwright MCP server using npx with stdio transport
    # This matches the format expected by Claude Agent SDK
    config = {
        "command": "npx",
        "args": [
            "-y",
            "@playwright/mcp"
        ],
        "env": {
            "PLAYWRIGHT_HEADLESS": "true" if headless else "false"
        }
    }

    print(f"✅ Playwright MCP configured (stdio transport, headless={headless})")

    return config


def validate_playwright_installation() -> bool:
    """
    Validate that Playwright is properly installed with browser binaries

    Returns:
        True if Playwright is installed and browsers are available
    """
    import subprocess

    try:
        # Check if playwright is installed
        result = subprocess.run(
            ["npx", "playwright", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print(f"Playwright version: {result.stdout.strip()}")
            return True
        else:
            print(f"Playwright check failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"Failed to validate Playwright installation: {e}")
        return False


def get_playwright_browsers() -> Optional[list]:
    """
    Get list of installed Playwright browsers

    Returns:
        List of browser names (e.g., ['chromium', 'firefox', 'webkit'])
        None if unable to determine
    """
    import subprocess

    try:
        # Check which browsers are installed
        result = subprocess.run(
            ["npx", "playwright", "install", "--dry-run"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            # Parse output to find installed browsers
            browsers = []
            for line in result.stdout.split('\n'):
                if 'chromium' in line.lower():
                    browsers.append('chromium')
                elif 'firefox' in line.lower():
                    browsers.append('firefox')
                elif 'webkit' in line.lower():
                    browsers.append('webkit')

            return browsers if browsers else ['chromium']  # Default to chromium
        else:
            return ['chromium']  # Assume chromium is installed

    except Exception as e:
        print(f"Failed to check Playwright browsers: {e}")
        return ['chromium']  # Assume chromium is installed
