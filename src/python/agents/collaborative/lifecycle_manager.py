"""
Agent Lifecycle Manager

Manages the complete lifecycle of agent instances including:
- Spawning with token tracking
- Real-time monitoring
- Automatic handoff triggering
- Agent termination and cleanup
- State persistence via HandoffManager
"""

import asyncio
from typing import Dict, Optional, Callable, Any, List
from datetime import datetime
from dataclasses import dataclass

from agents.collaborative.token_tracker import AgentTokenTracker, ContextWindowExhausted
from agents.collaborative.lifecycle_states import AgentLifecycleState, AgentTerminationReason
from agents.collaborative.handoff_manager import HandoffManager
from agents.collaborative.handoff_models import HandoffDocument

# Import Logfire tracing
from utils.telemetry import (
    trace_agent_spawn,
    trace_agent_handoff,
    trace_threshold_event,
    log_event
)


@dataclass
class AgentInstance:
    """
    Represents a running agent instance with its state.
    """
    agent_id: str
    agent_type: str
    agent_role: str
    version: int
    spawn_timestamp: datetime
    token_tracker: AgentTokenTracker
    state: AgentLifecycleState
    agent_object: Any  # The actual agent instance
    trace_id: str
    task_id: str
    user_id: str
    project_id: str


class AgentLifecycleManager:
    """
    Manages agent lifecycles with automatic context window management.

    Features:
    - Token tracking for all agents
    - Automatic handoff when context window exhausted
    - Agent registry with state management
    - Integration with HandoffManager for persistence
    - Callbacks for orchestrator integration

    Usage:
        manager = AgentLifecycleManager(handoff_manager)
        agent = await manager.spawn_agent(
            agent_type="frontend",
            agent_role="Frontend Developer",
            ...
        )
        await manager.monitor_agents()  # Run in background
    """

    def __init__(
        self,
        handoff_manager: HandoffManager,
        context_window_limit: int = 200_000,
        warning_threshold: float = 0.75,
        critical_threshold: float = 0.90
    ):
        """
        Initialize lifecycle manager.

        Args:
            handoff_manager: HandoffManager for persisting handoffs
            context_window_limit: Token limit per agent (default: 200K)
            warning_threshold: Warning threshold (default: 0.75 = 75%)
            critical_threshold: Critical threshold (default: 0.90 = 90%)
        """
        self.handoff_manager = handoff_manager
        self.context_window_limit = context_window_limit
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold

        # Agent registry: agent_id -> AgentInstance
        self.active_agents: Dict[str, AgentInstance] = {}

        # Version tracking: agent_type -> current_version
        self.agent_versions: Dict[str, int] = {}

        # Callbacks for orchestrator
        self.on_warning_callback: Optional[Callable] = None
        self.on_critical_callback: Optional[Callable] = None
        self.on_handoff_callback: Optional[Callable] = None
        self.on_agent_terminated_callback: Optional[Callable] = None

        # Monitoring
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None

        print(f"🎯 AgentLifecycleManager initialized")
        print(f"   Context Limit: {context_window_limit:,} tokens")
        print(f"   WARNING @ {warning_threshold:.0%}, CRITICAL @ {critical_threshold:.0%}")

    def set_callbacks(
        self,
        on_warning: Optional[Callable] = None,
        on_critical: Optional[Callable] = None,
        on_handoff: Optional[Callable] = None,
        on_agent_terminated: Optional[Callable] = None
    ):
        """
        Set callbacks for lifecycle events.

        Args:
            on_warning: Called when agent reaches warning threshold
            on_critical: Called when agent reaches critical threshold
            on_handoff: Called when handoff is created
            on_agent_terminated: Called when agent is terminated
        """
        self.on_warning_callback = on_warning
        self.on_critical_callback = on_critical
        self.on_handoff_callback = on_handoff
        self.on_agent_terminated_callback = on_agent_terminated

        print(f"✅ Callbacks configured")

    def spawn_agent(
        self,
        agent_type: str,
        agent_role: str,
        agent_object: Any,
        user_id: str,
        project_id: str,
        trace_id: Optional[str] = None,
        task_id: Optional[str] = None,
        handoff_document: Optional[HandoffDocument] = None
    ) -> AgentInstance:
        """
        Spawn a new agent instance with token tracking.

        Args:
            agent_type: Type of agent (frontend, backend, etc.)
            agent_role: Role description
            agent_object: The actual agent instance
            user_id: User identifier
            project_id: Project identifier
            trace_id: Optional trace ID for handoff chain
            task_id: Optional task identifier
            handoff_document: Optional handoff from previous agent

        Returns:
            AgentInstance
        """
        # Determine version
        if agent_type in self.agent_versions:
            version = self.agent_versions[agent_type] + 1
        else:
            version = 1

        self.agent_versions[agent_type] = version

        # Generate IDs
        import uuid
        agent_id = f"{agent_type}_v{version}_{uuid.uuid4().hex[:8]}"
        trace_id = trace_id or f"trace_{uuid.uuid4().hex[:16]}"
        task_id = task_id or f"task_{uuid.uuid4().hex[:16]}"

        # Logfire: Trace agent spawn
        with trace_agent_spawn(
            agent_id=agent_id,
            agent_type=agent_type,
            version=version,
            handoff_id=handoff_document.handoff_id if handoff_document else None,
            predecessor_agent_id=handoff_document.source_agent.agent_id if handoff_document else None
        ):
            # Create token tracker
            token_tracker = AgentTokenTracker(
                agent_id=agent_id,
                context_window_limit=self.context_window_limit,
                warning_threshold=self.warning_threshold,
                critical_threshold=self.critical_threshold
            )

            # Create agent instance
            instance = AgentInstance(
                agent_id=agent_id,
                agent_type=agent_type,
                agent_role=agent_role,
                version=version,
                spawn_timestamp=datetime.utcnow(),
                token_tracker=token_tracker,
                state=AgentLifecycleState.INITIALIZING,
                agent_object=agent_object,
                trace_id=trace_id,
                task_id=task_id,
                user_id=user_id,
                project_id=project_id
            )

            # Register agent
            self.active_agents[agent_id] = instance

            # Transition to ACTIVE
            self._transition_state(agent_id, AgentLifecycleState.ACTIVE)

            # Log spawn event
            log_event(
                "agent_spawned",
                agent_id=agent_id,
                agent_type=agent_type,
                version=version,
                continuation_mode="handoff" if handoff_document else "fresh",
                user_id=user_id,
                project_id=project_id
            )

            print(f"🚀 Spawned agent: {agent_id}")
            print(f"   Type: {agent_type}")
            print(f"   Version: v{version}")
            print(f"   User: {user_id}")
            print(f"   Project: {project_id}")

            if handoff_document:
                print(f"   Continuing from handoff: {handoff_document.handoff_id}")
                print(f"   Previous completion: {handoff_document.task_progress.overall_completion_percentage}%")

        return instance

    def get_agent(self, agent_id: str) -> Optional[AgentInstance]:
        """Get agent instance by ID."""
        return self.active_agents.get(agent_id)

    def get_agents_by_type(self, agent_type: str) -> List[AgentInstance]:
        """Get all agents of a specific type."""
        return [
            agent for agent in self.active_agents.values()
            if agent.agent_type == agent_type
        ]

    def get_agents_by_user(self, user_id: str) -> List[AgentInstance]:
        """Get all agents for a specific user."""
        return [
            agent for agent in self.active_agents.values()
            if agent.user_id == user_id
        ]

    def record_usage(
        self,
        agent_id: str,
        operation_name: str,
        usage_obj: Any
    ) -> str:
        """
        Record token usage for an agent.

        Args:
            agent_id: Agent identifier
            operation_name: Name of operation
            usage_obj: Anthropic API usage object

        Returns:
            Status: "OK", "WARNING", or "CRITICAL"

        Raises:
            ContextWindowExhausted: If critical threshold exceeded
        """
        agent = self.active_agents.get(agent_id)
        if not agent:
            print(f"⚠️  Agent not found: {agent_id}")
            return "OK"

        # Record usage
        status = agent.token_tracker.record_usage(operation_name, usage_obj)

        # Handle state transitions
        if status == "WARNING" and agent.state == AgentLifecycleState.ACTIVE:
            # Logfire: Trace warning threshold event
            with trace_threshold_event(
                agent_id=agent_id,
                threshold_type='warning',
                token_usage=agent.token_tracker.total_tokens,
                usage_percentage=agent.token_tracker.usage_percentage,
                tokens_remaining=agent.token_tracker.remaining_tokens
            ):
                self._transition_state(agent_id, AgentLifecycleState.WARNING)

                # Call warning callback
                if self.on_warning_callback:
                    asyncio.create_task(self.on_warning_callback(agent))

        elif status == "CRITICAL" and agent.state in {AgentLifecycleState.ACTIVE, AgentLifecycleState.WARNING}:
            # Logfire: Trace critical threshold event
            with trace_threshold_event(
                agent_id=agent_id,
                threshold_type='critical',
                token_usage=agent.token_tracker.total_tokens,
                usage_percentage=agent.token_tracker.usage_percentage,
                tokens_remaining=agent.token_tracker.remaining_tokens
            ):
                self._transition_state(agent_id, AgentLifecycleState.CRITICAL)

                # Call critical callback
                if self.on_critical_callback:
                    asyncio.create_task(self.on_critical_callback(agent))

            # Raise exception to trigger handoff
            raise ContextWindowExhausted(
                agent_id=agent_id,
                total_tokens=agent.token_tracker.total_tokens,
                usage_percentage=agent.token_tracker.usage_percentage
            )

        return status

    async def create_handoff(
        self,
        agent_id: str,
        termination_reason: AgentTerminationReason,
        platform: str,
        workflow_type: str,
        original_request: str,
        task_description: str,
        current_phase: str,
        completion_percentage: int,
        task_status: str,
        **kwargs  # Additional handoff fields
    ) -> HandoffDocument:
        """
        Create a handoff document for an agent.

        Args:
            agent_id: Agent being handed off
            termination_reason: Why agent is terminating
            platform: Platform (whatsapp, github)
            workflow_type: Workflow type
            original_request: Original user request
            task_description: Current task description
            current_phase: Current phase
            completion_percentage: Completion percentage (0-100)
            task_status: Task status
            **kwargs: Additional handoff fields

        Returns:
            HandoffDocument
        """
        agent = self.active_agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")

        # Calculate target agent ID (next version)
        next_version = agent.version + 1
        import uuid
        target_agent_id = f"{agent.agent_type}_v{next_version}_{uuid.uuid4().hex[:8]}"

        # Logfire: Trace agent handoff
        with trace_agent_handoff(
            source_agent_id=agent.agent_id,
            target_agent_id=target_agent_id,
            handoff_id=f"handoff_{uuid.uuid4().hex[:16]}",
            trace_id=agent.trace_id,
            termination_reason=str(termination_reason),
            completion_percentage=completion_percentage,
            tokens_used=agent.token_tracker.total_tokens
        ):
            # Transition to handoff pending
            self._transition_state(agent_id, AgentLifecycleState.HANDOFF_PENDING)

            # Create handoff
            handoff = await self.handoff_manager.create_handoff(
                source_agent_id=agent.agent_id,
                source_agent_type=agent.agent_type,
                source_agent_role=agent.agent_role,
                source_agent_version=agent.version,
                termination_reason=str(termination_reason),
                token_tracker=agent.token_tracker,
                user_id=agent.user_id,
                project_id=agent.project_id,
                platform=platform,
                workflow_type=workflow_type,
                original_request=original_request,
                task_description=task_description,
                current_phase=current_phase,
                completion_percentage=completion_percentage,
                task_status=task_status,
                trace_id=agent.trace_id,
                task_id=agent.task_id,
                source_spawn_timestamp=agent.spawn_timestamp.isoformat(),
                **kwargs
            )

            # Get predecessor handoff ID if exists
            predecessor_id = kwargs.get('predecessor_handoff_id')

            # Save to database
            await self.handoff_manager.save_handoff(handoff, predecessor_handoff_id=predecessor_id)

            # Transition to handoff complete
            self._transition_state(agent_id, AgentLifecycleState.HANDOFF_COMPLETE)

            # Call handoff callback
            if self.on_handoff_callback:
                await self.on_handoff_callback(agent, handoff)

            print(f"📦 Handoff created for {agent_id}")
            print(f"   Database ID: {handoff.database_id}")
            print(f"   Trace ID: {handoff.trace_id}")

        return handoff

    async def terminate_agent(
        self,
        agent_id: str,
        reason: AgentTerminationReason
    ):
        """
        Terminate an agent instance.

        Args:
            agent_id: Agent to terminate
            reason: Termination reason
        """
        agent = self.active_agents.get(agent_id)
        if not agent:
            print(f"⚠️  Agent not found: {agent_id}")
            return

        # Transition to terminated
        self._transition_state(agent_id, AgentLifecycleState.TERMINATED)

        # Call termination callback
        if self.on_agent_terminated_callback:
            await self.on_agent_terminated_callback(agent, reason)

        # Logfire: Log agent termination
        log_event(
            "agent_terminated",
            agent_id=agent_id,
            agent_type=agent.agent_type,
            termination_reason=str(reason),
            total_tokens_used=agent.token_tracker.total_tokens,
            lifetime_seconds=(datetime.utcnow() - agent.spawn_timestamp).total_seconds()
        )

        # Remove from active agents
        del self.active_agents[agent_id]

        print(f"🛑 Terminated agent: {agent_id}")
        print(f"   Reason: {reason}")
        print(f"   Total tokens used: {agent.token_tracker.total_tokens:,}")
        print(f"   Active agents remaining: {len(self.active_agents)}")

    def _transition_state(self, agent_id: str, new_state: AgentLifecycleState):
        """Transition agent to new state."""
        agent = self.active_agents.get(agent_id)
        if not agent:
            return

        old_state = agent.state
        agent.state = new_state

        emoji = new_state.get_emoji()
        print(f"{emoji} State transition: {agent_id}")
        print(f"   {old_state.value} → {new_state.value}")

    async def start_monitoring(self, interval: float = 5.0):
        """
        Start monitoring all agents.

        Args:
            interval: Monitoring interval in seconds
        """
        if self._monitoring:
            print("⚠️  Monitoring already running")
            return

        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop(interval))

        print(f"👁️  Started agent monitoring (interval: {interval}s)")

    async def stop_monitoring(self):
        """Stop monitoring agents."""
        if not self._monitoring:
            return

        self._monitoring = False

        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        print("🛑 Stopped agent monitoring")

    async def _monitor_loop(self, interval: float):
        """Background monitoring loop."""
        while self._monitoring:
            try:
                await self._check_agents()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                await asyncio.sleep(interval)

    async def _check_agents(self):
        """Check all active agents for issues."""
        for agent_id, agent in list(self.active_agents.items()):
            # Check if agent needs attention
            if agent.state.requires_attention:
                print(f"⚠️  Agent requires attention: {agent_id} ({agent.state.value})")

            # Check if agent is stuck in transitional state
            if agent.state.is_transitioning:
                elapsed = (datetime.utcnow() - agent.spawn_timestamp).total_seconds()
                if elapsed > 300:  # 5 minutes
                    print(f"⚠️  Agent stuck in {agent.state.value}: {agent_id}")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get lifecycle manager statistics.

        Returns:
            Statistics dictionary
        """
        total_agents = len(self.active_agents)
        agents_by_state = {}
        agents_by_type = {}
        total_tokens = 0

        for agent in self.active_agents.values():
            # Count by state
            state_name = agent.state.value
            agents_by_state[state_name] = agents_by_state.get(state_name, 0) + 1

            # Count by type
            agents_by_type[agent.agent_type] = agents_by_type.get(agent.agent_type, 0) + 1

            # Sum tokens
            total_tokens += agent.token_tracker.total_tokens

        return {
            'total_active_agents': total_agents,
            'agents_by_state': agents_by_state,
            'agents_by_type': agents_by_type,
            'total_tokens_consumed': total_tokens,
            'average_tokens_per_agent': round(total_tokens / total_agents, 1) if total_agents > 0 else 0,
            'monitoring_enabled': self._monitoring
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"AgentLifecycleManager(active_agents={len(self.active_agents)}, "
            f"monitoring={self._monitoring})"
        )
