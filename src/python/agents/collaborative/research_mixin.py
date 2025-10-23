"""
Research & Planning Mixin for Agents
Adds mandatory research and planning phases before task execution

This mixin provides a structured approach to task execution:
1. Research Phase: Gather context, analyze requirements, explore alternatives
2. Planning Phase: Create detailed execution plan based on research
3. Execution Phase: Execute with plan guidance (implemented by agent)
"""

from typing import Dict, Any, Tuple
import json
import re


class ResearchPlanningMixin:
    """
    Mixin to add research & planning capabilities to agents

    Usage:
        class MyAgent(BaseAgent, ResearchPlanningMixin):
            def _build_research_prompt(self, task):
                # Agent-specific research prompt
                ...

            def _build_planning_prompt(self, task, research):
                # Agent-specific planning prompt
                ...

            async def execute_task_with_plan(self, task, research, plan):
                # Execute using research and plan
                ...
    """

    # Feature flag - can be toggled per agent or globally
    enable_research_planning = True

    async def research_and_plan(self, task: 'Task') -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Execute research and planning phases

        Args:
            task: Task to research and plan for

        Returns:
            Tuple of (research_findings, execution_plan)
        """
        print(f"🔬 [{self.agent_card.name}] Starting research & planning...")

        # Phase 1: Research
        print(f"   Phase 1/2: Research...")
        research = await self._research_phase(task)
        print(f"   ✓ Research complete")

        # Phase 2: Planning
        print(f"   Phase 2/2: Planning...")
        plan = await self._planning_phase(task, research)
        print(f"   ✓ Planning complete")

        return research, plan

    async def _research_phase(self, task: 'Task') -> Dict[str, Any]:
        """
        Research phase - gather context and information

        This phase focuses on:
        - Understanding requirements deeply
        - Gathering relevant context
        - Researching best practices
        - Identifying potential challenges
        - Exploring alternative approaches

        Args:
            task: Task to research

        Returns:
            Research findings as dict
        """
        # Build agent-specific research prompt
        research_prompt = self._build_research_prompt(task)

        try:
            # Execute research via Claude
            response = await self.claude_sdk.send_message(research_prompt)

            # Parse research findings
            findings = self._parse_research_findings(response)

            print(f"   📊 Research findings: {len(findings)} key insights")
            return findings

        except Exception as e:
            print(f"   ⚠️  Research error: {e}, using minimal research")
            # Fallback to minimal research
            return {
                "status": "minimal_research",
                "task_description": task.description,
                "error": str(e),
                "fallback": True
            }

    async def _planning_phase(self, task: 'Task', research: Dict[str, Any]) -> Dict[str, Any]:
        """
        Planning phase - create execution strategy

        This phase focuses on:
        - Synthesizing research findings
        - Defining clear success criteria
        - Breaking down into sub-tasks
        - Identifying risks and mitigation
        - Creating detailed execution plan

        Args:
            task: Task to plan for
            research: Research findings from previous phase

        Returns:
            Execution plan as dict
        """
        # Build agent-specific planning prompt
        planning_prompt = self._build_planning_prompt(task, research)

        try:
            # Execute planning via Claude
            response = await self.claude_sdk.send_message(planning_prompt)

            # Parse execution plan
            plan = self._parse_execution_plan(response)

            steps_count = len(plan.get('implementation_steps', []))
            print(f"   📋 Execution plan: {steps_count} steps defined")
            return plan

        except Exception as e:
            print(f"   ⚠️  Planning error: {e}, using basic plan")
            # Fallback to basic plan
            return {
                "status": "basic_plan",
                "task_description": task.description,
                "research_summary": research,
                "error": str(e),
                "fallback": True
            }

    def _parse_research_findings(self, response: str) -> Dict[str, Any]:
        """
        Parse research findings from Claude response

        Expects JSON format, but handles plain text as fallback

        Args:
            response: Claude's response

        Returns:
            Parsed research findings
        """
        try:
            # Try to extract JSON from response
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            elif response.strip().startswith('{'):
                return json.loads(response)
            else:
                # Plain text response - wrap it
                return {
                    "research_summary": response,
                    "format": "text",
                    "parsed": False
                }
        except Exception as e:
            print(f"   ⚠️  JSON parse error: {e}")
            return {
                "research_summary": response,
                "format": "text",
                "parse_error": str(e)
            }

    def _parse_execution_plan(self, response: str) -> Dict[str, Any]:
        """
        Parse execution plan from Claude response

        Expects JSON format, but handles plain text as fallback

        Args:
            response: Claude's response

        Returns:
            Parsed execution plan
        """
        try:
            # Try to extract JSON from response
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            elif response.strip().startswith('{'):
                return json.loads(response)
            else:
                # Plain text response - wrap it
                return {
                    "plan_summary": response,
                    "format": "text",
                    "parsed": False
                }
        except Exception as e:
            print(f"   ⚠️  JSON parse error: {e}")
            return {
                "plan_summary": response,
                "format": "text",
                "parse_error": str(e)
            }

    # Abstract methods - must be implemented by agent subclasses

    def _build_research_prompt(self, task: 'Task') -> str:
        """
        Build agent-specific research prompt

        This method must be implemented by each agent to provide
        role-specific research guidance.

        Args:
            task: Task to research

        Returns:
            Research prompt string

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError(
            f"{self.agent_card.name} must implement _build_research_prompt()"
        )

    def _build_planning_prompt(self, task: 'Task', research: Dict[str, Any]) -> str:
        """
        Build agent-specific planning prompt

        This method must be implemented by each agent to provide
        role-specific planning guidance.

        Args:
            task: Task to plan for
            research: Research findings

        Returns:
            Planning prompt string

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError(
            f"{self.agent_card.name} must implement _build_planning_prompt()"
        )

    async def execute_task_with_plan(
        self,
        task: 'Task',
        research: Dict[str, Any],
        plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute task guided by research and plan

        This method should be implemented by each agent to execute
        the task using the research findings and execution plan.

        Args:
            task: Task to execute
            research: Research findings
            plan: Execution plan

        Returns:
            Task execution result

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError(
            f"{self.agent_card.name} must implement execute_task_with_plan()"
        )


class ResearchPromptTemplates:
    """
    Common research prompt templates for different agent types

    These can be used as starting points for agent-specific research prompts
    """

    @staticmethod
    def generic_research_template(task_description: str, agent_role: str) -> str:
        """Generic research template for any agent"""
        return f"""You are conducting research as a {agent_role} for the following task:

