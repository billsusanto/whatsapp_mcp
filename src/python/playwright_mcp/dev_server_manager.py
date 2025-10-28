"""
Dev Server Manager for Playwright Testing

Manages lifecycle of development servers (npm run dev) for testing purposes.
Handles starting, health checking, and graceful shutdown of dev servers.
"""

import subprocess
import asyncio
import httpx
import os
import signal
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DevServerManager:
    """Manages dev server lifecycle for Playwright testing"""

    def __init__(self, project_dir: str, port: int = 3000, timeout: int = 60):
        """
        Initialize dev server manager

        Args:
            project_dir: Path to the project directory containing package.json
            port: Port to run dev server on (default: 3000)
            timeout: Maximum seconds to wait for server to become ready (default: 60)
        """
        self.project_dir = project_dir
        self.port = port
        self.timeout = timeout
        self.process: Optional[subprocess.Popen] = None
        self.is_running = False

    async def start(self) -> bool:
        """
        Start dev server and wait until ready

        Returns:
            True if server started successfully, False otherwise

        Raises:
            TimeoutError: If server doesn't become ready within timeout
            RuntimeError: If npm run dev fails to start
        """
        logger.info(f"🚀 Starting dev server in {self.project_dir} on port {self.port}...")

        # Check if package.json exists
        package_json_path = os.path.join(self.project_dir, 'package.json')
        if not os.path.exists(package_json_path):
            raise RuntimeError(f"package.json not found in {self.project_dir}")

        # Ensure dev script binds to 0.0.0.0 for Docker/Render compatibility
        # This allows Playwright in the same container to access localhost
        env = os.environ.copy()
        env['PORT'] = str(self.port)

        try:
            # Start process
            self.process = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=self.project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                # Important: Create new process group for proper cleanup
                preexec_fn=os.setsid if os.name != 'nt' else None
            )

            logger.info(f"📦 Dev server process started (PID: {self.process.pid})")

            # Wait for server to be ready
            if await self._wait_for_ready():
                self.is_running = True
                logger.info(f"✅ Dev server ready on port {self.port}")
                return True
            else:
                # Server didn't become ready - kill process
                self.stop()
                raise TimeoutError(f"Dev server failed to start within {self.timeout}s")

        except Exception as e:
            logger.error(f"❌ Failed to start dev server: {e}")
            if self.process:
                self.stop()
            raise

    async def _wait_for_ready(self) -> bool:
        """
        Poll server until it responds to HTTP requests

        Returns:
            True if server becomes ready, False if timeout
        """
        start_time = asyncio.get_event_loop().time()
        url = self._get_server_url()

        logger.info(f"⏳ Waiting for dev server at {url}...")

        async with httpx.AsyncClient(timeout=5.0) as client:
            while (asyncio.get_event_loop().time() - start_time) < self.timeout:
                # Check if process is still alive
                if self.process and self.process.poll() is not None:
                    logger.error(f"❌ Dev server process died (exit code: {self.process.returncode})")
                    return False

                try:
                    response = await client.get(url)
                    if response.status_code < 500:  # Any non-500 response means server is ready
                        logger.info(f"✅ Server responded with status {response.status_code}")
                        return True
                except (httpx.RequestError, httpx.TimeoutException):
                    # Server not ready yet, keep waiting
                    pass

                await asyncio.sleep(1)

        logger.error(f"❌ Timeout waiting for dev server after {self.timeout}s")
        return False

    def stop(self):
        """Stop dev server gracefully"""
        if not self.process:
            return

        logger.info(f"🛑 Stopping dev server (PID: {self.process.pid})...")

        try:
            # Kill process group (handles child processes like Vite/Next.js/Turbopack)
            if os.name != 'nt':
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            else:
                self.process.terminate()

            # Wait for process to exit (with timeout)
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("⚠️ Process didn't exit gracefully, forcing kill...")
                if os.name != 'nt':
                    os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                else:
                    self.process.kill()
                self.process.wait()

            self.is_running = False
            logger.info("✅ Dev server stopped")

        except Exception as e:
            logger.error(f"❌ Error stopping dev server: {e}")
        finally:
            self.process = None

    def _get_server_url(self) -> str:
        """
        Get server URL based on environment

        Returns:
            URL string (e.g., "http://localhost:3000")
        """
        # In Docker, we use localhost because Playwright runs in same container
        # In Render, same applies - all in one container
        return f"http://localhost:{self.port}"

    def get_logs(self, lines: int = 50) -> str:
        """
        Get last N lines of server logs

        Args:
            lines: Number of lines to retrieve

        Returns:
            Log output as string
        """
        if not self.process:
            return "No server process running"

        try:
            # Read available output
            stdout = self.process.stdout.read().decode('utf-8', errors='ignore') if self.process.stdout else ""
            stderr = self.process.stderr.read().decode('utf-8', errors='ignore') if self.process.stderr else ""

            output = f"STDOUT:\n{stdout}\n\nSTDERR:\n{stderr}"
            output_lines = output.split('\n')

            return '\n'.join(output_lines[-lines:])
        except Exception as e:
            return f"Error reading logs: {e}"

    def __enter__(self):
        """Context manager support (sync)"""
        raise RuntimeError("Use 'async with' instead of 'with'")

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup (sync)"""
        pass

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        self.stop()
        return False
