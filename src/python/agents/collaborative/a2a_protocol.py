"""
A2A Protocol Implementation
Handles agent-to-agent communication
"""

import asyncio
import time
from typing import Optional, Callable, Dict
from .models import (
    A2AMessage, AgentCard, Task, TaskResponse,
    MessageType, TaskStatus
)
from utils.telemetry import trace_operation, log_event, log_metric, log_error


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

        # Log agent registration
        log_event("a2a.agent_registered",
                 agent_id=agent.agent_card.agent_id,
                 agent_name=agent.agent_card.name,
                 agent_role=agent.agent_card.role.value if hasattr(agent.agent_card.role, 'value') else str(agent.agent_card.role),
                 capabilities_count=len(agent.agent_card.capabilities),
                 total_agents=len(self.agents))

        print(f"📝 A2A: Registered agent {agent.agent_card.name} ({agent.agent_card.agent_id})")

    def unregister_agent(self, agent_id: str):
        """Unregister an agent"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]

            # Log agent unregistration
            log_event("a2a.agent_unregistered",
                     agent_id=agent_id,
                     agent_name=agent.agent_card.name,
                     total_agents=len(self.agents) - 1)

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
            error_msg = f"Sender agent {from_agent_id} not registered"
            log_error(ValueError(error_msg), "a2a_send_message",
                     from_agent_id=from_agent_id,
                     to_agent_id=to_agent_id,
                     error_type="sender_not_registered")
            raise ValueError(error_msg)

        if to_agent_id not in self.agents:
            error_msg = f"Recipient agent {to_agent_id} not registered"
            log_error(ValueError(error_msg), "a2a_send_message",
                     from_agent_id=from_agent_id,
                     to_agent_id=to_agent_id,
                     error_type="recipient_not_registered")
            raise ValueError(error_msg)

        # Create A2A message
        message = A2AMessage(
            from_agent=from_agent_id,
            to_agent=to_agent_id,
            message_type=message_type,
            content=content
        )

        # Get agent names for logging
        from_name = self.agents[from_agent_id].agent_card.name
        to_name = self.agents[to_agent_id].agent_card.name

        # Calculate payload size
        import json
        try:
            payload_size = len(json.dumps(content))
        except:
            payload_size = 0

        print(f"\n📨 A2A Message: {from_name} → {to_name}")
        print(f"   Type: {message_type.value}")
        print(f"   Message ID: {message.message_id}")

        # Trace message delivery with timing
        try:
            with trace_operation("a2a_send_message",
                               from_agent_id=from_agent_id,
                               to_agent_id=to_agent_id,
                               from_agent_name=from_name,
                               to_agent_name=to_name,
                               message_type=message_type.value,
                               message_id=message.message_id,
                               payload_size_bytes=payload_size) as span:

                # Track start time for latency calculation
                start_time = time.time()

                # Deliver to recipient
                recipient = self.agents[to_agent_id]
                response = await recipient.receive_message(message)

                # Calculate delivery latency
                delivery_latency_ms = (time.time() - start_time) * 1000

                # Track successful delivery
                span.set_attribute("delivery_latency_ms", delivery_latency_ms)
                span.set_attribute("delivery_status", "success")
                span.set_attribute("response_size_bytes", len(json.dumps(response)) if response else 0)

            # Log successful message delivery
            log_event("a2a.message_delivered",
                     from_agent_id=from_agent_id,
                     to_agent_id=to_agent_id,
                     from_agent_name=from_name,
                     to_agent_name=to_name,
                     message_type=message_type.value,
                     message_id=message.message_id,
                     delivery_latency_ms=delivery_latency_ms,
                     payload_size_bytes=payload_size,
                     success=True)

            # Track latency metrics
            log_metric("a2a.message_delivery_latency_ms", delivery_latency_ms)
            log_metric("a2a.message_payload_size_bytes", payload_size)
            log_metric("a2a.messages_delivered", 1)

            return response

        except Exception as e:
            # Log failed delivery
            log_error(e, "a2a_send_message",
                     from_agent_id=from_agent_id,
                     to_agent_id=to_agent_id,
                     message_type=message_type.value,
                     message_id=message.message_id)

            log_event("a2a.message_delivery_failed",
                     from_agent_id=from_agent_id,
                     to_agent_id=to_agent_id,
                     message_type=message_type.value,
                     message_id=message.message_id,
                     error=str(e))

            log_metric("a2a.messages_failed", 1)

            # Re-raise the exception
            raise

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

        # Log task send start
        log_event("a2a.task_sent",
                 from_agent_id=from_agent_id,
                 to_agent_id=to_agent_id,
                 task_id=task.task_id,
                 task_description_length=len(task.description),
                 task_priority=task.priority if hasattr(task, 'priority') else None)

        # Track task execution time
        start_time = time.time()

        try:
            response = await self.send_message(
                from_agent_id=from_agent_id,
                to_agent_id=to_agent_id,
                message_type=MessageType.TASK_REQUEST,
                content=task.model_dump()
            )

            # Calculate total task execution time
            execution_time_ms = (time.time() - start_time) * 1000

            # Parse response
            task_response = TaskResponse(**response)

            # Log task completion
            log_event("a2a.task_completed",
                     from_agent_id=from_agent_id,
                     to_agent_id=to_agent_id,
                     task_id=task.task_id,
                     execution_time_ms=execution_time_ms,
                     status=task_response.status.value if hasattr(task_response.status, 'value') else str(task_response.status),
                     success=task_response.status == TaskStatus.COMPLETED)

            # Track task execution metrics
            log_metric("a2a.task_execution_time_ms", execution_time_ms)
            log_metric("a2a.tasks_completed", 1)

            return task_response

        except Exception as e:
            # Log task failure
            execution_time_ms = (time.time() - start_time) * 1000

            log_error(e, "a2a_send_task",
                     from_agent_id=from_agent_id,
                     to_agent_id=to_agent_id,
                     task_id=task.task_id,
                     execution_time_ms=execution_time_ms)

            log_event("a2a.task_failed",
                     from_agent_id=from_agent_id,
                     to_agent_id=to_agent_id,
                     task_id=task.task_id,
                     execution_time_ms=execution_time_ms,
                     error=str(e))

            log_metric("a2a.tasks_failed", 1)

            raise

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

        # Calculate artifact size
        import json
        try:
            artifact_size = len(json.dumps(artifact))
        except:
            artifact_size = 0

        # Log review request
        log_event("a2a.review_requested",
                 from_agent_id=from_agent_id,
                 to_agent_id=to_agent_id,
                 artifact_size_bytes=artifact_size,
                 artifact_type=artifact.get('type', 'unknown') if isinstance(artifact, dict) else 'unknown')

        # Track review time
        start_time = time.time()

        try:
            response = await self.send_message(
                from_agent_id=from_agent_id,
                to_agent_id=to_agent_id,
                message_type=MessageType.REVIEW_REQUEST,
                content={"artifact": artifact}
            )

            # Calculate review time
            review_time_ms = (time.time() - start_time) * 1000

            # Extract review score if available
            review_score = None
            review_approved = None
            if isinstance(response, dict):
                review_score = response.get('score') or response.get('overall_score')
                review_approved = response.get('approved')

            # Log review completion
            log_event("a2a.review_completed",
                     from_agent_id=from_agent_id,
                     to_agent_id=to_agent_id,
                     review_time_ms=review_time_ms,
                     review_score=review_score,
                     review_approved=review_approved)

            # Track review metrics
            log_metric("a2a.review_time_ms", review_time_ms)
            log_metric("a2a.reviews_completed", 1)

            if review_score is not None:
                log_metric("a2a.review_score", review_score)

            return response

        except Exception as e:
            # Log review failure
            review_time_ms = (time.time() - start_time) * 1000

            log_error(e, "a2a_request_review",
                     from_agent_id=from_agent_id,
                     to_agent_id=to_agent_id,
                     review_time_ms=review_time_ms)

            log_event("a2a.review_failed",
                     from_agent_id=from_agent_id,
                     to_agent_id=to_agent_id,
                     review_time_ms=review_time_ms,
                     error=str(e))

            log_metric("a2a.reviews_failed", 1)

            raise

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
