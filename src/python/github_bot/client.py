"""
GitHub API Client

Provides methods for interacting with GitHub API to post comments,
create PRs, and manage repositories. Used by the orchestrator to
send status updates and results.
"""

import os
import requests
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class GitHubClient:
    """
    Client for interacting with GitHub API.

    Uses GitHub Personal Access Token for authentication.
    Provides methods for commenting on issues/PRs.
    """

    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub client.

        Args:
            token: GitHub Personal Access Token (or reads from env)
        """
        self.token = token or os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
        if not self.token:
            raise ValueError(
                "GitHub token not found. Set GITHUB_PERSONAL_ACCESS_TOKEN "
                "environment variable."
            )

        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    def post_comment(
        self,
        repo: str,
        issue_number: int,
        body: str
    ) -> Optional[Dict[str, Any]]:
        """
        Post a comment to an issue or pull request.

        Args:
            repo: Repository in format "owner/repo"
            issue_number: Issue or PR number
            body: Comment text (supports markdown)

        Returns:
            Response data with comment details, or None on error

        Example:
            >>> client.post_comment("owner/repo", 42, "✅ Task complete!")
        """
        url = f"{self.base_url}/repos/{repo}/issues/{issue_number}/comments"

        payload = {"body": body}

        try:
            response = requests.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 201:
                logger.info(f"✅ Posted comment to {repo}#{issue_number}")
                return response.json()
            else:
                logger.error(
                    f"Failed to post comment to {repo}#{issue_number}: "
                    f"{response.status_code} {response.text}"
                )
                return None

        except Exception as e:
            logger.error(f"Exception posting comment: {e}", exc_info=True)
            return None

    def update_comment(
        self,
        repo: str,
        comment_id: int,
        body: str
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing comment.

        Args:
            repo: Repository in format "owner/repo"
            comment_id: ID of the comment to update
            body: New comment text

        Returns:
            Response data with updated comment, or None on error
        """
        url = f"{self.base_url}/repos/{repo}/issues/comments/{comment_id}"

        payload = {"body": body}

        try:
            response = requests.patch(
                url,
                json=payload,
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 200:
                logger.info(f"✅ Updated comment {comment_id} in {repo}")
                return response.json()
            else:
                logger.error(
                    f"Failed to update comment {comment_id}: "
                    f"{response.status_code} {response.text}"
                )
                return None

        except Exception as e:
            logger.error(f"Exception updating comment: {e}", exc_info=True)
            return None

    def get_pull_request(
        self,
        repo: str,
        pr_number: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get pull request details.

        Args:
            repo: Repository in format "owner/repo"
            pr_number: Pull request number

        Returns:
            PR details including head/base branches, or None on error
        """
        url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}"

        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"Failed to get PR {repo}#{pr_number}: "
                    f"{response.status_code} {response.text}"
                )
                return None

        except Exception as e:
            logger.error(f"Exception getting PR: {e}", exc_info=True)
            return None

    def get_issue(
        self,
        repo: str,
        issue_number: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get issue details.

        Args:
            repo: Repository in format "owner/repo"
            issue_number: Issue number

        Returns:
            Issue details, or None on error
        """
        url = f"{self.base_url}/repos/{repo}/issues/{issue_number}"

        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"Failed to get issue {repo}#{issue_number}: "
                    f"{response.status_code} {response.text}"
                )
                return None

        except Exception as e:
            logger.error(f"Exception getting issue: {e}", exc_info=True)
            return None

    def react_to_comment(
        self,
        repo: str,
        comment_id: int,
        reaction: str = "+1"
    ) -> Optional[Dict[str, Any]]:
        """
        Add a reaction to a comment.

        Args:
            repo: Repository in format "owner/repo"
            comment_id: Comment ID
            reaction: Reaction type (+1, -1, laugh, confused, heart, hooray, rocket, eyes)

        Returns:
            Response data, or None on error
        """
        url = f"{self.base_url}/repos/{repo}/issues/comments/{comment_id}/reactions"

        payload = {"content": reaction}

        try:
            response = requests.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 201:
                logger.info(f"✅ Added reaction '{reaction}' to comment {comment_id}")
                return response.json()
            else:
                logger.error(
                    f"Failed to add reaction: {response.status_code} {response.text}"
                )
                return None

        except Exception as e:
            logger.error(f"Exception adding reaction: {e}", exc_info=True)
            return None


# Singleton instance for reuse
_github_client: Optional[GitHubClient] = None


def get_github_client() -> GitHubClient:
    """
    Get or create singleton GitHub client instance.

    Returns:
        GitHubClient instance
    """
    global _github_client
    if _github_client is None:
        _github_client = GitHubClient()
    return _github_client
