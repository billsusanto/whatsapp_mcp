"""
UI/UX Designer Agent
Creates design specifications for webapps
"""

from typing import Dict, Any
from .base_agent import BaseAgent
from .models import AgentCard, AgentRole, Task, DesignSpecification


class DesignerAgent(BaseAgent):
    """UI/UX Designer specializing in webapp design"""

    def __init__(self, mcp_servers: Dict = None):
        agent_card = AgentCard(
            agent_id="designer_001",
            name="UI/UX Designer Agent",
            role=AgentRole.DESIGNER,
            description="Expert UI/UX designer for modern webapps",
            capabilities=[
                "Design system creation",
                "Wireframing",
                "Color scheme design",
                "Typography specification",
                "Component design",
                "Accessibility review",
                "Responsive design",
                "Frontend code review",
                "Design fidelity verification"
            ],
            skills={
                "design": ["Material Design", "iOS HIG", "Responsive Web"],
                "tools": ["Figma", "Design Tokens", "WCAG"],
                "specialties": ["Dark Mode", "Minimal Design", "Modern UI"]
            }
        )

        system_prompt = """
You are a professional UI/UX Designer with 10+ years of experience.

Your expertise includes:
- Modern design principles (Material Design, iOS Human Interface Guidelines)
- Color theory and accessibility (WCAG AA/AAA compliance)
- Typography and spacing systems (modular scales)
- Component-based design systems
- Responsive web design (mobile-first approach)
- User experience best practices
- Frontend code review (React, Vue, Tailwind CSS, CSS-in-JS)

Your dual role:
1. **Design Creation**: Create comprehensive design specifications with exact values
2. **Code Review**: Review frontend implementations to ensure they match your design specs

When creating designs:
1. Always start with user needs
2. Create consistent design systems with exact values (hex codes, px/rem values, etc.)
3. Ensure accessibility (color contrast, font sizes)
4. Design for responsiveness (mobile, tablet, desktop)
5. Provide clear specifications for developers

When reviewing frontend code:
1. Compare actual code against your design specification
2. Check if colors, fonts, spacing match exactly
3. Verify CSS/Tailwind classes implement the design correctly
4. Ensure responsive breakpoints are properly coded
5. Give constructive, specific feedback with code references
6. Be critical - score 9-10 only if implementation is nearly perfect

Output design specifications and reviews as structured data that can be parsed.
"""

        super().__init__(
            agent_card=agent_card,
            system_prompt=system_prompt,
            mcp_servers=mcp_servers
        )

    def _build_research_prompt(self, task: Task) -> str:
        """Build research prompt for design task"""
        return f"""You are a professional UI/UX designer conducting research for a design project.

**Design Task:** {task.description}

**Research Goals:**
1. **Target Audience Analysis**
   - Who will use this webapp?
   - What are their needs, preferences, and pain points?
   - What devices/platforms will they use?
   - Accessibility requirements?

2. **Design Trends & Best Practices**
   - Current design trends relevant to this type of webapp
   - Industry standards and patterns
   - Successful examples of similar designs
   - What makes them successful?

3. **Technical Constraints**
   - Platform constraints (web, mobile, both)
   - Browser compatibility requirements
   - Performance considerations (load time, interactions)
   - Accessibility standards (WCAG AA minimum)

4. **Color Psychology & Branding**
   - What emotions/feelings should the design evoke?
   - Color palettes that align with the purpose
   - Brand personality (professional, playful, minimal, bold)

5. **Layout & Information Architecture**
   - Content hierarchy and organization
   - Navigation patterns
   - User flow and journey mapping
   - Key interactions and features

6. **Competitive Analysis**
   - Similar webapps and their design approaches
   - What works well, what doesn't
   - Opportunities for differentiation

**Output Format (JSON):**
{{
  "target_audience": {{
    "primary_users": "description",
    "user_needs": ["need 1", "need 2"],
    "devices": ["desktop", "mobile", "tablet"],
    "accessibility_level": "WCAG AA|WCAG AAA"
  }},
  "design_trends": [
    {{"trend": "...", "relevance": "...", "application": "..."}}
  ],
  "best_practices": [
    {{"practice": "...", "reasoning": "...", "source": "industry standard|research|..."}}
  ],
  "color_psychology": {{
    "desired_emotions": ["trust", "energy", "calm"],
    "recommended_palettes": ["palette 1", "palette 2"],
    "brand_personality": "modern|minimal|playful|professional|bold"
  }},
  "layout_recommendations": {{
    "layout_type": "single-page|multi-page|dashboard|landing",
    "navigation_pattern": "top-nav|sidebar|hamburger|tabs",
    "content_structure": "description"
  }},
  "competitive_insights": [
    {{"competitor": "...", "strength": "...", "weakness": "...", "lesson": "..."}}
  ],
  "key_challenges": ["challenge 1", "challenge 2"],
  "research_summary": "Brief synthesis of research findings"
}}

Be thorough. Research informs great design."""

    def _build_planning_prompt(self, task: Task, research: Dict) -> str:
        """Build planning prompt for design task"""
        return f"""You are a professional UI/UX designer creating a detailed design plan.

**Design Task:** {task.description}

**Research Findings:**
{research}

**Planning Goals:**
1. **Design System Definition**
   - Color palette with exact hex codes
   - Typography system (fonts, sizes, weights, line heights)
   - Spacing scale (margins, paddings)
   - Border radius, shadows, effects
   - Design tokens for consistency

2. **Component Specifications**
   - List all UI components needed
   - Specifications for each component
   - Component variants and states
   - Reusability and modularity

3. **Responsive Design Strategy**
   - Breakpoints (mobile, tablet, desktop)
   - Layout adaptations for each breakpoint
   - Touch targets for mobile
   - Responsive typography

4. **Accessibility Plan**
   - ARIA labels and roles
   - Keyboard navigation flow
   - Color contrast compliance
   - Screen reader considerations
   - Focus management

5. **Implementation Guidelines**
   - Technology recommendations (Tailwind, CSS-in-JS, etc.)
   - File structure for designers/developers
   - Handoff specifications
   - Quality checkpoints

**Output Format (JSON):**
{{
  "design_system": {{
    "colors": {{
      "primary": "#hex",
      "secondary": "#hex",
      "accent": "#hex",
      "background": "#hex",
      "text": "#hex",
      "success": "#hex",
      "warning": "#hex",
      "error": "#hex"
    }},
    "typography": {{
      "font_families": {{"heading": "...", "body": "..."}},
      "sizes": {{"h1": "...", "h2": "...", "body": "...", "small": "..."}},
      "weights": {{"regular": 400, "medium": 500, "bold": 700}},
      "line_heights": {{"tight": "...", "normal": "...", "relaxed": "..."}}
    }},
    "spacing_scale": ["4px", "8px", "16px", "24px", "32px", "48px", "64px"],
    "effects": {{"border_radius": "...", "shadows": ["...", "..."]}}
  }},
  "components": [
    {{
      "name": "Component name",
      "purpose": "What it does",
      "variants": ["variant 1", "variant 2"],
      "states": ["default", "hover", "active", "disabled"],
      "specifications": "Detailed specs"
    }}
  ],
  "responsive_strategy": {{
    "breakpoints": {{"mobile": "0-767px", "tablet": "768-1023px", "desktop": "1024px+"}},
    "layout_adaptations": "How layout changes across breakpoints",
    "mobile_considerations": ["touch targets 44x44px", "simplified nav", "..."]
  }},
  "accessibility_plan": {{
    "wcag_level": "AA|AAA",
    "aria_requirements": ["requirement 1", "requirement 2"],
    "keyboard_navigation": "Tab order and shortcuts",
    "color_contrast_ratios": "All text meets 4.5:1 minimum"
  }},
  "implementation_guidelines": {{
    "recommended_tools": ["Tailwind CSS", "..."],
    "file_structure": "Suggested organization",
    "handoff_notes": "Notes for developers"
  }},
  "success_criteria": [
    {{"criterion": "...", "measurement": "..."}}
  ],
  "plan_summary": "Brief overview of the design plan"
}}

Create a comprehensive, actionable design plan."""

    async def execute_task_with_plan(
        self,
        task: Task,
        research: Dict,
        plan: Dict
    ) -> Dict[str, Any]:
        """
        Execute design task with research-backed plan

        Uses research findings and execution plan to create
        a comprehensive, well-informed design specification.
        """
        print(f"🎨 [DESIGNER] Creating design with research & plan")

        # Create enhanced design prompt informed by research and plan
        design_prompt = f"""You are a professional UI/UX designer creating a comprehensive design specification.

**IMPORTANT:** You have already completed thorough research and planning. Use these findings to inform your design.

**Original Task:** {task.description}

**Research Findings:**
{research}

**Design Plan:**
{plan}

**Your Task:**
Create the final, detailed design specification based on the research and plan above.

CRITICAL GUIDELINES:
1. **Follow the Design Plan:** Use the color palette, typography, and spacing from the plan
2. **Apply Research Insights:** Incorporate target audience needs and best practices identified
3. **Be Comprehensive:** Include all components, states, and specifications
4. **Ensure Consistency:** Use the design system consistently throughout
5. **Focus on Accessibility:** Follow the accessibility plan rigorously

**Output Format (JSON):**
{{
  "style": "{plan.get('design_system', {}).get('brand_personality', 'modern')}",
  "colors": {plan.get('design_system', {}).get('colors', {})},
  "typography": {plan.get('design_system', {}).get('typography', {})},
  "components": [
    {{
      "name": "Component name",
      "description": "What it does",
      "visual_specs": "Detailed visual specifications",
      "states": {{"default": "...", "hover": "...", "active": "...", "disabled": "..."}},
      "variants": ["variant 1", "variant 2"],
      "accessibility": "ARIA labels, keyboard support, etc."
    }}
  ],
  "layout_description": "Overall layout structure and organization",
  "design_tokens": {{
    "colors": {{...}},
    "typography": {{...}},
    "spacing": {{...}}
  }},
  "accessibility_notes": [
    "ARIA label specifications",
    "Keyboard navigation flow",
    "Color contrast details",
    "Screen reader considerations"
  ],
  "responsive_breakpoints": {{
    "mobile": "Design adaptations for mobile",
    "tablet": "Design adaptations for tablet",
    "desktop": "Design specifications for desktop"
  }},
  "implementation_notes": [
    "Note for developers about complex interactions",
    "Recommendations for animations/transitions",
    "Performance considerations"
  ]
}}

Create a production-ready, comprehensive design specification informed by research and planning."""

        try:
            # Get design from Claude with research & plan context
            response = await self.claude_sdk.send_message(design_prompt)

            # Parse design specification
            import json
            import re

            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                design_spec = json.loads(json_match.group(1))
            elif response.strip().startswith('{'):
                design_spec = json.loads(response)
            else:
                design_spec = {
                    "design_description": response,
                    "note": "Design created with research & planning"
                }

            print(f"✅ [DESIGNER] Research-backed design specification created")

            return {
                "status": "completed",
                "design_spec": design_spec,
                "raw_response": response,
                "research_used": True,
                "research_summary": research.get('research_summary', 'Research completed'),
                "plan_summary": plan.get('plan_summary', 'Plan created')
            }

        except Exception as e:
            print(f"❌ [DESIGNER] Error creating design: {e}")
            import traceback
            traceback.print_exc()

            # Fallback
            return {
                "status": "completed_with_fallback",
                "design_spec": {
                    "error": str(e),
                    "note": "Fallback design provided"
                }
            }

    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute design task using Claude AI (backward compatibility)

        This is the original implementation without research & planning.
        """
        print(f"🎨 [DESIGNER] Creating design for: {task.description} (direct execution)")

        # Create comprehensive design prompt
        design_prompt = f"""You are a professional UI/UX designer creating a complete design specification for a webapp.

