"""
PostgreSQL-based Session Manager

Replaces Redis with PostgreSQL for persistent session storage.
Each platform (WhatsApp, GitHub) has separate sessions.
"""

import os
import sys
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, update, delete

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from agents.session.base import BaseSessionManager
from database import get_session, ConversationSession


class PostgreSQLSessionManager(BaseSessionManager):
    """
    Manages conversation sessions using PostgreSQL for persistence.

    Features:
    - Platform-specific sessions (WhatsApp and GitHub are separate)
    - Persistent storage (survives restarts)
    - Scalable (works with multiple instances)
    """

    def __init__(self, ttl_minutes: int = 60, max_history: int = 10, platform: str = "unknown"):
        """
        Initialize PostgreSQL session manager

        Args:
            ttl_minutes: Time-to-live for sessions (cleanup after inactivity)
            max_history: Maximum number of messages to keep in history
            platform: Platform identifier ("whatsapp" or "github")
        """
        self.ttl_minutes = ttl_minutes
        self.max_history = max_history
        self.platform = platform
        print(f"✅ PostgreSQLSessionManager initialized")
        print(f"   Platform: {platform}")
        print(f"   TTL: {ttl_minutes} minutes")
        print(f"   Max history: {max_history} messages")

    async def _get_session_async(self, session_id: str) -> Dict:
        """
        Get or create a session for a user.

        Args:
            session_id: Platform-specific identifier (phone number, repo#issue, etc.)

        Returns:
            Session dict with conversation history and metadata
        """
        async for db_session in get_session():
            stmt = select(ConversationSession).where(ConversationSession.session_id == session_id)
            result = await db_session.execute(stmt)
            session = result.scalar_one_or_none()

            if session:
                # Update last_active timestamp
                stmt = (
                    update(ConversationSession)
                    .where(ConversationSession.session_id == session_id)
                    .values(last_active=datetime.utcnow())
                )
                await db_session.execute(stmt)
                await db_session.commit()

                return {
                    "session_id": session_id,
                    "platform": session.platform,
                    "conversation_history": session.conversation_history or [],
                    "metadata": session.session_metadata or {},
                    "created_at": session.created_at.isoformat(),
                    "last_active": datetime.utcnow().isoformat()
                }
            else:
                # Create new session
                new_session = ConversationSession(
                    session_id=session_id,
                    platform=self.platform,
                    conversation_history=[],
                    session_metadata={},
                    created_at=datetime.utcnow(),
                    last_active=datetime.utcnow()
                )
                db_session.add(new_session)
                await db_session.commit()

                print(f"📝 Created new {self.platform} session for {session_id}")

                return {
                    "session_id": session_id,
                    "platform": self.platform,
                    "conversation_history": [],
                    "metadata": {},
                    "created_at": datetime.utcnow().isoformat(),
                    "last_active": datetime.utcnow().isoformat()
                }

    async def _add_message_async(self, session_id: str, role: str, content: str):
        """
        Add a message to the conversation history (async version).

        Args:
            session_id: Platform-specific identifier
            role: "user" or "assistant"
            content: Message text
        """
        session = await self._get_session_async(session_id)

        # Add message to history
        history = session["conversation_history"]
        history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Limit history to prevent token overflow
        if len(history) > self.max_history:
            history = history[-self.max_history:]
            print(f"🗑️ Trimmed history for {session_id} to {self.max_history} messages")

        # Update in database
        async for db_session in get_session():
            stmt = (
                update(ConversationSession)
                .where(ConversationSession.session_id == session_id)
                .values(
                    conversation_history=history,
                    last_active=datetime.utcnow()
                )
            )
            await db_session.execute(stmt)
            await db_session.commit()

    async def _get_conversation_history_async(self, session_id: str) -> List[Dict]:
        """
        Get conversation history for a user (async version).

        Args:
            session_id: Platform-specific identifier

        Returns:
            List of message dicts
        """
        session = await self._get_session_async(session_id)
        history = session["conversation_history"]

        # Log for persistence visibility
        if history:
            print(f"📚 Loaded {len(history)} messages from PostgreSQL for {session_id}")

        return history

    async def _clear_session_async(self, session_id: str):
        """Clear/delete a session (async version)."""
        async for db_session in get_session():
            stmt = delete(ConversationSession).where(ConversationSession.session_id == session_id)
            await db_session.execute(stmt)
            await db_session.commit()
            print(f"🗑️ Cleared session for {session_id}")

    async def _cleanup_expired_sessions_impl(self) -> int:
        """
        Internal implementation: Remove sessions that haven't been active for > TTL.

        Returns:
            Number of sessions cleaned up
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=self.ttl_minutes)

        async for db_session in get_session():
            # Find expired sessions
            stmt = select(ConversationSession).where(
                ConversationSession.last_active < cutoff_time
            )
            result = await db_session.execute(stmt)
            expired_sessions = result.scalars().all()

            # Delete expired sessions
            if expired_sessions:
                stmt = delete(ConversationSession).where(
                    ConversationSession.last_active < cutoff_time
                )
                await db_session.execute(stmt)
                await db_session.commit()

                count = len(expired_sessions)
                print(f"🧹 Cleaned up {count} expired sessions")
                return count

            return 0

    async def get_active_sessions_count(self) -> int:
        """Get number of active sessions."""
        async for db_session in get_session():
            stmt = select(ConversationSession)
            result = await db_session.execute(stmt)
            sessions = result.scalars().all()
            return len(sessions)

    async def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Get session metadata without conversation history."""
        async for db_session in get_session():
            stmt = select(ConversationSession).where(ConversationSession.session_id == session_id)
            result = await db_session.execute(stmt)
            session = result.scalar_one_or_none()

            if session:
                return {
                    "session_id": session_id,
                    "platform": session.platform,
                    "message_count": len(session.conversation_history or []),
                    "created_at": session.created_at.isoformat(),
                    "last_active": session.last_active.isoformat()
                }
            return None

    # Synchronous wrappers for BaseSessionManager interface compatibility
    # Note: These should NOT be called from async code. Use _*_async methods instead.
    def add_message(self, session_id: str, role: str, content: str):
        """
        Add a message to the conversation history.

        Synchronous wrapper for compatibility with BaseSessionManager.
        WARNING: Do not call from async code - use _add_message_async instead.
        """
        import asyncio
        try:
            # This will raise RuntimeError if called from async context
            return asyncio.run(self._add_message_async(session_id, role, content))
        except RuntimeError as e:
            if "cannot be called from a running event loop" in str(e):
                raise RuntimeError(
                    "Cannot call sync add_message from async context. "
                    "Use 'await session_manager._add_message_async()' instead."
                ) from e
            raise

    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """
        Get conversation history for a user.

        Synchronous wrapper for compatibility with BaseSessionManager.
        WARNING: Do not call from async code - use _get_conversation_history_async instead.
        """
        import asyncio
        try:
            return asyncio.run(self._get_conversation_history_async(session_id))
        except RuntimeError as e:
            if "cannot be called from a running event loop" in str(e):
                raise RuntimeError(
                    "Cannot call sync get_conversation_history from async context. "
                    "Use 'await session_manager._get_conversation_history_async()' instead."
                ) from e
            raise

    def clear_session(self, session_id: str):
        """
        Clear/delete a session.

        Synchronous wrapper for compatibility with BaseSessionManager.
        WARNING: Do not call from async code - use _clear_session_async instead.
        """
        import asyncio
        try:
            return asyncio.run(self._clear_session_async(session_id))
        except RuntimeError as e:
            if "cannot be called from a running event loop" in str(e):
                raise RuntimeError(
                    "Cannot call sync clear_session from async context. "
                    "Use 'await session_manager._clear_session_async()' instead."
                ) from e
            raise

    def get_session(self, session_id: str) -> Dict:
        """
        Get or create a session for a user.

        Synchronous wrapper for compatibility with BaseSessionManager.
        WARNING: Do not call from async code - use _get_session_async instead.
        """
        import asyncio
        try:
            return asyncio.run(self._get_session_async(session_id))
        except RuntimeError as e:
            if "cannot be called from a running event loop" in str(e):
                raise RuntimeError(
                    "Cannot call sync get_session from async context. "
                    "Use 'await session_manager._get_session_async()' instead."
                ) from e
            raise

    def cleanup_expired_sessions(self) -> int:
        """
        Cleanup expired sessions (sync wrapper).

        WARNING: Do not call from async code - use cleanup_expired_sessions_async instead.
        """
        import asyncio
        try:
            return asyncio.run(self._cleanup_expired_sessions_impl())
        except RuntimeError as e:
            if "cannot be called from a running event loop" in str(e):
                raise RuntimeError(
                    "Cannot call sync cleanup_expired_sessions from async context. "
                    "Use 'await session_manager.cleanup_expired_sessions_async()' instead."
                ) from e
            raise

    async def cleanup_expired_sessions_async(self) -> int:
        """
        Cleanup expired sessions (async version).

        Calls the main async implementation.
        """
        # Call the actual cleanup implementation (defined earlier in the class)
        return await self._cleanup_expired_sessions_impl()
