"""
Agent Manager

Manages the lifecycle of multiple Claude agents (one per WhatsApp user)
"""

from typing import Dict, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agents.agent import Agent
from agents.session import SessionManager

# Phase 1.5: Multi-agent system integration
try:
    from agents.collaborative.orchestrator import CollaborativeOrchestrator
    MULTI_AGENT_AVAILABLE = True
except ImportError:
    MULTI_AGENT_AVAILABLE = False
    print("⚠️  Multi-agent system not available")


class AgentManager:
    """Manages multiple agent instances"""

    def __init__(self, whatsapp_mcp_tools: Optional[list] = None, enable_github: bool = False, enable_netlify: bool = False):
        """
        Initialize the agent manager

        Args:
            whatsapp_mcp_tools: List of WhatsApp MCP tools
            enable_github: Whether to enable GitHub MCP integration
            enable_netlify: Whether to enable Netlify MCP integration
        """
        # Session TTL: 60 minutes (1 hour), max history: 10 messages for memory optimization
        self.session_manager = SessionManager(ttl_minutes=60, max_history=10)
        self.agents: Dict[str, Agent] = {}

        # Build available MCP servers dict
        self.available_mcp_servers = {}

        # 1. Add WhatsApp MCP if tools provided
        if whatsapp_mcp_tools:
            self.available_mcp_servers["whatsapp"] = whatsapp_mcp_tools
            print(f"✅ WhatsApp MCP configured with {len(whatsapp_mcp_tools)} tools")

        # 2. Add GitHub MCP if enabled
        self.enable_github = enable_github
        if self.enable_github:
            try:
                sys.path.append(os.path.dirname(os.path.dirname(__file__)))
                from github_mcp.server import create_github_mcp_config

                # Create GitHub MCP config and add to available servers
                github_config = create_github_mcp_config()
                self.available_mcp_servers["github"] = github_config
                print("✅ GitHub MCP configured")
            except ValueError as e:
                print(f"⚠️  GitHub MCP not available: {e}")
                print("   Set GITHUB_PERSONAL_ACCESS_TOKEN environment variable to enable")
                self.enable_github = False
            except Exception as e:
                print(f"❌ Failed to configure GitHub MCP: {e}")
                import traceback
                traceback.print_exc()
                self.enable_github = False

        # 3. Add Netlify MCP if enabled
        self.enable_netlify = enable_netlify
        if self.enable_netlify:
            try:
                sys.path.append(os.path.dirname(os.path.dirname(__file__)))
                from netlify_mcp.server import create_netlify_mcp_config

                # Create Netlify MCP config and add to available servers
                netlify_config = create_netlify_mcp_config()
                self.available_mcp_servers["netlify"] = netlify_config
                print("✅ Netlify MCP configured")
            except ValueError as e:
                print(f"⚠️  Netlify MCP not available: {e}")
                print("   Set NETLIFY_PERSONAL_ACCESS_TOKEN environment variable to enable")
                self.enable_netlify = False
            except Exception as e:
                print(f"❌ Failed to configure Netlify MCP: {e}")
                import traceback
                traceback.print_exc()
                self.enable_netlify = False

        # 4. Initialize Multi-Agent Orchestrator (Phase 1.5+)
        self.multi_agent_enabled = False
        self.orchestrator = None

        if MULTI_AGENT_AVAILABLE and self.enable_netlify:
            try:
                # Note: Orchestrator is initialized without phone number
                # Phone number will be set dynamically when processing messages
                self.orchestrator = None
                self.multi_agent_enabled = True
                print("✅ Multi-agent orchestrator enabled (will be initialized per user)")
            except Exception as e:
                print(f"⚠️  Multi-agent orchestrator failed to initialize: {e}")
                self.multi_agent_enabled = False

        print(f"\nAgentManager initialized")
        print(f"Available MCP servers: {list(self.available_mcp_servers.keys())}")
        print(f"Multi-agent mode: {'✅ Enabled' if self.multi_agent_enabled else '❌ Disabled'}")

    def get_or_create_agent(self, phone_number: str) -> Agent:
        """
        Get existing agent or create a new one for a phone number

        Args:
            phone_number: User's WhatsApp phone number

        Returns:
            Agent instance for this user
        """
        if phone_number not in self.agents:
            # Create new agent with all available MCP servers
            agent = Agent(
                phone_number=phone_number,
                session_manager=self.session_manager,
                available_mcp_servers=self.available_mcp_servers
            )
            self.agents[phone_number] = agent

        return self.agents[phone_number]

    async def process_message(self, phone_number: str, message: str) -> str:
        """
        Process a message by routing to the appropriate agent

        Phase 1.5: Routes to multi-agent orchestrator for webapp requests,
        single agent for regular conversations.

        Args:
            phone_number: User's phone number
            message: Message text

        Returns:
            Agent's response
        """
        # Phase 1.5: Check if this is a webapp build request using AI detection
        if self.multi_agent_enabled and await self._is_webapp_request(message):
            print(f"🎨 Multi-agent request detected from {phone_number}")
            print(f"   Routing to collaborative orchestrator...")

            try:
                # Create or get orchestrator for this user
                if self.orchestrator is None:
                    self.orchestrator = CollaborativeOrchestrator(
                        mcp_servers=self.available_mcp_servers,
                        user_phone_number=phone_number
                    )
                elif self.orchestrator.user_phone_number != phone_number:
                    # If different user, update phone number
                    self.orchestrator.user_phone_number = phone_number
                    # Reinitialize WhatsApp client with new number
                    if "whatsapp" in self.available_mcp_servers:
                        try:
                            from whatsapp_mcp.client import WhatsAppClient
                            self.orchestrator.whatsapp_client = WhatsAppClient()
                        except Exception as e:
                            print(f"⚠️  Failed to update WhatsApp client: {e}")

                # Use multi-agent orchestrator
                response = await self.orchestrator.build_webapp(message)
                return response
            except Exception as e:
                print(f"❌ Multi-agent orchestrator error: {e}")
                import traceback
                traceback.print_exc()
                # Fallback to single agent
                print("   Falling back to single agent...")

        # Regular conversation: use single agent
        agent = self.get_or_create_agent(phone_number)
        return await agent.process_message(message)

    async def _is_webapp_request(self, message: str) -> bool:
        """
        Use AI to intelligently detect if user is requesting webapp creation

        Instead of hardcoded keyword matching, uses Claude to understand intent.

        Args:
            message: User's message text

        Returns:
            True if message appears to be a webapp build request
        """
        # Quick heuristic for obvious cases to save API calls
        quick_check_keywords = ["build a", "create a", "make a", "webapp", "website", "application"]
        if any(keyword in message.lower() for keyword in quick_check_keywords):
            # Likely a webapp request, but verify with AI
            pass
        elif len(message.split()) <= 3:
            # Very short messages are unlikely to be webapp requests
            return False

        # Use AI to determine intent
        decision_prompt = f"""Analyze this user message and determine if they are requesting webapp/website creation or just having a conversation.

**User Message:** "{message}"

**Your Task:**
Determine if this is:
A) A request to build/create/design a webapp, website, or application
B) A regular conversation, question, or general request

**Examples of webapp requests:**
- "Build me a todo list app"
- "Create a booking website"
- "I need a portfolio site"
- "Make a dashboard for my business"
- "Design a landing page"

**Examples of regular conversation:**
- "How are you?"
- "Tell me about AI"
- "What can you do?"
- "Hello"
- "Thanks for your help"

**Output Format (JSON):**
{{
  "is_webapp_request": true | false,
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation of the decision"
}}

Be precise. Only return true if the user is clearly requesting webapp/website development."""

        try:
            # Create a temporary Claude SDK for decision making
            from sdk.claude_sdk import ClaudeSDK
            decision_sdk = ClaudeSDK(available_mcp_servers={})

            response = await decision_sdk.send_message(decision_prompt)
            await decision_sdk.close()

            # Extract JSON
            import json
            import re

            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                decision = json.loads(json_match.group(1))
            elif response.strip().startswith('{'):
                decision = json.loads(response)
            else:
                # Fallback: if AI didn't return JSON, assume not webapp request
                print(f"⚠️  Could not parse webapp detection response, defaulting to single agent")
                return False

            is_webapp = decision.get('is_webapp_request', False)
            confidence = decision.get('confidence', 0.0)
            reasoning = decision.get('reasoning', 'N/A')

            print(f"   🧠 Webapp detection: {is_webapp} (confidence: {confidence:.2f})")
            print(f"   💭 Reasoning: {reasoning}")

            return is_webapp

        except Exception as e:
            print(f"⚠️  Error in webapp detection: {e}")
            # Fallback to keyword matching only on error
            webapp_keywords = ["build", "create", "make", "website", "webapp", "app", "site"]
            return any(keyword in message.lower() for keyword in webapp_keywords)

    async def stream_response(self, phone_number: str, message: str):
        """
        Stream response for a message

        Args:
            phone_number: User's phone number
            message: User's message text

        Yields:
            Response text chunks
        """
        agent = self.get_or_create_agent(phone_number)
        async for chunk in agent.stream_response(message):
            yield chunk

    def reset_conversation(self, phone_number: str):
        """Reset conversation for a user"""
        if phone_number in self.agents:
            self.agents[phone_number].reset_conversation()

    async def cleanup_agent(self, phone_number: str):
        """Clean up and remove an agent"""
        if phone_number in self.agents:
            await self.agents[phone_number].cleanup()
            del self.agents[phone_number]
            print(f"Cleaned up agent for {phone_number}")

    async def cleanup_all_agents(self):
        """Clean up all agents"""
        for phone_number in list(self.agents.keys()):
            await self.cleanup_agent(phone_number)
        print("All agents cleaned up")

    def get_active_agents_count(self) -> int:
        """Get number of active agents"""
        return len(self.agents)

    def cleanup_expired_sessions(self):
        """Cleanup expired sessions via session manager"""
        return self.session_manager.cleanup_expired_sessions()
