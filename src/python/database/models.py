"""
SQLAlchemy Database Models for WhatsApp Multi-Agent System
Uses Neon PostgreSQL for serverless database hosting
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, String, Boolean, Integer, Text, DateTime, JSON, Index
)
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all database models"""
    pass


class OrchestratorState(Base):
    """
    Stores orchestrator state for crash recovery and persistence

    Enables:
    - State recovery after crashes or restarts
    - Audit trail of orchestrator activities
    - Analytics on workflow patterns
    - Multi-instance orchestrator coordination
    """
    __tablename__ = "orchestrator_state"

    # Primary key (supports both phone numbers and GitHub repo#issue identifiers)
    phone_number: Mapped[str] = mapped_column(String(100), primary_key=True)

    # State tracking
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    current_phase: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    current_workflow: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Task details
    original_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    accumulated_refinements: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    current_implementation: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    current_design_spec: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Workflow progress
    workflow_steps_completed: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    workflow_steps_total: Mapped[int] = mapped_column(Integer, default=0)
    current_agent_working: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    current_task_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Indexes for query performance
    __table_args__ = (
        Index('idx_phone_number', 'phone_number'),
        Index('idx_is_active', 'is_active'),
        Index('idx_updated_at', 'updated_at'),
    )


class OrchestratorAudit(Base):
    """
    Audit trail for orchestrator events

    Tracks:
    - State changes
    - Phase transitions
    - Agent assignments
    - User interactions
    """
    __tablename__ = "orchestrator_audit"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Event details (supports both phone numbers and GitHub repo#issue identifiers)
    phone_number: Mapped[str] = mapped_column(String(100), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes for query performance
    __table_args__ = (
        Index('idx_audit_phone', 'phone_number'),
        Index('idx_audit_created', 'created_at'),
        Index('idx_audit_event_type', 'event_type'),
    )


class ConversationSession(Base):
    """
    Stores conversation sessions and message history

    Replaces Redis for persistent session storage.
    Each platform (WhatsApp, GitHub) has separate sessions.

    session_id format:
    - WhatsApp: phone number (e.g., "+1234567890")
    - GitHub: repo#issue (e.g., "owner/repo#123")
    """
    __tablename__ = "conversation_session"

    # Primary key (session_id = phone number or repo#issue)
    session_id: Mapped[str] = mapped_column(String(200), primary_key=True)

    # Platform identifier
    platform: Mapped[str] = mapped_column(String(20), nullable=False)  # "whatsapp" or "github"

    # Session data
    conversation_history: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=list)
    session_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_active: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Indexes
    __table_args__ = (
        Index('idx_session_id', 'session_id'),
        Index('idx_session_platform', 'platform'),
        Index('idx_session_last_active', 'last_active'),
    )


class ProjectMetadata(Base):
    """
    Tracks all user projects and their dedicated database schemas

    Each project gets its own PostgreSQL schema for data isolation:
    - Schema name format: project_{user_hash}_{project_id}
    - Enables multi-tenancy with schema-level isolation
    - Allows safe database operations per project
    """
    __tablename__ = "project_metadata"

    # Primary key
    project_id: Mapped[str] = mapped_column(String(100), primary_key=True)

    # User identification (hashed for privacy)
    user_id: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    user_id_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA256 hash

    # Platform (whatsapp, github, etc.)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)

    # Project details
    project_name: Mapped[str] = mapped_column(String(200), nullable=False)
    project_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Database isolation
    schema_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    # Project specification (from design phase)
    design_spec: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    backend_spec: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    frontend_spec: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Deployment information
    deployment_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    deployment_status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, deployed, failed

    # Database schema metadata
    tables_created: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    schema_version: Mapped[int] = mapped_column(Integer, default=1)

    # Neon PostgreSQL connection information (for webapp deployment)
    # These fields store the dedicated Neon project created for each webapp
    neon_project_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # e.g., "ep-cool-meadow-123456"
    neon_database_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # Regular connection string
    neon_database_url_pooled: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # Pooled connection (for serverless)
    neon_region: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # e.g., "aws-us-east-1"
    neon_branch_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # e.g., "br-main-xyz"
    neon_database_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # e.g., "neondb"

    # Project status
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, archived, deleted

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    last_accessed: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_project_user_id', 'user_id'),
        Index('idx_project_user_hash', 'user_id_hash'),
        Index('idx_project_schema', 'schema_name'),
        Index('idx_project_platform', 'platform'),
        Index('idx_project_status', 'status'),
        Index('idx_project_created', 'created_at'),
    )


