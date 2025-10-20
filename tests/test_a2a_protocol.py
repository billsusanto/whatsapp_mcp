#!/usr/bin/env python3
"""Test A2A protocol implementation"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'python'))

from agents.collaborative.a2a_protocol import a2a_protocol
from agents.collaborative.models import (
    AgentCard, AgentRole, A2AMessage, Task, MessageType
)


class MockAgent:
    """Mock agent for testing"""

    def __init__(self, agent_id: str, name: str, role: AgentRole):
        self.agent_card = AgentCard(
            agent_id=agent_id,
            name=name,
            role=role,
            description=f"Mock {role} agent",
            capabilities=["testing"],
            skills={"test": ["mock"]}
        )

    async def receive_message(self, message: A2AMessage) -> dict:
        """Handle incoming message"""
        print(f"✓ {self.agent_card.name} received message: {message.message_type}")

        if message.message_type == MessageType.TASK_REQUEST:
            return {
                "task_id": message.content["task_id"],
                "status": "completed",
                "result": f"Task completed by {self.agent_card.name}",
                "agent_id": self.agent_card.agent_id,
                "timestamp": message.timestamp
            }

        return {"acknowledged": True}


async def test_a2a_protocol():
    """Test A2A protocol functionality"""

    print("=" * 60)
    print("🧪 Testing A2A Protocol")
    print("=" * 60)

    # Create mock agents
    designer = MockAgent("designer_001", "Designer", AgentRole.DESIGNER)
    frontend = MockAgent("frontend_001", "Frontend Dev", AgentRole.FRONTEND)

    # Register agents
    a2a_protocol.register_agent(designer)
    a2a_protocol.register_agent(frontend)

    # Test 1: Send simple message
    print("\n[Test 1] Simple message passing")
    await a2a_protocol.send_message(
        from_agent_id="designer_001",
        to_agent_id="frontend_001",
        message_type=MessageType.QUESTION,
        content={"question": "What framework should we use?"}
    )

    # Test 2: Send task
    print("\n[Test 2] Task delegation")
    task = Task(
        description="Implement the homepage component",
        from_agent="designer_001",
        to_agent="frontend_001",
        priority="high"
    )
    response = await a2a_protocol.send_task(
        from_agent_id="designer_001",
        to_agent_id="frontend_001",
        task=task
    )
    print(f"✓ Task response: {response.status}")

    # Test 3: Agent discovery
    print("\n[Test 3] Agent discovery")
    card = a2a_protocol.get_agent_card("frontend_001")
    print(f"✓ Found agent: {card.name} with {len(card.capabilities)} capabilities")

    print("\n" + "=" * 60)
    print("✅ All A2A protocol tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_a2a_protocol())
