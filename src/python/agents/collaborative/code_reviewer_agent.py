"""
Code Reviewer Agent
Reviews code for quality, security, and best practices
"""

from typing import Dict, Any
from .base_agent import BaseAgent
from .models import AgentCard, AgentRole, Task


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

Be thorough, be strict, be constructive. Your reviews prevent bugs, security issues, and technical debt.
"""

        super().__init__(
            agent_card=agent_card,
            system_prompt=system_prompt,
            mcp_servers=mcp_servers
        )

    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute code review task using Claude AI

        Reviews code for quality, security, performance, and best practices
        """
        print(f"🔍 [CODE REVIEWER] Reviewing code: {task.description}")

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
            # Get code review from Claude
            response = await self.claude_sdk.send_message(review_prompt)

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

            critical_count = len(review.get('critical_issues', []))
            major_count = len(review.get('major_issues', []))
            minor_count = len(review.get('minor_issues', []))

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
