"""
Handoff Manager - PostgreSQL Storage for Agent Handoffs

Manages agent handoff documents with database-first approach for memory efficiency.
Stores handoffs in PostgreSQL organized by user_id (WhatsApp number) with optional markdown files.
"""

import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

from sqlalchemy import select, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import AgentHandoff
from agents.collaborative.handoff_models import HandoffDocument
from agents.collaborative.token_tracker import AgentTokenTracker

# Import Logfire tracing
from utils.telemetry import (
    trace_handoff_document,
    trace_database_operation,
    log_event
)


class HandoffManager:
    """
    Manages agent handoff documents with PostgreSQL storage.

    Primary storage: PostgreSQL database (memory-efficient)
    Secondary storage: Optional markdown files (human-readable)

    Responsibilities:
    - Create handoff documents from agent state
    - Save handoffs to PostgreSQL
    - Load handoffs for agent respawn
    - Query handoffs by user, project, agent type, etc.
    - Generate optional markdown files
    - Manage handoff chains (trace_id linking)
    """

    def __init__(
        self,
        db_session: AsyncSession,
        markdown_base_path: Optional[str] = None,
        enable_markdown: bool = False
    ):
        """
        Initialize handoff manager.

        Args:
            db_session: Async SQLAlchemy database session
            markdown_base_path: Base directory for markdown files (optional)
            enable_markdown: Whether to generate markdown files (default: False for memory efficiency)
        """
        self.db = db_session
        self.markdown_base_path = Path(markdown_base_path) if markdown_base_path else None
        self.enable_markdown = enable_markdown

        print(f"🔄 HandoffManager initialized")
        print(f"   Database: PostgreSQL (async)")
        print(f"   Markdown: {'Enabled' if enable_markdown else 'Disabled (memory-efficient)'}")

    async def create_handoff(
        self,
        source_agent_id: str,
        source_agent_type: str,
        source_agent_role: str,
        source_agent_version: int,
        termination_reason: str,
        token_tracker: AgentTokenTracker,
        user_id: str,
        project_id: str,
        platform: str,
        workflow_type: str,
        original_request: str,
        task_description: str,
        current_phase: str,
        completion_percentage: int,
        task_status: str,
        trace_id: Optional[str] = None,
        task_id: Optional[str] = None,
        **kwargs  # Additional handoff fields (decisions, TODOs, work_completed, etc.)
    ) -> HandoffDocument:
        """
        Create a new handoff document.

        Args:
            source_agent_id: Agent being terminated
            source_agent_type: Type of agent (frontend, backend, etc.)
            source_agent_role: Agent's role description
            source_agent_version: Instance version number
            termination_reason: Why agent is being terminated
            token_tracker: Token tracker with usage history
            user_id: User identifier (WhatsApp number, GitHub repo)
            project_id: Project identifier
            platform: Platform (whatsapp, github)
            workflow_type: Workflow type (full_build, bug_fix, etc.)
            original_request: Original user request
            task_description: Current task description
            current_phase: Current workflow phase
            completion_percentage: Task completion (0-100)
            task_status: Status (in_progress, completed, blocked)
            trace_id: Optional trace ID for handoff chain
            task_id: Optional task identifier
            **kwargs: Additional handoff document fields

        Returns:
            HandoffDocument instance
        """
        # Generate IDs
        handoff_id = f"handoff_{uuid.uuid4().hex[:16]}"
        trace_id = trace_id or f"trace_{uuid.uuid4().hex[:16]}"
        task_id = task_id or f"task_{uuid.uuid4().hex[:16]}"

        # Create target agent info (incremented version)
        target_agent_id = f"{source_agent_type}_v{source_agent_version + 1}"
        target_agent_version = source_agent_version + 1

        # Build HandoffDocument
        from agents.collaborative.handoff_models import (
            AgentInfo,
            TokenUsageInfo,
            TaskProgress
        )

        # Extract token usage from tracker
        token_usage = TokenUsageInfo(
            total_input_tokens=token_tracker.total_input_tokens,
            total_output_tokens=token_tracker.total_output_tokens,
            total_cached_tokens=token_tracker.total_cached_tokens,
            total_tokens=token_tracker.total_tokens,
            usage_percentage=token_tracker.usage_percentage,
            remaining_tokens=token_tracker.remaining_tokens,
            context_window_limit=token_tracker.context_window_limit,
            operation_count=len(token_tracker.operation_history)
        )

        # Create handoff document
        handoff = HandoffDocument(
            schema_version="1.0.0",
            handoff_id=handoff_id,
            trace_id=trace_id,
            task_id=task_id,
            timestamp=datetime.utcnow().isoformat(),
            source_agent=AgentInfo(
                agent_id=source_agent_id,
                agent_type=source_agent_type,
                role=source_agent_role,
                instance_version=source_agent_version,
                spawn_timestamp=kwargs.get('source_spawn_timestamp', datetime.utcnow().isoformat()),
                termination_reason=termination_reason
            ),
            target_agent=AgentInfo(
                agent_id=target_agent_id,
                agent_type=source_agent_type,  # Same type, new instance
                role=source_agent_role,  # Same role
                instance_version=target_agent_version,
                spawn_timestamp=datetime.utcnow().isoformat(),
                termination_reason=None
            ),
            token_usage=token_usage,
            task_progress=TaskProgress(
                overall_completion_percentage=completion_percentage,
                current_phase=current_phase,
                current_subphase=kwargs.get('current_subphase'),
                status=task_status
            ),
            project_id=project_id,
            user_id=user_id,
            platform=platform,
            workflow_type=workflow_type,
            original_request=original_request,
            task_description=task_description,
            # Optional fields from kwargs
            decisions_made=kwargs.get('decisions_made', []),
            rejected_alternatives=kwargs.get('rejected_alternatives', []),
            work_completed=kwargs.get('work_completed'),
            current_work_in_progress=kwargs.get('current_work_in_progress'),
            todo_list=kwargs.get('todo_list', []),
            tool_state=kwargs.get('tool_state', []),
            assumptions=kwargs.get('assumptions', []),
            constraints=kwargs.get('constraints', []),
            upstream_dependencies=kwargs.get('upstream_dependencies', {}),
            downstream_consumers=kwargs.get('downstream_consumers', []),
            errors_encountered=kwargs.get('errors_encountered', []),
            quality_metrics=kwargs.get('quality_metrics', {}),
            validation_rules=kwargs.get('validation_rules', [])
        )

        print(f"✅ Created handoff document: {handoff_id}")
        print(f"   Source: {source_agent_id} (v{source_agent_version})")
        print(f"   Target: {target_agent_id} (v{target_agent_version})")
        print(f"   Token Usage: {token_usage.total_tokens:,} tokens ({token_usage.usage_percentage:.1f}%)")
        print(f"   Completion: {completion_percentage}%")

        return handoff

    async def save_handoff(
        self,
        handoff: HandoffDocument,
        predecessor_handoff_id: Optional[str] = None
    ) -> int:
        """
        Save handoff document to PostgreSQL database.

        Args:
            handoff: HandoffDocument to save
            predecessor_handoff_id: Optional ID of previous handoff in chain

        Returns:
            Database ID of saved handoff
        """
        # Generate markdown if enabled
        markdown_path = None
        if self.enable_markdown and self.markdown_base_path:
            markdown_path = await self._save_markdown(handoff)

        # Logfire: Trace database save operation
        with trace_database_operation(
            table_name='agent_handoff',
            operation='insert',
            record_id=handoff.handoff_id
        ) as span:
            # Convert handoff to database model
            handoff_data_json = handoff.model_dump(mode='json')
            data_size_kb = round(len(str(handoff_data_json)) / 1024, 2)

            db_handoff = AgentHandoff(
                handoff_id=handoff.handoff_id,
                trace_id=handoff.trace_id,
                task_id=handoff.task_id,
                user_id=handoff.user_id,
                project_id=handoff.project_id,
                platform=handoff.platform,
                workflow_type=handoff.workflow_type,
                source_agent_id=handoff.source_agent.agent_id,
                source_agent_type=handoff.source_agent.agent_type,
                source_agent_role=handoff.source_agent.role,
                source_agent_version=handoff.source_agent.instance_version,
                target_agent_id=handoff.target_agent.agent_id,
                target_agent_type=handoff.target_agent.agent_type,
                target_agent_role=handoff.target_agent.role,
                target_agent_version=handoff.target_agent.instance_version,
                termination_reason=handoff.source_agent.termination_reason or "unknown",
                total_tokens=handoff.token_usage.total_tokens,
                total_input_tokens=handoff.token_usage.total_input_tokens,
                total_output_tokens=handoff.token_usage.total_output_tokens,
                usage_percentage=handoff.token_usage.usage_percentage,
                completion_percentage=handoff.task_progress.overall_completion_percentage,
                current_phase=handoff.task_progress.current_phase,
                task_status=handoff.task_progress.status,
                handoff_data=handoff_data_json,  # Full document as JSON
                markdown_path=markdown_path,
                schema_version=handoff.schema_version,
                is_active=True,
                handoff_timestamp=datetime.fromisoformat(handoff.timestamp),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            # Add span attributes
            if span:
                span.set_attribute('data_size_kb', data_size_kb)
                span.set_attribute('handoff_id', handoff.handoff_id)
                span.set_attribute('user_id', handoff.user_id)
                span.set_attribute('agent_type', handoff.source_agent.agent_type)

            # Add to session and flush to get ID
            self.db.add(db_handoff)
            await self.db.flush()

            # Update predecessor's successor_handoff_id if provided
            if predecessor_handoff_id:
                await self._link_handoffs(predecessor_handoff_id, handoff.handoff_id)

            # Commit transaction
            await self.db.commit()

            # Update handoff document with database ID
            handoff.database_id = db_handoff.id
            handoff.markdown_path = markdown_path
            handoff.created_at = db_handoff.created_at
            handoff.updated_at = db_handoff.updated_at

            # Log save event
            log_event(
                "handoff_saved",
                handoff_id=handoff.handoff_id,
                database_id=db_handoff.id,
                data_size_kb=data_size_kb,
                user_id=handoff.user_id,
                agent_type=handoff.source_agent.agent_type
            )

            print(f"💾 Saved handoff to database: ID={db_handoff.id}")
            if markdown_path:
                print(f"   Markdown: {markdown_path}")

        return db_handoff.id

    async def load_handoff(self, handoff_id: str) -> Optional[HandoffDocument]:
        """
        Load handoff document from database by handoff_id.

        Args:
            handoff_id: Unique handoff identifier

        Returns:
            HandoffDocument or None if not found
        """
        stmt = select(AgentHandoff).where(AgentHandoff.handoff_id == handoff_id)
        result = await self.db.execute(stmt)
        db_handoff = result.scalar_one_or_none()

        if not db_handoff:
            print(f"❌ Handoff not found: {handoff_id}")
            return None

        # Convert database model to Pydantic model
        handoff = HandoffDocument(**db_handoff.handoff_data)
        handoff.database_id = db_handoff.id
        handoff.markdown_path = db_handoff.markdown_path
        handoff.created_at = db_handoff.created_at
        handoff.updated_at = db_handoff.updated_at

        print(f"📥 Loaded handoff: {handoff_id}")
        return handoff

    async def get_latest_handoff_for_user(
        self,
        user_id: str,
        agent_type: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> Optional[HandoffDocument]:
        """
        Get the most recent handoff for a user.

        Args:
            user_id: User identifier (WhatsApp number, GitHub repo)
            agent_type: Optional filter by agent type
            project_id: Optional filter by project

        Returns:
            Latest HandoffDocument or None
        """
        stmt = select(AgentHandoff).where(
            and_(
                AgentHandoff.user_id == user_id,
                AgentHandoff.is_active == True
            )
        )

        if agent_type:
            stmt = stmt.where(AgentHandoff.source_agent_type == agent_type)

        if project_id:
            stmt = stmt.where(AgentHandoff.project_id == project_id)

        stmt = stmt.order_by(desc(AgentHandoff.created_at)).limit(1)

        result = await self.db.execute(stmt)
        db_handoff = result.scalar_one_or_none()

        if not db_handoff:
            return None

        handoff = HandoffDocument(**db_handoff.handoff_data)
        handoff.database_id = db_handoff.id
        handoff.markdown_path = db_handoff.markdown_path
        handoff.created_at = db_handoff.created_at
        handoff.updated_at = db_handoff.updated_at

        return handoff

    async def get_handoff_chain(self, trace_id: str) -> List[HandoffDocument]:
        """
        Get all handoffs in a chain by trace_id.

        Args:
            trace_id: Trace ID linking handoffs

        Returns:
            List of HandoffDocuments in chronological order
        """
        stmt = select(AgentHandoff).where(
            AgentHandoff.trace_id == trace_id
        ).order_by(AgentHandoff.created_at)

        result = await self.db.execute(stmt)
        db_handoffs = result.scalars().all()

        handoffs = []
        for db_handoff in db_handoffs:
            handoff = HandoffDocument(**db_handoff.handoff_data)
            handoff.database_id = db_handoff.id
            handoff.markdown_path = db_handoff.markdown_path
            handoff.created_at = db_handoff.created_at
            handoff.updated_at = db_handoff.updated_at
            handoffs.append(handoff)

        print(f"🔗 Retrieved handoff chain: {len(handoffs)} handoffs (trace={trace_id})")
        return handoffs

    async def get_user_handoff_history(
        self,
        user_id: str,
        limit: int = 10,
        offset: int = 0
    ) -> List[HandoffDocument]:
        """
        Get handoff history for a user.

        Args:
            user_id: User identifier
            limit: Maximum number of handoffs to return
            offset: Offset for pagination

        Returns:
            List of HandoffDocuments (most recent first)
        """
        stmt = select(AgentHandoff).where(
            AgentHandoff.user_id == user_id
        ).order_by(desc(AgentHandoff.created_at)).limit(limit).offset(offset)

        result = await self.db.execute(stmt)
        db_handoffs = result.scalars().all()

        handoffs = []
        for db_handoff in db_handoffs:
            handoff = HandoffDocument(**db_handoff.handoff_data)
            handoff.database_id = db_handoff.id
            handoff.markdown_path = db_handoff.markdown_path
            handoff.created_at = db_handoff.created_at
            handoff.updated_at = db_handoff.updated_at
            handoffs.append(handoff)

        return handoffs

    async def deactivate_handoff(self, handoff_id: str) -> bool:
        """
        Mark a handoff as inactive (superseded by newer handoff).

        Args:
            handoff_id: Handoff to deactivate

        Returns:
            True if successful
        """
        stmt = select(AgentHandoff).where(AgentHandoff.handoff_id == handoff_id)
        result = await self.db.execute(stmt)
        db_handoff = result.scalar_one_or_none()

        if not db_handoff:
            return False

        db_handoff.is_active = False
        db_handoff.updated_at = datetime.utcnow()

        await self.db.commit()

        print(f"🔄 Deactivated handoff: {handoff_id}")
        return True

    async def _link_handoffs(self, predecessor_id: str, successor_id: str):
        """Link two handoffs in a chain."""
        stmt = select(AgentHandoff).where(AgentHandoff.handoff_id == predecessor_id)
        result = await self.db.execute(stmt)
        predecessor = result.scalar_one_or_none()

        if predecessor:
            predecessor.successor_handoff_id = successor_id
            predecessor.is_active = False  # Deactivate superseded handoff
            predecessor.updated_at = datetime.utcnow()
            await self.db.flush()

    async def _save_markdown(self, handoff: HandoffDocument) -> str:
        """
        Save handoff document as markdown file.

        Args:
            handoff: HandoffDocument to save

        Returns:
            Path to saved markdown file
        """
        if not self.markdown_base_path:
            raise ValueError("markdown_base_path not configured")

        # Create directory structure: base_path / user_id / handoffs / handoff_id.md
        user_dir = self.markdown_base_path / handoff.user_id.replace('+', '').replace('/', '_')
        handoff_dir = user_dir / "handoffs"
        handoff_dir.mkdir(parents=True, exist_ok=True)

        # Generate markdown
        markdown_content = handoff.to_markdown()

        # Save file
        file_path = handoff_dir / f"{handoff.handoff_id}.md"
        file_path.write_text(markdown_content, encoding='utf-8')

        print(f"📝 Saved markdown: {file_path}")
        return str(file_path)

    async def get_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get handoff statistics.

        Args:
            user_id: Optional filter by user

        Returns:
            Statistics dictionary
        """
        from sqlalchemy import func

        # Base query
        stmt = select(
            func.count(AgentHandoff.id).label('total_handoffs'),
            func.avg(AgentHandoff.total_tokens).label('avg_tokens'),
            func.avg(AgentHandoff.completion_percentage).label('avg_completion'),
            func.count(AgentHandoff.id).filter(
                AgentHandoff.termination_reason == 'context_window_exhausted'
            ).label('context_exhausted_count')
        )

        if user_id:
            stmt = stmt.where(AgentHandoff.user_id == user_id)

        result = await self.db.execute(stmt)
        stats = result.one()

        return {
            'total_handoffs': stats.total_handoffs or 0,
            'avg_tokens_at_handoff': round(stats.avg_tokens or 0, 1),
            'avg_completion_at_handoff': round(stats.avg_completion or 0, 1),
            'context_exhausted_handoffs': stats.context_exhausted_count or 0,
            'user_id': user_id
        }
