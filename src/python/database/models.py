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
