"""
PostgreSQL-based Orchestrator State Manager
Enables crash recovery, persistence, and audit trail using Neon PostgreSQL
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from typing import Dict, Optional, List
from datetime import datetime, timedelta
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database import OrchestratorState, OrchestratorAudit, get_session, init_db


class OrchestratorStateManager:
    """
    Manages orchestrator state in PostgreSQL/Neon for persistence and recovery

    Features:
    - Automatic state persistence after every change
    - Crash recovery (resume from last state)
    - Audit trail (track all state changes)
    - Stale state cleanup (remove old inactive sessions)
    - Multi-instance coordination (shared state across instances)

    Usage:
        manager = OrchestratorStateManager()
        await manager.initialize()

        # Save state
        await manager.save_state(phone_number, state_dict)

        # Load state
        state = await manager.load_state(phone_number)

        # Delete state
        await manager.delete_state(phone_number)
    """

    def __init__(self):
        """Initialize state manager"""
        self._initialized = False
        print("🗄️  OrchestratorStateManager created (Neon PostgreSQL)")

    async def initialize(self):
        """
        Initialize database connection and create tables

        Should be called once at startup before using any other methods
        """
        if self._initialized:
            return

        try:
            # Initialize database tables
            await init_db()
            self._initialized = True
            print("✅ OrchestratorStateManager initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize OrchestratorStateManager: {e}")
            raise

    async def save_state(self, phone_number: str, state: Dict):
        """
        Save orchestrator state to database

        Args:
            phone_number: User's phone number (unique identifier)
            state: Dictionary containing orchestrator state

        State dictionary should contain:
            - is_active: bool
            - current_phase: str | None
            - current_workflow: str | None
            - original_prompt: str | None
            - accumulated_refinements: list
            - current_implementation: dict | None
            - current_design_spec: dict | None
            - workflow_steps_completed: list
            - workflow_steps_total: int
            - current_agent_working: str | None
            - current_task_description: str | None

        Raises:
            Exception: If database operation fails
        """
        if not self._initialized:
            raise RuntimeError("OrchestratorStateManager not initialized. Call initialize() first.")

        try:
            async for session in get_session():
                # Check if state exists
                result = await session.execute(
                    select(OrchestratorState).where(OrchestratorState.phone_number == phone_number)
                )
                existing_state = result.scalar_one_or_none()

                if existing_state:
                    # Update existing state
                    existing_state.is_active = state.get('is_active', False)
                    existing_state.current_phase = state.get('current_phase')
                    existing_state.current_workflow = state.get('current_workflow')
                    existing_state.original_prompt = state.get('original_prompt')
                    existing_state.accumulated_refinements = state.get('accumulated_refinements', [])
                    existing_state.current_implementation = state.get('current_implementation')
                    existing_state.current_design_spec = state.get('current_design_spec')
                    existing_state.workflow_steps_completed = state.get('workflow_steps_completed', [])
                    existing_state.workflow_steps_total = state.get('workflow_steps_total', 0)
                    existing_state.current_agent_working = state.get('current_agent_working')
                    existing_state.current_task_description = state.get('current_task_description')
                    existing_state.updated_at = datetime.utcnow()
                else:
                    # Create new state
                    new_state = OrchestratorState(
                        phone_number=phone_number,
                        is_active=state.get('is_active', False),
                        current_phase=state.get('current_phase'),
                        current_workflow=state.get('current_workflow'),
                        original_prompt=state.get('original_prompt'),
                        accumulated_refinements=state.get('accumulated_refinements', []),
                        current_implementation=state.get('current_implementation'),
                        current_design_spec=state.get('current_design_spec'),
                        workflow_steps_completed=state.get('workflow_steps_completed', []),
                        workflow_steps_total=state.get('workflow_steps_total', 0),
                        current_agent_working=state.get('current_agent_working'),
                        current_task_description=state.get('current_task_description')
                    )
                    session.add(new_state)

                await session.commit()

                # Log audit event
                await self._log_audit(session, phone_number, 'state_saved', {
                    'phase': state.get('current_phase'),
                    'workflow': state.get('current_workflow'),
                    'is_active': state.get('is_active')
                })

        except Exception as e:
            print(f"❌ Error saving orchestrator state for {phone_number}: {e}")
            raise

    async def load_state(self, phone_number: str) -> Optional[Dict]:
        """
        Load orchestrator state from database

        Args:
            phone_number: User's phone number

        Returns:
            Dictionary containing orchestrator state, or None if not found

        Raises:
            Exception: If database operation fails
        """
        if not self._initialized:
            raise RuntimeError("OrchestratorStateManager not initialized. Call initialize() first.")

        try:
            async for session in get_session():
                result = await session.execute(
                    select(OrchestratorState).where(OrchestratorState.phone_number == phone_number)
                )
                state_record = result.scalar_one_or_none()

                if not state_record:
                    return None

                # Convert to dictionary
                state = {
                    'phone_number': state_record.phone_number,
                    'is_active': state_record.is_active,
                    'current_phase': state_record.current_phase,
                    'current_workflow': state_record.current_workflow,
                    'original_prompt': state_record.original_prompt,
                    'accumulated_refinements': state_record.accumulated_refinements or [],
                    'current_implementation': state_record.current_implementation,
                    'current_design_spec': state_record.current_design_spec,
                    'workflow_steps_completed': state_record.workflow_steps_completed or [],
                    'workflow_steps_total': state_record.workflow_steps_total,
                    'current_agent_working': state_record.current_agent_working,
                    'current_task_description': state_record.current_task_description,
                    'created_at': state_record.created_at,
                    'updated_at': state_record.updated_at
                }

                return state

        except Exception as e:
            print(f"❌ Error loading orchestrator state for {phone_number}: {e}")
            raise

    async def delete_state(self, phone_number: str):
        """
        Delete orchestrator state from database

        Args:
            phone_number: User's phone number

        Raises:
            Exception: If database operation fails
        """
        if not self._initialized:
            raise RuntimeError("OrchestratorStateManager not initialized. Call initialize() first.")

        try:
            async for session in get_session():
                await session.execute(
                    delete(OrchestratorState).where(OrchestratorState.phone_number == phone_number)
                )
                await session.commit()

                # Log audit event
                await self._log_audit(session, phone_number, 'state_deleted', {})

        except Exception as e:
            print(f"❌ Error deleting orchestrator state for {phone_number}: {e}")
            raise

    async def get_active_orchestrators(self) -> List[str]:
        """
        Get list of phone numbers with active orchestrators

        Returns:
            List of phone numbers with is_active=True

        Raises:
            Exception: If database operation fails
        """
        if not self._initialized:
            raise RuntimeError("OrchestratorStateManager not initialized. Call initialize() first.")

        try:
            async for session in get_session():
                result = await session.execute(
                    select(OrchestratorState.phone_number).where(OrchestratorState.is_active == True)
                )
                phone_numbers = [row[0] for row in result.fetchall()]
                return phone_numbers

        except Exception as e:
            print(f"❌ Error getting active orchestrators: {e}")
            raise

    async def cleanup_stale_orchestrators(self, max_age_hours: int = 24) -> int:
        """
        Clean up orchestrators that have been inactive for too long

        Args:
            max_age_hours: Maximum age in hours (default: 24 hours)

        Returns:
            Number of orchestrators cleaned up

        Raises:
            Exception: If database operation fails
        """
        if not self._initialized:
            raise RuntimeError("OrchestratorStateManager not initialized. Call initialize() first.")

        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)

            async for session in get_session():
                result = await session.execute(
                    delete(OrchestratorState).where(
                        OrchestratorState.updated_at < cutoff_time
                    ).returning(OrchestratorState.phone_number)
                )
                deleted_phones = result.fetchall()
                count = len(deleted_phones)

                await session.commit()

                if count > 0:
                    print(f"🧹 Cleaned up {count} stale orchestrator(s)")

                return count

        except Exception as e:
            print(f"❌ Error cleaning up stale orchestrators: {e}")
            raise

    async def get_audit_trail(self, phone_number: str, limit: int = 100) -> List[Dict]:
        """
        Get audit trail for a phone number

        Args:
            phone_number: User's phone number
            limit: Maximum number of audit records to return (default: 100)

        Returns:
            List of audit records (newest first)

        Raises:
            Exception: If database operation fails
        """
        if not self._initialized:
            raise RuntimeError("OrchestratorStateManager not initialized. Call initialize() first.")

        try:
            async for session in get_session():
                result = await session.execute(
                    select(OrchestratorAudit)
                    .where(OrchestratorAudit.phone_number == phone_number)
                    .order_by(OrchestratorAudit.created_at.desc())
                    .limit(limit)
                )
                audit_records = result.scalars().all()

                # Convert to dictionaries
                audit_trail = [
                    {
                        'id': record.id,
                        'phone_number': record.phone_number,
                        'event_type': record.event_type,
                        'event_data': record.event_data,
                        'created_at': record.created_at
                    }
                    for record in audit_records
                ]

                return audit_trail

        except Exception as e:
            print(f"❌ Error getting audit trail for {phone_number}: {e}")
            raise

    async def _log_audit(self, session: AsyncSession, phone_number: str, event_type: str, event_data: Dict):
        """
        Log audit event (internal method)

        Args:
            session: Database session
            phone_number: User's phone number
            event_type: Type of event (e.g., 'state_saved', 'state_deleted')
            event_data: Additional event data
        """
        try:
            audit_record = OrchestratorAudit(
                phone_number=phone_number,
                event_type=event_type,
                event_data=event_data
            )
            session.add(audit_record)
            await session.commit()
        except Exception as e:
            print(f"⚠️  Warning: Failed to log audit event: {e}")
            # Don't raise - audit logging should not break main functionality
