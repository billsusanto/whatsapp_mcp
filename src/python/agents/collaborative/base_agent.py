"""
Base Agent Class
All specialized agents inherit from this
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sdk.claude_sdk import ClaudeSDK
from .models import AgentCard, A2AMessage, MessageType, Task, TaskResponse
from .a2a_protocol import a2a_protocol


class BaseAgent(ABC):
    """
    Base class for all collaborative agents

    Provides:
    - A2A communication
    - Claude SDK integration
    - Message handling
    """

    def __init__(
        self,
        agent_card: AgentCard,
        system_prompt: str,
        mcp_servers: Optional[Dict] = None
    ):
        """
        Initialize base agent

        Args:
            agent_card: Agent's capabilities and metadata
            system_prompt: Claude system prompt for this agent
            mcp_servers: Available MCP servers
        """
        self.agent_card = agent_card
        self.system_prompt = system_prompt
        self.mcp_servers = mcp_servers or {}

        # Initialize Claude SDK
        self.claude_sdk = ClaudeSDK(
            available_mcp_servers=mcp_servers
        )

        # Register with A2A protocol
        a2a_protocol.register_agent(self)

        print(f"✨ {self.agent_card.name} initialized")
        print(f"   Role: {self.agent_card.role}")
        print(f"   Capabilities: {', '.join(self.agent_card.capabilities[:3])}...")

    async def receive_message(self, message: A2AMessage) -> Dict[str, Any]:
        """
        Handle incoming A2A message
        Routes to appropriate handler based on message type

        Args:
            message: Incoming A2A message

        Returns:
            Response dict
        """
        # message.message_type is already a string due to use_enum_values = True
        print(f"📥 {self.agent_card.name} received: {message.message_type}")

        # Use string values as keys since message.message_type is serialized to string
        handlers = {
            "task_request": self.handle_task_request,
            "review_request": self.handle_review_request,
            "question": self.handle_question,
        }

        handler = handlers.get(message.message_type)
        if handler:
            return await handler(message)
        else:
            return {"error": f"Unsupported message type: {message.message_type}"}

    async def handle_task_request(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle incoming task request"""
        task = Task(**message.content)

        print(f"🎯 {self.agent_card.name} processing task: {task.task_id}")

        # Execute the task (implemented by subclass)
        result = await self.execute_task(task)

        # Return task response
        return {
            "task_id": task.task_id,
            "status": "completed",
            "result": result,
            "agent_id": self.agent_card.agent_id,
            "timestamp": message.timestamp
        }

    async def handle_review_request(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle incoming review request"""
        artifact = message.content.get("artifact")

        print(f"🔍 {self.agent_card.name} reviewing artifact")

        # Review the artifact (implemented by subclass)
        review = await self.review_artifact(artifact)

        return review

    async def handle_question(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle incoming question"""
        question = message.content.get("question")

        print(f"❓ {self.agent_card.name} answering question")

        # Answer using Claude
        answer = await self.claude_sdk.send_message(question)

        return {"answer": answer}

    @abstractmethod
    async def execute_task(self, task: Task) -> Any:
        """
        Execute a task - must be implemented by subclass

        Args:
            task: Task to execute

        Returns:
            Task result
        """
        pass

    @abstractmethod
    async def review_artifact(self, artifact: Any) -> Dict[str, Any]:
        """
        Review an artifact - must be implemented by subclass

        Args:
            artifact: Work product to review

        Returns:
            Review feedback
        """
        pass

    async def send_task_to(
        self,
        target_agent_id: str,
        task_description: str,
        priority: str = "medium"
    ) -> TaskResponse:
        """
        Send a task to another agent

        Args:
            target_agent_id: Agent to send task to
            task_description: What needs to be done
            priority: Task priority

        Returns:
            TaskResponse from target agent
        """
        task = Task(
            description=task_description,
            from_agent=self.agent_card.agent_id,
            to_agent=target_agent_id,
            priority=priority
        )

        response_dict = await a2a_protocol.send_task(
            from_agent_id=self.agent_card.agent_id,
            to_agent_id=target_agent_id,
            task=task
        )

        return TaskResponse(**response_dict)

    async def request_review_from(
        self,
        target_agent_id: str,
        artifact: Any
    ) -> Dict[str, Any]:
        """
        Request review from another agent

        Args:
            target_agent_id: Agent to review
            artifact: Work product to review

        Returns:
            Review feedback
        """
        return await a2a_protocol.request_review(
            from_agent_id=self.agent_card.agent_id,
            to_agent_id=target_agent_id,
            artifact=artifact
        )

    async def cleanup(self):
        """Clean up agent resources"""
        a2a_protocol.unregister_agent(self.agent_card.agent_id)
        await self.claude_sdk.close()
        print(f"🧹 {self.agent_card.name} cleaned up")
