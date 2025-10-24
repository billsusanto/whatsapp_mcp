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
                "Logfire production error analysis",
                "Debugging with telemetry data",
                "Netlify deployment"
            ],
            skills={
                "languages": ["JavaScript", "TypeScript", "HTML", "CSS"],
                "frameworks": ["React", "Vue", "Next.js"],
                "styling": ["CSS", "Tailwind", "CSS-in-JS"],
                "tools": ["npm", "Next.js", "Webpack", "Git"]
            }
        )

        system_prompt = """
You are an expert Frontend Developer with 10+ years of experience and a passion for clean, production-ready code.

**🔥 CRITICAL: You have READ ACCESS to Logfire Production Telemetry**

You have access to query production telemetry data from Logfire to debug code issues:
- **Dashboard URL:** https://logfire.pydantic.dev/
- **Project:** whatsapp-mcp
- **Access:** Read-only (query traces, view errors, analyze performance)

**When debugging bugs or fixing build errors, ALWAYS:**
1. Query Logfire for recent error traces related to your code
2. Extract exact error messages, stack traces, component names from telemetry
3. Reference specific trace IDs in your bug fix analysis
4. Use production data (not assumptions) to understand failures

**How to query Logfire:**
- Find runtime errors: `agent_name = "Frontend Developer" AND result_status = "error"`
- Find slow operations: `agent_name = "Frontend Developer" AND duration > 15s`
- Find build failures: `build_error contains "Type" AND error_message contains specific component`
- See detailed guide in LOGFIRE_AGENT_QUERY_GUIDE.md

**Example Logfire-powered debugging:**
```
DevOps: "Build failed with TypeScript error in AlbumCard component"

You:
1. Query Logfire: span.name contains "execute_task" AND error_message contains "AlbumCard"
2. Found trace def456 showing your previous implementation attempt
3. Extract: Error was "Property 'title' does not exist on type Album"
4. Extract: You used album.title but data has album.name
5. Fix based on trace evidence

Response: "Based on Logfire trace def456, I previously used album.title
but the Album type from the API has 'name' not 'title'. I'll update
AlbumCard to use album.name and add proper type checking."
```

**Your debugging workflow:**
1. **Check Logfire when fixing bugs** - See what actually failed in production
2. **Analyze your previous attempts** - Query traces of your past implementations
3. **Learn from errors** - If build fails, see exact TypeScript errors from traces
4. **Optimize based on data** - Query slow operations to find performance issues

Your expertise includes:
- React with hooks, Context API, and modern patterns (useCallback, useMemo, custom hooks)
- TypeScript for type safety and better developer experience
- Vue.js with Composition API (when applicable)
- Modern CSS (Flexbox, Grid, Custom Properties, Tailwind CSS)
- Responsive design (mobile-first approach)
- Web performance optimization (code splitting, lazy loading, memoization)
- Accessibility (WCAG 2.1 AA/AAA compliance, ARIA, semantic HTML)
- Build tools (Next.js, Webpack) and version control (Git, GitHub)

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

    def _build_research_prompt(self, task: Task) -> str:
        """Build research prompt for frontend implementation"""
        return f"""You are an expert Frontend Developer conducting research before implementing a webapp.

**Implementation Task:** {task.description}

**Research Goals:**
1. **Framework & Technology Selection**
   - Best framework for this webapp (Next.js, React, Vue, vanilla JS)
   - Should we use TypeScript? (usually yes for production apps)
   - State management needed? (useState, Context API, Redux, Zustand)
   - Styling approach (Tailwind CSS recommended, CSS Modules, styled-components)
   - Any third-party libraries needed? (date pickers, charts, animations)

2. **Architecture & Patterns**
   - Component architecture (atomic design, feature-based, etc.)
   - State management strategy (local state vs global state)
   - Data flow patterns
   - Routing strategy (if multi-page)
   - API integration patterns (if backend needed)

3. **Dependencies & Package Analysis**
   - Core dependencies needed (react, next, tailwind, etc.)
   - Dev dependencies (typescript, eslint, prettier)
   - Build tools and configuration
   - Package versions to use (latest stable recommended)
   - Potential dependency conflicts to avoid

4. **Implementation Challenges**
   - Complex features that need special attention
   - Potential technical difficulties
   - Performance considerations
   - Browser compatibility requirements
   - Mobile responsiveness challenges

