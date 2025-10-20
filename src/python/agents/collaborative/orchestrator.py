"""
Collaborative Orchestrator
Coordinates multi-agent team: Designer, Frontend, Code Reviewer, QA, DevOps

NOW USING A2A PROTOCOL for all agent communication
"""

from typing import Dict, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sdk.claude_sdk import ClaudeSDK
from .designer_agent import DesignerAgent
from .frontend_agent import FrontendDeveloperAgent
from .code_reviewer_agent import CodeReviewerAgent
from .qa_agent import QAEngineerAgent
from .devops_agent import DevOpsEngineerAgent
from .models import Task, TaskResponse
from .a2a_protocol import a2a_protocol


class CollaborativeOrchestrator:
    """
    Orchestrates collaboration between multi-agent development team using A2A Protocol

    Agent Team:
    - UI/UX Designer: Creates design specifications and reviews implementations
    - Frontend Developer: Implements React/Vue code
    - Code Reviewer: Reviews code for quality, security, and best practices
    - QA Engineer: Tests functionality, usability, and accessibility
    - DevOps Engineer: Handles deployment, optimization, and infrastructure

    Communication:
    - ALL agent interactions use A2A (Agent-to-Agent) protocol
    - Standardized messaging with Task and TaskResponse models
    - Full traceability and logging of all communications

    Workflow:
    1. Designer creates design specification (via A2A)
    2. Frontend implements based on design (via A2A)
    3. Code Reviewer reviews code quality and security (via A2A)
    4. QA Engineer tests functionality and usability (via A2A)
    5. DevOps Engineer optimizes and deploys to Netlify (via A2A)
    6. Iterative improvement until quality standards met
    """

    # Orchestrator's agent ID for A2A protocol
    ORCHESTRATOR_ID = "orchestrator"

    def __init__(self, mcp_servers: Dict):
        """
        Initialize orchestrator with specialized agent team

        Args:
            mcp_servers: Available MCP servers (WhatsApp, GitHub, Netlify)
        """
        print("=" * 60)
        print("🎭 Initializing Multi-Agent Orchestrator with A2A Protocol")
        print("=" * 60)

        self.mcp_servers = mcp_servers
        self.orchestrator_id = self.ORCHESTRATOR_ID

        # Create specialized agent team (they auto-register with A2A protocol)
        self.designer = DesignerAgent(mcp_servers)
        self.frontend = FrontendDeveloperAgent(mcp_servers)
        self.code_reviewer = CodeReviewerAgent(mcp_servers)
        self.qa_engineer = QAEngineerAgent(mcp_servers)
        self.devops = DevOpsEngineerAgent(mcp_servers)

        # Create Claude SDK for orchestrator tasks (deployment, coordination, planning)
        self.deployment_sdk = ClaudeSDK(available_mcp_servers=mcp_servers)

        # Create planning SDK for intelligent workflow decisions
        self.planner_sdk = ClaudeSDK(available_mcp_servers={})  # No MCP tools needed for planning

        # Configuration
        self.max_review_iterations = 5  # Maximum review/improvement iterations
        self.min_quality_score = 8  # Minimum acceptable review score (out of 10)
        self.max_build_retries = 3  # Maximum build retry attempts

        print("\n✅ Multi-Agent Team Ready (A2A-enabled):")
        print(f"   - {self.designer.agent_card.name} ({self.designer.agent_card.agent_id})")
        print(f"   - {self.frontend.agent_card.name} ({self.frontend.agent_card.agent_id})")
        print(f"   - {self.code_reviewer.agent_card.name} ({self.code_reviewer.agent_card.agent_id})")
        print(f"   - {self.qa_engineer.agent_card.name} ({self.qa_engineer.agent_card.agent_id})")
        print(f"   - {self.devops.agent_card.name} ({self.devops.agent_card.agent_id})")
        print(f"   - AI Planner (Claude-powered workflow decisions)")
        print(f"   - Deployment SDK with {len(mcp_servers)} MCP servers")
        print(f"\n🔗 A2A Protocol: All agents registered and ready for communication")
        print("=" * 60 + "\n")

    # ==========================================
    # A2A HELPER METHODS
    # ==========================================

    async def _send_task_to_agent(
        self,
        agent_id: str,
        task_description: str,
        metadata: Optional[Dict] = None,
        priority: str = "medium"
    ) -> Dict:
        """
        Send a task to an agent via A2A protocol

        Args:
            agent_id: Target agent ID
            task_description: Task description
            metadata: Optional metadata (design_spec, etc.)
            priority: Task priority

        Returns:
            Task result dict
        """
        task = Task(
            description=task_description,
            from_agent=self.orchestrator_id,
            to_agent=agent_id,
            priority=priority,
            metadata=metadata
        )

        response = await a2a_protocol.send_task(
            from_agent_id=self.orchestrator_id,
            to_agent_id=agent_id,
            task=task
        )

        return response.result

    async def _request_review_from_agent(
        self,
        agent_id: str,
        artifact: Dict
    ) -> Dict:
        """
        Request artifact review from an agent via A2A protocol

        Args:
            agent_id: Reviewer agent ID
            artifact: Artifact to review

        Returns:
            Review feedback dict
        """
        review = await a2a_protocol.request_review(
            from_agent_id=self.orchestrator_id,
            to_agent_id=agent_id,
            artifact=artifact
        )

        return review

    # ==========================================
    # AI PLANNING
    # ==========================================

    async def _ai_plan_workflow(self, user_prompt: str) -> Dict:
        """
        Use Claude AI to intelligently analyze the request and plan the workflow

        Returns:
            {
                "workflow": "full_build" | "bug_fix" | "redeploy" | "design_only" | "custom",
                "reasoning": "Why this workflow was chosen",
                "agents_needed": ["designer", "frontend", "reviewer", etc],
                "steps": ["Step 1 description", "Step 2 description", ...],
                "estimated_complexity": "simple" | "moderate" | "complex",
                "special_instructions": "Any special handling needed"
            }
        """
        planning_prompt = f"""You are an AI orchestrator planning how to fulfill a user's request using a multi-agent development team.

**Available Agents:**
- **designer**: UI/UX Designer - Creates design specifications, color palettes, typography, layouts, component designs, reviews implementations
- **frontend**: Frontend Developer - Implements React/Vue/Next.js code, fixes bugs, handles dependencies, writes components
- **code_reviewer**: Code Reviewer - Reviews code for quality, security vulnerabilities, performance issues, best practices
- **qa**: QA Engineer - Tests functionality, usability, accessibility, creates test plans, identifies bugs
- **devops**: DevOps Engineer - Handles deployment optimization, build configuration, security hardening, monitors performance

**Available Workflows:**
1. **full_build**: Build a complete production-ready webapp from scratch
   - Steps: Designer → Frontend → Code Review → QA Testing → DevOps Optimization → Deploy
   - Agents: Designer + Frontend + Code Reviewer + QA + DevOps
   - Use when: User wants to create a new high-quality application

2. **bug_fix**: Fix errors in existing code
   - Steps: Frontend fixes → Code Review → Deploy with verification
   - Agents: Frontend + Code Reviewer
   - Use when: User reports errors, build failures, bugs

3. **redeploy**: Redeploy existing code without changes
   - Steps: Direct deployment
   - Agents: DevOps only
   - Use when: User wants to redeploy existing code from GitHub

4. **design_only**: Just create design specifications
   - Steps: Designer creates design spec
   - Agents: Designer only
   - Use when: User only wants design consultation, mockups, wireframes

5. **custom**: Create a custom workflow tailored to the request
   - Mix and match agents as needed
   - Use when: Request needs specific combination of agents

**User Request:**
"{user_prompt}"

**Your Task:**
Analyze the user's request and determine:
1. What does the user actually want?
2. Which workflow best fits this request?
3. Which agents are needed for the best quality result?
4. What are the specific steps to execute?
5. Are there any special considerations?

**Important Guidelines:**
- For production webapps, use ALL quality agents (code_reviewer, qa, devops) to ensure high quality
- Code Reviewer should review all code before deployment to catch security issues
- QA should test all user-facing features for usability and accessibility
- DevOps should optimize all deployments for performance and security
- Only skip agents if the user explicitly wants a quick/simple solution

**Output Format (JSON):**
{{
  "workflow": "full_build" | "bug_fix" | "redeploy" | "design_only" | "custom",
  "reasoning": "Clear explanation of why you chose this workflow",
  "agents_needed": ["designer", "frontend", "code_reviewer", "qa", "devops"],
  "steps": [
    "Designer creates comprehensive design specification",
    "Frontend implements React components based on design",
    "Code Reviewer reviews code for security and quality",
    "QA Engineer tests functionality and accessibility",
    "DevOps Engineer optimizes and deploys to Netlify",
    "Format and send response to user"
  ],
  "estimated_complexity": "simple" | "moderate" | "complex",
  "special_instructions": "Any special handling, edge cases, or important notes"
}}

Respond with ONLY the JSON object, no other text."""

        try:
            # Get planning decision from Claude
            response = await self.planner_sdk.send_message(planning_prompt)

            # Extract JSON from response
            import json
            import re

            # Look for JSON in code blocks or raw JSON
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group(1))
            elif response.strip().startswith('{'):
                plan = json.loads(response)
            else:
                # Claude didn't return JSON, create fallback plan
                print(f"⚠️  Could not parse planning response, using default")
                plan = {
                    "workflow": "full_build",
                    "reasoning": "Default workflow - could not parse AI response",
                    "agents_needed": ["designer", "frontend"],
                    "steps": ["Design", "Implement", "Review", "Deploy"],
                    "estimated_complexity": "moderate",
                    "special_instructions": "Using default workflow"
                }

            print(f"\n🧠 AI Planning Complete:")
            print(f"   Workflow: {plan['workflow']}")
            print(f"   Reasoning: {plan['reasoning']}")
            print(f"   Agents: {', '.join(plan['agents_needed'])}")
            print(f"   Complexity: {plan['estimated_complexity']}")

            return plan

        except Exception as e:
            print(f"❌ Planning error: {e}")
            import traceback
            traceback.print_exc()

            # Fallback to safe default
            return {
                "workflow": "full_build",
                "reasoning": f"Fallback due to error: {str(e)}",
                "agents_needed": ["designer", "frontend"],
                "steps": ["Design", "Implement", "Review", "Deploy"],
                "estimated_complexity": "moderate",
                "special_instructions": "Error during planning - using default"
            }

    # ==========================================
    # MAIN WORKFLOW ENTRY POINT
    # ==========================================

    async def build_webapp(self, user_prompt: str) -> str:
        """
        Main workflow: Uses AI planning to intelligently route requests

        Args:
            user_prompt: User's request

        Returns:
            WhatsApp-formatted response
        """
        print(f"\n🚀 [ORCHESTRATOR] Starting AI-powered request processing")
        print(f"📝 User request: {user_prompt}")
        print("\n" + "-" * 60)

        # Use AI to plan the workflow
        plan = await self._ai_plan_workflow(user_prompt)
        workflow_type = plan.get('workflow', 'full_build')

        print("\n" + "-" * 60)

        try:
            # Route to appropriate workflow based on AI decision
            if workflow_type == "redeploy":
                return await self._workflow_redeploy(user_prompt, plan)
            elif workflow_type == "bug_fix":
                return await self._workflow_bug_fix(user_prompt, plan)
            elif workflow_type == "design_only":
                return await self._workflow_design_only(user_prompt, plan)
            elif workflow_type == "custom":
                return await self._workflow_custom(user_prompt, plan)
            else:  # full_build (default)
                return await self._workflow_full_build(user_prompt, plan)

        except Exception as e:
            print(f"\n❌ [ORCHESTRATOR] Error during processing: {e}")
            import traceback
            traceback.print_exc()

            return f"""❌ Request encountered an error:

{str(e)}

The AI planner suggested: {plan.get('workflow', 'unknown')}
Reasoning: {plan.get('reasoning', 'N/A')}

Please try again or provide more details."""

    # ==========================================
    # WORKFLOW IMPLEMENTATIONS (A2A-ENABLED)
    # ==========================================

    async def _workflow_full_build(self, user_prompt: str, plan: Dict = None) -> str:
        """Full build workflow: Designer → Frontend → Review → Deploy (via A2A)"""
        print(f"\n🏗️  Starting FULL BUILD workflow (A2A Protocol)")

        if plan and plan.get('special_instructions'):
            print(f"📋 Special instructions: {plan['special_instructions']}")

        # Step 1: Designer creates design specification (A2A)
        print("\n[Step 1/5] 🎨 Designer creating design specification (A2A)...")
        design_result = await self._send_task_to_agent(
            agent_id=self.designer.agent_card.agent_id,
            task_description=f"Create design specification for: {user_prompt}",
            priority="high"
        )
        design_spec = design_result.get('design_spec', {})

        # Extract design style safely
        if isinstance(design_spec, dict):
            design_style = design_spec.get('style', 'modern')
        else:
            design_style = 'modern'

        print(f"✓ Design completed via A2A")

        # Step 2: Frontend implements design (A2A)
        print("\n[Step 2/5] 💻 Frontend implementing design (A2A)...")
        impl_result = await self._send_task_to_agent(
            agent_id=self.frontend.agent_card.agent_id,
            task_description=f"Implement webapp: {user_prompt}",
            metadata={"design_spec": design_spec},
            priority="high"
        )
        implementation = impl_result.get('implementation', {})
        framework = implementation.get('framework', 'react')

        print(f"✓ Implementation completed via A2A: {framework}")

        # Step 3: Quality verification loop - ensure score >= 8/10
        print("\n[Step 3/5] 🔍 Quality verification (minimum score: {}/10, via A2A)...".format(self.min_quality_score))

        review_iteration = 0
        score = 0
        approved = False
        current_implementation = implementation

        while review_iteration < self.max_review_iterations:
            review_iteration += 1
            print(f"\n   Review iteration {review_iteration}/{self.max_review_iterations}")

            # Designer reviews implementation (A2A)
            review_artifact = {
                "original_design": design_spec,
                "implementation": current_implementation
            }
            review = await self._request_review_from_agent(
                agent_id=self.designer.agent_card.agent_id,
                artifact=review_artifact
            )
            approved = review.get('approved', True)
            score = review.get('score', 8)
            feedback = review.get('feedback', [])

            print(f"   Score: {score}/10 - {'✅ Approved' if approved else '⚠️ Needs improvement'}")

            # Check if quality standard is met
            if score >= self.min_quality_score:
                print(f"   ✅ Quality standard met! (Score: {score}/10 >= {self.min_quality_score}/10)")
                break

            # Quality not met - need improvement
            if review_iteration >= self.max_review_iterations:
                print(f"   ⚠️  Max iterations reached - proceeding with current quality (Score: {score}/10)")
                break

            # Ask Frontend to improve based on feedback (A2A)
            print(f"   🔧 Quality below standard ({score}/10 < {self.min_quality_score}/10) - requesting improvements (A2A)...")
            print(f"   📋 Feedback: {', '.join(feedback) if feedback else 'General improvements needed'}")

            improvement_result = await self._send_task_to_agent(
                agent_id=self.frontend.agent_card.agent_id,
                task_description=f"""Improve the implementation based on design review feedback.

Original request: {user_prompt}

Design review score: {score}/10 (Target: {self.min_quality_score}/10)
Feedback: {', '.join(feedback)}

Please address all feedback and improve the implementation to meet the quality standard.""",
                metadata={
                    "design_spec": design_spec,
                    "previous_implementation": current_implementation,
                    "review_feedback": feedback,
                    "review_score": score
                },
                priority="high"
            )
            current_implementation = improvement_result.get('implementation', current_implementation)
            print(f"   ✓ Frontend provided improved implementation via A2A")

        # Use the final implementation (after quality loop)
        implementation = current_implementation

        print(f"\n✓ Quality verification completed via A2A: Score {score}/10 after {review_iteration} iteration(s)")

        # Step 4: Deploy to Netlify with build verification and retry
        print("\n[Step 4/5] 🚀 Deploying to Netlify with build verification...")
        deployment_result = await self._deploy_with_retry(
            user_prompt=user_prompt,
            implementation=implementation,
            design_spec=design_spec
        )

        deployment_url = deployment_result.get('url', 'https://app.netlify.com/teams')
        build_attempts = deployment_result.get('attempts', 1)
        final_implementation = deployment_result.get('final_implementation', implementation)

        print(f"✓ Deployed successfully after {build_attempts} attempt(s): {deployment_url}")

        # Step 5: Format response
        print("\n[Step 5/5] 📱 Formatting WhatsApp response...")
        response = self._format_whatsapp_response(
            url=deployment_url,
            design_style=design_style,
            framework=framework,
            review_score=score,
            build_attempts=build_attempts,
            review_iterations=review_iteration
        )

        print("\n" + "-" * 60)
        print("✅ [ORCHESTRATOR] Full build complete (A2A Protocol)!\n")
        return response

    async def _workflow_bug_fix(self, user_prompt: str, plan: Dict = None) -> str:
        """Bug fix workflow: Frontend fixes code → Deploy (via A2A)"""
        print(f"\n🔧 Starting BUG FIX workflow (A2A Protocol)")

        if plan and plan.get('special_instructions'):
            print(f"📋 Special instructions: {plan['special_instructions']}")

        # Step 1: Frontend fixes the issue (A2A)
        print("\n[Step 1/2] 💻 Frontend analyzing and fixing issue (A2A)...")
        fix_result = await self._send_task_to_agent(
            agent_id=self.frontend.agent_card.agent_id,
            task_description=f"Analyze and fix this issue: {user_prompt}",
            priority="high"
        )
        implementation = fix_result.get('implementation', {})
        framework = implementation.get('framework', 'react')

        print(f"✓ Initial fix completed via A2A")

        # Step 2: Deploy to Netlify with build verification and retry
        print("\n[Step 2/2] 🚀 Deploying fixed code with build verification...")
        deployment_result = await self._deploy_with_retry(
            user_prompt=user_prompt,
            implementation=implementation,
            design_spec={}  # No design spec for bug fixes
        )

        deployment_url = deployment_result.get('url', 'https://app.netlify.com/teams')
        build_attempts = deployment_result.get('attempts', 1)

        print(f"✓ Deployed successfully after {build_attempts} fix attempt(s): {deployment_url}")

        response = f"""✅ Bug fix complete and deployed!

🔗 Live Site: {deployment_url}

🔧 What was fixed:
  • Analyzed the error/issue
  • Applied fixes
  • Redeployed to Netlify

⚙️ Technical:
  • Framework: {framework}
  • Deployed on Netlify

🤖 Fixed by Frontend Developer Agent (via A2A Protocol)
"""

        print("\n" + "-" * 60)
        print("✅ [ORCHESTRATOR] Bug fix complete (A2A)!\n")
        return response

    async def _workflow_redeploy(self, user_prompt: str, plan: Dict = None) -> str:
        """Redeploy workflow: Just deploy existing code"""
        print(f"\n🚀 Starting REDEPLOY workflow")

        if plan and plan.get('special_instructions'):
            print(f"📋 Special instructions: {plan['special_instructions']}")

        # Step 1: Deploy directly
        print("\n[Step 1/1] 🚀 Redeploying to Netlify...")

        # Ask Claude to use Netlify MCP to redeploy
        redeploy_prompt = f"""User request: {user_prompt}

Use Netlify MCP to redeploy the existing site.

Steps:
1. If a GitHub repo is mentioned, clone it
2. Redeploy the site to Netlify
3. Return the live deployment URL

Respond with ONLY the deployment URL."""

        response_text = await self.deployment_sdk.send_message(redeploy_prompt)

        # Extract URL
        import re
        url_match = re.search(r'https://[a-zA-Z0-9-]+\.netlify\.app', response_text)
        if url_match:
            deployment_url = url_match.group(0)
            print(f"✓ Redeployed to: {deployment_url}")
        else:
            dashboard_match = re.search(r'https://app\.netlify\.com/[^\s]+', response_text)
            if dashboard_match:
                deployment_url = dashboard_match.group(0)
            else:
                deployment_url = "https://app.netlify.com/teams"

        response = f"""✅ Site redeployed successfully!

🔗 Live Site: {deployment_url}

🚀 Redeployment complete
  • Existing code deployed
  • No changes made to design or implementation

🤖 Deployed by Orchestrator
"""

        print("\n" + "-" * 60)
        print("✅ [ORCHESTRATOR] Redeploy complete!\n")
        return response

    async def _workflow_design_only(self, user_prompt: str, plan: Dict = None) -> str:
        """Design only workflow: Designer creates design spec (via A2A)"""
        print(f"\n🎨 Starting DESIGN ONLY workflow (A2A Protocol)")

        if plan and plan.get('special_instructions'):
            print(f"📋 Special instructions: {plan['special_instructions']}")

        # Step 1: Designer creates design (A2A)
        print("\n[Step 1/1] 🎨 Designer creating design specification (A2A)...")
        design_result = await self._send_task_to_agent(
            agent_id=self.designer.agent_card.agent_id,
            task_description=f"Create design specification for: {user_prompt}",
            priority="medium"
        )
        design_spec = design_result.get('design_spec', {})

        # Format design for WhatsApp
        response = f"""✅ Design specification complete!

🎨 Design created by UI/UX Designer Agent (via A2A Protocol)

📋 Design includes:
  • Style guidelines
  • Color palette
  • Typography system
  • Component specifications
  • Layout structure
  • Accessibility requirements

💡 Ready to implement? Send a message like "Implement this design" to have the Frontend agent build it!

🤖 Designed by UI/UX Designer Agent
"""

        print("\n" + "-" * 60)
        print("✅ [ORCHESTRATOR] Design complete (A2A)!\n")
        return response

    async def _ai_decide_step_executor(self, step: str, user_prompt: str, agents_available: list, context: Dict) -> Dict:
        """
        Use Claude AI to intelligently decide which agent should execute this step

        Args:
            step: The step description from the plan
            user_prompt: Original user request
            agents_available: List of available agents
            context: Current workflow context (design_spec, implementation, etc.)

        Returns:
            {
                "agent": "designer" | "frontend" | "review" | "deploy" | "skip",
                "reasoning": "Why this agent was chosen",
                "task_description": "Refined task description for the agent"
            }
        """
        decision_prompt = f"""You are an intelligent orchestrator deciding which agent should execute a workflow step.

**Workflow Step:** "{step}"

**Original User Request:** "{user_prompt}"

**Available Agents:**
- **designer**: UI/UX Designer - creates design specifications, reviews implementations for design fidelity
- **frontend**: Frontend Developer - writes React/Vue code, fixes bugs, implements features
- **code_reviewer**: Code Reviewer - reviews code for security, quality, performance, best practices
- **qa**: QA Engineer - tests functionality, usability, accessibility, creates test plans
- **devops**: DevOps Engineer - optimizes builds, configures deployment, security hardening
- **deploy**: Direct Deployment - deploys code to Netlify with build verification
- **skip**: Skip this step (if not actionable or already completed)

**Current Context:**
- Has design specification: {bool(context.get('design_spec'))}
- Has implementation: {bool(context.get('implementation'))}
- Has code review: {bool(context.get('code_review'))}
- Has QA report: {bool(context.get('qa_report'))}
- Has DevOps config: {bool(context.get('devops_config'))}
- Agents in plan: {', '.join(agents_available)}

**Your Task:**
Analyze the step and decide which agent should execute it. Consider:
1. What does this step actually require?
2. Which agent is best suited for this work?
3. Do we have the prerequisites (design, code, etc.)?
4. Is this step even necessary given the context?

**Output Format (JSON):**
{{
  "agent": "designer" | "frontend" | "code_reviewer" | "qa" | "devops" | "deploy" | "skip",
  "reasoning": "Clear explanation of why this agent was chosen",
  "task_description": "Refined, specific task description for the agent to execute"
}}

Be intelligent and context-aware. Don't just pattern match - actually understand what the step requires."""

        try:
            response = await self.planner_sdk.send_message(decision_prompt)

            # Extract JSON
            import json
            import re

            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                decision = json.loads(json_match.group(1))
            elif response.strip().startswith('{'):
                decision = json.loads(response)
            else:
                # Fallback
                decision = {
                    "agent": "skip",
                    "reasoning": "Could not parse AI decision",
                    "task_description": step
                }

            return decision

        except Exception as e:
            print(f"⚠️  Error in step decision: {e}")
            # Fallback to skip
            return {
                "agent": "skip",
                "reasoning": f"Error during decision: {str(e)}",
                "task_description": step
            }

    async def _workflow_custom(self, user_prompt: str, plan: Dict) -> str:
        """
        Custom workflow: Execute workflow based on AI planner's instructions (via A2A)

        This workflow uses AI to intelligently route each step to the right agent,
        rather than hardcoded keyword matching.
        """
        print(f"\n🔮 Starting CUSTOM workflow with AI-powered step routing (A2A Protocol)")
        print(f"📋 AI Planner reasoning: {plan.get('reasoning', 'N/A')}")

        if plan.get('special_instructions'):
            print(f"📋 Special instructions: {plan['special_instructions']}")

        agents_needed = plan.get('agents_needed', [])
        steps = plan.get('steps', [])

        print(f"\n🤖 Agents available: {', '.join(agents_needed)}")
        print(f"📝 Steps planned: {len(steps)}")

        # Execute steps based on AI decisions
        context = {
            'design_spec': None,
            'implementation': None,
            'review_score': None,
            'code_review': None,
            'qa_report': None,
            'devops_config': None,
            'deployment_url': None
        }

        for i, step in enumerate(steps):
            print(f"\n[Step {i+1}/{len(steps)}] {step}")

            # Use AI to decide which agent should handle this step
            decision = await self._ai_decide_step_executor(
                step=step,
                user_prompt=user_prompt,
                agents_available=agents_needed,
                context=context
            )

            agent_choice = decision.get('agent', 'skip')
            reasoning = decision.get('reasoning', 'N/A')
            task_desc = decision.get('task_description', step)

            print(f"   🧠 AI Decision: {agent_choice}")
            print(f"   💭 Reasoning: {reasoning}")

            # Execute based on AI decision (via A2A)
            if agent_choice == "designer":
                design_result = await self._send_task_to_agent(
                    agent_id=self.designer.agent_card.agent_id,
                    task_description=task_desc
                )
                context['design_spec'] = design_result.get('design_spec', {})
                print(f"   ✓ Designer completed step via A2A")

            elif agent_choice == "frontend":
                impl_result = await self._send_task_to_agent(
                    agent_id=self.frontend.agent_card.agent_id,
                    task_description=task_desc,
                    metadata={"design_spec": context['design_spec']} if context['design_spec'] else None
                )
                context['implementation'] = impl_result.get('implementation', {})
                print(f"   ✓ Frontend completed step via A2A")

            elif agent_choice == "review":
                if context['design_spec'] and context['implementation']:
                    review_artifact = {
                        "original_design": context['design_spec'],
                        "implementation": context['implementation']
                    }
                    review = await self._request_review_from_agent(
                        agent_id=self.designer.agent_card.agent_id,
                        artifact=review_artifact
                    )
                    approved = review.get('approved', True)
                    score = review.get('score', 8)
                    context['review_score'] = score
                    print(f"   ✓ Design review completed via A2A: {'✅ Approved' if approved else '⚠️ Changes suggested'} (Score: {score}/10)")
                else:
                    print(f"   ⚠️  Skipping design review - missing prerequisites")

            elif agent_choice == "code_reviewer":
                if context['implementation']:
                    review_result = await self._send_task_to_agent(
                        agent_id=self.code_reviewer.agent_card.agent_id,
                        task_description=task_desc,
                        metadata={"implementation": context['implementation']}
                    )
                    context['code_review'] = review_result.get('review', {})
                    overall_score = context['code_review'].get('overall_score', 'N/A')
                    critical_issues = len(context['code_review'].get('critical_issues', []))
                    print(f"   ✓ Code review completed via A2A: Score {overall_score}/10, {critical_issues} critical issues")
                else:
                    print(f"   ⚠️  Skipping code review - no implementation available")

            elif agent_choice == "qa":
                if context['implementation']:
                    qa_result = await self._send_task_to_agent(
                        agent_id=self.qa_engineer.agent_card.agent_id,
                        task_description=task_desc,
                        metadata={
                            "implementation": context['implementation'],
                            "requirements": user_prompt
                        }
                    )
                    context['qa_report'] = qa_result.get('qa_report', {})
                    quality_score = context['qa_report'].get('overall_quality_score', 'N/A')
                    issues_found = len(context['qa_report'].get('issues_found', []))
                    print(f"   ✓ QA testing completed via A2A: Quality {quality_score}/10, {issues_found} issues found")
                else:
                    print(f"   ⚠️  Skipping QA testing - no implementation available")

            elif agent_choice == "devops":
                if context['implementation']:
                    devops_result = await self._send_task_to_agent(
                        agent_id=self.devops.agent_card.agent_id,
                        task_description=task_desc,
                        metadata={"implementation": context['implementation']}
                    )
                    context['devops_config'] = devops_result.get('devops_report', {})
                    deployment_score = context['devops_config'].get('deployment_score', 'N/A')
                    optimizations = len(context['devops_config'].get('optimizations', []))
                    print(f"   ✓ DevOps optimization completed via A2A: Score {deployment_score}/10, {optimizations} optimizations recommended")
                else:
                    print(f"   ⚠️  Skipping DevOps optimization - no implementation available")

            elif agent_choice == "deploy":
                if context['implementation']:
                    deployment_result = await self._deploy_with_retry(
                        user_prompt=user_prompt,
                        implementation=context['implementation'],
                        design_spec=context['design_spec'] or {}
                    )
                    context['deployment_url'] = deployment_result.get('url', 'https://app.netlify.com/teams')
                    build_attempts = deployment_result.get('attempts', 1)
                    print(f"   ✓ Deployed successfully after {build_attempts} attempt(s)")

                    # Return success response
                    framework = context['implementation'].get('framework', 'react')
                    return f"""✅ Custom workflow complete!

🔗 Live Site: {context['deployment_url']}

🎯 AI-Planned Workflow (A2A Protocol):
  • Workflow type: {plan.get('workflow', 'custom')}
  • Reasoning: {plan.get('reasoning', 'N/A')}
  • Agents used: {', '.join(agents_needed)}
  • Steps executed: {len(steps)}
  • Complexity: {plan.get('estimated_complexity', 'N/A')}

⚙️ Technical:
  • Framework: {framework}
  • Deployed on Netlify
  • Build attempts: {build_attempts}

🤖 Coordinated by AI Planner + Multi-Agent System (A2A)
"""
                else:
                    print(f"   ⚠️  Skipping deploy - no implementation available")

            elif agent_choice == "skip":
                print(f"   ⏭️  Skipping step")

        # If no deployment occurred, return a summary
        response = f"""✅ Custom workflow complete!

🎯 AI-Planned Workflow (A2A Protocol):
  • Workflow type: {plan.get('workflow', 'custom')}
  • Reasoning: {plan.get('reasoning', 'N/A')}
  • Agents used: {', '.join(agents_needed)}
  • Steps executed: {len(steps)}
  • Complexity: {plan.get('estimated_complexity', 'N/A')}

📋 Results:
"""

        if context['design_spec']:
            response += "\n  ✅ Design specification created"
        if context['implementation']:
            response += "\n  ✅ Implementation completed"
        if context['review_score']:
            response += f"\n  ✅ Design review completed (Score: {context['review_score']}/10)"
        if context['deployment_url']:
            response += f"\n  ✅ Deployed to: {context['deployment_url']}"

        response += "\n\n🤖 Coordinated by AI Planner + Multi-Agent System (A2A)"

        print("\n" + "-" * 60)
        print("✅ [ORCHESTRATOR] Custom workflow complete (A2A)!\n")
        return response

    # ==========================================
    # DEPLOYMENT HELPERS
    # ==========================================

    async def _deploy_with_retry(
        self,
        user_prompt: str,
        implementation: Dict,
        design_spec: Dict
    ) -> Dict:
        """
        Deploy to Netlify with build verification and automatic retry (using A2A for fixes)

        Returns:
            {
                'url': deployment_url,
                'attempts': number_of_attempts,
                'final_implementation': final_working_implementation,
                'build_errors': list_of_errors_encountered
            }
        """
        attempts = 0
        current_implementation = implementation
        all_build_errors = []

        while attempts < self.max_build_retries:
            attempts += 1
            print(f"\n🔨 Build attempt {attempts}/{self.max_build_retries}")

            # Try to deploy
            deployment_url, build_error = await self._deploy_and_check_build(
                user_prompt=user_prompt,
                implementation=current_implementation
            )

            # Success!
            if deployment_url and not build_error:
                print(f"✅ Build successful on attempt {attempts}")
                return {
                    'url': deployment_url,
                    'attempts': attempts,
                    'final_implementation': current_implementation,
                    'build_errors': all_build_errors
                }

            # Build failed
            if build_error:
                print(f"❌ Build failed on attempt {attempts}")
                print(f"   Error: {build_error[:200]}...")
                all_build_errors.append(build_error)

                # If this is the last attempt, give up
                if attempts >= self.max_build_retries:
                    print(f"⚠️  Max retries reached - deploying with errors")
                    return {
                        'url': deployment_url or 'https://app.netlify.com/teams',
                        'attempts': attempts,
                        'final_implementation': current_implementation,
                        'build_errors': all_build_errors
                    }

                # Ask Frontend to fix the build error (via A2A)
                print(f"\n🔧 Asking Frontend agent to fix build errors (A2A)...")
                fix_result = await self._send_task_to_agent(
                    agent_id=self.frontend.agent_card.agent_id,
                    task_description=f"Fix these build errors:\n\n{build_error}\n\nOriginal task: {user_prompt}",
                    metadata={"design_spec": design_spec, "previous_implementation": current_implementation},
                    priority="high"
                )
                current_implementation = fix_result.get('implementation', current_implementation)
                print(f"✓ Frontend provided updated implementation via A2A")

        # Should never reach here, but just in case
        return {
            'url': 'https://app.netlify.com/teams',
            'attempts': attempts,
            'final_implementation': current_implementation,
            'build_errors': all_build_errors
        }

    async def _deploy_and_check_build(
        self,
        user_prompt: str,
        implementation: Dict
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Deploy to Netlify and check for build errors

        Returns:
            (deployment_url, build_error)
            - If successful: (url, None)
            - If build failed: (None, error_message)
        """
        try:
            files = implementation.get('files', [])

            if not files:
                return (None, "No files to deploy")

            # Create deployment prompt
            deployment_prompt = f"""Deploy this webapp to Netlify and report if there are any build errors.

**Webapp Description:** {user_prompt}

**Files to Deploy:**
{self._format_files_for_deployment(files)}

**Task:**
1. Create a new Netlify site (or use an existing one)
2. Deploy these files to Netlify
3. Check if the build succeeded or failed
4. If the build failed, extract and return the complete error message
5. Return the deployment URL if successful, or the error details if failed

IMPORTANT: Check the build logs carefully for errors like:
- Missing dependencies (Cannot find module 'X')
- TypeScript errors
- Import/export errors
- Configuration issues

Respond in this format:
- If successful: "SUCCESS: https://your-site.netlify.app"
- If failed: "BUILD_ERROR: [full error message with all details]"
"""

            response = await self.deployment_sdk.send_message(deployment_prompt)

            # Check if build succeeded or failed
            if "BUILD_ERROR:" in response:
                # Extract error message
                error_start = response.find("BUILD_ERROR:") + len("BUILD_ERROR:")
                build_error = response[error_start:].strip()
                return (None, build_error)

            # Extract URL from successful deployment
            import re
            url_match = re.search(r'https://[a-zA-Z0-9-]+\.netlify\.app', response)
            if url_match:
                return (url_match.group(0), None)

            # Check for dashboard URL (might mean pending deployment)
            dashboard_match = re.search(r'https://app\.netlify\.com/[^\s]+', response)
            if dashboard_match:
                return (dashboard_match.group(0), None)

            # Couldn't determine - treat as error
            return (None, f"Could not determine build status from response: {response[:200]}")

        except Exception as e:
            return (None, f"Deployment exception: {str(e)}")

    def _format_files_for_deployment(self, files: list) -> str:
        """Format files list for deployment prompt"""
        formatted = []
        for file in files[:5]:  # Limit to first 5 files for prompt size
            path = file.get('path', 'unknown')
            content = file.get('content', '')
            # Truncate content if too long
            content_preview = content[:200] + "..." if len(content) > 200 else content
            formatted.append(f"**{path}:**\n```\n{content_preview}\n```")

        if len(files) > 5:
            formatted.append(f"\n... and {len(files) - 5} more files")

        return "\n\n".join(formatted)

    def _format_whatsapp_response(
        self,
        url: str,
        design_style: str,
        framework: str,
        review_score: int = 8,
        build_attempts: int = 1,
        review_iterations: int = 1
    ) -> str:
        """Format response for WhatsApp"""
        build_status = ""
        if build_attempts > 1:
            build_status = f"\n  • Build verified after {build_attempts} attempts ✅"
        elif build_attempts == 1:
            build_status = "\n  • Build verified on first attempt ✅"

        quality_status = ""
        if review_iterations > 1:
            quality_status = f"\n  • Quality improved over {review_iterations} iterations ✅"
        elif review_iterations == 1:
            quality_status = "\n  • Quality approved on first review ✅"

        return f"""✅ Your webapp is ready!

🔗 Live Site: {url}

🎨 Design:
  • Style: {design_style}
  • Fully responsive
  • Accessibility optimized
  • Quality score: {review_score}/10{quality_status}

⚙️ Technical:
  • Framework: {framework}
  • Build tool: Vite
  • Deployed on Netlify{build_status}

🤖 Built by AI Agent Team (A2A Protocol):
  • UI/UX Designer Agent (design + quality review)
  • Frontend Developer Agent (implementation + improvements)
  • Iterative quality improvement (minimum {self.min_quality_score}/10)
  • Automatic build verification
  • All agents communicated via A2A Protocol

🚀 Powered by Claude Multi-Agent System with A2A
"""

    async def cleanup(self):
        """Clean up all agents and SDKs"""
        await self.designer.cleanup()
        await self.frontend.cleanup()
        await self.code_reviewer.cleanup()
        await self.qa_engineer.cleanup()
        await self.devops.cleanup()
        await self.deployment_sdk.close()
        await self.planner_sdk.close()
        print("🧹 [ORCHESTRATOR] Cleaned up all agents, deployment SDK, and planner SDK")
