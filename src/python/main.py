"""
FastAPI Service for WhatsApp + Claude Agent SDK + MCP
Modular architecture with Agent Manager
"""

import os
import asyncio
import sys

# IMPORTANT: Import mcp.types first to avoid import order issues with claude_agent_sdk
import mcp.types

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import Dict, Optional, Any
from claude_agent_sdk import tool
from dotenv import load_dotenv

sys.path.append(os.path.dirname(__file__))

from agents.unified_manager import UnifiedAgentManager
from agents.adapters.whatsapp_adapter import WhatsAppAdapter
from agents.session_redis import RedisSessionManager
from whatsapp_mcp.client import WhatsAppClient
from whatsapp_mcp.parser import WhatsAppWebhookParser
from github_bot import router as github_router

# Load environment variables
load_dotenv()

# Initialize Logfire telemetry
from utils.telemetry import (
    initialize_logfire,
    instrument_fastapi,
    instrument_anthropic,
    instrument_httpx,
    log_event,
    log_user_action,
    log_error,
    set_user_context,
    track_session_event,
    trace_operation,
    measure_performance
)

# Initialize telemetry (auto-configures if LOGFIRE_TOKEN is set)
initialize_logfire()

app = FastAPI(title="WhatsApp MCP Service", version="1.0.0")

# Instrument FastAPI for automatic tracing
instrument_fastapi(app)

# Instrument Anthropic SDK for LLM call tracking
instrument_anthropic()

# Instrument HTTP clients for external API tracking
instrument_httpx()

# Initialize WhatsApp client
whatsapp_client = WhatsAppClient()

# Define WhatsApp MCP Tool
@tool("send_whatsapp", "Send a WhatsApp message", {"to": str, "text": str})
async def whatsapp_send_tool(args: dict[str, Any]) -> dict[str, Any]:
    """MCP tool for sending WhatsApp messages"""
    try:
        to = args.get('to')
        text = args.get('text')
        whatsapp_client.send_message(to, text)
        return {
            "content": [{
                "type": "text",
                "text": f"Successfully sent message to {to}"
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error sending message: {str(e)}"
            }],
            "isError": True
        }

# Build MCP configuration
mcp_config = {}

# Add WhatsApp MCP tools
mcp_config["whatsapp"] = [whatsapp_send_tool]

# Add GitHub MCP if enabled
enable_github = os.getenv("ENABLE_GITHUB_MCP", "false").lower() == "true"
if enable_github:
    try:
        from github_mcp.server import create_github_mcp_config
        mcp_config["github"] = create_github_mcp_config()
        print("✅ GitHub MCP configured")
    except Exception as e:
        print(f"⚠️  GitHub MCP not available: {e}")

# Add Netlify MCP if enabled
enable_netlify = os.getenv("ENABLE_NETLIFY_MCP", "false").lower() == "true"
if enable_netlify:
    try:
        from netlify_mcp.server import create_netlify_mcp_config
        mcp_config["netlify"] = create_netlify_mcp_config()
        print("✅ Netlify MCP configured")
    except Exception as e:
        print(f"⚠️  Netlify MCP not available: {e}")

# Add PostgreSQL MCP if enabled
try:
    from utils.pgsql_mcp_helper import get_postgres_mcp_config, is_postgres_mcp_enabled
    if is_postgres_mcp_enabled():
        postgres_config = get_postgres_mcp_config()
        if postgres_config:
            mcp_config["postgres"] = postgres_config
            print("✅ PostgreSQL MCP configured")
except Exception as e:
    print(f"⚠️  PostgreSQL MCP not available: {e}")

# Initialize WhatsApp adapter
whatsapp_adapter = WhatsAppAdapter(whatsapp_client)

# Initialize Redis session manager
session_manager = RedisSessionManager(ttl_minutes=60, max_history=10)

# Initialize Unified Agent Manager
agent_manager = UnifiedAgentManager(
    platform="whatsapp",
    session_manager=session_manager,
    notification_adapter=whatsapp_adapter,
    mcp_config=mcp_config,
    enable_multi_agent=enable_netlify
)

# Include GitHub bot webhook routes
app.include_router(github_router)

# Pydantic models for API
class MessageRequest(BaseModel):
    phone_number: str
    message: str

class MessageResponse(BaseModel):
    response: str
    status: str = "success"