5. **Best Practices & Patterns**
   - React hooks best practices for this type of app
   - Component composition strategies
   - Performance optimization opportunities
   - Error handling patterns
   - Accessibility implementation strategies

6. **Project Structure**
   - Recommended folder organization
   - File naming conventions
   - Component organization strategy
   - Where to put hooks, utils, types

**Output Format (JSON):**
{{
  "framework_recommendation": {{
    "framework": "next.js|react|vue",
    "reasoning": "Why this framework is best for this webapp",
    "version": "Latest stable version",
    "typescript": true|false,
    "typescript_reasoning": "Why TypeScript should/shouldn't be used"
  }},
  "technology_stack": {{
    "core_framework": "Next.js 14|React 18|Vue 3",
    "styling": "Tailwind CSS|CSS Modules|styled-components",
    "state_management": "useState + Context|Redux|Zustand|none",
    "routing": "Next.js App Router|React Router|none",
    "build_tool": "Next.js|Vite|Webpack"
  }},
  "dependencies": {{
    "production": {{
      "package-name": "version",
      "react": "^18.2.0",
      "next": "^14.0.0"
    }},
    "dev": {{
      "typescript": "^5.0.0",
      "@types/react": "^18.2.0"
    }}
  }},
  "architecture": {{
    "component_pattern": "Atomic Design|Feature-based|Page-based",
    "state_strategy": "Description of state management approach",
    "folder_structure": {{
      "src/": ["components/", "hooks/", "utils/", "types/", "styles/"]
    }}
  }},
  "implementation_challenges": [
    {{"challenge": "...", "solution_approach": "...", "complexity": "low|medium|high"}}
  ],
  "best_practices": [
    {{"practice": "...", "reasoning": "...", "priority": "critical|high|medium"}}
  ],
  "performance_considerations": [
    "Lazy loading for routes",
    "Image optimization with Next.js Image",
    "Code splitting strategies"
  ],
  "estimated_complexity": "simple|moderate|complex|very complex",
  "research_summary": "Brief summary of research findings"
}}

Be thorough. Research prevents implementation issues."""

    def _build_planning_prompt(self, task: Task, research: Dict) -> str:
        """Build planning prompt for frontend implementation"""
        return f"""You are an expert Frontend Developer creating a detailed implementation plan.

**Implementation Task:** {task.description}

**Research Findings:**
{research}

**Planning Goals:**
1. **Component Breakdown**
   - List ALL components needed (from largest container to smallest atom)
   - Define component hierarchy and relationships
   - Specify props for each component
   - Identify reusable components

2. **State Management Plan**
   - What state is needed (local vs global)
   - Where state should live (which components)
   - How state flows through the app
   - When to use Context API vs props

3. **File Structure & Organization**
   - Exact file and folder structure
   - Where each component goes
   - How files are named
   - How imports are organized

4. **Implementation Steps**
   - Ordered steps to build the webapp
   - Dependencies between steps
   - What to build first, second, third
   - Integration points

5. **Data Flow & Logic**
   - How data flows through components
   - Event handling strategy
   - Form validation approach
   - Error handling strategy

6. **Styling Strategy**
   - How to apply design system
   - Tailwind classes vs custom CSS
   - Responsive breakpoints implementation
   - Component-specific styling notes

7. **Quality Checkpoints**
   - What to verify at each step
   - Testing checkpoints
   - Accessibility checks
   - Performance validations

