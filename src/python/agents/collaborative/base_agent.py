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
from .research_mixin import ResearchPlanningMixin

# Import telemetry utilities
from utils.telemetry import (
    trace_operation,
    measure_performance,
    log_event,
    log_metric,
    log_error
)


class BaseAgent(ABC, ResearchPlanningMixin):
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
        mcp_servers: Optional[Dict] = None,
        enable_research_planning: bool = True
    ):
        """
        Initialize base agent

        Args:
            agent_card: Agent's capabilities and metadata
            system_prompt: Claude system prompt for this agent
            mcp_servers: Available MCP servers
            enable_research_planning: Enable research & planning phase (default: True)
        """
        self.agent_card = agent_card
        self.system_prompt = system_prompt
        self.mcp_servers = mcp_servers or {}

        # Research & Planning feature flag
        self.enable_research_planning = enable_research_planning

        # Initialize Claude SDK
        self.claude_sdk = ClaudeSDK(
            available_mcp_servers=mcp_servers
        )

        # Register with A2A protocol
        a2a_protocol.register_agent(self)

        rp_status = "✅ Enabled" if enable_research_planning else "❌ Disabled"
        print(f"✨ {self.agent_card.name} initialized")
        print(f"   Role: {self.agent_card.role}")
        print(f"   Capabilities: {', '.join(self.agent_card.capabilities[:3])}...")
        print(f"   Research & Planning: {rp_status}")

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
        """Handle incoming task request with full telemetry tracking"""
        task = Task(**message.content)

        # Create main agent task span with comprehensive metadata
        with trace_operation(
            f"{self.agent_card.name}: execute_task",
            agent_id=self.agent_card.agent_id,
            agent_name=self.agent_card.name,
            agent_role=str(self.agent_card.role),
            task_id=task.task_id,
            task_description=task.description[:200] if len(task.description) > 200 else task.description,
            task_priority=task.priority,
            from_agent=task.from_agent,
            to_agent=task.to_agent,
            research_enabled=self.enable_research_planning
        ) as main_span:

            print(f"🎯 {self.agent_card.name} processing task: {task.task_id}")

            try:
                # Execute with or without research & planning based on feature flag
                if self.enable_research_planning:
                    result = await self.execute_task_with_research(task)
                else:
                    # Backward compatibility: direct execution
                    result = await self.execute_task(task)

                # Add result metadata to span
                if main_span and isinstance(result, dict):
                    main_span.set_attribute("result_status", "success")
                    main_span.set_attribute("result_size", len(str(result)))
                    main_span.set_attribute("result_type", type(result).__name__)

                    # Track specific result metrics based on result content
                    if 'design_spec' in result:
                        main_span.set_attribute("output_type", "design_specification")
                        if isinstance(result['design_spec'], dict):
                            main_span.set_attribute("components_designed", len(result['design_spec'].get('components', [])))
                    elif 'implementation' in result:
                        main_span.set_attribute("output_type", "implementation")
                        if isinstance(result['implementation'], dict):
                            main_span.set_attribute("files_generated", len(result['implementation'].get('files', [])))
                            main_span.set_attribute("framework", result['implementation'].get('framework', 'unknown'))
                    elif 'review' in result or 'score' in result:
                        main_span.set_attribute("output_type", "review")
                        main_span.set_attribute("review_score", result.get('score', 0))

                # Log completion event
                log_event(
                    "agent_task_completed",
                    agent_id=self.agent_card.agent_id,
                    agent_name=self.agent_card.name,
                    task_id=task.task_id,
                    result_status="success"
                )

                # Return task response
                return {
                    "task_id": task.task_id,
                    "status": "completed",
                    "result": result,
                    "agent_id": self.agent_card.agent_id,
                    "timestamp": message.timestamp
                }

            except Exception as e:
                # Track error in span
                if main_span:
                    main_span.set_attribute("result_status", "error")
                    main_span.set_attribute("error_type", type(e).__name__)
                    main_span.set_attribute("error_message", str(e))

                # Log error event
                log_error(
                    e,
                    context="agent_task_execution",
                    agent_id=self.agent_card.agent_id,
                    agent_name=self.agent_card.name,
                    task_id=task.task_id
                )

                # Re-raise to maintain error handling behavior
                raise

    async def execute_task_with_research(self, task: Task) -> Dict[str, Any]:
        """
        Execute task with research & planning phase - with full telemetry

        Workflow:
        1. Research Phase: Gather context and information (tracked)
        2. Planning Phase: Create detailed execution plan (tracked)
        3. Execution Phase: Execute with plan guidance (tracked)
        4. Return result

        Args:
            task: Task to execute

        Returns:
            Task execution result
        """
        print(f"🔬 [{self.agent_card.name}] Executing with research & planning")

        try:
            # Phase 1 & 2: Research and Plan (with telemetry)
            with trace_operation(
                "Research & Planning Phase",
                agent_id=self.agent_card.agent_id,
                agent_name=self.agent_card.name,
                task_id=task.task_id,
                phase="research_and_planning"
            ) as rp_span:
                research, plan = await self.research_and_plan(task)

                # Add research & planning metadata to span
                if rp_span:
                    rp_span.set_attribute("research_summary", research.get('research_summary', '')[:500])
                    rp_span.set_attribute("plan_summary", plan.get('plan_summary', '')[:500])
                    rp_span.set_attribute("research_topics_count", len(research.keys()) if isinstance(research, dict) else 0)
                    rp_span.set_attribute("plan_components_count", len(plan.keys()) if isinstance(plan, dict) else 0)

                # Log research completion
                log_event(
                    "agent_research_completed",
                    agent_id=self.agent_card.agent_id,
                    agent_name=self.agent_card.name,
                    task_id=task.task_id,
                    research_topics=len(research.keys()) if isinstance(research, dict) else 0
                )

            # Phase 3: Execute with plan (with telemetry)
            with trace_operation(
                "Execution Phase",
                agent_id=self.agent_card.agent_id,
                agent_name=self.agent_card.name,
                task_id=task.task_id,
                phase="execution",
                has_research=True,
                has_plan=True
            ) as exec_span:
                result = await self.execute_task_with_plan(task, research, plan)

                # Add execution metadata to span
                if exec_span and isinstance(result, dict):
                    exec_span.set_attribute("execution_completed", True)
                    exec_span.set_attribute("result_keys_count", len(result.keys()))

                    # Track type-specific metrics
                    if 'design_spec' in result:
                        exec_span.set_attribute("execution_type", "design")
                    elif 'implementation' in result:
                        exec_span.set_attribute("execution_type", "implementation")
                        if isinstance(result['implementation'], dict):
                            exec_span.set_attribute("files_count", len(result['implementation'].get('files', [])))

            # Add research & planning metadata to result
            if isinstance(result, dict):
                result['research_used'] = True
                result['research_summary'] = research.get('research_summary', 'Research completed')
                result['plan_summary'] = plan.get('plan_summary', 'Plan created')

            return result

        except NotImplementedError:
            # Agent hasn't implemented research & planning yet - fallback
            print(f"   ⚠️  Research & planning not implemented, using direct execution")
            log_event(
                "agent_research_fallback",
                agent_id=self.agent_card.agent_id,
                reason="not_implemented"
            )
            return await self.execute_task(task)

        except Exception as e:
            print(f"   ❌ Research & planning error: {e}, falling back to direct execution")
            log_error(
                e,
                context="agent_research_planning",
                agent_id=self.agent_card.agent_id,
                task_id=task.task_id
            )
            return await self.execute_task(task)

    async def handle_review_request(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle incoming review request with telemetry tracking"""
        artifact = message.content.get("artifact")

        # Create review span with metadata
        with trace_operation(
            f"{self.agent_card.name}: review_artifact",
            agent_id=self.agent_card.agent_id,
            agent_name=self.agent_card.name,
            agent_role=str(self.agent_card.role),
            review_type="design_fidelity"
        ) as review_span:

            print(f"🔍 {self.agent_card.name} reviewing artifact")

            try:
                # Review the artifact (implemented by subclass)
                review = await self.review_artifact(artifact)

                # Add review metrics to span
                if review_span and isinstance(review, dict):
                    review_span.set_attribute("review_completed", True)
                    review_span.set_attribute("review_score", review.get('score', 0))
                    review_span.set_attribute("review_approved", review.get('approved', False))
                    review_span.set_attribute("feedback_count", len(review.get('feedback', [])))
                    review_span.set_attribute("review_status", "approved" if review.get('approved') else "needs_improvement")

                # Log review completion event
                log_event(
                    "agent_review_completed",
                    agent_id=self.agent_card.agent_id,
                    agent_name=self.agent_card.name,
                    review_score=review.get('score', 0),
                    approved=review.get('approved', False)
                )

                # Log score as metric for analytics
                log_metric(
                    f"{self.agent_card.agent_id}.review_score",
                    float(review.get('score', 0)),
                    agent_id=self.agent_card.agent_id,
                    agent_name=self.agent_card.name
                )

                return review

            except Exception as e:
                # Track review error
                if review_span:
                    review_span.set_attribute("review_status", "error")
                    review_span.set_attribute("error_type", type(e).__name__)
                    review_span.set_attribute("error_message", str(e))

                log_error(
                    e,
                    context="agent_review",
                    agent_id=self.agent_card.agent_id,
                    agent_name=self.agent_card.name
                )

                # Re-raise to maintain error handling
                raise

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
