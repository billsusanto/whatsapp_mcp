"""
Unified Agent Manager

Platform-agnostic manager for routing messages to single-agent or multi-agent systems.
Eliminates code duplication between AgentManager and GitHubAgentManager.
"""

from typing import Dict, Optional, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agents.agent import Agent
from agents.session.base import BaseSessionManager
from agents.adapters.notification import NotificationAdapter

# Multi-agent system integration
try:
    from agents.collaborative.orchestrator import CollaborativeOrchestrator
    MULTI_AGENT_AVAILABLE = True
except ImportError:
    MULTI_AGENT_AVAILABLE = False
    print("⚠️  Multi-agent system not available")


class UnifiedAgentManager:
    """
    Platform-agnostic agent manager.

    Routes messages to single-agent or multi-agent systems using AI classification.
    Works with any platform via NotificationAdapter pattern.
    """

    def __init__(
        self,
        platform: str,
        session_manager: BaseSessionManager,
        notification_adapter: NotificationAdapter,
        mcp_config: Dict[str, Any],
        enable_multi_agent: bool = True,
        platform_context: Optional[Dict] = None
    ):
        """
        Initialize unified agent manager.

        Args:
            platform: Platform identifier ("whatsapp", "github", etc.)
            session_manager: Session storage implementation
            notification_adapter: Platform notification interface
            mcp_config: MCP server configuration
            enable_multi_agent: Enable multi-agent orchestrator
            platform_context: Platform-specific context (optional)
        """
        self.platform = platform
        self.session_manager = session_manager
        self.notification_adapter = notification_adapter
        self.mcp_config = mcp_config
        self.platform_context = platform_context or {}

        # Agent storage
        self.agents: Dict[str, Agent] = {}
        self.orchestrators: Dict[str, Any] = {}

        # Multi-agent configuration
        self.multi_agent_enabled = False
        if enable_multi_agent and MULTI_AGENT_AVAILABLE:
            # Check if Netlify MCP is available (required for deployments)
            if "netlify" in mcp_config:
                self.multi_agent_enabled = True
                print("✅ Multi-agent orchestrator enabled")
            else:
                print("⚠️  Multi-agent disabled: Netlify MCP not available")
        else:
            print("❌ Multi-agent orchestrator disabled")

        print(f"\n✅ UnifiedAgentManager initialized")
        print(f"   Platform: {platform}")
        print(f"   Session Manager: {type(session_manager).__name__}")
        print(f"   Notification Adapter: {type(notification_adapter).__name__}")
        print(f"   MCP Servers: {list(mcp_config.keys())}")
        print(f"   Multi-agent: {'Enabled' if self.multi_agent_enabled else 'Disabled'}")

    async def process_message(
        self,
        user_id: str,
        message: str,
        context: Optional[Dict] = None
    ) -> str:
        """
        Process a user message with smart routing.

        Routes to multi-agent orchestrator for webapp requests, handles refinements
        intelligently when a task is already in progress.

        Args:
            user_id: User identifier (phone number, repo#issue, etc.)
            message: Message text
            context: Platform-specific context (optional)

        Returns:
            Response message
        """
        # Merge platform context
        full_context = {**self.platform_context, **(context or {})}

        # Check if this user has an active orchestrator
        active_orchestrator = self.orchestrators.get(user_id)

        if active_orchestrator and active_orchestrator.is_active:
            # Orchestrator is currently processing a task
            print(f"🔄 [UNIFIED MANAGER] Active orchestrator found for {user_id}")
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
                del self.orchestrators[user_id]
                return response

            elif message_type == "new_task":
                # User wants to start a completely new task
                print(f"   → User requesting new task while one is active")
                # Ask for confirmation
                return f"""⚠️ The multi-agent team is currently working on your previous request:

🎯 Active task: {active_orchestrator.original_prompt[:100]}

Would you like to:
1. Continue with the current task (send 'continue')
2. Cancel it and start fresh (send 'cancel')
3. Wait for it to complete

Please let me know!"""

            else:
                # Unclassified - treat as conversation
                print(f"   → Unclassified message, treating as general conversation")
                agent = self._get_or_create_agent(user_id)
                return await agent.process_message(message)

        # No active orchestrator - check if this is a new webapp request
        if self.multi_agent_enabled and await self._is_webapp_request(message):
            print(f"🎨 [UNIFIED MANAGER] Multi-agent request detected from {user_id}")
            print(f"   Creating new orchestrator instance...")

            try:
                # Create orchestrator for this user
                orchestrator = await self._create_orchestrator(user_id, full_context)
                self.orchestrators[user_id] = orchestrator

                # Execute multi-agent build
                response = await orchestrator.build_webapp(message)

                # Clean up orchestrator if completed
                if not orchestrator.is_active:
                    del self.orchestrators[user_id]

                return response

            except Exception as e:
                print(f"❌ Multi-agent orchestrator error: {e}")
                import traceback
                traceback.print_exc()

                # Clean up failed orchestrator
                if user_id in self.orchestrators:
                    del self.orchestrators[user_id]

                # Fallback to single agent
                print("   Falling back to single agent...")

        # Regular conversation: use single agent
        agent = self._get_or_create_agent(user_id)
        return await agent.process_message(message)

    async def _is_webapp_request(self, message: str) -> bool:
        """
        Use AI to intelligently detect if user is requesting webapp creation.

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

    async def _classify_message(
        self,
        message: str,
        active_task: str,
        current_phase: str
    ) -> str:
        """
        Classify a message when an orchestrator is already active.

        Args:
            message: New message from user
            active_task: The currently active task description
            current_phase: Current phase of the orchestrator

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

    def _get_or_create_agent(self, user_id: str) -> Agent:
        """
        Get existing agent or create a new one for a user.

        Args:
            user_id: User identifier

        Returns:
            Agent instance for this user
        """
        if user_id not in self.agents:
            # Create new agent with all available MCP servers
            agent = Agent(
                phone_number=user_id,
                session_manager=self.session_manager,
                available_mcp_servers=self.mcp_config
            )
            self.agents[user_id] = agent
            print(f"✨ Created new agent for {user_id}")

        return self.agents[user_id]

    async def _create_orchestrator(
        self,
        user_id: str,
        context: Dict[str, Any]
    ) -> Any:
        """
        Create a multi-agent orchestrator for a user.

        Args:
            user_id: User identifier
            context: Platform-specific context

        Returns:
            CollaborativeOrchestrator instance
        """
        # Create callback that binds the user_id
        async def send_callback(message: str):
            await self.notification_adapter.send_message(user_id, message)

        # Determine platform-specific parameters
        if self.platform == "github":
            orchestrator = CollaborativeOrchestrator(
                user_id=user_id,
                send_message_callback=send_callback,
                platform="github",
                github_context=context,
                available_mcp_servers=self.mcp_config
            )
        else:
            # WhatsApp or other platforms
            orchestrator = CollaborativeOrchestrator(
                user_id=user_id,
                send_message_callback=send_callback,
                platform=self.platform,
                available_mcp_servers=self.mcp_config
            )

        print(f"🎭 Created new orchestrator for {user_id} on {self.platform}")
        return orchestrator

    async def stream_response(self, user_id: str, message: str):
        """
        Stream response for a message (single-agent only).

        Args:
            user_id: User identifier
            message: User's message text

        Yields:
            Response text chunks
        """
        agent = self._get_or_create_agent(user_id)
        async for chunk in agent.stream_response(message):
            yield chunk

    async def reset_conversation(self, user_id: str):
        """Reset conversation for a user."""
        if user_id in self.agents:
            await self.agents[user_id].reset_conversation()
        if hasattr(self.session_manager, '_clear_session_async'):
            await self.session_manager._clear_session_async(user_id)
        else:
            self.session_manager.clear_session(user_id)
        print(f"🔄 Reset conversation for {user_id}")

    async def cleanup_agent(self, user_id: str):
        """Clean up and remove an agent."""
        if user_id in self.agents:
            await self.agents[user_id].cleanup()
            del self.agents[user_id]
            print(f"🧹 Cleaned up agent for {user_id}")

    async def cleanup_all_agents(self):
        """Clean up all agents."""
        for user_id in list(self.agents.keys()):
            await self.cleanup_agent(user_id)
        print("✅ All agents cleaned up")

    def get_active_agents_count(self) -> int:
        """Get number of active agents."""
        return len(self.agents)

    async def cleanup_expired_sessions(self) -> int:
        """Cleanup expired sessions via session manager."""
        if hasattr(self.session_manager, 'cleanup_expired_sessions_async'):
            return await self.session_manager.cleanup_expired_sessions_async()
        else:
            return self.session_manager.cleanup_expired_sessions()
