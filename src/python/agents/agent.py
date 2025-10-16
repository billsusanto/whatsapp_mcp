"""
Claude Agent

Represents a single Claude agent instance that handles conversations
"""

from typing import Dict, Optional
import sys
sys.path.append('..')
from sdk.claude_sdk import ClaudeSDK
from agents.session import SessionManager


class Agent:
    """Individual Claude agent for handling WhatsApp conversations"""

    def __init__(self, phone_number: str, session_manager: SessionManager):
        """
        Initialize an agent for a specific user

        Args:
            phone_number: The WhatsApp user's phone number
            session_manager: Shared session manager instance

        TODO:
        - Store phone_number
        - Store reference to session_manager
        - Initialize ClaudeSDK instance
        """
        pass

    def process_message(self, user_message: str) -> str:
        """
        Process a message from the user and generate a response

        Args:
            user_message: The message text from WhatsApp user

        Returns:
            Claude's response text

        TODO:
        - Get conversation history from session_manager
        - Send message to Claude SDK with history
        - Add user message to session
        - Add assistant response to session
        - Return response
        """
        pass

    def reset_conversation(self):
        """
        Clear the conversation history for this user

        TODO:
        - Call session_manager.clear_session(phone_number)
        """
        pass
