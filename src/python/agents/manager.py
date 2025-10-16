"""
Agent Manager

Manages the lifecycle of multiple Claude agents (one per WhatsApp user)
"""

from typing import Dict, Optional
from agents.agent import Agent
from agents.session import SessionManager


class AgentManager:
    """Manages multiple agent instances"""

    def __init__(self):
        """
        Initialize the agent manager

        TODO:
        - Create a SessionManager instance (shared across all agents)
        - Initialize storage for active agents: dict[phone_number] -> Agent
        """
        pass

    def get_or_create_agent(self, phone_number: str) -> Agent:
        """
        Get existing agent or create a new one for a phone number

        Args:
            phone_number: User's WhatsApp phone number

        Returns:
            Agent instance for this user

        TODO:
        - Check if agent exists in storage
        - If not, create new Agent(phone_number, session_manager)
        - Store and return agent
        """
        pass

    def process_message(self, phone_number: str, message: str) -> str:
        """
        Process a message by routing to the appropriate agent

        Args:
            phone_number: User's phone number
            message: Message text

        Returns:
            Agent's response

        TODO:
        - Get or create agent for phone_number
        - Call agent.process_message(message)
        - Return response
        """
        pass

    def cleanup(self):
        """
        Clean up inactive agents and sessions

        TODO:
        - Call session_manager.cleanup_expired_sessions()
        - Remove agents with expired sessions
        - Run this periodically
        """
        pass
