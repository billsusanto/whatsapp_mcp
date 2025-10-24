"""
Conversation Session Management

Tracks conversation history per WhatsApp user for multi-turn conversations
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agents.session.base import BaseSessionManager


class SessionManager(BaseSessionManager):
    """Manages conversation sessions for multiple users"""

    def __init__(self, ttl_minutes: int = 30, max_history: int = 20):
        """
        Initialize session manager

        Args:
            ttl_minutes: Time-to-live for sessions (auto-cleanup after inactivity)
            max_history: Maximum number of messages to keep in history
        """
        self.sessions: Dict[str, Dict] = {}
        self.ttl_minutes = ttl_minutes
        self.max_history = max_history
        print(f"SessionManager initialized (TTL: {ttl_minutes}min, Max history: {max_history})")

    def get_session(self, phone_number: str) -> Dict:
        """
        Get or create a session for a phone number

        Returns:
            Session dict with conversation history and metadata
        """
        if phone_number not in self.sessions:
            # Create new session
            self.sessions[phone_number] = {
                "phone_number": phone_number,
                "conversation_history": [],
                "created_at": datetime.utcnow(),
                "last_active": datetime.utcnow()
            }
            print(f"Created new session for {phone_number}")
        else:
            # Update last active time
            self.sessions[phone_number]["last_active"] = datetime.utcnow()

        return self.sessions[phone_number]

    def add_message(self, phone_number: str, role: str, content: str):
        """
        Add a message to the conversation history

        Args:
            phone_number: User's phone number
            role: "user" or "assistant"
            content: Message text
        """
        session = self.get_session(phone_number)

        # Add message to history
        session["conversation_history"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Limit history to prevent token overflow
        if len(session["conversation_history"]) > self.max_history:
            # Keep only the most recent messages
            session["conversation_history"] = session["conversation_history"][-self.max_history:]
            print(f"Trimmed history for {phone_number} to {self.max_history} messages")

        # Update last active
        session["last_active"] = datetime.utcnow()

    def get_conversation_history(self, phone_number: str) -> List[Dict]:
        """
        Get conversation history for a phone number

        Returns:
            List of message dicts in format [{"role": "user", "content": "..."}, ...]
        """
        session = self.get_session(phone_number)
        return session["conversation_history"]

    def clear_session(self, phone_number: str):
        """Clear/delete a session"""
        if phone_number in self.sessions:
            del self.sessions[phone_number]
            print(f"Cleared session for {phone_number}")

    def cleanup_expired_sessions(self):
        """Remove sessions that haven't been active for > TTL"""
        now = datetime.utcnow()
        expired = []

        for phone_number, session in self.sessions.items():
            last_active = session["last_active"]
            time_diff = now - last_active

            if time_diff > timedelta(minutes=self.ttl_minutes):
                expired.append(phone_number)

        # Delete expired sessions
        for phone_number in expired:
            del self.sessions[phone_number]
            print(f"Expired session for {phone_number}")

        if expired:
            print(f"Cleaned up {len(expired)} expired sessions")

        return len(expired)

    def get_active_sessions_count(self) -> int:
        """Get number of active sessions"""
        return len(self.sessions)

    def get_session_info(self, phone_number: str) -> Optional[Dict]:
        """Get session metadata without conversation history"""
        if phone_number in self.sessions:
            session = self.sessions[phone_number]
            return {
                "phone_number": phone_number,
                "message_count": len(session["conversation_history"]),
                "created_at": session["created_at"].isoformat(),
                "last_active": session["last_active"].isoformat()
            }
        return None
