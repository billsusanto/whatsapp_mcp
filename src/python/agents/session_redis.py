"""
Redis-based Session Manager

Replaces in-memory session storage for persistence and scalability.
Maintains the same interface as the original SessionManager for compatibility.
"""

import os
import json
import redis
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class RedisSessionManager:
    """Manages conversation sessions using Redis for persistence"""

    def __init__(self, ttl_minutes: int = 60, max_history: int = 10):
        """
        Initialize Redis session manager

        Args:
            ttl_minutes: Time-to-live for sessions (auto-cleanup after inactivity)
            max_history: Maximum number of messages to keep in history
        """
        # Connect to Redis
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')

        try:
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )

            # Test connection
            self.redis_client.ping()
            print(f"✅ Redis SessionManager initialized (TTL: {ttl_minutes}min, Max history: {max_history})")
            print(f"   Connected to: {redis_url}")

        except redis.ConnectionError as e:
            print(f"❌ Redis connection failed: {e}")
            print(f"   Attempted to connect to: {redis_url}")
            print(f"   Please ensure Redis is running and REDIS_URL is correct")
            raise

        self.ttl_minutes = ttl_minutes
        self.ttl_seconds = ttl_minutes * 60
        self.max_history = max_history

    def _get_session_key(self, phone_number: str) -> str:
        """Get Redis key for a session"""
        return f"session:{phone_number}"

    def get_session(self, phone_number: str) -> Dict:
        """
        Get or create a session for a phone number

        Returns:
            Session dict with conversation history and metadata
        """
        key = self._get_session_key(phone_number)
        session_json = self.redis_client.get(key)

        if session_json:
            # Deserialize existing session
            session = json.loads(session_json)

            # Convert ISO format strings back to datetime objects for last_active
            session["last_active"] = datetime.utcnow()

            # Keep created_at as ISO string for consistency
            if isinstance(session.get("created_at"), str):
                # Already in ISO format, leave it
                pass

            # Update in Redis with TTL refresh
            self.redis_client.setex(key, self.ttl_seconds, json.dumps(session))

            return session
        else:
            # Create new session
            session = {
                "phone_number": phone_number,
                "conversation_history": [],
                "created_at": datetime.utcnow().isoformat(),
                "last_active": datetime.utcnow()
            }

            # Store in Redis with TTL
            # Convert to JSON-serializable format
            session_to_store = session.copy()
            session_to_store["last_active"] = session["last_active"].isoformat()

            self.redis_client.setex(key, self.ttl_seconds, json.dumps(session_to_store))
            print(f"Created new session for {phone_number}")

            return session

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
            session["conversation_history"] = session["conversation_history"][-self.max_history:]
            print(f"Trimmed history for {phone_number} to {self.max_history} messages")

        # Update last active
        session["last_active"] = datetime.utcnow()

        # Save to Redis
        key = self._get_session_key(phone_number)
        session_to_store = session.copy()
        session_to_store["last_active"] = session["last_active"].isoformat()
        self.redis_client.setex(key, self.ttl_seconds, json.dumps(session_to_store))

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
        key = self._get_session_key(phone_number)
        result = self.redis_client.delete(key)
        if result:
            print(f"Cleared session for {phone_number}")

    def cleanup_expired_sessions(self):
        """
        Remove sessions that haven't been active for > TTL

        Note: Redis handles TTL automatically, so this is mostly for reporting
        Returns the count of active sessions (expired ones are already removed by Redis)
        """
        # Get all session keys
        pattern = "session:*"
        keys = self.redis_client.keys(pattern)

        # Count active sessions
        active_count = len(keys)

        print(f"Active sessions: {active_count} (Redis automatically expires old sessions)")
        return 0  # Redis handles expiration automatically, so 0 were manually cleaned

    def get_active_sessions_count(self) -> int:
        """Get number of active sessions"""
        pattern = "session:*"
        keys = self.redis_client.keys(pattern)
        return len(keys)

    def get_session_info(self, phone_number: str) -> Optional[Dict]:
        """Get session metadata without conversation history"""
        key = self._get_session_key(phone_number)
        session_json = self.redis_client.get(key)

        if session_json:
            session = json.loads(session_json)
            return {
                "phone_number": phone_number,
                "message_count": len(session["conversation_history"]),
                "created_at": session["created_at"],
                "last_active": session["last_active"]
            }
        return None

    def close(self):
        """Close Redis connection (for cleanup)"""
        try:
            self.redis_client.close()
            print("Redis connection closed")
        except Exception as e:
            print(f"Error closing Redis connection: {e}")
