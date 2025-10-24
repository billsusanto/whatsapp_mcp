"""
GitHub Bot Module

Handles GitHub App webhook events for @droid mentions in PR/Issue comments.
Integrates with the existing multi-agent orchestrator system.
"""

from github_bot.webhook_handler import router

__all__ = ["router"]