**Task:** {task_description}

**Research Goals:**
1. Understand the requirements deeply
2. Identify key challenges and constraints
3. Research best practices and patterns
4. Explore alternative approaches
5. Identify potential risks and edge cases
6. Gather relevant context and information

**Output Format (JSON):**
{{
  "requirements_analysis": {{
    "core_requirements": ["requirement 1", "requirement 2"],
    "implicit_requirements": ["implicit 1", "implicit 2"],
    "constraints": ["constraint 1", "constraint 2"]
  }},
  "key_challenges": [
    {{"challenge": "...", "impact": "high|medium|low", "mitigation": "..."}}
  ],
  "best_practices": [
    {{"practice": "...", "reasoning": "...", "source": "..."}}
  ],
  "alternative_approaches": [
    {{"approach": "...", "pros": [...], "cons": [...], "recommended": true|false}}
  ],
  "potential_risks": [
    {{"risk": "...", "probability": "high|medium|low", "impact": "high|medium|low"}}
  ],
  "edge_cases": ["edge case 1", "edge case 2"],
  "context_needed": ["context 1", "context 2"],
  "estimated_complexity": "simple|moderate|complex|very complex",
  "time_estimate": "quick|normal|extended",
  "research_summary": "Brief summary of key findings"
}}

Be thorough. Quality over speed."""

    @staticmethod
    def planning_template(task_description: str, research: Dict[str, Any], agent_role: str) -> str:
        """Generic planning template for any agent"""
        return f"""You are creating a detailed execution plan as a {agent_role}.

**Task:** {task_description}

**Research Findings:**
{json.dumps(research, indent=2)}

**Planning Goals:**
1. Synthesize research findings into actionable plan
2. Define clear success criteria
3. Break down into concrete steps
4. Identify dependencies and order of operations
5. Plan for error handling and edge cases
6. Define validation checkpoints

**Output Format (JSON):**
{{
  "execution_strategy": "High-level approach based on research",
  "success_criteria": [
    {{"criterion": "...", "measurement": "...", "threshold": "..."}}
  ],
  "implementation_steps": [
    {{
      "step": 1,
      "action": "Specific action to take",
      "expected_output": "What this step should produce",
      "validation": "How to verify this step succeeded",
      "dependencies": ["step 0"],
      "estimated_time": "quick|normal|extended"
    }}
  ],
  "risk_mitigation": [
    {{"risk": "...", "mitigation_strategy": "...", "fallback_plan": "..."}}
  ],
  "edge_case_handling": [
    {{"edge_case": "...", "handling_strategy": "..."}}
  ],
  "quality_checkpoints": [
    {{"checkpoint": "...", "validation_method": "...", "threshold": "..."}}
  ],
  "rollback_plan": "What to do if execution fails",
  "estimated_complexity": "simple|moderate|complex",
  "plan_summary": "Brief summary of the execution plan"
}}

Create a clear, actionable, step-by-step plan."""


# Example usage patterns for agents:
"""
class MyAgent(BaseAgent, ResearchPlanningMixin):

    def _build_research_prompt(self, task: Task) -> str:
        # Option 1: Use generic template
        return ResearchPromptTemplates.generic_research_template(
            task_description=task.description,
            agent_role=self.agent_card.role
        )

        # Option 2: Customize for agent
        return f'''
        Custom research prompt for {self.agent_card.name}
        Task: {task.description}

        Research specific things for this agent...
        '''

    def _build_planning_prompt(self, task: Task, research: Dict) -> str:
        # Similar pattern
        return ResearchPromptTemplates.planning_template(
            task_description=task.description,
            research=research,
            agent_role=self.agent_card.role
        )

    async def execute_task_with_plan(self, task, research, plan):
        # Use research and plan to guide execution
        prompt = f'''
        Execute this task using the research and plan:

        Research: {research}
        Plan: {plan}
        Task: {task.description}

        Follow the plan precisely...
        '''
        result = await self.claude_sdk.send_message(prompt)
        return {"status": "completed", "result": result}
"""
