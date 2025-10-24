"""
Base Session Manager Interface

Defines the contract for session storage implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseSessionManager(ABC):
    """
    Abstract base class for session management.

    Implementations can use different storage backends:
    - InMemorySessionManager: In-memory storage (fast, not persistent)
    - RedisSessionManager: Redis-backed storage (distributed, persistent)
    - DatabaseSessionManager: Database storage (persistent, queryable)
    """

    @abstractmethod
    def add_message(self, session_id: str, role: str, content: str) -> None:
        """
        Add a message to the conversation history.

        Args:
            session_id: Unique session identifier (phone number, user ID, etc.)
            role: Message role ("user" or "assistant")
            content: Message content
        """
        pass

    @abstractmethod
    def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session.

        Args:
            session_id: Unique session identifier

        Returns:
            List of message dicts with keys: role, content, timestamp
            Example: [
                {"role": "user", "content": "Hello", "timestamp": "2025-01-24T12:00:00"},
                {"role": "assistant", "content": "Hi!", "timestamp": "2025-01-24T12:00:01"}
            ]
        """
        pass

    @abstractmethod
    def clear_session(self, session_id: str) -> None:
        """
        Clear all messages for a session.

        Args:
            session_id: Unique session identifier
        """
        pass

    @abstractmethod
    def get_session(self, session_id: str) -> Dict[str, Any]:
        """
        Get full session object including metadata.

        Args:
            session_id: Unique session identifier

        Returns:
            Session dict with keys: session_id, conversation_history, created_at, last_active
        """
        pass

    def session_exists(self, session_id: str) -> bool:
        """
        Check if a session exists.

        Args:
            session_id: Unique session identifier

        Returns:
            True if session exists, False otherwise
        """
        # Default implementation - subclasses can override for efficiency
        history = self.get_conversation_history(session_id)
        return len(history) > 0

    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions (optional, for TTL-based implementations).

        Returns:
            Number of sessions cleaned up (or 0 if not applicable)
        """
        # Default implementation - no-op
        # Subclasses with TTL support should override
        return 0

    def get_active_sessions_count(self) -> int:
        """
        Get count of active sessions (optional, for monitoring).

        Returns:
            Number of active sessions (or 0 if not tracked)
        """
        # Default implementation - no-op
        # Subclasses can override for monitoring
        return 0