**Output Format (JSON):**
{{
  "component_hierarchy": [
    {{
      "name": "App",
      "type": "container",
      "children": ["Header", "MainContent", "Footer"],
      "state": ["currentTab", "isLoading"],
      "props": [],
      "file_path": "src/components/App.tsx"
    }},
    {{
      "name": "Header",
      "type": "presentational",
      "children": ["Logo", "Navigation"],
      "state": [],
      "props": ["onNavigate"],
      "file_path": "src/components/Header.tsx"
    }}
  ],
  "state_management_plan": {{
    "global_state": [
      {{"name": "user", "type": "User | null", "managed_by": "UserContext"}}
    ],
    "local_state": [
      {{"component": "TodoList", "state": ["todos", "filter"], "type": "array, string"}}
    ],
    "context_providers": ["UserContext", "ThemeContext"]
  }},
  "file_structure": {{
    "src/": {{
      "components/": ["App.tsx", "Header.tsx", "TodoList.tsx"],
      "hooks/": ["useTodos.ts", "useAuth.ts"],
      "utils/": ["helpers.ts", "validation.ts"],
      "types/": ["index.ts"],
      "styles/": ["globals.css"]
    }},
    "public/": ["favicon.ico", "images/"],
    "root": [".gitignore", "README.md", "package.json", "tsconfig.json", "tailwind.config.js", "next.config.js"]
  }},
  "implementation_steps": [
    {{
      "step": 1,
      "action": "Set up Next.js project with TypeScript and Tailwind",
      "commands": ["npx create-next-app@latest --typescript --tailwind"],
      "expected_output": "Clean Next.js project structure",
      "validation": "npm run dev works"
    }},
    {{
      "step": 2,
      "action": "Create base layout and navigation",
      "files_to_create": ["src/components/Header.tsx", "src/components/Footer.tsx"],
      "expected_output": "App shell with navigation",
      "validation": "Layout renders correctly"
    }}
  ],
  "styling_strategy": {{
    "approach": "Tailwind CSS with custom design tokens",
    "design_tokens": {{
      "colors": "Define in tailwind.config.js",
      "fonts": "Import from Google Fonts",
      "spacing": "Use Tailwind's default scale"
    }},
    "responsive_breakpoints": {{
      "mobile": "default (< 768px)",
      "tablet": "md: (768px - 1024px)",
      "desktop": "lg: (1024px+)"
    }}
  }},
  "error_handling_strategy": {{
    "approach": "Error boundaries + try-catch + user-friendly messages",
    "error_boundary": "Wrap app in ErrorBoundary component",
    "api_errors": "Try-catch with user feedback",
    "validation_errors": "Inline form validation messages"
  }},
  "accessibility_plan": {{
    "semantic_html": "Use proper HTML5 elements",
    "aria_labels": "Add to interactive elements without text",
    "keyboard_nav": "Ensure tab order is logical",
    "focus_indicators": "Visible focus states on all interactive elements"
  }},
  "performance_optimizations": [
    "Use React.memo() for TodoItem component",
    "Lazy load heavy components",
    "Optimize images with Next.js Image component"
  ],
  "quality_checkpoints": [
    {{"phase": "Setup", "check": "TypeScript compiles without errors"}},
    {{"phase": "Implementation", "check": "All components render correctly"}},
    {{"phase": "Integration", "check": "State flows correctly between components"}},
    {{"phase": "Final", "check": "Accessibility audit passes, responsive on all devices"}}
  ],
  "plan_summary": "Brief overview of the implementation plan"
}}

Create a clear, step-by-step implementation plan."""

    async def execute_task_with_plan(
        self,
        task: Task,
        research: Dict,
        plan: Dict
    ) -> Dict[str, Any]:
        """
        Execute frontend implementation with research-backed plan

        Uses research findings and execution plan to create
        production-ready code following best practices.
        """
        print(f"💻 [FRONTEND] Implementing with research & plan")

        # Extract design spec from task metadata
        design_spec = {}
        if task.metadata and isinstance(task.metadata, dict):
            design_spec = task.metadata.get('design_spec', {})

        # Get framework and tech stack from research
        framework = research.get('framework_recommendation', {}).get('framework', 'react')
        tech_stack = research.get('technology_stack', {})

        # Create enhanced implementation prompt informed by research and plan
        implementation_prompt = f"""You are an expert Frontend Developer implementing a production-ready webapp.

**IMPORTANT:** You have completed thorough research and planning. Use these findings to guide your implementation.

**Original Task:** {task.description}

**Design Specification:**
{design_spec}

**Research Findings:**
{research}

**Implementation Plan:**
{plan}

**Your Task:**
Implement the complete, production-ready webapp following the research and plan.

**CRITICAL IMPLEMENTATION GUIDELINES:**

1. **Follow the Plan Precisely:**
   - Use the recommended framework: {framework}
   - Use the technology stack: {tech_stack}
   - Follow the component hierarchy from the plan
   - Implement the state management strategy from the plan
   - Use the file structure from the plan

2. **Code Quality (Based on Research Best Practices):**
   - Write COMPLETE, WORKING code (NO placeholders, NO TODOs)
   - Follow the best practices identified in research
   - Address the implementation challenges identified
   - Apply performance optimizations from the plan

3. **File Structure:**
   Create ALL files according to the plan's file structure:
   {plan.get('file_structure', {})}

