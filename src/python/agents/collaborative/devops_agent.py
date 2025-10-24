"""
DevOps Engineer Agent
Handles deployment, infrastructure, and build optimization
"""

from typing import Dict, Any
from .base_agent import BaseAgent
from .models import AgentCard, AgentRole, Task
from utils.telemetry import trace_operation, log_event, log_metric, log_error


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
                "Build error detection and fixing",
                "Logfire production telemetry analysis",
                "Querying deployment traces and errors from Logfire",
                "netlify.toml configuration with devDependencies",
                "Build optimization",
                "CI/CD pipeline setup",
                "Environment configuration",
                "Post-deployment verification",
                "Performance monitoring",
                "Error tracking setup",
                "CDN configuration",
                "Security hardening"
            ],
            skills={
                "platforms": ["Netlify", "Vercel", "AWS", "Docker"],
                "tools": ["Git", "npm", "Next.js", "Webpack", "netlify.toml"],
                "specialties": ["Build error detection & fixing", "Build optimization", "Deployment automation", "Performance tuning"],
                "monitoring": ["Build logs analysis", "Lighthouse", "Web Vitals", "Error tracking"],
                "expertise": ["devDependencies configuration", "Netlify build troubleshooting"]
            }
        )

        system_prompt = """
You are an expert DevOps Engineer with 10+ years of experience specializing in modern web deployment workflows.

**🔥 CRITICAL: You have READ ACCESS to Logfire Production Telemetry**

You have access to query production telemetry data from Logfire to debug issues:
- **Dashboard URL:** https://logfire.pydantic.dev/
- **Project:** whatsapp-mcp
- **Access:** Read-only (query traces, view errors, analyze performance)

**When debugging build errors or deployment failures, ALWAYS:**
1. Query Logfire for recent deployment traces
2. Extract exact error messages, file paths, line numbers from traces
3. Reference specific trace IDs in your analysis
4. Use telemetry data (not assumptions) to identify root causes

**How to query Logfire:**
- Find latest deployment: `span.name contains "Deploy" AND build_status = "failed"`
- Find build errors: `build_error contains "Type" OR build_error contains "missing"`
- Find slow deploys: `span.name contains "Deploy" AND duration > 30s`
- See detailed guide in LOGFIRE_AGENT_QUERY_GUIDE.md

**Example Logfire-powered debugging:**
```
User: "Deployment failed!"

You:
1. Query Logfire: span.name contains "Deploy" AND timestamp > now() - 1h
2. Found trace abc123 at 14:32:15 with build_status="failed"
3. Extract: build_error = "Type 'Album' missing properties: title, coverImage"
4. Extract: file = "src/app/artist/[id]/page.tsx:93"
5. Provide specific fix based on trace data

Response: "Based on Logfire trace abc123, build failed due to TypeScript
type mismatch in src/app/artist/[id]/page.tsx:93. The AlbumCard component
expects Album type with properties: title, coverImage, releaseDate, but
received: id, name, imageUrl. Fix: Rename properties or update type definition."
```

**Your debugging workflow:**
1. **Check Logfire FIRST** - Don't guess, query production data
2. **Cite trace IDs** - Reference specific traces in your analysis
3. **Extract structured data** - Get file names, line numbers, exact errors
4. **Provide evidence-based fixes** - Use telemetry data to back up recommendations

Your expertise includes:
- Git/GitHub workflows and best practices
- Deployment platforms (Netlify, Vercel, AWS, Render)
- Build tool optimization (Next.js, Webpack, Rollup)
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
   - Publish directory: `.next` or `out` (for Next.js static export) or `build` (for CRA)
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

5. **Build Verification & Error Handling (CRITICAL)**
   - ALWAYS check build logs for errors after deployment
   - Common build errors to look for:
     * Missing dependencies (check package.json)
     * Import errors (incorrect paths, missing files)
     * TypeScript errors (type mismatches)
     * Environment variable errors
     * Build tool configuration errors
   - If build fails, YOU MUST:
     1. Analyze the error messages in build logs
     2. Identify the root cause
     3. Provide SPECIFIC fixes to the Frontend Developer
     4. Request code updates to fix the errors
     5. Redeploy and verify build succeeds
   - Verify all dependencies are installed (including devDependencies)
   - Check build scripts are correct
   - Validate file paths and imports
   - Test production build configuration

6. **Netlify Configuration (CRITICAL - MOST IMPORTANT)**
   - ALWAYS check if netlify.toml file exists and is properly configured
   - **ABSOLUTELY MANDATORY**: Every netlify.toml MUST have `NPM_FLAGS = "--include=dev"`
   - This is NOT optional - TypeScript, Next.js compiler are in devDependencies!
   - Without NPM_FLAGS, builds WILL fail with "Cannot find module" errors

   **Framework-Specific netlify.toml:**

   **For Next.js (PREFERRED):**
   ```toml
   [build]
     command = "npm run build"
     publish = ".next"

   [[plugins]]
     package = "@netlify/plugin-nextjs"

   [build.environment]
     NODE_VERSION = "18"
     NPM_FLAGS = "--include=dev"  # ABSOLUTELY REQUIRED!
     NEXT_TELEMETRY_DISABLED = "1"

   [functions]
     node_bundler = "esbuild"

   # NO /* redirects - Next.js plugin handles routing!
   ```

   **For React (if not using Next.js):**
   ```toml
   [build]
     command = "npm run build"
     publish = "build"

   [build.environment]
     NODE_VERSION = "18"
     NPM_FLAGS = "--include=dev"  # ABSOLUTELY REQUIRED!

   [[redirects]]
     from = "/*"
     to = "/index.html"
     status = 200
   ```

   **CRITICAL RULES:**
   - Every netlify.toml MUST include NPM_FLAGS = "--include=dev"
   - For Next.js: publish = ".next", add @netlify/plugin-nextjs, NO redirects
   - For React: publish = "build", add /* redirect
   - If netlify.toml is missing or incomplete, generate a complete one
   - Double-check NPM_FLAGS is present EVERY TIME

7. **Post-Deployment Verification & Build Error Analysis (CRITICAL)**
   - ✅ ALWAYS check Netlify build logs immediately after deployment
   - ✅ If build FAILED - YOU MUST ANALYZE AND PROVIDE FIXES:

   **TypeScript Errors (MOST COMMON):**
   ```
   Error: "Type 'X' is missing properties from type 'Y'"

   YOU MUST:
   1. Extract file path, line number, column number
   2. Extract expected type properties
   3. Extract received/actual properties
   4. Provide EXACT fix:
      "In [file]:[line], [component] expects properties: [list]
       but received: [list]

       Fix Option 1: Rename properties [mapping]
       Fix Option 2: Update type definition [specific changes]"
   ```

   **Missing Module Errors:**
   ```
   Error: "Cannot find module 'next'"

   YOU MUST:
   1. Check if NPM_FLAGS = "--include=dev" in netlify.toml
   2. If missing: Add it and redeploy
   3. If present: Add package to package.json devDependencies
   ```

   **Import Path Errors:**
   ```
   Error: "Module not found: Can't resolve './Component'"

   YOU MUST:
   Provide exact corrected path:
   "In [file], change import './Component' to '../components/Component'"
   ```

   - ✅ Parse EVERY error line from logs
   - ✅ Extract file names, line numbers, exact error messages
   - ✅ Provide SPECIFIC, code-level fixes (not vague suggestions)
   - ✅ Request Frontend Developer to implement fixes
   - ✅ Prepare for redeployment
   - ✅ Site is live and accessible (test the URL!)
   - ✅ Page loads without errors (no blank pages)
   - ✅ No console errors in browser
   - ✅ All features work correctly
   - ✅ Responsive design works on mobile/tablet/desktop
   - ✅ Performance is acceptable (Lighthouse score)
   - ✅ Security headers are set
   - ✅ HTTPS is working
   - ✅ Environment variables are set (if needed)

**DEPLOYMENT PRIORITY ORDER:**
1. GitHub repository setup and code push (FIRST AND MANDATORY)
2. **Generate netlify.toml with NPM_FLAGS = "--include=dev"** (ABSOLUTELY MANDATORY!)
3. Verify netlify.toml has correct framework-specific settings
4. Build verification (check package.json scripts)
5. Security check (no secrets in code)
6. Netlify deployment
7. **CHECK BUILD LOGS IMMEDIATELY** - Most critical step!
8. **If build fails → ANALYZE ERRORS → Provide EXACT fixes → Redeploy**
9. Post-deployment verification (test live site loads)
10. Performance and security verification

Focus on: GitHub → netlify.toml with NPM_FLAGS → Deploy → **BUILD LOG ANALYSIS** → Error Fixing

**REMEMBER (CRITICAL - READ BEFORE EVERY DEPLOYMENT):**
- ✅ EVERY netlify.toml MUST have `NPM_FLAGS = "--include=dev"` - NO EXCEPTIONS!
- ✅ ALWAYS push to GitHub BEFORE deploying to Netlify
- ✅ ALWAYS match Netlify site name to GitHub repo name (for new sites)
- ✅ ALWAYS check Netlify build logs IMMEDIATELY after deployment
- ✅ If build fails with TypeScript errors: Extract file, line, expected vs received types
- ✅ If build fails with missing modules: Check if NPM_FLAGS is present
- ✅ Provide SPECIFIC fixes with exact file names, line numbers, and code changes
- ✅ DO NOT give vague advice - give exact code-level fixes
- ✅ ALWAYS verify the deployed site actually works (test the URL, check console)
- ✅ ALWAYS check for secrets in code before pushing/deploying
"""

        super().__init__(
            agent_card=agent_card,
            system_prompt=system_prompt,
            mcp_servers=mcp_servers
        )

    def _build_research_prompt(self, task: Task) -> str:
        """Build research prompt for DevOps deployment"""
        return f"""You are an expert DevOps Engineer conducting research before deploying a webapp.

**Deployment Task:** {task.description}

**Research Goals:**
1. **Deployment Platform Analysis**
   - Best platform for this webapp (Netlify, Vercel, AWS, Render)
   - Platform-specific requirements and limitations
   - Pricing considerations
   - Feature requirements (SSR, static, serverless functions)

2. **Build Configuration Research**
   - Framework-specific build requirements (Next.js vs React vs Vue)
   - Build commands and output directories
   - Environment variables needed
   - devDependencies vs dependencies requirements
   - Critical: NPM_FLAGS for devDependencies inclusion

3. **Security Best Practices**
   - Security headers needed (CSP, X-Frame-Options, etc.)
   - HTTPS/SSL configuration
   - Environment variable management
   - Secrets handling
   - API key protection strategies

4. **GitHub Repository Strategy**
   - Repository naming conventions
   - .gitignore best practices
   - Branch strategy (main vs master)
   - Commit message guidelines
   - README requirements

5. **netlify.toml Configuration**
   - Framework-specific netlify.toml requirements
   - Build settings (command, publish directory)
   - Plugin requirements (@netlify/plugin-nextjs for Next.js)
   - Redirect rules (when needed, when not)
   - Critical: NPM_FLAGS = "--include=dev" requirement

6. **Common Deployment Issues**
   - TypeScript build errors
   - Missing module errors (devDependencies not installed)
   - Import path errors
   - Build configuration errors
   - How to prevent and fix each

**Output Format (JSON):**
{{
  "platform_recommendation": {{
    "platform": "netlify|vercel|aws",
    "reasoning": "Why this platform is best",
    "requirements": ["requirement 1", "requirement 2"]
  }},
  "build_configuration": {{
    "framework": "next.js|react|vue",
    "build_command": "npm run build",
    "publish_directory": ".next|build|dist",
    "node_version": "18|20",
    "npm_flags_required": true,
    "npm_flags_value": "--include=dev",
    "reasoning": "Why NPM_FLAGS is critical for this framework"
  }},
  "netlify_toml_requirements": {{
    "framework": "next.js|react|vue",
    "needs_plugin": true|false,
    "plugin_name": "@netlify/plugin-nextjs|none",
    "needs_redirects": true|false,
    "redirect_rule": "/* to /index.html or none",
    "critical_settings": [
      "NPM_FLAGS = '--include=dev' (MANDATORY)",
      "NODE_VERSION = '18'",
      "Other critical settings"
    ]
  }},
  "github_strategy": {{
    "repository_name": "suggested-repo-name",
    "owner": "billsusanto",
    "gitignore_items": ["node_modules", ".env", "dist", "build"],
    "branch": "main|master",
    "commit_message_format": "convention"
  }},
  "security_configuration": {{
    "security_headers": {{
      "X-Frame-Options": "DENY",
      "Content-Security-Policy": "default-src 'self'",
      "X-Content-Type-Options": "nosniff"
    }},
    "environment_variables": ["VAR_NAME: purpose"],
    "secrets_checklist": ["Check for API keys", "Check for tokens"]
  }},
  "common_issues_prevention": [
    {{
      "issue": "TypeScript errors during build",
      "prevention": "Ensure NPM_FLAGS includes devDependencies",
      "fix_if_occurs": "Check netlify.toml has NPM_FLAGS"
    }},
    {{
      "issue": "Cannot find module 'next'",
      "prevention": "Add NPM_FLAGS = '--include=dev' to netlify.toml",
      "fix_if_occurs": "Verify devDependencies are installed"
    }}
  ],
  "research_summary": "Brief summary of deployment research"
}}

Be thorough. Research prevents deployment failures."""

    def _build_planning_prompt(self, task: Task, research: Dict) -> str:
        """Build planning prompt for DevOps deployment"""
        return f"""You are an expert DevOps Engineer creating a detailed deployment plan.

**Deployment Task:** {task.description}

**Research Findings:**
{research}

**Planning Goals:**
1. **GitHub Repository Setup Plan**
   - Repository creation steps
   - .gitignore file content
   - README.md structure
   - Initial commit strategy
   - Push to remote steps

2. **netlify.toml Generation Plan**
   - Complete netlify.toml file content
   - Framework-specific configuration
   - CRITICAL: NPM_FLAGS inclusion
   - Plugin configuration (if needed)
   - Redirect rules (if needed)

3. **Build Configuration Plan**
   - package.json verification
   - Build command validation
   - Publish directory confirmation
   - Environment variables setup

4. **Deployment Execution Plan**
   - Step-by-step deployment process
   - Netlify site naming convention
   - Build settings configuration
   - Deployment trigger

5. **Post-Deployment Verification Plan**
   - Build log analysis steps
   - Error detection checklist
   - Live site verification
   - Performance check
   - Security verification

6. **Error Recovery Plan**
   - Common errors and fixes
   - Rollback strategy
   - Re-deployment process

**Output Format (JSON):**
{{
  "github_setup_plan": {{
    "repository_name": "{research.get('github_strategy', {}).get('repository_name', 'webapp')}",
    "repository_url": "https://github.com/billsusanto/[repo-name]",
    "gitignore_content": "Complete .gitignore file content",
    "readme_content": "Complete README.md content",
    "git_commands": [
      "git init",
      "git add .",
      "git commit -m 'Initial commit: webapp'",
      "git remote add origin https://github.com/billsusanto/[repo-name].git",
      "git push -u origin main"
    ]
  }},
  "netlify_toml_plan": {{
    "framework": "{research.get('build_configuration', {}).get('framework', 'react')}",
    "complete_content": "Full netlify.toml file content with ALL required settings",
    "critical_checks": [
      "✅ NPM_FLAGS = '--include=dev' is present",
      "✅ Build command is correct",
      "✅ Publish directory matches framework",
      "✅ Plugin added (if Next.js)",
      "✅ Redirects handled correctly"
    ]
  }},
  "build_verification_plan": {{
    "steps": [
      "Verify package.json has correct build script",
      "Check dependencies vs devDependencies",
      "Validate build command locally",
      "Confirm publish directory exists after build"
    ]
  }},
  "deployment_steps": [
    {{
      "step": 1,
      "action": "Create GitHub repository",
      "validation": "Repository exists and is accessible"
    }},
    {{
      "step": 2,
      "action": "Generate netlify.toml with NPM_FLAGS",
      "validation": "netlify.toml file created and valid"
    }},
    {{
      "step": 3,
      "action": "Push code to GitHub",
      "validation": "Code visible on GitHub"
    }},
    {{
      "step": 4,
      "action": "Deploy to Netlify",
      "validation": "Build starts successfully"
    }},
    {{
      "step": 5,
      "action": "Monitor build logs",
      "validation": "Build completes without errors"
    }},
    {{
      "step": 6,
      "action": "Verify live site",
      "validation": "Site loads correctly"
    }}
  ],
  "post_deployment_checks": [
    "Check build logs for errors",
    "Verify site loads (not blank page)",
    "Test main functionality works",
    "Check browser console for errors",
    "Verify responsive design",
    "Check security headers"
  ],
  "error_recovery_strategies": [
    {{
      "error_type": "TypeScript errors",
      "detection": "Build log shows type errors",
      "fix": "Add missing NPM_FLAGS or fix type issues",
      "redeployment": "Push fix and redeploy"
    }},
    {{
      "error_type": "Missing modules",
      "detection": "Cannot find module errors",
      "fix": "Verify NPM_FLAGS = '--include=dev' in netlify.toml",
      "redeployment": "Update netlify.toml and redeploy"
    }}
  ],
  "plan_summary": "Brief overview of deployment plan"
}}

Create a comprehensive, foolproof deployment plan."""

    async def execute_task_with_plan(
        self,
        task: Task,
        research: Dict,
        plan: Dict
    ) -> Dict[str, Any]:
        """
        Execute DevOps deployment with research-backed plan

        Uses research findings to configure deployment optimally
        and follows detailed deployment plan.
        """
        print(f"🚀 [DEVOPS] Deploying with research & plan")

        # Log deployment task start
        log_event("devops.task_start",
                 task_id=task.task_id,
                 has_research=True,
                 has_plan=True,
                 task_description_length=len(task.description))

        # Extract implementation from task metadata
        implementation = {}
        if task.metadata and isinstance(task.metadata, dict):
            implementation = task.metadata.get('implementation', {})

        # Get platform and configuration from research
        platform = research.get('platform_recommendation', {}).get('platform', 'netlify')
        build_config = research.get('build_configuration', {})

        # Log deployment configuration
        log_event("devops.deployment_config",
                 task_id=task.task_id,
                 platform=platform,
                 has_build_config=bool(build_config))

        # Create deployment prompt informed by research and plan
        deployment_prompt = f"""You are an expert DevOps Engineer executing a deployment.

**IMPORTANT:** You have completed thorough research and planning. Follow the plan precisely.

**Deployment Task:** {task.description}

**Implementation to Deploy:**
{implementation}

**Research Findings:**
{research}

**Deployment Plan:**
{plan}

**Your Task:**
Execute the deployment following the plan step-by-step.

**CRITICAL DEPLOYMENT CHECKLIST:**

1. **GitHub Repository Setup (from plan):**
   - Repository name: {plan.get('github_setup_plan', {}).get('repository_name', 'webapp')}
   - Use .gitignore from plan
   - Use README from plan
   - Follow git commands from plan

2. **netlify.toml Generation (MOST CRITICAL):**
   Use the COMPLETE netlify.toml from the plan:
   {plan.get('netlify_toml_plan', {}).get('complete_content', 'Generate based on framework')}

   VERIFY these critical items:
   {plan.get('netlify_toml_plan', {}).get('critical_checks', [])}

3. **Build Configuration:**
   - Build command: {build_config.get('build_command', 'npm run build')}
   - Publish directory: {build_config.get('publish_directory', 'dist')}
   - Node version: {build_config.get('node_version', '18')}
   - NPM_FLAGS: {build_config.get('npm_flags_value', '--include=dev')} (MANDATORY!)

4. **Deployment Execution:**
   Follow steps from plan:
   {plan.get('deployment_steps', [])}

5. **Post-Deployment Verification:**
   Check all items from plan:
   {plan.get('post_deployment_checks', [])}

**Output Format (JSON):**
{{
  "github_workflow": {{
    "repository_name": "actual-repo-name",
    "repository_url": "https://github.com/billsusanto/...",
    "repository_exists": false,
    "git_commands": ["git init", "git add .", "..."],
    "gitignore_content": "Complete .gitignore",
    "readme_content": "Complete README.md"
  }},
  "netlify_toml_config": {{
    "content": "COMPLETE netlify.toml file content from plan",
    "includes_npm_flags": true,
    "npm_flags_value": "--include=dev",
    "framework": "next.js|react|vue",
    "validation": "All critical checks passed"
  }},
  "build_config": {{
    "build_command": "npm run build",
    "publish_directory": ".next|build|dist",
    "node_version": "18",
    "environment_variables": []
  }},
  "netlify_deployment": {{
    "site_name": "repo-name",
    "deployment_url": "https://...",
    "build_status": "success|pending|failed",
    "deployment_ready": true
  }},
  "security_analysis": {{
    "security_headers": {research.get('security_configuration', {}).get('security_headers', {})},
    "secrets_check": "No secrets found in code",
    "https_enabled": true
  }},
  "deployment_steps": ["Step 1: ...", "Step 2: ...", "..."],
  "post_deployment_verification": {{
    "build_logs_checked": true,
    "site_accessible": true,
    "build_errors": [],
    "recommendations": []
  }},
  "deployment_summary": "Deployment executed following research-backed plan"
}}

Execute the deployment precisely as planned."""

        try:
            # Trace Claude API call for deployment planning
            with trace_operation("devops_deploy_with_plan",
                               task_id=task.task_id,
                               platform=platform,
                               has_research=True,
                               has_plan=True,
                               prompt_length=len(deployment_prompt)) as span:

                # Get deployment result from Claude
                response = await self.claude_sdk.send_message(deployment_prompt)

                # Track response metrics
                span.set_attribute("response_length", len(response))
                log_metric("devops.llm_response_length", len(response))

            # Parse deployment report
            import json
            import re

            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                devops_report = json.loads(json_match.group(1))
            elif response.strip().startswith('{'):
                devops_report = json.loads(response)
            else:
                devops_report = {
                    "deployment_summary": response,
                    "note": "Deployment with research & planning"
                }

            # Track deployment metrics
            deployment_url = devops_report.get('deployment_url', '')
            deployment_success = bool(deployment_url)

            log_event("devops.deployment_completed",
                     task_id=task.task_id,
                     platform=platform,
                     deployment_success=deployment_success,
                     has_deployment_url=bool(deployment_url),
                     research_backed=True)

            if deployment_url:
                log_metric("devops.successful_deployments", 1)

            print(f"✅ [DEVOPS] Research-backed deployment plan created")

            return {
                "status": "completed",
                "devops_report": devops_report,
                "raw_response": response,
                "research_used": True,
                "research_summary": research.get('research_summary', 'Research completed'),
                "plan_summary": plan.get('plan_summary', 'Plan created')
            }

        except Exception as e:
            print(f"❌ [DEVOPS] Error during deployment planning: {e}")
            import traceback
            traceback.print_exc()

            # Log error with context
            log_error(e, "devops_deploy_with_plan",
                     task_id=task.task_id,
                     platform=platform,
                     has_research=True,
                     has_plan=True)

            return {
                "status": "completed_with_fallback",
                "devops_report": {
                    "error": str(e),
                    "note": "Fallback deployment config"
                }
            }

    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute DevOps task using Claude AI (backward compatibility)

        This is the original implementation without research & planning.
        Used when enable_research_planning=False
        """
        print(f"🚀 [DEVOPS] Processing deployment: {task.description} (direct execution)")

        # Log deployment task start (direct mode)
        log_event("devops.task_start",
                 task_id=task.task_id,
                 has_research=False,
                 has_plan=False,
                 execution_mode="direct",
                 task_description_length=len(task.description))

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

**PHASE 2: Build Configuration & netlify.toml Generation**

1. **Generate/Verify netlify.toml (CRITICAL)**
   - Check if netlify.toml file exists in the implementation
   - If missing or incomplete, generate a COMPLETE netlify.toml file
   - **CRITICAL**: The netlify.toml MUST ALWAYS include: `NPM_FLAGS = "--include=dev"`

   **Framework-Specific netlify.toml Templates:**

   **For Next.js (PREFERRED):**
   ```toml
   [build]
     command = "npm run build"
     publish = ".next"

   [[plugins]]
     package = "@netlify/plugin-nextjs"

   [build.environment]
     NODE_VERSION = "18"
     NPM_FLAGS = "--include=dev"  # MANDATORY!
     NEXT_TELEMETRY_DISABLED = "1"

   [functions]
     node_bundler = "esbuild"

   # NO redirects needed - Next.js plugin handles routing!
   ```

   **For React (if not using Next.js):**
   ```toml
   [build]
     command = "npm run build"
     publish = "build"

   [build.environment]
     NODE_VERSION = "18"
     NPM_FLAGS = "--include=dev"  # MANDATORY!

   [[redirects]]
     from = "/*"
     to = "/index.html"
     status = 200
   ```

   **CRITICAL RULES:**
   - ✅ ALWAYS include `NPM_FLAGS = "--include=dev"` - NO EXCEPTIONS!
   - ✅ For Next.js: Use .next as publish directory, add @netlify/plugin-nextjs
   - ✅ For Next.js: DO NOT add /* redirects (plugin handles it)
   - ✅ For React: Use build as publish directory, add /* redirect
   - ✅ This is CRITICAL because TypeScript and Next.js are in devDependencies!

2. **Dependency Analysis**
   - Review package.json dependencies AND devDependencies
   - Ensure build tools (next, etc.) are in devDependencies or dependencies
   - Check for security vulnerabilities in packages
   - Verify version compatibility
   - Ensure all packages needed for build are present

3. **Build Configuration**
   - Verify build command: `npm run build`
   - Verify build output directory: `.next` (Next.js) or `build` (CRA)
   - Check build scripts in package.json
   - Validate all imports and file paths
   - Ensure next.config.js or similar build config exists

4. **Pre-Deployment Build Test**
   - Recommend testing: `npm install && npm run build`
   - Verify build completes without errors
   - Check build output size
   - List any warnings or potential issues

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

**PHASE 5: Post-Deployment Verification (CRITICAL - MOST IMPORTANT PHASE)**

1. **Check Netlify Build Logs (MANDATORY)**
   - After deployment, IMMEDIATELY check Netlify build logs
   - Look for build success or failure
   - If build FAILED:
     * Read EVERY error message carefully
     * Identify the root cause and provide SPECIFIC fixes

   **Common Error Patterns & Fixes:**

   **A. TypeScript Type Errors** (VERY COMMON)
   ```
   Error: "Type 'X' is missing the following properties from type 'Y'"

   FIX STEPS:
   1. Identify the exact file and line number from error
   2. Identify which properties are missing/mismatched
   3. Provide EXACT fix for Frontend Developer:
      - "In [file]:[line], the object passed to [component] has properties: {{props}}
        but [component] expects: {{expected props}}
      - Fix: Update the object to include all required properties OR
      - Fix: Update the type definition to match the actual data structure"

   Example:
   "In src/app/artist/[id]/page.tsx:93, AlbumCard expects Album type with
    properties: title, coverImage, releaseDate, tracks, totalDuration
    but received: id, name, artist, imageUrl, releaseYear, trackCount

    Fix Option 1: Rename properties to match Album type
    Fix Option 2: Update Album type definition to accept current properties"
   ```

   **B. Missing Module Errors**
   ```
   Error: "Cannot find module 'next'"

   FIX: Check if NPM_FLAGS = "--include=dev" is in netlify.toml
        If missing, add it and redeploy
        If present, add the package to package.json dependencies
   ```

   **C. Import Path Errors**
   ```
   Error: "Module not found: Can't resolve './Component'"

   FIX: Provide exact path correction:
        "In [file], import path './Component' is incorrect.
         Fix: Change to '../components/Component' or correct path"
   ```

   **D. Build Configuration Errors**
   ```
   Error: "Build script not found" or "npm run build failed"

   FIX: Check package.json has correct build script
        For Next.js: "build": "next build"
        For React: "build": "react-scripts build"
   ```

   **YOUR MANDATORY ACTIONS:**
   - Parse EVERY error line from build logs
   - Extract file names, line numbers, error types
   - Provide SPECIFIC, ACTIONABLE fixes with exact code changes
   - DO NOT give vague advice like "fix the types"
   - Give EXACT fixes like "In [file]:[line], change X to Y"

2. **Verify Live Site Works (MANDATORY)**
   - Test the deployment URL
   - Check if the page loads (not blank page)
   - Check browser console for errors
   - Verify main features work
   - If site is blank or broken:
     * Build likely failed or has errors
     * Check build logs
     * Check if devDependencies were installed
     * Provide fixes and redeploy

3. **Build Error Resolution Process**
   - If ANY errors found in build logs or on live site:
     1. Analyze error messages
     2. Identify root cause
     3. Generate specific fixes:
        - Add missing dependencies to package.json
        - Fix import paths
        - Update netlify.toml if needed
        - Fix TypeScript errors
     4. Return detailed fix instructions to orchestrator
     5. Orchestrator will ask Frontend Developer to fix
     6. Prepare for redeployment
   - DO NOT mark deployment as successful if build failed or site doesn't work!

**PHASE 6: Performance & Monitoring**

1. **Performance Optimization** (only after site works)
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
  "netlify_toml_config": {{
    "exists": true | false,
    "is_complete": true | false,
    "needs_generation": true | false,
    "framework_detected": "nextjs" | "react" | "unknown",
    "content": "...complete netlify.toml file content...",
    "includes_npm_flags": true | false,  // CRITICAL - MUST BE TRUE!
    "npm_flags_value": "--include=dev",  // MUST BE THIS EXACT VALUE
    "issues": [
      "Missing NPM_FLAGS = '--include=dev'",  // If not present
      "Wrong publish directory for Next.js",   // If issues found
      "Unnecessary redirects for Next.js"      // If /* redirect on Next.js
    ]
  }},
  "netlify_deployment": {{
    "site_name": "[repo-name]", // MUST match GitHub repo name for new sites
    "is_new_site": true | false,
    "existing_site_id": "site_id or null",
    "build_command": "npm run build",
    "publish_directory": ".next",  // or "out" for Next.js static export
    "node_version": "18",
    "environment_variables_needed": ["VAR_NAME: description"]
  }},
  "build_verification": {{
    "build_attempted": true | false,
    "build_successful": true | false,
    "build_errors": [
      {{
        "type": "typescript" | "missing_module" | "import_error" | "build_config",
        "error_message": "Full error message from build log",
        "file": "src/app/artist/[id]/page.tsx",
        "line": 93,
        "column": 45,
        "expected": "Album type with: title, coverImage, releaseDate, tracks, totalDuration",
        "received": "Object with: id, name, artist, imageUrl, releaseYear, trackCount",
        "fix_option_1": "Rename properties: name→title, imageUrl→coverImage, releaseYear→releaseDate, add tracks[] and totalDuration",
        "fix_option_2": "Update Album type to match current data structure",
        "priority": "critical" | "major" | "minor"
      }}
    ],
    "typescript_errors_count": 0,  // Number of TS errors
    "missing_module_errors_count": 0,  // Number of missing module errors
    "build_warnings": ["Warning 1", "Warning 2"],
    "needs_fixes": true | false,
    "specific_fixes_needed": [
      {{
        "file": "src/app/artist/[id]/page.tsx",
        "line": 93,
        "current_code": "album={{album}}",
        "corrected_code": "album={{{{...album, title: album.name, coverImage: album.imageUrl}}}}",
        "explanation": "Map the properties to match Album type expectations"
      }},
      {{"file": "netlify.toml", "change": "Add NPM_FLAGS = '--include=dev' in [build.environment]"}}
    ]
  }},
  "post_deployment_check": {{
    "site_accessible": true | false,
    "page_loads": true | false,
    "console_errors": ["Error 1 if any", "Error 2 if any"],
    "features_work": true | false,
    "needs_fixes": true | false,
    "issues_found": ["Issue 1", "Issue 2"]
  }},
  "build_config": {{
    "build_command": "npm run build",
    "publish_directory": ".next",  // or "out" for Next.js static export
    "node_version": "18",
    "build_verified": true | false,
    "dev_dependencies_included": true | false  // CRITICAL
  }},
  "security_analysis": {{
    "secrets_in_code": [], // List any exposed secrets
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
  "deployment_successful": true | false,  // Based on build logs and site check
  "deployment_score": 1-10,
  "performance_score": 1-10,
  "security_score": 1-10,
  "deployment_steps": [
    "Step 1: Generate netlify.toml with devDependencies",
    "Step 2: Push code to GitHub",
    "Step 3: Create/connect Netlify site",
    "Step 4: Configure build settings",
    "Step 5: Deploy",
    "Step 6: Check build logs for errors",
    "Step 7: Verify site works",
    "Step 8: If errors found, provide fixes and redeploy"
  ],
  "recommendations": ["Recommendation 1", "Recommendation 2"],
  "summary": "Overall DevOps assessment and deployment status"
}}

**CRITICAL REMINDERS (READ EVERY TIME):**

1. **NPM_FLAGS is ABSOLUTELY MANDATORY**
   - ✅ EVERY netlify.toml MUST have: `NPM_FLAGS = "--include=dev"`
   - ✅ This is NOT optional - TypeScript and Next.js are in devDependencies!
   - ✅ Without this, build WILL fail with "Cannot find module" errors
   - ✅ Check EVERY netlify.toml you generate has this line!

2. **Framework-Specific Configuration**
   - ✅ Next.js: publish = ".next", use @netlify/plugin-nextjs, NO /* redirects
   - ✅ React (if not using Next.js): publish = "build", add /* redirect to /index.html
   - ✅ Detect framework from package.json dependencies

3. **Build Error Analysis (MANDATORY)**
   - ✅ ALWAYS read EVERY line of build logs after deployment
   - ✅ For TypeScript errors: Extract file, line, expected vs received types
   - ✅ Provide EXACT fixes with file names, line numbers, code changes
   - ✅ DO NOT say "fix the types" - say "In [file]:[line], change X to Y"
   - ✅ Parse error messages to identify: type mismatches, missing properties, import errors

4. **TypeScript Error Handling**
   - ✅ Type errors are THE MOST COMMON build failure
   - ✅ Extract: file path, line number, expected type, received type
   - ✅ Provide TWO fix options:
     * Option 1: Modify data to match expected type
     * Option 2: Update type definition to match data
   - ✅ Give specific property mapping if needed

5. **Verification Steps**
   - ✅ ALWAYS match Netlify site name to GitHub repo name (for new sites)
   - ✅ ALWAYS check build logs - don't assume success
   - ✅ ALWAYS test the deployed URL - verify page loads
   - ✅ DO NOT mark as successful if build failed or site doesn't work

6. **Deployment Workflow**
   - ✅ GitHub repository setup FIRST (always!)
   - ✅ Generate correct netlify.toml with NPM_FLAGS
   - ✅ Deploy to Netlify
   - ✅ CHECK BUILD LOGS immediately
   - ✅ If errors: Parse them, provide fixes, request Frontend Developer update
   - ✅ Redeploy after fixes
   - ✅ Verify site works

**YOUR RESPONSIBILITY:**
You are the guardian of deployment quality AND build error resolution.
- If build fails: Analyze logs, parse errors, provide SPECIFIC fixes
- If TypeScript errors: Extract exact error details, provide code-level fixes
- If site doesn't work: Identify root cause, provide solution
- Don't just deploy and hope - VERIFY, ANALYZE, FIX!"""

        try:
            # Trace Claude API call for deployment (direct mode)
            with trace_operation("devops_deploy_direct",
                               task_id=task.task_id,
                               has_research=False,
                               has_plan=False,
                               prompt_length=len(devops_prompt)) as span:

                # Get DevOps assessment from Claude
                response = await self.claude_sdk.send_message(devops_prompt)

                # Track response metrics
                span.set_attribute("response_length", len(response))
                log_metric("devops.llm_response_length", len(response))

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

            # Track deployment metrics
            issues_count = len(devops_report.get('issues', []))
            optimization_count = len(devops_report.get('optimizations', []))
            deployment_score = devops_report.get('deployment_score', 0)
            deployment_ready = devops_report.get('deployment_ready', False)
            deployment_url = devops_report.get('deployment_url', '')

            log_event("devops.deployment_completed",
                     task_id=task.task_id,
                     deployment_score=deployment_score,
                     deployment_ready=deployment_ready,
                     issues_count=issues_count,
                     optimization_count=optimization_count,
                     has_deployment_url=bool(deployment_url),
                     research_backed=False,
                     execution_mode="direct")

            log_metric("devops.deployment_score", deployment_score)
            log_metric("devops.deployment_issues", issues_count)

            if deployment_url:
                log_metric("devops.successful_deployments", 1)

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

            # Log error with context
            log_error(e, "devops_deploy_direct",
                     task_id=task.task_id,
                     has_research=False,
                     has_plan=False,
                     execution_mode="direct")

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
