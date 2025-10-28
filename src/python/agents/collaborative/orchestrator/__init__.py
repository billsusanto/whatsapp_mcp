"""
Collaborative Orchestrator Module

Coordinates multi-agent team for webapp development using A2A Protocol.

This module is split into multiple files for maintainability:
- orchestrator_core: Main class and public API
- orchestrator_workflows: Workflow implementations
- orchestrator_agents: Agent lifecycle management
- orchestrator_state: State persistence and recovery
"""

from .orchestrator_core import CollaborativeOrchestrator

__all__ = ['CollaborativeOrchestrator']