class AgentHandoff(Base):
    """
    Stores agent handoff documents for context window management

    When an agent reaches its context window limit (200K tokens), it creates
    a handoff document containing all state, decisions, work completed, and TODOs.
    The orchestrator then spawns a new agent instance that continues from this handoff.

    This enables:
    - Seamless agent continuity across context window boundaries
    - Prevention of context rot
    - Full audit trail of agent lifecycle events
    - Memory-efficient storage (database vs in-memory)
    - Organization by user (WhatsApp number, GitHub repo)
    """
    __tablename__ = "agent_handoff"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Handoff identification
    handoff_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    trace_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # Links handoffs in same task chain
    task_id: Mapped[str] = mapped_column(String(100), nullable=False)

    # User and project identification
    user_id: Mapped[str] = mapped_column(String(200), nullable=False, index=True)  # WhatsApp number or GitHub repo#issue
    project_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)  # "whatsapp", "github"
    workflow_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "full_build", "bug_fix", "feature_add"

    # Agent information
    source_agent_id: Mapped[str] = mapped_column(String(100), nullable=False)
    source_agent_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # "frontend", "backend", etc.
    source_agent_role: Mapped[str] = mapped_column(String(100), nullable=False)
    source_agent_version: Mapped[int] = mapped_column(Integer, nullable=False)

    target_agent_id: Mapped[str] = mapped_column(String(100), nullable=False)
    target_agent_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_agent_role: Mapped[str] = mapped_column(String(100), nullable=False)
    target_agent_version: Mapped[int] = mapped_column(Integer, nullable=False)

    termination_reason: Mapped[str] = mapped_column(String(50), nullable=False)  # "context_window_exhausted", "task_completed", etc.

    # Token usage summary (for quick queries without parsing JSON)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    total_input_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    total_output_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    usage_percentage: Mapped[float] = mapped_column(Integer, nullable=False)  # 0-100

    # Task progress summary (for quick queries)
    completion_percentage: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-100
    current_phase: Mapped[str] = mapped_column(String(100), nullable=False)
    task_status: Mapped[str] = mapped_column(String(20), nullable=False)  # "in_progress", "completed", "blocked"

    # Complete handoff document (JSON/JSONB for flexible schema)
    # This contains all 17 categories from HandoffDocument Pydantic model
    handoff_data: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Optional markdown file path for human readability
    markdown_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Metadata
    schema_version: Mapped[str] = mapped_column(String(20), default="1.0.0", nullable=False)

    # Handoff lifecycle
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)  # False if superseded or archived
    successor_handoff_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Next handoff in chain

    # Timestamps
    handoff_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)  # When handoff occurred
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Indexes for efficient queries
    __table_args__ = (
        # Most common query: Get latest handoff for a user
        Index('idx_handoff_user_created', 'user_id', 'created_at'),

        # Get handoffs by agent type (e.g., all frontend agent handoffs)
        Index('idx_handoff_agent_type', 'source_agent_type', 'created_at'),

        # Get handoffs for a specific project
        Index('idx_handoff_project', 'project_id', 'created_at'),

        # Track handoff chains via trace_id
        Index('idx_handoff_trace', 'trace_id', 'created_at'),

        # Query by task
        Index('idx_handoff_task', 'task_id', 'created_at'),

        # Find active handoffs
        Index('idx_handoff_active', 'is_active', 'user_id'),

        # Analytics queries (token usage, completion rate)
        Index('idx_handoff_tokens', 'total_tokens'),
        Index('idx_handoff_completion', 'completion_percentage'),

        # Platform-specific queries
        Index('idx_handoff_platform', 'platform', 'user_id'),
    )
