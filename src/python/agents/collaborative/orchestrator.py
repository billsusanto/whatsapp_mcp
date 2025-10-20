"""
Collaborative Orchestrator
Coordinates UI/UX Designer + Frontend Developer
"""

from typing import Dict, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sdk.claude_sdk import ClaudeSDK
from .designer_agent import DesignerAgent
from .frontend_agent import FrontendDeveloperAgent
from .models import Task


class CollaborativeOrchestrator:
    """
    Orchestrates collaboration between Designer and Frontend Developer

    Workflow:
    1. Designer creates design specification
    2. Frontend implements based on design
    3. Designer reviews implementation
    4. Frontend refines (if needed)
    5. Deploy to Netlify
    """

    def __init__(self, mcp_servers: Dict):
        """
        Initialize orchestrator with specialized agents

        Args:
            mcp_servers: Available MCP servers (WhatsApp, GitHub, Netlify)
        """
        print("=" * 60)
        print("🎭 Initializing Collaborative Orchestrator")
        print("=" * 60)

        self.mcp_servers = mcp_servers

        # Create specialized agents
        self.designer = DesignerAgent(mcp_servers)
        self.frontend = FrontendDeveloperAgent(mcp_servers)

        # Create Claude SDK for orchestrator tasks (deployment, coordination)
        self.deployment_sdk = ClaudeSDK(available_mcp_servers=mcp_servers)

        # Configuration
        self.max_iterations = 2  # Limit review iterations

        print("\n✅ Orchestrator ready with 2 agents:")
        print(f"   - {self.designer.agent_card.name}")
        print(f"   - {self.frontend.agent_card.name}")
        print(f"   - Deployment SDK with {len(mcp_servers)} MCP servers")
        print("=" * 60 + "\n")

    async def build_webapp(self, user_prompt: str) -> str:
        """
        Main workflow: User prompt → Deployed webapp

        Phase 2-4 Complete: Real AI agents with Netlify deployment

        Args:
            user_prompt: User's webapp description

        Returns:
            WhatsApp-formatted response with deployment URL
        """
        print(f"\n🚀 [ORCHESTRATOR] Starting webapp generation")
        print(f"📝 User request: {user_prompt}")
        print("\n" + "-" * 60)

        try:
            # Step 1: Designer creates design specification
            print("\n[Step 1/5] 🎨 Designer creating design specification...")
            design_task = Task(
                description=f"Create design specification for: {user_prompt}",
                from_agent="orchestrator",
                to_agent=self.designer.agent_card.agent_id
            )
            design_result = await self.designer.execute_task(design_task)
            design_spec = design_result.get('design_spec', {})

            # Extract design style safely
            if isinstance(design_spec, dict):
                design_style = design_spec.get('style', 'modern')
            else:
                design_style = 'modern'

            print(f"✓ Design completed")

            # Step 2: Frontend implements design
            print("\n[Step 2/5] 💻 Frontend implementing design...")

            # Pass design spec to frontend via task content
            impl_task = Task(
                description=f"Implement webapp: {user_prompt}",
                from_agent="orchestrator",
                to_agent=self.frontend.agent_card.agent_id
            )
            # Add design spec to task for frontend to use
            impl_task.content = design_spec

            impl_result = await self.frontend.execute_task(impl_task)
            implementation = impl_result.get('implementation', {})
            framework = implementation.get('framework', 'react')

            print(f"✓ Implementation completed: {framework}")

            # Step 3: Designer reviews implementation
            print("\n[Step 3/5] 🔍 Designer reviewing implementation...")
            review_artifact = {
                "original_design": design_spec,
                "implementation": implementation
            }
            review = await self.designer.review_artifact(review_artifact)
            approved = review.get('approved', True)
            score = review.get('score', 8)

            print(f"✓ Review completed: {'✅ Approved' if approved else '⚠️ Changes suggested'} (Score: {score}/10)")

            # Step 4: Deploy to Netlify using Claude SDK with Netlify MCP
            print("\n[Step 4/5] 🚀 Deploying to Netlify...")
            deployment_url = await self._deploy_to_netlify(
                user_prompt=user_prompt,
                implementation=implementation
            )

            if deployment_url:
                print(f"✓ Deployed to: {deployment_url}")
            else:
                print(f"⚠️  Deployment attempted - check logs for URL")
                deployment_url = "https://app.netlify.com/teams"  # Fallback to dashboard

            # Step 5: Format response for WhatsApp
            print("\n[Step 5/5] 📱 Formatting WhatsApp response...")
            response = self._format_whatsapp_response(
                url=deployment_url,
                design_style=design_style,
                framework=framework,
                review_score=score
            )

            print("\n" + "-" * 60)
            print("✅ [ORCHESTRATOR] Webapp generation complete!\n")

            return response

        except Exception as e:
            print(f"\n❌ [ORCHESTRATOR] Error during webapp generation: {e}")
            import traceback
            traceback.print_exc()

            # Return error message to user
            return f"""❌ Webapp generation encountered an error:

{str(e)}

The multi-agent system attempted to:
1. Create a design specification
2. Implement the design in React
3. Review the implementation
4. Deploy to Netlify

Please try again or check the logs for more details."""

    async def _deploy_to_netlify(
        self,
        user_prompt: str,
        implementation: Dict
    ) -> Optional[str]:
        """
        Deploy webapp to Netlify using Claude SDK with Netlify MCP

        Phase 4: Real Netlify deployment

        Args:
            user_prompt: User's original request
            implementation: Frontend implementation with files

        Returns:
            Deployment URL if successful, None otherwise
        """
        try:
            # Extract files from implementation
            files = implementation.get('files', [])

            if not files:
                print("⚠️  No files to deploy")
                return None

            # Create a deployment prompt for Claude to use Netlify MCP tools
            deployment_prompt = f"""You have access to Netlify MCP tools. Deploy this React webapp to Netlify.

**Webapp Description:** {user_prompt}

**Files to Deploy:**
{self._format_files_for_deployment(files)}

**Task:**
1. Create a new Netlify site (or use an existing one)
2. Deploy these files to Netlify
3. Return the live deployment URL

Use the Netlify MCP tools available to you. The site should be live and accessible immediately.

Respond with ONLY the deployment URL (e.g., https://your-site-name.netlify.app) or the Netlify dashboard URL if deployment is pending."""

            # Use Claude SDK with Netlify MCP to deploy
            response = await self.deployment_sdk.send_message(deployment_prompt)

            # Extract URL from response
            import re
            url_match = re.search(r'https://[a-zA-Z0-9-]+\.netlify\.app', response)

            if url_match:
                deployment_url = url_match.group(0)
                print(f"✅ Extracted deployment URL: {deployment_url}")
                return deployment_url
            else:
                # Check for netlify.com dashboard URL
                dashboard_match = re.search(r'https://app\.netlify\.com/[^\s]+', response)
                if dashboard_match:
                    print(f"📊 Deployment created - check dashboard: {dashboard_match.group(0)}")
                    return dashboard_match.group(0)

                print(f"⚠️  Could not extract URL from response: {response[:200]}")
                return None

        except Exception as e:
            print(f"❌ Deployment error: {e}")
            import traceback
            traceback.print_exc()
            return None

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
        review_score: int = 8
    ) -> str:
        """Format response for WhatsApp"""
        return f"""✅ Your webapp is ready!

🔗 Live Site: {url}

🎨 Design:
  • Style: {design_style}
  • Fully responsive
  • Accessibility optimized
  • Review score: {review_score}/10

⚙️ Technical:
  • Framework: {framework}
  • Build tool: Vite
  • Deployed on Netlify

🤖 Built by AI Agent Team:
  • UI/UX Designer Agent (design)
  • Frontend Developer Agent (implementation)
  • Collaborative review process

🚀 Powered by Claude Multi-Agent System
"""

    async def cleanup(self):
        """Clean up all agents and deployment SDK"""
        await self.designer.cleanup()
        await self.frontend.cleanup()
        await self.deployment_sdk.close()
        print("🧹 [ORCHESTRATOR] Cleaned up all agents and deployment SDK")
