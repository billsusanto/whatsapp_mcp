# Logfire Nested Spans Design - Multi-Agent System

## Overview

This document defines the comprehensive nested span hierarchy for tracking all agent activities in Logfire. Every operation from user request to final deployment will be visible with proper parent-child relationships.

## Span Hierarchy Structure

```
Level 1: User Request (Root)
│
├─ Level 2: Workflow Execution
│  │
│  ├─ Level 3: Agent Lifecycle
│  │  │
│  │  ├─ Level 4: Agent Spawn
│  │  │  └─ Level 5: Token Tracker Init
│  │  │
│  │  ├─ Level 4: Agent Task Execution
│  │  │  │
│  │  │  ├─ Level 5: Task Received (A2A)
│  │  │  │
│  │  │  ├─ Level 5: Claude API Call
│  │  │  │  ├─ Level 6: Token Usage Recorded
│  │  │  │  └─ Level 6: Threshold Check
│  │  │  │
│  │  │  ├─ Level 5: Tool Execution (MCP)
│  │  │  │  ├─ Level 6: GitHub API Call
│  │  │  │  ├─ Level 6: Netlify API Call
│  │  │  │  └─ Level 6: File System Operation
│  │  │  │
│  │  │  ├─ Level 5: A2A Communication
│  │  │  │  └─ Level 6: Message Sent
│  │  │  │
│  │  │  └─ Level 5: Task Response Generated
│  │  │
│  │  ├─ Level 4: Agent Warning/Critical State
│  │  │  └─ Level 5: User Notification Sent
│  │  │
│  │  ├─ Level 4: Agent Handoff
│  │  │  ├─ Level 5: Handoff Document Created
│  │  │  ├─ Level 5: Database Save
│  │  │  ├─ Level 5: Agent Terminated
│  │  │  └─ Level 5: New Agent Spawned
│  │  │     └─ Level 6: Continuation Prompt Injected
│  │  │
│  │  └─ Level 4: Agent Cleanup
│  │
│  ├─ Level 3: Phase Transition
│  │  └─ Level 4: State Persistence
│  │
│  └─ Level 3: Workflow Completion
│
└─ Level 2: Response Sent to User
```

## Detailed Span Definitions

### Level 1: User Request (Root Span)

**Span Name**: `user_request`

**Attributes**:
- `user_id`: Hashed WhatsApp number or GitHub repo
- `platform`: "whatsapp" or "github"
- `request_type`: "build", "fix", "status", "refine"
- `request_length`: Character count of user message
- `timestamp`: ISO 8601 timestamp
- `trace_id`: Unique trace identifier

**Duration**: From request received to final response sent

**Example**:
```python
with logfire.span(
    'user_request',
    user_id=user_hash,
    platform='whatsapp',
    request_type='build',
    request_length=len(user_prompt),
    request_preview=user_prompt[:100]
):
    # All workflow operations
    ...
```

---

### Level 2: Workflow Execution

**Span Name**: `workflow:{workflow_type}`

**Types**:
- `workflow:full_build`
- `workflow:bug_fix`
- `workflow:design_only`
- `workflow:redeploy`
- `workflow:custom`

**Attributes**:
- `workflow_type`: Type of workflow
- `ai_reasoning`: Why this workflow was chosen
- `agents_needed`: List of agent types required
- `estimated_complexity`: "low", "medium", "high"
- `estimated_steps`: Total workflow steps
- `user_prompt`: Truncated user request (100 chars)

**Example**:
```python
with logfire.span(
    f'workflow:{workflow_type}',
    workflow_type='full_build',
    ai_reasoning=plan.get('reasoning'),
    agents_needed=['designer', 'frontend', 'devops'],
    estimated_complexity='medium',
    estimated_steps=15
):
    # Workflow phases
    ...
```

---

### Level 3: Agent Lifecycle

**Span Name**: `agent_lifecycle:{agent_type}`

**Agent Types**:
- `designer`
- `backend`
- `frontend`
- `code_reviewer`
- `qa`
- `devops`

