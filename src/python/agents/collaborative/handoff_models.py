"""
Handoff Document Pydantic Models

Defines the structure of agent handoff documents for state transfer.
These models are used both for in-memory representation and database storage.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


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
    total_cached_tokens: int = 0
    total_tokens: int
    usage_percentage: float
    remaining_tokens: int
    context_window_limit: int = 200_000
    operation_count: int


class TaskProgress(BaseModel):
    """Task progress information"""
    overall_completion_percentage: int = Field(ge=0, le=100)
    current_phase: str
    current_subphase: Optional[str] = None
    status: str  # "in_progress", "completed", "blocked", etc.


class Decision(BaseModel):
    """A decision made by the agent"""
    decision: str
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)
    timestamp: str
    impact: Optional[str] = None


class RejectedAlternative(BaseModel):
    """An alternative approach that was rejected"""
    alternative: str
    reason: str
    confidence_rejection: float = Field(ge=0.0, le=1.0)


class FileInfo(BaseModel):
    """Information about a created/modified file"""
    filename: str
    purpose: str
    status: str  # "complete", "in_progress", "blocked"
    lines: int
    language: Optional[str] = None
    location: Optional[str] = None  # File path or URL


class TodoItem(BaseModel):
    """A task item in the TODO list"""
    task: str
    priority: str  # "high", "medium", "low"
    estimated_time: str
    dependencies: List[str] = Field(default_factory=list)
    status: str = "pending"  # "pending", "in_progress", "completed"


class ToolState(BaseModel):
    """State of a specific tool or resource"""
    tool_name: str
    state_data: Dict[str, Any]  # Flexible schema for tool-specific state
    session_id: Optional[str] = None
    last_used: Optional[str] = None


class ErrorRecord(BaseModel):
    """Record of an error encountered"""
    error_type: str
    error_message: str
    timestamp: str
    recovery_attempted: bool = False
    recovery_successful: bool = False


class WorkCompleted(BaseModel):
    """Summary of work completed by the agent"""
    files_created: List[FileInfo] = Field(default_factory=list)
    files_modified: List[FileInfo] = Field(default_factory=list)
    summary: Optional[str] = None
    key_achievements: List[str] = Field(default_factory=list)


class HandoffDocument(BaseModel):
    """
    Complete handoff document structure.

    This document contains all information needed for a new agent instance
    to seamlessly continue work from where the previous instance left off.
    """

    # ==========================================
    # METADATA
    # ==========================================
    schema_version: str = "1.0.0"
    handoff_id: str
    trace_id: str
    task_id: str
    timestamp: str

    # ==========================================
    # AGENT INFORMATION
    # ==========================================
    source_agent: AgentInfo
    target_agent: AgentInfo

    # ==========================================
    # TOKEN USAGE
    # ==========================================
    token_usage: TokenUsageInfo

    # ==========================================
    # TASK PROGRESS
    # ==========================================
    task_progress: TaskProgress

    # ==========================================
    # ORCHESTRATION CONTEXT
    # ==========================================
    project_id: str
    user_id: str  # WhatsApp number or GitHub identifier
    platform: str  # "whatsapp", "github", etc.
    workflow_type: str  # "full_build", "bug_fix", "feature_add", etc.

    # ==========================================
    # CONTENT - CORE CONTEXT
    # ==========================================
    original_request: str = Field(
        description="The initial user request that started this task"
    )
    task_description: str = Field(
        description="Current understanding of what needs to be accomplished"
    )

    # ==========================================
    # CONTENT - DECISION HISTORY
    # ==========================================
    decisions_made: List[Decision] = Field(
        default_factory=list,
        description="Key decisions with reasoning to avoid re-exploration"
    )
    rejected_alternatives: List[RejectedAlternative] = Field(
        default_factory=list,
        description="Approaches explicitly rejected to prevent retries"
    )

    # ==========================================
    # CONTENT - WORK STATUS
    # ==========================================
    work_completed: WorkCompleted = Field(
        default_factory=WorkCompleted,
        description="Summary of work already done"
    )
    current_work_in_progress: Optional[str] = Field(
        None,
        description="Detailed description of current incomplete work"
    )
    todo_list: List[TodoItem] = Field(
        default_factory=list,
        description="Prioritized list of remaining tasks"
    )

    # ==========================================
    # CONTENT - TECHNICAL STATE
    # ==========================================
    tool_state: List[ToolState] = Field(
        default_factory=list,
        description="State of tools, sessions, and resources"
    )
    assumptions: List[str] = Field(
        default_factory=list,
        description="Explicit assumptions that may need validation"
    )
    constraints: List[str] = Field(
        default_factory=list,
        description="Project constraints and requirements"
    )

    # ==========================================
    # CONTENT - DEPENDENCIES
    # ==========================================
    upstream_dependencies: Dict[str, str] = Field(
        default_factory=dict,
        description="Dependencies from other agents (e.g., designer handoff)"
    )
    downstream_consumers: List[str] = Field(
        default_factory=list,
        description="Agents that will consume this agent's output"
    )

    # ==========================================
    # CONTENT - ERROR HISTORY
    # ==========================================
    errors_encountered: List[ErrorRecord] = Field(
        default_factory=list,
        description="Errors encountered and recovery attempts"
    )

    # ==========================================
    # CONTENT - QUALITY & VALIDATION
    # ==========================================
    quality_metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Quality metrics and validation results"
    )
    validation_rules: List[str] = Field(
        default_factory=list,
        description="Validation rules that must pass"
    )

    # ==========================================
    # METADATA - STORAGE
    # ==========================================
    database_id: Optional[int] = Field(
        None,
        description="Primary key in PostgreSQL database"
    )
    markdown_path: Optional[str] = Field(
        None,
        description="Optional path to human-readable markdown file"
    )
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
        validate_assignment = True

    def get_continuation_prompt(self) -> str:
        """
        Generate a system prompt addition for the new agent instance.

        This prompt provides the new agent with critical context from the handoff.

        Returns:
            Prompt text to prepend to the agent's system prompt
        """
        prompt = f"""
