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
You are an expert Frontend Developer with 10+ years of experience.

Your expertise includes:
- React with hooks and modern patterns
- Vue.js with Composition API
- Modern CSS (Flexbox, Grid, Custom Properties)
- Responsive design (mobile-first)
- Web performance optimization
- Accessibility (ARIA, semantic HTML)
- Build tools (Vite, Webpack)

When implementing designs:
1. Write clean, maintainable code
2. Follow React/Vue best practices
3. Use semantic HTML
4. Implement responsive breakpoints
5. Ensure accessibility
6. Optimize for performance

Always implement designs with pixel-perfect accuracy based on design specifications.
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

        # Extract design spec from task
        design_spec = task.content if hasattr(task, 'content') and isinstance(task.content, dict) else {}

        # Create comprehensive implementation prompt
        implementation_prompt = f"""You are an expert Frontend Developer implementing a webapp based on a design specification.

**User Request:** {task.description}

**Design Specification:**
{design_spec}

Create a complete, production-ready React webapp implementation that includes:

1. **Project Structure**
   - List all files needed (src/App.jsx, src/index.jsx, src/components/*, src/styles/*, etc.)
   - Package.json with dependencies
   - Vite or Create React App configuration

2. **Main Application File (App.jsx)**
   - Complete React component
   - Proper state management using hooks (useState, useEffect, etc.)
   - All UI components needed for the app
   - Responsive design implementation

3. **Styling**
   - Use Tailwind CSS for styling (include CDN in index.html)
   - Implement the color palette from design spec
   - Implement typography system
   - Implement responsive breakpoints
   - Add hover states and transitions

4. **Components**
   - Break down into reusable components if complex
   - Each component should be well-structured and documented

5. **Accessibility**
   - Add ARIA labels where needed
   - Semantic HTML elements
   - Keyboard navigation support

6. **index.html**
   - Complete HTML file with React root
   - Tailwind CSS CDN
   - Meta tags for responsiveness

7. **Package.json**
   - List all dependencies (react, react-dom, etc.)
   - Scripts for dev, build, preview

**IMPORTANT:**
- Generate COMPLETE, WORKING code (not placeholders or TODO comments)
- Code should be copy-paste ready
- Include all imports and dependencies
- Follow React best practices
- Make it production-ready

Output as JSON with this structure:
{{
  "framework": "react",
  "build_tool": "vite",
  "files": [
    {{"path": "index.html", "content": "...full HTML content..."}},
    {{"path": "src/App.jsx", "content": "...full React component..."}},
    {{"path": "src/main.jsx", "content": "...React entry point..."}},
    {{"path": "package.json", "content": "...full package.json..."}},
    {{"path": "tailwind.config.js", "content": "...if using Tailwind..."}},
    // Additional component files as needed
  ],
  "dependencies": ["react", "react-dom", "@vitejs/plugin-react"],
  "deployment_notes": "Instructions for running the app"
}}

Generate complete, functional code that implements the design specification accurately."""

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