**Attributes**:
- `agent_id`: Unique agent identifier (e.g., "frontend_v1_abc123")
- `agent_type`: Type of agent
- `agent_version`: Instance version number
- `lifecycle_state`: Current state (ACTIVE, WARNING, CRITICAL, etc.)
- `spawn_timestamp`: When agent was spawned
- `user_id`: User this agent is working for
- `project_id`: Project identifier

**Example**:
```python
with logfire.span(
    f'agent_lifecycle:{agent_type}',
    agent_id=agent_instance.agent_id,
    agent_type='frontend',
    agent_version=1,
    lifecycle_state='ACTIVE',
    user_id=user_id,
    project_id=project_id
):
    # All agent operations from spawn to terminate
    ...
```

---

### Level 4: Agent Spawn

**Span Name**: `agent_spawn`

**Attributes**:
- `agent_id`: New agent identifier
- `agent_type`: Type being spawned
- `version`: Version number
- `handoff_id`: If continuing from handoff (optional)
- `predecessor_agent_id`: Previous agent ID (if handoff)
- `continuation_mode`: "fresh" or "handoff"

**Example**:
```python
with logfire.span(
    'agent_spawn',
    agent_id=agent_id,
    agent_type='frontend',
    version=1,
    continuation_mode='fresh'
):
    # Token tracker initialization
    # Agent registration
    ...
```

---

### Level 4: Agent Task Execution

**Span Name**: `agent_task:{task_type}`

**Task Types**:
- `design_creation`
- `implementation`
- `code_review`
- `quality_assurance`
- `deployment`
- `bug_fix`

**Attributes**:
- `agent_id`: Agent executing the task
- `task_id`: Unique task identifier
- `task_description`: What the task is
- `task_source`: "orchestrator" or "a2a:{from_agent}"
- `priority`: Task priority
- `estimated_duration`: Expected time

**Example**:
```python
with logfire.span(
    f'agent_task:{task_type}',
    agent_id=agent_instance.agent_id,
    task_id=task.task_id,
    task_description=task.description,
    task_source='orchestrator',
    priority='high'
):
    # Claude API calls
    # Tool executions
    # A2A communications
    ...
```

---

### Level 5: Claude API Call

**Span Name**: `claude_api_call` (Auto-instrumented)

**Note**: This is automatically instrumented by `logfire.instrument_anthropic()`

**Attributes** (Auto-captured):
- `model`: "claude-sonnet-4-5"
- `input_tokens`: Tokens in request
- `output_tokens`: Tokens in response
- `cache_read_tokens`: Cached tokens
- `total_tokens`: Total consumed
- `duration_ms`: API call duration
- `prompt_preview`: First 100 chars of prompt
- `response_preview`: First 100 chars of response

