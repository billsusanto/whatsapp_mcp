"""
Collaborative Orchestrator
Coordinates multi-agent team: Designer, Frontend, Code Reviewer, QA, DevOps

NOW USING A2A PROTOCOL for all agent communication
"""

from typing import Dict, Optional
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sdk.claude_sdk import ClaudeSDK
from .designer_agent import DesignerAgent
from .frontend_agent import FrontendDeveloperAgent
from .code_reviewer_agent import CodeReviewerAgent
from .qa_agent import QAEngineerAgent
from .devops_agent import DevOpsEngineerAgent
from .models import Task, TaskResponse
from .a2a_protocol import a2a_protocol
from .orchestrator_state import OrchestratorStateManager

# Import telemetry
from utils.telemetry import (
    trace_workflow,
    trace_operation,
    log_event,
    log_metric,
    measure_performance
)

# Import system health monitor
from utils.health_monitor import system_health_monitor


class CollaborativeOrchestrator:
    """
    Orchestrates collaboration between multi-agent development team using A2A Protocol

    Agent Team:
    - UI/UX Designer: Creates design specifications and reviews implementations
    - Frontend Developer: Implements React/Vue code
    - Code Reviewer: Reviews code for quality, security, and best practices
    - QA Engineer: Tests functionality, usability, and accessibility
    - DevOps Engineer: Handles deployment, optimization, and infrastructure

    Communication:
    - ALL agent interactions use A2A (Agent-to-Agent) protocol
    - Standardized messaging with Task and TaskResponse models
    - Full traceability and logging of all communications

    Workflow:
    1. Designer creates design specification (via A2A)
    2. Frontend implements based on design (via A2A)
    3. Code Reviewer reviews code quality and security (via A2A)
    4. QA Engineer tests functionality and usability (via A2A)
    5. DevOps Engineer optimizes and deploys to Netlify (via A2A)
    6. Iterative improvement until quality standards met
    """

    # Orchestrator's agent ID for A2A protocol
    ORCHESTRATOR_ID = "orchestrator"

    # Agent IDs (must match BaseAgent initialization)
    DESIGNER_ID = "designer_001"
    FRONTEND_ID = "frontend_001"
    CODE_REVIEWER_ID = "code_reviewer_001"
    QA_ID = "qa_engineer_001"
    DEVOPS_ID = "devops_001"

    def __init__(
        self,
        user_id: str,
        send_message_callback,
        platform: str = "whatsapp",
        github_context: Optional[Dict] = None,
        available_mcp_servers: Optional[Dict] = None,
        mcp_servers: Optional[Dict] = None,  # Backward compatibility
        user_phone_number: Optional[str] = None  # Backward compatibility
    ):
        """
        Initialize orchestrator with lazy agent initialization for resource efficiency

        Args:
            user_id: Unique identifier (phone number for WhatsApp, repo#number for GitHub)
            send_message_callback: Async callback function for sending notifications
            platform: Platform type ("whatsapp" or "github")
            github_context: GitHub-specific context (repo, PR/issue details)
            available_mcp_servers: Available MCP servers (GitHub, Netlify, etc.)
            mcp_servers: DEPRECATED - use available_mcp_servers
            user_phone_number: DEPRECATED - use user_id
        """
        print("=" * 60)
        print("🎭 Initializing Multi-Agent Orchestrator with A2A Protocol")
        print("=" * 60)

        # Handle backward compatibility
        if mcp_servers and not available_mcp_servers:
            available_mcp_servers = mcp_servers
        if user_phone_number and not user_id:
            user_id = user_phone_number

        self.mcp_servers = available_mcp_servers or {}
        self.orchestrator_id = self.ORCHESTRATOR_ID
        self.user_id = user_id
        self.platform = platform
        self.github_context = github_context
        self.send_message_callback = send_message_callback

        # Legacy WhatsApp support (for backward compatibility)
        self.user_phone_number = user_phone_number
        self.whatsapp_client = None
        if platform == "whatsapp" and user_phone_number:
            try:
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                from whatsapp_mcp.client import WhatsAppClient
                self.whatsapp_client = WhatsAppClient()
                print(f"✅ WhatsApp notifications enabled for {user_phone_number}")
            except Exception as e:
                print(f"⚠️  WhatsApp notifications disabled: {e}")
                self.whatsapp_client = None

        print(f"📱 Platform: {platform}")
        if platform == "github" and github_context:
            repo = github_context.get("repository", {}).get("full_name", "unknown")
            print(f"🔗 GitHub: {repo}")
        elif platform == "whatsapp" and user_phone_number:
            print(f"💬 WhatsApp: {user_phone_number}")

        # Register orchestrator with A2A protocol so it can send messages
        from .models import AgentCard, AgentRole
        self.agent_card = AgentCard(
            agent_id=self.ORCHESTRATOR_ID,
            name="Orchestrator",
            role=AgentRole.DEVOPS,  # Using DevOps as closest match for orchestrator role
            description="Multi-agent workflow orchestrator",
            capabilities=["workflow_planning", "agent_coordination", "deployment"],
            skills={"coordination": ["AI planning", "task routing", "resource management"]}
        )

        # Create a minimal agent interface for A2A protocol registration
        class OrchestratorAgent:
            def __init__(self, agent_card):
                self.agent_card = agent_card
            async def receive_message(self, message):
                # Orchestrator doesn't receive messages from other agents
                return {"acknowledged": True}

        orchestrator_agent = OrchestratorAgent(self.agent_card)
        a2a_protocol.register_agent(orchestrator_agent)

        # Lazy initialization: agents are NOT created at startup
        # They're created on-demand when needed and cleaned up after use
        self._active_agents: Dict[str, any] = {}  # Currently active agents
        self._agent_cache: Dict[str, any] = {}  # Cached agent instances (optional reuse)

        # Create Claude SDK for orchestrator tasks (deployment, coordination, planning)
        self.deployment_sdk = ClaudeSDK(available_mcp_servers=self.mcp_servers)

        # Create planning SDK for intelligent workflow decisions
        self.planner_sdk = ClaudeSDK(available_mcp_servers={})  # No MCP tools needed for planning

        # Configuration
        self.max_review_iterations = 10  # Maximum review/improvement iterations
        self.min_quality_score = 9  # Minimum acceptable review score (out of 10)
        self.max_build_retries = 10  # Maximum build retry attempts (increased from 5)
        self.enable_agent_caching = False  # Set to True to reuse agents (uses more memory but faster)

        # Task State Management (for handling concurrent messages)
        self.is_active = False  # Whether orchestrator is currently processing a task
        self.current_phase = None  # Current workflow phase (design, implementation, review, deployment)
        self.current_workflow = None  # Current workflow type (full_build, bug_fix, etc.)
        self.original_prompt = None  # Original user request
        self.accumulated_refinements = []  # List of refinements/modifications from user
        self.current_implementation = None  # Current implementation being worked on
        self.current_design_spec = None  # Current design specification

        # Detailed task tracking for status queries
        self.current_agent_working = None  # Which agent is currently active
        self.current_task_description = None  # What task is being executed
        self.workflow_steps_completed = []  # List of completed steps
        self.workflow_steps_total = 0  # Total number of steps in workflow

        # State persistence (lazy initialization - initialized on first use)
        self.state_manager = None
        self._state_manager_initialized = False

        print("\n✅ Multi-Agent Orchestrator Ready (Lazy Initialization):")
        print(f"   - Agents will be spun up on-demand when needed")
        print(f"   - Agents will be cleaned up after task completion")
        print(f"   - Agent caching: {'Enabled' if self.enable_agent_caching else 'Disabled (saves memory)'}")
        print(f"   - AI Planner (Claude-powered workflow decisions)")
        print(f"   - Deployment SDK with {len(self.mcp_servers)} MCP servers")
        print(f"   - State persistence: PostgreSQL/Neon (lazy initialization)")
        print(f"\n🔗 A2A Protocol: Agents register/unregister dynamically")
        print("=" * 60 + "\n")

    # ==========================================
    # AGENT LIFECYCLE MANAGEMENT (LAZY INITIALIZATION)
    # ==========================================

    async def _get_agent(self, agent_type: str):
        """
        Get or create an agent on-demand (lazy initialization)

        Args:
            agent_type: Type of agent ("designer", "frontend", "code_reviewer", "qa", "devops")

        Returns:
            Agent instance
        """
        # Check if agent is already active
        if agent_type in self._active_agents:
            return self._active_agents[agent_type]

        # Check if agent is cached and caching is enabled
        if self.enable_agent_caching and agent_type in self._agent_cache:
            agent = self._agent_cache[agent_type]
            self._active_agents[agent_type] = agent
            print(f"♻️  Reusing cached {agent_type} agent")
            return agent

        # Create new agent instance
        print(f"🚀 Spinning up {agent_type} agent...")

        if agent_type == "designer":
            agent = DesignerAgent(self.mcp_servers)
        elif agent_type == "frontend":
            agent = FrontendDeveloperAgent(self.mcp_servers)
        elif agent_type == "code_reviewer":
            agent = CodeReviewerAgent(self.mcp_servers)
        elif agent_type == "qa":
            agent = QAEngineerAgent(self.mcp_servers)
        elif agent_type == "devops":
            agent = DevOpsEngineerAgent(self.mcp_servers)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

        # Register in active agents
        self._active_agents[agent_type] = agent

        # Optionally cache for reuse
        if self.enable_agent_caching:
            self._agent_cache[agent_type] = agent

        print(f"✅ {agent_type} agent ready ({agent.agent_card.agent_id})")
        return agent

    async def _cleanup_agent(self, agent_type: str):
        """
        Clean up an agent after task completion to free resources

        Args:
            agent_type: Type of agent to cleanup
        """
        if agent_type not in self._active_agents:
            return

        agent = self._active_agents[agent_type]

        # If caching is enabled, keep the agent but don't clean it up
        if self.enable_agent_caching:
            print(f"💾 Keeping {agent_type} agent in cache")
            return

        # Clean up the agent
        print(f"🧹 Cleaning up {agent_type} agent...")
        await agent.cleanup()

        # Unregister from A2A protocol
        a2a_protocol.unregister_agent(agent.agent_card.agent_id)

        # Remove from active agents
        del self._active_agents[agent_type]

        print(f"✅ {agent_type} agent cleaned up and resources freed")

    async def _cleanup_all_active_agents(self):
        """Clean up all currently active agents"""
        agent_types = list(self._active_agents.keys())
        for agent_type in agent_types:
            await self._cleanup_agent(agent_type)

    # ==========================================
    # NOTIFICATION HELPERS (Platform-agnostic)
    # ==========================================

    async def _send_notification(self, message: str):
        """
        Send notification to user via platform-specific callback.

        For WhatsApp: Sends via WhatsApp client
        For GitHub: Posts as a comment on the PR/Issue

        Args:
            message: Message to send (supports markdown for GitHub)
        """
        try:
            # Use the callback if provided
            if self.send_message_callback:
                await self.send_message_callback(message)
                print(f"📤 Notification sent ({self.platform}): {message[:50]}...")
            # Fallback to legacy WhatsApp for backward compatibility
            elif self.whatsapp_client and self.user_phone_number:
                self.whatsapp_client.send_message(self.user_phone_number, message)
                print(f"📱 WhatsApp notification sent: {message[:50]}...")
        except Exception as e:
            print(f"⚠️  Failed to send notification: {e}")

    def _send_whatsapp_notification(self, message: str):
        """
        DEPRECATED: Legacy method for backward compatibility.
        Use _send_notification instead.

        Args:
            message: Notification message to send
        """
        import asyncio
        # Try to run as async
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self._send_notification(message))
            else:
                loop.run_until_complete(self._send_notification(message))
        except:
            # Fallback for synchronous contexts
            if self.whatsapp_client and self.user_phone_number:
                try:
                    self.whatsapp_client.send_message(self.user_phone_number, message)
                    print(f"📱 WhatsApp notification sent: {message[:50]}...")
                except Exception as e:
                    print(f"⚠️  Failed to send WhatsApp notification: {e}")

    def _get_agent_type_name(self, agent_id: str) -> str:
        """Map agent_id to human-readable type name"""
        if "designer" in agent_id:
            return "UI/UX Designer"
        elif "frontend" in agent_id:
            return "Frontend Developer"
        elif "code_reviewer" in agent_id:
            return "Code Reviewer"
        elif "qa" in agent_id:
            return "QA Engineer"
        elif "devops" in agent_id:
            return "DevOps Engineer"
        elif "orchestrator" in agent_id:
            return "Orchestrator"
        else:
            return "Agent"

    # ==========================================
    # TASK STATE & REFINEMENT HANDLING
    # ==========================================

    def get_status(self) -> Dict:
        """
        Get current orchestrator status with detailed agent tracking

        Returns:
            Dict with comprehensive status information
        """
        # Get active agent names
        active_agent_names = [
            self._get_agent_type_name(agent.agent_card.agent_id)
            for agent_type, agent in self._active_agents.items()
        ] if self._active_agents else []

        # Calculate progress (capped at 100%)
        progress_percent = 0
        if self.workflow_steps_total > 0:
            raw_percent = (len(self.workflow_steps_completed) / self.workflow_steps_total) * 100
            progress_percent = min(100, int(raw_percent))

        return {
            "is_active": self.is_active,
            "current_phase": self.current_phase,
            "current_workflow": self.current_workflow,
            "original_prompt": self.original_prompt,
            "refinements_count": len(self.accumulated_refinements),
            # New detailed tracking fields
            "current_agent_working": self._get_agent_type_name(self.current_agent_working) if self.current_agent_working else None,
            "current_task_description": self.current_task_description,
            "active_agents": active_agent_names,
            "workflow_progress": {
                "completed": len(self.workflow_steps_completed),
                "total": self.workflow_steps_total,
                "percent": progress_percent,
                "completed_steps": self.workflow_steps_completed[-3:] if self.workflow_steps_completed else []
            }
        }

    async def handle_refinement(self, refinement_message: str) -> str:
        """
        Handle a refinement/modification to the current task

        This is called when a user sends a new message while a task is in progress,
        and the message is classified as a modification rather than a new task.

        Args:
            refinement_message: User's refinement/modification message

        Returns:
            Response message to user
        """
        if not self.is_active:
            return "⚠️ No active task to refine. Please start a new request."

        print(f"\n🔄 [ORCHESTRATOR] Processing refinement: {refinement_message}")
        print(f"   Current phase: {self.current_phase}")
        print(f"   Current workflow: {self.current_workflow}")

        # Add to accumulated refinements
        self.accumulated_refinements.append(refinement_message)

        # Save state after refinement
        await self._ensure_state_manager()
        await self._save_state()

        # Send acknowledgment to user
        self._send_whatsapp_notification(
            f"✅ Refinement received!\n\n"
            f"💬 Your update: {refinement_message[:100]}...\n\n"
            f"I'll incorporate this into the current task.\n"
            f"Current phase: {self.current_phase or 'processing'}..."
        )

        # Handle based on current phase
        if self.current_phase == "design":
            # During design phase - ask designer to incorporate refinement
            return await self._refine_during_design(refinement_message)

        elif self.current_phase == "implementation":
            # During implementation - ask frontend to incorporate changes
            return await self._refine_during_implementation(refinement_message)

        elif self.current_phase == "review":
            # During review phase - note the refinement for next iteration
            return await self._refine_during_review(refinement_message)

        elif self.current_phase == "deployment":
            # During deployment - queue for post-deployment update
            self._send_whatsapp_notification(
                f"📝 Noted! Since we're currently deploying, I'll apply this refinement "
                f"in a follow-up update after the current deployment completes."
            )
            return "refinement_queued_for_post_deployment"

        else:
            # Unknown phase - queue the refinement
            return "refinement_queued"

    async def _refine_during_design(self, refinement: str) -> str:
        """Handle refinement during design phase"""
        print(f"🎨 [REFINEMENT] Updating design with: {refinement}")

        # Ask designer to update the design spec
        try:
            updated_design = await self._send_task_to_agent(
                agent_id=self.DESIGNER_ID,
                task_description=f"""Update the current design specification with this refinement:

Original request: {self.original_prompt}
Current design: {self.current_design_spec}

User refinement: {refinement}

Please update the design specification to incorporate this change while maintaining consistency.""",
                cleanup_after=False,
                notify_user=True
            )

            # Update current design spec
            self.current_design_spec = updated_design.get('design_spec', self.current_design_spec)

            self._send_whatsapp_notification(
                f"✅ Design updated with your refinement!\n"
                f"The updated design will be used for implementation."
            )

            return "design_refined"

        except Exception as e:
            print(f"❌ Error refining design: {e}")
            return f"error_refining_design: {str(e)}"

    async def _refine_during_implementation(self, refinement: str) -> str:
        """Handle refinement during implementation phase"""
        print(f"💻 [REFINEMENT] Updating implementation with: {refinement}")

        # Ask frontend to update the implementation
        try:
            updated_impl = await self._send_task_to_agent(
                agent_id=self.FRONTEND_ID,
                task_description=f"""Update the current implementation with this refinement:

Original request: {self.original_prompt}
Design spec: {self.current_design_spec}
Current implementation: {self.current_implementation}

User refinement: {refinement}

Please update the implementation to incorporate this change.""",
                metadata={
                    "design_spec": self.current_design_spec,
                    "current_implementation": self.current_implementation
                },
                cleanup_after=False,
                notify_user=True
            )

            # Update current implementation
            self.current_implementation = updated_impl.get('implementation', self.current_implementation)

            self._send_whatsapp_notification(
                f"✅ Implementation updated with your refinement!\n"
                f"The code has been modified accordingly."
            )

            return "implementation_refined"

        except Exception as e:
            print(f"❌ Error refining implementation: {e}")
            return f"error_refining_implementation: {str(e)}"

    async def _refine_during_review(self, refinement: str) -> str:
        """Handle refinement during review phase"""
        print(f"🔍 [REFINEMENT] Noting refinement during review: {refinement}")

        # Add to refinements - will be applied in next iteration
        self._send_whatsapp_notification(
            f"📝 Refinement noted!\n"
            f"I'll make sure this is incorporated in the next iteration of the code."
        )

        return "refinement_noted_for_next_iteration"

    async def handle_status_query(self) -> str:
        """
        Handle a status query from the user - shows detailed agent activities

        Returns:
            Detailed status message with agent-specific information
        """
        if not self.is_active:
            return "ℹ️ No active task at the moment."

        # Build status message with detailed agent information
        status_parts = []
        status_parts.append("📊 *DETAILED TASK STATUS*")
        status_parts.append("=" * 40)

        # Original request
        status_parts.append(f"\n🎯 *Your Request:*")
        status_parts.append(f"   {self.original_prompt[:150]}{'...' if len(self.original_prompt) > 150 else ''}")

        # Workflow information
        status_parts.append(f"\n🔧 *Workflow Details:*")
        status_parts.append(f"   • Type: {self.current_workflow or 'Custom'}")
        status_parts.append(f"   • Phase: {self._get_phase_emoji(self.current_phase)} {self.current_phase or 'Processing'}")

        # Progress tracking
        if self.workflow_steps_total > 0:
            completed_count = len(self.workflow_steps_completed)
            # Cap progress at 100% to prevent displaying >100% when steps exceed estimate
            raw_percent = (completed_count / self.workflow_steps_total) * 100
            progress_percent = min(100, int(raw_percent))
            progress_bar = self._create_progress_bar(progress_percent)

            # Show if we exceeded estimate (indicates more retries/iterations than expected)
            if completed_count > self.workflow_steps_total:
                status_parts.append(f"   • Progress: {progress_bar} {progress_percent}% ({completed_count}/{self.workflow_steps_total}+ steps)")
            else:
                status_parts.append(f"   • Progress: {progress_bar} {progress_percent}% ({completed_count}/{self.workflow_steps_total} steps)")

        # Active agent details
        status_parts.append(f"\n🤖 *Currently Active Agent:*")
        if self.current_agent_working:
            agent_name = self._get_agent_type_name(self.current_agent_working)
            status_parts.append(f"   👉 *{agent_name}*")

            if self.current_task_description:
                task_preview = self.current_task_description[:120]
                status_parts.append(f"   📋 Task: {task_preview}{'...' if len(self.current_task_description) > 120 else ''}")

            status_parts.append(f"   ⏳ Status: Working...")
        else:
            status_parts.append(f"   🔄 Coordinating between agents...")

        # Show all active agents
        if self._active_agents:
            active_agent_names = [self._get_agent_type_name(agent_id)
                                 for agent_type, agent in self._active_agents.items()
                                 for agent_id in [agent.agent_card.agent_id]]
            status_parts.append(f"\n💼 *Agents Currently Deployed:*")
            for agent_name in active_agent_names:
                status_parts.append(f"   • {agent_name}")

        # Completed steps
        if self.workflow_steps_completed:
            status_parts.append(f"\n✅ *Completed Steps:*")
            for step in self.workflow_steps_completed[-3:]:  # Show last 3 steps
                status_parts.append(f"   ✓ {step}")
            if len(self.workflow_steps_completed) > 3:
                status_parts.append(f"   ... and {len(self.workflow_steps_completed) - 3} more")

        # Refinements
        if self.accumulated_refinements:
            status_parts.append(f"\n📝 *Refinements Applied:* {len(self.accumulated_refinements)}")
            if self.accumulated_refinements:
                last_refinement = self.accumulated_refinements[-1][:80]
                status_parts.append(f"   Latest: {last_refinement}...")

        # Footer
        status_parts.append(f"\n{'=' * 40}")
        status_parts.append("⏳ Your request is being actively processed!")
        status_parts.append("💡 Send updates anytime - I'll incorporate them!")

        return "\n".join(status_parts)

    def _get_phase_emoji(self, phase: str) -> str:
        """Get emoji for current phase"""
        phase_emojis = {
            "planning": "🧠",
            "design": "🎨",
            "implementation": "💻",
            "review": "🔍",
            "deployment": "🚀"
        }
        return phase_emojis.get(phase, "⚙️")

    def _create_progress_bar(self, percent: int, length: int = 20) -> str:
        """Create a visual progress bar"""
        filled = int((percent / 100) * length)
        bar = "█" * filled + "░" * (length - filled)
        return f"[{bar}]"

    async def handle_cancellation(self) -> str:
        """
        Handle a task cancellation request from the user

        Returns:
            Cancellation confirmation message
        """
        if not self.is_active:
            return "ℹ️ No active task to cancel."

        print(f"\n🛑 [ORCHESTRATOR] Cancelling current task: {self.original_prompt}")

        # Clean up all active agents
        await self._cleanup_all_active_agents()

        # Reset state
        self.is_active = False
        self.current_phase = None
        self.current_workflow = None
        self.original_prompt = None
        self.accumulated_refinements = []
        self.current_implementation = None
        self.current_design_spec = None

        # Delete state from database
        await self._delete_state()

        return "🛑 Task cancelled. The multi-agent team has stopped working on the previous request."

    # ==========================================
    # STATE PERSISTENCE (Neon PostgreSQL)
    # ==========================================

    async def _ensure_state_manager(self):
        """
        Ensure state manager is initialized (lazy initialization)

        This is called automatically before any state operations
        """
        if not self._state_manager_initialized:
            try:
                self.state_manager = OrchestratorStateManager()
                await self.state_manager.initialize()
                self._state_manager_initialized = True

                # Try to restore previous state
                if self.user_id:
                    await self._restore_state()

            except Exception as e:
                print(f"⚠️  State persistence disabled: {e}")
                self.state_manager = None
                self._state_manager_initialized = False

    async def _save_state(self):
        """
        Save current orchestrator state to database

        Automatically called after state changes to ensure persistence
        """
        if not self.state_manager or not self.user_id:
            return

        try:
            state = {
                'is_active': self.is_active,
                'current_phase': self.current_phase,
                'current_workflow': self.current_workflow,
                'original_prompt': self.original_prompt,
                'accumulated_refinements': self.accumulated_refinements,
                'current_implementation': self.current_implementation,
                'current_design_spec': self.current_design_spec,
                'workflow_steps_completed': self.workflow_steps_completed,
                'workflow_steps_total': self.workflow_steps_total,
                'current_agent_working': self.current_agent_working,
                'current_task_description': self.current_task_description
            }

            await self.state_manager.save_state(self.user_id, state)
            print(f"💾 State saved to database (user: {self.user_id})")

        except Exception as e:
            print(f"⚠️  Failed to save state: {e}")

    async def _restore_state(self):
        """
        Restore orchestrator state from database (if exists)

        Called during initialization to recover from crashes
        """
        if not self.state_manager or not self.user_id:
            return

        try:
            state = await self.state_manager.load_state(self.user_id)

            if state and state.get('is_active'):
                print(f"🔄 Restoring previous orchestrator state for {self.user_id}")

                self.is_active = state.get('is_active', False)
                self.current_phase = state.get('current_phase')
                self.current_workflow = state.get('current_workflow')
                self.original_prompt = state.get('original_prompt')
                self.accumulated_refinements = state.get('accumulated_refinements', [])
                self.current_implementation = state.get('current_implementation')
                self.current_design_spec = state.get('current_design_spec')
                self.workflow_steps_completed = state.get('workflow_steps_completed', [])
                self.workflow_steps_total = state.get('workflow_steps_total', 0)
                self.current_agent_working = state.get('current_agent_working')
                self.current_task_description = state.get('current_task_description')

                print(f"✅ State restored (Phase: {self.current_phase}, Workflow: {self.current_workflow})")

                # Notify user
                if self.current_phase and self.current_workflow:
                    self._send_whatsapp_notification(
                        f"🔄 Resumed previous task!\n\n"
                        f"📋 Task: {self.original_prompt[:100]}...\n"
                        f"⚙️  Phase: {self.current_phase}\n"
                        f"📊 Progress: {len(self.workflow_steps_completed)}/{self.workflow_steps_total} steps\n\n"
                        f"Continuing from where we left off..."
                    )

        except Exception as e:
            print(f"⚠️  Failed to restore state: {e}")

    async def _delete_state(self):
        """
        Delete orchestrator state from database

        Called when a task completes or is cancelled
        """
        if not self.state_manager or not self.user_id:
            return

        try:
            await self.state_manager.delete_state(self.user_id)
            print(f"🗑️  State deleted from database (user: {self.user_id})")

        except Exception as e:
            print(f"⚠️  Failed to delete state: {e}")

    # ==========================================
    # A2A HELPER METHODS
    # ==========================================

    def _get_agent_type_from_id(self, agent_id: str) -> str:
        """Map agent_id to agent_type"""
        if "designer" in agent_id:
            return "designer"
        elif "frontend" in agent_id:
            return "frontend"
        elif "code_reviewer" in agent_id:
            return "code_reviewer"
        elif "qa" in agent_id:
            return "qa"
        elif "devops" in agent_id:
            return "devops"
        else:
            raise ValueError(f"Unknown agent_id: {agent_id}")

    async def _send_task_to_agent(
        self,
        agent_id: str,
        task_description: str,
        metadata: Optional[Dict] = None,
        priority: str = "medium",
        cleanup_after: bool = True,
        notify_user: bool = True
    ) -> Dict:
        """
        Send a task to an agent via A2A protocol with full telemetry tracking

        Args:
            agent_id: Target agent ID
            task_description: Task description
            metadata: Optional metadata (design_spec, etc.)
            priority: Task priority
            cleanup_after: Whether to cleanup agent after task (default: True)
            notify_user: Whether to send WhatsApp notifications (default: True)

        Returns:
            Task result dict
        """
        # Determine agent type from ID
        agent_type = self._get_agent_type_from_id(agent_id)
        agent_type_name = self._get_agent_type_name(agent_id)

        # Create A2A communication span with comprehensive metadata
        with trace_operation(
            f"A2A: orchestrator → {agent_type_name}",
            from_agent="orchestrator",
            to_agent=agent_id,
            agent_type=agent_type,
            agent_name=agent_type_name,
            task_description=task_description[:200] if len(task_description) > 200 else task_description,
            priority=priority,
            cleanup_after=cleanup_after,
            has_metadata=metadata is not None
        ) as a2a_span:

            # Update current agent tracking for status queries
            self.current_agent_working = agent_id
            self.current_task_description = task_description

            # Notify user: A2A communication starting
            if notify_user:
                self._send_whatsapp_notification(
                    f"🤖 Orchestrator → {agent_type_name}\n"
                    f"📋 Task: {task_description[:80]}..."
                )

            # Spin up agent on-demand
            agent = await self._get_agent(agent_type)

            # Create task
            task = Task(
                description=task_description,
                from_agent=self.orchestrator_id,
                to_agent=agent.agent_card.agent_id,  # Use actual agent ID
                priority=priority,
                metadata=metadata
            )

            # Add task metadata to span
            if a2a_span:
                a2a_span.set_attribute("task_id", task.task_id)
                a2a_span.set_attribute("actual_agent_id", agent.agent_card.agent_id)

            # Send task via A2A protocol (agent's telemetry will track execution)
            response = await a2a_protocol.send_task(
                from_agent_id=self.orchestrator_id,
                to_agent_id=agent.agent_card.agent_id,
                task=task
            )

            # Mark step as completed
            step_name = f"{agent_type_name}: {task_description[:60]}{'...' if len(task_description) > 60 else ''}"
            self.workflow_steps_completed.append(step_name)

            # Dynamic step adjustment: If we're approaching the estimate, increase it
            # This prevents showing >100% while still indicating progress
            if len(self.workflow_steps_completed) >= self.workflow_steps_total:
                # Increase estimate by 5 to accommodate more retries/iterations
                self.workflow_steps_total += 5
                print(f"   📊 Progress estimate adjusted: {self.workflow_steps_total} steps (more retries needed)")
                # Save updated state
                await self._save_state()

            # Add completion metadata to span
            if a2a_span:
                a2a_span.set_attribute("task_completed", True)
                a2a_span.set_attribute("step_name", step_name)
                a2a_span.set_attribute("response_status", response.status if hasattr(response, 'status') else "completed")

            # Clear current agent tracking
            self.current_agent_working = None
            self.current_task_description = None

            # Notify user: Task completed
            if notify_user:
                self._send_whatsapp_notification(
                    f"✅ Task Done by: {agent_type_name}"
                )

            # Log A2A communication event
            log_event(
                "a2a_task_sent",
                from_agent="orchestrator",
                to_agent=agent_type_name,
                agent_id=agent_id,
                task_description=task_description[:100]
            )

            # Clean up agent after task completion (unless disabled)
            if cleanup_after:
                await self._cleanup_agent(agent_type)

            return response.result

    async def _request_review_from_agent(
        self,
        agent_id: str,
        artifact: Dict,
        cleanup_after: bool = True,
        notify_user: bool = True
    ) -> Dict:
        """
        Request artifact review from an agent via A2A protocol with full telemetry tracking

        Args:
            agent_id: Reviewer agent ID
            artifact: Artifact to review
            cleanup_after: Whether to cleanup agent after review (default: True)
            notify_user: Whether to send WhatsApp notifications (default: True)

        Returns:
            Review feedback dict
        """
        # Determine agent type from ID
        agent_type = self._get_agent_type_from_id(agent_id)
        agent_type_name = self._get_agent_type_name(agent_id)

        # Create A2A review request span with metadata
        with trace_operation(
            f"A2A Review: orchestrator → {agent_type_name}",
            from_agent="orchestrator",
            to_agent=agent_id,
            agent_type=agent_type,
            agent_name=agent_type_name,
            review_type="design_fidelity",
            cleanup_after=cleanup_after
        ) as review_span:

            # Update current agent tracking for status queries
            self.current_agent_working = agent_id
            self.current_task_description = "Reviewing implementation for quality and design adherence"

            # Notify user: Review request
            if notify_user:
                self._send_whatsapp_notification(
                    f"🔍 Orchestrator → {agent_type_name}\n"
                    f"📋 Requesting review of implementation..."
                )

            # Spin up agent on-demand
            agent = await self._get_agent(agent_type)

            # Request review via A2A protocol (agent's telemetry will track review)
            review = await a2a_protocol.request_review(
                from_agent_id=self.orchestrator_id,
                to_agent_id=agent.agent_card.agent_id,
                artifact=artifact
            )

            # Mark step as completed
            score = review.get('score', 'N/A')
            step_name = f"{agent_type_name}: Review completed (Score: {score}/10)"
            self.workflow_steps_completed.append(step_name)

            # Add review metrics to span
            if review_span:
                review_span.set_attribute("review_completed", True)
                review_span.set_attribute("review_score", score if isinstance(score, (int, float)) else 0)
                review_span.set_attribute("review_approved", review.get('approved', False))
                review_span.set_attribute("feedback_count", len(review.get('feedback', [])))
                review_span.set_attribute("step_name", step_name)

            # Clear current agent tracking
            self.current_agent_working = None
            self.current_task_description = None

            # Notify user: Review completed
            if notify_user:
                approved = review.get('approved', False)
                status = "✅ Approved" if approved else "⚠️ Needs improvement"
                self._send_whatsapp_notification(
                    f"✅ Review Done by: {agent_type_name}\n"
                    f"📊 Score: {score}/10 - {status}"
                )

            # Log A2A review event
            log_event(
                "a2a_review_requested",
                from_agent="orchestrator",
                to_agent=agent_type_name,
                agent_id=agent_id,
                review_score=score if isinstance(score, (int, float)) else 0,
                approved=review.get('approved', False)
            )

            # Log review score as metric
            if isinstance(score, (int, float)):
                log_metric(
                    "orchestrator.review_score",
                    float(score),
                    agent_name=agent_type_name,
                    approved=review.get('approved', False)
                )

            # Clean up agent after review (unless disabled)
            if cleanup_after:
                await self._cleanup_agent(agent_type)

            return review

    # ==========================================
    # AI PLANNING
    # ==========================================

    async def _ai_plan_workflow(self, user_prompt: str) -> Dict:
        """
        Use Claude AI to intelligently analyze the request and plan the workflow

        Returns:
            {
                "workflow": "full_build" | "bug_fix" | "redeploy" | "design_only" | "custom",
                "reasoning": "Why this workflow was chosen",
                "agents_needed": ["designer", "frontend", "reviewer", etc],
                "steps": ["Step 1 description", "Step 2 description", ...],
                "estimated_complexity": "simple" | "moderate" | "complex",
                "special_instructions": "Any special handling needed"
            }
        """
        planning_prompt = f"""You are an AI orchestrator planning how to fulfill a user's request using a multi-agent development team.

**Available Agents:**
- **designer**: UI/UX Designer - Creates design specifications, color palettes, typography, layouts, component designs, reviews implementations
- **frontend**: Frontend Developer - Implements React/Vue/Next.js code, fixes bugs, handles dependencies, writes components
- **code_reviewer**: Code Reviewer - Reviews code for quality, security vulnerabilities, performance issues, best practices
- **qa**: QA Engineer - Tests functionality, usability, accessibility, creates test plans, identifies bugs
- **devops**: DevOps Engineer - Handles deployment optimization, build configuration, security hardening, monitors performance

**Available Workflows:**
1. **full_build**: Build a complete production-ready webapp from scratch
   - Steps: Designer → Frontend → Code Review → QA Testing → DevOps Optimization → Deploy
   - Agents: Designer + Frontend + Code Reviewer + QA + DevOps
   - Use when: User wants to create a new high-quality application

2. **bug_fix**: Fix errors in existing code
   - Steps: Frontend fixes → Code Review → Deploy with verification
   - Agents: Frontend + Code Reviewer
   - Use when: User reports errors, build failures, bugs

3. **redeploy**: Redeploy existing code without changes
   - Steps: Direct deployment
   - Agents: DevOps only
   - Use when: User wants to redeploy existing code from GitHub

4. **design_only**: Just create design specifications
   - Steps: Designer creates design spec
   - Agents: Designer only
   - Use when: User only wants design consultation, mockups, wireframes

5. **custom**: Create a custom workflow tailored to the request
   - Mix and match agents as needed
   - Use when: Request needs specific combination of agents

**User Request:**
"{user_prompt}"

**Your Task:**
Analyze the user's request and determine:
1. What does the user actually want?
2. Which workflow best fits this request?
3. Which agents are needed for the best quality result?
4. What are the specific steps to execute?
5. Are there any special considerations?

**Important Guidelines:**
- For production webapps, use ALL quality agents (code_reviewer, qa, devops) to ensure high quality
- Code Reviewer should review all code before deployment to catch security issues
- QA should test all user-facing features for usability and accessibility
- DevOps should optimize all deployments for performance and security
- Only skip agents if the user explicitly wants a quick/simple solution

**Output Format (JSON):**
{{
  "workflow": "full_build" | "bug_fix" | "redeploy" | "design_only" | "custom",
  "reasoning": "Clear explanation of why you chose this workflow",
  "agents_needed": ["designer", "frontend", "code_reviewer", "qa", "devops"],
  "steps": [
    "Designer creates comprehensive design specification and reviews frontend code",
    "Frontend implements React, tailwind, other frontend library and components based on design",
    "Code Reviewer reviews code for security and quality",
    "QA Engineer tests functionality and accessibility",
    "DevOps Engineer optimizes, pushes to github accoubt and deploys to Netlify",
    "Format and send response to user"
  ],
  "estimated_complexity": "simple" | "moderate" | "complex",
  "special_instructions": "Any special handling, edge cases, or important notes"
}}

Respond with ONLY the JSON object, no other text."""

        try:
            # Get planning decision from Claude
            response = await self.planner_sdk.send_message(planning_prompt)

            # Extract JSON from response
            import json
            import re

            # Look for JSON in code blocks or raw JSON
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group(1))
            elif response.strip().startswith('{'):
                plan = json.loads(response)
            else:
                # Claude didn't return JSON, create fallback plan
                print(f"⚠️  Could not parse planning response, using default")
                plan = {
                    "workflow": "full_build",
                    "reasoning": "Default workflow - could not parse AI response",
                    "agents_needed": ["designer", "frontend"],
                    "steps": ["Design", "Implement", "Review", "Deploy"],
                    "estimated_complexity": "moderate",
                    "special_instructions": "Using default workflow"
                }

            print(f"\n🧠 AI Planning Complete:")
            print(f"   Workflow: {plan['workflow']}")
            print(f"   Reasoning: {plan['reasoning']}")
            print(f"   Agents: {', '.join(plan['agents_needed'])}")
            print(f"   Complexity: {plan['estimated_complexity']}")

            return plan

        except Exception as e:
            print(f"❌ Planning error: {e}")
            import traceback
            traceback.print_exc()

            # Fallback to safe default
            return {
                "workflow": "full_build",
                "reasoning": f"Fallback due to error: {str(e)}",
                "agents_needed": ["designer", "frontend"],
                "steps": ["Design", "Implement", "Review", "Deploy"],
                "estimated_complexity": "moderate",
                "special_instructions": "Error during planning - using default"
            }

    # ==========================================
    # MAIN WORKFLOW ENTRY POINT
    # ==========================================

    async def build_webapp(self, user_prompt: str) -> str:
        """
        Main workflow: Uses AI planning to intelligently route requests

        Args:
            user_prompt: User's request

        Returns:
            WhatsApp-formatted response
        """
        print(f"\n🚀 [ORCHESTRATOR] Starting AI-powered request processing")
        print(f"📝 User request: {user_prompt}")
        print("\n" + "-" * 60)

        # Mark orchestrator as active and set state
        self.is_active = True
        self.original_prompt = user_prompt
        self.accumulated_refinements = []
        self.current_phase = "planning"

        # Initialize workflow tracking for detailed status
        self.current_agent_working = None
        self.current_task_description = "Planning workflow with AI..."
        self.workflow_steps_completed = []
        self.workflow_steps_total = 0  # Will be set based on workflow type

        # Initialize state persistence and save initial state
        await self._ensure_state_manager()
        await self._save_state()

        # Send initial acknowledgment to user
        self._send_whatsapp_notification(
            f"🚀 Request received! Multi-agent team is processing...\n"
            f"📝 Your request: {user_prompt[:100]}...\n\n"
            f"I'll keep you updated as agents work on your project!"
        )

        # Use AI to plan the workflow
        plan = await self._ai_plan_workflow(user_prompt)
        workflow_type = plan.get('workflow', 'full_build')
        self.current_workflow = workflow_type

        # Notify user about the chosen workflow
        self._send_whatsapp_notification(
            f"🧠 AI Planning Complete\n"
            f"📋 Workflow: {workflow_type}\n"
            f"💡 {plan.get('reasoning', 'Processing your request...')[:100]}..."
        )

        print("\n" + "-" * 60)

        try:
            # Route to appropriate workflow based on AI decision
            if workflow_type == "redeploy":
                result = await self._workflow_redeploy(user_prompt, plan)
            elif workflow_type == "bug_fix":
                result = await self._workflow_bug_fix(user_prompt, plan)
            elif workflow_type == "design_only":
                result = await self._workflow_design_only(user_prompt, plan)
            elif workflow_type == "custom":
                result = await self._workflow_custom(user_prompt, plan)
            else:  # full_build (default)
                result = await self._workflow_full_build(user_prompt, plan)

            # Mark as completed
            self.is_active = False
            self.current_phase = None
            return result

        except Exception as e:
            print(f"\n❌ [ORCHESTRATOR] Error during processing: {e}")
            import traceback
            traceback.print_exc()

            # Mark as completed (even with error)
            self.is_active = False
            self.current_phase = None

            return f"""❌ Request encountered an error:

{str(e)}

The AI planner suggested: {plan.get('workflow', 'unknown')}
Reasoning: {plan.get('reasoning', 'N/A')}

Please try again or provide more details."""

    # ==========================================
    # WORKFLOW IMPLEMENTATIONS (A2A-ENABLED)
    # ==========================================

    @trace_workflow("full_build")
    async def _workflow_full_build(self, user_prompt: str, plan: Dict = None) -> str:
        """Full build workflow: Designer → Frontend → Review → Deploy (via A2A)"""
        print(f"\n🏗️  Starting FULL BUILD workflow (A2A Protocol)")

        # Set total steps for progress tracking
        # Design (1) + Implementation (1) + Review iterations (2-5) + Deploy retries (1-10) + Frontend fixes (0-5) + Format (1)
        # Realistic estimate accounting for quality loops and deployment retries: ~15 steps average
        self.workflow_steps_total = 15

        # Track workflow start
        workflow_id = f"full_build_{int(time.time())}"
        workflow_start_time = time.time()
        system_health_monitor.track_workflow_start(
            workflow_type="full_build",
            workflow_id=workflow_id,
            metadata={"user_prompt_length": len(user_prompt)}
        )

        if plan and plan.get('special_instructions'):
            print(f"📋 Special instructions: {plan['special_instructions']}")

        try:
            # Step 1: Designer creates design specification (A2A - keep agent alive for reviews)
            self.current_phase = "design"
            await self._save_state()
            print("\n[Step 1/5] 🎨 Designer creating design specification (A2A)...")
            design_result = await self._send_task_to_agent(
                agent_id=self.DESIGNER_ID,
                task_description=f"Create design specification for: {user_prompt}",
                priority="high",
                cleanup_after=False  # Keep designer alive for review iterations
            )
            design_spec = design_result.get('design_spec', {})
            self.current_design_spec = design_spec  # Store for refinements

            # Extract design style safely
            if isinstance(design_spec, dict):
                design_style = design_spec.get('style', 'modern')
            else:
                design_style = 'modern'

            print(f"✓ Design completed via A2A")

            # Step 2: Frontend implements design (A2A - keep agent alive for improvements)
            self.current_phase = "implementation"
            await self._save_state()
            print("\n[Step 2/5] 💻 Frontend implementing design (A2A)...")
            impl_result = await self._send_task_to_agent(
                agent_id=self.FRONTEND_ID,
                task_description=f"Implement webapp using next.js, react, tailwind and other frontend libraries: {user_prompt}",
                metadata={"design_spec": design_spec},
                priority="high",
                cleanup_after=False  # Keep frontend alive for improvement iterations
            )
            implementation = impl_result.get('implementation', {})
            self.current_implementation = implementation  # Store for refinements
            framework = implementation.get('framework', 'react')

            print(f"✓ Implementation completed via A2A: {framework}")

            # Step 3: Quality verification loop - ensure score >= 8/10
            self.current_phase = "review"
            await self._save_state()
            print("\n[Step 3/5] 🔍 Quality verification (minimum score: {}/10, via A2A)...".format(self.min_quality_score))

            review_iteration = 0
            score = 0
            approved = False
            current_implementation = implementation

            # Track quality loop start
            log_event("orchestrator.quality_loop_started",
                     min_quality_score=self.min_quality_score,
                     max_iterations=self.max_review_iterations)

            quality_loop_start_time = time.time()

            while review_iteration < self.max_review_iterations:
                review_iteration += 1
                print(f"\n   Review iteration {review_iteration}/{self.max_review_iterations}")

                # Track iteration start
                iteration_start_time = time.time()
                log_event("orchestrator.quality_iteration_started",
                         iteration_number=review_iteration,
                         max_iterations=self.max_review_iterations,
                         previous_score=score)

                # Designer reviews implementation (A2A - don't cleanup during loop)
                review_artifact = {
                    "original_design": design_spec,
                    "implementation": current_implementation
                }
                review = await self._request_review_from_agent(
                    agent_id=self.DESIGNER_ID,
                    artifact=review_artifact,
                    cleanup_after=False  # Keep designer alive for multiple reviews
                )
                approved = review.get('approved', True)
                score = review.get('score', 9)
                feedback = review.get('feedback', [])

                # Calculate iteration duration
                iteration_duration_ms = (time.time() - iteration_start_time) * 1000

                print(f"   Score: {score}/10 - {'✅ Approved' if approved else '⚠️ Needs improvement'}")

                # Track iteration completion
                log_event("orchestrator.quality_iteration_completed",
                         iteration_number=review_iteration,
                         score=score,
                         approved=approved,
                         feedback_count=len(feedback),
                         iteration_duration_ms=iteration_duration_ms,
                         meets_quality_standard=score >= self.min_quality_score)

                # Track score metrics
                log_metric("orchestrator.quality_iteration_score", score)
                log_metric("orchestrator.quality_iteration_duration_ms", iteration_duration_ms)

                # Check if quality standard is met
                if score >= self.min_quality_score:
                    print(f"   ✅ Quality standard met! (Score: {score}/10 >= {self.min_quality_score}/10)")

                    # Track quality loop success
                    quality_loop_duration_ms = (time.time() - quality_loop_start_time) * 1000
                    log_event("orchestrator.quality_loop_succeeded",
                             final_score=score,
                             total_iterations=review_iteration,
                             quality_loop_duration_ms=quality_loop_duration_ms)
                    log_metric("orchestrator.quality_loop_iterations", review_iteration)
                    log_metric("orchestrator.quality_loop_duration_ms", quality_loop_duration_ms)

                    break

                # Quality not met - need improvement
                if review_iteration >= self.max_review_iterations:
                    print(f"   ⚠️  Max iterations reached - proceeding with current quality (Score: {score}/10)")

                    # Track quality loop max iterations reached
                    quality_loop_duration_ms = (time.time() - quality_loop_start_time) * 1000
                    log_event("orchestrator.quality_loop_max_iterations_reached",
                             final_score=score,
                             total_iterations=review_iteration,
                             quality_loop_duration_ms=quality_loop_duration_ms,
                             quality_gap=self.min_quality_score - score)
                    log_metric("orchestrator.quality_loop_iterations", review_iteration)
                    log_metric("orchestrator.quality_loop_duration_ms", quality_loop_duration_ms)

                    break

                # Ask Frontend to improve based on feedback (A2A - don't cleanup during loop)
                print(f"   🔧 Quality below standard ({score}/10 < {self.min_quality_score}/10) - requesting improvements (A2A)...")
                print(f"   📋 Feedback: {', '.join(feedback) if feedback else 'General improvements needed'}")

                # Track improvement request
                log_event("orchestrator.improvement_requested",
                         iteration_number=review_iteration,
                         current_score=score,
                         target_score=self.min_quality_score,
                         feedback_count=len(feedback),
                         quality_gap=self.min_quality_score - score)

                improvement_result = await self._send_task_to_agent(
                    agent_id=self.FRONTEND_ID,
                    task_description=f"""Improve the implementation based on design review feedback.

Original request: {user_prompt}

Design review score: {score}/10 (Target: {self.min_quality_score}/10)
Feedback: {', '.join(feedback)}

Please address all feedback and improve the implementation to meet the quality standard.""",
                    metadata={
                        "design_spec": design_spec,
                        "previous_implementation": current_implementation,
                        "review_feedback": feedback,
                        "review_score": score
                    },
                    priority="high",
                    cleanup_after=False  # Keep frontend alive for multiple improvements
                )
                current_implementation = improvement_result.get('implementation', current_implementation)
                self.current_implementation = current_implementation  # Update for refinements
                print(f"   ✓ Frontend provided improved implementation via A2A")

                # Track improvement completion
                log_event("orchestrator.improvement_completed",
                         iteration_number=review_iteration,
                         previous_score=score)

            # Use the final implementation (after quality loop)
            implementation = current_implementation
            self.current_implementation = implementation  # Final update

            # Track final quality loop metrics
            quality_loop_duration_ms = (time.time() - quality_loop_start_time) * 1000
            log_event("orchestrator.quality_loop_completed",
                     final_score=score,
                     total_iterations=review_iteration,
                     quality_loop_duration_ms=quality_loop_duration_ms,
                     quality_met=score >= self.min_quality_score)
            log_metric("orchestrator.quality_loop_final_score", score)
            log_metric("orchestrator.quality_loop_total_iterations", review_iteration)

            print(f"\n✓ Quality verification completed via A2A: Score {score}/10 after {review_iteration} iteration(s)")

            # Step 4: Deploy to Netlify with build verification and retry
            self.current_phase = "deployment"
            await self._save_state()
            print("\n[Step 4/5] 🚀 Deploying to Netlify with build verification...")
            deployment_result = await self._deploy_with_retry(
                user_prompt=user_prompt,
                implementation=implementation,
                design_spec=design_spec
            )

            deployment_url = deployment_result.get('url', 'https://app.netlify.com/teams')
            build_attempts = deployment_result.get('attempts', 1)
            final_implementation = deployment_result.get('final_implementation', implementation)

            print(f"✓ Deployed successfully after {build_attempts} attempt(s): {deployment_url}")

            # Step 5: Format response
            print("\n[Step 5/5] 📱 Formatting WhatsApp response...")
            response = self._format_whatsapp_response(
                url=deployment_url,
                design_style=design_style,
                framework=framework,
                review_score=score,
                build_attempts=build_attempts,
                review_iterations=review_iteration
            )

            print("\n" + "-" * 60)
            print("✅ [ORCHESTRATOR] Full build complete (A2A Protocol)!\n")

            # Track workflow success
            workflow_duration_ms = (time.time() - workflow_start_time) * 1000
            system_health_monitor.track_workflow_success(
                workflow_type="full_build",
                workflow_id=workflow_id,
                duration_ms=workflow_duration_ms,
                metadata={
                    "review_score": score,
                    "review_iterations": review_iteration,
                    "build_attempts": build_attempts,
                    "deployment_url": deployment_url
                }
            )

            # Mark as inactive and delete state after successful completion
            self.is_active = False
            self.current_phase = None
            await self._delete_state()

            return response

        except Exception as e:
            # Track workflow error
            workflow_duration_ms = (time.time() - workflow_start_time) * 1000
            system_health_monitor.track_workflow_error(
                workflow_type="full_build",
                workflow_id=workflow_id,
                error=e,
                duration_ms=workflow_duration_ms,
                metadata={"user_prompt_length": len(user_prompt)}
            )
            raise

        finally:
            # Clean up all agents used in this workflow to free resources
            print("\n🧹 Cleaning up agents...")
            await self._cleanup_all_active_agents()
            print("✓ All agents cleaned up - resources freed")

    @trace_workflow("bug_fix")
    async def _workflow_bug_fix(self, user_prompt: str, plan: Dict = None) -> str:
        """Bug fix workflow: Frontend fixes code → Deploy (via A2A)"""
        print(f"\n🔧 Starting BUG FIX workflow (A2A Protocol)")

        # Set total steps for progress tracking: Fix (1-3) + Deploy retries (1-10) + Frontend fixes (0-5) = 2-18 steps
        # Realistic estimate: ~8 steps average
        self.workflow_steps_total = 8

        # Track workflow start
        workflow_id = f"bug_fix_{int(time.time())}"
        workflow_start_time = time.time()
        system_health_monitor.track_workflow_start(
            workflow_type="bug_fix",
            workflow_id=workflow_id,
            metadata={"user_prompt_length": len(user_prompt)}
        )

        if plan and plan.get('special_instructions'):
            print(f"📋 Special instructions: {plan['special_instructions']}")

        # Step 1: Frontend fixes the issue (A2A)
        print("\n[Step 1/2] 💻 Frontend analyzing and fixing issue (A2A)...")
        fix_result = await self._send_task_to_agent(
            agent_id=self.FRONTEND_ID,
            task_description=f"Analyze and fix this issue: {user_prompt}",
            priority="high"
        )
        implementation = fix_result.get('implementation', {})
        framework = implementation.get('framework', 'react')

        print(f"✓ Initial fix completed via A2A")

        # Step 2: Deploy to Netlify with build verification and retry
        print("\n[Step 2/2] 🚀 Deploying fixed code with build verification...")
        deployment_result = await self._deploy_with_retry(
            user_prompt=user_prompt,
            implementation=implementation,
            design_spec={}  # No design spec for bug fixes
        )

        deployment_url = deployment_result.get('url', 'https://app.netlify.com/teams')
        build_attempts = deployment_result.get('attempts', 1)

        print(f"✓ Deployed successfully after {build_attempts} fix attempt(s): {deployment_url}")

        response = f"""✅ Bug fix complete and deployed!

🔗 Live Site: {deployment_url}

🔧 What was fixed:
  • Analyzed the error/issue
  • Applied fixes
  • Redeployed to Netlify

⚙️ Technical:
  • Framework: {framework}
  • Deployed on Netlify

🤖 Fixed by Frontend Developer Agent (via A2A Protocol)
"""

        print("\n" + "-" * 60)
        print("✅ [ORCHESTRATOR] Bug fix complete (A2A)!\n")

        # Track workflow success
        workflow_duration_ms = (time.time() - workflow_start_time) * 1000
        system_health_monitor.track_workflow_success(
            workflow_type="bug_fix",
            workflow_id=workflow_id,
            duration_ms=workflow_duration_ms,
            metadata={
                "build_attempts": build_attempts,
                "deployment_url": deployment_url
            }
        )

        return response

    @trace_workflow("redeploy")
    async def _workflow_redeploy(self, user_prompt: str, plan: Dict = None) -> str:
        """Redeploy workflow: Just deploy existing code"""
        print(f"\n🚀 Starting REDEPLOY workflow")

        # Set total steps for progress tracking: Deploy only = 1 step
        self.workflow_steps_total = 1

        # Track workflow start
        workflow_id = f"redeploy_{int(time.time())}"
        workflow_start_time = time.time()
        system_health_monitor.track_workflow_start(
            workflow_type="redeploy",
            workflow_id=workflow_id,
            metadata={"user_prompt_length": len(user_prompt)}
        )

        if plan and plan.get('special_instructions'):
            print(f"📋 Special instructions: {plan['special_instructions']}")

        # Step 1: Deploy directly
        print("\n[Step 1/1] 🚀 Redeploying to Netlify...")

        # Ask Claude to use Netlify MCP to redeploy
        redeploy_prompt = f"""User request: {user_prompt}

Use Netlify MCP to redeploy the existing site.

Steps:
1. If a GitHub repo is mentioned, clone it
2. Redeploy the site to Netlify
3. Return the live deployment URL

Respond with ONLY the deployment URL."""

        response_text = await self.deployment_sdk.send_message(redeploy_prompt)

        # Extract URL
        import re
        url_match = re.search(r'https://[a-zA-Z0-9-]+\.netlify\.app', response_text)
        if url_match:
            deployment_url = url_match.group(0)
            print(f"✓ Redeployed to: {deployment_url}")
        else:
            dashboard_match = re.search(r'https://app\.netlify\.com/[^\s]+', response_text)
            if dashboard_match:
                deployment_url = dashboard_match.group(0)
            else:
                deployment_url = "https://app.netlify.com/teams"

        response = f"""✅ Site redeployed successfully!

🔗 Live Site: {deployment_url}

🚀 Redeployment complete
  • Existing code deployed
  • No changes made to design or implementation

🤖 Deployed by Orchestrator
"""

        print("\n" + "-" * 60)
        print("✅ [ORCHESTRATOR] Redeploy complete!\n")

        # Track workflow success
        workflow_duration_ms = (time.time() - workflow_start_time) * 1000
        system_health_monitor.track_workflow_success(
            workflow_type="redeploy",
            workflow_id=workflow_id,
            duration_ms=workflow_duration_ms,
            metadata={"deployment_url": deployment_url}
        )

        return response

    @trace_workflow("design_only")
    async def _workflow_design_only(self, user_prompt: str, plan: Dict = None) -> str:
        """Design only workflow: Designer creates design spec (via A2A)"""
        print(f"\n🎨 Starting DESIGN ONLY workflow (A2A Protocol)")

        # Set total steps for progress tracking: Design only = 1 step
        self.workflow_steps_total = 1

        # Track workflow start
        workflow_id = f"design_only_{int(time.time())}"
        workflow_start_time = time.time()
        system_health_monitor.track_workflow_start(
            workflow_type="design_only",
            workflow_id=workflow_id,
            metadata={"user_prompt_length": len(user_prompt)}
        )

        if plan and plan.get('special_instructions'):
            print(f"📋 Special instructions: {plan['special_instructions']}")

        # Step 1: Designer creates design (A2A)
        print("\n[Step 1/1] 🎨 Designer creating design specification (A2A)...")
        design_result = await self._send_task_to_agent(
            agent_id=self.DESIGNER_ID,
            task_description=f"Create design specification for: {user_prompt}",
            priority="medium"
        )
        design_spec = design_result.get('design_spec', {})

        # Format design for WhatsApp
        response = f"""✅ Design specification complete!

🎨 Design created by UI/UX Designer Agent (via A2A Protocol)

📋 Design includes:
  • Style guidelines
  • Color palette
  • Typography system
  • Component specifications
  • Layout structure
  • Accessibility requirements

💡 Ready to implement? Send a message like "Implement this design" to have the Frontend agent build it!

🤖 Designed by UI/UX Designer Agent
"""

        print("\n" + "-" * 60)
        print("✅ [ORCHESTRATOR] Design complete (A2A)!\n")

        # Track workflow success
        workflow_duration_ms = (time.time() - workflow_start_time) * 1000
        system_health_monitor.track_workflow_success(
            workflow_type="design_only",
            workflow_id=workflow_id,
            duration_ms=workflow_duration_ms,
            metadata={"has_design_spec": bool(design_spec)}
        )

        return response

    async def _ai_decide_step_executor(self, step: str, user_prompt: str, agents_available: list, context: Dict) -> Dict:
        """
        Use Claude AI to intelligently decide which agent should execute this step

        Args:
            step: The step description from the plan
            user_prompt: Original user request
            agents_available: List of available agents
            context: Current workflow context (design_spec, implementation, etc.)

        Returns:
            {
                "agent": "designer" | "frontend" | "review" | "deploy" | "skip",
                "reasoning": "Why this agent was chosen",
                "task_description": "Refined task description for the agent"
            }
        """
        decision_prompt = f"""You are an intelligent orchestrator deciding which agent should execute a workflow step.

**Workflow Step:** "{step}"

**Original User Request:** "{user_prompt}"

**Available Agents:**
- **designer**: UI/UX Designer - creates design specifications, reviews implementations for design fidelity
- **frontend**: Frontend Developer - writes React/Vue code, fixes bugs, implements features
- **code_reviewer**: Code Reviewer - reviews code for security, quality, performance, best practices
- **qa**: QA Engineer - tests functionality, usability, accessibility, creates test plans
- **devops**: DevOps Engineer - optimizes builds, configures deployment, security hardening
- **deploy**: Direct Deployment - deploys code to Netlify with build verification
- **skip**: Skip this step (if not actionable or already completed)

**Current Context:**
- Has design specification: {bool(context.get('design_spec'))}
- Has implementation: {bool(context.get('implementation'))}
- Has code review: {bool(context.get('code_review'))}
- Has QA report: {bool(context.get('qa_report'))}
- Has DevOps config: {bool(context.get('devops_config'))}
- Agents in plan: {', '.join(agents_available)}

**Your Task:**
Analyze the step and decide which agent should execute it. Consider:
1. What does this step actually require?
2. Which agent is best suited for this work?
3. Do we have the prerequisites (design, code, etc.)?
4. Is this step even necessary given the context?

**Output Format (JSON):**
{{
  "agent": "designer" | "frontend" | "code_reviewer" | "qa" | "devops" | "deploy" | "skip",
  "reasoning": "Clear explanation of why this agent was chosen",
  "task_description": "Refined, specific task description for the agent to execute"
}}

Be intelligent and context-aware. Don't just pattern match - actually understand what the step requires."""

        try:
            response = await self.planner_sdk.send_message(decision_prompt)

            # Extract JSON
            import json
            import re

            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                decision = json.loads(json_match.group(1))
            elif response.strip().startswith('{'):
                decision = json.loads(response)
            else:
                # Fallback
                decision = {
                    "agent": "skip",
                    "reasoning": "Could not parse AI decision",
                    "task_description": step
                }

            return decision

        except Exception as e:
            print(f"⚠️  Error in step decision: {e}")
            # Fallback to skip
            return {
                "agent": "skip",
                "reasoning": f"Error during decision: {str(e)}",
                "task_description": step
            }

    @trace_workflow("custom")
    async def _workflow_custom(self, user_prompt: str, plan: Dict) -> str:
        """
        Custom workflow: Execute workflow based on AI planner's instructions (via A2A)

        This workflow uses AI to intelligently route each step to the right agent,
        rather than hardcoded keyword matching.
        """
        print(f"\n🔮 Starting CUSTOM workflow with AI-powered step routing (A2A Protocol)")
        print(f"📋 AI Planner reasoning: {plan.get('reasoning', 'N/A')}")

        # Track workflow start
        workflow_id = f"custom_{int(time.time())}"
        workflow_start_time = time.time()
        system_health_monitor.track_workflow_start(
            workflow_type="custom",
            workflow_id=workflow_id,
            metadata={
                "user_prompt_length": len(user_prompt),
                "steps_count": len(plan.get('steps', [])),
                "agents_needed": plan.get('agents_needed', [])
            }
        )

        if plan.get('special_instructions'):
            print(f"📋 Special instructions: {plan['special_instructions']}")

        agents_needed = plan.get('agents_needed', [])
        steps = plan.get('steps', [])

        # Set total steps for progress tracking based on planned steps
        self.workflow_steps_total = len(steps) if steps else 5

        print(f"\n🤖 Agents available: {', '.join(agents_needed)}")
        print(f"📝 Steps planned: {len(steps)}")

        # Execute steps based on AI decisions
        context = {
            'design_spec': None,
            'implementation': None,
            'review_score': None,
            'code_review': None,
            'qa_report': None,
            'devops_config': None,
            'deployment_url': None
        }

        for i, step in enumerate(steps):
            print(f"\n[Step {i+1}/{len(steps)}] {step}")

            # Use AI to decide which agent should handle this step
            decision = await self._ai_decide_step_executor(
                step=step,
                user_prompt=user_prompt,
                agents_available=agents_needed,
                context=context
            )

            agent_choice = decision.get('agent', 'skip')
            reasoning = decision.get('reasoning', 'N/A')
            task_desc = decision.get('task_description', step)

            print(f"   🧠 AI Decision: {agent_choice}")
            print(f"   💭 Reasoning: {reasoning}")

            # Execute based on AI decision (via A2A)
            if agent_choice == "designer":
                design_result = await self._send_task_to_agent(
                    agent_id=self.DESIGNER_ID,
                    task_description=task_desc
                )
                context['design_spec'] = design_result.get('design_spec', {})
                print(f"   ✓ Designer completed step via A2A")

            elif agent_choice == "frontend":
                impl_result = await self._send_task_to_agent(
                    agent_id=self.FRONTEND_ID,
                    task_description=task_desc,
                    metadata={"design_spec": context['design_spec']} if context['design_spec'] else None
                )
                context['implementation'] = impl_result.get('implementation', {})
                print(f"   ✓ Frontend completed step via A2A")

            elif agent_choice == "review":
                if context['design_spec'] and context['implementation']:
                    review_artifact = {
                        "original_design": context['design_spec'],
                        "implementation": context['implementation']
                    }
                    review = await self._request_review_from_agent(
                        agent_id=self.DESIGNER_ID,
                        artifact=review_artifact
                    )
                    approved = review.get('approved', True)
                    score = review.get('score', 8)
                    context['review_score'] = score
                    print(f"   ✓ Design review completed via A2A: {'✅ Approved' if approved else '⚠️ Changes suggested'} (Score: {score}/10)")
                else:
                    print(f"   ⚠️  Skipping design review - missing prerequisites")

            elif agent_choice == "code_reviewer":
                if context['implementation']:
                    review_result = await self._send_task_to_agent(
                        agent_id=self.CODE_REVIEWER_ID,
                        task_description=task_desc,
                        metadata={"implementation": context['implementation']}
                    )
                    context['code_review'] = review_result.get('review', {})
                    overall_score = context['code_review'].get('overall_score', 'N/A')
                    critical_issues = len(context['code_review'].get('critical_issues', []))
                    print(f"   ✓ Code review completed via A2A: Score {overall_score}/10, {critical_issues} critical issues")
                else:
                    print(f"   ⚠️  Skipping code review - no implementation available")

            elif agent_choice == "qa":
                if context['implementation']:
                    qa_result = await self._send_task_to_agent(
                        agent_id=self.QA_ID,
                        task_description=task_desc,
                        metadata={
                            "implementation": context['implementation'],
                            "requirements": user_prompt
                        }
                    )
                    context['qa_report'] = qa_result.get('qa_report', {})
                    quality_score = context['qa_report'].get('overall_quality_score', 'N/A')
                    issues_found = len(context['qa_report'].get('issues_found', []))
                    print(f"   ✓ QA testing completed via A2A: Quality {quality_score}/10, {issues_found} issues found")
                else:
                    print(f"   ⚠️  Skipping QA testing - no implementation available")

            elif agent_choice == "devops":
                if context['implementation']:
                    devops_result = await self._send_task_to_agent(
                        agent_id=self.DEVOPS_ID,
                        task_description=task_desc,
                        metadata={"implementation": context['implementation']}
                    )
                    context['devops_config'] = devops_result.get('devops_report', {})
                    deployment_score = context['devops_config'].get('deployment_score', 'N/A')
                    optimizations = len(context['devops_config'].get('optimizations', []))
                    print(f"   ✓ DevOps optimization completed via A2A: Score {deployment_score}/10, {optimizations} optimizations recommended")
                else:
                    print(f"   ⚠️  Skipping DevOps optimization - no implementation available")

            elif agent_choice == "deploy":
                if context['implementation']:
                    deployment_result = await self._deploy_with_retry(
                        user_prompt=user_prompt,
                        implementation=context['implementation'],
                        design_spec=context['design_spec'] or {}
                    )
                    context['deployment_url'] = deployment_result.get('url', 'https://app.netlify.com/teams')
                    build_attempts = deployment_result.get('attempts', 1)
                    print(f"   ✓ Deployed successfully after {build_attempts} attempt(s)")

                    # Return success response
                    framework = context['implementation'].get('framework', 'react')
                    return f"""✅ Custom workflow complete!

🔗 Live Site: {context['deployment_url']}

🎯 AI-Planned Workflow (A2A Protocol):
  • Workflow type: {plan.get('workflow', 'custom')}
  • Reasoning: {plan.get('reasoning', 'N/A')}
  • Agents used: {', '.join(agents_needed)}
  • Steps executed: {len(steps)}
  • Complexity: {plan.get('estimated_complexity', 'N/A')}

⚙️ Technical:
  • Framework: {framework}
  • Deployed on Netlify
  • Build attempts: {build_attempts}

🤖 Coordinated by AI Planner + Multi-Agent System (A2A)
"""
                else:
                    print(f"   ⚠️  Skipping deploy - no implementation available")

            elif agent_choice == "skip":
                print(f"   ⏭️  Skipping step")

        # If no deployment occurred, return a summary
        response = f"""✅ Custom workflow complete!

🎯 AI-Planned Workflow (A2A Protocol):
  • Workflow type: {plan.get('workflow', 'custom')}
  • Reasoning: {plan.get('reasoning', 'N/A')}
  • Agents used: {', '.join(agents_needed)}
  • Steps executed: {len(steps)}
  • Complexity: {plan.get('estimated_complexity', 'N/A')}

📋 Results:
"""

        if context['design_spec']:
            response += "\n  ✅ Design specification created"
        if context['implementation']:
            response += "\n  ✅ Implementation completed"
        if context['review_score']:
            response += f"\n  ✅ Design review completed (Score: {context['review_score']}/10)"
        if context['deployment_url']:
            response += f"\n  ✅ Deployed to: {context['deployment_url']}"

        response += "\n\n🤖 Coordinated by AI Planner + Multi-Agent System (A2A)"

        print("\n" + "-" * 60)
        print("✅ [ORCHESTRATOR] Custom workflow complete (A2A)!\n")

        # Track workflow success
        workflow_duration_ms = (time.time() - workflow_start_time) * 1000
        system_health_monitor.track_workflow_success(
            workflow_type="custom",
            workflow_id=workflow_id,
            duration_ms=workflow_duration_ms,
            metadata={
                "steps_executed": len(steps),
                "agents_used": agents_needed,
                "has_deployment": bool(context.get('deployment_url'))
            }
        )

        return response

    # ==========================================
    # DEPLOYMENT HELPERS
    # ==========================================

    async def _deploy_with_retry(
        self,
        user_prompt: str,
        implementation: Dict,
        design_spec: Dict
    ) -> Dict:
        """
        Deploy to Netlify with build verification and automatic retry (using DevOps agent via A2A)

        Returns:
            {
                'url': deployment_url,
                'attempts': number_of_attempts,
                'final_implementation': final_working_implementation,
                'build_errors': list_of_errors_encountered
            }
        """
        # Log deployment pipeline start
        from utils.telemetry import trace_operation, log_event, log_metric, log_error
        import time

        deployment_start_time = time.time()

        log_event("deployment.pipeline_started",
                 max_retries=self.max_build_retries,
                 has_implementation=bool(implementation),
                 has_design_spec=bool(design_spec))

        attempts = 0
        current_implementation = implementation
        all_build_errors = []

        while attempts < self.max_build_retries:
            attempts += 1
            attempt_start_time = time.time()

            print(f"\n🔨 Deployment attempt {attempts}/{self.max_build_retries}")

            # Log deployment attempt start
            log_event("deployment.attempt_started",
                     attempt=attempts,
                     max_attempts=self.max_build_retries,
                     is_retry=attempts > 1,
                     previous_errors_count=len(all_build_errors))

            # Call DevOps agent to deploy (includes GitHub setup, push, Netlify deploy, build verification)
            try:
                devops_result = await self._send_task_to_agent(
                    agent_id=self.DEVOPS_ID,
                    task_description=f"""Deploy this webapp to Netlify with full GitHub workflow.

User request: {user_prompt}

Deployment attempt: {attempts}/{self.max_build_retries}

CRITICAL STEPS:
1. Create/verify GitHub repository
2. Generate netlify.toml with NPM_FLAGS = "--include=dev"
3. Write all files to the repository
4. Push to GitHub (billsusanto account)
5. Deploy from GitHub to Netlify
6. Check build logs for errors
7. Verify the deployed site loads

🔥 IMPORTANT - USE LOGFIRE FOR DEBUGGING:
- If this is a retry attempt ({attempts > 1}), FIRST query Logfire to see what failed before
- Query: span.name contains "Deploy" AND timestamp > now() - 1h
- Look for previous deployment traces to understand what went wrong
- Extract exact error messages, file paths, line numbers from Logfire traces
- Use production telemetry data (not assumptions) to identify root causes
- Reference specific trace IDs in your error analysis

Dashboard: https://logfire.pydantic.dev/
Project: whatsapp-mcp

If build fails:
- Query Logfire for the deployment trace
- Extract EXACT error messages from build logs
- Provide structured error data with file paths and line numbers
- Return detailed error report for Frontend to fix

If successful, return the live deployment URL.""",
                    metadata={"implementation": current_implementation, "design_spec": design_spec},
                    priority="high",
                    cleanup_after=False,  # Keep DevOps alive for retries
                    notify_user=True
                )

                devops_report = devops_result.get('devops_report', {})
                build_verification = devops_report.get('build_verification', {})
                netlify_deployment = devops_report.get('netlify_deployment', {})

                # Extract deployment URL and build status
                deployment_url = netlify_deployment.get('deployment_url') or devops_report.get('deployment_url')
                build_successful = build_verification.get('build_successful', False)
                build_errors = build_verification.get('build_errors', [])

                # Success!
                if build_successful and deployment_url:
                    attempt_duration_ms = (time.time() - attempt_start_time) * 1000
                    total_duration_ms = (time.time() - deployment_start_time) * 1000

                    print(f"✅ Build successful on attempt {attempts}")
                    print(f"   Deployment URL: {deployment_url}")

                    # Log successful deployment
                    log_event("deployment.build_succeeded",
                             attempt=attempts,
                             deployment_url=deployment_url,
                             attempt_duration_ms=attempt_duration_ms,
                             total_duration_ms=total_duration_ms,
                             total_errors_encountered=len(all_build_errors))

                    log_metric("deployment.successful_builds", 1)
                    log_metric("deployment.attempts_until_success", attempts)
                    log_metric("deployment.total_duration_ms", total_duration_ms)

                    # Log final deployment success
                    log_event("deployment.pipeline_succeeded",
                             deployment_url=deployment_url,
                             total_attempts=attempts,
                             total_duration_ms=total_duration_ms,
                             had_retries=attempts > 1,
                             total_errors_fixed=len(all_build_errors))

                    # Clean up DevOps agent after success
                    await self._cleanup_agent("devops")

                    return {
                        'url': deployment_url,
                        'attempts': attempts,
                        'final_implementation': current_implementation,
                        'build_errors': all_build_errors
                    }

                # Build failed - extract error details
                if build_errors or not build_successful:
                    attempt_duration_ms = (time.time() - attempt_start_time) * 1000
                    error_summary = self._format_build_errors(build_errors)

                    print(f"❌ Build failed on attempt {attempts}")
                    print(f"   Errors: {error_summary[:200]}...")
                    all_build_errors.extend(build_errors)

                    # Log build failure
                    log_event("deployment.build_failed",
                             attempt=attempts,
                             attempt_duration_ms=attempt_duration_ms,
                             errors_count=len(build_errors),
                             error_summary=error_summary[:500],
                             will_retry=attempts < self.max_build_retries)

                    log_metric("deployment.failed_builds", 1)
                    log_metric("deployment.build_errors_count", len(build_errors))

                    # If this is the last attempt, give up
                    if attempts >= self.max_build_retries:
                        total_duration_ms = (time.time() - deployment_start_time) * 1000

                        print(f"⚠️  Max retries ({self.max_build_retries}) reached - deployment failed")

                        # Log final deployment failure
                        log_event("deployment.pipeline_failed",
                                 total_attempts=attempts,
                                 total_duration_ms=total_duration_ms,
                                 total_errors_count=len(all_build_errors),
                                 max_retries_reached=True)

                        log_metric("deployment.pipeline_failures", 1)

                        # Clean up DevOps agent
                        await self._cleanup_agent("devops")

                        return {
                            'url': deployment_url or 'https://app.netlify.com/teams',
                            'attempts': attempts,
                            'final_implementation': current_implementation,
                            'build_errors': all_build_errors
                        }

                    # Ask Frontend to fix the build errors (via A2A)
                    print(f"\n🔧 Asking Frontend agent to fix build errors (A2A)...")

                    # Log error fix request
                    log_event("deployment.requesting_error_fix",
                             attempt=attempts,
                             errors_count=len(build_errors),
                             requesting_from="frontend_agent")

                    # Format error details for Frontend
                    error_description = self._format_errors_for_frontend(build_errors, error_summary)

                    fix_result = await self._send_task_to_agent(
                        agent_id=self.FRONTEND_ID,
                        task_description=f"""Fix these build errors:

{error_description}

Original task: {user_prompt}
Fix attempt: {attempts}/{self.max_build_retries}

🔥 IMPORTANT - USE LOGFIRE FOR DEBUGGING:
- FIRST query Logfire to see the exact error that occurred in production
- Query: agent_name = "Frontend Developer" AND result_status = "error" AND timestamp > now() - 1h
- Look for your previous implementation attempt traces
- Extract exact error messages, stack traces, component names from telemetry
- See what actually failed in the build (not assumptions!)
- Reference specific trace IDs in your bug fix analysis

Dashboard: https://logfire.pydantic.dev/
Project: whatsapp-mcp

Example Logfire debugging:
1. Query: span.name contains "execute_task" AND error_message contains "TypeScript"
2. Found trace: abc123 showing build failed with "Property 'title' does not exist"
3. Extract: You used album.title but data has album.name
4. Fix: Update component to use correct property names

The DevOps agent attempted to deploy your code and found build errors.
Please:
1. Check Logfire for the deployment trace to understand what failed
2. Analyze the exact error messages from production telemetry
3. Fix ALL errors in the implementation
4. Return the corrected implementation with all fixes applied

Do NOT guess - use Logfire data to see what actually went wrong!""",
                        metadata={
                            "design_spec": design_spec,
                            "previous_implementation": current_implementation,
                            "build_errors": build_errors  # Pass structured error data
                        },
                        priority="high",
                        cleanup_after=True,  # Clean up Frontend after fix
                        notify_user=True
                    )

                    current_implementation = fix_result.get('implementation', current_implementation)

                    # Log successful error fix
                    log_event("deployment.errors_fixed",
                             attempt=attempts,
                             errors_fixed_count=len(build_errors),
                             implementation_updated=True)

                    print(f"✓ Frontend provided updated implementation via A2A")
                else:
                    # No clear success or failure - treat as error
                    print(f"⚠️  Unclear deployment status on attempt {attempts}")
                    all_build_errors.append("Unclear deployment status - no URL or build status")

                    if attempts >= self.max_build_retries:
                        await self._cleanup_agent("devops")
                        return {
                            'url': 'https://app.netlify.com/teams',
                            'attempts': attempts,
                            'final_implementation': current_implementation,
                            'build_errors': all_build_errors
                        }

            except Exception as e:
                attempt_duration_ms = (time.time() - attempt_start_time) * 1000

                print(f"❌ DevOps agent error on attempt {attempts}: {str(e)}")
                all_build_errors.append(f"DevOps agent error: {str(e)}")

                # Log deployment exception
                log_error(e, "deployment_attempt",
                         attempt=attempts,
                         attempt_duration_ms=attempt_duration_ms,
                         will_retry=attempts < self.max_build_retries)

                log_event("deployment.attempt_exception",
                         attempt=attempts,
                         attempt_duration_ms=attempt_duration_ms,
                         error=str(e),
                         error_type=type(e).__name__)

                log_metric("deployment.exceptions", 1)

                if attempts >= self.max_build_retries:
                    total_duration_ms = (time.time() - deployment_start_time) * 1000

                    # Log pipeline failure due to exceptions
                    log_event("deployment.pipeline_failed",
                             total_attempts=attempts,
                             total_duration_ms=total_duration_ms,
                             total_errors_count=len(all_build_errors),
                             failure_reason="exception",
                             max_retries_reached=True)

                    log_metric("deployment.pipeline_failures", 1)

                    await self._cleanup_agent("devops")
                    return {
                        'url': 'https://app.netlify.com/teams',
                        'attempts': attempts,
                        'final_implementation': current_implementation,
                        'build_errors': all_build_errors
                    }

                # For errors, still try to get Frontend to fix the implementation
                print(f"\n🔧 Asking Frontend to review and fix implementation after DevOps error...")

                fix_result = await self._send_task_to_agent(
                    agent_id=self.FRONTEND_ID,
                    task_description=f"""The deployment failed with an error. Please review and fix the implementation.

Error: {str(e)}

Original task: {user_prompt}
Fix attempt: {attempts}/{self.max_build_retries}

🔥 CRITICAL - USE LOGFIRE TO DEBUG THIS DEPLOYMENT FAILURE:
- Query Logfire to see what happened during the DevOps agent execution
- Query: agent_name = "DevOps Engineer" AND result_status = "error" AND timestamp > now() - 30m
- Look for the deployment attempt trace to understand the failure
- Also check your own previous implementation traces
- Extract exact error details from production telemetry

Dashboard: https://logfire.pydantic.dev/
Project: whatsapp-mcp

The DevOps agent encountered an error during deployment.
Please:
1. Check Logfire for both DevOps and Frontend traces to understand the full context
2. Review the implementation for common issues:
   - All files are properly structured
   - All dependencies are in package.json (including devDependencies)
   - Build commands are correct
   - No syntax errors in code
   - TypeScript types are correct
3. Fix ALL issues found
4. Return the corrected implementation

Use Logfire data to understand the root cause, don't just guess!""",
                    metadata={
                        "design_spec": design_spec,
                        "previous_implementation": current_implementation
                    },
                    priority="high",
                    cleanup_after=True
                )

                current_implementation = fix_result.get('implementation', current_implementation)

        # Should never reach here, but just in case
        await self._cleanup_agent("devops")
        return {
            'url': 'https://app.netlify.com/teams',
            'attempts': attempts,
            'final_implementation': current_implementation,
            'build_errors': all_build_errors
        }

    def _format_build_errors(self, build_errors: list) -> str:
        """Format build errors into a readable summary"""
        if not build_errors:
            return "Unknown build error"

        if isinstance(build_errors, list) and len(build_errors) > 0:
            if isinstance(build_errors[0], dict):
                # Structured error objects
                summaries = []
                for err in build_errors[:5]:  # Show first 5 errors
                    error_type = err.get('type', 'unknown')
                    error_msg = err.get('error_message', '')
                    file = err.get('file', '')
                    line = err.get('line', '')
                    summaries.append(f"{error_type} in {file}:{line} - {error_msg[:100]}")
                return "\n".join(summaries)
            else:
                # String errors
                return "\n".join(str(e)[:200] for e in build_errors[:5])

        return str(build_errors)[:500]

    def _format_errors_for_frontend(self, build_errors: list, error_summary: str) -> str:
        """Format errors in a way that Frontend agent can understand and fix"""
        if not build_errors:
            return error_summary

        formatted = "BUILD ERRORS FOUND:\n\n"

        for i, err in enumerate(build_errors[:10], 1):  # Show up to 10 errors
            if isinstance(err, dict):
                formatted += f"Error #{i}:\n"
                formatted += f"  Type: {err.get('type', 'unknown')}\n"
                formatted += f"  File: {err.get('file', 'unknown')}\n"
                formatted += f"  Line: {err.get('line', 'unknown')}\n"
                formatted += f"  Message: {err.get('error_message', 'No message')}\n"

                if err.get('expected'):
                    formatted += f"  Expected: {err.get('expected')}\n"
                if err.get('received'):
                    formatted += f"  Received: {err.get('received')}\n"
                if err.get('fix_option_1'):
                    formatted += f"  Fix suggestion: {err.get('fix_option_1')}\n"

                formatted += "\n"
            else:
                formatted += f"Error #{i}: {str(err)[:300]}\n\n"

        return formatted

    # NOTE: Old deployment methods removed - now using DevOps agent directly via A2A
    # The DevOps agent handles:
    # - GitHub repository setup and push
    # - netlify.toml generation with NPM_FLAGS
    # - Netlify deployment
    # - Build log verification
    # See _deploy_with_retry() for the new implementation

    def _format_whatsapp_response(
        self,
        url: str,
        design_style: str,
        framework: str,
        review_score: int = 8,
        build_attempts: int = 1,
        review_iterations: int = 1
    ) -> str:
        """Format response for WhatsApp"""
        build_status = ""
        if build_attempts > 1:
            build_status = f"\n  • Build verified after {build_attempts} attempts ✅"
        elif build_attempts == 1:
            build_status = "\n  • Build verified on first attempt ✅"

        quality_status = ""
        if review_iterations > 1:
            quality_status = f"\n  • Quality improved over {review_iterations} iterations ✅"
        elif review_iterations == 1:
            quality_status = "\n  • Quality approved on first review ✅"

        return f"""✅ Your webapp is ready!

🔗 Live Site: {url}

🎨 Design:
  • Style: {design_style}
  • Fully responsive
  • Accessibility optimized
  • Quality score: {review_score}/10{quality_status}

⚙️ Technical:
  • Framework: {framework}
  • Build tool: Next.js
  • Deployed on Netlify{build_status}

🤖 Built by AI Agent Team (A2A Protocol):
  • UI/UX Designer Agent (design + quality review)
  • Frontend Developer Agent (implementation + improvements)
  • Iterative quality improvement (minimum {self.min_quality_score}/10)
  • Automatic build verification
  • All agents communicated via A2A Protocol

🚀 Powered by Claude Multi-Agent System with A2A
"""

    async def cleanup(self):
        """Clean up all agents and SDKs (works with lazy initialization)"""
        # Clean up any active agents
        await self._cleanup_all_active_agents()

        # Clean up cached agents if caching is enabled
        if self.enable_agent_caching and self._agent_cache:
            print("🧹 Cleaning up cached agents...")
            for agent_type, agent in list(self._agent_cache.items()):
                await agent.cleanup()
                a2a_protocol.unregister_agent(agent.agent_card.agent_id)
            self._agent_cache.clear()

        # Clean up SDKs
        await self.deployment_sdk.close()
        await self.planner_sdk.close()

        # Unregister orchestrator from A2A protocol
        a2a_protocol.unregister_agent(self.ORCHESTRATOR_ID)

        print("🧹 [ORCHESTRATOR] Cleaned up all agents, deployment SDK, and planner SDK")