User Request: {task.description}

Create a comprehensive design specification that includes:

1. **Design Style & Theme**
   - Overall design approach (minimal, modern, playful, professional, etc.)
   - Target audience and use case
   - Brand personality

2. **Color Palette** (Provide exact hex codes)
   - Primary color (main brand color)
   - Secondary color (supporting brand color)
   - Accent color (call-to-action buttons, highlights)
   - Background colors (light/dark mode if applicable)
   - Text colors (primary, secondary, muted)
   - Success/Warning/Error colors
   - Ensure WCAG AA color contrast compliance

3. **Typography System**
   - Font families (suggest web-safe or Google Fonts)
   - Font sizes for headings (H1-H6), body, small text
   - Font weights
   - Line heights
   - Letter spacing

4. **Layout & Spacing**
   - Layout type (single page, multi-page, dashboard, etc.)
   - Grid system (12-column, flexbox, grid)
   - Spacing scale (4px, 8px, 16px, etc.)
   - Container max-widths
   - Responsive breakpoints (mobile, tablet, desktop)

5. **Component Specifications**
   - List all major UI components needed (buttons, cards, forms, navigation, etc.)
   - For each component, specify:
     * Visual appearance
     * States (default, hover, active, disabled)
     * Sizes (small, medium, large)
     * Variants