4. **Dependencies:**
   Use the dependencies identified in research:
   - Production: {research.get('dependencies', {}).get('production', {})}
   - Dev: {research.get('dependencies', {}).get('dev', {})}

5. **Output Format:**
   Return a comprehensive JSON with ALL files needed:

{{
  "framework": "{framework}",
  "dependencies": {{
    "production": {research.get('dependencies', {}).get('production', {})},
    "dev": {research.get('dependencies', {}).get('dev', {})}
  }},
  "files": [
    {{
      "path": "package.json",
      "content": "Full package.json content with all dependencies"
    }},
    {{
      "path": "src/components/App.tsx",
      "content": "Complete component code"
    }},
    {{
      "path": "src/components/[ComponentName].tsx",
      "content": "Complete component code for each component"
    }},
    {{
      "path": "tailwind.config.js",
      "content": "Tailwind configuration with design tokens"
    }},
    {{
      "path": ".gitignore",
      "content": "Comprehensive .gitignore file"
    }},
    {{
      "path": "README.md",
      "content": "Comprehensive README with setup instructions"
    }},
    {{
      "path": ".env.example",
      "content": "Environment variables template if needed"
    }}
  ],
  "setup_instructions": [
    "npm install",
    "npm run dev"
  ],
  "deployment_notes": "Notes for deployment",
  "implementation_summary": "What was implemented and how it follows the plan"
}}

**REMEMBER:**
- Follow the implementation plan step-by-step
- Use research findings to inform decisions
- Create production-ready, deployable code
- Include ALL necessary files
- Follow best practices identified in research
- Address challenges identified in research planning

Implement now, following the plan precisely."""

        try:
            # Get implementation from Claude with research & plan context
            response = await self.claude_sdk.send_message(implementation_prompt)

            # Parse implementation
            import json
            import re

            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                implementation = json.loads(json_match.group(1))
            elif response.strip().startswith('{'):
                implementation = json.loads(response)
            else:
                implementation = {
                    "implementation_description": response,
                    "note": "Implementation created with research & planning"
                }

            files_count = len(implementation.get('files', []))
            print(f"✅ [FRONTEND] Research-backed implementation completed ({files_count} files)")

            return {
                "status": "completed",
                "implementation": implementation,
                "raw_response": response,
                "research_used": True,
                "research_summary": research.get('research_summary', 'Research completed'),
                "plan_summary": plan.get('plan_summary', 'Plan created')
            }

        except Exception as e:
            print(f"❌ [FRONTEND] Error during implementation: {e}")
            import traceback
            traceback.print_exc()

            # Fallback
            return {
                "status": "completed_with_fallback",
                "implementation": {
                    "error": str(e),
                    "note": "Fallback implementation"
                }
            }

    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute implementation task using Claude AI (backward compatibility)

        This is the original implementation without research & planning.
        Used when enable_research_planning=False
        """
        print(f"💻 [FRONTEND] Implementing: {task.description} (direct execution)")

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
   - All necessary files: pages/, components/, hooks/, utils/, public/
   - package.json with all dependencies and scripts
   - next.config.js for build configuration
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
   - All required dependencies (react, react-dom, next, etc.)
   - Dev dependencies (eslint, etc.)
   - Scripts: dev, build, start, lint
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
  "build_tool": "nextjs",
  "files": [
    {{"path": "pages/_app.js", "content": "...COMPLETE Next.js App component..."}},
    {{"path": "pages/index.js", "content": "...COMPLETE React component with all logic..."}},
    {{"path": "components/...", "content": "...Component files..."}},
    {{"path": "package.json", "content": "...COMPLETE package.json..."}},
    {{"path": "next.config.js", "content": "...Next.js configuration..."}},
    {{"path": ".gitignore", "content": "...Complete .gitignore..."}},
    {{"path": "README.md", "content": "...Comprehensive README..."}},
    {{"path": ".env.example", "content": "...Environment variable template..."}},
    {{"path": "tailwind.config.js", "content": "...if using Tailwind build setup..."}},
    // Additional component files (components/*, hooks/*, etc.)
  ],
  "dependencies": ["react", "react-dom", "next"],
  "dev_dependencies": ["eslint", "eslint-plugin-react"],
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
                    "build_tool": "nextjs",
                    "files": [{
                        "path": "pages/index.js",
                        "content": response
                    }],
                    "dependencies": ["react", "react-dom", "next"],
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
                    "build_tool": "nextjs",
                    "files": [{
                        "path": "pages/index.js",
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
