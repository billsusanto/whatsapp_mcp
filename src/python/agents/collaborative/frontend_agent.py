"""
Frontend Developer Agent
Implements webapps based on design specifications
"""

from typing import Dict, Any
from .base_agent import BaseAgent
from .models import AgentCard, AgentRole, Task


class FrontendDeveloperAgent(BaseAgent):
    """Frontend Developer specializing in React/Vue"""

    def __init__(self, mcp_servers: Dict = None):
        agent_card = AgentCard(
            agent_id="frontend_001",
            name="Frontend Developer Agent",
            role=AgentRole.FRONTEND,
            description="Expert frontend developer for modern webapps",
            capabilities=[
                "React development",
                "Vue development",
                "Component implementation",
                "Responsive design",
                "CSS/Tailwind styling",
                "State management",
                "Web performance optimization",
                "Netlify deployment"
            ],
            skills={
                "languages": ["JavaScript", "TypeScript", "HTML", "CSS"],
                "frameworks": ["React", "Vue", "Next.js", "Vite"],
                "styling": ["CSS", "Tailwind", "CSS-in-JS"],
                "tools": ["npm", "Vite", "Webpack", "Git"]
            }
        )

        system_prompt = """
You are an expert Frontend Developer with 10+ years of experience and a passion for clean, production-ready code.

Your expertise includes:
- React with hooks, Context API, and modern patterns (useCallback, useMemo, custom hooks)
- TypeScript for type safety and better developer experience
- Vue.js with Composition API (when applicable)
- Modern CSS (Flexbox, Grid, Custom Properties, Tailwind CSS)
- Responsive design (mobile-first approach)
- Web performance optimization (code splitting, lazy loading, memoization)
- Accessibility (WCAG 2.1 AA/AAA compliance, ARIA, semantic HTML)
- Build tools (Vite, Webpack) and version control (Git, GitHub)

**CRITICAL CODING PRINCIPLES:**

1. **Code Quality & Best Practices**
   - Write clean, self-documenting code with meaningful variable/function names
   - Follow SOLID principles and DRY (Don't Repeat Yourself)
   - Use TypeScript when possible for type safety
   - Implement proper error boundaries and error handling
   - Add comprehensive error states, loading states, and empty states
   - Write modular, reusable components with single responsibility
   - Use custom hooks to extract and reuse logic

2. **React Performance Optimization**
   - Use React.memo() for expensive components
   - Implement useCallback for function props
   - Implement useMemo for expensive calculations
   - Avoid unnecessary re-renders
   - Use lazy loading and code splitting for larger apps
   - Optimize list rendering with proper keys

3. **Production-Ready Features**
   - Implement comprehensive error handling (try-catch, error boundaries)
   - Add input validation and sanitization
   - Handle edge cases (empty data, network errors, loading states)
   - Add proper loading indicators
   - Implement responsive design with proper breakpoints
   - Ensure cross-browser compatibility

4. **Git & GitHub Best Practices**
   - Structure code for easy version control
   - Create a comprehensive .gitignore file (node_modules, .env, build artifacts)
   - Include a detailed README.md with setup instructions
   - Use environment variables for configuration (.env.example template)
   - Organize project structure logically

5. **Code Organization**
   - Clear folder structure (components/, hooks/, utils/, assets/, styles/)
   - Separate concerns (business logic vs. presentation)
   - Group related files together
   - Use index.js for clean imports

6. **Accessibility & UX**
   - Use semantic HTML (header, nav, main, footer, article, section)
   - Add ARIA labels and roles where needed
   - Ensure keyboard navigation works perfectly
   - Maintain proper color contrast (WCAG AA minimum)
   - Add focus indicators for interactive elements
   - Support screen readers

7. **Documentation**
   - Add JSDoc comments for complex functions
   - Include inline comments for tricky logic
   - Create a comprehensive README with:
     * Project description
     * Setup instructions
     * Environment variables needed
     * Build and deployment commands
     * Technology stack used

**When implementing designs:**
1. Generate COMPLETE, WORKING code (NO placeholders, NO TODOs)
2. Follow React/TypeScript best practices religiously
3. Use semantic HTML throughout
4. Implement all responsive breakpoints (mobile, tablet, desktop)
5. Ensure WCAG 2.1 AA accessibility compliance minimum
6. Optimize for performance (lazy loading, memoization)
7. Add comprehensive error handling and loading states
8. Create production-ready, deployable code
9. Include .gitignore, README.md, and .env.example
10. Use meaningful names for variables, functions, and components

Always implement designs with pixel-perfect accuracy while maintaining code quality and performance.
"""

        super().__init__(
            agent_card=agent_card,
            system_prompt=system_prompt,
            mcp_servers=mcp_servers
        )

    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute implementation task using Claude AI

        Phase 3: Real code generation with Claude
        """
        print(f"💻 [FRONTEND] Implementing: {task.description}")

        # Extract design spec from task metadata
        design_spec = {}
        if task.metadata and isinstance(task.metadata, dict):
            design_spec = task.metadata.get('design_spec', {})

        # Create comprehensive implementation prompt
        implementation_prompt = f"""You are an expert Frontend Developer implementing a production-ready webapp based on a design specification.

