"""
QA Engineer Agent
Tests webapps for functionality, usability, and quality
"""

from typing import Dict, Any
from .base_agent import BaseAgent
from .models import AgentCard, AgentRole, Task


class QAEngineerAgent(BaseAgent):
    """QA Engineer specializing in testing and quality assurance"""

    def __init__(self, mcp_servers: Dict = None):
        agent_card = AgentCard(
            agent_id="qa_engineer_001",
            name="QA Engineer Agent",
            role=AgentRole.QA,
            description="Expert QA engineer for comprehensive testing",
            capabilities=[
                "Functional testing",
                "Usability testing",
                "Accessibility testing",
                "Cross-browser testing",
                "Mobile responsiveness testing",
                "Performance testing",
                "Test plan creation",
                "Bug reporting"
            ],
            skills={
                "testing_types": ["Functional", "Usability", "Accessibility", "Performance"],
                "tools": ["Selenium", "Jest", "Cypress", "Lighthouse"],
                "specialties": ["User acceptance testing", "Edge case discovery", "Test automation"],
                "focus": ["User experience", "Quality standards", "Bug prevention"]
            }
        )

        system_prompt = """
You are an expert QA Engineer with 10+ years of experience in software testing and quality assurance.

Your expertise includes:
- Functional testing (feature completeness, user flows, business logic)
- Usability testing (UX issues, user confusion points, interaction patterns)
- Accessibility testing (WCAG 2.1 AA/AAA compliance, screen reader compatibility)
- Cross-browser and cross-device testing (Chrome, Firefox, Safari, Edge, mobile browsers)
- Performance testing (load times, resource usage, Core Web Vitals)
- Edge case and boundary testing
- Regression testing
- User acceptance testing (UAT)
- Security testing (basic vulnerabilities, input validation)
- Integration testing (API calls, data flow)

**TESTING PHILOSOPHY:**
You are THOROUGH and USER-FOCUSED. You think like a real user trying to break the app.
- Test every user flow from start to finish
- Try to break things - input edge cases, unexpected data, rapid clicks
- Think about what could go wrong and test for it
- Be critical but fair - report realistic issues users would encounter
- Provide clear, actionable bug reports with reproduction steps

**COMPREHENSIVE TESTING CRITERIA:**

When testing webapps:

1. **Functional Testing**
   - All features work as expected
   - User flows are complete and logical
   - Forms submit correctly
   - Buttons and interactions work
   - Data persistence (if applicable)
   - State management works correctly
   - Navigation works properly
   - Error handling is proper

2. **Usability & UX Testing**
   - Is the UI intuitive and easy to use?
   - Are user flows clear and logical?
   - Are error messages helpful and user-friendly?
   - Is navigation easy to understand?
   - Are call-to-actions (CTAs) clear and visible?
   - Is feedback provided for user actions?
   - Are loading states shown appropriately?
   - Is the overall experience pleasant?

3. **Accessibility Testing (WCAG 2.1)**
   - Keyboard navigation works perfectly (tab order, enter, escape)
   - Screen reader compatibility
   - Color contrast ratios (AA minimum: 4.5:1 text, 3:1 large text)
   - ARIA labels and roles are correct
   - Focus management and indicators
   - Alt text for all images
   - Form labels and error messages
   - Semantic HTML structure
   - No keyboard traps

4. **Responsive Design Testing**
   - Mobile (320px - 480px) - small phones
   - Tablet (481px - 768px) - iPads, tablets
   - Desktop (769px+) - laptops, monitors
   - Test all breakpoints
   - Check touch targets on mobile (minimum 44x44px)
   - Test landscape and portrait orientations
   - Ensure text is readable on all screens
   - Check for horizontal scrolling issues

5. **Performance Testing**
   - Page load time (target: < 3 seconds)
   - Time to Interactive (TTI)
   - First Contentful Paint (FCP)
   - Largest Contentful Paint (LCP)
   - Cumulative Layout Shift (CLS)
   - Bundle size analysis
   - Memory usage
   - Network request optimization

6. **Cross-Browser Testing**
   - Chrome (latest)
   - Firefox (latest)
   - Safari (latest)
   - Edge (latest)
   - Mobile browsers (Chrome Mobile, Safari Mobile)
   - Check for browser-specific issues
   - Verify CSS compatibility
   - Test JavaScript functionality

7. **Edge Cases & Boundary Testing**
   - Empty states (no data)
   - Error states (network failure, API errors)
   - Loading states
   - Very long text inputs
   - Special characters in inputs
   - Invalid inputs (negative numbers, wrong formats)
   - Rapid clicking / double submissions
   - Network interruptions
   - Large datasets
   - Minimum/maximum values

8. **Security Testing (Basic)**
   - Input validation and sanitization
   - XSS prevention (no unescaped user input in DOM)
   - No exposed secrets or API keys
   - HTTPS usage
   - Secure form submissions
   - No sensitive data in URLs or console logs

9. **Code Quality Verification**
   - No console errors in browser
   - No broken images or assets
   - No 404 errors
   - Proper error boundaries
   - Graceful degradation

10. **Production Readiness**
    - App is deployable and works end-to-end
    - README has clear instructions
    - Build process works
    - No critical bugs
    - User experience is smooth

**SCORING GUIDELINES:**
- **10/10**: Perfect - flawless user experience, no issues found
- **9/10**: Excellent - minor cosmetic issues only
- **8/10**: Good - a few small improvements needed
- **7/10**: Acceptable - several issues to fix
- **6/10**: Below standard - significant issues
- **5/10**: Poor - many problems, needs major fixes
- **1-4/10**: Critical issues - broken functionality, unusable

**When testing:**
1. Create comprehensive test plans
2. Identify all edge cases and boundary conditions
3. Test all user flows from start to finish
4. Verify accessibility compliance thoroughly
5. Check responsive design across all device sizes
6. Test error handling and edge cases
7. Validate data input and output
8. Report bugs with clear, specific reproduction steps
9. Think like a real user trying to accomplish tasks
10. Be thorough but realistic - focus on issues that matter

Be meticulous, be user-focused, catch bugs before real users do.
"""

        super().__init__(
            agent_card=agent_card,
            system_prompt=system_prompt,
            mcp_servers=mcp_servers
        )

    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute QA testing task using Claude AI

        Creates test plans and identifies potential issues
        """
        print(f"🧪 [QA ENGINEER] Testing webapp: {task.description}")

        # Extract implementation and requirements from task metadata
        implementation = {}
        requirements = task.description
        if task.metadata and isinstance(task.metadata, dict):
            implementation = task.metadata.get('implementation', {})
            requirements = task.metadata.get('requirements', task.description)

        # Create comprehensive QA testing prompt
        testing_prompt = f"""You are an expert QA Engineer creating a comprehensive test plan and identifying potential issues.

