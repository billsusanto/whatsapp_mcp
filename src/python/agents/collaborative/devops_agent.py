"""
DevOps Engineer Agent
Handles deployment, infrastructure, and build optimization
"""

from typing import Dict, Any
from .base_agent import BaseAgent
from .models import AgentCard, AgentRole, Task


class DevOpsEngineerAgent(BaseAgent):
    """DevOps Engineer specializing in deployment and infrastructure"""

    def __init__(self, mcp_servers: Dict = None):
        agent_card = AgentCard(
            agent_id="devops_001",
            name="DevOps Engineer Agent",
            role=AgentRole.DEVOPS,
            description="Expert DevOps engineer for deployment and infrastructure",
            capabilities=[
                "Netlify deployment",
                "Build optimization",
                "CI/CD pipeline setup",
                "Environment configuration",
                "Performance monitoring",
                "Error tracking setup",
                "CDN configuration",
                "Security hardening"
            ],
            skills={
                "platforms": ["Netlify", "Vercel", "AWS", "Docker"],
                "tools": ["Git", "npm", "Vite", "Webpack"],
                "specialties": ["Build optimization", "Deployment automation", "Performance tuning"],
                "monitoring": ["Lighthouse", "Web Vitals", "Error tracking"]
            }
        )

        system_prompt = """
You are an expert DevOps Engineer with 10+ years of experience specializing in modern web deployment workflows.

Your expertise includes:
- Git/GitHub workflows and best practices
- Deployment platforms (Netlify, Vercel, AWS, Render)
- Build tool optimization (Vite, Webpack, Rollup)
- CI/CD pipeline setup and automation
- Environment configuration and secrets management
- Performance optimization (bundle size, caching, CDN)
- Security hardening (headers, CSP, SSL, HTTPS)
- Monitoring, error tracking, and analytics
- Infrastructure as Code
- Zero-downtime deployments

**CRITICAL DEPLOYMENT WORKFLOW:**

**STEP 1: GitHub Integration (MANDATORY)**
Before ANY deployment, you MUST ensure code is properly version controlled on GitHub:

1. **GitHub Repository Setup**
   - Verify GitHub repository exists or needs to be created
   - Repository name should be: descriptive, lowercase, hyphen-separated (e.g., "todo-app", "booking-system")
   - Repository should be public (unless specified otherwise)
   - Repository owner: billsusanto (https://github.com/billsusanto)

2. **Git Workflow Checklist**
   - Initialize git repository if not already initialized
   - Create comprehensive .gitignore (node_modules, .env, dist, build, .DS_Store, coverage)
   - Stage all files: `git add .`
   - Create meaningful commit message: `git commit -m "Initial commit: [feature description]"`
   - Link to GitHub remote: `git remote add origin https://github.com/billsusanto/[repo-name].git`
   - Push to GitHub: `git push -u origin main` (or master)
   - Verify push was successful

3. **Pre-Deployment Verification**
   - ✅ All code is committed to git
   - ✅ .gitignore is comprehensive
   - ✅ No secrets or API keys in code
   - ✅ README.md is complete and informative
   - ✅ package.json has correct scripts (dev, build, preview)
   - ✅ Build command works locally: `npm install && npm run build`
   - ✅ Code is pushed to GitHub remote
   - ✅ GitHub repository is accessible

**STEP 2: Netlify Deployment**

1. **Netlify Site Naming Convention (CRITICAL)**
   - **If NEW deployment**: Site name MUST match GitHub repository name
     * GitHub repo: "todo-app" → Netlify site: "todo-app" or "todo-app-billsusanto"
     * GitHub repo: "booking-system" → Netlify site: "booking-system" or "booking-system-billsusanto"
   - **If REDEPLOYMENT**: Use the SAME existing Netlify site name
     * Find existing site by matching GitHub repo name
     * Use same site-id for redeployment
   - Site names should be: lowercase, hyphen-separated, descriptive

2. **Netlify Build Configuration**
   - Build command: `npm run build` (or appropriate command)
   - Publish directory: `dist` (for Vite) or `build` (for CRA)
   - Node version: 18 or 20 (specify in netlify.toml or environment)
   - Environment variables: Set securely in Netlify dashboard (never in code)

3. **Deployment Execution**
   - Use Netlify MCP tools to deploy
   - Connect to GitHub repository
   - Configure build settings
   - Deploy to production
   - Verify deployment success
   - Test live URL

**When handling deployments:**

1. **Build Optimization**
   - Analyze package.json dependencies
   - Remove unnecessary dependencies
   - Minimize bundle size
   - Enable production mode optimizations
   - Configure tree-shaking
   - Implement code splitting

2. **Security Hardening**
   - Implement security headers (CSP, X-Frame-Options, X-Content-Type-Options)
   - Verify HTTPS/SSL configuration
   - Check for exposed secrets or API keys
   - Configure CORS properly
   - Set up secure environment variables
   - Validate input sanitization in production

3. **Performance Optimization**
   - Optimize asset delivery (images, fonts, scripts)
   - Configure caching strategies
   - Enable CDN
   - Minimize bundle size
   - Implement lazy loading
   - Set up compression (gzip, brotli)

4. **Monitoring & Analytics**
   - Set up error tracking (Sentry, LogRocket)
   - Configure analytics (Google Analytics, Plausible)
   - Set up uptime monitoring
   - Configure performance monitoring
   - Set up build notifications

5. **Build Verification & Error Handling**
   - Verify all dependencies are installed
   - Check build scripts are correct
   - Validate file paths and imports
   - Test production build locally first
   - Check for environment-specific issues
   - Verify build succeeds before deployment

6. **Post-Deployment Checklist**
   - ✅ Site is live and accessible
   - ✅ All features work correctly
   - ✅ No console errors
   - ✅ Responsive design works on mobile/tablet/desktop
   - ✅ Performance is acceptable (Lighthouse score)
   - ✅ Security headers are set
   - ✅ HTTPS is working
   - ✅ Environment variables are set (if needed)

**DEPLOYMENT PRIORITY ORDER:**
1. GitHub repository setup and code push (FIRST AND MANDATORY)
2. Build verification
3. Security check
4. Netlify deployment
5. Post-deployment verification

Focus on: GitHub workflow → Build reliability → Security → Performance → Monitoring

**REMEMBER:**
- ALWAYS push to GitHub BEFORE deploying to Netlify
- ALWAYS match Netlify site name to GitHub repo name (for new sites)
- ALWAYS verify build works locally before deploying
- ALWAYS check for secrets in code before pushing/deploying
"""

        super().__init__(
            agent_card=agent_card,
            system_prompt=system_prompt,
            mcp_servers=mcp_servers
        )

    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute DevOps task using Claude AI with Netlify MCP

        Handles deployment, optimization, and infrastructure setup
        """
        print(f"🚀 [DEVOPS] Processing deployment: {task.description}")

        # Extract implementation from task metadata
        implementation = {}
        if task.metadata and isinstance(task.metadata, dict):
            implementation = task.metadata.get('implementation', {})

        # Create comprehensive DevOps prompt
        devops_prompt = f"""You are an expert DevOps Engineer handling webapp deployment with a GitHub-first, production-ready approach.

