"""
Agent Lifecycle Management Module for Collaborative Orchestrator
Handles lazy agent initialization, cleanup, and lifecycle management
"""

from typing import Dict, Optional

# Import telemetry
from utils.telemetry import log_event


class OrchestratorAgentsMixin:
    """
    Mixin providing agent lifecycle management methods for the orchestrator.

    This mixin handles:
    - Lazy agent initialization (on-demand)
    - Agent cleanup and resource management
    - Lifecycle manager integration
    - Context window management callbacks
    """

    async def _get_agent(self, agent_type: str):
        """
        Get or create an agent on-demand (lazy initialization)

        Args:
            agent_type: Type of agent ("designer", "backend", "frontend", "code_reviewer", "qa", "devops")

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

        # Import agents lazily
        from agents.collaborative.designer_agent import DesignerAgent
        from agents.collaborative.frontend_agent import FrontendDeveloperAgent
        from agents.collaborative.backend_agent import BackendAgent
        from agents.collaborative.code_reviewer_agent import CodeReviewerAgent
        from agents.collaborative.qa_agent import QAEngineerAgent
        from agents.collaborative.devops_agent import DevOpsEngineerAgent

        # Import project manager for backend/devops
        try:
            from database.project_manager import project_manager
            PROJECT_MANAGER_AVAILABLE = True
        except ImportError:
            PROJECT_MANAGER_AVAILABLE = False
            project_manager = None

        if agent_type == "designer":
            agent = DesignerAgent(self.mcp_servers)
        elif agent_type == "backend":
            # Backend agent needs project_manager for database operations
            if PROJECT_MANAGER_AVAILABLE:
                agent = BackendAgent(self.mcp_servers, project_manager=project_manager)
            else:
                raise ValueError("Backend agent requires project_manager (database features)")
        elif agent_type == "frontend":
            agent = FrontendDeveloperAgent(self.mcp_servers)
        elif agent_type == "code_reviewer":
            agent = CodeReviewerAgent(self.mcp_servers)
        elif agent_type == "qa":
            agent = QAEngineerAgent(self.mcp_servers)
        elif agent_type == "devops":
            agent = DevOpsEngineerAgent(self.mcp_servers, project_manager=project_manager)
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
        from agents.collaborative.a2a_protocol import a2a_protocol
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
    # LIFECYCLE MANAGER (CONTEXT WINDOW MANAGEMENT)
    # ==========================================

    async def _ensure_lifecycle_manager(self):
        """Initialize lifecycle manager on first use (async lazy initialization)"""
        if self.lifecycle_manager is not None:
            return

        if not self._lifecycle_enabled:
            return

        print("🔄 Initializing Lifecycle Manager...")

        # Import lifecycle manager
        from agents.collaborative.lifecycle_manager import AgentLifecycleManager

        # For now, create lifecycle manager without handoff persistence
        # Full database integration will be added in Phase 2
        self.lifecycle_manager = AgentLifecycleManager(
            handoff_manager=None,  # TODO: Add handoff manager with database session
            context_window_limit=200_000,
            warning_threshold=0.75,
            critical_threshold=0.90
        )

        # Set up callbacks
        self.lifecycle_manager.set_callbacks(
            on_warning=self._on_agent_warning,
            on_critical=self._on_agent_critical,
            on_handoff=self._on_agent_handoff,
            on_agent_terminated=self._on_agent_terminated
        )

        print("✅ Lifecycle Manager initialized")

    async def _on_agent_warning(self, agent_instance):
        """Called when agent reaches warning threshold (75%)"""
        print(f"⚠️  Agent warning: {agent_instance.agent_id}")
        print(f"   Token usage: {agent_instance.token_tracker.usage_percentage:.1f}%")

        # Notify user
        await self._send_notification(
            f"⚠️ {self._get_agent_type_name(agent_instance.agent_id)} at {agent_instance.token_tracker.usage_percentage:.1f}% token usage\n"
            f"   Approaching context limit. Will auto-handoff at 90%."
        )

    async def _on_agent_critical(self, agent_instance):
        """Called when agent reaches critical threshold (90%)"""
        print(f"🚨 Agent critical: {agent_instance.agent_id}")
        print(f"   Token usage: {agent_instance.token_tracker.usage_percentage:.1f}%")

        # Notify user
        await self._send_notification(
            f"🚨 {self._get_agent_type_name(agent_instance.agent_id)} at CRITICAL token usage\n"
            f"   Handoff will trigger soon..."
        )

    async def _on_agent_handoff(self, agent_instance, handoff_document):
        """Called when handoff is created"""
        print(f"📦 Handoff created: {handoff_document.handoff_id}")

        # Log to telemetry
        log_event(
            "agent_handoff",
            {
                "agent_id": agent_instance.agent_id,
                "agent_type": agent_instance.agent_type,
                "handoff_id": handoff_document.handoff_id,
                "tokens_used": handoff_document.token_usage.total_tokens,
                "completion": handoff_document.task_progress.overall_completion_percentage
            }
        )

    async def _on_agent_terminated(self, agent_instance, reason):
        """Called when agent is terminated"""
        print(f"🛑 Agent terminated: {agent_instance.agent_id}")
        print(f"   Reason: {reason}")

        # Log to telemetry
        log_event(
            "agent_terminated",
            {
                "agent_id": agent_instance.agent_id,
                "agent_type": agent_instance.agent_type,
                "reason": str(reason),
                "total_tokens": agent_instance.token_tracker.total_tokens
            }
        )

    def _calculate_completion_percentage(self) -> int:
        """Calculate current workflow completion percentage"""
        if self.workflow_steps_total == 0:
            return 0

        completed = len(self.workflow_steps_completed)
        total = self.workflow_steps_total

        return min(100, int((completed / total) * 100))
