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

from agents.manager import AgentManager
from whatsapp_mcp.client import WhatsAppClient
from whatsapp_mcp.parser import WhatsAppWebhookParser

# Load environment variables
load_dotenv()

app = FastAPI(title="WhatsApp MCP Service", version="1.0.0")

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

# Initialize Agent Manager with available MCP servers
enable_github = os.getenv("ENABLE_GITHUB_MCP", "false").lower() == "true"
enable_netlify = os.getenv("ENABLE_NETLIFY_MCP", "false").lower() == "true"
agent_manager = AgentManager(
    whatsapp_mcp_tools=[whatsapp_send_tool],
    enable_github=enable_github,
    enable_netlify=enable_netlify
)

# Pydantic models for API
class MessageRequest(BaseModel):
    phone_number: str
    message: str

class MessageResponse(BaseModel):
    response: str
    status: str = "success"


@app.get("/health")
async def health_check():
    """Health check endpoint for Render"""
    return {
        "status": "healthy",
        "service": "whatsapp-mcp",
        "api_key_configured": bool(os.getenv("ANTHROPIC_API_KEY")),
        "whatsapp_configured": bool(os.getenv("WHATSAPP_ACCESS_TOKEN")),
        "github_mcp_enabled": agent_manager.enable_github,
        "github_token_configured": bool(os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")),
        "netlify_mcp_enabled": agent_manager.enable_netlify,
        "netlify_token_configured": bool(os.getenv("NETLIFY_PERSONAL_ACCESS_TOKEN")),
        "active_agents": agent_manager.get_active_agents_count(),
        "available_mcp_servers": list(agent_manager.available_mcp_servers.keys())
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
        return {"status": "error", "message": str(e)}


async def process_whatsapp_message(phone_number: str, message: str):
    """
    Process WhatsApp message with Agent Manager
    Spawns/retrieves agent and sends response back via WhatsApp
    """
    try:
        # Process with Agent Manager
        response = await agent_manager.process_message(phone_number, message)

        # Send response back via WhatsApp
        whatsapp_client.send_message(phone_number, response)

        print(f"✅ Sent response to {phone_number}")

    except Exception as e:
        print(f"❌ Error processing message for {phone_number}: {str(e)}")
        # Send error message to user
        try:
            whatsapp_client.send_message(
                phone_number,
                "Sorry, I encountered an error processing your message. Please try again."
            )
        except Exception as send_error:
            print(f"❌ Failed to send error message: {str(send_error)}")


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
    print(f"ANTHROPIC_API_KEY configured: {bool(os.getenv('ANTHROPIC_API_KEY'))}")
    print(f"WHATSAPP_ACCESS_TOKEN configured: {bool(os.getenv('WHATSAPP_ACCESS_TOKEN'))}")
    print(f"GITHUB_PERSONAL_ACCESS_TOKEN configured: {bool(os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN'))}")
    print(f"\nAvailable MCP servers: {list(agent_manager.available_mcp_servers.keys())}")
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
