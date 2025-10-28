"""
Testing Coordinator

Coordinates iterative testing workflows between Designer, Frontend, and QA agents.
Manages design review loops and QA testing loops with Playwright.
"""

import os
import sys
from enum import Enum
from typing import Dict, List, Optional, TYPE_CHECKING
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from playwright_mcp.session_manager import PlaywrightSessionManager

if TYPE_CHECKING:
    from .orchestrator import CollaborativeOrchestrator

logger = logging.getLogger(__name__)


class TestingPhase(Enum):
    """Testing workflow phases"""
    DESIGN_REVIEW = "design_review"           # Designer reviews UI
    DESIGN_FEEDBACK = "design_feedback"       # Designer provides feedback
    FRONTEND_FIXES = "frontend_fixes"         # Frontend makes changes
    QA_TESTING = "qa_testing"                 # Code Reviewer runs E2E tests
    QA_REPORTING = "qa_reporting"             # Code Reviewer reports issues
    ISSUE_RESOLUTION = "issue_resolution"     # Frontend/Backend fix bugs
    APPROVED = "approved"                     # All tests passed


class TestingCoordinator:
    """Coordinates iterative testing workflow"""

    def __init__(self, orchestrator: 'CollaborativeOrchestrator'):
        """
        Initialize testing coordinator

        Args:
            orchestrator: CollaborativeOrchestrator instance for agent coordination
        """
        self.orchestrator = orchestrator
        self.current_phase: Optional[TestingPhase] = None
        self.iteration_count = 0
        self.max_iterations = int(os.getenv('MAX_TESTING_ITERATIONS', '5'))
        self.design_feedback_history: List[Dict] = []
        self.qa_issues_history: List[Dict] = []

    async def run_design_review_loop(self, project_dir: str) -> Dict:
        """
        Run Designer's visual review loop with Playwright

        Workflow:
        1. Start dev server on localhost
        2. Designer takes screenshots via Playwright
        3. Designer analyzes screenshots vs design spec
        4. Designer provides visual feedback
        5. Frontend makes changes
        6. Repeat until approved or max iterations

        Args:
            project_dir: Path to project directory containing the webapp

        Returns:
            Dictionary with status and iteration count:
            - status: "approved" | "max_iterations" | "error"
            - iterations: Number of iterations completed
            - final_score: Final design score (0-10)
        """
        logger.info("\n🎨 === DESIGN REVIEW PHASE ===")
        await self._send_notification("🎨 Starting design review with visual testing...")

        self.current_phase = TestingPhase.DESIGN_REVIEW
        iteration = 0

        while iteration < self.max_iterations:
            iteration += 1
            self.iteration_count = iteration
            logger.info(f"\n🔄 Design Review Iteration {iteration}/{self.max_iterations}")
            await self._send_notification(
                f"🔄 Design review iteration {iteration}/{self.max_iterations}..."
            )

            try:
                # Create Playwright session (starts dev server)
                session_manager = PlaywrightSessionManager(project_dir, timeout=90)

                async with session_manager.create_session() as server_url:
                    logger.info(f"🌐 Dev server ready at {server_url}")

                    # Designer performs visual review with Playwright
                    review_result = await self._designer_visual_review(server_url, iteration)

                    # Check approval
                    if review_result.get('approved', False):
                        logger.info(f"✅ Design approved! (Score: {review_result.get('score', 'N/A')}/10)")
                        await self._send_notification(
                            f"✅ Design approved! Final score: {review_result.get('score', 10)}/10"
                        )
                        return {
                            "status": "approved",
                            "iterations": iteration,
                            "final_score": review_result.get('score', 10)
                        }

                    # Get feedback
                    feedback = review_result.get('feedback', [])
                    score = review_result.get('score', 0)
                    self.design_feedback_history.append({
                        'iteration': iteration,
                        'score': score,
                        'feedback': feedback
                    })

                    logger.info(f"📊 Design score: {score}/10 ({len(feedback)} issues)")
                    await self._send_notification(
                        f"📊 Design score: {score}/10 - Found {len(feedback)} visual issues"
                    )

                    # If last iteration, don't request fixes
                    if iteration >= self.max_iterations:
                        break

                    # Send feedback to frontend for fixes
                    await self._send_notification("🔧 Sending feedback to Frontend agent...")
                    await self._frontend_apply_feedback(feedback, iteration)

            except Exception as e:
                logger.error(f"❌ Error in design review iteration {iteration}: {e}")
                await self._send_notification(f"⚠️ Error in design review: {str(e)}")
                return {
                    "status": "error",
                    "iterations": iteration,
                    "error": str(e)
                }

        # Max iterations reached
        logger.warning(f"⚠️ Design review reached max iterations ({self.max_iterations})")
        await self._send_notification(
            f"⚠️ Design review completed {self.max_iterations} iterations. Proceeding with current implementation."
        )
        return {
            "status": "max_iterations",
            "iterations": iteration,
            "final_score": self.design_feedback_history[-1]['score'] if self.design_feedback_history else 0
        }

    async def _designer_visual_review(self, server_url: str, iteration: int) -> Dict:
        """
        Have Designer agent perform visual review using Playwright

        Args:
            server_url: URL of dev server (e.g., "http://localhost:3000")
            iteration: Current iteration number

        Returns:
            Review result with approval status, score, and feedback
        """
        logger.info(f"🎨 Designer performing visual review (iteration {iteration})...")

        # Get designer agent
        designer = self.orchestrator._get_or_create_agent('designer')

        # Prepare context for designer
        context = {
            'server_url': server_url,
            'iteration': iteration,
            'previous_feedback': self.design_feedback_history,
            'task': 'visual_review'
        }

        # Send task to designer
        from .handoff_models import Task, TaskType

        task = Task(
            task_type=TaskType.VISUAL_REVIEW,
            description=f"Perform visual design review using Playwright. Navigate to {server_url}, take screenshots, analyze against design spec.",
            context=context,
            from_agent='orchestrator'
        )

        # Designer executes visual review
        response = await designer.handle_task(task)

        # Parse response
        if response.status == 'completed':
            return response.result
        else:
            logger.error(f"❌ Designer visual review failed: {response.error_message}")
            return {
                'approved': False,
                'score': 0,
                'feedback': [{
                    'issue': f"Visual review failed: {response.error_message}",
                    'severity': 'critical'
                }]
            }

    async def _frontend_apply_feedback(self, feedback: List[Dict], iteration: int):
        """
        Send design feedback to Frontend agent for fixes

        Args:
            feedback: List of feedback items from designer
            iteration: Current iteration number
        """
        logger.info(f"🔧 Sending {len(feedback)} feedback items to Frontend agent...")

        # Get frontend agent
        frontend = self.orchestrator._get_or_create_agent('frontend')

        # Prepare context
        context = {
            'feedback': feedback,
            'iteration': iteration,
            'task': 'apply_design_feedback'
        }

        # Send task to frontend
        from .handoff_models import Task, TaskType

        task = Task(
            task_type=TaskType.IMPLEMENT,
            description=f"Apply visual design feedback from iteration {iteration}. Make targeted fixes to match design specification.",
            context=context,
            from_agent='orchestrator'
        )

        # Frontend applies feedback
        response = await frontend.handle_task(task)

        if response.status == 'completed':
            logger.info(f"✅ Frontend applied feedback successfully")
        else:
            logger.error(f"❌ Frontend failed to apply feedback: {response.error_message}")

    async def _send_notification(self, message: str):
        """
        Send notification to user via orchestrator's notification adapter

        Args:
            message: Notification message
        """
        try:
            if hasattr(self.orchestrator, 'notification_adapter') and self.orchestrator.notification_adapter:
                await self.orchestrator.notification_adapter.send_message(
                    self.orchestrator.phone_number,
                    message
                )
        except Exception as e:
            logger.warning(f"⚠️ Failed to send notification: {e}")

    async def run_qa_testing_loop(self, project_dir: str, functional_spec: Optional[Dict] = None) -> Dict:
        """
        Run QA's E2E testing loop with Playwright

        Workflow:
        1. Start dev server on localhost
        2. Code Reviewer discovers all interactive elements via DOM inspection
        3. Code Reviewer tests each element systematically (buttons, forms, links)
        4. Code Reviewer verifies functionality, not visuals (uses playwright_evaluate)
        5. If tests fail, Frontend/Backend fix issues
        6. Repeat until approved or max iterations

        Args:
            project_dir: Path to project directory containing the webapp
            functional_spec: Optional specification of expected functionality

        Returns:
            Dictionary with status and test results:
            - status: "approved" | "max_iterations" | "error"
            - iterations: Number of iterations completed
            - pass_rate: Final pass rate percentage
            - test_results: Detailed test results
        """
        logger.info("\n🧪 === QA TESTING PHASE ===")
        await self._send_notification("🧪 Starting QA functional testing...")

        self.current_phase = TestingPhase.QA_TESTING
        iteration = 0

        while iteration < self.max_iterations:
            iteration += 1
            self.iteration_count = iteration
            logger.info(f"\n🔄 QA Testing Iteration {iteration}/{self.max_iterations}")
            await self._send_notification(
                f"🔄 QA testing iteration {iteration}/{self.max_iterations}..."
            )

            try:
                # Create Playwright session (starts dev server)
                session_manager = PlaywrightSessionManager(project_dir, timeout=90)

                async with session_manager.create_session() as server_url:
                    logger.info(f"🌐 Dev server ready at {server_url}")

                    # Code Reviewer performs E2E testing with Playwright
                    test_result = await self._code_reviewer_qa_testing(
                        server_url,
                        iteration,
                        functional_spec
                    )

                    # Check approval
                    if test_result.get('approved', False):
                        pass_rate = test_result.get('pass_rate', 100)
                        logger.info(f"✅ QA tests passed! (Pass rate: {pass_rate:.1f}%)")
                        await self._send_notification(
                            f"✅ QA tests passed! Pass rate: {pass_rate:.1f}% ({test_result.get('passed_count', 0)}/{test_result.get('test_count', 0)} tests)"
                        )
                        return {
                            "status": "approved",
                            "iterations": iteration,
                            "pass_rate": pass_rate,
                            "test_results": test_result
                        }

                    # Get issues
                    issues = test_result.get('issues', [])
                    pass_rate = test_result.get('pass_rate', 0)
                    critical_issues = test_result.get('critical_issues', [])
                    self.qa_issues_history.append({
                        'iteration': iteration,
                        'pass_rate': pass_rate,
                        'issues': issues
                    })

                    logger.info(f"📊 QA pass rate: {pass_rate:.1f}% ({len(issues)} issues, {len(critical_issues)} critical)")
                    await self._send_notification(
                        f"📊 QA pass rate: {pass_rate:.1f}% - Found {len(issues)} issues ({len(critical_issues)} critical)"
                    )

                    # If last iteration, don't request fixes
                    if iteration >= self.max_iterations:
                        break

                    # Send issues to appropriate agent for fixes
                    await self._send_notification("🔧 Sending issues to agents for fixes...")
                    await self._apply_qa_fixes(issues, iteration)

            except Exception as e:
                logger.error(f"❌ Error in QA testing iteration {iteration}: {e}")
                await self._send_notification(f"⚠️ Error in QA testing: {str(e)}")
                return {
                    "status": "error",
                    "iterations": iteration,
                    "error": str(e)
                }

        # Max iterations reached
        final_pass_rate = self.qa_issues_history[-1]['pass_rate'] if self.qa_issues_history else 0
        logger.warning(f"⚠️ QA testing reached max iterations ({self.max_iterations})")
        await self._send_notification(
            f"⚠️ QA testing completed {self.max_iterations} iterations. Final pass rate: {final_pass_rate:.1f}%"
        )
        return {
            "status": "max_iterations",
            "iterations": iteration,
            "pass_rate": final_pass_rate
        }

    async def _code_reviewer_qa_testing(
        self,
        server_url: str,
        iteration: int,
        functional_spec: Optional[Dict] = None
    ) -> Dict:
        """
        Have Code Reviewer agent perform E2E QA testing using Playwright

        Args:
            server_url: URL of dev server (e.g., "http://localhost:3000")
            iteration: Current iteration number
            functional_spec: Optional specification of expected functionality

        Returns:
            Test result with pass rate, issues, and test details
        """
        logger.info(f"🧪 Code Reviewer performing QA testing (iteration {iteration})...")

        # Get code reviewer agent
        code_reviewer = self.orchestrator._get_or_create_agent('code_reviewer')

        # Call the perform_qa_testing method directly
        test_result = await code_reviewer.perform_qa_testing(
            server_url=server_url,
            iteration=iteration,
            functional_spec=functional_spec,
            previous_test_results=self.qa_issues_history[-1] if self.qa_issues_history else None
        )

        return test_result

    async def _apply_qa_fixes(self, issues: List[Dict], iteration: int):
        """
        Send QA issues to Frontend/Backend agents for fixes

        Args:
            issues: List of issues found during QA testing
            iteration: Current iteration number
        """
        if not issues:
            return

        logger.info(f"🔧 Sending {len(issues)} QA issues for fixes...")

        # Separate frontend and backend issues
        frontend_issues = [i for i in issues if self._is_frontend_issue(i)]
        backend_issues = [i for i in issues if self._is_backend_issue(i)]

        # Send frontend issues
        if frontend_issues:
            await self._send_notification(f"🔧 Fixing {len(frontend_issues)} frontend issues...")
            await self._frontend_fix_issues(frontend_issues, iteration)

        # Send backend issues
        if backend_issues:
            await self._send_notification(f"🔧 Fixing {len(backend_issues)} backend issues...")
            await self._backend_fix_issues(backend_issues, iteration)

    def _is_frontend_issue(self, issue: Dict) -> bool:
        """Determine if issue is frontend-related"""
        frontend_keywords = ['button', 'form', 'link', 'input', 'ui', 'click', 'validation', 'display']
        issue_text = (issue.get('issue', '') + ' ' + issue.get('element', '')).lower()
        return any(keyword in issue_text for keyword in frontend_keywords)

    def _is_backend_issue(self, issue: Dict) -> bool:
        """Determine if issue is backend-related"""
        backend_keywords = ['api', 'endpoint', 'database', 'server', 'response', 'data']
        issue_text = issue.get('issue', '').lower()
        return any(keyword in issue_text for keyword in backend_keywords)

    async def _frontend_fix_issues(self, issues: List[Dict], iteration: int):
        """Send issues to Frontend agent for fixes"""
        frontend = self.orchestrator._get_or_create_agent('frontend')

        context = {
            'issues': issues,
            'iteration': iteration,
            'task': 'fix_qa_issues'
        }

        from .handoff_models import Task, TaskType

        task = Task(
            task_type=TaskType.IMPLEMENT,
            description=f"Fix QA issues from iteration {iteration}. Issues found: {len(issues)}",
            context=context,
            from_agent='orchestrator'
        )

        response = await frontend.handle_task(task)

        if response.status == 'completed':
            logger.info(f"✅ Frontend fixed QA issues successfully")
        else:
            logger.error(f"❌ Frontend failed to fix issues: {response.error_message}")

    async def _backend_fix_issues(self, issues: List[Dict], iteration: int):
        """Send issues to Backend agent for fixes"""
        backend = self.orchestrator._get_or_create_agent('backend')

        context = {
            'issues': issues,
            'iteration': iteration,
            'task': 'fix_qa_issues'
        }

        from .handoff_models import Task, TaskType

        task = Task(
            task_type=TaskType.IMPLEMENT,
            description=f"Fix QA issues from iteration {iteration}. Issues found: {len(issues)}",
            context=context,
            from_agent='orchestrator'
        )

        response = await backend.handle_task(task)

        if response.status == 'completed':
            logger.info(f"✅ Backend fixed QA issues successfully")
        else:
            logger.error(f"❌ Backend failed to fix issues: {response.error_message}")

    def get_design_feedback_summary(self) -> Dict:
        """
        Get summary of all design feedback iterations

        Returns:
            Summary dictionary with scores and feedback across iterations
        """
        if not self.design_feedback_history:
            return {"iterations": 0, "feedback": []}

        return {
            "iterations": len(self.design_feedback_history),
            "scores": [item['score'] for item in self.design_feedback_history],
            "feedback": self.design_feedback_history
        }

    def get_qa_testing_summary(self) -> Dict:
        """
        Get summary of all QA testing iterations

        Returns:
            Summary dictionary with pass rates and issues across iterations
        """
        if not self.qa_issues_history:
            return {"iterations": 0, "issues": []}

        return {
            "iterations": len(self.qa_issues_history),
            "pass_rates": [item['pass_rate'] for item in self.qa_issues_history],
            "issues": self.qa_issues_history
        }
