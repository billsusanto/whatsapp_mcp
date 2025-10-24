"""
Session Management for Multi-Platform Agent Manager

This module provides session storage interfaces and implementations.
"""

from .base import BaseSessionManager
from .inmemory import SessionManager

__all__ = ["BaseSessionManager", "SessionManager"]
