"""
Unit Tests for AgentTokenTracker

Tests token tracking, threshold detection, and context window management.
"""

import pytest
from datetime import datetime
from src.python.agents.collaborative.token_tracker import (
    AgentTokenTracker,
    ContextWindowExhausted,
    TokenOperation
)


# Mock usage object (mimics Anthropic API response)
class MockUsage:
    """Mock Anthropic API usage object"""

    def __init__(
        self,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cache_creation_input_tokens: int = 0,
        cache_read_input_tokens: int = 0
    ):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.cache_creation_input_tokens = cache_creation_input_tokens
        self.cache_read_input_tokens = cache_read_input_tokens


class TestAgentTokenTracker:
    """Test suite for AgentTokenTracker"""

    def test_initialization(self):
        """Test tracker initialization with default values"""
        tracker = AgentTokenTracker(agent_id="test_agent")

        assert tracker.agent_id == "test_agent"
        assert tracker.context_window_limit == 200_000
        assert tracker.warning_threshold == 0.75
        assert tracker.critical_threshold == 0.90
        assert tracker.total_tokens == 0
        assert tracker.remaining_tokens == 200_000
        assert tracker.usage_percentage == 0.0

    def test_initialization_custom_limits(self):
        """Test tracker with custom limits"""
        tracker = AgentTokenTracker(
            agent_id="test_agent",
            context_window_limit=100_000,
            warning_threshold=0.8,
            critical_threshold=0.95
        )

        assert tracker.context_window_limit == 100_000
        assert tracker.warning_threshold == 0.8
        assert tracker.critical_threshold == 0.95
        assert tracker.warning_token_count == 80_000
        assert tracker.critical_token_count == 95_000

    def test_record_usage_basic(self):
        """Test basic usage recording"""
        tracker = AgentTokenTracker("test_agent", context_window_limit=1000)
        usage = MockUsage(input_tokens=100, output_tokens=50)

        status = tracker.record_usage("test_operation", usage)

        assert status == "OK"
        assert tracker.total_input_tokens == 100
        assert tracker.total_output_tokens == 50
        assert tracker.total_tokens == 150
        assert tracker.usage_percentage == 15.0
        assert tracker.remaining_tokens == 850
        assert len(tracker.operation_history) == 1

    def test_record_usage_cumulative(self):
        """Test cumulative token tracking"""
        tracker = AgentTokenTracker("test_agent", context_window_limit=1000)

        # First operation
        usage1 = MockUsage(input_tokens=100, output_tokens=50)
        tracker.record_usage("operation_1", usage1)

        # Second operation
        usage2 = MockUsage(input_tokens=200, output_tokens=100)
        tracker.record_usage("operation_2", usage2)

        # Third operation
        usage3 = MockUsage(input_tokens=150, output_tokens=75)
        tracker.record_usage("operation_3", usage3)

        assert tracker.total_input_tokens == 450
        assert tracker.total_output_tokens == 225
        assert tracker.total_tokens == 675
        assert tracker.usage_percentage == 67.5
        assert len(tracker.operation_history) == 3

    def test_warning_threshold(self):
        """Test warning threshold detection"""
        tracker = AgentTokenTracker("test_agent", context_window_limit=1000)

        # Add tokens up to 74% (below warning)
        usage1 = MockUsage(input_tokens=740, output_tokens=0)
        status1 = tracker.record_usage("operation_1", usage1)
        assert status1 == "OK"
        assert not tracker.warning_triggered

        # Add tokens to cross warning threshold (75%)
        usage2 = MockUsage(input_tokens=10, output_tokens=0)
        status2 = tracker.record_usage("operation_2", usage2)
        assert status2 == "WARNING"
        assert tracker.warning_triggered
        assert not tracker.critical_triggered
        assert not tracker.should_handoff()

    def test_critical_threshold(self):
        """Test critical threshold detection"""
        tracker = AgentTokenTracker("test_agent", context_window_limit=1000)

        # Add tokens up to 89% (below critical)
        usage1 = MockUsage(input_tokens=890, output_tokens=0)
        status1 = tracker.record_usage("operation_1", usage1)
        assert status1 == "WARNING"  # Above warning but below critical

        # Add tokens to cross critical threshold (90%)
        usage2 = MockUsage(input_tokens=10, output_tokens=0)
        status2 = tracker.record_usage("operation_2", usage2)
        assert status2 == "CRITICAL"
        assert tracker.critical_triggered
        assert tracker.should_handoff()

    def test_should_handoff(self):
        """Test handoff decision logic"""
        tracker = AgentTokenTracker("test_agent", context_window_limit=1000)

        # Below critical
        usage1 = MockUsage(input_tokens=850, output_tokens=0)
        tracker.record_usage("op1", usage1)
        assert not tracker.should_handoff()

        # At critical threshold
        usage2 = MockUsage(input_tokens=50, output_tokens=0)
        tracker.record_usage("op2", usage2)
        assert tracker.should_handoff()

    def test_tokens_until_thresholds(self):
        """Test calculation of tokens until thresholds"""
        tracker = AgentTokenTracker("test_agent", context_window_limit=1000)

        # Initial state
        assert tracker.tokens_until_warning == 750
        assert tracker.tokens_until_critical == 900

        # After consuming 500 tokens
        usage = MockUsage(input_tokens=500, output_tokens=0)
        tracker.record_usage("op", usage)

        assert tracker.tokens_until_warning == 250
        assert tracker.tokens_until_critical == 400

        # After exceeding warning
        usage2 = MockUsage(input_tokens=300, output_tokens=0)
        tracker.record_usage("op2", usage2)

        assert tracker.tokens_until_warning == 0
        assert tracker.tokens_until_critical == 100

    def test_cache_tokens(self):
        """Test tracking of cached tokens"""
        tracker = AgentTokenTracker("test_agent")

        usage = MockUsage(
            input_tokens=100,
            output_tokens=50,
            cache_creation_input_tokens=20,
            cache_read_input_tokens=30
        )
        tracker.record_usage("cached_op", usage)

        assert tracker.total_cached_tokens == 20
        assert tracker.total_input_tokens == 100
        assert tracker.total_output_tokens == 50

    def test_operation_history(self):
        """Test operation history tracking"""
        tracker = AgentTokenTracker("test_agent")

        # Record multiple operations
        for i in range(5):
            usage = MockUsage(input_tokens=100 * (i + 1), output_tokens=50 * (i + 1))
            tracker.record_usage(f"operation_{i}", usage)

        assert len(tracker.operation_history) == 5

        # Check operation details
        op = tracker.operation_history[0]
        assert isinstance(op, TokenOperation)
        assert op.operation == "operation_0"
        assert op.input_tokens == 100
        assert op.output_tokens == 50
        assert op.cumulative_total == 150

        # Last operation
        last_op = tracker.operation_history[-1]
        assert last_op.operation == "operation_4"
        assert last_op.cumulative_total == 1500  # Sum of all operations

    def test_get_recent_operations(self):
        """Test getting recent operations"""
        tracker = AgentTokenTracker("test_agent")

        # Add 15 operations
        for i in range(15):
            usage = MockUsage(input_tokens=10, output_tokens=5)
            tracker.record_usage(f"op_{i}", usage)

        # Get recent 10
        recent = tracker.get_recent_operations(10)
        assert len(recent) == 10
        assert recent[0]["operation"] == "op_5"  # Last 10 start from op_5
        assert recent[-1]["operation"] == "op_14"

        # Get recent 5
        recent5 = tracker.get_recent_operations(5)
        assert len(recent5) == 5
        assert recent5[0]["operation"] == "op_10"

    def test_statistics(self):
        """Test usage statistics"""
        tracker = AgentTokenTracker("test_agent")

        # No operations yet
        stats = tracker.get_statistics()
        assert stats["total_operations"] == 0

        # Add varied operations
        usage1 = MockUsage(input_tokens=100, output_tokens=50)
        usage2 = MockUsage(input_tokens=200, output_tokens=100)
        usage3 = MockUsage(input_tokens=50, output_tokens=25)

        tracker.record_usage("op1", usage1)
        tracker.record_usage("op2", usage2)
        tracker.record_usage("op3", usage3)

        stats = tracker.get_statistics()
        assert stats["total_operations"] == 3
        assert stats["average_input_per_operation"] == pytest.approx(116.7, rel=0.1)
        assert stats["average_output_per_operation"] == pytest.approx(58.3, rel=0.1)
        assert stats["largest_operation"]["name"] == "op2"
        assert stats["largest_operation"]["tokens"] == 300
        assert stats["smallest_operation"]["name"] == "op3"
        assert stats["smallest_operation"]["tokens"] == 75

    def test_to_dict(self):
        """Test exporting tracker state to dict"""
        tracker = AgentTokenTracker("test_agent", context_window_limit=1000)

        usage = MockUsage(input_tokens=500, output_tokens=250)
        tracker.record_usage("test_op", usage)

        state = tracker.to_dict()

        assert state["agent_id"] == "test_agent"
        assert state["total_input_tokens"] == 500
        assert state["total_output_tokens"] == 250
        assert state["total_tokens"] == 750
        assert state["usage_percentage"] == 75.0
        assert state["remaining_tokens"] == 250
        assert state["context_window_limit"] == 1000
        assert state["operation_count"] == 1
        assert state["warning_triggered"] == True
        assert state["critical_triggered"] == False
        assert "recent_operations" in state
        assert "statistics" in state

    def test_reset(self):
        """Test resetting tracker"""
        tracker = AgentTokenTracker("test_agent")

        # Add usage
        usage = MockUsage(input_tokens=1000, output_tokens=500)
        tracker.record_usage("op", usage)

        assert tracker.total_tokens == 1500
        assert len(tracker.operation_history) == 1

        # Reset
        tracker.reset()

        assert tracker.total_tokens == 0
        assert tracker.total_input_tokens == 0
        assert tracker.total_output_tokens == 0
        assert tracker.total_cached_tokens == 0
        assert len(tracker.operation_history) == 0
        assert not tracker.warning_triggered
        assert not tracker.critical_triggered

    def test_repr(self):
        """Test string representation"""
        tracker = AgentTokenTracker("test_agent")
        usage = MockUsage(input_tokens=1000, output_tokens=500)
        tracker.record_usage("op", usage)

        repr_str = repr(tracker)
        assert "test_agent" in repr_str
        assert "1,500" in repr_str  # Total tokens
        assert "operations=1" in repr_str


