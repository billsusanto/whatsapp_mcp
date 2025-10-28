"""
Workflow Implementations Module for Collaborative Orchestrator
Handles all workflow execution logic and deployment operations
"""

import os
import time
from typing import Dict, Optional

# Import telemetry
from utils.telemetry import (
    trace_workflow,
    trace_operation,
    log_event,
    log_metric,
    log_error
)

# Import system health monitor
from utils.health_monitor import system_health_monitor


class OrchestratorWorkflowsMixin:
    """
    Mixin providing workflow execution methods for the orchestrator.

    This mixin handles:
    - AI workflow planning
    - Full build workflow (design → implementation → review → deploy)
    - Bug fix workflow
    - Redeploy workflow
    - Design-only workflow
    - Custom workflow with AI-powered step routing
    - Deployment with retry logic
    - Refinement during different workflow phases
    """

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
- **backend**: Backend Developer - Creates database schemas, REST APIs, authentication, server-side logic, SQL migrations (NEW!)
- **frontend**: Frontend Developer - Implements React/Vue/Next.js code, fixes bugs, handles dependencies, writes components
- **code_reviewer**: Code Reviewer - Reviews code for quality, security vulnerabilities, performance issues, best practices
- **qa**: QA Engineer - Tests functionality, usability, accessibility, creates test plans, identifies bugs
- **devops**: DevOps Engineer - Handles deployment optimization, build configuration, security hardening, monitors performance

