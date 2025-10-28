# Agent Lifecycle Manager - Orchestrator Integration Guide

## Overview

This guide documents the integration of `AgentLifecycleManager` into the `CollaborativeOrchestrator` to enable automatic context window management and agent handoffs.

## Integration Strategy

### Phase 1: Add Lifecycle Manager (Non-Breaking)

Add lifecycle manager as an optional layer that wraps existing agent management without breaking current functionality.

#### 1.1 Modify `__init__` to add lifecycle manager

```python
def __init__(self, ...):
    # ... existing initialization ...

    # NEW: Lifecycle Manager (with HandoffManager)
    self.lifecycle_manager = None  # Lazy initialization
    self._lifecycle_enabled = os.getenv('ENABLE_LIFECYCLE_MANAGEMENT', 'true').lower() == 'true'
    self._handoff_manager = None  # Will be initialized async

    print(f"   - Lifecycle Management: {'Enabled' if self._lifecycle_enabled else 'Disabled'}")
```

#### 1.2 Add async initialization method

```python
async def _ensure_lifecycle_manager(self):
    """Initialize lifecycle manager on first use (async lazy initialization)"""
    if self.lifecycle_manager is not None:
        return

    if not self._lifecycle_enabled:
        return

    from database.config import get_handoff_manager
    from agents.collaborative.lifecycle_manager import AgentLifecycleManager

    # Create handoff manager with database session
    # Note: This creates a manager but doesn't start a session yet
    # Sessions will be created per-handoff operation

    # For now, we'll create lifecycle manager without handoff persistence
    # Full integration will require async context management
    print("🔄 Initializing Lifecycle Manager...")

    # TODO: Implement proper async handoff manager integration
    # For now, create lifecycle manager without persistence
    self.lifecycle_manager = AgentLifecycleManager(
        handoff_manager=None,  # Will be added in Phase 2
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
```

### Phase 2: Wrap Agent Operations

Modify `_get_agent()` to integrate with lifecycle manager without breaking existing code.

#### 2.1 Enhanced `_get_agent()` with lifecycle tracking

```python
async def _get_agent(self, agent_type: str):
    """
    Get or create an agent on-demand with lifecycle management
    """
    # Ensure lifecycle manager is initialized
    await self._ensure_lifecycle_manager()

    # Check if agent is already active
    if agent_type in self._active_agents:
        return self._active_agents[agent_type]

    # Check cache if enabled
    if self.enable_agent_caching and agent_type in self._agent_cache:
        agent = self._agent_cache[agent_type]
        self._active_agents[agent_type] = agent
        print(f"♻️  Reusing cached {agent_type} agent")
        return agent

    # Create new agent instance (existing code)
    print(f"🚀 Spinning up {agent_type} agent...")

    if agent_type == "designer":
        agent = DesignerAgent(self.mcp_servers)
    elif agent_type == "backend":
        if PROJECT_MANAGER_AVAILABLE:
            agent = BackendAgent(self.mcp_servers, project_manager=project_manager)
        else:
            raise ValueError("Backend agent requires project_manager")
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

    # NEW: Register with lifecycle manager
    if self.lifecycle_manager:
        lifecycle_instance = self.lifecycle_manager.spawn_agent(
            agent_type=agent_type,
            agent_role=agent.agent_card.role.value,
            agent_object=agent,
            user_id=self.user_id,
            project_id=self.project_id or "default",
            trace_id=None,  # Will be set per workflow
            task_id=None
        )

        # Attach lifecycle instance to agent for tracking
        agent._lifecycle_instance = lifecycle_instance

        # Wrap agent's SDK with token tracking
        if hasattr(agent, 'sdk') and agent.sdk:
            # Add token tracker to SDK
            agent.sdk.token_tracker = lifecycle_instance.token_tracker
            agent.sdk.agent_id = lifecycle_instance.agent_id

    # Cache if enabled
    if self.enable_agent_caching:
        self._agent_cache[agent_type] = agent

    print(f"✅ {agent_type} agent ready ({agent.agent_card.agent_id})")
    return agent
```

