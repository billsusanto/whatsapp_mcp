"""
A2A Protocol Implementation
Handles agent-to-agent communication
"""

import asyncio
from typing import Optional, Callable, Dict
from .models import (
    A2AMessage, AgentCard, Task, TaskResponse,
    MessageType, TaskStatus
)


class A2AProtocol:
    """
    Handles agent-to-agent communication using A2A protocol

    This is a simplified in-memory implementation.
    For production with multiple servers, use HTTP/gRPC.
    """

    def __init__(self):
        self.agents: Dict[str, 'BaseAgent'] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.message_handlers: Dict[str, Callable] = {}

    def register_agent(self, agent: 'BaseAgent'):
        """Register an agent in the system"""
        self.agents[agent.agent_card.agent_id] = agent
        print(f"📝 A2A: Registered agent {agent.agent_card.name} ({agent.agent_card.agent_id})")

    def unregister_agent(self, agent_id: str):
        """Unregister an agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            print(f"📝 A2A: Unregistered agent {agent_id}")

    async def send_message(
        self,
        from_agent_id: str,
        to_agent_id: str,
        message_type: MessageType,
        content: dict
    ) -> Optional[dict]:
        """
        Send a message from one agent to another

        Args:
            from_agent_id: Sender agent ID
            to_agent_id: Recipient agent ID
            message_type: Type of message
            content: Message payload

        Returns:
            Response from recipient agent (if synchronous)
        """
        # Validate agents exist
        if from_agent_id not in self.agents:
            raise ValueError(f"Sender agent {from_agent_id} not registered")
        if to_agent_id not in self.agents:
            raise ValueError(f"Recipient agent {to_agent_id} not registered")

        # Create A2A message
        message = A2AMessage(
            from_agent=from_agent_id,
            to_agent=to_agent_id,
            message_type=message_type,
            content=content
        )

        # Log communication
        from_name = self.agents[from_agent_id].agent_card.name
        to_name = self.agents[to_agent_id].agent_card.name
        print(f"\n📨 A2A Message: {from_name} → {to_name}")
        print(f"   Type: {message_type.value}")
        print(f"   Message ID: {message.message_id}")

        # Deliver to recipient
        recipient = self.agents[to_agent_id]
        response = await recipient.receive_message(message)

        return response

    async def send_task(
        self,
        from_agent_id: str,
        to_agent_id: str,
        task: Task
    ) -> TaskResponse:
        """
        Send a task to another agent and wait for completion

        Args:
            from_agent_id: Requesting agent
            to_agent_id: Executing agent
            task: Task to execute

        Returns:
            TaskResponse with results
        """
        print(f"\n📋 A2A Task: {from_agent_id} → {to_agent_id}")
        print(f"   Task ID: {task.task_id}")
        print(f"   Description: {task.description[:80]}...")

        response = await self.send_message(
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            message_type=MessageType.TASK_REQUEST,
            content=task.model_dump()
        )

        return TaskResponse(**response)

    async def request_review(
        self,
        from_agent_id: str,
        to_agent_id: str,
        artifact: dict
    ) -> dict:
        """
        Request review of an artifact from another agent

        Args:
            from_agent_id: Agent requesting review
            to_agent_id: Agent performing review
            artifact: Work product to review

        Returns:
            Review feedback
        """
        print(f"\n🔍 A2A Review Request: {from_agent_id} → {to_agent_id}")

        response = await self.send_message(
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            message_type=MessageType.REVIEW_REQUEST,
            content={"artifact": artifact}
        )

        return response

    def get_agent_card(self, agent_id: str) -> Optional[AgentCard]:
        """Get agent card for discovery"""
        agent = self.agents.get(agent_id)
        return agent.agent_card if agent else None

    def discover_agents_by_role(self, role: str) -> list[AgentCard]:
        """Find all agents with a specific role"""
        return [
            agent.agent_card
            for agent in self.agents.values()
            if agent.agent_card.role == role
        ]


# Singleton instance for in-memory communication
a2a_protocol = A2AProtocol()
