"""
Claude Agent

Represents a single Claude agent instance that handles conversations
"""

from typing import Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sdk.claude_sdk import ClaudeSDK
from agents.session import SessionManager


class Agent:
    """Individual Claude agent for handling WhatsApp conversations"""

    def __init__(self, phone_number: str, session_manager: SessionManager, mcp_tools: Optional[list] = None):
        """
        Initialize an agent for a specific user

        Args:
            phone_number: The WhatsApp user's phone number
            session_manager: Shared session manager instance
            mcp_tools: List of MCP tools to register with the agent
        """
        self.phone_number = phone_number
        self.session_manager = session_manager
        self.mcp_tools = mcp_tools or []

        # Initialize Claude SDK with tools
        self.claude_sdk = ClaudeSDK(tools=self.mcp_tools)

        print(f"Agent created for {phone_number} with {len(self.mcp_tools)} MCP tools")

    async def process_message(self, user_message: str) -> str:
        """
        Process a message from the user and generate a response

        Args:
            user_message: The message text from WhatsApp user

        Returns:
            Claude's response text
        """
        try:
            # Add user message to session
            self.session_manager.add_message(self.phone_number, "user", user_message)

            # Get conversation history
            history = self.session_manager.get_conversation_history(self.phone_number)

            # Send to Claude SDK
            response = await self.claude_sdk.send_message(user_message, history)

            # Add assistant response to session
            self.session_manager.add_message(self.phone_number, "assistant", response)

            return response

        except Exception as e:
            print(f"Error in agent processing for {self.phone_number}: {str(e)}")
            raise

    async def stream_response(self, user_message: str):
        """
        Stream response for real-time updates

        Args:
            user_message: The message from user

        Yields:
            Text chunks as they arrive from Claude
        """
        try:
            # Add user message to session
            self.session_manager.add_message(self.phone_number, "user", user_message)

            # Get conversation history
            history = self.session_manager.get_conversation_history(self.phone_number)

            # Stream from Claude SDK
            full_response = ""
            async for chunk in self.claude_sdk.stream_message(user_message, history):
                full_response += chunk
                yield chunk

            # Add complete response to session
            self.session_manager.add_message(self.phone_number, "assistant", full_response)

        except Exception as e:
            print(f"Error in agent streaming for {self.phone_number}: {str(e)}")
            raise

    def reset_conversation(self):
        """Clear the conversation history for this user"""
        self.session_manager.clear_session(self.phone_number)
        print(f"Conversation reset for {self.phone_number}")

    async def cleanup(self):
        """Clean up agent resources"""
        await self.claude_sdk.close()
        print(f"Agent cleanup completed for {self.phone_number}")