## 🔄 AGENT CONTINUITY CONTEXT

You are **{self.target_agent.role} v{self.target_agent.instance_version}**, resuming work from a previous agent instance.

### 📋 HANDOFF SUMMARY
- **Previous Agent:** {self.source_agent.agent_id} (v{self.source_agent.instance_version})
- **Handoff Reason:** {self.source_agent.termination_reason}
- **Token Usage:** {self.token_usage.total_tokens:,} tokens ({self.token_usage.usage_percentage:.1f}% of context window)
- **Task Progress:** {self.task_progress.overall_completion_percentage}% complete
- **Current Phase:** {self.task_progress.current_phase}

### 🎯 ORIGINAL USER REQUEST
{self.original_request}

### 📊 CURRENT STATUS
{self.task_description}

**Completion:** {self.task_progress.overall_completion_percentage}%
**Phase:** {self.task_progress.current_phase}
**Status:** {self.task_progress.status}

### ✅ YOUR IMMEDIATE PRIORITIES
"""
        # Add top 5 TODO items
        for i, todo in enumerate(self.todo_list[:5], 1):
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(todo.priority.lower(), "⚪")
            prompt += f"{i}. {priority_emoji} {todo.task} (Priority: {todo.priority}, Est: {todo.estimated_time})\n"

        if len(self.todo_list) > 5:
            prompt += f"\n... and {len(self.todo_list) - 5} more tasks.\n"

        # Add key decisions
        if self.decisions_made:
            prompt += "\n### 🧠 KEY DECISIONS ALREADY MADE (DO NOT REVISIT)\n"
            for decision in self.decisions_made[:5]:
                prompt += f"- **{decision.decision}**: {decision.reasoning}\n"

        # Add rejected alternatives
        if self.rejected_alternatives:
            prompt += "\n### ❌ REJECTED ALTERNATIVES (DO NOT RETRY)\n"
            for alt in self.rejected_alternatives[:3]:
                prompt += f"- **{alt.alternative}**: {alt.reason}\n"

        # Add work completed summary
        if self.work_completed.summary:
            prompt += f"\n### ✨ WORK COMPLETED\n{self.work_completed.summary}\n"

        prompt += f"""
