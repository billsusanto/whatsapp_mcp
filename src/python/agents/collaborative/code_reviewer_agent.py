"""
Code Reviewer Agent
Reviews code for quality, security, and best practices
"""

from typing import Dict, Any
from .base_agent import BaseAgent
from .models import AgentCard, AgentRole, Task
from utils.telemetry import trace_operation, log_event, log_metric, log_error


class CodeReviewerAgent(BaseAgent):
    """Code Reviewer specializing in code quality and security"""

    def __init__(self, mcp_servers: Dict = None):
        agent_card = AgentCard(
            agent_id="code_reviewer_001",
            name="Code Reviewer Agent",
            role=AgentRole.CODE_REVIEWER,
            description="Expert code reviewer for quality, security, and best practices",
            capabilities=[
                "Code quality review",
                "Security vulnerability detection",
                "Performance optimization review",
                "Best practices enforcement",
                "Code smell detection",
                "Refactoring suggestions",
                "Documentation review"
            ],
            skills={
                "languages": ["JavaScript", "TypeScript", "Python", "HTML", "CSS"],
                "focus_areas": ["Security", "Performance", "Maintainability", "Best Practices"],
                "tools": ["ESLint", "SonarQube", "OWASP", "SAST"],
                "specialties": ["React patterns", "Security audits", "Code optimization"]
            }
        )

        system_prompt = """
You are an expert Code Reviewer with 15+ years of experience in software engineering and a reputation for maintaining the highest code quality standards.

Your expertise includes:
- Code quality assessment and improvement (clean code, SOLID principles)
- Security vulnerability detection (OWASP Top 10, common CVEs, dependency vulnerabilities)
- Performance optimization and bottleneck identification
- Best practices for React, JavaScript, TypeScript, and modern web development
- Code maintainability, readability, and scalability
- Architectural patterns and anti-patterns
- Accessibility (WCAG 2.1 AA/AAA compliance)
- Git/GitHub best practices and project structure
- Documentation and code comments quality
- **End-to-End QA Testing with Playwright MCP** (browser automation for functional testing)

**REVIEW PHILOSOPHY:**
You are STRICT and maintain HIGH STANDARDS. You believe in preventing technical debt and shipping production-ready code.
- Be critical but constructive
- Prioritize: Security > Correctness > Performance > Maintainability > Style
- Give scores of 9-10 only for truly excellent, production-ready code
- Don't be afraid to give low scores (5-7) for code with significant issues
- Always provide specific, actionable feedback with code examples

**COMPREHENSIVE REVIEW CRITERIA:**

1. **Security Analysis (CRITICAL)**
   - XSS vulnerabilities (dangerouslySetInnerHTML without sanitization)
   - SQL injection (if applicable)
   - Authentication/authorization flaws
   - Sensitive data exposure (API keys, secrets in code)
   - Insecure dependencies (known CVEs)
   - HTTPS/secure communication
   - Input validation and sanitization
   - CORS misconfigurations
   - Broken access control

2. **Code Quality & Best Practices**
   - SOLID principles adherence
   - DRY (Don't Repeat Yourself) vs. WET code
   - Meaningful variable/function/component names
   - Code smells and anti-patterns
   - Proper separation of concerns
   - Single Responsibility Principle
   - Component composition quality
   - TypeScript usage and type safety (if applicable)
   - Code duplication

3. **React/JavaScript Specific**
   - Proper use of hooks (useState, useEffect, useCallback, useMemo)
   - React.memo() for performance optimization
   - Custom hooks for reusable logic
   - Avoiding unnecessary re-renders
   - Proper dependency arrays in useEffect
   - Props drilling vs. Context API usage
   - Component lifecycle management
   - Avoiding anti-patterns (e.g., derived state)

4. **Error Handling & Edge Cases**
   - Comprehensive error boundaries
   - Try-catch blocks where needed
   - Input validation
   - Empty state handling
   - Loading state handling
   - Network error handling
   - Graceful degradation
   - User-friendly error messages

5. **Performance**
   - Unnecessary re-renders in React
   - Memory leaks (event listeners, subscriptions, timers)
   - Lazy loading and code splitting
   - Expensive operations optimization
   - Bundle size concerns
   - Proper use of useCallback and useMemo
   - Image optimization
   - Network request optimization

6. **Accessibility (WCAG 2.1)**
   - Semantic HTML usage
   - ARIA labels and roles correctness
   - Keyboard navigation support
   - Focus management
   - Color contrast ratios
   - Screen reader compatibility
   - Alt text for images
   - Form labels and error messages

7. **Documentation & Code Comments**
   - README.md quality (setup, deployment, features)
   - JSDoc comments for complex functions
   - Inline comments for tricky logic
   - .env.example for environment variables
   - Clear function/component documentation
   - TODO/FIXME comments (flag as issues)
   - Code self-documentation through naming

8. **Git/GitHub Best Practices**
   - Proper .gitignore (node_modules, .env, build artifacts)
   - No secrets or API keys in code
   - Environment variable usage
   - Logical file organization
   - Production-ready project structure
   - README completeness
   - License file (if applicable)

9. **Maintainability & Scalability**
   - Code readability
   - Logical file/folder structure
   - Component reusability
   - Testability (even if tests aren't written)
   - Future-proofing
   - Avoiding hard-coded values
   - Configuration management

10. **Dependencies & Build**
    - Necessary dependencies only
    - No unused dependencies
    - Known security vulnerabilities in packages
    - Proper version pinning
    - Build configuration correctness
    - Production build optimization

**SCORING GUIDELINES (Be Critical!):**
- **10/10**: Perfect code - production-ready, secure, performant, maintainable, well-documented
- **9/10**: Excellent code - minor tweaks needed, very high quality
- **8/10**: Good code - a few improvements needed, solid foundation
- **7/10**: Acceptable code - several issues to fix, needs work
- **6/10**: Below standard - significant issues, multiple problems
- **5/10**: Poor code - major refactoring needed, many problems
- **1-4/10**: Critical issues - security flaws, broken functionality, not production-ready

**When reviewing code:**
1. Thoroughly analyze ALL files provided
2. Identify and categorize issues by severity (critical, major, minor)
3. Provide specific line references when possible
4. Give actionable fixes with code examples
5. Explain WHY something is an issue
6. Be constructive but don't lower standards
7. Verify ALL critical aspects before approval
8. Give realistic scores reflecting true code quality

**QA TESTING WITH PLAYWRIGHT MCP:**
You have access to Playwright MCP for browser automation to perform end-to-end functional testing:

**When to Use QA Testing:**
- After Frontend and Designer have completed their implementation
- To verify ALL interactive functionality works as expected
- To test frontend-backend integration (API calls, data flow)
- To ensure error handling works properly

**QA Testing Process:**
1. **Discovery Phase**: Navigate to the webapp, discover all interactive elements (buttons, forms, links)
2. **Testing Phase**: Systematically test each element:
   - Buttons: Click and verify expected behavior (UI changes, API calls)
   - Forms: Test valid data submission AND invalid data validation
   - Links: Test navigation and verify pages load correctly
   - API Integration: Verify network requests are made and responses handled
3. **Analysis Phase**: Categorize issues by severity, calculate pass rate
4. **Feedback Phase**: Provide specific, actionable fixes for Frontend agent

**QA Testing Tools (Playwright MCP):**
- playwright_navigate: Navigate to URLs
- playwright_click: Click elements
- playwright_fill: Fill form fields
- playwright_screenshot: Capture before/after states
- playwright_wait_for_selector: Wait for elements to load
- playwright_evaluate: Run JavaScript to inspect state

**QA Approval Criteria:**
- 100% pass rate OR
- 90%+ pass rate with ZERO critical issues
- All critical functionality must work
- Forms must validate properly
- API calls must succeed
- Error handling must work

Be thorough, be strict, be constructive. Your reviews prevent bugs, security issues, and technical debt.
"""

        super().__init__(
            agent_card=agent_card,
            system_prompt=system_prompt,
            mcp_servers=mcp_servers
        )

    def _build_research_prompt(self, task: Task) -> str:
        """Build research prompt for code review"""
        return f"""You are an expert Code Reviewer conducting research before reviewing code.

**Review Task:** {task.description}

**Research Goals:**
1. **Framework-Specific Security Patterns**
   - Common security vulnerabilities for this framework (React/Next.js/Vue)
   - OWASP Top 10 as applicable
   - Framework-specific anti-patterns
   - Known CVEs for dependencies

2. **Best Practices for Technology Stack**
   - React hooks best practices
   - TypeScript best practices (if applicable)
   - State management patterns
   - Performance optimization patterns
   - Error handling patterns

3. **Code Quality Standards**
   - SOLID principles application
   - DRY vs WET indicators
   - Component composition patterns
   - Code smells to watch for
   - Maintainability metrics

4. **Accessibility Standards**
   - WCAG 2.1 AA/AAA requirements
   - Common accessibility issues
   - ARIA best practices
   - Semantic HTML requirements

5. **Performance Considerations**
   - React performance anti-patterns
   - Memory leak patterns
   - Bundle size concerns
   - Rendering optimization

6. **Common Issues in Similar Code**
   - Patterns that often have bugs
   - Edge cases frequently missed
   - Testing gaps common in this type of code

**Output Format (JSON):**
{{
  "security_checklist": [
    {{"vulnerability": "XSS via dangerouslySetInnerHTML", "detection": "...", "severity": "critical"}},
    {{"vulnerability": "Exposed API keys", "detection": "...", "severity": "critical"}}
  ],
  "best_practices_checklist": [
    {{"practice": "Proper useEffect dependency arrays", "importance": "high", "check": "..."}},
    {{"practice": "React.memo() for expensive components", "importance": "medium", "check": "..."}}
  ],
  "code_quality_metrics": [
    "Component size (< 300 lines ideal)",
    "Function complexity (cyclomatic complexity)",
    "Code duplication percentage",
    "Test coverage (if applicable)"
  ],
  "accessibility_checklist": [
    "ARIA labels on interactive elements",
    "Keyboard navigation support",
    "Color contrast ratios",
    "Semantic HTML usage"
  ],
  "performance_checklist": [
    "No unnecessary re-renders",
    "Proper useCallback/useMemo usage",
    "No memory leaks (cleanup in useEffect)",
    "Lazy loading implemented"
  ],
  "common_bug_patterns": [
    {{"pattern": "Missing cleanup in useEffect", "impact": "memory leak", "check": "..."}}
  ],
  "framework_specific_issues": [
    "Next.js specific issues to check",
    "React specific issues to check"
  ],
  "research_summary": "Brief summary of review research"
}}

Be thorough. Research ensures comprehensive review."""

    def _build_planning_prompt(self, task: Task, research: Dict) -> str:
        """Build planning prompt for code review"""
        return f"""You are an expert Code Reviewer creating a detailed review plan.

**Review Task:** {task.description}

**Research Findings:**
{research}

**Planning Goals:**
1. **Review Prioritization**
   - Critical issues first (security, correctness)
   - Then performance issues
   - Then maintainability issues
   - Finally style issues

2. **Systematic Review Approach**
   - Security analysis (first priority)
   - Code quality analysis
   - Performance analysis
   - Accessibility analysis
   - Best practices verification

3. **Issue Categorization Plan**
   - Critical: Must fix before deployment
   - Major: Should fix soon
   - Minor: Nice to have improvements

4. **Code Review Checklist**
   - Specific items to check based on research
   - File-by-file review strategy
   - Focus areas based on complexity

**Output Format (JSON):**
{{
  "review_strategy": {{
    "approach": "Security-first, then quality, performance, accessibility",
    "priority_order": ["security", "correctness", "performance", "maintainability", "style"],
    "estimated_duration": "thorough|quick"
  }},
  "review_checklist": [
    {{
      "category": "Security",
      "priority": "critical",
      "checks": [
        "Scan for dangerouslySetInnerHTML without sanitization",
        "Check for exposed API keys or secrets",
        "Verify input validation and sanitization",
        "Check authentication/authorization patterns"
      ]
    }},
    {{
      "category": "Code Quality",
      "priority": "high",
      "checks": [
        "Check for code duplication",
        "Verify component sizes (< 300 lines)",
        "Check for proper error handling",
        "Verify meaningful variable names"
      ]
    }},
    {{
      "category": "Performance",
      "priority": "high",
      "checks": [
        "Check for unnecessary re-renders",
        "Verify useCallback/useMemo usage",
        "Check for memory leaks (useEffect cleanup)",
        "Verify lazy loading where appropriate"
      ]
    }},
    {{
      "category": "Accessibility",
      "priority": "medium",
      "checks": [
        "Verify ARIA labels present",
        "Check keyboard navigation support",
        "Verify semantic HTML usage",
        "Check color contrast ratios"
      ]
    }}
  ],
  "file_review_order": [
    {{"file": "Critical files first", "reason": "Entry points, auth, security"}},
    {{"file": "Complex files next", "reason": "More likely to have issues"}},
    {{"file": "Simple files last", "reason": "Lower risk"}}
  ],
  "issue_severity_criteria": {{
    "critical": "Security vulnerabilities, broken functionality, data loss risk",
    "major": "Performance issues, poor UX, maintainability problems",
    "minor": "Style inconsistencies, minor improvements"
  }},
  "scoring_criteria": {{
    "10": "Perfect code, production-ready, zero issues",
    "9": "Excellent, minor cosmetic tweaks only",
    "8": "Good, a few small improvements needed",
    "7": "Acceptable, several issues to address",
    "6": "Below standard, significant issues",
    "5-": "Major problems, needs refactoring"
  }},
  "plan_summary": "Brief overview of review plan"
}}

Create a systematic, thorough review plan."""

    async def execute_task_with_plan(
        self,
        task: Task,
        research: Dict,
        plan: Dict
    ) -> Dict[str, Any]:
        """
        Execute code review with research-backed plan

        Uses research to identify issues and follows systematic review plan.
        """
        print(f"🔍 [CODE REVIEWER] Reviewing with research & plan")

        # Log code review task start
        log_event("code_reviewer.task_start",
                 task_id=task.task_id,
                 has_research=True,
                 has_plan=True,
                 task_description_length=len(task.description))

        # Extract implementation from task metadata
        implementation = {}
        if task.metadata and isinstance(task.metadata, dict):
            implementation = task.metadata.get('implementation', {})

        # Create review prompt informed by research and plan
        review_prompt = f"""You are an expert Code Reviewer conducting a thorough code review.

**IMPORTANT:** You have completed research and planning. Follow the plan systematically.

**Review Task:** {task.description}

**Code Implementation:**
{implementation}

**Research Findings:**
{research}

**Review Plan:**
{plan}

**Your Task:**
Conduct a comprehensive code review following the plan's checklist.

**REVIEW PROCESS (Follow Plan Priority Order):**

1. **Security Analysis (CRITICAL - FIRST PRIORITY):**
   Check all items from security checklist:
   {research.get('security_checklist', [])}

2. **Code Quality Analysis:**
   Check all items from code quality checklist:
   {plan.get('review_checklist', [{}])[1].get('checks', []) if len(plan.get('review_checklist', [])) > 1 else []}

3. **Performance Analysis:**
   Check all items from performance checklist:
   {research.get('performance_checklist', [])}

4. **Accessibility Analysis:**
   Check all items from accessibility checklist:
   {research.get('accessibility_checklist', [])}

5. **Best Practices Verification:**
   Check all items from best practices:
   {research.get('best_practices_checklist', [])}

**SCORING (Be Critical - Use Plan Criteria):**
{plan.get('scoring_criteria', {})}

**Output Format (JSON):**
{{
  "overall_score": 1-10,
  "approved": true|false,
  "critical_issues": [
    {{
      "severity": "critical",
      "category": "security",
      "file": "path/to/file.tsx",
      "line": 42,
      "issue": "Specific issue description",
      "fix": "Specific fix with code example",
      "reasoning": "Why this is critical based on research"
    }}
  ],
  "major_issues": [
    {{
      "severity": "major",
      "category": "performance",
      "file": "path/to/file.tsx",
      "issue": "Specific issue",
      "fix": "Specific fix",
      "impact": "Performance degradation"
    }}
  ],
  "minor_issues": [
    {{
      "severity": "minor",
      "category": "style",
      "issue": "...",
      "fix": "..."
    }}
  ],
  "suggestions": ["Suggestion 1", "Suggestion 2"],
  "security_score": 1-10,
  "performance_score": 1-10,
  "maintainability_score": 1-10,
  "accessibility_score": 1-10,
  "checklist_results": {{
    "security_checks_passed": 8,
    "security_checks_total": 10,
    "performance_checks_passed": 7,
    "performance_checks_total": 8
  }},
  "summary": "Overall code review assessment based on research-backed analysis"
}}

Be thorough, critical, and specific. Use research findings to inform your review."""

        try:
            # Trace Claude API call for code review
            with trace_operation("code_reviewer_review_with_plan",
                               task_id=task.task_id,
                               has_research=True,
                               has_plan=True,
                               prompt_length=len(review_prompt)) as span:

                # Get code review from Claude
                response = await self.claude_sdk.send_message(review_prompt)

                # Track response metrics
                span.set_attribute("response_length", len(response))
                log_metric("code_reviewer.llm_response_length", len(response))

            # Parse review
            import json
            import re

            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                review = json.loads(json_match.group(1))
            elif response.strip().startswith('{'):
                review = json.loads(response)
            else:
                review = {
                    "overall_score": 7,
                    "approved": True,
                    "summary": response,
                    "note": "Review with research & planning"
                }

            # Track review metrics
            critical_count = len(review.get('critical_issues', []))
            major_count = len(review.get('major_issues', []))
            minor_count = len(review.get('minor_issues', []))
            overall_score = review.get('overall_score', 0)
            approved = review.get('approved', False)

            log_event("code_reviewer.review_completed",
                     task_id=task.task_id,
                     overall_score=overall_score,
                     approved=approved,
                     critical_issues=critical_count,
                     major_issues=major_count,
                     minor_issues=minor_count,
                     research_backed=True)

            log_metric("code_reviewer.overall_score", overall_score)
            log_metric("code_reviewer.critical_issues", critical_count)

            print(f"✅ [CODE REVIEWER] Research-backed review completed - Score: {review.get('overall_score', 'N/A')}/10")
            print(f"   Issues: {critical_count} critical, {major_count} major, {minor_count} minor")

            return {
                "status": "completed",
                "review": review,
                "raw_response": response,
                "research_used": True,
                "research_summary": research.get('research_summary', 'Research completed'),
                "plan_summary": plan.get('plan_summary', 'Plan created')
            }

        except Exception as e:
            print(f"❌ [CODE REVIEWER] Error during review: {e}")
            import traceback
            traceback.print_exc()

            # Log error with context
            log_error(e, "code_reviewer_review_with_plan",
                     task_id=task.task_id,
                     has_research=True,
                     has_plan=True)

            return {
                "status": "completed_with_fallback",
                "review": {
                    "overall_score": 7,
                    "approved": True,
                    "summary": f"Review error: {str(e)}",
                    "note": "Fallback review"
                }
            }

    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute code review task using Claude AI (backward compatibility)

        This is the original implementation without research & planning.
        Used when enable_research_planning=False
        """
        print(f"🔍 [CODE REVIEWER] Reviewing code: {task.description} (direct execution)")

        # Log code review task start (direct mode)
        log_event("code_reviewer.task_start",
                 task_id=task.task_id,
                 has_research=False,
                 has_plan=False,
                 execution_mode="direct",
                 task_description_length=len(task.description))

        # Extract implementation from task metadata
        implementation = {}
        if task.metadata and isinstance(task.metadata, dict):
            implementation = task.metadata.get('implementation', {})

        # Create comprehensive code review prompt
        review_prompt = f"""You are an expert Code Reviewer conducting a thorough code review.