### Phase 3: Add Handoff Error Handling

Wrap all agent operations with context window error handling.

#### 3.1 Add handoff wrapper method

```python
async def _execute_agent_task_with_handoff_protection(
    self,
    agent_type: str,
    task_func,
    *args,
    **kwargs
):
    """
    Execute agent task with automatic handoff on context window exhaustion

    Args:
        agent_type: Type of agent
        task_func: Async function to execute
        *args, **kwargs: Arguments to pass to task_func

    Returns:
        Task result
    """
    from agents.collaborative.token_tracker import ContextWindowExhausted
    from agents.collaborative.lifecycle_states import AgentTerminationReason

    max_handoffs = 5  # Prevent infinite handoff loops
    handoff_count = 0
    predecessor_handoff_id = None

    while handoff_count < max_handoffs:
        try:
            # Execute the task
            result = await task_func(*args, **kwargs)
            return result

        except ContextWindowExhausted as e:
            print(f"🚨 Context window exhausted for {agent_type}")
            print(f"   Tokens: {e.total_tokens:,} ({e.usage_percentage:.1f}%)")

            # Get current agent
            agent = self._active_agents.get(agent_type)
            if not agent or not hasattr(agent, '_lifecycle_instance'):
                # Lifecycle not enabled or agent not tracked
                raise

            lifecycle_instance = agent._lifecycle_instance

            # Notify user
            await self._send_notification(
                f"⚠️ {self._get_agent_type_name(lifecycle_instance.agent_id)} reached context limit\n"
                f"📊 Used {e.total_tokens:,} tokens ({e.usage_percentage:.1f}%)\n"
                f"🔄 Creating handoff and spawning fresh agent..."
            )

            # Create handoff document
            handoff = await self.lifecycle_manager.create_handoff(
                agent_id=lifecycle_instance.agent_id,
                termination_reason=AgentTerminationReason.CONTEXT_WINDOW_EXHAUSTED,
                platform=self.platform,
                workflow_type=self.current_workflow or "unknown",
                original_request=self.original_prompt or "Unknown request",
                task_description=self.current_task_description or "Unknown task",
                current_phase=self.current_phase or "unknown",
                completion_percentage=self._calculate_completion_percentage(),
                task_status="in_progress",
                predecessor_handoff_id=predecessor_handoff_id,
                # TODO: Add more handoff fields (decisions, work_completed, todo_list, etc.)
            )

            # Save handoff ID for next iteration
            predecessor_handoff_id = handoff.handoff_id

            # Terminate old agent
            await self.lifecycle_manager.terminate_agent(
                lifecycle_instance.agent_id,
                AgentTerminationReason.CONTEXT_WINDOW_EXHAUSTED
            )

            # Clean up old agent from orchestrator
            await self._cleanup_agent(agent_type)

            # Spawn new agent with handoff context
            new_agent = await self._get_agent(agent_type)

            # Inject handoff continuation prompt into new agent
            if hasattr(new_agent, 'sdk') and new_agent.sdk:
                continuation_prompt = handoff.get_continuation_prompt()
                # Prepend to system prompt
                if hasattr(new_agent.sdk, 'system_prompt'):
                    new_agent.sdk.system_prompt = (
                        continuation_prompt + "\n\n" +
                        (new_agent.sdk.system_prompt or "")
                    )

            # Notify user
            await self._send_notification(
                f"✅ New {self._get_agent_type_name(new_agent.agent_card.agent_id)} spawned\n"
                f"📦 Handoff ID: {handoff.handoff_id}\n"
                f"🔄 Continuing from {handoff.task_progress.overall_completion_percentage}% completion..."
            )

            # Increment handoff count
            handoff_count += 1

            # Continue loop to retry with new agent
            continue

    # If we get here, we've exceeded max handoffs
    raise RuntimeError(f"Exceeded maximum handoffs ({max_handoffs}) for {agent_type}")
```

### Phase 4: Add Lifecycle Callbacks

Implement callback methods for lifecycle events.

```python
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
```

