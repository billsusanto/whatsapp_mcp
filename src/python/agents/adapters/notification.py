"""
Notification Adapter Abstract Interface

Defines the contract for platform-specific notification implementations.
"""

from abc import ABC, abstractmethod
from typing import Optional


class NotificationAdapter(ABC):
    """
    Abstract interface for platform-specific notifications.

    Each platform (WhatsApp, GitHub, Slack, etc.) should implement this interface
    to provide a consistent notification API for the UnifiedAgentManager.
    """

    @abstractmethod
    async def send_message(self, recipient: str, message: str) -> None:
        """
        Send a message to a recipient.

        Args:
            recipient: Platform-specific recipient identifier
                      - WhatsApp: phone number (e.g., "+1234567890")
                      - GitHub: Not used (comment posted to PR/issue)
                      - Slack: channel ID
            message: Message text to send

        Raises:
            Exception: If message sending fails
        """
        pass

    @abstractmethod
    async def send_reaction(self, message_id: str, reaction: str) -> None:
        """
        React to a message (optional, platform-dependent).

        Args:
            message_id: Platform-specific message/comment identifier
            reaction: Reaction emoji or identifier

        Note:
            Some platforms may not support reactions. Implementations
            should handle this gracefully (no-op or log warning).
        """
        pass

    @abstractmethod
    def get_platform_name(self) -> str:
        """
        Get the platform name identifier.

        Returns:
            Platform name (e.g., "whatsapp", "github", "slack")
        """
        pass