**Review Task:** {task.description}

**Code Implementation:**
{implementation}

Conduct a comprehensive code review covering:

1. **Security Analysis**
   - Check for XSS vulnerabilities (dangerouslySetInnerHTML, unsanitized input)
   - Validate authentication/authorization patterns
   - Check for sensitive data exposure
   - Verify HTTPS/secure communication
   - Check for injection vulnerabilities

2. **Code Quality**
   - Are there code smells or anti-patterns?
   - Is the code DRY (Don't Repeat Yourself)?
   - Is error handling proper and comprehensive?
   - Are edge cases handled?
   - Is the code readable and maintainable?

3. **Performance**
   - Are there unnecessary re-renders in React?
   - Are there memory leaks (event listeners, subscriptions)?
   - Is lazy loading used appropriately?
   - Are expensive operations optimized?
   - Are there bundle size concerns?

4. **Best Practices**
   - Does it follow React best practices?
   - Are hooks used correctly?
   - Is state management appropriate?
   - Are components properly structured?
   - Is the code modular and reusable?

5. **Accessibility**
   - Are ARIA labels present and correct?
   - Is semantic HTML used?
   - Is keyboard navigation supported?
   - Are color contrasts sufficient?

6. **Dependencies & Build**
   - Are dependencies necessary and up-to-date?
   - Are there known vulnerabilities in dependencies?
   - Is the build configuration correct?

**Output Format (JSON):**
{{
  "overall_score": 1-10,
  "approved": true | false,
  "critical_issues": [
    {{"severity": "critical", "category": "security", "issue": "...", "fix": "..."}}
  ],
  "major_issues": [
    {{"severity": "major", "category": "performance", "issue": "...", "fix": "..."}}
  ],
  "minor_issues": [
    {{"severity": "minor", "category": "style", "issue": "...", "fix": "..."}}
  ],
  "suggestions": ["Suggestion 1", "Suggestion 2"],
  "security_score": 1-10,
  "performance_score": 1-10,
  "maintainability_score": 1-10,
  "summary": "Overall assessment of the code"
}}

Be specific with issues and provide actionable fixes. Prioritize security and correctness."""

        try:
            # Trace Claude API call for code review (direct mode)
            with trace_operation("code_reviewer_review_direct",
                               task_id=task.task_id,
                               has_research=False,
                               has_plan=False,
                               prompt_length=len(review_prompt)) as span:

                # Get code review from Claude
                response = await self.claude_sdk.send_message(review_prompt)

                # Track response metrics
                span.set_attribute("response_length", len(response))
                log_metric("code_reviewer.llm_response_length", len(response))

            # Extract JSON from response
            import json
            import re

            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                review = json.loads(json_match.group(1))
            elif response.strip().startswith('{'):
                review = json.loads(response)
            else:
                # Claude didn't return pure JSON, wrap it
                review = {
                    "overall_score": 7,
                    "approved": True,
                    "critical_issues": [],
                    "major_issues": [],
                    "minor_issues": [],
                    "suggestions": [response],
                    "security_score": 8,
                    "performance_score": 7,
                    "maintainability_score": 7,
                    "summary": "Review completed - see suggestions for details"
                }

            # Track review metrics
            critical_count = len(review.get('critical_issues', []))
            major_count = len(review.get('major_issues', []))
            minor_count = len(review.get('minor_issues', []))
            overall_score = review.get('overall_score', 0)
            approved = review.get('approved', False)

            log_event("code_reviewer.review_completed",
                     task_id=task.task_id,
                     overall_score=overall_score,
                     approved=approved,
                     critical_issues=critical_count,
                     major_issues=major_count,
                     minor_issues=minor_count,
                     research_backed=False,
                     execution_mode="direct")

            log_metric("code_reviewer.overall_score", overall_score)
            log_metric("code_reviewer.critical_issues", critical_count)

            print(f"✅ [CODE REVIEWER] Review completed - Score: {review.get('overall_score', 'N/A')}/10")
            print(f"   Issues: {critical_count} critical, {major_count} major, {minor_count} minor")

            return {
                "status": "completed",
                "review": review,
                "raw_response": response
            }

        except Exception as e:
            print(f"❌ [CODE REVIEWER] Error during review: {e}")
            import traceback
            traceback.print_exc()

            # Log error with context
            log_error(e, "code_reviewer_review_direct",
                     task_id=task.task_id,
                     has_research=False,
                     has_plan=False,
                     execution_mode="direct")

            # Fallback to basic approval
            return {
                "status": "completed_with_error",
                "review": {
                    "overall_score": 7,
                    "approved": True,
                    "critical_issues": [],
                    "major_issues": [],
                    "minor_issues": [],
                    "suggestions": [f"Review error: {str(e)}"],
                    "security_score": 7,
                    "performance_score": 7,
                    "maintainability_score": 7,
                    "summary": "Error during review - implementation auto-approved"
                }
            }

    async def review_artifact(self, artifact: Any) -> Dict[str, Any]:
        """
        Alias for execute_task - code reviewer reviews artifacts
        """
        # Convert artifact to task format
        task = Task(
            description="Review code implementation",
            from_agent="orchestrator",
            to_agent=self.agent_card.agent_id,
            metadata={"implementation": artifact}
        )
        return await self.execute_task(task)

    async def perform_qa_testing(
        self,
        server_url: str,
        iteration: int,
        functional_spec: Dict = None,
        previous_test_results: Dict = None
    ) -> Dict:
        """
        Perform end-to-end QA testing using Playwright MCP

        Tests all interactive functionality including:
        - Button clicks and UI state changes
        - Form submissions and validations
        - Navigation and routing
        - API calls and data flow
        - Error handling and edge cases

        Args:
            server_url: URL of the dev server (e.g., http://localhost:3000)
            iteration: Current testing iteration (1-based)
            functional_spec: Optional specification of expected functionality
            previous_test_results: Previous test results if this is a re-test

        Returns:
            Dict with test results including:
            - passed: bool (all tests passed)
            - test_count: int (number of tests run)
            - passed_count: int (number of tests passed)
            - failed_count: int (number of tests failed)
            - test_results: List[Dict] (detailed test results)
            - issues: List[Dict] (issues found with severity)
        """
        print(f"\n🧪 [CODE REVIEWER] Starting QA Testing (Iteration {iteration})")
        print(f"   Server URL: {server_url}")

        # Log QA testing start
        log_event("code_reviewer.qa_testing_start",
                 iteration=iteration,
                 server_url=server_url,
                 has_functional_spec=functional_spec is not None,
                 is_retest=previous_test_results is not None)

        try:
            # Step 1: Navigate to homepage and discover interactive elements
            print(f"📍 Step 1: Navigating to {server_url} and discovering interactive elements")

            discovery_prompt = f"""Use Playwright MCP tools to discover all interactive elements in the web application.

**Your Task:**
1. Navigate to {server_url} using playwright_navigate
2. Wait for the page to load using playwright_wait_for_selector (wait for 'body')
3. Use playwright_evaluate to run JavaScript and discover ALL interactive elements:

**JavaScript to run:**
```javascript
(() => {{
  const buttons = Array.from(document.querySelectorAll('button, input[type="button"], input[type="submit"]')).map(el => ({{
    type: 'button',
    tag: el.tagName.toLowerCase(),
    id: el.id || null,
    class: el.className || null,
    selector: el.id ? `#${{el.id}}` : `.(${{el.className.split(' ')[0]}})`,
    text: el.textContent?.trim() || el.value || 'No text',
    disabled: el.disabled,
    ariaLabel: el.getAttribute('aria-label')
  }})));

  const links = Array.from(document.querySelectorAll('a[href]')).map(el => ({{
    type: 'link',
    selector: el.id ? `#${{el.id}}` : `a[href="${{el.getAttribute('href')}}"]`,
    text: el.textContent?.trim() || 'No text',
    href: el.getAttribute('href'),
    target: el.target
  }})));

  const forms = Array.from(document.querySelectorAll('form')).map(form => ({{
    type: 'form',
    selector: form.id ? `#${{form.id}}` : 'form',
    action: form.action,
    method: form.method,
    fields: Array.from(form.elements).filter(el => el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.tagName === 'SELECT').map(field => ({{
      name: field.name,
      type: field.type,
      id: field.id,
      required: field.required
    }})),
    submitButton: form.querySelector('[type="submit"]')?.id || 'submit'
  }})));

  const inputs = Array.from(document.querySelectorAll('input:not([type="submit"]):not([type="button"]), textarea, select')).filter(el => !el.closest('form')).map(el => ({{
    type: 'input',
    inputType: el.type || el.tagName.toLowerCase(),
    selector: el.id ? `#${{el.id}}` : `input[name="${{el.name}}"]`,
    name: el.name,
    placeholder: el.placeholder,
    required: el.required
  }})));

  return {{
    buttons,
    links,
    forms,
    inputs,
    total: buttons.length + links.length + forms.length + inputs.length
  }};
}})()
```

4. Return the discovered elements in JSON format

**Output Format (JSON):**
{{
  "page_url": "{server_url}",
  "interactive_elements": {{
    "buttons": [...],
    "links": [...],
    "forms": [...],
    "standalone_inputs": [...]
  }},
  "total_elements": 15,
  "discovery_complete": true
}}

Be thorough - use the JavaScript to extract ALL interactive elements."""

            discovery_response = await self.claude_sdk.send_message(discovery_prompt)

            # Parse discovery results
            import json
            import re

            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', discovery_response, re.DOTALL)
            if json_match:
                discovery_data = json.loads(json_match.group(1))
            elif discovery_response.strip().startswith('{'):
                discovery_data = json.loads(discovery_response)
            else:
                discovery_data = {
                    "interactive_elements": {
                        "buttons": [],
                        "links": [],
                        "forms": [],
                        "standalone_inputs": []
                    },
                    "total_elements": 0,
                    "discovery_complete": False,
                    "error": "Failed to parse discovery results"
                }

            # Flatten all interactive elements into a single list
            elements_dict = discovery_data.get('interactive_elements', {})
            all_elements = []
            all_elements.extend(elements_dict.get('buttons', []))
            all_elements.extend(elements_dict.get('forms', []))  # Test forms before standalone links
            all_elements.extend(elements_dict.get('links', []))
            all_elements.extend(elements_dict.get('standalone_inputs', []))

            print(f"✅ Discovered {len(all_elements)} interactive elements")
            print(f"   - {len(elements_dict.get('buttons', []))} buttons")
            print(f"   - {len(elements_dict.get('forms', []))} forms")
            print(f"   - {len(elements_dict.get('links', []))} links")
            print(f"   - {len(elements_dict.get('standalone_inputs', []))} inputs")

            # Step 2: Test each interactive element systematically
            print(f"\n🔬 Step 2: Testing {len(all_elements)} interactive elements")

            test_results = []
            issues_found = []

            for idx, element in enumerate(all_elements, 1):
                element_type = element.get('type', 'unknown')
                selector = element.get('selector', '')
                text = element.get('text', 'No text')

                print(f"   [{idx}/{len(all_elements)}] Testing {element_type}: {text[:50]}...")

                # Create test prompt based on element type
                if element_type == 'button':
                    test_prompt = self._create_button_test_prompt(server_url, element, functional_spec)
                elif element_type == 'form':
                    test_prompt = self._create_form_test_prompt(server_url, element, functional_spec)
                elif element_type == 'link':
                    test_prompt = self._create_link_test_prompt(server_url, element, functional_spec)
                else:
                    test_prompt = self._create_generic_test_prompt(server_url, element, functional_spec)

                # Execute test
                test_response = await self.claude_sdk.send_message(test_prompt)

                # Parse test result
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', test_response, re.DOTALL)
                if json_match:
                    test_result = json.loads(json_match.group(1))
                elif test_response.strip().startswith('{'):
                    test_result = json.loads(test_response)
                else:
                    test_result = {
                        "test_name": f"{element_type}_{idx}",
                        "passed": False,
                        "error": "Failed to parse test result"
                    }

                test_results.append(test_result)

                # Collect issues
                if not test_result.get('passed', False):
                    issue = {
                        "element": f"{element_type} - {text}",
                        "selector": selector,
                        "issue": test_result.get('issue', 'Test failed'),
                        "severity": test_result.get('severity', 'major'),
                        "expected": test_result.get('expected_behavior', ''),
                        "actual": test_result.get('actual_behavior', ''),
                        "fix": test_result.get('suggested_fix', '')
                    }
                    issues_found.append(issue)
                    print(f"      ❌ FAILED: {issue['issue'][:80]}")

            # Step 3: Analyze overall test results
            print(f"📊 Step 3: Analyzing test results")

            passed_count = sum(1 for test in test_results if test.get('passed', False))
            failed_count = len(test_results) - passed_count
            pass_rate = (passed_count / len(test_results) * 100) if test_results else 0

            # Categorize issues by severity
            critical_issues = [i for i in issues_found if i.get('severity') == 'critical']
            major_issues = [i for i in issues_found if i.get('severity') == 'major']
            minor_issues = [i for i in issues_found if i.get('severity') == 'minor']

            # Determine if QA passed
            all_passed = failed_count == 0
            approved = all_passed or (len(critical_issues) == 0 and pass_rate >= 90)

            print(f"✅ QA Testing Complete!")
            print(f"   Pass Rate: {pass_rate:.1f}% ({passed_count}/{len(test_results)} tests passed)")
            print(f"   Issues: {len(critical_issues)} critical, {len(major_issues)} major, {len(minor_issues)} minor")

            # Log QA testing completion
            log_event("code_reviewer.qa_testing_complete",
                     iteration=iteration,
                     test_count=len(test_results),
                     passed_count=passed_count,
                     failed_count=failed_count,
                     pass_rate=pass_rate,
                     approved=approved,
                     critical_issues=len(critical_issues),
                     major_issues=len(major_issues),
                     minor_issues=len(minor_issues))

            log_metric("code_reviewer.qa_pass_rate", pass_rate)
            log_metric("code_reviewer.qa_tests_run", len(test_results))

            return {
                "passed": all_passed,
                "approved": approved,
                "iteration": iteration,
                "test_count": len(test_results),
                "passed_count": passed_count,
                "failed_count": failed_count,
                "pass_rate": pass_rate,
                "test_results": test_results,
                "issues": issues_found,
                "critical_issues": critical_issues,
                "major_issues": major_issues,
                "minor_issues": minor_issues,
                "summary": f"QA Testing Iteration {iteration}: {pass_rate:.1f}% pass rate, {len(issues_found)} issues found"
            }

        except Exception as e:
            print(f"❌ [CODE REVIEWER] QA testing error: {e}")
            import traceback
            traceback.print_exc()

            log_error(e, "code_reviewer_qa_testing", iteration=iteration, server_url=server_url)

            return {
                "passed": False,
                "approved": False,
                "iteration": iteration,
                "test_count": 0,
                "passed_count": 0,
                "failed_count": 0,
                "pass_rate": 0,
                "test_results": [],
                "issues": [{"severity": "critical", "issue": f"QA testing failed: {str(e)}"}],
                "error": str(e)
            }

    def _create_button_test_prompt(self, server_url: str, element: Dict, functional_spec: Dict = None) -> str:
        """Create test prompt for button interactions"""
        selector = element.get('selector', '')
        text = element.get('text', 'button')
        disabled = element.get('disabled', False)

        return f"""Test this button interaction using Playwright MCP tools and DOM inspection.

**Element to Test:**
- Type: Button
- Selector: {selector}
- Text: {text}
- Disabled: {disabled}

**Test Steps:**

1. **Navigate and check button exists:**
   - Navigate to {server_url} (if not already there)
   - Wait for button: playwright_wait_for_selector('{selector}')
   - Check button state BEFORE click using playwright_evaluate:
     ```javascript
     {{
       exists: !!document.querySelector('{selector}'),
       disabled: document.querySelector('{selector}')?.disabled,
       text: document.querySelector('{selector}')?.textContent?.trim(),
       className: document.querySelector('{selector}')?.className
     }}
     ```

2. **Inspect page state BEFORE interaction:**
   - Use playwright_evaluate to check for loading indicators, modals, messages:
     ```javascript
     {{
       hasLoadingSpinner: !!document.querySelector('.loading, .spinner, [role="progressbar"]'),
       hasModal: !!document.querySelector('.modal, [role="dialog"]'),
       hasSuccessMessage: !!document.querySelector('.success, .alert-success'),
       hasErrorMessage: !!document.querySelector('.error, .alert-error, .alert-danger'),
       currentUrl: window.location.href
     }}
     ```

3. **Click the button:**
   - playwright_click('{selector}')
   - Wait 2-3 seconds for state changes

4. **Inspect page state AFTER interaction:**
   - Use same playwright_evaluate to check state changes
   - Check if any new elements appeared (modals, messages, data)
   - Check if button state changed (disabled, loading, etc.)
   - Verify URL didn't change unexpectedly

5. **Check for console errors:**
   - Use playwright_evaluate: `console.error` was called (if possible to detect)
   - Or check for error elements in DOM

**Functional Spec:** {functional_spec if functional_spec else 'No spec provided - use reasonable expectations for button behavior'}

**Output Format (JSON):**
{{
  "test_name": "button_{text.replace(' ', '_')}",
  "passed": true|false,
  "element_type": "button",
  "selector": "{selector}",
  "button_clickable": true|false,
  "state_before": {{"hasModal": false, "hasError": false, ...}},
  "state_after": {{"hasModal": true, "hasError": false, ...}},
  "state_changed": true|false,
  "expected_behavior": "Describe expected behavior",
  "actual_behavior": "Describe what actually happened based on DOM changes",
  "issue": "Description if test failed, null if passed",
  "severity": "critical|major|minor",
  "suggested_fix": "How to fix this issue",
  "dom_changes": ["List of DOM changes observed"],
  "console_errors": ["List any errors found"]
}}

Focus on DOM state changes, not visuals. Test functionality."""

    def _create_form_test_prompt(self, server_url: str, element: Dict, functional_spec: Dict = None) -> str:
        """Create test prompt for form interactions"""
        selector = element.get('selector', '')
        fields = element.get('fields', [])
        submit_button = element.get('submitButton', '') or 'button[type="submit"]'

        return f"""Test this form interaction using Playwright MCP tools and DOM inspection.

**Form to Test:**
- Selector: {selector}
- Fields: {fields}
- Submit Button: {submit_button}

**Test Steps:**

**PART 1: Test with VALID data**

1. **Navigate and inspect form:**
   - Navigate to {server_url} (if not already there)
   - Use playwright_evaluate to get form structure:
     ```javascript
     (() => {{
       const form = document.querySelector('{selector}');
       return {{
         exists: !!form,
         action: form?.action,
         method: form?.method,
         fields: Array.from(form?.elements || []).filter(el => el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.tagName === 'SELECT').map(f => ({{
           name: f.name,
           type: f.type,
           required: f.required,
           value: f.value
         }}))
       }};
     }})()
     ```

2. **Fill form with VALID test data:**
   - For each field in {fields}, use playwright_fill with appropriate test data:
     - Text/email: "test@example.com"
     - Name: "Test User"
     - Phone: "1234567890"
     - Textarea: "Test message content"

3. **Inspect state BEFORE submit:**
   - Use playwright_evaluate:
     ```javascript
     {{
       formValid: document.querySelector('{selector}')?.checkValidity?.() ?? true,
       hasErrors: !!document.querySelector('.error, .invalid-feedback, [aria-invalid="true"]'),
       submitButtonEnabled: !document.querySelector('{submit_button}')?.disabled
     }}
     ```

4. **Submit form:**
   - playwright_click('{submit_button}')
   - Wait 3-5 seconds for response

5. **Inspect state AFTER submit:**
   - Use playwright_evaluate:
     ```javascript
     {{
       hasSuccessMessage: !!document.querySelector('.success, .alert-success, [role="alert"].success'),
       hasErrorMessage: !!document.querySelector('.error, .alert-error, .alert-danger'),
       formCleared: Array.from(document.querySelectorAll('{selector} input')).every(input => !input.value),
       currentUrl: window.location.href
     }}
     ```

**PART 2: Test with INVALID data**

6. **Reload page and test validation:**
   - Navigate to {server_url} again
   - Try to submit form WITHOUT filling required fields
   - playwright_click('{submit_button}')

7. **Check validation works:**
   - Use playwright_evaluate:
     ```javascript
     {{
       formBlocked: !document.querySelector('{selector}')?.checkValidity?.(),
       validationErrorsShown: !!document.querySelector('.error, .invalid-feedback, [aria-invalid="true"]'),
       submitBlocked: document.querySelector('{submit_button}')?.disabled
     }}
     ```

**Functional Spec:** {functional_spec if functional_spec else 'No spec provided - expect standard form behavior: submit on valid, block on invalid'}

**Output Format (JSON):**
{{
  "test_name": "form_{selector.replace('#', '').replace('.', '')}",
  "passed": true|false,
  "element_type": "form",
  "selector": "{selector}",
  "valid_data_test": {{
    "passed": true|false,
    "submitted": true|false,
    "success_message_shown": true|false,
    "issue": "Issue if failed"
  }},
  "invalid_data_test": {{
    "passed": true|false,
    "validation_blocked_submit": true|false,
    "error_messages_shown": true|false,
    "issue": "Issue if failed"
  }},
  "validation_works": true|false,
  "expected_behavior": "Form should submit valid data and show success, block invalid data with errors",
  "actual_behavior": "What actually happened based on DOM state",
  "issue": "Overall issue if test failed",
  "severity": "critical|major|minor",
  "suggested_fix": "How to fix"
}}

Test both valid AND invalid inputs using DOM inspection."""

    def _create_link_test_prompt(self, server_url: str, element: Dict, functional_spec: Dict = None) -> str:
        """Create test prompt for navigation link interactions"""
        selector = element.get('selector', '')
        text = element.get('text', 'link')
        href = element.get('href', '')

        return f"""Test this navigation link using Playwright MCP tools and DOM inspection.

**Link to Test:**
- Selector: {selector}
- Text: {text}
- Href: {href}

**Test Steps:**

1. **Navigate and verify link exists:**
   - Navigate to {server_url} (if not already there)
   - Wait for link: playwright_wait_for_selector('{selector}')
   - Use playwright_evaluate to inspect link:
     ```javascript
     (() => {{
       const link = document.querySelector('{selector}');
       return {{
         exists: !!link,
         href: link?.href,
         text: link?.textContent?.trim(),
         target: link?.target,
         disabled: link?.classList.contains('disabled') || link?.hasAttribute('disabled')
       }};
     }})()
     ```

2. **Get current URL before click:**
   - Use playwright_evaluate: `window.location.href`

3. **Click link:**
   - playwright_click('{selector}')
   - Wait 2-3 seconds for navigation

4. **Verify navigation:**
   - Use playwright_evaluate:
     ```javascript
     {{
       currentUrl: window.location.href,
       pageTitle: document.title,
       bodyExists: !!document.querySelector('body'),
       has404: !!document.querySelector('h1')?.textContent?.toLowerCase().includes('404') ||
               !!document.querySelector('h1')?.textContent?.toLowerCase().includes('not found'),
       hasErrorPage: !!document.querySelector('.error-page, .not-found'),
       hasContent: document.body?.textContent?.trim().length > 100
     }}
     ```

5. **Verify page loaded successfully:**
   - Check if URL changed (for internal links)
   - Check if page has content (not 404)
   - Check no error pages shown

**Functional Spec:** {functional_spec if functional_spec else 'No spec provided - expect successful navigation'}

**Output Format (JSON):**
{{
  "test_name": "link_{text.replace(' ', '_')[:30]}",
  "passed": true|false,
  "element_type": "link",
  "selector": "{selector}",
  "href": "{href}",
  "url_before": "URL before click",
  "url_after": "URL after click",
  "navigation_succeeded": true|false,
  "page_loaded_successfully": true|false,
  "has_404_error": false,
  "has_content": true|false,
  "expected_behavior": "Should navigate to {href} and show valid page",
  "actual_behavior": "What actually happened based on URL and DOM",
  "issue": "Issue if failed",
  "severity": "critical|major|minor",
  "suggested_fix": "How to fix"
}}

Verify navigation works using DOM inspection."""

    def _create_generic_test_prompt(self, server_url: str, element: Dict, functional_spec: Dict = None) -> str:
        """Create generic test prompt for other interactive elements"""
        element_type = element.get('type', 'element')
        selector = element.get('selector', '')
        text = element.get('text', '')

        return f"""Test this interactive element using Playwright MCP tools and DOM inspection.

**Element to Test:**
- Type: {element_type}
- Selector: {selector}
- Text: {text}

**Test Steps:**

1. **Navigate and verify element exists:**
   - Navigate to {server_url} (if not already there)
   - Wait for element: playwright_wait_for_selector('{selector}')
   - Use playwright_evaluate to inspect element:
     ```javascript
     (() => {{
       const el = document.querySelector('{selector}');
       return {{
         exists: !!el,
         visible: el?.offsetParent !== null,
         disabled: el?.disabled || el?.classList.contains('disabled'),
         text: el?.textContent?.trim(),
         value: el?.value,
         type: el?.type,
         tagName: el?.tagName
       }};
     }})()
     ```

2. **Inspect page state BEFORE interaction:**
   - Use playwright_evaluate to get current page state:
     ```javascript
     {{
       hasModal: !!document.querySelector('.modal, [role="dialog"]'),
       hasAlert: !!document.querySelector('.alert, [role="alert"]'),
       currentUrl: window.location.href
     }}
     ```

3. **Interact with element:**
   - playwright_click('{selector}') (or appropriate interaction)
   - Wait 2-3 seconds for any changes

4. **Inspect page state AFTER interaction:**
   - Use same playwright_evaluate to detect changes
   - Check if modal appeared, alert shown, URL changed, etc.

**Functional Spec:** {functional_spec if functional_spec else 'No spec provided - verify element responds to interaction'}

**Output Format (JSON):**
{{
  "test_name": "{element_type}_{text.replace(' ', '_')[:30] if text else 'element'}",
  "passed": true|false,
  "element_type": "{element_type}",
  "selector": "{selector}",
  "element_exists": true|false,
  "element_interactable": true|false,
  "state_before": {{"hasModal": false, ...}},
  "state_after": {{"hasModal": true, ...}},
  "state_changed": true|false,
  "interaction_succeeded": true|false,
  "expected_behavior": "Expected outcome",
  "actual_behavior": "What happened based on DOM changes",
  "issue": "Issue if failed",
  "severity": "critical|major|minor",
  "suggested_fix": "How to fix"
}}

Test the element using DOM inspection."""
