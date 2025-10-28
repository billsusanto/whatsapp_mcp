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
from agents.session_postgres import PostgreSQLSessionManager
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

# Security and performance imports
from utils.security import (
    SecretManager,
    InputValidator,
    SecurityHeaders,
    validate_and_sanitize_input
)
from utils.performance import cache_manager, get_performance_config, perf_monitor

# System health monitoring
from utils.health_monitor import system_health_monitor

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="WhatsApp MCP Service", version="1.0.0")

# Add rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        for header, value in SecurityHeaders.get_security_headers().items():
            response.headers[header] = value
        return response

app.add_middleware(SecurityHeadersMiddleware)

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

        # Validate phone number
        is_valid, cleaned_phone = InputValidator.validate_phone_number(to)
        if not is_valid:
            return {
                "content": [{
                    "type": "text",
                    "text": "Invalid phone number format"
                }],
                "isError": True
            }

        whatsapp_client.send_message(cleaned_phone, text)
        return {
            "content": [{
                "type": "text",
                "text": f"Successfully sent message to {cleaned_phone}"
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

# Add Neon MCP if enabled
enable_neon = os.getenv("ENABLE_NEON_MCP", "false").lower() == "true"
neon_mcp_error = None
if enable_neon:
    try:
        from neon_mcp.server import create_neon_mcp_config
        mcp_config["neon"] = create_neon_mcp_config()
        print("✅ Neon MCP configured")
    except Exception as e:
        neon_mcp_error = str(e)
        print(f"⚠️  Neon MCP not available: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"ℹ️  Neon MCP disabled (ENABLE_NEON_MCP={os.getenv('ENABLE_NEON_MCP', 'not set')})")

# Add Playwright MCP if enabled
enable_playwright = os.getenv("ENABLE_PLAYWRIGHT_MCP", "false").lower() == "true"
if enable_playwright:
    try:
        from playwright_mcp.server import create_playwright_mcp_config
        mcp_config["playwright"] = create_playwright_mcp_config()
        print("✅ Playwright MCP configured")
    except Exception as e:
        print(f"⚠️  Playwright MCP not available: {e}")

# Initialize WhatsApp adapter
whatsapp_adapter = WhatsAppAdapter(whatsapp_client)

# Initialize PostgreSQL session manager for WhatsApp
session_manager = PostgreSQLSessionManager(ttl_minutes=60, max_history=10, platform="whatsapp")

# Initialize Unified Agent Manager
agent_manager = UnifiedAgentManager(
    platform="whatsapp",
    session_manager=session_manager,
    notification_adapter=whatsapp_adapter,
    mcp_config=mcp_config,
    enable_multi_agent=enable_netlify
)

# Log MCP configuration summary
print("\n" + "=" * 60)
print("📦 MCP SERVERS CONFIGURATION")
print("=" * 60)
if mcp_config:
    for server_name, config in mcp_config.items():
        if isinstance(config, dict) and 'command' in config:
            print(f"✅ {server_name:15} - {config['command']} {' '.join(config.get('args', [])[:2])}")
        elif isinstance(config, list):
            print(f"✅ {server_name:15} - Custom tools ({len(config)} tools)")
        else:
            print(f"✅ {server_name:15} - Configured")
else:
    print("⚠️  No MCP servers configured")
print("=" * 60 + "\n")

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
    """
    Comprehensive health check endpoint

    Returns system health, workflow stats, agent stats, and configuration
    """
    # Get system health metrics
    health_data = system_health_monitor.get_system_health()

    # Get performance config
    perf_config = get_performance_config()

    # Mask API key for security
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    # Neon MCP diagnostics
    neon_status = {
        "enabled_env_var": os.getenv("ENABLE_NEON_MCP", "not set"),
        "enabled": "neon" in mcp_config,
        "api_key_configured": bool(os.getenv("NEON_API_KEY")),
        "api_key_masked": SecretManager.mask_secret(os.getenv("NEON_API_KEY")) if os.getenv("NEON_API_KEY") else None
    }

    # Add error if Neon failed to load
    if neon_mcp_error:
        neon_status["error"] = neon_mcp_error

    return {
        "status": health_data["status"],
        "service": "whatsapp-mcp",
        "system_health": health_data,
        "platform": agent_manager.platform,
        "api_key_configured": bool(anthropic_key),
        "api_key_masked": SecretManager.mask_secret(anthropic_key) if anthropic_key else None,
        "whatsapp_configured": bool(os.getenv("WHATSAPP_ACCESS_TOKEN")),
        "github_mcp_enabled": "github" in mcp_config,
        "github_token_configured": bool(os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")),
        "netlify_mcp_enabled": "netlify" in mcp_config,
        "netlify_token_configured": bool(os.getenv("NETLIFY_PERSONAL_ACCESS_TOKEN")),
        "neon_mcp_status": neon_status,
        "multi_agent_enabled": agent_manager.multi_agent_enabled,
        "active_agents": agent_manager.get_active_agents_count(),
        "available_mcp_servers": list(mcp_config.keys()),
        "performance": {
            "cache_enabled": cache_manager.enabled,
            "agent_caching": perf_config['enable_agent_caching'],
            "db_pool_size": perf_config['db_pool_size']
        }
    }


@app.get("/metrics/performance")
async def get_performance_metrics():
    """Get performance statistics"""
    stats = await perf_monitor.get_all_stats()
    return {
        "status": "ok",
        "metrics": stats,
        "cache_enabled": cache_manager.enabled
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
@limiter.limit("20/minute")  # Rate limit: 20 messages per minute per IP
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

        # Validate and sanitize input
        is_valid, sanitized_message, error = validate_and_sanitize_input(
            message_text, from_number
        )

        if not is_valid:
            log_error(
                ValueError(error),
                "input_validation",
                user_id=from_number,
                message_preview=message_text[:100] if message_text else ""
            )

            # Send error message to user
            try:
                whatsapp_client.send_message(
                    from_number,
                    "Sorry, your message contains invalid content. Please send a valid message."
                )
            except Exception as send_error:
                print(f"Failed to send validation error: {send_error}")

            return {"status": "rejected", "reason": error}

        # Use sanitized message
        message_text = sanitized_message

        print(f"Processing message from {from_number}: {message_text[:50]}...")

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
            expired_count = await agent_manager.cleanup_expired_sessions()

            # Get current state
            active_agents = agent_manager.get_active_agents_count()
            active_details = agent_manager.get_active_agents_details()

            print(f"✓ Cleanup complete - Expired sessions: {expired_count}, Active agents: {active_agents}")

            # Show detailed info about active agents if any
            if active_details:
                print(f"📋 Active agent details:")
                for agent_info in active_details:
                    if agent_info["type"] == "single-agent":
                        print(f"   • Single Agent - User: {agent_info['user_id']}")
                    elif agent_info["type"] == "orchestrator":
                        state_info = f", State: {agent_info.get('state', 'unknown')}" if 'state' in agent_info else ""
                        project_info = f", Project: {agent_info.get('project_id', 'none')}" if 'project_id' in agent_info else ""
                        print(f"   • Orchestrator - User: {agent_info['user_id']}, Platform: {agent_info.get('platform', 'unknown')}, Active: {agent_info.get('is_active', False)}{state_info}{project_info}")

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


@app.get("/agent/history/{session_id}")
async def get_conversation_history_endpoint(session_id: str):
    """
    Get conversation history for a session (demonstrates persistence).

    This endpoint proves that conversation history persists across server restarts
    because it loads directly from PostgreSQL.

    Args:
        session_id: Session identifier (phone number for WhatsApp, repo#issue for GitHub)

    Returns:
        Conversation history with metadata
    """
    try:
        from database import ConversationSession, get_session
        from sqlalchemy import select

        async for db_session in get_session():
            stmt = select(ConversationSession).where(ConversationSession.session_id == session_id)
            result = await db_session.execute(stmt)
            session = result.scalar_one_or_none()

            if session:
                return {
                    "status": "success",
                    "session_id": session_id,
                    "platform": session.platform,
                    "message_count": len(session.conversation_history or []),
                    "conversation_history": session.conversation_history or [],
                    "created_at": session.created_at.isoformat(),
                    "last_active": session.last_active.isoformat(),
                    "persistence_note": "✅ This data is loaded from PostgreSQL and persists across server restarts"
                }
            else:
                return {
                    "status": "success",
                    "session_id": session_id,
                    "message_count": 0,
                    "conversation_history": [],
                    "persistence_note": "No conversation history yet. Start a conversation to see persistence in action!"
                }

    except Exception as e:
        print(f"Error getting conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    print("=" * 60)
    print("🚀 WhatsApp MCP Service Starting...")
    print("=" * 60)

    # CRITICAL: Validate all required secrets first
    is_valid, missing_secrets = SecretManager.validate_secrets()
    if not is_valid:
        error_msg = f"❌ Missing required secrets: {', '.join(missing_secrets)}"
        print(error_msg)
        raise RuntimeError(error_msg)

    print("✅ All required secrets validated")

    # Initialize database tables
    try:
        from database import init_db
        await init_db()
        print("✅ Database tables initialized")
    except Exception as e:
        print(f"⚠️  Database initialization failed: {e}")
        # Don't crash on database errors, continue running

    # Initialize performance cache
    await cache_manager.initialize()

    # Get performance config
    perf_config = get_performance_config()

    print(f"Platform: {agent_manager.platform}")
    print(f"ANTHROPIC_API_KEY: {SecretManager.mask_secret(os.getenv('ANTHROPIC_API_KEY', ''))}")
    print(f"WHATSAPP_ACCESS_TOKEN: {SecretManager.mask_secret(os.getenv('WHATSAPP_ACCESS_TOKEN', ''))}")
    print(f"Multi-agent enabled: {agent_manager.multi_agent_enabled}")
    print(f"Available MCP servers: {list(mcp_config.keys())}")
    print(f"Cache enabled: {cache_manager.enabled}")
    print(f"Agent caching: {perf_config['enable_agent_caching']}")
    print(f"DB pool size: {perf_config['db_pool_size']}")
    print("=" * 60)

    # Start background task for periodic cleanup
    asyncio.create_task(periodic_cleanup())


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up all agents on shutdown"""
    print("Shutting down WhatsApp MCP Service...")
    await agent_manager.cleanup_all_agents()
    await cache_manager.close()  # Close Redis connection

    # Close database connections
    try:
        from database import close_db
        await close_db()
    except Exception as e:
        print(f"⚠️  Database cleanup error: {e}")

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