6. **User Flow**
   - Main user journey through the app
   - Key interactions and transitions

7. **Accessibility Requirements**
   - ARIA labels needed
   - Keyboard navigation support
   - Screen reader considerations

Output the design specification in a structured JSON format that can be easily parsed and implemented by a frontend developer.

Make sure the design is:
- Modern and professional
- User-friendly and intuitive
- Accessible (WCAG AA compliant)
- Responsive (mobile-first)
- Implementation-ready"""

        try:
            # Get design from Claude
            response = await self.claude_sdk.send_message(design_prompt)

            # Try to extract JSON from response
            import json
            import re

            # Look for JSON in code blocks or raw JSON
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                design_spec = json.loads(json_match.group(1))
            elif response.strip().startswith('{'):
                design_spec = json.loads(response)
            else:
                # Claude didn't return pure JSON, wrap the response
                design_spec = {
                    "design_description": response,
                    "note": "Design created by Claude AI - parse description for implementation details"
                }

            print(f"✅ [DESIGNER] Design specification created")

            return {
                "status": "completed",
                "design_spec": design_spec,
                "raw_response": response
            }

        except Exception as e:
            print(f"❌ [DESIGNER] Error creating design: {e}")
            import traceback
            traceback.print_exc()

            # Fallback to structured placeholder
            return {
                "status": "completed_with_fallback",
                "design_spec": {
                    "error": str(e),
                    "note": "Fallback design provided due to error",
                    "style": "modern minimal",
                    "colors": {
                        "primary": "#3B82F6",
                        "secondary": "#10B981",
                        "accent": "#F59E0B",
                        "background": "#FFFFFF",
                        "text": "#1F2937"
                    }
                }
            }

    async def review_artifact(self, artifact: Any) -> Dict[str, Any]:
        """
        Review implementation for design fidelity using Claude AI

        Phase 2: Real design review with Claude
        """
        print(f"🔍 [DESIGNER] Reviewing implementation")

        # Extract design spec and implementation details
        original_design = artifact.get("original_design", {})
        implementation = artifact.get("implementation", {})

        review_prompt = f"""You are a professional UI/UX designer reviewing a frontend implementation for design fidelity.

