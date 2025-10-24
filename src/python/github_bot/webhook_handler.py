"""
GitHub Webhook Handler

FastAPI routes for receiving and processing GitHub App webhook events.
Handles @droid mentions in PR and Issue comments.
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from github_bot.utils import (
    verify_github_signature,
    extract_droid_mention,
    is_bot_comment,
    format_github_comment,
)
from github_bot.parser import parse_github_event

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/github", tags=["github"])


@router.get("/webhook")
async def webhook_verify(request: Request):
    """
    GitHub webhook verification endpoint.

    This is called by GitHub when you first set up the webhook URL
    to verify that the endpoint is valid and under your control.

    GitHub doesn't use this for App webhooks, but we implement it
    for compatibility with other GitHub webhook types.
    """
    logger.info("GitHub webhook verification requested")
    return JSONResponse(
        content={"status": "ok", "message": "GitHub webhook endpoint active"},
        status_code=200
    )


@router.post("/webhook")
async def webhook_receive(request: Request, background_tasks: BackgroundTasks):
    """
    Main GitHub webhook endpoint.

    Receives webhook events from GitHub, verifies signatures,
    parses events, and processes @droid mentions.

    Flow:
    1. Verify webhook signature (security)
    2. Parse event payload
    3. Check if it's a comment event with @droid mention
    4. If yes, spawn background task to process with orchestrator
    5. Return 200 OK immediately (GitHub requires < 10s response)
    """
    # Get webhook secret from environment
    webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET")
    if not webhook_secret:
        logger.error("GITHUB_WEBHOOK_SECRET not configured")
        raise HTTPException(
            status_code=500,
            detail="Webhook secret not configured"
        )

    # Get raw body and signature
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    event_type = request.headers.get("X-GitHub-Event", "")
    delivery_id = request.headers.get("X-GitHub-Delivery", "")

    logger.info(
        f"Received GitHub webhook: event={event_type}, "
        f"delivery={delivery_id}"
    )

    # Verify signature
    if not verify_github_signature(body, signature, webhook_secret):
        logger.warning(f"Invalid signature for delivery {delivery_id}")
        raise HTTPException(status_code=403, detail="Invalid signature")

    # Parse JSON payload
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Parse event
    context = parse_github_event(payload, event_type)

    if not context:
        # Event not relevant (e.g., not a comment creation)
        logger.debug(f"Ignoring event type {event_type}")
        return JSONResponse(
            content={"status": "ignored", "reason": "not a relevant event"},
            status_code=200
        )

    # Extract comment body
    comment_body = context.get("comment", {}).get("body", "")
    comment_author = context.get("comment", {}).get("author", "")

    # Check if comment is from a bot (avoid loops)
    if is_bot_comment(comment_author):
        logger.debug(f"Ignoring comment from bot: {comment_author}")
        return JSONResponse(
            content={"status": "ignored", "reason": "bot comment"},
            status_code=200
        )

    # Check for @droid mention
    command = extract_droid_mention(comment_body)

    if not command:
        logger.debug("No @droid mention found in comment")
        return JSONResponse(
            content={"status": "ignored", "reason": "no mention"},
            status_code=200
        )

    # We have a valid @droid mention! Process it in the background
    logger.info(
        f"Processing @droid mention in {context['repository']['full_name']} "
        f"#{context.get('pull_request', context.get('issue', {})).get('number')}"
    )

    # Add background task to process the command
    background_tasks.add_task(
        process_droid_command,
        command=command,
        context=context
    )

    # Return immediately (GitHub requires fast response)
    return JSONResponse(
        content={
            "status": "processing",
            "message": "Command received and processing"
        },
        status_code=200
    )


async def process_droid_command(command: str, context: Dict[str, Any]):
    """
    Process a @droid command with the orchestrator.

    This runs in the background after the webhook response is sent.

    Args:
        command: The command text extracted from @droid mention
        context: Full context from the GitHub event
    """
    try:
        logger.info(f"Starting command processing: {command[:50]}...")

        # Import here to avoid circular imports
        from agents.github_manager import GitHubAgentManager

        # Create session key (e.g., "owner/repo#42")
        session_key = f"{context['repository']['full_name']}#{context.get('pull_request', context.get('issue', {})).get('number')}"

        # Create/get GitHub agent manager
        manager = GitHubAgentManager(
            session_key=session_key,
            context=context
        )

        # Process the command
        await manager.process_command(command)

        logger.info(f"Command processing completed for {session_key}")

    except Exception as e:
        logger.error(f"Error processing @droid command: {e}", exc_info=True)

        # Try to post error comment to GitHub
        try:
            await post_error_comment(context, str(e))
        except Exception as post_error:
            logger.error(f"Failed to post error comment: {post_error}")


async def post_error_comment(context: Dict[str, Any], error_message: str):
    """
    Post an error message as a GitHub comment.

    Args:
        context: GitHub event context
        error_message: Error message to post
    """
    try:
        import requests

        github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
        if not github_token:
            logger.error("Cannot post error comment: GITHUB_PERSONAL_ACCESS_TOKEN not set")
            return

        repo = context["repository"]["full_name"]
        number = context.get("pull_request", context.get("issue", {})).get("number")

        if not number:
            logger.error("Cannot post error comment: no issue/PR number found")
            return

        url = f"https://api.github.com/repos/{repo}/issues/{number}/comments"
        headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        error_comment = format_github_comment(
            f"I encountered an error processing your request:\n\n```\n{error_message}\n```\n\n"
            f"Please try again or contact support if the issue persists.",
            status="error"
        )

        response = requests.post(
            url,
            json={"body": error_comment},
            headers=headers,
            timeout=10
        )

        if response.status_code == 201:
            logger.info(f"Posted error comment to {repo}#{number}")
        else:
            logger.error(f"Failed to post error comment: {response.status_code} {response.text}")

    except Exception as e:
        logger.error(f"Exception in post_error_comment: {e}", exc_info=True)


@router.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.

    Returns:
        Status of the GitHub bot service
    """
    return {
        "status": "healthy",
        "service": "github-bot",
        "webhook_configured": bool(os.getenv("GITHUB_WEBHOOK_SECRET")),
        "github_token_configured": bool(os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")),
        "app_id": os.getenv("GITHUB_APP_ID", "not set"),
    }


@router.get("/config")
async def get_config():
    """
    Get GitHub bot configuration (for debugging).

    Returns:
        Configuration status (without sensitive values)
    """
    return {
        "app_id": os.getenv("GITHUB_APP_ID", "not set"),
        "installation_id": os.getenv("GITHUB_INSTALLATION_ID", "not set"),
        "webhook_secret_configured": bool(os.getenv("GITHUB_WEBHOOK_SECRET")),
        "private_key_path": os.getenv("GITHUB_PRIVATE_KEY_PATH", "not set"),
        "github_token_configured": bool(os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")),
    }
