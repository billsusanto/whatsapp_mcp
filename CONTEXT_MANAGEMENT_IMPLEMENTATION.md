# Context Window Management - Implementation Plan

**Date:** 2025-10-27
**Status:** Implementation Design Phase
**Related:** CONTEXT_WINDOW_MANAGEMENT_PLAN.md

---

## Table of Contents

1. [Agent Lifecycle Management](#1-agent-lifecycle-management)
2. [State Transfer Mechanism](#2-state-transfer-mechanism)
3. [Orchestrator Monitoring](#3-orchestrator-monitoring)
4. [File Structure](#4-file-structure)
5. [Implementation Phases](#5-implementation-phases)
6. [Testing Strategy](#6-testing-strategy)

---

## 1. Agent Lifecycle Management

### 1.1 Agent States

```python
from enum import Enum

class AgentLifecycleState(Enum):
    """Agent instance lifecycle states"""
    INITIALIZING = "initializing"      # Agent being created
    ACTIVE = "active"                  # Agent processing tasks
    WARNING = "warning"                # Token usage > 75%
    CRITICAL = "critical"              # Token usage > 90%
    HANDOFF_PENDING = "handoff_pending"  # Creating handoff document
    HANDOFF_COMPLETE = "handoff_complete"  # Handoff doc written
    TERMINATED = "terminated"          # Agent instance killed
```

### 1.2 Agent Lifecycle Manager

**Location:** `src/python/agents/collaborative/agent_lifecycle_manager.py`

```python
"""
Agent Lifecycle Manager

Manages the complete lifecycle of agent instances including:
- Spawning new agents
- Monitoring token usage
- Triggering handoffs
- Terminating agents
- Maintaining agent registry
"""

from typing import Dict, Optional, Any, Type
from datetime import datetime
import asyncio
from pathlib import Path

from .base_agent import BaseAgent
from .models import AgentCard, AgentRole
from .token_tracker import AgentTokenTracker
from .handoff_manager import HandoffManager, HandoffDocument
from utils.telemetry import trace_operation, log_event, log_metric


class AgentInstance:
    """Represents a single agent instance with metadata"""

    def __init__(
        self,
        agent: BaseAgent,
        instance_id: str,
        version: int,
        spawn_time: datetime
    ):
        self.agent = agent
        self.instance_id = instance_id
        self.version = version
        self.spawn_time = spawn_time
        self.lifecycle_state = AgentLifecycleState.INITIALIZING
        self.token_tracker = AgentTokenTracker(
            agent_id=instance_id,
            context_window_limit=200_000
        )
        self.last_health_check = datetime.utcnow()
        self.handoff_document: Optional[HandoffDocument] = None

    @property
    def agent_type(self) -> str:
        """Get the type of agent (frontend, backend, etc.)"""
        return self.agent.agent_card.role.value

    @property
    def uptime_seconds(self) -> float:
        """How long has this instance been running"""
        return (datetime.utcnow() - self.spawn_time).total_seconds()

    def should_handoff(self) -> bool:
        """Determine if agent should perform handoff"""
        return self.token_tracker.should_handoff()


class AgentLifecycleManager:
    """
    Manages agent lifecycles with context window management.

    Responsibilities:
    - Spawn new agent instances
    - Monitor token usage
    - Trigger handoffs when approaching context limit
    - Kill and respawn agents
    - Maintain agent registry
    """

    def __init__(
        self,
        handoff_directory: Path,
        project_id: str,
        orchestrator_callback: Optional[callable] = None
    ):
        """
        Initialize lifecycle manager.

        Args:
            handoff_directory: Base directory for handoff documents
            project_id: Current project ID
            orchestrator_callback: Callback to notify orchestrator of events
        """
        self.handoff_directory = handoff_directory
        self.project_id = project_id
        self.orchestrator_callback = orchestrator_callback

        # Agent registry: {agent_type: AgentInstance}
        self.active_agents: Dict[str, AgentInstance] = {}

        # Agent class registry for spawning
        self.agent_classes: Dict[str, Type[BaseAgent]] = {}

        # Handoff manager
        self.handoff_manager = HandoffManager(handoff_directory)

        # Monitoring
        self.monitoring_task: Optional[asyncio.Task] = None
        self.monitoring_interval = 30  # Check every 30 seconds

        print("✅ AgentLifecycleManager initialized")
        print(f"   Project ID: {project_id}")
        print(f"   Handoff Directory: {handoff_directory}")

    def register_agent_class(
        self,
        agent_type: str,
        agent_class: Type[BaseAgent]
    ):
        """
        Register an agent class for spawning.

        Args:
            agent_type: Type identifier (e.g., "frontend_agent")
            agent_class: The class to instantiate
        """
        self.agent_classes[agent_type] = agent_class
        print(f"📝 Registered agent class: {agent_type}")

    async def spawn_agent(
        self,
        agent_type: str,
        mcp_servers: Dict,
        handoff_document: Optional[HandoffDocument] = None,
        version: int = 1
    ) -> AgentInstance:
        """
        Spawn a new agent instance.

        Args:
            agent_type: Type of agent to spawn
            mcp_servers: Available MCP servers
            handoff_document: Optional handoff from previous instance
            version: Instance version number

        Returns:
            AgentInstance object
        """
        with trace_operation(
            "spawn_agent",
            agent_type=agent_type,
            version=version,
            is_handoff=handoff_document is not None
        ):
            # Get agent class
            if agent_type not in self.agent_classes:
                raise ValueError(f"Unknown agent type: {agent_type}")

            agent_class = self.agent_classes[agent_type]

            # Generate instance ID
            instance_id = f"{agent_type}_v{version}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

            # Instantiate agent
            print(f"🚀 Spawning {agent_type} instance: {instance_id}")
            agent = agent_class(mcp_servers=mcp_servers)

            # Create instance wrapper
            instance = AgentInstance(
                agent=agent,
                instance_id=instance_id,
                version=version,
                spawn_time=datetime.utcnow()
            )

            # If resuming from handoff, load state
            if handoff_document:
                await self._load_handoff_state(instance, handoff_document)

            # Register in active agents
            self.active_agents[agent_type] = instance
            instance.lifecycle_state = AgentLifecycleState.ACTIVE

            # Log event
            log_event(
                "agent_spawned",
                agent_type=agent_type,
                instance_id=instance_id,
                version=version,
                is_handoff_continuation=handoff_document is not None
            )

            # Notify orchestrator
            if self.orchestrator_callback:
                await self.orchestrator_callback("agent_spawned", {
                    "agent_type": agent_type,
                    "instance_id": instance_id,
                    "version": version
                })

            print(f"✅ Agent spawned: {instance_id}")
            return instance

    async def _load_handoff_state(
        self,
        instance: AgentInstance,
        handoff_doc: HandoffDocument
    ):
        """
        Load state from handoff document into new agent instance.

        Args:
            instance: New agent instance
            handoff_doc: Handoff document from previous instance
        """
        print(f"📥 Loading handoff state into {instance.instance_id}...")

        # Set initial token count (carry over from previous instance)
        instance.token_tracker.total_input_tokens = handoff_doc.token_usage["total_input_tokens"]
        instance.token_tracker.total_output_tokens = handoff_doc.token_usage["total_output_tokens"]

        # Store handoff document reference
        instance.handoff_document = handoff_doc

        # Inject context into agent's Claude SDK
        # This is done by prepending handoff context to system prompt
        handoff_context = self._build_handoff_context_prompt(handoff_doc)
        instance.agent.claude_sdk.system_prompt = (
            handoff_context + "\n\n" + instance.agent.claude_sdk.system_prompt
        )

        print(f"✅ Handoff state loaded. Starting token count: {instance.token_tracker.total_tokens}")

    def _build_handoff_context_prompt(self, handoff_doc: HandoffDocument) -> str:
        """
        Build a system prompt addition from handoff document.

        Args:
            handoff_doc: Handoff document

        Returns:
            Prompt text to prepend to system prompt
        """
        return f"""
## AGENT CONTINUITY CONTEXT

You are resuming work from a previous agent instance (version {handoff_doc.source_agent.instance_version}).
The previous agent consumed {handoff_doc.token_usage['usage_percentage']:.1f}% of the context window before handoff.

### TASK CONTEXT
- **Original Request:** {handoff_doc.original_request}
- **Current Status:** {handoff_doc.task_progress.overall_completion_percentage}% complete
- **Current Phase:** {handoff_doc.task_progress.current_phase}

### YOUR IMMEDIATE PRIORITIES
{self._format_todo_list(handoff_doc.todo_list)}

### DECISIONS ALREADY MADE (DO NOT REVISIT)
{self._format_decisions(handoff_doc.decisions_made)}

### REJECTED ALTERNATIVES (DO NOT RETRY)
{self._format_rejected_alternatives(handoff_doc.rejected_alternatives)}

### WORK COMPLETED
{self._format_completed_work(handoff_doc.work_completed)}

**IMPORTANT:** Build upon the previous agent's work. Do not repeat decisions or re-explore rejected paths.
Focus on the TODO list above. Reference the full handoff document at:
{handoff_doc.file_path}
"""

    def _format_todo_list(self, todos: list) -> str:
        """Format TODO list for prompt"""
        if not todos:
            return "No pending tasks."
        return "\n".join([f"{i+1}. {todo['task']} (Priority: {todo['priority']})" for i, todo in enumerate(todos)])

    def _format_decisions(self, decisions: list) -> str:
        """Format decision history for prompt"""
        if not decisions:
            return "No previous decisions."
        return "\n".join([f"- {d['decision']}: {d['reasoning']}" for d in decisions[:5]])  # Top 5

    def _format_rejected_alternatives(self, rejected: list) -> str:
        """Format rejected alternatives for prompt"""
        if not rejected:
            return "No rejected alternatives."
        return "\n".join([f"- {r['alternative']}: {r['reason']}" for r in rejected[:3]])  # Top 3

    def _format_completed_work(self, work: dict) -> str:
        """Format completed work summary"""
        files = work.get('files_created', [])
        if not files:
            return "No files created yet."
        return "\n".join([f"- {f['filename']} ({f['status']})" for f in files[:5]])  # Top 5

    async def record_agent_usage(
        self,
        agent_type: str,
        operation_name: str,
        usage_obj: Any
    ) -> str:
        """
        Record token usage for an agent and check thresholds.

        Args:
            agent_type: Type of agent
            operation_name: Name of the operation
            usage_obj: Usage object from Anthropic API

        Returns:
            Status: "OK", "WARNING", or "CRITICAL"
        """
        if agent_type not in self.active_agents:
            raise ValueError(f"No active agent of type: {agent_type}")

        instance = self.active_agents[agent_type]
        status = instance.token_tracker.record_usage(operation_name, usage_obj)

        # Update lifecycle state
        if status == "CRITICAL":
            instance.lifecycle_state = AgentLifecycleState.CRITICAL
            # Trigger handoff immediately
            await self._initiate_handoff(agent_type)
        elif status == "WARNING":
            instance.lifecycle_state = AgentLifecycleState.WARNING

        # Log metric
        log_metric(
            "agent_token_usage",
            instance.token_tracker.total_tokens,
            agent_type=agent_type,
            instance_id=instance.instance_id,
            usage_percentage=instance.token_tracker.usage_percentage
        )

        return status

    async def _initiate_handoff(self, agent_type: str):
        """
        Initiate handoff process for an agent.

        Steps:
        1. Create handoff document
        2. Write to disk
        3. Spawn new agent instance
        4. Terminate old instance

        Args:
            agent_type: Type of agent to handoff
        """
        instance = self.active_agents[agent_type]
        print(f"\n🔄 INITIATING HANDOFF for {instance.instance_id}")
        print(f"   Token Usage: {instance.token_tracker.usage_percentage:.1f}%")

        with trace_operation(
            "agent_handoff",
            agent_type=agent_type,
            instance_id=instance.instance_id,
            token_usage=instance.token_tracker.total_tokens
        ):
            # Step 1: Pause agent from receiving new tasks
            instance.lifecycle_state = AgentLifecycleState.HANDOFF_PENDING

            # Notify orchestrator to pause task routing
            if self.orchestrator_callback:
                await self.orchestrator_callback("agent_handoff_starting", {
                    "agent_type": agent_type,
                    "instance_id": instance.instance_id
                })

            # Step 2: Create handoff document
            handoff_doc = await self.handoff_manager.create_handoff_document(
                agent_instance=instance,
                project_id=self.project_id
            )

            # Step 3: Write handoff document to disk
            handoff_path = await self.handoff_manager.write_handoff(
                handoff_doc,
                agent_type,
                instance.version
            )

            instance.lifecycle_state = AgentLifecycleState.HANDOFF_COMPLETE
            print(f"✅ Handoff document written: {handoff_path}")

            # Step 4: Spawn new agent instance
            new_version = instance.version + 1
            new_instance = await self.spawn_agent(
                agent_type=agent_type,
                mcp_servers=instance.agent.mcp_servers,
                handoff_document=handoff_doc,
                version=new_version
            )

            # Step 5: Terminate old instance
            await self.terminate_agent(agent_type, instance)

            # Notify orchestrator that handoff is complete
            if self.orchestrator_callback:
                await self.orchestrator_callback("agent_handoff_complete", {
                    "agent_type": agent_type,
                    "old_instance_id": instance.instance_id,
                    "new_instance_id": new_instance.instance_id,
                    "handoff_path": str(handoff_path)
                })

            log_event(
                "agent_handoff_complete",
                agent_type=agent_type,
                old_instance=instance.instance_id,
                new_instance=new_instance.instance_id,
                handoff_path=str(handoff_path)
            )

    async def terminate_agent(
        self,
        agent_type: str,
        instance: Optional[AgentInstance] = None
    ):
        """
        Terminate an agent instance and clean up resources.

        Args:
            agent_type: Type of agent
            instance: Specific instance to terminate (if None, uses active)
        """
        if instance is None:
            if agent_type not in self.active_agents:
                return
            instance = self.active_agents[agent_type]

        print(f"🛑 Terminating agent: {instance.instance_id}")

        # Cleanup agent resources
        await instance.agent.cleanup()

        # Update state
        instance.lifecycle_state = AgentLifecycleState.TERMINATED

        # Remove from active agents if currently active
        if agent_type in self.active_agents and self.active_agents[agent_type] == instance:
            del self.active_agents[agent_type]

        # Log event
        log_event(
            "agent_terminated",
            agent_type=agent_type,
            instance_id=instance.instance_id,
            uptime_seconds=instance.uptime_seconds,
            total_tokens_consumed=instance.token_tracker.total_tokens
        )

        print(f"✅ Agent terminated: {instance.instance_id}")

    async def start_monitoring(self):
        """Start background monitoring task"""
        if self.monitoring_task is not None:
            return

        print("🔍 Starting agent lifecycle monitoring...")
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())

    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while True:
            try:
                await asyncio.sleep(self.monitoring_interval)

                # Check all active agents
                for agent_type, instance in list(self.active_agents.items()):
                    # Health check
                    instance.last_health_check = datetime.utcnow()

                    # Log current state
                    log_metric(
                        "agent_health_check",
                        instance.token_tracker.usage_percentage,
                        agent_type=agent_type,
                        instance_id=instance.instance_id,
                        lifecycle_state=instance.lifecycle_state.value
                    )

                    # Check if handoff needed (defensive check)
                    if instance.should_handoff() and instance.lifecycle_state == AgentLifecycleState.ACTIVE:
                        print(f"⚠️  Agent {instance.instance_id} exceeds token threshold!")
                        await self._initiate_handoff(agent_type)

            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                import traceback
                traceback.print_exc()

    async def stop_monitoring(self):
        """Stop background monitoring task"""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            self.monitoring_task = None
            print("🔍 Agent lifecycle monitoring stopped")

    async def cleanup_all_agents(self):
        """Cleanup all active agents"""
        print("🧹 Cleaning up all agents...")
        for agent_type in list(self.active_agents.keys()):
            await self.terminate_agent(agent_type)
        print("✅ All agents cleaned up")

    def get_agent_status(self, agent_type: str) -> Optional[Dict]:
        """Get status information for an agent"""
        if agent_type not in self.active_agents:
            return None

        instance = self.active_agents[agent_type]
        return {
            "instance_id": instance.instance_id,
            "agent_type": agent_type,
            "version": instance.version,
            "lifecycle_state": instance.lifecycle_state.value,
            "uptime_seconds": instance.uptime_seconds,
            "token_usage": instance.token_tracker.to_dict(),
            "last_health_check": instance.last_health_check.isoformat()
        }

    def get_all_agent_statuses(self) -> Dict[str, Dict]:
        """Get status for all active agents"""
        return {
            agent_type: self.get_agent_status(agent_type)
            for agent_type in self.active_agents
        }
```

---

## 2. State Transfer Mechanism

### 2.1 Handoff Manager

**Location:** `src/python/agents/collaborative/handoff_manager.py`

```python
"""
Handoff Manager

Handles creation, serialization, and loading of agent handoff documents.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import json
import yaml
from pydantic import BaseModel, Field

from .models import AgentCard
from utils.telemetry import trace_operation


class AgentInfo(BaseModel):
    """Agent identification information"""
    agent_id: str
    agent_type: str
    role: str
    instance_version: int
    spawn_timestamp: str
    termination_reason: Optional[str] = None


class TokenUsageInfo(BaseModel):
    """Token usage metrics"""
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    usage_percentage: float
    remaining_tokens: int
    context_window_limit: int = 200_000
    operation_count: int


class TaskProgress(BaseModel):
    """Task progress information"""
    overall_completion_percentage: int
    current_phase: str
    current_subphase: Optional[str] = None
    status: str


class Decision(BaseModel):
    """A decision made by the agent"""
    decision: str
    reasoning: str
    confidence: float
    timestamp: str
    impact: Optional[str] = None


class RejectedAlternative(BaseModel):
    """An alternative approach that was rejected"""
    alternative: str
    reason: str
    confidence_rejection: float


class FileInfo(BaseModel):
    """Information about a created/modified file"""
    filename: str
    purpose: str
    status: str
    lines: int
    language: Optional[str] = None


class TodoItem(BaseModel):
    """A task item in the TODO list"""
    task: str
    priority: str
    estimated_time: str
    dependencies: List[str] = Field(default_factory=list)
    status: str = "pending"


class HandoffDocument(BaseModel):
    """Complete handoff document structure"""

    # Metadata
    schema_version: str = "1.0.0"
    trace_id: str
    task_id: str
    handoff_id: str
    timestamp: str

    # Agent information
    source_agent: AgentInfo
    target_agent: AgentInfo

    # Token usage
    token_usage: TokenUsageInfo

    # Task progress
    task_progress: TaskProgress

    # Orchestration context
    project_id: str
    user_id: str
    platform: str
    workflow_type: str

    # Content
    original_request: str
    task_description: str
    decisions_made: List[Decision]
    rejected_alternatives: List[RejectedAlternative]
    work_completed: Dict[str, Any]
    current_work_in_progress: Optional[str] = None
    todo_list: List[TodoItem]

    # Additional context
    tool_state: Dict[str, Any] = Field(default_factory=dict)
    assumptions: List[str] = Field(default_factory=list)
    dependencies: Dict[str, str] = Field(default_factory=dict)

    # File path (set after writing)
    file_path: Optional[str] = None


class HandoffManager:
    """Manages creation and loading of handoff documents"""

    def __init__(self, handoff_directory: Path):
        """
        Initialize handoff manager.

        Args:
            handoff_directory: Base directory for handoff files
        """
        self.handoff_directory = Path(handoff_directory)
        self.handoff_directory.mkdir(parents=True, exist_ok=True)

    async def create_handoff_document(
        self,
        agent_instance: 'AgentInstance',
        project_id: str,
        orchestrator_context: Optional[Dict] = None
    ) -> HandoffDocument:
        """
        Create a handoff document by interrogating the agent.

        This is the critical method that extracts all necessary state
        from the current agent instance.

        Args:
            agent_instance: Current agent instance
            project_id: Project ID
            orchestrator_context: Additional context from orchestrator

        Returns:
            HandoffDocument object
        """
        print(f"📝 Creating handoff document for {agent_instance.instance_id}...")

        with trace_operation(
            "create_handoff_document",
            agent_type=agent_instance.agent_type,
            instance_id=agent_instance.instance_id
        ):
            # Get orchestrator context
            ctx = orchestrator_context or {}

            # Ask the agent to generate handoff content
            handoff_content = await self._query_agent_for_handoff(agent_instance)

            # Build handoff document
            handoff_doc = HandoffDocument(
                trace_id=ctx.get('trace_id', f"trace_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"),
                task_id=ctx.get('task_id', f"task_{project_id}"),
                handoff_id=f"handoff_{agent_instance.instance_id}",
                timestamp=datetime.utcnow().isoformat(),

                # Agent info
                source_agent=AgentInfo(
                    agent_id=agent_instance.instance_id,
                    agent_type=agent_instance.agent_type,
                    role=agent_instance.agent.agent_card.role.value,
                    instance_version=agent_instance.version,
                    spawn_timestamp=agent_instance.spawn_time.isoformat(),
                    termination_reason="context_window_exhausted"
                ),
                target_agent=AgentInfo(
                    agent_id=f"{agent_instance.agent_type}_v{agent_instance.version + 1}",
                    agent_type=agent_instance.agent_type,
                    role=agent_instance.agent.agent_card.role.value,
                    instance_version=agent_instance.version + 1,
                    spawn_timestamp="",  # Will be set when spawned
                    termination_reason=None
                ),

                # Token usage
                token_usage=TokenUsageInfo(**agent_instance.token_tracker.to_dict()),

                # Task progress
                task_progress=TaskProgress(
                    overall_completion_percentage=handoff_content.get('completion_percentage', 0),
                    current_phase=handoff_content.get('current_phase', 'unknown'),
                    current_subphase=handoff_content.get('current_subphase'),
                    status="in_progress"
                ),

                # Orchestration
                project_id=project_id,
                user_id=ctx.get('user_id', 'unknown'),
                platform=ctx.get('platform', 'unknown'),
                workflow_type=ctx.get('workflow_type', 'unknown'),

                # Content from agent
                original_request=handoff_content.get('original_request', ''),
                task_description=handoff_content.get('task_description', ''),
                decisions_made=handoff_content.get('decisions_made', []),
                rejected_alternatives=handoff_content.get('rejected_alternatives', []),
                work_completed=handoff_content.get('work_completed', {}),
                current_work_in_progress=handoff_content.get('current_work_in_progress'),
                todo_list=handoff_content.get('todo_list', []),
                tool_state=handoff_content.get('tool_state', {}),
                assumptions=handoff_content.get('assumptions', []),
                dependencies=handoff_content.get('dependencies', {})
            )

            print(f"✅ Handoff document created ({len(json.dumps(handoff_doc.model_dump()))} bytes)")
            return handoff_doc

    async def _query_agent_for_handoff(
        self,
        agent_instance: 'AgentInstance'
    ) -> Dict[str, Any]:
        """
        Query the agent to generate handoff content.

        This uses a special system prompt to extract comprehensive
        state information from the agent.

        Args:
            agent_instance: Agent instance to query

        Returns:
            Dict containing handoff content
        """
        handoff_query_prompt = """
## HANDOFF DOCUMENT GENERATION REQUEST

You are about to be replaced by a new instance of the same agent type due to context window limitations.
Before termination, you must create a comprehensive handoff document for your replacement.

**CRITICAL:** Your replacement needs to seamlessly continue your work without repeating your research, decisions, or mistakes.

Please provide a structured JSON response with the following information:

```json
{
  "original_request": "The initial user request that started this task",
  "task_description": "What you were asked to accomplish",
  "completion_percentage": 0-100,
  "current_phase": "What phase of work you're in",
  "current_subphase": "Specific sub-task within the phase (optional)",

  "decisions_made": [
    {
      "decision": "What you decided",
      "reasoning": "Why you made this decision",
      "confidence": 0.0-1.0,
      "timestamp": "ISO 8601 timestamp",
      "impact": "What effect this had on the task"
    }
  ],

  "rejected_alternatives": [
    {
      "alternative": "Approach you considered but rejected",
      "reason": "Why this won't work",
      "confidence_rejection": 0.0-1.0
    }
  ],

  "work_completed": {
    "files_created": [
      {
        "filename": "path/to/file",
        "purpose": "What this file does",
        "status": "complete|in_progress",
        "lines": 123,
        "language": "python|typescript|etc"
      }
    ],
    "summary": "High-level summary of what's been accomplished"
  },

  "current_work_in_progress": "Detailed description of what you're currently working on (if incomplete)",

  "todo_list": [
    {
      "task": "What needs to be done",
      "priority": "high|medium|low",
      "estimated_time": "15 minutes|2 hours|etc",
      "dependencies": ["List of dependencies"],
      "status": "pending"
    }
  ],

  "tool_state": {
    "example_tool": {
      "session_id": "...",
      "filters": {},
      "cache_keys": []
    }
  },

  "assumptions": [
    "Explicit assumption 1",
    "Explicit assumption 2"
  ],

  "dependencies": {
    "designer_handoff": "path/to/designer/handoff.md",
    "backend_api": "path/to/api/spec.yaml"
  }
}
```

**Format:** Provide ONLY the JSON object. No markdown code blocks, no explanations.
**Be comprehensive:** Your replacement will only have this document and the system context.
"""

        try:
            # Send query to agent's Claude SDK
            response = await agent_instance.agent.claude_sdk.send_message(handoff_query_prompt)

            # Parse JSON response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                handoff_data = json.loads(json_match.group(0))
                return handoff_data
            else:
                print("⚠️  Agent response did not contain valid JSON, using fallback")
                return self._generate_fallback_handoff_content(agent_instance)

        except Exception as e:
            print(f"❌ Error querying agent for handoff: {e}")
            return self._generate_fallback_handoff_content(agent_instance)

    def _generate_fallback_handoff_content(
        self,
        agent_instance: 'AgentInstance'
    ) -> Dict[str, Any]:
        """
        Generate minimal handoff content when agent query fails.

        Args:
            agent_instance: Agent instance

        Returns:
            Fallback handoff content
        """
        return {
            "original_request": "Unknown (agent query failed)",
            "task_description": f"{agent_instance.agent_type} task",
            "completion_percentage": 0,
            "current_phase": "unknown",
            "decisions_made": [],
            "rejected_alternatives": [],
            "work_completed": {},
            "todo_list": [],
            "tool_state": {},
            "assumptions": [],
            "dependencies": {}
        }

    async def write_handoff(
        self,
        handoff_doc: HandoffDocument,
        agent_type: str,
        version: int
    ) -> Path:
        """
        Write handoff document to disk as markdown with YAML front matter.

        Args:
            handoff_doc: Handoff document to write
            agent_type: Agent type
            version: Agent version

        Returns:
            Path to written file
        """
        # Create agent-specific directory
        agent_dir = self.handoff_directory / handoff_doc.project_id / agent_type
        agent_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_v{version}_handoff.md"
        file_path = agent_dir / filename

        # Convert to markdown with YAML front matter
        markdown_content = self._to_markdown(handoff_doc)

        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        # Update document with file path
        handoff_doc.file_path = str(file_path)

        print(f"💾 Handoff document written: {file_path}")
        return file_path

    def _to_markdown(self, handoff_doc: HandoffDocument) -> str:
        """
        Convert handoff document to markdown with YAML front matter.

        Args:
            handoff_doc: Handoff document

        Returns:
            Markdown string
        """
        # Extract metadata for YAML front matter
        metadata = handoff_doc.model_dump(exclude={
            'original_request', 'task_description', 'decisions_made',
            'rejected_alternatives', 'work_completed', 'current_work_in_progress',
            'todo_list', 'tool_state', 'assumptions', 'dependencies'
        })

        # Build YAML front matter
        yaml_content = yaml.dump(metadata, default_flow_style=False, sort_keys=False)

        # Build markdown content
        md_content = f"""---
{yaml_content}---

# AGENT HANDOFF DOCUMENT

**From:** {handoff_doc.source_agent.agent_type} v{handoff_doc.source_agent.instance_version}
**To:** {handoff_doc.target_agent.agent_type} v{handoff_doc.target_agent.instance_version}
**Date:** {handoff_doc.timestamp}
**Reason:** Context window exhausted ({handoff_doc.token_usage.usage_percentage:.1f}% usage)

---

## 1. ORIGINAL REQUEST & CONTEXT

{handoff_doc.original_request}

---

## 2. TASK DESCRIPTION & STATUS

{handoff_doc.task_description}

**Completion:** {handoff_doc.task_progress.overall_completion_percentage}%
**Current Phase:** {handoff_doc.task_progress.current_phase}

---

## 3. DECISIONS MADE

{self._format_decisions_md(handoff_doc.decisions_made)}

---

## 4. REJECTED ALTERNATIVES

{self._format_rejected_alternatives_md(handoff_doc.rejected_alternatives)}

---

## 5. WORK COMPLETED

{self._format_work_completed_md(handoff_doc.work_completed)}

---

## 6. CURRENT WORK IN PROGRESS

{handoff_doc.current_work_in_progress or "No work currently in progress."}

---

## 7. TODO LIST

{self._format_todo_list_md(handoff_doc.todo_list)}

---

## 8. TOOL STATE

{self._format_tool_state_md(handoff_doc.tool_state)}

---

## 9. ASSUMPTIONS

{self._format_assumptions_md(handoff_doc.assumptions)}

---

## 10. DEPENDENCIES

{self._format_dependencies_md(handoff_doc.dependencies)}

---

**END OF HANDOFF DOCUMENT**
"""
        return md_content

    def _format_decisions_md(self, decisions: List[Decision]) -> str:
        """Format decisions as markdown"""
        if not decisions:
            return "No decisions made yet."

        md = ""
        for i, decision in enumerate(decisions, 1):
            md += f"\n### Decision {i}: {decision.decision}\n"
            md += f"- **Reasoning:** {decision.reasoning}\n"
            md += f"- **Confidence:** {decision.confidence:.0%}\n"
            md += f"- **Timestamp:** {decision.timestamp}\n"
            if decision.impact:
                md += f"- **Impact:** {decision.impact}\n"
        return md

    def _format_rejected_alternatives_md(self, rejected: List[RejectedAlternative]) -> str:
        """Format rejected alternatives as markdown"""
        if not rejected:
            return "No rejected alternatives."

        md = ""
        for i, alt in enumerate(rejected, 1):
            md += f"\n### Alternative {i}: {alt.alternative}\n"
            md += f"- **Reason for Rejection:** {alt.reason}\n"
            md += f"- **Confidence in Rejection:** {alt.confidence_rejection:.0%}\n"
        return md

    def _format_work_completed_md(self, work: Dict[str, Any]) -> str:
        """Format work completed as markdown"""
        if not work:
            return "No work completed yet."

        md = ""
        if 'files_created' in work and work['files_created']:
            md += "\n### Files Created\n\n"
            for file in work['files_created']:
                status_emoji = "✅" if file['status'] == "complete" else "🔄"
                md += f"{status_emoji} **{file['filename']}**\n"
                md += f"  - Purpose: {file['purpose']}\n"
                md += f"  - Lines: {file['lines']}\n"
                if 'language' in file:
                    md += f"  - Language: {file['language']}\n"
                md += "\n"

        if 'summary' in work:
            md += f"\n### Summary\n\n{work['summary']}\n"

        return md

    def _format_todo_list_md(self, todos: List[TodoItem]) -> str:
        """Format TODO list as markdown"""
        if not todos:
            return "No pending tasks."

        md = ""
        for i, todo in enumerate(todos, 1):
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            emoji = priority_emoji.get(todo.priority.lower(), "⚪")

            md += f"\n### {i}. {emoji} {todo.task}\n"
            md += f"- **Priority:** {todo.priority}\n"
            md += f"- **Estimated Time:** {todo.estimated_time}\n"
            if todo.dependencies:
                md += f"- **Dependencies:** {', '.join(todo.dependencies)}\n"
            md += f"- **Status:** {todo.status}\n"

        return md

    def _format_tool_state_md(self, tool_state: Dict[str, Any]) -> str:
        """Format tool state as markdown"""
        if not tool_state:
            return "No tool state to preserve."

        md = "```json\n"
        md += json.dumps(tool_state, indent=2)
        md += "\n```"
        return md

    def _format_assumptions_md(self, assumptions: List[str]) -> str:
        """Format assumptions as markdown"""
        if not assumptions:
            return "No explicit assumptions."

        return "\n".join([f"- {assumption}" for assumption in assumptions])

    def _format_dependencies_md(self, dependencies: Dict[str, str]) -> str:
        """Format dependencies as markdown"""
        if not dependencies:
            return "No dependencies."

        md = ""
        for name, path in dependencies.items():
            md += f"- **{name}:** `{path}`\n"
        return md

    async def load_handoff(self, handoff_path: Path) -> HandoffDocument:
        """
        Load a handoff document from disk.

        Args:
            handoff_path: Path to handoff document

        Returns:
            HandoffDocument object
        """
        with open(handoff_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse YAML front matter
        import re
        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not match:
            raise ValueError("Invalid handoff document format (missing YAML front matter)")

        yaml_content = match.group(1)
        metadata = yaml.safe_load(yaml_content)

        # Parse markdown content for additional data
        # (This is simplified - in practice, you'd parse markdown sections)

        # Create HandoffDocument from metadata
        handoff_doc = HandoffDocument(**metadata)
        handoff_doc.file_path = str(handoff_path)

        return handoff_doc
```

---

## 3. Orchestrator Monitoring

### 3.1 Orchestrator Integration

**Modifications to:** `src/python/agents/collaborative/orchestrator.py`

```python
from .agent_lifecycle_manager import AgentLifecycleManager, AgentLifecycleState

class CollaborativeOrchestrator:
    def __init__(self, ...):
        # ... existing code ...

        # Add lifecycle manager
        handoff_dir = Path("handoffs")
        self.lifecycle_manager = AgentLifecycleManager(
            handoff_directory=handoff_dir,
            project_id=self.project_id or f"proj_{user_id}",
            orchestrator_callback=self._handle_lifecycle_event
        )

        # Register agent classes
        from .designer_agent import DesignerAgent
        from .backend_agent import BackendAgent
        from .frontend_agent import FrontendDeveloperAgent
        # ... etc

        self.lifecycle_manager.register_agent_class("designer", DesignerAgent)
        self.lifecycle_manager.register_agent_class("backend", BackendAgent)
        self.lifecycle_manager.register_agent_class("frontend", FrontendDeveloperAgent)
        # ... etc

    async def _handle_lifecycle_event(self, event_type: str, event_data: dict):
        """
        Callback for lifecycle manager events.

        Args:
            event_type: Type of event
            event_data: Event data
        """
        if event_type == "agent_spawned":
            print(f"🎉 Orchestrator notified: Agent spawned - {event_data['instance_id']}")
            # Update workflow state
            # Send notification to user

        elif event_type == "agent_handoff_starting":
            print(f"⏸️  Orchestrator: Pausing task routing to {event_data['agent_type']}")
            # Pause sending tasks to this agent

        elif event_type == "agent_handoff_complete":
            print(f"✅ Orchestrator: Handoff complete for {event_data['agent_type']}")
            # Resume task routing
            # Send notification to user about continuity

    async def _get_agent(self, agent_type: str):
        """Modified to use lifecycle manager"""
        # Check if agent exists in lifecycle manager
        status = self.lifecycle_manager.get_agent_status(agent_type)

        if status is None:
            # Spawn new agent
            instance = await self.lifecycle_manager.spawn_agent(
                agent_type=agent_type,
                mcp_servers=self.mcp_servers,
                version=1
            )
            return instance.agent
        else:
            # Return existing agent
            return self.lifecycle_manager.active_agents[agent_type].agent

    async def _execute_agent_task(
        self,
        agent_type: str,
        task: Task
    ) -> TaskResponse:
        """Modified to track token usage"""
        agent = await self._get_agent(agent_type)

        # Execute task via A2A protocol
        response = await a2a_protocol.send_message(
            from_agent_id=self.ORCHESTRATOR_ID,
            to_agent_id=agent.agent_card.agent_id,
            message_type=MessageType.TASK_REQUEST,
            content=task.model_dump()
        )

        # Record token usage (if available from response)
        if 'token_usage' in response:
            status = await self.lifecycle_manager.record_agent_usage(
                agent_type=agent_type,
                operation_name=f"task_{task.task_id}",
                usage_obj=response['token_usage']
            )

            if status == "CRITICAL":
                print(f"⚠️  Agent {agent_type} approaching context limit!")
                # Lifecycle manager will automatically trigger handoff

        return TaskResponse(**response)
```

---

## 4. File Structure

```
src/python/agents/collaborative/
├── agent_lifecycle_manager.py    # NEW - Agent lifecycle management
├── handoff_manager.py             # NEW - Handoff document management
├── token_tracker.py               # NEW - Token usage tracking
├── orchestrator.py                # MODIFIED - Integration with lifecycle manager
├── base_agent.py                  # MODIFIED - Token tracking integration
├── ... (existing agent files)

handoffs/                           # NEW - Handoff documents storage
├── {project_id}/
│   ├── designer_agent/
│   │   ├── 20251027_120000_v1_handoff.md
│   │   └── 20251027_143000_v2_handoff.md
│   ├── frontend_agent/
│   │   └── 20251027_140000_v1_handoff.md
│   └── backend_agent/
│       └── 20251027_135000_v1_handoff.md
```

---

## 5. Implementation Phases

### Phase 1: Token Tracking (Week 1)
- [ ] Implement `AgentTokenTracker` class
- [ ] Modify `ClaudeSDK` to track token usage
- [ ] Add token metrics to telemetry
- [ ] Unit tests for token tracking

### Phase 2: Handoff Documents (Week 2)
- [ ] Implement `HandoffDocument` Pydantic models
- [ ] Implement `HandoffManager` class
- [ ] Create markdown generation logic
- [ ] Test handoff document creation

### Phase 3: Lifecycle Management (Week 3)
- [ ] Implement `AgentLifecycleManager` class
- [ ] Implement agent spawn/terminate logic
- [ ] Implement handoff triggering
- [ ] Integration tests

### Phase 4: Orchestrator Integration (Week 4)
- [ ] Modify orchestrator to use lifecycle manager
- [ ] Add lifecycle event handling
- [ ] Add monitoring loop
- [ ] End-to-end testing

### Phase 5: Production Hardening (Week 5)
- [ ] Error handling and recovery
- [ ] Handoff document validation
- [ ] Performance optimization
- [ ] Documentation

---

## 6. Testing Strategy

### 6.1 Unit Tests

```python
# tests/test_token_tracker.py
def test_token_tracker_basic():
    tracker = AgentTokenTracker("test_agent", context_window_limit=1000)
    usage = MockUsage(input_tokens=100, output_tokens=50)

    status = tracker.record_usage("test_op", usage)
    assert status == "OK"
    assert tracker.total_tokens == 150
    assert tracker.usage_percentage == 15.0

def test_token_tracker_warning_threshold():
    tracker = AgentTokenTracker("test_agent", context_window_limit=1000)
    usage = MockUsage(input_tokens=760, output_tokens=0)

    status = tracker.record_usage("test_op", usage)
    assert status == "WARNING"
    assert tracker.should_handoff() == False

def test_token_tracker_critical_threshold():
    tracker = AgentTokenTracker("test_agent", context_window_limit=1000)
    usage = MockUsage(input_tokens=910, output_tokens=0)

    status = tracker.record_usage("test_op", usage)
    assert status == "CRITICAL"
    assert tracker.should_handoff() == True
```

### 6.2 Integration Tests

```python
# tests/test_agent_handoff.py
@pytest.mark.asyncio
async def test_complete_handoff_flow():
    """Test complete handoff from agent v1 to v2"""

    # Setup
    lifecycle_manager = AgentLifecycleManager(...)
    lifecycle_manager.register_agent_class("test_agent", TestAgent)

    # Spawn agent v1
    instance_v1 = await lifecycle_manager.spawn_agent("test_agent", {}, version=1)

    # Simulate heavy token usage
    for i in range(10):
        usage = MockUsage(input_tokens=18000, output_tokens=2000)
        await lifecycle_manager.record_agent_usage("test_agent", f"op_{i}", usage)

    # Verify handoff was triggered
    assert instance_v1.lifecycle_state == AgentLifecycleState.TERMINATED

    # Verify new instance exists
    status = lifecycle_manager.get_agent_status("test_agent")
    assert status['version'] == 2

    # Verify handoff document exists
    handoff_dir = Path("handoffs") / "test_project" / "test_agent"
    handoff_files = list(handoff_dir.glob("*_v1_handoff.md"))
    assert len(handoff_files) == 1
```

### 6.3 End-to-End Tests

```python
# tests/test_e2e_webapp_build.py
@pytest.mark.asyncio
async def test_webapp_build_with_handoffs():
    """Test complete webapp build with multiple agent handoffs"""

    # Setup orchestrator with lifecycle management
    orchestrator = CollaborativeOrchestrator(...)

    # Start webapp build
    response = await orchestrator.build_webapp("Build a todo app with 20 features")

    # Verify multiple handoffs occurred
    handoff_dir = Path("handoffs") / orchestrator.project_id
    designer_handoffs = list((handoff_dir / "designer").glob("*.md"))
    frontend_handoffs = list((handoff_dir / "frontend").glob("*.md"))

    # Should have multiple versions if complex enough
    assert len(frontend_handoffs) >= 1

    # Verify final deployment
    assert "Deployed to" in response
```

---

**END OF IMPLEMENTATION PLAN**