class TestContextWindowExhausted:
    """Test suite for ContextWindowExhausted exception"""

    def test_exception_creation(self):
        """Test creating exception"""
        exc = ContextWindowExhausted(
            agent_id="test_agent",
            total_tokens=185000,
            usage_percentage=92.5
        )

        assert exc.agent_id == "test_agent"
        assert exc.total_tokens == 185000
        assert exc.usage_percentage == 92.5
        assert "test_agent" in str(exc)
        assert "185,000" in str(exc)
        assert "92.5%" in str(exc)

    def test_exception_custom_message(self):
        """Test exception with custom message"""
        exc = ContextWindowExhausted(
            agent_id="test_agent",
            total_tokens=185000,
            usage_percentage=92.5,
            message="Custom error message"
        )

        assert str(exc) == "Custom error message"

    def test_exception_to_dict(self):
        """Test exception export to dict"""
        exc = ContextWindowExhausted(
            agent_id="test_agent",
            total_tokens=185000,
            usage_percentage=92.5
        )

        exc_dict = exc.to_dict()

        assert exc_dict["error_type"] == "ContextWindowExhausted"
        assert exc_dict["agent_id"] == "test_agent"
        assert exc_dict["total_tokens"] == 185000
        assert exc_dict["usage_percentage"] == 92.5
        assert "message" in exc_dict


