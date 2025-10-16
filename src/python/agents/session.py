"""
Conversation Session Management

Tracks conversation history per WhatsApp user for multi-turn conversations
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta


class SessionManager:
    """Manages conversation sessions for multiple users"""

    def __init__(self, ttl_minutes: int = 30):
        """
        Initialize session manager

        Args:
            ttl_minutes: Time-to-live for sessions (auto-cleanup after inactivity)

        TODO:
        - Initialize in-memory storage: dict[phone_number] -> Session
        - Set TTL for auto-cleanup
        - Later: Replace with Redis for production
        """
        self.sessions: Dict = {}
        self.ttl = ttl_minutes

    def get_session(self, phone_number: str) -> Optional[Dict]:
        """
        Get or create a session for a phone number

        Returns:
            Session dict with:
            {
                "phone_number": str,
                "conversation_history": List[Dict],  # Claude message format
                "created_at": datetime,
                "last_active": datetime
            }

        TODO:
        - Check if session exists in self.sessions
        - If not, create new session
        - Update last_active timestamp
        - Return session data
        """
        pass

    def add_message(self, phone_number: str, role: str, content: str):
        """
        Add a message to the conversation history

        Args:
            phone_number: User's phone number
            role: "user" or "assistant"
            content: Message text

        TODO:
        - Get session for phone_number
        - Append {"role": role, "content": content} to conversation_history
        - Limit history to last N messages (e.g., 20) to avoid token limits
        - Update last_active timestamp
        """
        pass

    def clear_session(self, phone_number: str):
        """
        Clear/delete a session

        TODO:
        - Remove session from self.sessions
        """
        pass

    def cleanup_expired_sessions(self):
        """
        Remove sessions that haven't been active for > TTL

        TODO:
        - Iterate through all sessions
        - Check if last_active > TTL
        - Delete expired sessions
        - Run this periodically (background task)
        """
        pass
