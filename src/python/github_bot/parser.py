"""
GitHub Webhook Payload Parser

Parses GitHub webhook payloads and extracts relevant context
for the multi-agent orchestrator system.
"""

from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class GitHubEventParser:
    """
    Parser for GitHub webhook event payloads.

    Extracts relevant information from issue_comment and
    pull_request_review_comment events.
    """

    def __init__(self, payload: Dict[str, Any], event_type: str):
        """
        Initialize parser with webhook payload.

        Args:
            payload: Parsed JSON webhook payload from GitHub
            event_type: Value from X-GitHub-Event header
        """
        self.payload = payload
        self.event_type = event_type

    def is_valid_event(self) -> bool:
        """
        Check if this is an event we should process.

        Returns:
            True if this is a comment creation event we can handle
        """
        # We only process comment creation events
        if self.event_type not in ["issue_comment", "pull_request_review_comment"]:
            logger.debug(f"Ignoring event type: {self.event_type}")
            return False

        # Only process "created" actions (not edited or deleted)
        action = self.payload.get("action")
        if action != "created":
            logger.debug(f"Ignoring action: {action}")
            return False

        return True

    def get_comment_body(self) -> Optional[str]:
        """
        Extract comment body from payload.

        Returns:
            Comment text, or None if not found
        """
        if self.event_type == "issue_comment":
            return self.payload.get("comment", {}).get("body")
        elif self.event_type == "pull_request_review_comment":
            return self.payload.get("comment", {}).get("body")
        return None

    def get_comment_author(self) -> Optional[str]:
        """
        Extract comment author username.

        Returns:
            GitHub username of comment author
        """
        if self.event_type == "issue_comment":
            return self.payload.get("comment", {}).get("user", {}).get("login")
        elif self.event_type == "pull_request_review_comment":
            return self.payload.get("comment", {}).get("user", {}).get("login")
        return None

    def get_repository_context(self) -> Dict[str, str]:
        """
        Extract repository information.

        Returns:
            Dict with repo owner, name, and full_name
        """
        repo = self.payload.get("repository", {})
        return {
            "full_name": repo.get("full_name", ""),
            "owner": repo.get("owner", {}).get("login", ""),
            "name": repo.get("name", ""),
            "default_branch": repo.get("default_branch", "main"),
            "url": repo.get("html_url", ""),
        }

    def get_installation_id(self) -> Optional[int]:
        """
        Extract GitHub App installation ID.

        Returns:
            Installation ID for this repository
        """
        return self.payload.get("installation", {}).get("id")

    def is_pull_request_comment(self) -> bool:
        """
        Check if this is a comment on a pull request.

        Note: In GitHub's API, PR comments trigger "issue_comment" events,
        but we can detect them by checking for the pull_request field.

        Returns:
            True if this is a PR comment
        """
        if self.event_type == "pull_request_review_comment":
            return True

        # For issue_comment events, check if issue has pull_request field
        if self.event_type == "issue_comment":
            return "pull_request" in self.payload.get("issue", {})

        return False

    def get_pull_request_context(self) -> Optional[Dict[str, Any]]:
        """
        Extract pull request context.

        Returns:
            Dict with PR details, or None if not a PR comment
        """
        if not self.is_pull_request_comment():
            return None

        if self.event_type == "pull_request_review_comment":
            pr = self.payload.get("pull_request", {})
        else:  # issue_comment on a PR
            # We need to get PR details from the issue
            issue = self.payload.get("issue", {})
            pr_url = issue.get("pull_request", {}).get("url", "")
            # For issue_comment events, we have limited PR info
            pr = {
                "number": issue.get("number"),
                "title": issue.get("title"),
                "html_url": issue.get("html_url"),
                "state": issue.get("state"),
                "user": issue.get("user"),
                # Note: We don't have head/base branch info from issue_comment
                # The orchestrator can fetch this via GitHub API if needed
            }

        return {
            "number": pr.get("number"),
            "title": pr.get("title", ""),
            "url": pr.get("html_url", ""),
            "state": pr.get("state", ""),
            "author": pr.get("user", {}).get("login", ""),
            "head_branch": pr.get("head", {}).get("ref"),
            "base_branch": pr.get("base", {}).get("ref"),
            "head_sha": pr.get("head", {}).get("sha"),
        }

    def get_issue_context(self) -> Optional[Dict[str, Any]]:
        """
        Extract issue context.

        Returns:
            Dict with issue details, or None if this is a PR comment
        """
        if self.is_pull_request_comment():
            return None

        issue = self.payload.get("issue", {})
        return {
            "number": issue.get("number"),
            "title": issue.get("title", ""),
            "url": issue.get("html_url", ""),
            "state": issue.get("state", ""),
            "author": issue.get("user", {}).get("login", ""),
            "labels": [label.get("name") for label in issue.get("labels", [])],
            "assignees": [assignee.get("login") for assignee in issue.get("assignees", [])],
        }

    def get_comment_context(self) -> Dict[str, Any]:
        """
        Extract comment-specific context.

        Returns:
            Dict with comment details
        """
        comment = self.payload.get("comment", {})
        return {
            "id": comment.get("id"),
            "url": comment.get("html_url", ""),
            "created_at": comment.get("created_at", ""),
            "author": self.get_comment_author(),
            "body": self.get_comment_body(),
        }

    def build_full_context(self) -> Dict[str, Any]:
        """
        Build complete context object for the orchestrator.

        This combines all relevant information about the event into
        a single context dict that the orchestrator can use.

        Returns:
            Complete context dict with all relevant information
        """
        context = {
            "event_type": self.event_type,
            "action": self.payload.get("action"),
            "repository": self.get_repository_context(),
            "installation_id": self.get_installation_id(),
            "comment": self.get_comment_context(),
        }

        # Add PR or Issue context depending on type
        if self.is_pull_request_comment():
            context["type"] = "pull_request"
            context["pull_request"] = self.get_pull_request_context()
        else:
            context["type"] = "issue"
            context["issue"] = self.get_issue_context()

        return context

    def get_session_key(self) -> str:
        """
        Generate a unique session key for this PR/Issue.

        This is used to track conversation state across multiple comments.

        Returns:
            Session key in format "owner/repo#number"
        """
        repo = self.get_repository_context()
        if self.is_pull_request_comment():
            pr_context = self.get_pull_request_context()
            number = pr_context.get("number") if pr_context else "unknown"
        else:
            issue_context = self.get_issue_context()
            number = issue_context.get("number") if issue_context else "unknown"

        return f"{repo['full_name']}#{number}"


def parse_github_event(payload: Dict[str, Any], event_type: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to parse a GitHub webhook event.

    Args:
        payload: Parsed JSON webhook payload
        event_type: Value from X-GitHub-Event header

    Returns:
        Complete context dict, or None if event should not be processed
    """
    parser = GitHubEventParser(payload, event_type)

    if not parser.is_valid_event():
        return None

    return parser.build_full_context()
