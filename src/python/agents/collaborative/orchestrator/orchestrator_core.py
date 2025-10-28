"""
Collaborative Orchestrator - Core Module
Coordinates multi-agent team: Designer, Frontend, Code Reviewer, QA, DevOps

NOW USING A2A PROTOCOL for all agent communication
"""

from typing import Dict, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sdk.claude_sdk import ClaudeSDK
from agents.collaborative.models import AgentCard, AgentRole
from agents.collaborative.a2a_protocol import a2a_protocol

# Import project database manager for full-stack apps
try:
    from database.project_manager import project_manager
    PROJECT_MANAGER_AVAILABLE = True
except ImportError:
    PROJECT_MANAGER_AVAILABLE = False
    project_manager = None
    print("⚠️  Project manager not available - backend features disabled")

# Import telemetry
from utils.telemetry import (
    trace_workflow,
    trace_operation,
    trace_user_request,
    trace_phase_transition,
    log_event,
    log_metric,
    measure_performance
)

# Import system health monitor
from utils.health_monitor import system_health_monitor

# Import mixins
from .orchestrator_state import OrchestratorStateMixin
from .orchestrator_agents import OrchestratorAgentsMixin
from .orchestrator_workflows import OrchestratorWorkflowsMixin


class CollaborativeOrchestrator(OrchestratorStateMixin, OrchestratorAgentsMixin, OrchestratorWorkflowsMixin):
    """
    Orchestrates collaboration between multi-agent development team using A2A Protocol

    Agent Team:
    - UI/UX Designer: Creates design specifications and reviews implementations
    - Backend Developer: Creates database schemas, APIs, and server-side logic (NEW!)
    - Frontend Developer: Implements React/Vue code
    - Code Reviewer: Reviews code for quality, security, and best practices
    - QA Engineer: Tests functionality, usability, and accessibility
    - DevOps Engineer: Handles deployment, optimization, and infrastructure

    Communication:
    - ALL agent interactions use A2A (Agent-to-Agent) protocol
    - Standardized messaging with Task and TaskResponse models
    - Full traceability and logging of all communications

    Workflow (Full-Stack):
    1. Designer creates design specification (via A2A)
    2. Backend creates database schema and API (via A2A) - if backend required
    3. Frontend implements based on design + backend API (via A2A)
    4. Code Reviewer reviews code quality and security (via A2A)
    5. QA Engineer tests functionality and usability (via A2A)
    6. DevOps Engineer optimizes and deploys to Netlify (via A2A)
    7. Iterative improvement until quality standards met
    """

    # Orchestrator's agent ID for A2A protocol
    ORCHESTRATOR_ID = "orchestrator"

    # Agent IDs (must match BaseAgent initialization)
    DESIGNER_ID = "designer_001"
    BACKEND_ID = "backend_001"
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
        self.current_backend_spec = None  # Current backend specification (NEW!)

        # Detailed task tracking for status queries
        self.current_agent_working = None  # Which agent is currently active
        self.current_task_description = None  # What task is being executed
        self.workflow_steps_completed = []  # List of completed steps
        self.workflow_steps_total = 0  # Total number of steps in workflow

        # Project database management (for full-stack apps)
        self.project_id = None  # Project ID (set when creating backend)
        self.project_metadata = None  # Project metadata from database

        # State persistence (lazy initialization - initialized on first use)
        self.state_manager = None
        self._state_manager_initialized = False

        # Agent Lifecycle Management (NEW!)
        self.lifecycle_manager = None  # Lazy initialization
        self._lifecycle_enabled = os.getenv('ENABLE_LIFECYCLE_MANAGEMENT', 'true').lower() == 'true'
        self._handoff_manager = None  # Will be initialized async

        print("\n✅ Multi-Agent Orchestrator Ready (Lazy Initialization):")
        print(f"   - Agents will be spun up on-demand when needed")
        print(f"   - Agents will be cleaned up after task completion")
        print(f"   - Agent caching: {'Enabled' if self.enable_agent_caching else 'Disabled (saves memory)'}")
        print(f"   - Lifecycle Management: {'Enabled' if self._lifecycle_enabled else 'Disabled'}")
        print(f"   - AI Planner (Claude-powered workflow decisions)")
        print(f"   - Deployment SDK with {len(self.mcp_servers)} MCP servers")
        print(f"   - State persistence: PostgreSQL/Neon (lazy initialization)")
        print(f"\n🔗 A2A Protocol: Agents register/unregister dynamically")
        print("=" * 60 + "\n")

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
        if agent_id is None:
            return "Agent"
        elif "designer" in agent_id:
            return "UI/UX Designer"
        elif "backend" in agent_id:
            return "Backend Developer"
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
            "backend": "🔧",
            "implementation": "💻",
            "visual_review": "📸",
            "qa_testing": "🧪",
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
    # A2A HELPER METHODS
    # ==========================================

    def _get_agent_type_from_id(self, agent_id: str) -> str:
        """Map agent_id to agent_type"""
        if "designer" in agent_id:
            return "designer"
        elif "backend" in agent_id:
            return "backend"
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
        from agents.collaborative.models import Task

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
        # Logfire: Trace entire user request (root span)
        with trace_user_request(
            user_id=self.user_id,
            platform=self.platform,
            request_type='build_webapp',
            user_prompt=user_prompt
        ):
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
