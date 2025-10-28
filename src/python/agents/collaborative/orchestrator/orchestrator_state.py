"""
State Persistence Module for Collaborative Orchestrator
Handles state management with Neon PostgreSQL database
"""

from typing import Optional


class OrchestratorStateMixin:
    """
    Mixin providing state persistence methods for the orchestrator.

    This mixin handles saving/restoring orchestrator state to/from Neon PostgreSQL
    to enable crash recovery and state persistence across sessions.
    """

    async def _ensure_state_manager(self):
        """
        Ensure state manager is initialized (lazy initialization)

        This is called automatically before any state operations
        """
        if not self._state_manager_initialized:
            try:
                print(f"🗄️  Initializing state manager for user: {self.user_id}")
                from agents.collaborative.orchestrator_state import OrchestratorStateManager
                self.state_manager = OrchestratorStateManager()
                await self.state_manager.initialize()
                self._state_manager_initialized = True
                print(f"✅ State manager initialized successfully")

                # Try to restore previous state
                if self.user_id:
                    await self._restore_state()

            except Exception as e:
                print(f"❌ State persistence FAILED - Database will NOT be used!")
                print(f"   Error: {e}")
                import traceback
                traceback.print_exc()
                self.state_manager = None
                self._state_manager_initialized = False

    async def _save_state(self):
        """
        Save current orchestrator state to database

        Automatically called after state changes to ensure persistence
        """
        if not self.state_manager:
            print(f"⚠️  State manager not initialized - skipping database save")
            return

        if not self.user_id:
            print(f"⚠️  No user_id - skipping database save")
            return

        try:
            state = {
                'is_active': self.is_active,
                'current_phase': self.current_phase,
                'current_workflow': self.current_workflow,
                'original_prompt': self.original_prompt,
                'accumulated_refinements': self.accumulated_refinements,
                'current_implementation': self.current_implementation,
                'current_design_spec': self.current_design_spec,
                'workflow_steps_completed': self.workflow_steps_completed,
                'workflow_steps_total': self.workflow_steps_total,
                'current_agent_working': self.current_agent_working,
                'current_task_description': self.current_task_description
            }

            print(f"💾 Saving state to database for user: {self.user_id}")
            print(f"   Phase: {self.current_phase}, Workflow: {self.current_workflow}")
            await self.state_manager.save_state(self.user_id, state)
            print(f"✅ State successfully saved to Neon database!")

        except Exception as e:
            print(f"❌ Failed to save state to database!")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()

    async def _restore_state(self):
        """
        Restore orchestrator state from database (if exists)

        Called during initialization to recover from crashes
        """
        if not self.state_manager or not self.user_id:
            return

        try:
            state = await self.state_manager.load_state(self.user_id)

            if state and state.get('is_active'):
                print(f"🔄 Restoring previous orchestrator state for {self.user_id}")

                self.is_active = state.get('is_active', False)
                self.current_phase = state.get('current_phase')
                self.current_workflow = state.get('current_workflow')
                self.original_prompt = state.get('original_prompt')
                self.accumulated_refinements = state.get('accumulated_refinements', [])
                self.current_implementation = state.get('current_implementation')
                self.current_design_spec = state.get('current_design_spec')
                self.workflow_steps_completed = state.get('workflow_steps_completed', [])
                self.workflow_steps_total = state.get('workflow_steps_total', 0)
                self.current_agent_working = state.get('current_agent_working')
                self.current_task_description = state.get('current_task_description')

                print(f"✅ State restored (Phase: {self.current_phase}, Workflow: {self.current_workflow})")

                # Notify user
                if self.current_phase and self.current_workflow:
                    self._send_whatsapp_notification(
                        f"🔄 Resumed previous task!\n\n"
                        f"📋 Task: {self.original_prompt[:100]}...\n"
                        f"⚙️  Phase: {self.current_phase}\n"
                        f"📊 Progress: {len(self.workflow_steps_completed)}/{self.workflow_steps_total} steps\n\n"
                        f"Continuing from where we left off..."
                    )

        except Exception as e:
            print(f"⚠️  Failed to restore state: {e}")

    async def _delete_state(self):
        """
        Delete orchestrator state from database

        Called when a task completes or is cancelled
        """
        if not self.state_manager or not self.user_id:
            return

        try:
            await self.state_manager.delete_state(self.user_id)
            print(f"🗑️  State deleted from database (user: {self.user_id})")

        except Exception as e:
            print(f"⚠️  Failed to delete state: {e}")
