"""
GitHub Notification Adapter

Implements NotificationAdapter for GitHub issues and pull requests.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from typing import Dict, Any, Optional
from .notification import NotificationAdapter
from github_bot.client import GitHubClient

# Import Logfire telemetry
from utils.telemetry import (
    log_event,
    log_error,
    measure_performance
)


class GitHubAdapter(NotificationAdapter):
    """
    GitHub platform adapter.

    Uses GitHubClient to post comments on issues/PRs and add reactions.
    """

    def __init__(self, client: GitHubClient, context: Dict[str, Any]):
        """
        Initialize GitHub adapter.

        Args:
            client: GitHubClient instance for API calls
            context: GitHub webhook context containing repository and issue/PR info
                    Expected keys:
                    - repository: {full_name: "owner/repo"}
                    - issue or pull_request: {number: int}
                    - comment (optional): {id: int}
        """
        self.client = client
        self.context = context
        self._repo = context.get("repository", {}).get("full_name", "unknown/unknown")
        self._number = self._extract_issue_number()
        self._comment_id = self._extract_comment_id()

        print(f"✅ GitHub notification adapter initialized for {self._repo}#{self._number}")

    def _extract_issue_number(self) -> int:
        """Extract issue or PR number from context."""
        # Try issue first, then pull_request
        if "issue" in self.context:
            return self.context["issue"].get("number", 0)
        elif "pull_request" in self.context:
            return self.context["pull_request"].get("number", 0)
        else:
            return 0

    def _extract_comment_id(self) -> Optional[int]:
        """Extract comment ID from context (for reactions)."""
        if "comment" in self.context:
            return self.context["comment"].get("id")
        return None

    async def send_message(self, recipient: str, message: str) -> None:
        """
        Post a comment to the GitHub issue or pull request.

        Args:
            recipient: Not used for GitHub (comment goes to the PR/issue)
            message: Comment text (supports GitHub-flavored markdown)

        Raises:
            Exception: If GitHub API call fails
        """
        try:
            with measure_performance("github.post_comment") as perf:
                result = self.client.post_comment(self._repo, self._number, message)

                perf.set_metadata(
                    repo=self._repo,
                    issue_number=self._number,
                    message_length=len(message)
                )

                if result:
                    print(f"💬 GitHub comment posted to {self._repo}#{self._number}: {message[:50]}...")
                    log_event(
                        "github.comment_posted",
                        repo=self._repo,
                        issue_number=self._number,
                        message_length=len(message)
                    )
                else:
                    raise Exception(f"Failed to post comment to {self._repo}#{self._number}")
        except Exception as e:
            print(f"❌ Failed to post GitHub comment to {self._repo}#{self._number}: {e}")
            log_error(
                e,
                "github.post_comment",
                repo=self._repo,
                issue_number=self._number
            )
            raise

    async def send_reaction(self, message_id: str, reaction: str) -> None:
        """
        Add a reaction to a GitHub comment.

        Args:
            message_id: GitHub comment ID (or uses context comment ID if empty)
            reaction: Reaction type (+1, -1, laugh, confused, heart, hooray, rocket, eyes)

        Note:
            Common reactions:
            - "eyes" (👀) - Acknowledged, working on it
            - "+1" (👍) - Approved
            - "rocket" (🚀) - Deployed
            - "heart" (❤️) - Thanks
        """
        try:
            # Use provided message_id or fall back to context comment_id
            comment_id = int(message_id) if message_id else self._comment_id

            if not comment_id:
                print("⚠️  No comment ID available for GitHub reaction")
                return

            result = self.client.react_to_comment(self._repo, comment_id, reaction)
            if result:
                print(f"👀 GitHub reaction '{reaction}' added to comment {comment_id}")
                log_event(
                    "github.reaction_added",
                    repo=self._repo,
                    issue_number=self._number,
                    comment_id=comment_id,
                    reaction=reaction
                )
            else:
                print(f"⚠️  Failed to add GitHub reaction to comment {comment_id}")

        except Exception as e:
            print(f"⚠️  Error adding GitHub reaction: {e}")
            # Don't raise - reactions are non-critical (but log the error)
            log_error(
                e,
                "github.add_reaction",
                repo=self._repo,
                issue_number=self._number,
                comment_id=comment_id if 'comment_id' in locals() else None,
                reaction=reaction
            )

    def get_platform_name(self) -> str:
        """Get platform identifier."""
        return "github"

    def get_context_info(self) -> Dict[str, Any]:
        """
        Get GitHub context information.

        Returns:
            Dict with repo, issue_number, and comment_id
        """
        return {
            "repo": self._repo,
            "issue_number": self._number,
            "comment_id": self._comment_id
        }