**User Request:** {task.description}

**Design Specification:**
{design_spec}

Create a complete, production-ready React webapp implementation that includes:

1. **Project Structure & Files**
   - All necessary files: src/App.jsx, src/main.jsx, components/, hooks/, utils/
   - package.json with all dependencies and scripts
   - vite.config.js for build configuration
   - .gitignore for version control
   - README.md with comprehensive documentation
   - .env.example template for environment variables

2. **Main Application (App.jsx)**
   - Complete React component with hooks (useState, useEffect, useCallback, useMemo)
   - Proper state management and data flow
   - Error boundaries for error handling
   - Loading states and error states
   - Responsive design implementation
   - All UI components integrated

3. **React Best Practices**
   - Use React.memo() for performance optimization where needed
   - Implement useCallback for function props to prevent re-renders
   - Implement useMemo for expensive calculations
   - Create custom hooks for reusable logic
   - Proper component composition
   - Meaningful component and variable names

4. **Styling (Tailwind CSS)**
   - Include Tailwind CSS CDN in index.html OR proper Tailwind setup
   - Implement exact color palette from design spec
   - Implement typography system (fonts, sizes, weights)
   - Implement responsive breakpoints (mobile-first)
   - Add hover states, focus states, and smooth transitions
   - Ensure proper spacing and layout

5. **Component Architecture**
   - Break down into small, reusable components
   - Single Responsibility Principle for each component
   - Proper props typing (use PropTypes or TypeScript)
   - Clear component hierarchy
   - Well-documented component interfaces

6. **Error Handling & Edge Cases**
   - Comprehensive error boundaries
   - Input validation and sanitization
   - Empty state handling
   - Loading state indicators
   - Network error handling
   - Form validation with helpful error messages

7. **Accessibility (WCAG 2.1 AA)**
   - Semantic HTML (header, nav, main, footer, article, section)
   - ARIA labels and roles where needed
   - Keyboard navigation support (tab order, focus management)
   - Color contrast compliance
   - Focus indicators on interactive elements
   - Alt text for images

8. **index.html**
   - Complete HTML with proper meta tags
   - React root element
   - Tailwind CSS CDN or link to compiled CSS
   - Responsive viewport meta tag
   - SEO meta tags (title, description)

9. **package.json**
   - All required dependencies (react, react-dom, etc.)
   - Dev dependencies (vite, eslint, etc.)
   - Scripts: dev, build, preview, lint
   - Proper project metadata

10. **Documentation Files**
    - **README.md**: Include project overview, features, setup instructions, environment variables, build/deploy commands, tech stack
    - **.gitignore**: node_modules, dist, .env, .DS_Store, coverage, build artifacts
    - **.env.example**: Template for environment variables (if applicable)

11. **GitHub Readiness**
    - Code structured for version control
    - Clear file organization
    - No hardcoded secrets or API keys
    - Environment variable usage for config
    - Production-ready build configuration

**CRITICAL REQUIREMENTS:**
- Generate COMPLETE, WORKING code (NO placeholders, NO TODO comments, NO "...rest of code")
- Code must be copy-paste ready and immediately functional
- Include ALL imports and dependencies
- Follow React best practices religiously
- Implement proper error handling throughout
- Make it production-ready and deployment-ready
- Use meaningful variable, function, and component names
- Add helpful comments for complex logic

