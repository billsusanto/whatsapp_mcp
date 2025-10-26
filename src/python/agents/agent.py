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

    def __init__(
        self,
        phone_number: str,
        session_manager: SessionManager,
        available_mcp_servers: Optional[dict] = None
    ):
        """
        Initialize an agent for a specific user

        Args:
            phone_number: The WhatsApp user's phone number
            session_manager: Shared session manager instance
            available_mcp_servers: Dict of MCP servers available to this agent
                                  Format: {"server_name": server_config or tools_list}
                                  Example: {
                                      "whatsapp": [send_whatsapp_tool],
                                      "github": {"url": "...", "headers": {...}}
                                  }
        """
        self.phone_number = phone_number
        self.session_manager = session_manager
        self.available_mcp_servers = available_mcp_servers or {}

        # Initialize Claude SDK with all available MCP servers
        self.claude_sdk = ClaudeSDK(
            available_mcp_servers=self.available_mcp_servers
        )

        server_names = list(self.available_mcp_servers.keys())
        print(f"Agent created for {phone_number}")
        print(f"  Available MCP servers: {server_names if server_names else 'none'}")

    async def process_message(self, user_message: str) -> str:
        """
        Process a message from the user and generate a response

        Args:
            user_message: The message text from WhatsApp user

        Returns:
            Claude's response text
        """
        try:
            # Add user message to session (use async method if available)
            if hasattr(self.session_manager, '_add_message_async'):
                await self.session_manager._add_message_async(self.phone_number, "user", user_message)
            else:
                self.session_manager.add_message(self.phone_number, "user", user_message)

            # Get conversation history (use async method if available)
            if hasattr(self.session_manager, '_get_conversation_history_async'):
                history = await self.session_manager._get_conversation_history_async(self.phone_number)
            else:
                history = self.session_manager.get_conversation_history(self.phone_number)

            # Send to Claude SDK
            response = await self.claude_sdk.send_message(user_message, history)

            # Add assistant response to session (use async method if available)
            if hasattr(self.session_manager, '_add_message_async'):
                await self.session_manager._add_message_async(self.phone_number, "assistant", response)
            else:
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
            # Add user message to session (use async method if available)
            if hasattr(self.session_manager, '_add_message_async'):
                await self.session_manager._add_message_async(self.phone_number, "user", user_message)
            else:
                self.session_manager.add_message(self.phone_number, "user", user_message)

            # Get conversation history (use async method if available)
            if hasattr(self.session_manager, '_get_conversation_history_async'):
                history = await self.session_manager._get_conversation_history_async(self.phone_number)
            else:
                history = self.session_manager.get_conversation_history(self.phone_number)

            # Stream from Claude SDK
            full_response = ""
            async for chunk in self.claude_sdk.stream_message(user_message, history):
                full_response += chunk
                yield chunk

            # Add complete response to session (use async method if available)
            if hasattr(self.session_manager, '_add_message_async'):
                await self.session_manager._add_message_async(self.phone_number, "assistant", full_response)
            else:
                self.session_manager.add_message(self.phone_number, "assistant", full_response)

        except Exception as e:
            print(f"Error in agent streaming for {self.phone_number}: {str(e)}")
            raise

    async def reset_conversation(self):
        """Clear the conversation history for this user"""
        if hasattr(self.session_manager, '_clear_session_async'):
            await self.session_manager._clear_session_async(self.phone_number)
        else:
            self.session_manager.clear_session(self.phone_number)
        print(f"Conversation reset for {self.phone_number}")

    async def cleanup(self):
        """Clean up agent resources"""
        await self.claude_sdk.close()
        print(f"Agent cleanup completed for {self.phone_number}")
