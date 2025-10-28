"""
Port Manager for Dynamic Port Allocation

Manages allocation of ports for dev servers to avoid conflicts.
Thread-safe with async locks for concurrent usage.
"""

import socket
import asyncio
from contextlib import asynccontextmanager
from typing import Set
import logging

logger = logging.getLogger(__name__)


class PortManager:
    """Manages port allocation for dev servers"""

    def __init__(self, port_range: tuple = (3000, 3100)):
        """
        Initialize port manager

        Args:
            port_range: Tuple of (start_port, end_port) for allocation range
        """
        self.port_range = port_range
        self._lock = asyncio.Lock()
        self._allocated_ports: Set[int] = set()
        logger.info(f"📡 PortManager initialized with range {port_range}")

    @staticmethod
    def is_port_available(port: int) -> bool:
        """
        Check if a port is available for binding

        Args:
            port: Port number to check

        Returns:
            True if port is available, False if already in use
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('0.0.0.0', port))
                return True
            except OSError:
                return False

    async def allocate_port(self) -> int:
        """
        Allocate an available port from the range

        Returns:
            Port number that was allocated

        Raises:
            RuntimeError: If no ports available in range
        """
        async with self._lock:
            start_port, end_port = self.port_range

            for port in range(start_port, end_port):
                # Skip if already allocated by this manager
                if port in self._allocated_ports:
                    continue

                # Check if port is actually available
                if self.is_port_available(port):
                    self._allocated_ports.add(port)
                    logger.info(f"✅ Allocated port {port}")
                    return port

            # No ports available
            raise RuntimeError(
                f"No available ports in range {self.port_range}. "
                f"Currently allocated: {len(self._allocated_ports)} ports"
            )

    async def release_port(self, port: int):
        """
        Release a previously allocated port

        Args:
            port: Port number to release
        """
        async with self._lock:
            if port in self._allocated_ports:
                self._allocated_ports.discard(port)
                logger.info(f"♻️ Released port {port}")
            else:
                logger.warning(f"⚠️ Attempted to release unallocated port {port}")

    @asynccontextmanager
    async def allocate(self):
        """
        Context manager for automatic port allocation and release

        Usage:
            async with port_manager.allocate() as port:
                # Use port
                pass
            # Port automatically released
        """
        port = await self.allocate_port()
        try:
            yield port
        finally:
            await self.release_port(port)

    def get_allocated_count(self) -> int:
        """Get number of currently allocated ports"""
        return len(self._allocated_ports)

    def get_available_count(self) -> int:
        """Get number of available ports in range"""
        total = self.port_range[1] - self.port_range[0]
        return total - len(self._allocated_ports)


# Global port manager instance
_global_port_manager: PortManager = None


def get_port_manager() -> PortManager:
    """
    Get global port manager instance (singleton)

    Returns:
        Global PortManager instance
    """
    global _global_port_manager
    if _global_port_manager is None:
        _global_port_manager = PortManager()
    return _global_port_manager
