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
        self.orchestrators: Dict[str, any] = {}  # Per-user orchestrators

        if MULTI_AGENT_AVAILABLE and self.enable_netlify:
            try:
                self.multi_agent_enabled = True
                print("✅ Multi-agent orchestrator enabled (per-user instances)")
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
        Process a message with smart context merging

        Routes to multi-agent orchestrator for webapp requests, handles refinements
        intelligently when a task is already in progress.

        Args:
            phone_number: User's phone number
            message: Message text

        Returns:
            Agent's response
        """
        # Check if this user has an active orchestrator
        active_orchestrator = self.orchestrators.get(phone_number)

        if active_orchestrator and active_orchestrator.is_active:
            # Orchestrator is currently processing a task
            print(f"🔄 [MANAGER] Active orchestrator found for {phone_number}")
            print(f"   Current phase: {active_orchestrator.current_phase}")
            print(f"   Classifying new message...")

            # Use AI to classify the incoming message
            message_type = await self._classify_message(
                message=message,
                active_task=active_orchestrator.original_prompt,
                current_phase=active_orchestrator.current_phase
            )

            print(f"   Message classification: {message_type}")

            # Route based on classification
            if message_type == "refinement":
                # User is refining/modifying the current task
                print(f"   → Routing to orchestrator.handle_refinement()")
                response = await active_orchestrator.handle_refinement(message)
                return f"✅ Refinement applied to ongoing task.\n\n{response if isinstance(response, str) and response.startswith('❌') else ''}"

            elif message_type == "status_query":
                # User is asking for status
                print(f"   → Routing to orchestrator.handle_status_query()")
                return await active_orchestrator.handle_status_query()

            elif message_type == "cancellation":
                # User wants to cancel current task
                print(f"   → Routing to orchestrator.handle_cancellation()")
                response = await active_orchestrator.handle_cancellation()
                # Clean up orchestrator
                del self.orchestrators[phone_number]
                return response

            elif message_type == "new_task":
                # User wants to start a completely new task
                print(f"   → User requesting new task while one is active")
                # Ask for confirmation
                return """⚠️ The multi-agent team is currently working on your previous request:

🎯 Active task: {}

Would you like to:
1. Continue with the current task (send 'continue')
2. Cancel it and start fresh (send 'cancel')
3. Wait for it to complete

Please let me know!""".format(active_orchestrator.original_prompt[:100])

            else:
                # Unclassified - treat as conversation
                print(f"   → Unclassified message, treating as general conversation")
                agent = self.get_or_create_agent(phone_number)
                return await agent.process_message(message)

        # No active orchestrator - check if this is a new webapp request
        if self.multi_agent_enabled and await self._is_webapp_request(message):
            print(f"🎨 [MANAGER] Multi-agent request detected from {phone_number}")
            print(f"   Creating new orchestrator instance...")

            try:
                # Create new orchestrator for this user
                orchestrator = CollaborativeOrchestrator(
                    mcp_servers=self.available_mcp_servers,
                    user_phone_number=phone_number
                )
                self.orchestrators[phone_number] = orchestrator

                # Use multi-agent orchestrator
                response = await orchestrator.build_webapp(message)

                # Clean up orchestrator if completed
                if not orchestrator.is_active:
                    del self.orchestrators[phone_number]

                return response

            except Exception as e:
                print(f"❌ Multi-agent orchestrator error: {e}")
                import traceback
                traceback.print_exc()

                # Clean up failed orchestrator
                if phone_number in self.orchestrators:
                    del self.orchestrators[phone_number]

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

    async def _classify_message(self, message: str, active_task: str, current_phase: str) -> str:
        """
        Classify a message when an orchestrator is already active

        Uses AI to determine if the user is:
        - Refining/modifying the current task
        - Asking for status
        - Wanting to cancel
        - Starting a completely new task
        - Just having a conversation

        Args:
            message: New message from user
            active_task: The currently active task description
            current_phase: Current phase of the orchestrator (design, implementation, review, deployment)

        Returns:
            Message type: "refinement", "status_query", "cancellation", "new_task", or "conversation"
        """
        classification_prompt = f"""You are a message classifier for a multi-agent webapp development system.

**Context:**
- An AI team is currently working on: "{active_task}"
- Current phase: {current_phase}

**New message from user:**
"{message}"

**Your Task:**
Classify this message into ONE of these categories:

1. **refinement** - User wants to modify/refine the current task
   Examples: "Make it blue", "Add a login feature", "Change the colors", "Use a different font"

2. **status_query** - User is asking about progress/status
   Examples: "How's it going?", "What's the status?", "Are you done yet?", "What are you working on?"

3. **cancellation** - User wants to cancel/stop the current task
   Examples: "Cancel", "Stop", "Never mind", "Forget it", "Cancel this"

4. **new_task** - User wants to start a completely different, unrelated task
   Examples: "Build me a booking system" (when currently building a todo app)

5. **conversation** - General conversation, unrelated to the task
   Examples: "Hello", "Thanks", "How are you?"

**Important Guidelines:**
- If the message is requesting changes/additions to the CURRENT task → "refinement"
- If the message is about a DIFFERENT task entirely → "new_task"
- If unclear, default to "refinement" if it could be related to current task
- Short messages like "blue", "add auth", "change that" → "refinement"

**Output Format (JSON):**
{{
  "classification": "refinement" | "status_query" | "cancellation" | "new_task" | "conversation",
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation"
}}"""

        try:
            # Create a temporary Claude SDK for classification
            from sdk.claude_sdk import ClaudeSDK
            classifier_sdk = ClaudeSDK(available_mcp_servers={})

            response = await classifier_sdk.send_message(classification_prompt)
            await classifier_sdk.close()

            # Extract JSON
            import json
            import re

            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
            elif response.strip().startswith('{'):
                result = json.loads(response)
            else:
                # Fallback: default to conversation
                print(f"⚠️  Could not parse classification response")
                return "conversation"

            classification = result.get('classification', 'conversation')
            confidence = result.get('confidence', 0.0)
            reasoning = result.get('reasoning', 'N/A')

            print(f"   🧠 Message classification: {classification} (confidence: {confidence:.2f})")
            print(f"   💭 Reasoning: {reasoning}")

            return classification

        except Exception as e:
            print(f"⚠️  Error in message classification: {e}")
            # Fallback heuristics
            message_lower = message.lower()

            # Check for status queries
            status_keywords = ["status", "progress", "done", "how's it going", "what's happening"]
            if any(kw in message_lower for kw in status_keywords):
                return "status_query"

            # Check for cancellation
            cancel_keywords = ["cancel", "stop", "forget", "never mind"]
            if any(kw in message_lower for kw in cancel_keywords):
                return "cancellation"

            # Default to refinement if short (likely a modification)
            if len(message.split()) <= 5:
                return "refinement"

            # Otherwise treat as conversation
            return "conversation"

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
