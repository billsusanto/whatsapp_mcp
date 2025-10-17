"""
Agent Manager

Manages the lifecycle of multiple Claude agents (one per WhatsApp user)
"""

from typing import Dict, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agents.agent import Agent
from agents.session import SessionManager


class AgentManager:
    """Manages multiple agent instances"""

    def __init__(self, mcp_tools: Optional[list] = None):
        """
        Initialize the agent manager

        Args:
            mcp_tools: List of MCP tools to register with each agent
        """
        self.session_manager = SessionManager()
        self.agents: Dict[str, Agent] = {}
        self.mcp_tools = mcp_tools or []

        print(f"AgentManager initialized with {len(self.mcp_tools)} MCP tools")

    def get_or_create_agent(self, phone_number: str) -> Agent:
        """
        Get existing agent or create a new one for a phone number

        Args:
            phone_number: User's WhatsApp phone number

        Returns:
            Agent instance for this user
        """
        if phone_number not in self.agents:
            # Create new agent
            agent = Agent(
                phone_number=phone_number,
                session_manager=self.session_manager,
                mcp_tools=self.mcp_tools
            )
            self.agents[phone_number] = agent
            print(f"Created new agent for {phone_number}")

        return self.agents[phone_number]

    async def process_message(self, phone_number: str, message: str) -> str:
        """
        Process a message by routing to the appropriate agent

        Args:
            phone_number: User's phone number
            message: Message text

        Returns:
            Agent's response
        """
        agent = self.get_or_create_agent(phone_number)
        return await agent.process_message(message)

    async def stream_response(self, phone_number: str, message: str):
        """
        Stream response for a message

        Args:
            phone_number: User's phone number
            message: User's message text

        Yields:
            Response text chunks
        """
        agent = self.get_or_create_agent(phone_number)
        async for chunk in agent.stream_response(message):
            yield chunk

    def reset_conversation(self, phone_number: str):
        """Reset conversation for a user"""
        if phone_number in self.agents:
            self.agents[phone_number].reset_conversation()

    async def cleanup_agent(self, phone_number: str):
        """Clean up and remove an agent"""
        if phone_number in self.agents:
            await self.agents[phone_number].cleanup()
            del self.agents[phone_number]
            print(f"Cleaned up agent for {phone_number}")

    async def cleanup_all_agents(self):
        """Clean up all agents"""
        for phone_number in list(self.agents.keys()):
            await self.cleanup_agent(phone_number)
        print("All agents cleaned up")

    def get_active_agents_count(self) -> int:
        """Get number of active agents"""
        return len(self.agents)

    def cleanup_expired_sessions(self):
        """Cleanup expired sessions via session manager"""
        return self.session_manager.cleanup_expired_sessions()
