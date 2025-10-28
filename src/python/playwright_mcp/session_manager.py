"""
Playwright Session Manager

Manages combined lifecycle of dev server + Playwright browser session.
Provides clean context manager interface for testing workflows.
"""

import os
import asyncio
from typing import Optional
from contextlib import asynccontextmanager
import logging

from .dev_server_manager import DevServerManager
from .port_manager import get_port_manager

logger = logging.getLogger(__name__)


class PlaywrightSessionManager:
    """
    Manages dev server + Playwright session lifecycle

    This provides a unified interface for:
    1. Allocating a port
    2. Starting dev server on that port
    3. Making server URL available for Playwright
    4. Cleaning up everything on exit
    """

    def __init__(self, project_dir: str, timeout: int = 60):
        """
        Initialize session manager

        Args:
            project_dir: Path to project directory with package.json
            timeout: Maximum seconds to wait for server startup
        """
        self.project_dir = project_dir
        self.timeout = timeout
        self.port_manager = get_port_manager()
        self.dev_server: Optional[DevServerManager] = None
        self.allocated_port: Optional[int] = None
        self.server_url: Optional[str] = None

    @asynccontextmanager
    async def create_session(self):
        """
        Create a testing session with dev server and return server URL

        Usage:
            async with session_manager.create_session() as server_url:
                # Use Playwright to navigate to server_url
                await playwright_navigate(server_url)
                # Take screenshots, run tests, etc.
                pass
            # Dev server automatically stopped, port released

        Yields:
            server_url: URL to access the dev server (e.g., "http://localhost:3000")
        """
        logger.info(f"🎬 Creating Playwright session for {self.project_dir}")

        # Allocate port
        self.allocated_port = await self.port_manager.allocate_port()
        logger.info(f"📡 Allocated port {self.allocated_port}")

        # Create dev server manager
        self.dev_server = DevServerManager(
            project_dir=self.project_dir,
            port=self.allocated_port,
            timeout=self.timeout
        )

        try:
            # Start dev server
            await self.dev_server.start()
            self.server_url = self.dev_server._get_server_url()

            logger.info(f"✅ Session ready: {self.server_url}")

            # Yield server URL to caller
            yield self.server_url

        finally:
            # Cleanup
            logger.info("🧹 Cleaning up session...")

            if self.dev_server:
                self.dev_server.stop()

            if self.allocated_port:
                await self.port_manager.release_port(self.allocated_port)

            logger.info("✅ Session cleanup complete")

    def get_server_logs(self, lines: int = 50) -> str:
        """
        Get dev server logs (useful for debugging)

        Args:
            lines: Number of log lines to retrieve

        Returns:
            Log output as string
        """
        if self.dev_server:
            return self.dev_server.get_logs(lines)
        return "No dev server running"


async def create_testing_session(project_dir: str, timeout: int = 60):
    """
    Convenience function to create a testing session

    Args:
        project_dir: Path to project directory
        timeout: Server startup timeout in seconds

    Returns:
        Async context manager yielding server URL
    """
    manager = PlaywrightSessionManager(project_dir, timeout)
    return manager.create_session()
