"""
GitHub Bot Utility Functions

Provides helper functions for webhook signature verification,
mention detection, and other GitHub-related utilities.
"""

import hmac
import hashlib
import re
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def verify_github_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify GitHub webhook signature using HMAC-SHA256.

    GitHub sends a signature in the X-Hub-Signature-256 header that we must verify
    to ensure the webhook is actually from GitHub and hasn't been tampered with.

    Args:
        payload: Raw request body as bytes
        signature: Value from X-Hub-Signature-256 header (format: "sha256=...")
        secret: Webhook secret configured in GitHub App settings

    Returns:
        True if signature is valid, False otherwise

    Example:
        >>> payload = b'{"action":"created"}'
        >>> signature = "sha256=abc123..."
        >>> verify_github_signature(payload, signature, "my_secret")
        True
    """
    if not signature:
        logger.warning("No signature provided in webhook request")
        return False

    if not secret:
        logger.error("No webhook secret configured - cannot verify signature")
        return False

    # Compute expected signature
    expected_signature = "sha256=" + hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()

    # Use constant-time comparison to prevent timing attacks
    is_valid = hmac.compare_digest(expected_signature, signature)

    if not is_valid:
        logger.warning(
            f"Invalid webhook signature. "
            f"Expected prefix: {expected_signature[:20]}..., "
            f"Got: {signature[:20]}..."
        )

    return is_valid


def extract_droid_mention(comment_body: str, bot_name: str = "droid") -> Optional[str]:
    """
    Extract command from @mention in a GitHub comment.

    Looks for patterns like:
    - "@droid help me fix the CSS"
    - "@Droid please review this code"
    - "Hey @droid can you implement this feature?"

    Args:
        comment_body: The full comment text from GitHub
        bot_name: Name of the bot to look for (default: "droid")

    Returns:
        The command text after the @mention, or None if no mention found

    Example:
        >>> extract_droid_mention("@droid help me fix the CSS")
        "help me fix the CSS"
        >>> extract_droid_mention("This looks good!")
        None
    """
    if not comment_body:
        return None

    # Match @botname followed by any text
    # Case-insensitive, handles multiple spaces, captures everything after mention
    pattern = rf'@{re.escape(bot_name)}\s+(.+)'
    match = re.search(pattern, comment_body, re.IGNORECASE | re.DOTALL)

    if match:
        command = match.group(1).strip()
        logger.info(f"Detected @{bot_name} mention with command: {command[:50]}...")
        return command

    return None


def sanitize_branch_name(text: str, max_length: int = 50) -> str:
    """
    Convert text into a valid Git branch name.

    Rules:
    - Lowercase alphanumeric and hyphens only
    - No spaces (replaced with hyphens)
    - No special characters
    - Truncate to max_length

    Args:
        text: Input text to convert
        max_length: Maximum branch name length

    Returns:
        Sanitized branch name

    Example:
        >>> sanitize_branch_name("Fix CSS styling issues")
        "fix-css-styling-issues"
    """
    # Convert to lowercase
    text = text.lower()

    # Replace spaces and underscores with hyphens
    text = re.sub(r'[\s_]+', '-', text)

    # Remove non-alphanumeric characters except hyphens
    text = re.sub(r'[^a-z0-9-]', '', text)

    # Remove consecutive hyphens
    text = re.sub(r'-+', '-', text)

    # Remove leading/trailing hyphens
    text = text.strip('-')

    # Truncate to max length
    if len(text) > max_length:
        text = text[:max_length].rstrip('-')

    return text or "droid-fix"


def format_github_comment(message: str, status: str = "info") -> str:
    """
    Format message for GitHub comment with appropriate emoji/styling.

    Args:
        message: Message to format
        status: Type of message (info, success, error, warning, working)

    Returns:
        Formatted message with emoji
    """
    emoji_map = {
        "info": "ℹ️",
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "working": "🔄",
        "rocket": "🚀",
        "brain": "🧠",
        "robot": "🤖",
        "review": "🔍",
        "deploy": "🚀",
    }

    emoji = emoji_map.get(status, "")
    return f"{emoji} {message}" if emoji else message


def is_bot_comment(comment_author: str, bot_names: list = None) -> bool:
    """
    Check if a comment is from a bot (to avoid infinite loops).

    Args:
        comment_author: GitHub username of comment author
        bot_names: List of bot names to check (default: common bot patterns)

    Returns:
        True if comment is from a bot
    """
    if bot_names is None:
        bot_names = ["github-actions", "dependabot", "renovate", "supernova-droid"]

    # Check if username ends with [bot]
    if comment_author.endswith("[bot]"):
        return True

    # Check against known bot names
    if comment_author.lower() in [name.lower() for name in bot_names]:
        return True

    return False