class TestRealWorldScenarios:
    """Test real-world usage scenarios"""

    def test_full_webapp_build_scenario(self):
        """Simulate a full webapp build with multiple operations"""
        tracker = AgentTokenTracker("frontend_agent")

        # Scenario: Frontend agent building a complex webapp

        # 1. Initial research phase
        tracker.record_usage("research_requirements", MockUsage(12000, 3000))
        tracker.record_usage("analyze_design_spec", MockUsage(8000, 2000))

        assert tracker.usage_percentage < 15  # Still OK

        # 2. Implementation phase (heavy token usage)
        for i in range(10):
            tracker.record_usage(
                f"implement_component_{i}",
                MockUsage(input_tokens=15000, output_tokens=5000)
            )

        # Should be at warning level
        assert tracker.warning_triggered
        assert not tracker.critical_triggered

        # 3. Final components push to critical
        for i in range(3):
            tracker.record_usage(
                f"final_component_{i}",
                MockUsage(input_tokens=10000, output_tokens=3000)
            )

        # Should now be critical
        assert tracker.critical_triggered
        assert tracker.should_handoff()

    def test_long_running_task_with_small_operations(self):
        """Test scenario with many small operations"""
        tracker = AgentTokenTracker("backend_agent")

        # Simulate 100 small API design iterations
        for i in range(100):
            tracker.record_usage(
                f"api_iteration_{i}",
                MockUsage(input_tokens=1800, output_tokens=600)
            )

        # Total: 240,000 tokens (exceeds limit!)
        assert tracker.total_tokens == 240_000
        assert tracker.should_handoff()
        assert tracker.usage_percentage == 120.0  # Over 100%!

    def test_cached_operations_savings(self):
        """Test scenario with prompt caching"""
        tracker = AgentTokenTracker("designer_agent")

        # First call: no cache
        tracker.record_usage(
            "design_iteration_1",
            MockUsage(
                input_tokens=10000,
                output_tokens=3000,
                cache_creation_input_tokens=2000
            )
        )

        # Subsequent calls: use cache
        for i in range(5):
            tracker.record_usage(
                f"design_iteration_{i+2}",
                MockUsage(
                    input_tokens=10000,
                    output_tokens=3000,
                    cache_read_input_tokens=2000  # Cache hit!
                )
            )

        # Total cached tokens should reflect cache creation
        assert tracker.total_cached_tokens == 2000

        # Total input/output should still count all operations
        assert tracker.total_input_tokens == 60_000
        assert tracker.total_output_tokens == 18_000
