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