### ⚠️ IMPORTANT INSTRUCTIONS
1. **Build upon existing work** - Do not repeat completed tasks
2. **Respect past decisions** - Do not revisit decisions already made
3. **Avoid rejected paths** - Do not retry approaches that failed
4. **Continue from current phase** - Pick up exactly where the previous agent left off
5. **Reference handoff document** - Full details available in database (ID: {self.database_id})

**Start immediately with the highest priority TODO item above.**
"""
        return prompt

    def to_markdown(self) -> str:
        """
        Generate human-readable markdown representation.

        Returns:
            Markdown string with YAML front matter
        """
        # Create metadata dict for YAML front matter
        metadata = {
            "schema_version": self.schema_version,
            "handoff_id": self.handoff_id,
            "trace_id": self.trace_id,
            "task_id": self.task_id,
            "timestamp": self.timestamp,
            "source_agent": self.source_agent.model_dump(),
            "target_agent": self.target_agent.model_dump(),
            "token_usage": self.token_usage.model_dump(),
            "task_progress": self.task_progress.model_dump(),
            "project_id": self.project_id,
            "user_id": self.user_id,
            "platform": self.platform,
            "workflow_type": self.workflow_type
        }

        # Import yaml for front matter
        import yaml

        yaml_content = yaml.dump(metadata, default_flow_style=False, sort_keys=False)

        # Build markdown content
        md = f"""---
{yaml_content}---

# AGENT HANDOFF DOCUMENT

**From:** {self.source_agent.role} v{self.source_agent.instance_version} ({self.source_agent.agent_id})
**To:** {self.target_agent.role} v{self.target_agent.instance_version} ({self.target_agent.agent_id})
**Date:** {self.timestamp}
**Reason:** {self.source_agent.termination_reason}
**Token Usage:** {self.token_usage.total_tokens:,} tokens ({self.token_usage.usage_percentage:.1f}%)

---

## 1. ORIGINAL REQUEST & CONTEXT

{self.original_request}

---

## 2. TASK DESCRIPTION & STATUS

{self.task_description}

**Completion:** {self.task_progress.overall_completion_percentage}%
**Current Phase:** {self.task_progress.current_phase}
**Status:** {self.task_progress.status}

---

## 3. DECISIONS MADE