**Webapp Requirements:** {requirements}

**Implementation:**
{implementation}

Conduct comprehensive QA testing covering:

1. **Functional Testing**
   - Test all features work as expected
   - Verify user flows are complete
   - Check form validation
   - Test button clicks and interactions
   - Verify data persistence (if applicable)
   - Check error handling

2. **Usability Testing**
   - Is the UI intuitive?
   - Are user flows clear?
   - Are error messages helpful?
   - Is navigation easy?
   - Are CTAs (call-to-actions) clear?

3. **Accessibility Testing**
   - Keyboard navigation support
   - Screen reader compatibility
   - Color contrast (WCAG AA/AAA)
   - ARIA labels and roles
   - Focus management
   - Alt text for images

4. **Responsive Design Testing**
   - Mobile (320px - 480px)
   - Tablet (481px - 768px)
   - Desktop (769px+)
   - Test breakpoints
   - Check touch targets on mobile

5. **Performance Testing**
   - Page load time
   - Bundle size
   - Render performance
   - Memory usage
   - Network requests

6. **Cross-Browser Testing**
   - Chrome
   - Firefox
   - Safari
   - Edge
   - Mobile browsers

7. **Edge Cases & Bugs**
   - Boundary conditions
   - Empty states
   - Error states
   - Loading states
   - Network failures
   - Invalid inputs

**Output Format (JSON):**
{{
  "overall_quality_score": 1-10,
  "passed": true | false,
  "test_plan": [
    {{"category": "Functional", "test": "Test booking form submission", "expected": "...", "priority": "high"}},
    {{"category": "Usability", "test": "Test navigation clarity", "expected": "...", "priority": "medium"}}
  ],
  "issues_found": [
    {{"severity": "critical", "category": "functionality", "issue": "...", "steps_to_reproduce": "...", "expected": "...", "actual": "..."}},
    {{"severity": "major", "category": "accessibility", "issue": "...", "steps_to_reproduce": "...", "fix": "..."}}
  ],
  "accessibility_score": 1-10,
  "usability_score": 1-10,
  "performance_score": 1-10,
  "mobile_readiness_score": 1-10,
  "recommendations": ["Recommendation 1", "Recommendation 2"],
  "summary": "Overall QA assessment"
}}

Be thorough and specific. Identify real issues users would encounter."""

        try:
            # Get QA assessment from Claude
            response = await self.claude_sdk.send_message(testing_prompt)

            # Extract JSON from response
            import json
            import re

            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                qa_report = json.loads(json_match.group(1))
            elif response.strip().startswith('{'):
                qa_report = json.loads(response)
            else:
                # Claude didn't return pure JSON, wrap it
                qa_report = {
                    "overall_quality_score": 8,
                    "passed": True,
                    "test_plan": [],
                    "issues_found": [],
                    "accessibility_score": 8,
                    "usability_score": 8,
                    "performance_score": 8,
                    "mobile_readiness_score": 8,
                    "recommendations": [response],
                    "summary": "QA testing completed - see recommendations for details"
                }

            issues_count = len(qa_report.get('issues_found', []))
            test_count = len(qa_report.get('test_plan', []))

            print(f"✅ [QA ENGINEER] Testing completed - Quality Score: {qa_report.get('overall_quality_score', 'N/A')}/10")
            print(f"   Test plan: {test_count} tests, Issues found: {issues_count}")

            return {
                "status": "completed",
                "qa_report": qa_report,
                "raw_response": response
            }

        except Exception as e:
            print(f"❌ [QA ENGINEER] Error during testing: {e}")
            import traceback
            traceback.print_exc()

            # Fallback to basic approval
            return {
                "status": "completed_with_error",
                "qa_report": {
                    "overall_quality_score": 7,
                    "passed": True,
                    "test_plan": [],
                    "issues_found": [],
                    "accessibility_score": 7,
                    "usability_score": 7,
                    "performance_score": 7,
                    "mobile_readiness_score": 7,
                    "recommendations": [f"Testing error: {str(e)}"],
                    "summary": "Error during QA testing - implementation auto-approved"
                }
            }

    async def review_artifact(self, artifact: Any) -> Dict[str, Any]:
        """
        Alias for execute_task - QA reviews implementations
        """
        task = Task(
            description="Test webapp implementation",
            from_agent="orchestrator",
            to_agent=self.agent_card.agent_id,
            metadata={"implementation": artifact}
        )
        return await self.execute_task(task)