### Phase 5: Helper Methods

```python
def _calculate_completion_percentage(self) -> int:
    """Calculate current workflow completion percentage"""
    if self.workflow_steps_total == 0:
        return 0

    completed = len(self.workflow_steps_completed)
    total = self.workflow_steps_total

    return min(100, int((completed / total) * 100))
```

## Implementation Steps

1. **Step 1**: Add lifecycle manager initialization to `__init__` ✅
2. **Step 2**: Add lifecycle manager lazy initialization method
3. **Step 3**: Modify `_get_agent()` to register agents with lifecycle manager
4. **Step 4**: Add handoff wrapper for agent operations
5. **Step 5**: Add lifecycle event callbacks
6. **Step 6**: Wrap critical agent operations (design, implement, review, deploy)
7. **Step 7**: Test with simulated context window exhaustion
8. **Step 8**: Test end-to-end with real database

## Testing Strategy

### Unit Tests

- Test lifecycle manager initialization
- Test agent spawning with token tracking
- Test handoff creation and persistence
- Test agent termination and cleanup

### Integration Tests

- Test full workflow with handoff triggered at 90%
- Test handoff chain (multiple handoffs in sequence)
- Test continuation from handoff document
- Test database persistence and retrieval

### End-to-End Tests

- Test with real Neon PostgreSQL database
- Test with real WhatsApp conversations
- Test with actual token consumption approaching 200K limit
- Test memory efficiency (verify handoffs saved to DB, not in-memory)

## Rollout Strategy

### Phase 1: Non-Breaking Addition (Week 1)
- Add lifecycle manager code without modifying existing flows
- Feature flag controlled (`ENABLE_LIFECYCLE_MANAGEMENT=false`)
- Monitor for any integration issues

### Phase 2: Gradual Enablement (Week 2)
- Enable lifecycle management in development
- Test with synthetic workloads
- Verify handoff documents are created correctly

### Phase 3: Production Testing (Week 3)
- Enable for select users (beta testing)
- Monitor telemetry for handoff events
- Verify memory savings from database storage

### Phase 4: Full Rollout (Week 4)
- Enable for all users
- Monitor for any issues
- Collect metrics on handoff frequency and effectiveness

## Success Metrics

- **Context Window Utilization**: Average % at handoff (target: ~90%)
- **Handoff Success Rate**: % of handoffs that successfully continue work (target: >95%)
- **Memory Efficiency**: Memory usage before/after database storage (target: <50% reduction)
- **Agent Continuity**: Task completion rate with handoffs (target: same as without)
- **Token Efficiency**: Total tokens used for same task with vs without handoffs (target: within 10%)

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Handoff overhead | High | Optimize handoff document size, use JSONB compression |
| Database latency | Medium | Use connection pooling, async operations |
| Handoff data loss | High | Database backups, transaction safety |
| Infinite handoff loops | High | Max handoff limit (5), circuit breaker |
| Prompt injection via handoff | High | Sanitize handoff content, validate schema |

## Database Schema Migration

The `AgentHandoff` table has been added to `models.py`. To create it in the database:

```python
from database.config import init_db
await init_db()  # Creates all tables including agent_handoff
```

## Environment Variables

```bash
# Enable/disable lifecycle management
ENABLE_LIFECYCLE_MANAGEMENT=true

# Database connection (already configured)
DATABASE_URL=postgresql://...

# Optional: Markdown file generation
ENABLE_HANDOFF_MARKDOWN=false
HANDOFF_MARKDOWN_PATH=/path/to/handoffs
```

## Monitoring and Observability

### Telemetry Events

- `agent_spawned` - New agent instance created
- `agent_warning` - Agent reached 75% token usage
- `agent_critical` - Agent reached 90% token usage
- `agent_handoff` - Handoff document created
- `agent_terminated` - Agent instance terminated

### Metrics

- `agent_token_usage` - Current token usage per agent
- `handoff_count` - Total handoffs created
- `handoff_chain_length` - Number of handoffs in a chain
- `agent_lifecycle_duration` - Time from spawn to termination