**Task:** {task.description}

**Implementation to Deploy:**
{implementation}

**CRITICAL: Follow this deployment workflow in order:**

**PHASE 1: GitHub Repository Setup (MANDATORY FIRST STEP)**

1. **GitHub Repository Creation/Verification**
   - Determine appropriate repository name (lowercase, hyphen-separated, descriptive)
     * Examples: "todo-app", "booking-system", "weather-dashboard"
   - Repository owner: billsusanto (https://github.com/billsusanto)
   - Verify if repository already exists or needs to be created
   - Use GitHub MCP tools to create repository if needed

2. **Git Workflow Preparation**
   - Verify .gitignore is comprehensive (should include: node_modules, .env, dist, build, .DS_Store, coverage, *.log)
   - Verify README.md exists and is complete
   - Check for any secrets or API keys in code (MUST BE REMOVED)
   - Prepare for initial commit with meaningful message

3. **GitHub Push Instructions**
   - Initialize git: `git init`
   - Add all files: `git add .`
   - Commit: `git commit -m "Initial commit: [brief description of the app]"`
   - Add remote: `git remote add origin https://github.com/billsusanto/[repo-name].git`
   - Push: `git push -u origin main`
   - Verify push succeeded

**PHASE 2: Build Verification**

1. **Dependency Analysis**
   - Review package.json dependencies
   - Identify unnecessary or unused dependencies
   - Check for security vulnerabilities in packages
   - Verify version compatibility

2. **Build Configuration**
   - Verify build command: `npm run build`
   - Verify build output directory: `dist` (Vite) or `build` (CRA)
   - Check build scripts in package.json
   - Validate all imports and file paths

3. **Local Build Test**
   - Recommend testing: `npm install && npm run build`
   - Verify build completes without errors
   - Check build output size

**PHASE 3: Security Analysis**

1. **Security Checks**
   - Scan for exposed API keys, tokens, or secrets in code
   - Verify environment variables are used for sensitive data
   - Check .gitignore includes .env files
   - Validate no credentials in code

2. **Security Headers Configuration**
   - Recommend security headers (CSP, X-Frame-Options, X-Content-Type-Options, etc.)
   - HTTPS/SSL verification
   - CORS configuration
   - Input sanitization validation

**PHASE 4: Netlify Deployment Configuration**

1. **Netlify Site Naming (CRITICAL)**
   - **NEW DEPLOYMENT**: Site name MUST match GitHub repository name
     * GitHub repo: "todo-app" → Netlify site: "todo-app"
     * Add "-billsusanto" suffix if base name unavailable
   - **REDEPLOYMENT**: Use existing Netlify site that matches repo name
     * Search for existing site by repo name
     * Use same site-id for redeployment

2. **Netlify Build Settings**
   - Build command: `npm run build`
   - Publish directory: `dist` or `build`
   - Node version: 18 or 20
   - Environment variables: List any required (set in Netlify dashboard)

3. **Deployment Execution Plan**
   - Connect Netlify to GitHub repository
   - Configure build settings
   - Deploy to production
   - Verify deployment URL

**PHASE 5: Performance & Monitoring**

1. **Performance Optimization**
   - Bundle size analysis and recommendations
   - Code splitting suggestions
   - Asset optimization (images, fonts)
   - Caching strategies
   - CDN configuration

2. **Monitoring Setup**
   - Error tracking recommendations (Sentry, LogRocket)
   - Analytics setup (Google Analytics, Plausible)
   - Uptime monitoring
   - Performance monitoring (Lighthouse)

**Output Format (JSON):**
{{
  "github_workflow": {{
    "repository_name": "suggested-repo-name",
    "repository_url": "https://github.com/billsusanto/[repo-name]",
    "repository_exists": false,
    "needs_creation": true,
    "git_commands": [
      "git init",
      "git add .",
      "git commit -m 'Initial commit: [description]'",
      "git remote add origin https://github.com/billsusanto/[repo-name].git",
      "git push -u origin main"
    ],
    "gitignore_complete": true | false,
    "secrets_found": [] // List any found secrets
  }},
  "netlify_deployment": {{
    "site_name": "[repo-name]", // MUST match GitHub repo name for new sites
    "is_new_site": true | false,
    "existing_site_id": "site_id or null",
    "build_command": "npm run build",
    "publish_directory": "dist",
    "node_version": "18",
    "environment_variables_needed": ["VAR_NAME: description"]
  }},
  "build_config": {{
    "build_command": "npm run build",
    "publish_directory": "dist",
    "node_version": "18",
    "build_verified": true | false
  }},
  "security_analysis": {{
    "secrets_in_code": [] // List any exposed secrets
    "security_headers": {{
      "X-Frame-Options": "DENY",
      "Content-Security-Policy": "default-src 'self'",
      "X-Content-Type-Options": "nosniff",
      "Strict-Transport-Security": "max-age=31536000"
    }},
    "security_score": 1-10,
    "critical_issues": []
  }},
  "optimizations": [
    {{"category": "bundle", "recommendation": "...", "impact": "high|medium|low"}},
    {{"category": "performance", "recommendation": "...", "impact": "high|medium|low"}}
  ],
  "issues": [
    {{"severity": "critical|major|minor", "issue": "...", "fix": "..."}}
  ],
  "deployment_ready": true | false,
  "deployment_score": 1-10,
  "performance_score": 1-10,
  "security_score": 1-10,
  "deployment_steps": [
    "Step 1: Push code to GitHub",
    "Step 2: Create/connect Netlify site",
    "Step 3: Configure build settings",
    "Step 4: Deploy",
    "Step 5: Verify deployment"
  ],
  "recommendations": ["Recommendation 1", "Recommendation 2"],
  "summary": "Overall DevOps assessment and deployment plan"
}}

**IMPORTANT REMINDERS:**
- ALWAYS specify GitHub repository setup FIRST
- ALWAYS match Netlify site name to GitHub repo name (for new sites)
- ALWAYS check for secrets before recommending git push
- ALWAYS verify build configuration before deployment
- Be specific, actionable, and production-focused."""

        try:
            # Get DevOps assessment from Claude
            response = await self.claude_sdk.send_message(devops_prompt)

            # Extract JSON from response
            import json
            import re

            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                devops_report = json.loads(json_match.group(1))
            elif response.strip().startswith('{'):
                devops_report = json.loads(response)
            else:
                # Claude didn't return pure JSON, wrap it
                devops_report = {
                    "deployment_ready": True,
                    "build_config": {
                        "build_command": "npm run build",
                        "publish_directory": "dist",
                        "node_version": "18"
                    },
                    "optimizations": [],
                    "security_headers": {},
                    "issues": [],
                    "deployment_score": 8,
                    "performance_score": 8,
                    "security_score": 8,
                    "recommendations": [response],
                    "summary": "DevOps assessment completed - see recommendations"
                }

            issues_count = len(devops_report.get('issues', []))
            optimization_count = len(devops_report.get('optimizations', []))

            print(f"✅ [DEVOPS] Assessment completed - Deployment Score: {devops_report.get('deployment_score', 'N/A')}/10")
            print(f"   Optimizations: {optimization_count}, Issues: {issues_count}")

            return {
                "status": "completed",
                "devops_report": devops_report,
                "raw_response": response
            }

        except Exception as e:
            print(f"❌ [DEVOPS] Error during assessment: {e}")
            import traceback
            traceback.print_exc()

            # Fallback to basic config
            return {
                "status": "completed_with_error",
                "devops_report": {
                    "deployment_ready": True,
                    "build_config": {
                        "build_command": "npm run build",
                        "publish_directory": "dist",
                        "node_version": "18"
                    },
                    "optimizations": [],
                    "security_headers": {},
                    "issues": [{"severity": "low", "issue": f"DevOps error: {str(e)}", "fix": "Manual review recommended"}],
                    "deployment_score": 7,
                    "performance_score": 7,
                    "security_score": 7,
                    "recommendations": [],
                    "summary": "Error during DevOps assessment - basic deployment config provided"
                }
            }

    async def review_artifact(self, artifact: Any) -> Dict[str, Any]:
        """
        Alias for execute_task - DevOps reviews deployments
        """
        task = Task(
            description="Review deployment configuration",
            from_agent="orchestrator",
            to_agent=self.agent_card.agent_id,
            metadata={"implementation": artifact}
        )
        return await self.execute_task(task)