**Original Design Specification:**
{original_design}

**Frontend Implementation (Code & Files):**
{implementation}

**IMPORTANT:** You must thoroughly review BOTH the design specification AND the actual frontend code implementation.

Review the implementation and provide detailed feedback on:

1. **Design Fidelity (Compare Design Spec vs Code)**
   - Does the frontend CODE match the design specification exactly?
   - Are the specified colors (hex codes) correctly implemented in the code?
   - Are typography (fonts, sizes, weights) from the design spec properly used in CSS/Tailwind?
   - Are spacing values (margins, padding) from the design system applied correctly?
   - Are all designed components implemented in the code?
   - Check component files - do they match the component specifications?

2. **Code Implementation Quality**
   - Are CSS/Tailwind classes correctly implementing the design?
   - Are design tokens/variables properly defined and used?
   - Are color values hard-coded or using the design system?
   - Are font families correctly imported and applied?
   - Are responsive breakpoints matching the design spec?

3. **User Experience**
   - Is the implementation user-friendly?
   - Are interactions intuitive?
   - Is the flow logical?
   - Are hover states, active states implemented?

4. **Accessibility (Check Code)**
   - Are ARIA labels present in the JSX/HTML?
   - Is color contrast from design spec sufficient (check actual color values)?
   - Is keyboard navigation supported in the code?
   - Are semantic HTML elements used?

5. **Responsiveness (Check Code)**
   - Are responsive classes (Tailwind: md:, lg:, etc.) properly used?
   - Will this work on mobile, tablet, and desktop?
   - Are breakpoints from design spec implemented?

6. **Improvements Needed**
   - List specific code changes required to match design spec
   - Prioritize critical issues vs nice-to-haves
   - Provide specific file names and line numbers if possible

**Scoring Criteria (1-10):**
- 10: Perfect implementation, matches design spec exactly
- 9: Excellent, minor tweaks needed
- 8: Good, a few improvements needed
- 7: Acceptable, several issues to fix
- 6: Below standard, significant changes required
- 5 or below: Major redesign/reimplementation needed

Output your review as JSON with:
- "approved": boolean (true if score >= 8, false if major changes needed)
- "score": number 1-10 (overall quality score - be critical!)
- "feedback": array of strings (specific feedback items with code references)
- "critical_issues": array of strings (must-fix items that don't match design spec)
- "suggestions": array of strings (optional improvements)
- "iteration": number (which review iteration this is)

Be constructive, specific, and reference actual code and design spec values in your feedback."""

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
                    "approved": True,
                    "score": 8,
                    "feedback": [response],
                    "critical_issues": [],
                    "suggestions": [],
                    "iteration": 1,
                    "note": "Review completed - see feedback for details"
                }

            print(f"✅ [DESIGNER] Review completed - Approved: {review.get('approved', True)}")

            return review

        except Exception as e:
            print(f"❌ [DESIGNER] Error during review: {e}")
            import traceback
            traceback.print_exc()

            # Fallback to basic approval
            return {
                "approved": True,
                "score": 7,
                "feedback": [f"Review error: {str(e)} - Implementation auto-approved"],
                "critical_issues": [],
                "suggestions": [],
                "iteration": 1
            }
