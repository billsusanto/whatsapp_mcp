"""
Playwright MCP Server Configuration

Provides browser automation capabilities via Playwright MCP.
Includes dev server management, port allocation, and screenshot analysis.
"""

from .server import create_playwright_mcp_config, validate_playwright_installation, get_playwright_browsers
from .dev_server_manager import DevServerManager
from .port_manager import PortManager, get_port_manager
from .session_manager import PlaywrightSessionManager, create_testing_session
from .screenshot_analyzer import ScreenshotAnalyzer, create_playwright_screenshot_message

__all__ = [
    # Server configuration
    'create_playwright_mcp_config',
    'validate_playwright_installation',
    'get_playwright_browsers',
    # Dev server management
    'DevServerManager',
    # Port management
    'PortManager',
    'get_port_manager',
    # Session management
    'PlaywrightSessionManager',
    'create_testing_session',
    # Screenshot analysis
    'ScreenshotAnalyzer',
    'create_playwright_screenshot_message',
]