**Additional Attributes** (We'll add):
- `agent_id`: Which agent made the call
- `operation`: "design", "implement", "review", etc.
- `cumulative_tokens`: Total tokens for agent so far

**Example** (we'll wrap it):
```python
with logfire.span(
    'claude_api_call',
    agent_id=agent_id,
    operation='implementation',
    cumulative_tokens=token_tracker.total_tokens
):
    # Anthropic client call (auto-instrumented)
    response = await client.messages.create(...)
```

---

### Level 5: Token Usage Recorded

**Span Name**: `token_usage_recorded`

**Attributes**:
- `agent_id`: Agent identifier
- `operation`: Operation name
- `input_tokens`: Input tokens
- `output_tokens`: Output tokens
- `cumulative_total`: Running total
- `usage_percentage`: Percentage of context window
- `threshold_status`: "OK", "WARNING", or "CRITICAL"
- `tokens_until_warning`: Tokens remaining until 75%
- `tokens_until_critical`: Tokens remaining until 90%

**Example**:
```python
with logfire.span(
    'token_usage_recorded',
    agent_id=agent_id,
    operation='implement_component',
    input_tokens=1500,
    output_tokens=800,
    cumulative_total=45000,
    usage_percentage=22.5,
    threshold_status='OK'
):
    # Record to tracker
    status = tracker.record_usage(...)
```

---

### Level 5: A2A Communication

**Span Name**: `a2a_communication`

**Attributes**:
- `from_agent_id`: Sending agent
- `to_agent_id`: Receiving agent
- `message_type`: "task", "query", "response", "handoff"
- `task_description`: What's being communicated
- `protocol_version`: A2A protocol version
- `priority`: Message priority

**Example**:
```python
with logfire.span(
    'a2a_communication',
    from_agent_id='orchestrator',
    to_agent_id='frontend_v1_abc123',
    message_type='task',
    task_description='Implement React components',
    priority='high'
):
    # Send message via A2A protocol
    response = await a2a_protocol.send_task(...)
```

---

### Level 5: Tool Execution (MCP)

**Span Name**: `mcp_tool:{tool_name}`

**Tool Types**:
- `github_create_repo`
- `github_commit`
- `netlify_deploy`
- `file_write`
- `file_read`
- `neon_create_database`

**Attributes**:
- `agent_id`: Agent using the tool
- `tool_name`: MCP tool name
- `server`: MCP server name ("github", "netlify", "neon")
- `parameters`: Tool parameters (sanitized)
- `result_status`: "success" or "failed"

**Example**:
```python
with logfire.span(
    f'mcp_tool:{tool_name}',
    agent_id=agent_id,
    tool_name='github_create_repo',
    server='github',
    repo_name=repo_name
):
    # MCP tool call
    result = await mcp_client.call_tool(...)
```

---

### Level 4: Agent Warning/Critical State

**Span Name**: `agent_threshold:{threshold_type}`

**Types**:
- `agent_threshold:warning` (75%)
- `agent_threshold:critical` (90%)

**Attributes**:
- `agent_id`: Agent identifier
- `threshold_type`: "warning" or "critical"
- `token_usage`: Current token count
- `usage_percentage`: Percentage used
- `tokens_remaining`: Tokens left
- `action_taken`: "notification_sent" or "handoff_triggered"

**Example**:
```python
with logfire.span(
    f'agent_threshold:{threshold_type}',
    agent_id=agent_id,
    threshold_type='warning',
    token_usage=150000,
    usage_percentage=75.0,
    tokens_remaining=50000,
    action_taken='notification_sent'
):
    # Send user notification
    await send_notification(...)
```

---

### Level 4: Agent Handoff

**Span Name**: `agent_handoff`

**Attributes**:
- `source_agent_id`: Agent being terminated
- `target_agent_id`: New agent being spawned
- `handoff_id`: Unique handoff identifier
- `trace_id`: Trace linking handoffs
- `termination_reason`: Why handoff occurred
- `completion_percentage`: Task completion at handoff
- `tokens_used`: Total tokens consumed
- `handoff_size_kb`: Size of handoff document
- `database_save_duration_ms`: Time to save to DB

**Example**:
```python
with logfire.span(
    'agent_handoff',
    source_agent_id=old_agent_id,
    target_agent_id=new_agent_id,
    handoff_id=handoff.handoff_id,
    trace_id=handoff.trace_id,
    termination_reason='context_window_exhausted',
    completion_percentage=65,
    tokens_used=180000
):
    # Create handoff document
    # Save to database
    # Terminate old agent
    # Spawn new agent
    ...
```

---

### Level 5: Handoff Document Created

**Span Name**: `handoff_document_created`

**Attributes**:
- `handoff_id`: Document identifier
- `document_size_kb`: Size in kilobytes
- `categories_included`: Number of filled categories (out of 17)
- `decisions_count`: Number of decisions captured
- `todos_count`: Number of TODO items
- `errors_count`: Number of errors recorded
- `work_items_count`: Number of work items completed

**Example**:
```python
with logfire.span(
    'handoff_document_created',
    handoff_id=handoff.handoff_id,
    document_size_kb=round(len(handoff.model_dump_json()) / 1024, 2),
    categories_included=17,
    decisions_count=len(handoff.decisions_made),
    todos_count=len(handoff.todo_list)
):
    # Create HandoffDocument Pydantic model
    handoff = HandoffDocument(...)
```

---

### Level 5: Database Save

**Span Name**: `database_save:{table_name}`

**Tables**:
- `agent_handoff`
- `orchestrator_state`
- `project_metadata`

**Attributes**:
- `table_name`: Database table
- `operation`: "insert", "update", "delete"
- `record_id`: Primary key of record
- `data_size_kb`: Size of data being saved
- `duration_ms`: Query duration
- `connection_pool_size`: Current pool size

**Example**:
```python
with logfire.span(
    f'database_save:{table_name}',
    table_name='agent_handoff',
    operation='insert',
    data_size_kb=5.2,
    handoff_id=handoff.handoff_id
):
    # Save to PostgreSQL
    await db.execute(insert_stmt)
    await db.commit()
```

---

### Level 3: Phase Transition

**Span Name**: `phase_transition`

**Phases**:
- `planning` → `design`
- `design` → `implementation`
- `implementation` → `review`
- `review` → `deployment`
- `deployment` → `completed`

**Attributes**:
- `from_phase`: Previous phase
- `to_phase`: New phase
- `reason`: Why transition occurred
- `phase_duration_seconds`: How long in previous phase
- `completion_percentage`: Overall workflow completion

**Example**:
```python
with logfire.span(
    'phase_transition',
    from_phase='design',
    to_phase='implementation',
    reason='design_approved',
    phase_duration_seconds=45.2,
    completion_percentage=30
):
    # Update orchestrator state
    self.current_phase = 'implementation'
    await self._save_state()
```

---

## Complete Example Flow

Here's what a complete trace looks like for a full build workflow:

```
┌─ user_request (user_hash=abc123, platform=whatsapp) [2m 35s]
│
├─ workflow:full_build (agents=['designer','frontend','devops']) [2m 30s]
│  │
│  ├─ phase_transition (design → implementation) [0.5s]
│  │
│  ├─ agent_lifecycle:frontend (agent_id=frontend_v1_xyz) [1m 45s]
│  │  │
│  │  ├─ agent_spawn (version=1, continuation_mode=fresh) [0.2s]
│  │  │  └─ token_tracker_init (context_limit=200000) [0.01s]
│  │  │
│  │  ├─ agent_task:implementation (task=React components) [1m 40s]
│  │  │  │
│  │  │  ├─ claude_api_call (operation=plan_components) [3.2s]
│  │  │  │  ├─ token_usage_recorded (input=1500, output=800) [0.01s]
│  │  │  │  └─ threshold_check (status=OK, usage=1.1%) [0.001s]
│  │  │  │
│  │  │  ├─ mcp_tool:file_write (file=App.tsx) [0.5s]
│  │  │  │
│  │  │  ├─ claude_api_call (operation=implement_component) [4.5s]
│  │  │  │  ├─ token_usage_recorded (input=2500, output=1800) [0.01s]
│  │  │  │  └─ threshold_check (status=OK, usage=3.2%) [0.001s]
│  │  │  │
│  │  │  ├─ a2a_communication (to=code_reviewer) [0.1s]
│  │  │  │  └─ message_sent (task=review_code) [0.05s]
│  │  │  │
│  │  │  └─ task_response_generated (status=success) [0.01s]
│  │  │
│  │  └─ agent_cleanup (resources_freed=True) [0.05s]
│  │
│  ├─ agent_lifecycle:devops (agent_id=devops_v1_abc) [45s]
│  │  │
│  │  ├─ agent_spawn (version=1) [0.2s]
│  │  │
│  │  ├─ agent_task:deployment (task=Deploy to Netlify) [40s]
│  │  │  │
│  │  │  ├─ mcp_tool:netlify_deploy (site=my-app) [35s]
│  │  │  │  ├─ http_request (POST /v1/sites) [2s]
│  │  │  │  └─ build_logs_streamed (lines=150) [30s]
│  │  │  │
│  │  │  └─ task_response_generated (deployment_url=...) [0.5s]
│  │  │
│  │  └─ agent_cleanup [0.05s]
│  │
│  └─ workflow_completion (status=success, url=https://...) [0.1s]
│
└─ response_sent_to_user (platform=whatsapp) [0.5s]
```

## Implementation Guidelines

### 1. Context Propagation

All spans must properly propagate context. Use nested `with` statements:

```python
# Parent span
with logfire.span('user_request', user_id=user_hash):

    # Child span
    with logfire.span('workflow:full_build', workflow_type='full_build'):

        # Grandchild span
        with logfire.span('agent_lifecycle:frontend', agent_id=agent_id):

            # Great-grandchild span
            with logfire.span('agent_task:implementation'):
                # Work happens here
                pass
```

### 2. Async Context Managers

For async code, use the same pattern:

```python
async def some_async_operation():
    with logfire.span('operation_name', **attributes):
        # Async work
        result = await async_call()
        return result
```

### 3. Exception Handling

Logfire automatically captures exceptions in spans:

```python
with logfire.span('risky_operation') as span:
    try:
        result = do_something()
        span.set_attribute('result', result)
    except Exception as e:
        span.set_attribute('error_type', type(e).__name__)
        # Exception is auto-captured
        raise
```

### 4. Dynamic Attributes

Add attributes after span creation:

```python
with logfire.span('agent_task') as span:
    result = await execute_task()

    # Add result attributes
    span.set_attribute('task_result', result.status)
    span.set_attribute('output_lines', len(result.output))
```

### 5. Performance Considerations

- Keep attribute values small (< 1KB each)
- Don't log sensitive data (API keys, passwords, full user messages)
- Use truncation for long strings: `user_prompt[:100]`
- Hash personally identifiable information: `hashlib.sha256(phone.encode()).hexdigest()[:16]`

## Instrumentation Locations

### Files to Instrument

1. **orchestrator.py**
   - `build_webapp()` → user_request span
   - `_workflow_full_build()` → workflow span
   - `_get_agent()` → agent_spawn span
   - `_cleanup_agent()` → agent_cleanup span
   - Phase transitions → phase_transition span

2. **lifecycle_manager.py**
   - `spawn_agent()` → agent_spawn span
   - `record_usage()` → token_usage_recorded span
   - `create_handoff()` → agent_handoff span
   - `terminate_agent()` → agent_cleanup span

3. **handoff_manager.py**
   - `create_handoff()` → handoff_document_created span
   - `save_handoff()` → database_save span
   - `load_handoff()` → database_load span

4. **base_agent.py** (or individual agent files)
   - `execute_task()` → agent_task span
   - `send_message()` → claude_api_call wrapper
   - Tool calls → mcp_tool span

5. **a2a_protocol.py**
   - `send_task()` → a2a_communication span
   - `receive_message()` → message processing span

6. **claude_sdk.py**
   - `send_message()` → claude_api_call wrapper
   - Token tracking → token_usage_recorded span

## Dashboard Views

With this instrumentation, you'll be able to create Logfire dashboards showing:

1. **User Request Timeline**
   - See entire request flow from start to finish
   - Identify slowest phases and agents

2. **Agent Performance**
   - Compare agent execution times
   - Track token usage patterns
   - Monitor handoff frequency

3. **Token Consumption**
   - Real-time token usage by agent
   - Warning/critical events
   - Average tokens per task type

4. **Handoff Analytics**
   - Handoff frequency by agent type
   - Completion percentage at handoff
   - Handoff success rate

5. **Error Tracking**
   - Errors by agent type
   - Failed tasks and reasons
   - Exception stack traces

6. **A2A Communication Flow**
   - Message flow between agents
   - Communication bottlenecks
   - Task handoff patterns

## Privacy & Security

### Data to Hash/Truncate

- **Phone numbers**: Hash with SHA-256
- **User messages**: Truncate to 100 characters
- **API tokens**: Never log
- **Passwords**: Never log
- **Repository contents**: Truncate or exclude

### Safe Attributes

✅ Safe to log:
- Agent IDs
- Task types
- Token counts
- Durations
- Status codes
- Workflow types

❌ Never log:
- Full user messages
- API credentials
- Personal information
- Private repository content

## Next Steps

1. ✅ Design span hierarchy (this document)
2. ⏳ Update `telemetry.py` with agent-specific helpers
3. ⏳ Instrument orchestrator.py
4. ⏳ Instrument lifecycle_manager.py
5. ⏳ Instrument handoff_manager.py
6. ⏳ Instrument base agents
7. ⏳ Test end-to-end tracing
8. ⏳ Create Logfire dashboards