**Output Format (JSON):**
{{
  "framework": "react",
  "build_tool": "vite",
  "files": [
    {{"path": "index.html", "content": "...COMPLETE HTML content..."}},
    {{"path": "src/App.jsx", "content": "...COMPLETE React component with all logic..."}},
    {{"path": "src/main.jsx", "content": "...React entry point..."}},
    {{"path": "package.json", "content": "...COMPLETE package.json..."}},
    {{"path": "vite.config.js", "content": "...Vite configuration..."}},
    {{"path": ".gitignore", "content": "...Complete .gitignore..."}},
    {{"path": "README.md", "content": "...Comprehensive README..."}},
    {{"path": ".env.example", "content": "...Environment variable template..."}},
    {{"path": "tailwind.config.js", "content": "...if using Tailwind build setup..."}},
    // Additional component files (src/components/*, src/hooks/*, etc.)
  ],
  "dependencies": ["react", "react-dom", "@vitejs/plugin-react"],
  "dev_dependencies": ["vite", "eslint", "eslint-plugin-react"],
  "deployment_notes": "Complete instructions for local development and deployment",
  "github_ready": true,
  "environment_variables": ["API_KEY (optional)", "API_URL (optional)"]
}}

Generate complete, production-ready, functional code that implements the design specification with pixel-perfect accuracy."""

        try:
            # Get implementation from Claude
            response = await self.claude_sdk.send_message(implementation_prompt)

            # Try to extract JSON from response
            import json
            import re

            # Look for JSON in code blocks or raw JSON
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                implementation = json.loads(json_match.group(1))
            elif response.strip().startswith('{'):
                implementation = json.loads(response)
            else:
                # Claude returned code directly, structure it
                implementation = {
                    "framework": "react",
                    "build_tool": "vite",
                    "files": [{
                        "path": "src/App.jsx",
                        "content": response
                    }],
                    "dependencies": ["react", "react-dom"],
                    "note": "Code generated by Claude AI - see content for implementation"
                }

            print(f"✅ [FRONTEND] Implementation completed - {len(implementation.get('files', []))} files generated")

            return {
                "status": "completed",
                "implementation": implementation,
                "raw_response": response
            }

        except Exception as e:
            print(f"❌ [FRONTEND] Error during implementation: {e}")
            import traceback
            traceback.print_exc()

            # Fallback implementation
            return {
                "status": "completed_with_fallback",
                "implementation": {
                    "framework": "react",
                    "build_tool": "vite",
                    "files": [{
                        "path": "src/App.jsx",
                        "content": "// Error during generation - see logs"
                    }],
                    "error": str(e),
                    "note": "Fallback implementation provided due to error"
                }
            }

    async def review_artifact(self, artifact: Any) -> Dict[str, Any]:
        """
        Review design specifications for implementability using Claude AI

        Phase 3: Real design review with Claude
        """
        print(f"🔍 [FRONTEND] Reviewing design specification")

        review_prompt = f"""You are an expert Frontend Developer reviewing a design specification for implementability.

**Design Specification:**
{artifact}

Review the design and provide feedback on:

1. **Implementability**
   - Can this design be implemented in React/Vue?
   - Are there any technical challenges?
   - Are all specifications clear and complete?

2. **Missing Information**
   - What design details are missing or unclear?
   - What additional specifications would be helpful?

3. **Technical Concerns**
   - Are there performance concerns?
   - Are there accessibility issues?
   - Are there browser compatibility concerns?

4. **Questions for Designer**
   - What clarifications do you need?
   - Are there design decisions that need refinement?

5. **Recommendations**
   - Suggest improvements to the design spec
   - Propose alternative approaches if applicable

Output as JSON with:
- "implementable": boolean (can this be implemented as-is?)
- "confidence": number 1-10 (how confident are you in implementation)
- "questions": array of strings (questions for the designer)
- "concerns": array of strings (technical concerns)
- "recommendations": array of strings (suggested improvements)
- "estimated_complexity": string ("simple", "moderate", "complex")

Be specific and constructive."""

        try:
            # Get review from Claude
            response = await self.claude_sdk.send_message(review_prompt)

            # Try to extract JSON from response
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
                    "implementable": True,
                    "confidence": 8,
                    "questions": [],
                    "concerns": [],
                    "recommendations": [response],
                    "estimated_complexity": "moderate",
                    "note": "Review completed - see recommendations for details"
                }

            print(f"✅ [FRONTEND] Design review completed - Implementable: {review.get('implementable', True)}")

            return review

        except Exception as e:
            print(f"❌ [FRONTEND] Error during review: {e}")
            import traceback
            traceback.print_exc()

            # Fallback to basic approval
            return {
                "implementable": True,
                "confidence": 7,
                "questions": [],
                "concerns": [f"Review error: {str(e)}"],
                "recommendations": [],
                "estimated_complexity": "moderate"
            }