"""
        # Add decisions
        if self.decisions_made:
            for i, decision in enumerate(self.decisions_made, 1):
                md += f"\n### Decision {i}: {decision.decision}\n"
                md += f"- **Reasoning:** {decision.reasoning}\n"
                md += f"- **Confidence:** {decision.confidence:.0%}\n"
                md += f"- **Timestamp:** {decision.timestamp}\n"
                if decision.impact:
                    md += f"- **Impact:** {decision.impact}\n"
        else:
            md += "\nNo decisions made yet.\n"

        md += "\n---\n\n## 4. REJECTED ALTERNATIVES\n\n"

        # Add rejected alternatives
        if self.rejected_alternatives:
            for i, alt in enumerate(self.rejected_alternatives, 1):
                md += f"\n### Alternative {i}: {alt.alternative}\n"
                md += f"- **Reason for Rejection:** {alt.reason}\n"
                md += f"- **Confidence in Rejection:** {alt.confidence_rejection:.0%}\n"
        else:
            md += "\nNo rejected alternatives.\n"

        md += "\n---\n\n## 5. WORK COMPLETED\n\n"

        # Add work completed
        if self.work_completed.files_created:
            md += "### Files Created\n\n"
            for file in self.work_completed.files_created:
                status_emoji = "✅" if file.status == "complete" else "🔄"
                md += f"{status_emoji} **{file.filename}**\n"
                md += f"  - Purpose: {file.purpose}\n"
                md += f"  - Lines: {file.lines}\n"
                if file.language:
                    md += f"  - Language: {file.language}\n"
                md += "\n"

        if self.work_completed.summary:
            md += f"\n### Summary\n\n{self.work_completed.summary}\n"

        md += "\n---\n\n## 6. CURRENT WORK IN PROGRESS\n\n"
        md += self.current_work_in_progress or "No work currently in progress.\n"

        md += "\n---\n\n## 7. TODO LIST\n\n"

        # Add TODO list
        if self.todo_list:
            for i, todo in enumerate(self.todo_list, 1):
                priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(todo.priority.lower(), "⚪")
                md += f"\n### {i}. {priority_emoji} {todo.task}\n"
                md += f"- **Priority:** {todo.priority}\n"
                md += f"- **Estimated Time:** {todo.estimated_time}\n"
                if todo.dependencies:
                    md += f"- **Dependencies:** {', '.join(todo.dependencies)}\n"
                md += f"- **Status:** {todo.status}\n"
        else:
            md += "\nNo pending tasks.\n"

        md += "\n---\n\n## 8. TOOL STATE & SESSIONS\n\n"

        # Add tool state
        if self.tool_state:
            for tool in self.tool_state:
                md += f"\n### {tool.tool_name}\n"
                md += "```json\n"
                import json
                md += json.dumps(tool.state_data, indent=2)
                md += "\n```\n"
        else:
            md += "\nNo tool state to preserve.\n"

        md += "\n---\n\n## 9. ASSUMPTIONS & CONSTRAINTS\n\n"

        # Add assumptions
        if self.assumptions:
            md += "### Assumptions\n\n"
            for assumption in self.assumptions:
                md += f"- {assumption}\n"
        else:
            md += "### Assumptions\n\nNo explicit assumptions.\n"

        # Add constraints
        if self.constraints:
            md += "\n### Constraints\n\n"
            for constraint in self.constraints:
                md += f"- {constraint}\n"
        else:
            md += "\n### Constraints\n\nNo constraints.\n"

        md += "\n---\n\n## 10. ERROR HISTORY\n\n"

        # Add error history
        if self.errors_encountered:
            for i, error in enumerate(self.errors_encountered, 1):
                md += f"\n### Error {i}: {error.error_type}\n"
                md += f"- **Message:** {error.error_message}\n"
                md += f"- **Timestamp:** {error.timestamp}\n"
                md += f"- **Recovery Attempted:** {'Yes' if error.recovery_attempted else 'No'}\n"
                if error.recovery_attempted:
                    md += f"- **Recovery Successful:** {'Yes' if error.recovery_successful else 'No'}\n"
        else:
            md += "\nNo errors encountered.\n"

        md += "\n---\n\n**END OF HANDOFF DOCUMENT**\n"
        md += f"\n*Database ID: {self.database_id}*\n"
        md += f"*Generated: {datetime.utcnow().isoformat()}*\n"

        return md

    def get_summary(self) -> str:
        """
        Get a brief summary of the handoff.

        Returns:
            One-paragraph summary
        """
        return (
            f"Handoff from {self.source_agent.agent_id} (v{self.source_agent.instance_version}) "
            f"to {self.target_agent.agent_id} (v{self.target_agent.instance_version}). "
            f"Task is {self.task_progress.overall_completion_percentage}% complete in "
            f"{self.task_progress.current_phase} phase. "
            f"Used {self.token_usage.total_tokens:,} tokens ({self.token_usage.usage_percentage:.1f}%). "
            f"{len(self.todo_list)} tasks remaining."
        )
