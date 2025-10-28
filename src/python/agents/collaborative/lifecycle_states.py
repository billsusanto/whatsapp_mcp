"""
Agent Lifecycle States

Defines the states an agent instance can be in during its lifecycle.
"""

from enum import Enum


class AgentLifecycleState(Enum):
    """
    Agent instance lifecycle states.

    Lifecycle flow:
    INITIALIZING → ACTIVE → WARNING → CRITICAL → HANDOFF_PENDING → HANDOFF_COMPLETE → TERMINATED
    """

    INITIALIZING = "initializing"
    """Agent is being created and initialized"""

    ACTIVE = "active"
    """Agent is actively processing tasks (normal operation)"""

    WARNING = "warning"
    """Agent has exceeded 75% token usage (monitor closely)"""

    CRITICAL = "critical"
    """Agent has exceeded 90% token usage (handoff imminent)"""

    HANDOFF_PENDING = "handoff_pending"
    """Agent is creating handoff document (paused from new tasks)"""

    HANDOFF_COMPLETE = "handoff_complete"
    """Handoff document created, waiting for termination"""

    TERMINATED = "terminated"
    """Agent instance has been terminated and cleaned up"""

    ERROR = "error"
    """Agent encountered an error and needs intervention"""

    PAUSED = "paused"
    """Agent is temporarily paused (not receiving tasks)"""

    def __str__(self) -> str:
        """String representation"""
        return self.value

    @property
    def is_operational(self) -> bool:
        """Check if agent is in an operational state"""
        return self in {
            AgentLifecycleState.ACTIVE,
            AgentLifecycleState.WARNING,
            AgentLifecycleState.CRITICAL
        }

    @property
    def can_accept_tasks(self) -> bool:
        """Check if agent can accept new tasks"""
        return self in {
            AgentLifecycleState.ACTIVE,
            AgentLifecycleState.WARNING
        }

    @property
    def requires_attention(self) -> bool:
        """Check if state requires orchestrator attention"""
        return self in {
            AgentLifecycleState.CRITICAL,
            AgentLifecycleState.ERROR,
            AgentLifecycleState.HANDOFF_PENDING
        }

    @property
    def is_transitioning(self) -> bool:
        """Check if agent is in a transitional state"""
        return self in {
            AgentLifecycleState.INITIALIZING,
            AgentLifecycleState.HANDOFF_PENDING,
            AgentLifecycleState.HANDOFF_COMPLETE
        }

    def get_emoji(self) -> str:
        """Get emoji representation for logging"""
        emoji_map = {
            AgentLifecycleState.INITIALIZING: "🔄",
            AgentLifecycleState.ACTIVE: "✅",
            AgentLifecycleState.WARNING: "⚠️",
            AgentLifecycleState.CRITICAL: "🚨",
            AgentLifecycleState.HANDOFF_PENDING: "⏸️",
            AgentLifecycleState.HANDOFF_COMPLETE: "📦",
            AgentLifecycleState.TERMINATED: "🛑",
            AgentLifecycleState.ERROR: "❌",
            AgentLifecycleState.PAUSED: "⏯️"
        }
        return emoji_map.get(self, "❓")


class AgentTerminationReason(Enum):
    """
    Reasons why an agent instance was terminated.

    Used for audit logging and analytics.
    """

    CONTEXT_WINDOW_EXHAUSTED = "context_window_exhausted"
    """Agent exhausted its context window (normal handoff)"""

    TASK_COMPLETED = "task_completed"
    """Agent completed its assigned task"""

    ERROR = "error"
    """Agent encountered an unrecoverable error"""

    MANUAL_TERMINATION = "manual_termination"
    """Agent was manually terminated by operator"""

    ORCHESTRATOR_SHUTDOWN = "orchestrator_shutdown"
    """Orchestrator is shutting down (graceful)"""

    TIMEOUT = "timeout"
    """Agent exceeded maximum runtime"""

    RESOURCE_CLEANUP = "resource_cleanup"
    """Agent terminated for resource management"""

    HANDOFF_COMPLETE = "handoff_complete"
    """Agent terminated after successful handoff"""

    def __str__(self) -> str:
        """String representation"""
        return self.value
