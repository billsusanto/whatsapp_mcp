"""
GitHub Agent Manager

Manages agent sessions for GitHub PR/Issue contexts.
Creates and coordinates the CollaborativeOrchestrator for GitHub events.
"""

import os
import time
import logging
from typing import Dict, Any, Optional

from agents.collaborative.orchestrator import CollaborativeOrchestrator
from github_mcp.server import create_github_mcp_config
from netlify_mcp.server import create_netlify_mcp_config
from github_bot.client import get_github_client
from github_bot.utils import format_github_comment

logger = logging.getLogger(__name__)


class GitHubAgentManager:
    """
    Manages agent sessions for GitHub contexts.

    Each PR or Issue gets its own session with a dedicated orchestrator.
    Handles GitHub-specific configuration and comment posting.
    """

    # Class-level session store (shared across all instances)
    _sessions: Dict[str, Dict[str, Any]] = {}

    def __init__(self, session_key: str, context: Dict[str, Any]):
        """
        Initialize GitHub Agent Manager.

        Args:
            session_key: Unique key for this PR/Issue (e.g., "owner/repo#42")
            context: Full context from GitHub event parser
        """
        self.session_key = session_key
        self.context = context
        self.github_client = get_github_client()

        logger.info(f"GitHubAgentManager initialized for {session_key}")

    async def process_command(self, command: str):
        """
        Process a @droid command.

        Checks if there's an existing session (multi-turn conversation)
        or creates a new one.

        Args:
            command: The command text extracted from @droid mention
        """
        session = self._sessions.get(self.session_key)

        if session and session.get("status") == "in_progress":
            # Existing session - this is a follow-up/refinement
            logger.info(f"Continuing existing session for {self.session_key}")
            orchestrator = session["orchestrator"]

            # Send refinement notification
            await self._send_notification(
                format_github_comment(
                    "Got it! Processing your additional request...",
                    status="working"
                )
            )

            # Handle as refinement
            await orchestrator.handle_user_message(command)

        else:
            # New session - start fresh workflow
            logger.info(f"Starting new session for {self.session_key}")

            # Create orchestrator
            orchestrator = await self._create_orchestrator()

            # Store session
            self._sessions[self.session_key] = {
                "orchestrator": orchestrator,
                "context": self.context,
                "status": "in_progress",
                "started_at": time.time(),
                "command": command
            }

            # Send initial notification
            await self._send_notification(
                format_github_comment(
                    "Request received! Multi-agent team processing your request...",
                    status="rocket"
                )
            )

            # Start workflow
            await orchestrator.start_workflow(command)

            # Mark session as completed
            self._sessions[self.session_key]["status"] = "completed"
            self._sessions[self.session_key]["completed_at"] = time.time()

    async def _create_orchestrator(self) -> CollaborativeOrchestrator:
        """
        Create a new CollaborativeOrchestrator configured for GitHub.

        Returns:
            Configured orchestrator instance
        """
        # Get GitHub MCP config
        github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
        repo = self.context["repository"]["full_name"]

        # Configure GitHub MCP with repository context
        github_mcp_config = create_github_mcp_config(token=github_token)

        # Set repository in environment for MCP
        github_mcp_config["env"] = {
            **github_mcp_config.get("env", {}),
            "GITHUB_REPOSITORY": repo
        }

        # Get Netlify MCP config if enabled
        available_mcp_servers = {"github": github_mcp_config}

        if os.getenv("ENABLE_NETLIFY_MCP", "false").lower() == "true":
            netlify_token = os.getenv("NETLIFY_PERSONAL_ACCESS_TOKEN")
            if netlify_token:
                netlify_mcp_config = create_netlify_mcp_config(token=netlify_token)
                available_mcp_servers["netlify"] = netlify_mcp_config

        # Create orchestrator
        orchestrator = CollaborativeOrchestrator(
            user_id=self.session_key,
            send_message_callback=self._send_notification,
            platform="github",
            github_context=self.context,
            available_mcp_servers=available_mcp_servers
        )

        logger.info(
            f"Created orchestrator for {self.session_key} with "
            f"MCP servers: {list(available_mcp_servers.keys())}"
        )

        return orchestrator

    async def _send_notification(self, message: str):
        """
        Send a notification to GitHub as a comment.

        This is the callback used by the orchestrator to post status updates.

        Args:
            message: Message to post (supports markdown)
        """
        try:
            repo = self.context["repository"]["full_name"]
            number = self._get_issue_number()

            if not number:
                logger.error("Cannot post comment: no issue/PR number found")
                return

            # Post comment
            result = self.github_client.post_comment(
                repo=repo,
                issue_number=number,
                body=message
            )

            if result:
                logger.info(f"Posted notification to {repo}#{number}")
            else:
                logger.warning(f"Failed to post notification to {repo}#{number}")

        except Exception as e:
            logger.error(f"Error posting notification: {e}", exc_info=True)

    def _get_issue_number(self) -> Optional[int]:
        """
        Get the issue or PR number from context.

        Returns:
            Issue/PR number, or None if not found
        """
        if self.context.get("type") == "pull_request":
            return self.context.get("pull_request", {}).get("number")
        else:
            return self.context.get("issue", {}).get("number")

    @classmethod
    def get_active_sessions(cls) -> Dict[str, Dict[str, Any]]:
        """
        Get all active sessions.

        Returns:
            Dict of session_key -> session data
        """
        return {
            key: value
            for key, value in cls._sessions.items()
            if value.get("status") == "in_progress"
        }

    @classmethod
    def cleanup_old_sessions(cls, max_age_hours: int = 24):
        """
        Clean up sessions older than max_age_hours.

        Args:
            max_age_hours: Maximum age in hours before cleanup
        """
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600

        keys_to_remove = []
        for key, session in cls._sessions.items():
            started_at = session.get("started_at", current_time)
            age = current_time - started_at

            if age > max_age_seconds:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            logger.info(f"Cleaning up old session: {key}")
            del cls._sessions[key]

        if keys_to_remove:
            logger.info(f"Cleaned up {len(keys_to_remove)} old sessions")

    @classmethod
    def get_session_stats(cls) -> Dict[str, Any]:
        """
        Get statistics about current sessions.

        Returns:
            Dict with session statistics
        """
        total = len(cls._sessions)
        in_progress = sum(
            1 for s in cls._sessions.values()
            if s.get("status") == "in_progress"
        )
        completed = sum(
            1 for s in cls._sessions.values()
            if s.get("status") == "completed"
        )

        return {
            "total_sessions": total,
            "in_progress": in_progress,
            "completed": completed,
            "session_keys": list(cls._sessions.keys())
        }
