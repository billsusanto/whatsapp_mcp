"""
Collaborative Orchestrator - Backward Compatibility Wrapper

This file maintains backward compatibility for imports.
The actual implementation is now in the orchestrator/ package.

Usage:
    from agents.collaborative.orchestrator import CollaborativeOrchestrator
    # This still works!
"""

# Import from new package structure
from .orchestrator import CollaborativeOrchestrator

__all__ = ['CollaborativeOrchestrator']
