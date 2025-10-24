"""
Platform Adapters for Multi-Platform Agent Manager

This module provides adapter interfaces for different messaging platforms.
"""

from .notification import NotificationAdapter
from .whatsapp_adapter import WhatsAppAdapter
from .github_adapter import GitHubAdapter

__all__ = ["NotificationAdapter", "WhatsAppAdapter", "GitHubAdapter"]
