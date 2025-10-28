"""
Token Tracker for Agent Context Window Management

Tracks cumulative token usage across all API calls for an agent instance.
Triggers warnings and critical alerts when approaching the 200K token limit.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

# Import telemetry for token usage tracing
from utils.telemetry import trace_token_usage


@dataclass
class TokenOperation:
    """Record of a single operation's token usage"""
    timestamp: str
    operation: str
    input_tokens: int
    output_tokens: int
    cumulative_total: int


class AgentTokenTracker:
    """
    Tracks cumulative token usage for an agent instance.

    Monitors token consumption across all Claude API calls and triggers
    warnings/critical alerts when approaching context window limits.

    Thresholds:
    - WARNING: 75% (150,000 tokens)
    - CRITICAL: 90% (180,000 tokens)
    - MAXIMUM: 100% (200,000 tokens)
    """

    def __init__(
        self,
        agent_id: str,
        context_window_limit: int = 200_000,
        warning_threshold: float = 0.75,
        critical_threshold: float = 0.90
    ):
        """
        Initialize token tracker.

        Args:
            agent_id: Unique agent identifier
            context_window_limit: Maximum context window size (default: 200K)
            warning_threshold: Warning threshold as percentage (default: 0.75)
            critical_threshold: Critical threshold as percentage (default: 0.90)
        """
        self.agent_id = agent_id
        self.context_window_limit = context_window_limit
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold

        # Cumulative counters
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cached_tokens = 0

        # Per-operation tracking
        self.operation_history: List[TokenOperation] = []

        # State flags
        self.warning_triggered = False
        self.critical_triggered = False

        print(f"🎯 TokenTracker initialized for {agent_id}")
        print(f"   Context Limit: {context_window_limit:,} tokens")
        print(f"   Warning @ {warning_threshold:.0%} ({self.warning_token_count:,} tokens)")
        print(f"   Critical @ {critical_threshold:.0%} ({self.critical_token_count:,} tokens)")

    @property
    def total_tokens(self) -> int:
        """Total tokens consumed (input + output)"""
        return self.total_input_tokens + self.total_output_tokens

    @property
    def remaining_tokens(self) -> int:
        """Tokens remaining before hitting limit"""
        return max(0, self.context_window_limit - self.total_tokens)

    @property
    def usage_percentage(self) -> float:
        """Percentage of context window used (0-100)"""
        if self.context_window_limit == 0:
            return 0.0
        return (self.total_tokens / self.context_window_limit) * 100

    @property
    def warning_token_count(self) -> int:
        """Token count that triggers warning"""
        return int(self.context_window_limit * self.warning_threshold)

    @property
    def critical_token_count(self) -> int:
        """Token count that triggers critical alert"""
        return int(self.context_window_limit * self.critical_threshold)

    @property
    def tokens_until_warning(self) -> int:
        """Tokens remaining until warning threshold"""
        return max(0, self.warning_token_count - self.total_tokens)

    @property
    def tokens_until_critical(self) -> int:
        """Tokens remaining until critical threshold"""
        return max(0, self.critical_token_count - self.total_tokens)

    def record_usage(
        self,
        operation_name: str,
        usage_obj: Any,
        timestamp: Optional[str] = None
    ) -> str:
        """
        Record token usage from Anthropic API response.

        Args:
            operation_name: Name of the operation (e.g., "send_message", "task_execute")
            usage_obj: Usage object from Anthropic API response (has input_tokens, output_tokens)
            timestamp: Optional ISO timestamp (defaults to now)

        Returns:
            Status string: "OK", "WARNING", or "CRITICAL"
        """
        # Extract token counts
        input_tokens = getattr(usage_obj, 'input_tokens', 0)
        output_tokens = getattr(usage_obj, 'output_tokens', 0)
        cache_creation_tokens = getattr(usage_obj, 'cache_creation_input_tokens', 0)
        cache_read_tokens = getattr(usage_obj, 'cache_read_input_tokens', 0)

        # Logfire: Trace token usage
        with trace_token_usage(
            agent_id=self.agent_id,
            operation_name=operation_name,
            total_tokens=self.total_tokens + input_tokens + output_tokens
        ) as span:
            # Update cumulative counters
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            self.total_cached_tokens += cache_creation_tokens

            # Record operation
            operation = TokenOperation(
                timestamp=timestamp or datetime.utcnow().isoformat(),
                operation=operation_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cumulative_total=self.total_tokens
            )
            self.operation_history.append(operation)

            # Determine status
            status = self._check_thresholds()

            # Add span attributes
            if span:
                span.set_attribute('input_tokens', input_tokens)
                span.set_attribute('output_tokens', output_tokens)
                span.set_attribute('cache_creation_tokens', cache_creation_tokens)
                span.set_attribute('cache_read_tokens', cache_read_tokens)
                span.set_attribute('usage_percentage', round(self.usage_percentage, 2))
                span.set_attribute('remaining_tokens', self.remaining_tokens)
                span.set_attribute('threshold_status', status)

            # Log operation
            print(f"📊 Token Usage [{self.agent_id}]:")
            print(f"   Operation: {operation_name}")
            print(f"   Input: {input_tokens:,} | Output: {output_tokens:,} | Total: {input_tokens + output_tokens:,}")
            print(f"   Cumulative: {self.total_tokens:,} / {self.context_window_limit:,} ({self.usage_percentage:.1f}%)")
            print(f"   Status: {status}")

            if cache_read_tokens > 0:
                print(f"   Cache Read: {cache_read_tokens:,} tokens (savings!)")

            return status

    def _check_thresholds(self) -> str:
        """
        Check if usage has crossed warning or critical thresholds.

        Returns:
            Status string: "OK", "WARNING", or "CRITICAL"
        """
        usage_pct = self.usage_percentage

        # Check critical threshold
        if usage_pct >= self.critical_threshold * 100:
            if not self.critical_triggered:
                self.critical_triggered = True
                print(f"🚨 CRITICAL: Agent {self.agent_id} at {usage_pct:.1f}% - HANDOFF REQUIRED!")
            return "CRITICAL"

        # Check warning threshold
        elif usage_pct >= self.warning_threshold * 100:
            if not self.warning_triggered:
                self.warning_triggered = True
                print(f"⚠️  WARNING: Agent {self.agent_id} at {usage_pct:.1f}% - approaching limit")
            return "WARNING"

        # Normal operation
        return "OK"

    def should_handoff(self) -> bool:
        """
        Determine if agent should perform handoff.

        Returns:
            True if usage >= critical threshold
        """
        return self.usage_percentage >= self.critical_threshold * 100

    def get_recent_operations(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most recent operations.

        Args:
            count: Number of recent operations to return

        Returns:
            List of operation dicts
        """
        recent = self.operation_history[-count:]
        return [
            {
                "timestamp": op.timestamp,
                "operation": op.operation,
                "input_tokens": op.input_tokens,
                "output_tokens": op.output_tokens,
                "cumulative_total": op.cumulative_total
            }
            for op in recent
        ]

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get detailed statistics about token usage.

        Returns:
            Dict with various statistics
        """
        if not self.operation_history:
            return {
                "total_operations": 0,
                "average_input_per_operation": 0,
                "average_output_per_operation": 0,
                "average_total_per_operation": 0,
                "largest_operation": None,
                "smallest_operation": None
            }

        # Calculate averages
        avg_input = self.total_input_tokens / len(self.operation_history)
        avg_output = self.total_output_tokens / len(self.operation_history)
        avg_total = (self.total_input_tokens + self.total_output_tokens) / len(self.operation_history)

        # Find largest and smallest
        largest = max(self.operation_history, key=lambda op: op.input_tokens + op.output_tokens)
        smallest = min(self.operation_history, key=lambda op: op.input_tokens + op.output_tokens)

        return {
            "total_operations": len(self.operation_history),
            "average_input_per_operation": round(avg_input, 1),
            "average_output_per_operation": round(avg_output, 1),
            "average_total_per_operation": round(avg_total, 1),
            "largest_operation": {
                "name": largest.operation,
                "tokens": largest.input_tokens + largest.output_tokens,
                "timestamp": largest.timestamp
            },
            "smallest_operation": {
                "name": smallest.operation,
                "tokens": smallest.input_tokens + smallest.output_tokens,
                "timestamp": smallest.timestamp
            }
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Export tracker state for persistence.

        Returns:
            Dict with all tracker state
        """
        return {
            "agent_id": self.agent_id,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cached_tokens": self.total_cached_tokens,
            "total_tokens": self.total_tokens,
            "usage_percentage": round(self.usage_percentage, 2),
            "remaining_tokens": self.remaining_tokens,
            "context_window_limit": self.context_window_limit,
            "operation_count": len(self.operation_history),
            "warning_triggered": self.warning_triggered,
            "critical_triggered": self.critical_triggered,
            "tokens_until_warning": self.tokens_until_warning,
            "tokens_until_critical": self.tokens_until_critical,
            "recent_operations": self.get_recent_operations(10),
            "statistics": self.get_statistics()
        }

    def reset(self):
        """
        Reset tracker to initial state.

        WARNING: This clears all history. Only use for testing.
        """
        print(f"🔄 Resetting token tracker for {self.agent_id}")
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cached_tokens = 0
        self.operation_history.clear()
        self.warning_triggered = False
        self.critical_triggered = False

    def __repr__(self) -> str:
        """String representation"""
        return (
            f"AgentTokenTracker(agent_id='{self.agent_id}', "
            f"total_tokens={self.total_tokens:,}, "
            f"usage={self.usage_percentage:.1f}%, "
            f"operations={len(self.operation_history)})"
        )


class ContextWindowExhausted(Exception):
    """
    Exception raised when context window is exhausted.

    This signals to the orchestrator that a handoff is required.
    """

    def __init__(
        self,
        agent_id: str,
        total_tokens: int,
        usage_percentage: float,
        message: Optional[str] = None
    ):
        """
        Initialize exception.

        Args:
            agent_id: Agent that exhausted context
            total_tokens: Total tokens consumed
            usage_percentage: Usage percentage
            message: Optional custom message
        """
        self.agent_id = agent_id
        self.total_tokens = total_tokens
        self.usage_percentage = usage_percentage

        if message is None:
            message = (
                f"Agent {agent_id} has exhausted context window: "
                f"{total_tokens:,} tokens ({usage_percentage:.1f}% used). "
                f"Handoff required."
            )

        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """Export exception details"""
        return {
            "error_type": "ContextWindowExhausted",
            "agent_id": self.agent_id,
            "total_tokens": self.total_tokens,
            "usage_percentage": self.usage_percentage,
            "message": str(self)
        }