@app.get("/")
async def root():
    """Root endpoint - Render health check"""
    return {
        "service": "whatsapp-mcp",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for Render"""
    return {
        "status": "healthy",
        "service": "whatsapp-mcp",
        "platform": agent_manager.platform,
        "api_key_configured": bool(os.getenv("ANTHROPIC_API_KEY")),
        "whatsapp_configured": bool(os.getenv("WHATSAPP_ACCESS_TOKEN")),
        "github_mcp_enabled": "github" in mcp_config,
        "github_token_configured": bool(os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")),
        "netlify_mcp_enabled": "netlify" in mcp_config,
        "netlify_token_configured": bool(os.getenv("NETLIFY_PERSONAL_ACCESS_TOKEN")),
        "multi_agent_enabled": agent_manager.multi_agent_enabled,
        "active_agents": agent_manager.get_active_agents_count(),
        "available_mcp_servers": list(mcp_config.keys())
    }


@app.get("/webhook")
async def webhook_verify(request: Request):
    """WhatsApp webhook verification endpoint (GET)"""
    mode = request.query_params.get('hub.mode')
    token = request.query_params.get('hub.verify_token')
    challenge = request.query_params.get('hub.challenge')

    print(f"Webhook verification: mode={mode}, token_match={token == os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN')}")

    if mode == 'subscribe' and token == os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN'):
        print("✅ Webhook verified successfully!")
        return PlainTextResponse(challenge, status_code=200)

    print("❌ Webhook verification failed")
    return PlainTextResponse("Forbidden", status_code=403)


@app.post("/webhook")
async def webhook_receive(request: Request):
    """WhatsApp webhook endpoint (POST) - Receives incoming messages"""
    try:
        body = await request.json()
        print(f"Received webhook: {body}")

        # Parse message using WhatsAppWebhookParser
        message_data = WhatsAppWebhookParser.parse_message(body)

        # Ignore if no valid message
        if not message_data:
            print("No valid message found, ignoring webhook")
            return {"status": "ok"}

        # Extract message details
        from_number = message_data.get('from')
        message_text = message_data.get('text', '')
        message_type = message_data.get('type')

        # Log user action
        log_user_action(
            "message_received",
            from_number,
            message_type=message_type,
            message_length=len(message_text)
        )

        # Only process text messages for now
        if message_type != 'text' or not message_text:
            print(f"Ignoring non-text message type: {message_type}")
            return {"status": "ok"}

        print(f"Processing message from {from_number}: {message_text}")

        # Process message with Agent Manager (async, don't wait)
        asyncio.create_task(process_whatsapp_message(from_number, message_text))

        # Return 200 OK immediately (WhatsApp requires quick response)
        return {"status": "ok"}

    except Exception as e:
        print(f"Webhook error: {str(e)}")
        log_error(e, "webhook_receive", body_keys=list(body.keys()) if 'body' in locals() else [])
        return {"status": "error", "message": str(e)}


async def process_whatsapp_message(phone_number: str, message: str):
    """
    Process WhatsApp message with Agent Manager
    Spawns/retrieves agent and sends response back via WhatsApp
    """
    # Set user context for all traces in this scope
    set_user_context(phone_number)

    with trace_operation(
        "process_whatsapp_message",
        message_length=len(message),
        message_preview=message[:50]
    ):
        try:
            # Measure agent processing time
            with measure_performance("agent_processing") as perf:
                # Process with Agent Manager
                response = await agent_manager.process_message(phone_number, message)
                perf.set_metadata(response_length=len(response))

            # Send response back via WhatsApp
            with measure_performance("whatsapp_send"):
                whatsapp_client.send_message(phone_number, response)

            print(f"✅ Sent response to {phone_number}")

            # Log successful interaction
            log_user_action(
                "message_processed",
                phone_number,
                message_length=len(message),
                response_length=len(response)
            )

        except Exception as e:
            print(f"❌ Error processing message for {phone_number}: {str(e)}")
            log_error(e, "process_whatsapp_message", message_length=len(message))

            # Send error message to user
            try:
                whatsapp_client.send_message(
                    phone_number,
                    "Sorry, I encountered an error processing your message. Please try again."
                )
            except Exception as send_error:
                print(f"❌ Failed to send error message: {str(send_error)}")
                log_error(send_error, "whatsapp_error_send")


async def periodic_cleanup():
    """
    Background task for periodic cleanup of expired sessions and agents
    Runs every 60 minutes to prevent memory leaks
    """
    while True:
        try:
            await asyncio.sleep(3600)  # Run every 60 minutes (1 hour)

            print("🧹 Running periodic cleanup...")

            # Cleanup expired sessions
            expired_count = agent_manager.cleanup_expired_sessions()

            # Get current state
            active_agents = agent_manager.get_active_agents_count()

            print(f"✓ Cleanup complete - Expired sessions: {expired_count}, Active agents: {active_agents}")

        except Exception as e:
            print(f"❌ Error in periodic cleanup: {str(e)}")


@app.post("/agent/process", response_model=MessageResponse)
async def process_message(request: MessageRequest):
    """
    Directly process a message (for testing)

    Args:
        request: MessageRequest with phone_number and message

    Returns:
        MessageResponse with agent's reply
    """
    try:
        phone_number = request.phone_number
        user_message = request.message

        # Process with Agent Manager
        response = await agent_manager.process_message(phone_number, user_message)

        return MessageResponse(
            response=response,
            status="success"
        )

    except Exception as e:
        print(f"Error processing message: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process message: {str(e)}"
        )


@app.post("/agent/reset/{phone_number}")
async def reset_session(phone_number: str):
    """
    Reset conversation session for a phone number

    Args:
        phone_number: Phone number to reset session for

    Returns:
        Status message
    """
    try:
        agent_manager.reset_conversation(phone_number)
        return {"status": "success", "message": f"Session reset for {phone_number}"}
    except Exception as e:
        print(f"Error resetting session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    print("=" * 60)
    print("🚀 WhatsApp MCP Service Starting...")
    print("=" * 60)
    print(f"Platform: {agent_manager.platform}")
    print(f"ANTHROPIC_API_KEY configured: {bool(os.getenv('ANTHROPIC_API_KEY'))}")
    print(f"WHATSAPP_ACCESS_TOKEN configured: {bool(os.getenv('WHATSAPP_ACCESS_TOKEN'))}")
    print(f"GITHUB_PERSONAL_ACCESS_TOKEN configured: {bool(os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN'))}")
    print(f"Multi-agent enabled: {agent_manager.multi_agent_enabled}")
    print(f"\nAvailable MCP servers: {list(mcp_config.keys())}")
    print("=" * 60)

    # Start background task for periodic cleanup
    asyncio.create_task(periodic_cleanup())


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up all agents on shutdown"""
    print("Shutting down WhatsApp MCP Service...")
    await agent_manager.cleanup_all_agents()
    print("Shutdown complete")


if __name__ == "__main__":
    import uvicorn

    # Get port from environment (Render sets this)
    port = int(os.getenv("PORT", 8000))

    print(f"Starting WhatsApp MCP Service on port {port}")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
