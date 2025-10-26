"""
GitHub Webhook Handler

FastAPI routes for receiving and processing GitHub App webhook events.
Handles @droid mentions in PR and Issue comments.
"""

import os
import sys
import json
import asyncio
import logging
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from github_bot.utils import (
    verify_github_signature,
    extract_droid_mention,
    is_bot_comment,
    format_github_comment,
)
from github_bot.parser import parse_github_event

# Import Logfire telemetry utilities
from utils.telemetry import (
    log_event,
    log_user_action,
    log_error,
    trace_operation,
    measure_performance
)

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

    # Log webhook event to Logfire
    log_event(
        "github.webhook_received",
        event_type=event_type,
        delivery_id=delivery_id
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
        log_event(
            "github.event_ignored",
            event_type=event_type,
            reason="not a relevant event"
        )
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
        log_event(
            "github.event_ignored",
            event_type=event_type,
            reason="bot comment",
            bot_author=comment_author
        )
        return JSONResponse(
            content={"status": "ignored", "reason": "bot comment"},
            status_code=200
        )

    # Check for @Supernova-Droid mention (GitHub App username)
    # Note: GitHub adds [bot] suffix, but we check without it for flexibility
    command = extract_droid_mention(comment_body, bot_name="Supernova-Droid")

    if not command:
        logger.debug("No @Supernova-Droid mention found in comment")
        log_event(
            "github.event_ignored",
            event_type=event_type,
            reason="no mention"
        )
        return JSONResponse(
            content={"status": "ignored", "reason": "no mention"},
            status_code=200
        )

    # We have a valid @droid mention! Process it in the background
    repo_full_name = context['repository']['full_name']
    issue_number = context.get('pull_request', context.get('issue', {})).get('number')

    logger.info(
        f"Processing @droid mention in {repo_full_name} "
        f"#{issue_number}"
    )

    # Log the mention to Logfire
    log_user_action(
        "github.mention_detected",
        f"{repo_full_name}#{issue_number}",
        repo=repo_full_name,
        issue_number=issue_number,
        command_preview=command[:100] if command else "",
        author=comment_author
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
    # Create session key
    repo_full_name = context['repository']['full_name']
    issue_number = context.get('pull_request', context.get('issue', {})).get('number')
    session_key = f"{repo_full_name}#{issue_number}"

    try:
        logger.info(f"Starting command processing: {command[:50]}...")

        # Start performance measurement and tracing
        with measure_performance("github.command_processing") as perf:
            with trace_operation(
                "GitHub Command Processing",
                repo=repo_full_name,
                issue_number=issue_number,
                command_preview=command[:100]
            ):
                # Import here to avoid circular imports
                from agents.unified_manager import UnifiedAgentManager
                from agents.adapters.github_adapter import GitHubAdapter
                from agents.session_postgres import PostgreSQLSessionManager
                from github_bot.client import GitHubClient

                # Build MCP configuration for GitHub platform
                mcp_config = {}

                # Add GitHub MCP
                enable_github = os.getenv("ENABLE_GITHUB_MCP", "false").lower() == "true"
                if enable_github:
                    try:
                        import sys
                        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
                        from github_mcp.server import create_github_mcp_config
                        mcp_config["github"] = create_github_mcp_config()
                    except Exception as e:
                        logger.warning(f"GitHub MCP not available: {e}")

                # Add Netlify MCP (required for deployments)
                enable_netlify = os.getenv("ENABLE_NETLIFY_MCP", "false").lower() == "true"
                if enable_netlify:
                    try:
                        import sys
                        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
                        from netlify_mcp.server import create_netlify_mcp_config
                        mcp_config["netlify"] = create_netlify_mcp_config()
                    except Exception as e:
                        logger.warning(f"Netlify MCP not available: {e}")

                # Add PostgreSQL MCP
                try:
                    import sys
                    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
                    from utils.pgsql_mcp_helper import get_postgres_mcp_config, is_postgres_mcp_enabled
                    if is_postgres_mcp_enabled():
                        postgres_config = get_postgres_mcp_config()
                        if postgres_config:
                            mcp_config["postgres"] = postgres_config
                except Exception as e:
                    logger.warning(f"PostgreSQL MCP not available: {e}")

                # Create GitHub adapter
                github_client = GitHubClient()
                github_adapter = GitHubAdapter(github_client, context)

                # Create session manager (PostgreSQL for GitHub sessions)
                session_manager = PostgreSQLSessionManager(ttl_minutes=60, max_history=10, platform="github")

                # Create unified manager
                manager = UnifiedAgentManager(
                    platform="github",
                    session_manager=session_manager,
                    notification_adapter=github_adapter,
                    mcp_config=mcp_config,
                    enable_multi_agent=enable_netlify,
                    platform_context=context
                )

                # Add 👀 reaction to acknowledge
                comment_id = context.get('comment', {}).get('id')
                if comment_id:
                    await github_adapter.send_reaction(str(comment_id), "eyes")

                # Process the command
                response = await manager.process_message(session_key, command, context)

                # Track response length for metrics
                perf.set_metadata(
                    repo=repo_full_name,
                    issue_number=issue_number,
                    response_length=len(response) if response else 0
                )

                # Send response back to GitHub
                if response:
                    await github_adapter.send_message(session_key, response)

                logger.info(f"Command processing completed for {session_key}")

                # Log successful completion
                log_user_action(
                    "github.command_completed",
                    session_key,
                    repo=repo_full_name,
                    issue_number=issue_number,
                    response_length=len(response) if response else 0
                )

    except Exception as e:
        logger.error(f"Error processing @droid command: {e}", exc_info=True)

        # Log error to Logfire
        log_error(
            e,
            "github.command_processing",
            repo=repo_full_name,
            issue_number=issue_number,
            session_key=session_key
        )

        # Try to post error comment to GitHub
        try:
            await post_error_comment(context, str(e))
        except Exception as post_error:
            logger.error(f"Failed to post error comment: {post_error}")
            log_error(post_error, "github.post_error_comment", session_key=session_key)


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