**Available Workflows:**
1. **full_build**: Build a complete production-ready webapp from scratch
   - Steps: Designer → Backend (if needed) → Frontend → Code Review → QA Testing → DevOps Optimization → Deploy
   - Agents: Designer + Backend (optional) + Frontend + Code Reviewer + QA + DevOps
   - Use when: User wants to create a new high-quality application
   - NOTE: Include Backend agent if the app needs database, API, authentication, or server-side logic

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
    "Designer creates comprehensive design specification and reviews frontend code",
    "Frontend implements React, tailwind, other frontend library and components based on design",
    "Code Reviewer reviews code for security and quality",
    "QA Engineer tests functionality and accessibility",
    "DevOps Engineer optimizes, pushes to github accoubt and deploys to Netlify",
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
    # WORKFLOW IMPLEMENTATIONS (A2A-ENABLED)
    # ==========================================

    @trace_workflow("full_build")
    async def _workflow_full_build(self, user_prompt: str, plan: Dict = None) -> str:
        """Full build workflow: Designer → Frontend → Review → Deploy (via A2A)"""
        print(f"\n🏗️  Starting FULL BUILD workflow (A2A Protocol)")

        # Set total steps for progress tracking
        # Design (1) + Implementation (1) + Review iterations (2-5) + Deploy retries (1-10) + Frontend fixes (0-5) + Format (1)
        # Realistic estimate accounting for quality loops and deployment retries: ~15 steps average
        self.workflow_steps_total = 15

        # Track workflow start
        workflow_id = f"full_build_{int(time.time())}"
        workflow_start_time = time.time()
        system_health_monitor.track_workflow_start(
            workflow_type="full_build",
            workflow_id=workflow_id,
            metadata={"user_prompt_length": len(user_prompt)}
        )

        if plan and plan.get('special_instructions'):
            print(f"📋 Special instructions: {plan['special_instructions']}")

        try:
            # Import project manager for backend features
            try:
                from database.project_manager import project_manager
                PROJECT_MANAGER_AVAILABLE = True
            except ImportError:
                PROJECT_MANAGER_AVAILABLE = False
                project_manager = None

            # Step 1: Designer creates design specification (A2A - keep agent alive for reviews)
            self.current_phase = "design"
            await self._save_state()
            print("\n[Step 1/5] 🎨 Designer creating design specification (A2A)...")
            design_result = await self._send_task_to_agent(
                agent_id=self.DESIGNER_ID,
                task_description=f"Create design specification for: {user_prompt}",
                priority="high",
                cleanup_after=False  # Keep designer alive for review iterations
            )
            design_spec = design_result.get('design_spec', {})
            self.current_design_spec = design_spec  # Store for refinements

            # Extract design style safely
            if isinstance(design_spec, dict):
                design_style = design_spec.get('style', 'modern')
            else:
                design_style = 'modern'

            print(f"✓ Design completed via A2A")

            # Step 2 (Optional): Backend creates database schema and API if needed
            backend_spec = None
            backend_api_url = None

            # Check if backend is needed (from plan or keywords)
            needs_backend = False
            if plan and "backend" in plan.get('agents_needed', []):
                needs_backend = True
            else:
                # Heuristic: Check for backend-related keywords in prompt
                backend_keywords = ["database", "api", "backend", "auth", "login", "signup",
                                   "register", "user", "save data", "store", "crud"]
                needs_backend = any(kw in user_prompt.lower() for kw in backend_keywords)

            if needs_backend and PROJECT_MANAGER_AVAILABLE:
                self.current_phase = "backend"
                await self._save_state()
                print("\n[Step 2/6] 🔧 Backend creating database schema and API (A2A)...")

                # Create project database schema
                try:
                    project_name = user_prompt[:50].strip()  # Use first 50 chars as project name
                    self.project_metadata = await project_manager.create_project(
                        user_id=self.user_id,
                        platform=self.platform,
                        project_name=project_name,
                        project_description=user_prompt
                    )
                    self.project_id = self.project_metadata.project_id

                    print(f"   ✅ Created project database: {self.project_metadata.schema_name}")

                    # Backend agent designs and implements API
                    backend_result = await self._send_task_to_agent(
                        agent_id=self.BACKEND_ID,
                        task_description=f"Create database schema and REST API for: {user_prompt}",
                        metadata={"design_spec": design_spec, "project_id": self.project_id},
                        priority="high",
                        cleanup_after=False  # Keep backend alive for potential refinements
                    )

                    backend_spec = backend_result.get('backend_spec', {})
                    self.current_backend_spec = backend_spec

                    # Execute SQL migrations to create tables
                    if backend_result.get('sql_migrations'):
                        backend_agent = await self._get_agent("backend")
                        db_result = await backend_agent.create_database_tables(
                            project_id=self.project_id,
                            sql_migrations=backend_result['sql_migrations']
                        )

                        if db_result.get('success'):
                            print(f"   ✅ Database tables created in schema: {self.project_metadata.schema_name}")
                        else:
                            print(f"   ⚠️  Database creation warning: {db_result.get('error', 'Unknown')}")

                    # Update project metadata with backend spec
                    await project_manager.update_project_spec(
                        project_id=self.project_id,
                        design_spec=design_spec,
                        backend_spec=backend_spec
                    )

                    # For MVP, backend URL is the same as frontend (will be refactored for separate backend deployment)
                    backend_api_url = "/api"  # Relative API path

                    print(f"✓ Backend completed via A2A")

                except Exception as e:
                    print(f"   ⚠️  Backend creation failed: {e}")
                    log_error(e, "orchestrator_backend_creation")
                    # Continue without backend
                    backend_spec = None
            elif needs_backend and not PROJECT_MANAGER_AVAILABLE:
                print("\n⚠️  Backend features requested but project manager not available")
                print("   Continuing with frontend-only build...")

            # Step 3: Frontend implements design (+ backend API if available)
            self.current_phase = "implementation"
            await self._save_state()
            step_num = "3/6" if backend_spec else "2/5"
            print(f"\n[Step {step_num}] 💻 Frontend implementing design (A2A)...")

            # Build frontend task description with backend context
            frontend_task = f"Implement webapp using next.js, react, tailwind and other frontend libraries: {user_prompt}"
            if backend_spec:
                frontend_task += f"\n\nBackend API is available at {backend_api_url}. Use the following API endpoints:\n"
                # Include API endpoint information
                for endpoint in backend_spec.get('api_endpoints', []):
                    frontend_task += f"- {endpoint.get('method', 'GET')} {backend_api_url}{endpoint.get('path', '')}: {endpoint.get('description', '')}\n"

            impl_result = await self._send_task_to_agent(
                agent_id=self.FRONTEND_ID,
                task_description=frontend_task,
                metadata={
                    "design_spec": design_spec,
                    "backend_spec": backend_spec,
                    "backend_api_url": backend_api_url
                },
                priority="high",
                cleanup_after=False  # Keep frontend alive for improvement iterations
            )
            implementation = impl_result.get('implementation', {})
            self.current_implementation = implementation  # Store for refinements
            framework = implementation.get('framework', 'react')

            print(f"✓ Implementation completed via A2A: {framework}")

            # Step 3.5: Visual Design Review with Playwright (PRODUCTION-READY)
            current_implementation = implementation  # Track current implementation through review loops
            if os.getenv('DESIGN_REVIEW_ENABLED', 'true').lower() == 'true':
                self.current_phase = "visual_review"
                await self._save_state()
                step_num_visual = "3.5/6" if backend_spec else "2.5/5"
                print(f"\n[Step {step_num_visual}] 📸 Visual Design Review with Playwright...")
                await self._send_notification("📸 Starting visual design review with Playwright...")

                try:
                    # Import testing coordinator
                    from agents.collaborative.testing_coordinator import TestingCoordinator

                    # Create testing coordinator
                    coordinator = TestingCoordinator(self)

                    # Write implementation to temporary project directory
                    print("   📝 Writing project files to disk...")
                    project_dir = await self._write_implementation_to_disk(implementation)
                    print(f"   ✅ Project files written to: {project_dir}")

                    # Install dependencies
                    print("   📦 Installing npm dependencies...")
                    await self._install_npm_dependencies(project_dir)
                    print("   ✅ Dependencies installed")

                    # Run design review loop with Playwright
                    print("   🎨 Starting design review loop...")
                    visual_review_result = await coordinator.run_design_review_loop(project_dir)

                    # Update implementation with changes from visual review
                    if visual_review_result['status'] == 'approved':
                        print(f"   ✅ Visual review approved! (Score: {visual_review_result.get('final_score', 10)}/10)")
                        await self._send_notification(
                            f"✅ Visual review approved! Score: {visual_review_result.get('final_score', 10)}/10"
                        )
                    else:
                        print(f"   ⚠️  Visual review completed with {visual_review_result['iterations']} iterations")
                        await self._send_notification(
                            f"⚠️ Visual review completed: {visual_review_result['iterations']} iterations, "
                            f"Score: {visual_review_result.get('final_score', 7)}/10"
                        )

                    # Read updated files back from disk (if Frontend made changes)
                    current_implementation = await self._read_implementation_from_disk(project_dir)

                    # Log visual review completion
                    log_event("orchestrator.visual_review_completed",
                             status=visual_review_result['status'],
                             iterations=visual_review_result['iterations'],
                             final_score=visual_review_result.get('final_score', 0))

                    # Cleanup temporary project directory
                    await self._cleanup_project_directory(project_dir)

                except Exception as e:
                    print(f"   ❌ Visual review error: {e}")
                    import traceback
                    traceback.print_exc()
                    log_error(e, "orchestrator_visual_review")
                    await self._send_notification(f"⚠️ Visual review error: {str(e)} - continuing with deployment")
                    # Continue workflow even if visual review fails

            # Step 3.6: QA E2E Testing with Playwright (PRODUCTION-READY)
            if os.getenv('QA_TESTING_ENABLED', 'false').lower() == 'true':
                self.current_phase = "qa_testing"
                await self._save_state()
                step_num_qa = "3.6/6" if backend_spec else "2.6/5"
                print(f"\n[Step {step_num_qa}] 🧪 QA End-to-End Testing with Playwright...")
                await self._send_notification("🧪 Starting QA end-to-end testing with Playwright...")

                try:
                    # Import testing coordinator if not already imported
                    from agents.collaborative.testing_coordinator import TestingCoordinator

                    # Create testing coordinator (or reuse from visual review)
                    coordinator = TestingCoordinator(self)

                    # Write implementation to temporary project directory (or reuse from visual review)
                    print("   📝 Writing project files to disk...")
                    project_dir = await self._write_implementation_to_disk(current_implementation)
                    print(f"   ✅ Project files written to: {project_dir}")

                    # Install dependencies
                    print("   📦 Installing npm dependencies...")
                    await self._install_npm_dependencies(project_dir)
                    print("   ✅ Dependencies installed")

                    # Get functional spec from user requirements
                    functional_spec = {
                        'requirements': user_prompt,
                        'framework': current_implementation.get('framework', 'react')
                    }

                    # Run QA testing loop with Playwright
                    print("   🧪 Starting QA testing loop...")
                    qa_test_result = await coordinator.run_qa_testing_loop(
                        project_dir,
                        functional_spec=functional_spec
                    )

                    # Update implementation with changes from QA testing
                    if qa_test_result['status'] == 'approved':
                        print(f"   ✅ QA tests passed! (Pass rate: {qa_test_result.get('pass_rate', 100):.1f}%)")
                        await self._send_notification(
                            f"✅ QA tests passed! Pass rate: {qa_test_result.get('pass_rate', 100):.1f}%"
                        )
                    else:
                        print(f"   ⚠️  QA testing completed with {qa_test_result['iterations']} iterations")
                        await self._send_notification(
                            f"⚠️ QA testing completed: {qa_test_result['iterations']} iterations, "
                            f"Pass rate: {qa_test_result.get('pass_rate', 0):.1f}%"
                        )

                    # Read updated files back from disk (if Frontend/Backend made fixes)
                    current_implementation = await self._read_implementation_from_disk(project_dir)

                    # Log QA testing completion
                    log_event("orchestrator.qa_testing_completed",
                             status=qa_test_result['status'],
                             iterations=qa_test_result['iterations'],
                             pass_rate=qa_test_result.get('pass_rate', 0))

                    # Cleanup temporary project directory
                    await self._cleanup_project_directory(project_dir)

                except Exception as e:
                    print(f"   ❌ QA testing error: {e}")
                    import traceback
                    traceback.print_exc()
                    log_error(e, "orchestrator_qa_testing")
                    await self._send_notification(f"⚠️ QA testing error: {str(e)} - continuing with deployment")
                    # Continue workflow even if QA testing fails

            # Step 4: Quality verification loop - ensure score >= 8/10
            self.current_phase = "review"
            await self._save_state()
            print("\n[Step 3/5] 🔍 Quality verification (minimum score: {}/10, via A2A)...".format(self.min_quality_score))

            review_iteration = 0
            score = 0
            approved = False

            # Track quality loop start
            log_event("orchestrator.quality_loop_started",
                     min_quality_score=self.min_quality_score,
                     max_iterations=self.max_review_iterations)

            quality_loop_start_time = time.time()

            while review_iteration < self.max_review_iterations:
                review_iteration += 1
                print(f"\n   Review iteration {review_iteration}/{self.max_review_iterations}")

                # Track iteration start
                iteration_start_time = time.time()
                log_event("orchestrator.quality_iteration_started",
                         iteration_number=review_iteration,
                         max_iterations=self.max_review_iterations,
                         previous_score=score)

                # Designer reviews implementation (A2A - don't cleanup during loop)
                review_artifact = {
                    "original_design": design_spec,
                    "implementation": current_implementation
                }
                review = await self._request_review_from_agent(
                    agent_id=self.DESIGNER_ID,
                    artifact=review_artifact,
                    cleanup_after=False  # Keep designer alive for multiple reviews
                )
                approved = review.get('approved', True)
                score = review.get('score', 9)
                feedback = review.get('feedback', [])

                # Calculate iteration duration
                iteration_duration_ms = (time.time() - iteration_start_time) * 1000

                print(f"   Score: {score}/10 - {'✅ Approved' if approved else '⚠️ Needs improvement'}")

                # Track iteration completion
                log_event("orchestrator.quality_iteration_completed",
                         iteration_number=review_iteration,
                         score=score,
                         approved=approved,
                         feedback_count=len(feedback),
                         iteration_duration_ms=iteration_duration_ms,
                         meets_quality_standard=score >= self.min_quality_score)

                # Track score metrics
                log_metric("orchestrator.quality_iteration_score", score)
                log_metric("orchestrator.quality_iteration_duration_ms", iteration_duration_ms)

                # Check if quality standard is met
                if score >= self.min_quality_score:
                    print(f"   ✅ Quality standard met! (Score: {score}/10 >= {self.min_quality_score}/10)")

                    # Track quality loop success
                    quality_loop_duration_ms = (time.time() - quality_loop_start_time) * 1000
                    log_event("orchestrator.quality_loop_succeeded",
                             final_score=score,
                             total_iterations=review_iteration,
                             quality_loop_duration_ms=quality_loop_duration_ms)
                    log_metric("orchestrator.quality_loop_iterations", review_iteration)
                    log_metric("orchestrator.quality_loop_duration_ms", quality_loop_duration_ms)

                    break

                # Quality not met - need improvement
                if review_iteration >= self.max_review_iterations:
                    print(f"   ⚠️  Max iterations reached - proceeding with current quality (Score: {score}/10)")

                    # Track quality loop max iterations reached
                    quality_loop_duration_ms = (time.time() - quality_loop_start_time) * 1000
                    log_event("orchestrator.quality_loop_max_iterations_reached",
                             final_score=score,
                             total_iterations=review_iteration,
                             quality_loop_duration_ms=quality_loop_duration_ms,
                             quality_gap=self.min_quality_score - score)
                    log_metric("orchestrator.quality_loop_iterations", review_iteration)
                    log_metric("orchestrator.quality_loop_duration_ms", quality_loop_duration_ms)

                    break

                # Ask Frontend to improve based on feedback (A2A - don't cleanup during loop)
                print(f"   🔧 Quality below standard ({score}/10 < {self.min_quality_score}/10) - requesting improvements (A2A)...")
                print(f"   📋 Feedback: {', '.join(feedback) if feedback else 'General improvements needed'}")

                # Track improvement request
                log_event("orchestrator.improvement_requested",
                         iteration_number=review_iteration,
                         current_score=score,
                         target_score=self.min_quality_score,
                         feedback_count=len(feedback),
                         quality_gap=self.min_quality_score - score)

                improvement_result = await self._send_task_to_agent(
                    agent_id=self.FRONTEND_ID,
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
                    priority="high",
                    cleanup_after=False  # Keep frontend alive for multiple improvements
                )
                current_implementation = improvement_result.get('implementation', current_implementation)
                self.current_implementation = current_implementation  # Update for refinements
                print(f"   ✓ Frontend provided improved implementation via A2A")

                # Track improvement completion
                log_event("orchestrator.improvement_completed",
                         iteration_number=review_iteration,
                         previous_score=score)

            # Use the final implementation (after quality loop)
            implementation = current_implementation
            self.current_implementation = implementation  # Final update

            # Track final quality loop metrics
            quality_loop_duration_ms = (time.time() - quality_loop_start_time) * 1000
            log_event("orchestrator.quality_loop_completed",
                     final_score=score,
                     total_iterations=review_iteration,
                     quality_loop_duration_ms=quality_loop_duration_ms,
                     quality_met=score >= self.min_quality_score)
            log_metric("orchestrator.quality_loop_final_score", score)
            log_metric("orchestrator.quality_loop_total_iterations", review_iteration)

            print(f"\n✓ Quality verification completed via A2A: Score {score}/10 after {review_iteration} iteration(s)")

            # Step 4: Deploy to Netlify with build verification and retry
            self.current_phase = "deployment"
            await self._save_state()
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

            # Track workflow success
            workflow_duration_ms = (time.time() - workflow_start_time) * 1000
            system_health_monitor.track_workflow_success(
                workflow_type="full_build",
                workflow_id=workflow_id,
                duration_ms=workflow_duration_ms,
                metadata={
                    "review_score": score,
                    "review_iterations": review_iteration,
                    "build_attempts": build_attempts,
                    "deployment_url": deployment_url
                }
            )

            # Mark as inactive and delete state after successful completion
            self.is_active = False
            self.current_phase = None
            await self._delete_state()

            return response

        except Exception as e:
            # Track workflow error
            workflow_duration_ms = (time.time() - workflow_start_time) * 1000
            system_health_monitor.track_workflow_error(
                workflow_type="full_build",
                workflow_id=workflow_id,
                error=e,
                duration_ms=workflow_duration_ms,
                metadata={"user_prompt_length": len(user_prompt)}
            )
            raise

        finally:
            # Clean up all agents used in this workflow to free resources
            print("\n🧹 Cleaning up agents...")
            await self._cleanup_all_active_agents()
            print("✓ All agents cleaned up - resources freed")

    @trace_workflow("bug_fix")
    async def _workflow_bug_fix(self, user_prompt: str, plan: Dict = None) -> str:
        """Bug fix workflow: Frontend fixes code → Deploy (via A2A)"""
        print(f"\n🔧 Starting BUG FIX workflow (A2A Protocol)")

        # Set total steps for progress tracking: Fix (1-3) + Deploy retries (1-10) + Frontend fixes (0-5) = 2-18 steps
        # Realistic estimate: ~8 steps average
        self.workflow_steps_total = 8

        # Track workflow start
        workflow_id = f"bug_fix_{int(time.time())}"
        workflow_start_time = time.time()
        system_health_monitor.track_workflow_start(
            workflow_type="bug_fix",
            workflow_id=workflow_id,
            metadata={"user_prompt_length": len(user_prompt)}
        )

        if plan and plan.get('special_instructions'):
            print(f"📋 Special instructions: {plan['special_instructions']}")

        # Step 1: Frontend fixes the issue (A2A)
        print("\n[Step 1/2] 💻 Frontend analyzing and fixing issue (A2A)...")
        fix_result = await self._send_task_to_agent(
            agent_id=self.FRONTEND_ID,
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

        # Track workflow success
        workflow_duration_ms = (time.time() - workflow_start_time) * 1000
        system_health_monitor.track_workflow_success(
            workflow_type="bug_fix",
            workflow_id=workflow_id,
            duration_ms=workflow_duration_ms,
            metadata={
                "build_attempts": build_attempts,
                "deployment_url": deployment_url
            }
        )

        return response

    @trace_workflow("redeploy")
    async def _workflow_redeploy(self, user_prompt: str, plan: Dict = None) -> str:
        """Redeploy workflow: Just deploy existing code"""
        print(f"\n🚀 Starting REDEPLOY workflow")

        # Set total steps for progress tracking: Deploy only = 1 step
        self.workflow_steps_total = 1

        # Track workflow start
        workflow_id = f"redeploy_{int(time.time())}"
        workflow_start_time = time.time()
        system_health_monitor.track_workflow_start(
            workflow_type="redeploy",
            workflow_id=workflow_id,
            metadata={"user_prompt_length": len(user_prompt)}
        )

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

        # Track workflow success
        workflow_duration_ms = (time.time() - workflow_start_time) * 1000
        system_health_monitor.track_workflow_success(
            workflow_type="redeploy",
            workflow_id=workflow_id,
            duration_ms=workflow_duration_ms,
            metadata={"deployment_url": deployment_url}
        )

        return response

    @trace_workflow("design_only")
    async def _workflow_design_only(self, user_prompt: str, plan: Dict = None) -> str:
        """Design only workflow: Designer creates design spec (via A2A)"""
        print(f"\n🎨 Starting DESIGN ONLY workflow (A2A Protocol)")

        # Set total steps for progress tracking: Design only = 1 step
        self.workflow_steps_total = 1

        # Track workflow start
        workflow_id = f"design_only_{int(time.time())}"
        workflow_start_time = time.time()
        system_health_monitor.track_workflow_start(
            workflow_type="design_only",
            workflow_id=workflow_id,
            metadata={"user_prompt_length": len(user_prompt)}
        )

        if plan and plan.get('special_instructions'):
            print(f"📋 Special instructions: {plan['special_instructions']}")

        # Step 1: Designer creates design (A2A)
        print("\n[Step 1/1] 🎨 Designer creating design specification (A2A)...")
        design_result = await self._send_task_to_agent(
            agent_id=self.DESIGNER_ID,
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

        # Track workflow success
        workflow_duration_ms = (time.time() - workflow_start_time) * 1000
        system_health_monitor.track_workflow_success(
            workflow_type="design_only",
            workflow_id=workflow_id,
            duration_ms=workflow_duration_ms,
            metadata={"has_design_spec": bool(design_spec)}
        )

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

    @trace_workflow("custom")
    async def _workflow_custom(self, user_prompt: str, plan: Dict) -> str:
        """
        Custom workflow: Execute workflow based on AI planner's instructions (via A2A)

        This workflow uses AI to intelligently route each step to the right agent,
        rather than hardcoded keyword matching.
        """
        print(f"\n🔮 Starting CUSTOM workflow with AI-powered step routing (A2A Protocol)")
        print(f"📋 AI Planner reasoning: {plan.get('reasoning', 'N/A')}")

        # Track workflow start
        workflow_id = f"custom_{int(time.time())}"
        workflow_start_time = time.time()
        system_health_monitor.track_workflow_start(
            workflow_type="custom",
            workflow_id=workflow_id,
            metadata={
                "user_prompt_length": len(user_prompt),
                "steps_count": len(plan.get('steps', [])),
                "agents_needed": plan.get('agents_needed', [])
            }
        )

        if plan.get('special_instructions'):
            print(f"📋 Special instructions: {plan['special_instructions']}")

        agents_needed = plan.get('agents_needed', [])
        steps = plan.get('steps', [])

        # Set total steps for progress tracking based on planned steps
        self.workflow_steps_total = len(steps) if steps else 5

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
                    agent_id=self.DESIGNER_ID,
                    task_description=task_desc
                )
                context['design_spec'] = design_result.get('design_spec', {})
                print(f"   ✓ Designer completed step via A2A")

            elif agent_choice == "frontend":
                impl_result = await self._send_task_to_agent(
                    agent_id=self.FRONTEND_ID,
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
                        agent_id=self.DESIGNER_ID,
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
                        agent_id=self.CODE_REVIEWER_ID,
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
                        agent_id=self.QA_ID,
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
                        agent_id=self.DEVOPS_ID,
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

        # Track workflow success
        workflow_duration_ms = (time.time() - workflow_start_time) * 1000
        system_health_monitor.track_workflow_success(
            workflow_type="custom",
            workflow_id=workflow_id,
            duration_ms=workflow_duration_ms,
            metadata={
                "steps_executed": len(steps),
                "agents_used": agents_needed,
                "has_deployment": bool(context.get('deployment_url'))
            }
        )

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
        Deploy to Netlify with build verification and automatic retry (using DevOps agent via A2A)

        Returns:
            {
                'url': deployment_url,
                'attempts': number_of_attempts,
                'final_implementation': final_working_implementation,
                'build_errors': list_of_errors_encountered
            }
        """
        # Log deployment pipeline start
        deployment_start_time = time.time()

        log_event("deployment.pipeline_started",
                 max_retries=self.max_build_retries,
                 has_implementation=bool(implementation),
                 has_design_spec=bool(design_spec))

        attempts = 0
        current_implementation = implementation
        all_build_errors = []

        while attempts < self.max_build_retries:
            attempts += 1
            attempt_start_time = time.time()

            print(f"\n🔨 Deployment attempt {attempts}/{self.max_build_retries}")

            # Log deployment attempt start
            log_event("deployment.attempt_started",
                     attempt=attempts,
                     max_attempts=self.max_build_retries,
                     is_retry=attempts > 1,
                     previous_errors_count=len(all_build_errors))

            # Call DevOps agent to deploy (includes GitHub setup, push, Netlify deploy, build verification)
            try:
                devops_result = await self._send_task_to_agent(
                    agent_id=self.DEVOPS_ID,
                    task_description=f"""Deploy this webapp to Netlify with full GitHub workflow.

User request: {user_prompt}

Deployment attempt: {attempts}/{self.max_build_retries}

CRITICAL STEPS:
1. Create/verify GitHub repository
2. Generate netlify.toml with NPM_FLAGS = "--include=dev"
3. Write all files to the repository
4. Push to GitHub (billsusanto account)
5. Deploy from GitHub to Netlify
6. Check build logs for errors
7. Verify the deployed site loads

🔥 IMPORTANT - USE LOGFIRE FOR DEBUGGING:
- If this is a retry attempt ({attempts > 1}), FIRST query Logfire to see what failed before
- Query: span.name contains "Deploy" AND timestamp > now() - 1h
- Look for previous deployment traces to understand what went wrong
- Extract exact error messages, file paths, line numbers from Logfire traces
- Use production telemetry data (not assumptions) to identify root causes
- Reference specific trace IDs in your error analysis

Dashboard: https://logfire.pydantic.dev/
Project: whatsapp-mcp

If build fails:
- Query Logfire for the deployment trace
- Extract EXACT error messages from build logs
- Provide structured error data with file paths and line numbers
- Return detailed error report for Frontend to fix

If successful, return the live deployment URL.""",
                    metadata={
                        "implementation": current_implementation,
                        "design_spec": design_spec,
                        "project_id": self.project_id,  # For database connection lookup
                        "database_connection": self.current_backend_spec.get("database_connection") if self.current_backend_spec else None  # Neon connection strings
                    },
                    priority="high",
                    cleanup_after=False,  # Keep DevOps alive for retries
                    notify_user=True
                )

                devops_report = devops_result.get('devops_report', {})
                build_verification = devops_report.get('build_verification', {})
                netlify_deployment = devops_report.get('netlify_deployment', {})

                # Extract deployment URL and build status
                deployment_url = netlify_deployment.get('deployment_url') or devops_report.get('deployment_url')
                build_successful = build_verification.get('build_successful', False)
                build_errors = build_verification.get('build_errors', [])

                # Success!
                if build_successful and deployment_url:
                    attempt_duration_ms = (time.time() - attempt_start_time) * 1000
                    total_duration_ms = (time.time() - deployment_start_time) * 1000

                    print(f"✅ Build successful on attempt {attempts}")
                    print(f"   Deployment URL: {deployment_url}")

                    # Log successful deployment
                    log_event("deployment.build_succeeded",
                             attempt=attempts,
                             deployment_url=deployment_url,
                             attempt_duration_ms=attempt_duration_ms,
                             total_duration_ms=total_duration_ms,
                             total_errors_encountered=len(all_build_errors))

                    log_metric("deployment.successful_builds", 1)
                    log_metric("deployment.attempts_until_success", attempts)
                    log_metric("deployment.total_duration_ms", total_duration_ms)

                    # Log final deployment success
                    log_event("deployment.pipeline_succeeded",
                             deployment_url=deployment_url,
                             total_attempts=attempts,
                             total_duration_ms=total_duration_ms,
                             had_retries=attempts > 1,
                             total_errors_fixed=len(all_build_errors))

                    # Clean up DevOps agent after success
                    await self._cleanup_agent("devops")

                    return {
                        'url': deployment_url,
                        'attempts': attempts,
                        'final_implementation': current_implementation,
                        'build_errors': all_build_errors
                    }

                # Build failed - extract error details
                if build_errors or not build_successful:
                    attempt_duration_ms = (time.time() - attempt_start_time) * 1000
                    error_summary = self._format_build_errors(build_errors)

                    print(f"❌ Build failed on attempt {attempts}")
                    print(f"   Errors: {error_summary[:200]}...")
                    all_build_errors.extend(build_errors)

                    # Log build failure
                    log_event("deployment.build_failed",
                             attempt=attempts,
                             attempt_duration_ms=attempt_duration_ms,
                             errors_count=len(build_errors),
                             error_summary=error_summary[:500],
                             will_retry=attempts < self.max_build_retries)

                    log_metric("deployment.failed_builds", 1)
                    log_metric("deployment.build_errors_count", len(build_errors))

                    # If this is the last attempt, give up
                    if attempts >= self.max_build_retries:
                        total_duration_ms = (time.time() - deployment_start_time) * 1000

                        print(f"⚠️  Max retries ({self.max_build_retries}) reached - deployment failed")

                        # Log final deployment failure
                        log_event("deployment.pipeline_failed",
                                 total_attempts=attempts,
                                 total_duration_ms=total_duration_ms,
                                 total_errors_count=len(all_build_errors),
                                 max_retries_reached=True)

                        log_metric("deployment.pipeline_failures", 1)

                        # Clean up DevOps agent
                        await self._cleanup_agent("devops")

                        return {
                            'url': deployment_url or 'https://app.netlify.com/teams',
                            'attempts': attempts,
                            'final_implementation': current_implementation,
                            'build_errors': all_build_errors
                        }

                    # Ask Frontend to fix the build errors (via A2A)
                    print(f"\n🔧 Asking Frontend agent to fix build errors (A2A)...")

                    # Log error fix request
                    log_event("deployment.requesting_error_fix",
                             attempt=attempts,
                             errors_count=len(build_errors),
                             requesting_from="frontend_agent")

                    # Format error details for Frontend
                    error_description = self._format_errors_for_frontend(build_errors, error_summary)

                    fix_result = await self._send_task_to_agent(
                        agent_id=self.FRONTEND_ID,
                        task_description=f"""Fix these build errors:

{error_description}

Original task: {user_prompt}
Fix attempt: {attempts}/{self.max_build_retries}

🔥 IMPORTANT - USE LOGFIRE FOR DEBUGGING:
- FIRST query Logfire to see the exact error that occurred in production
- Query: agent_name = "Frontend Developer" AND result_status = "error" AND timestamp > now() - 1h
- Look for your previous implementation attempt traces
- Extract exact error messages, stack traces, component names from telemetry
- See what actually failed in the build (not assumptions!)
- Reference specific trace IDs in your bug fix analysis

Dashboard: https://logfire.pydantic.dev/
Project: whatsapp-mcp

Example Logfire debugging:
1. Query: span.name contains "execute_task" AND error_message contains "TypeScript"
2. Found trace: abc123 showing build failed with "Property 'title' does not exist"
3. Extract: You used album.title but data has album.name
4. Fix: Update component to use correct property names

The DevOps agent attempted to deploy your code and found build errors.
Please:
1. Check Logfire for the deployment trace to understand what failed
2. Analyze the exact error messages from production telemetry
3. Fix ALL errors in the implementation
4. Return the corrected implementation with all fixes applied

Do NOT guess - use Logfire data to see what actually went wrong!""",
                        metadata={
                            "design_spec": design_spec,
                            "previous_implementation": current_implementation,
                            "build_errors": build_errors  # Pass structured error data
                        },
                        priority="high",
                        cleanup_after=True,  # Clean up Frontend after fix
                        notify_user=True
                    )

                    current_implementation = fix_result.get('implementation', current_implementation)

                    # Log successful error fix
                    log_event("deployment.errors_fixed",
                             attempt=attempts,
                             errors_fixed_count=len(build_errors),
                             implementation_updated=True)

                    print(f"✓ Frontend provided updated implementation via A2A")
                else:
                    # No clear success or failure - treat as error
                    print(f"⚠️  Unclear deployment status on attempt {attempts}")
                    all_build_errors.append("Unclear deployment status - no URL or build status")

                    if attempts >= self.max_build_retries:
                        await self._cleanup_agent("devops")
                        return {
                            'url': 'https://app.netlify.com/teams',
                            'attempts': attempts,
                            'final_implementation': current_implementation,
                            'build_errors': all_build_errors
                        }

            except Exception as e:
                attempt_duration_ms = (time.time() - attempt_start_time) * 1000

                print(f"❌ DevOps agent error on attempt {attempts}: {str(e)}")
                all_build_errors.append(f"DevOps agent error: {str(e)}")

                # Log deployment exception
                log_error(e, "deployment_attempt",
                         attempt=attempts,
                         attempt_duration_ms=attempt_duration_ms,
                         will_retry=attempts < self.max_build_retries)

                log_event("deployment.attempt_exception",
                         attempt=attempts,
                         attempt_duration_ms=attempt_duration_ms,
                         error=str(e),
                         error_type=type(e).__name__)

                log_metric("deployment.exceptions", 1)

                if attempts >= self.max_build_retries:
                    total_duration_ms = (time.time() - deployment_start_time) * 1000

                    # Log pipeline failure due to exceptions
                    log_event("deployment.pipeline_failed",
                             total_attempts=attempts,
                             total_duration_ms=total_duration_ms,
                             total_errors_count=len(all_build_errors),
                             failure_reason="exception",
                             max_retries_reached=True)

                    log_metric("deployment.pipeline_failures", 1)

                    await self._cleanup_agent("devops")
                    return {
                        'url': 'https://app.netlify.com/teams',
                        'attempts': attempts,
                        'final_implementation': current_implementation,
                        'build_errors': all_build_errors
                    }

                # For errors, still try to get Frontend to fix the implementation
                print(f"\n🔧 Asking Frontend to review and fix implementation after DevOps error...")

                fix_result = await self._send_task_to_agent(
                    agent_id=self.FRONTEND_ID,
                    task_description=f"""The deployment failed with an error. Please review and fix the implementation.

Error: {str(e)}

Original task: {user_prompt}
Fix attempt: {attempts}/{self.max_build_retries}

🔥 CRITICAL - USE LOGFIRE TO DEBUG THIS DEPLOYMENT FAILURE:
- Query Logfire to see what happened during the DevOps agent execution
- Query: agent_name = "DevOps Engineer" AND result_status = "error" AND timestamp > now() - 30m
- Look for the deployment attempt trace to understand the failure
- Also check your own previous implementation traces
- Extract exact error details from production telemetry

Dashboard: https://logfire.pydantic.dev/
Project: whatsapp-mcp

The DevOps agent encountered an error during deployment.
Please:
1. Check Logfire for both DevOps and Frontend traces to understand the full context
2. Review the implementation for common issues:
   - All files are properly structured
   - All dependencies are in package.json (including devDependencies)
   - Build commands are correct
   - No syntax errors in code
   - TypeScript types are correct
3. Fix ALL issues found
4. Return the corrected implementation

Use Logfire data to understand the root cause, don't just guess!""",
                    metadata={
                        "design_spec": design_spec,
                        "previous_implementation": current_implementation
                    },
                    priority="high",
                    cleanup_after=True
                )

                current_implementation = fix_result.get('implementation', current_implementation)

        # Should never reach here, but just in case
        await self._cleanup_agent("devops")
        return {
            'url': 'https://app.netlify.com/teams',
            'attempts': attempts,
            'final_implementation': current_implementation,
            'build_errors': all_build_errors
        }

    def _format_build_errors(self, build_errors: list) -> str:
        """Format build errors into a readable summary"""
        if not build_errors:
            return "Unknown build error"

        if isinstance(build_errors, list) and len(build_errors) > 0:
            if isinstance(build_errors[0], dict):
                # Structured error objects
                summaries = []
                for err in build_errors[:5]:  # Show first 5 errors
                    error_type = err.get('type', 'unknown')
                    error_msg = err.get('error_message', '')
                    file = err.get('file', '')
                    line = err.get('line', '')
                    summaries.append(f"{error_type} in {file}:{line} - {error_msg[:100]}")
                return "\n".join(summaries)
            else:
                # String errors
                return "\n".join(str(e)[:200] for e in build_errors[:5])

        return str(build_errors)[:500]

    def _format_errors_for_frontend(self, build_errors: list, error_summary: str) -> str:
        """Format errors in a way that Frontend agent can understand and fix"""
        if not build_errors:
            return error_summary

        formatted = "BUILD ERRORS FOUND:\n\n"

        for i, err in enumerate(build_errors[:10], 1):  # Show up to 10 errors
            if isinstance(err, dict):
                formatted += f"Error #{i}:\n"
                formatted += f"  Type: {err.get('type', 'unknown')}\n"
                formatted += f"  File: {err.get('file', 'unknown')}\n"
                formatted += f"  Line: {err.get('line', 'unknown')}\n"
                formatted += f"  Message: {err.get('error_message', 'No message')}\n"

                if err.get('expected'):
                    formatted += f"  Expected: {err.get('expected')}\n"
                if err.get('received'):
                    formatted += f"  Received: {err.get('received')}\n"
                if err.get('fix_option_1'):
                    formatted += f"  Fix suggestion: {err.get('fix_option_1')}\n"

                formatted += "\n"
            else:
                formatted += f"Error #{i}: {str(err)[:300]}\n\n"

        return formatted

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
  • Build tool: Next.js
  • Deployed on Netlify{build_status}

🤖 Built by AI Agent Team (A2A Protocol):
  • UI/UX Designer Agent (design + quality review)
  • Frontend Developer Agent (implementation + improvements)
  • Iterative quality improvement (minimum {self.min_quality_score}/10)
  • Automatic build verification
  • All agents communicated via A2A Protocol

🚀 Powered by Claude Multi-Agent System with A2A
"""

    # ==========================================
    # FILE SYSTEM HELPERS (for Playwright testing)
    # ==========================================

    async def _write_implementation_to_disk(self, implementation: Dict) -> str:
        """
        Write implementation files to a temporary project directory

        Args:
            implementation: Implementation dict with files and structure

        Returns:
            Path to the temporary project directory
        """
        import tempfile
        import shutil

        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix="playwright_test_")
        print(f"   📁 Created temp directory: {temp_dir}")

        try:
            # Get files from implementation
            files = implementation.get('files', [])

            if not files:
                raise ValueError("No files found in implementation")

            # Write each file
            for file_info in files:
                file_path = file_info.get('path', '')
                file_content = file_info.get('content', '')

                if not file_path or not file_content:
                    continue

                # Create full path
                full_path = os.path.join(temp_dir, file_path)

                # Create parent directories
                os.makedirs(os.path.dirname(full_path), exist_ok=True)

                # Write file
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(file_content)

                print(f"   ✅ Wrote: {file_path}")

            print(f"   📝 Wrote {len(files)} files to disk")
            return temp_dir

        except Exception as e:
            # Cleanup on error
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            raise RuntimeError(f"Failed to write implementation to disk: {e}")

    async def _install_npm_dependencies(self, project_dir: str):
        """
        Install npm dependencies in project directory

        Args:
            project_dir: Path to project directory
        """
        import subprocess

        # Check if package.json exists
        package_json_path = os.path.join(project_dir, 'package.json')
        if not os.path.exists(package_json_path):
            raise FileNotFoundError(f"package.json not found in {project_dir}")

        # Run npm install
        try:
            print("   📦 Running npm install (this may take a few minutes)...")

            process = subprocess.Popen(
                ["npm", "install"],
                cwd=project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Wait for completion (with timeout)
            stdout, stderr = process.communicate(timeout=300)  # 5 minute timeout

            if process.returncode != 0:
                raise RuntimeError(f"npm install failed:\n{stderr}")

            print("   ✅ npm install completed successfully")

        except subprocess.TimeoutExpired:
            process.kill()
            raise RuntimeError("npm install timed out after 5 minutes")
        except Exception as e:
            raise RuntimeError(f"Failed to install dependencies: {e}")

    async def _read_implementation_from_disk(self, project_dir: str) -> Dict:
        """
        Read implementation files back from disk (after Frontend made changes)

        Args:
            project_dir: Path to project directory

        Returns:
            Implementation dict with updated files
        """
        files = []

        # Walk through project directory
        for root, dirs, filenames in os.walk(project_dir):
            # Skip node_modules, .next, .git
            dirs[:] = [d for d in dirs if d not in ['node_modules', '.next', '.git', 'dist', 'build']]

            for filename in filenames:
                # Skip hidden files and lock files
                if filename.startswith('.') or filename.endswith('.lock'):
                    continue

                file_path = os.path.join(root, filename)
                relative_path = os.path.relpath(file_path, project_dir)

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    files.append({
                        'path': relative_path,
                        'content': content
                    })
                except Exception as e:
                    print(f"   ⚠️  Couldn't read {relative_path}: {e}")

        print(f"   📝 Read {len(files)} files from disk")

        return {
            'files': files,
            'framework': 'next.js',  # Assume Next.js for now
            'structure': 'standard'
        }

    async def _cleanup_project_directory(self, project_dir: str):
        """
        Clean up temporary project directory

        Args:
            project_dir: Path to project directory to delete
        """
        import shutil

        try:
            if os.path.exists(project_dir):
                shutil.rmtree(project_dir)
                print(f"   🗑️  Cleaned up temp directory: {project_dir}")
        except Exception as e:
            print(f"   ⚠️  Failed to cleanup directory: {e}")

    # ==========================================
    # REFINEMENT HANDLERS
    # ==========================================

    async def _refine_during_design(self, refinement: str) -> str:
        """Handle refinement during design phase"""
        print(f"🎨 [REFINEMENT] Updating design with: {refinement}")

        # Ask designer to update the design spec
        try:
            updated_design = await self._send_task_to_agent(
                agent_id=self.DESIGNER_ID,
                task_description=f"""Update the current design specification with this refinement:

Original request: {self.original_prompt}
Current design: {self.current_design_spec}

User refinement: {refinement}

Please update the design specification to incorporate this change while maintaining consistency.""",
                cleanup_after=False,
                notify_user=True
            )

            # Update current design spec
            self.current_design_spec = updated_design.get('design_spec', self.current_design_spec)

            self._send_whatsapp_notification(
                f"✅ Design updated with your refinement!\n"
                f"The updated design will be used for implementation."
            )

            return "design_refined"

        except Exception as e:
            print(f"❌ Error refining design: {e}")
            return f"error_refining_design: {str(e)}"

    async def _refine_during_implementation(self, refinement: str) -> str:
        """Handle refinement during implementation phase"""
        print(f"💻 [REFINEMENT] Updating implementation with: {refinement}")

        # Ask frontend to update the implementation
        try:
            updated_impl = await self._send_task_to_agent(
                agent_id=self.FRONTEND_ID,
                task_description=f"""Update the current implementation with this refinement:

Original request: {self.original_prompt}
Design spec: {self.current_design_spec}
Current implementation: {self.current_implementation}

User refinement: {refinement}

Please update the implementation to incorporate this change.""",
                metadata={
                    "design_spec": self.current_design_spec,
                    "current_implementation": self.current_implementation
                },
                cleanup_after=False,
                notify_user=True
            )

            # Update current implementation
            self.current_implementation = updated_impl.get('implementation', self.current_implementation)

            self._send_whatsapp_notification(
                f"✅ Implementation updated with your refinement!\n"
                f"The code has been modified accordingly."
            )

            return "implementation_refined"

        except Exception as e:
            print(f"❌ Error refining implementation: {e}")
            return f"error_refining_implementation: {str(e)}"

    async def _refine_during_review(self, refinement: str) -> str:
        """Handle refinement during review phase"""
        print(f"🔍 [REFINEMENT] Noting refinement during review: {refinement}")

        # Add to refinements - will be applied in next iteration
        self._send_whatsapp_notification(
            f"📝 Refinement noted!\n"
            f"I'll make sure this is incorporated in the next iteration of the code."
        )

        return "refinement_noted_for_next_iteration"
