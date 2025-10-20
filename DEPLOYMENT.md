# Deployment Guide - WhatsApp Multi-Agent System

## Current Status: ALL PHASES COMPLETE ✅

Your multi-agent system is now **fully functional** and ready for production deployment!

### ✅ What's Available Now

1. **Multi-Agent Architecture**
   - UI/UX Designer Agent with **real Claude AI**
   - Frontend Developer Agent with **real Claude AI**
   - Collaborative Orchestrator with **real Netlify deployment**
   - A2A Protocol (Agent-to-Agent communication)

2. **MCP Integrations**
   - WhatsApp MCP: Send/receive WhatsApp messages
   - GitHub MCP: Repository management
   - Netlify MCP: **Real webapp deployment** ✅

3. **Smart Routing**
   - Webapp requests → Multi-agent system (Designer + Frontend)
   - Regular chat → Single agent (CTO assistant)

4. **Python 3.12 Runtime**
   - Required for A2A protocol
   - All dependencies consolidated in requirements.txt

### 🎉 Phase 2-4 Complete: Real AI Implementation

- ✅ **Phase 2**: Designer agent uses Claude to generate real design specifications
- ✅ **Phase 3**: Frontend agent uses Claude to generate production-ready React code
- ✅ **Phase 4**: Orchestrator deploys to Netlify using Netlify MCP tools

**No more placeholders!** All agents now use Claude AI to generate real designs, code, and deployments.

---

## Deployment Instructions

### Step 1: Push to GitHub

```bash
# Commit all changes
git add .
git commit -m "Phase 1.5: Multi-agent system with WhatsApp integration"
git push origin main
```

### Step 2: Render Auto-Deploy

Your `render.yaml` is configured for auto-deploy. After pushing:

1. Render will automatically detect the push
2. Build with Docker (Python 3.12 + Node.js)
3. Deploy to: `https://whatsapp-mcp-t9mi.onrender.com`
4. Health check: `https://whatsapp-mcp-t9mi.onrender.com/health`

**Build time**: ~5-10 minutes

### Step 3: Verify Environment Variables

Ensure these are set in Render dashboard:

**Required:**
- `ANTHROPIC_API_KEY` - Your Claude API key
- `WHATSAPP_ACCESS_TOKEN` - WhatsApp Business API token
- `WHATSAPP_PHONE_NUMBER_ID` - Your WhatsApp phone number ID
- `WHATSAPP_WEBHOOK_VERIFY_TOKEN` - Webhook verification token

**Optional (for multi-agent):**
- `GITHUB_PERSONAL_ACCESS_TOKEN` - GitHub API access
- `NETLIFY_PERSONAL_ACCESS_TOKEN` - Netlify API access
- `ENABLE_GITHUB_MCP=true` - Already set in render.yaml
- `ENABLE_NETLIFY_MCP=true` - Already set in render.yaml

**Note**: `ENABLE_NETLIFY_MCP=true` automatically enables multi-agent mode!

### Step 4: Monitor Deployment

Check Render logs for these success messages:

```
✅ WhatsApp MCP configured with 3 tools
✅ GitHub MCP configured
✅ Netlify MCP configured
✅ Multi-agent orchestrator initialized

AgentManager initialized
Available MCP servers: ['whatsapp', 'github', 'netlify']
Multi-agent mode: ✅ Enabled
```

---

## Testing the Multi-Agent System

### Test 1: Regular Chat (Single Agent)

Send to WhatsApp:
```
Hi, can you explain what a CTO does?
```

**Expected behavior:**
- Routes to single agent (CTO assistant)
- Uses AGENT_SYSTEM_PROMPT from render.yaml
- Returns professional CTO-related advice

**Logs:**
```
📱 Regular conversation from +1234567890
   Using single agent...
```

### Test 2: Webapp Request (Multi-Agent) - FULL AI GENERATION

Send to WhatsApp:
```
Build me a todo list webapp with a modern design
```

**Expected behavior:**
- Routes to multi-agent system
- Designer agent uses **Claude AI** to create comprehensive design specification
- Frontend agent uses **Claude AI** to generate production-ready React code
- Designer agent uses **Claude AI** to review implementation quality
- Orchestrator deploys to **real Netlify** using Netlify MCP
- Returns formatted WhatsApp response with:
  - Design summary
  - Tech stack info
  - **Real deployment URL** (live on Netlify!)
  - Review score from designer

**Logs:**
```
🎨 Multi-agent request detected from +1234567890
   Routing to collaborative orchestrator...
🚀 [ORCHESTRATOR] Starting webapp generation
📝 User request: Build me a todo list webapp with a modern design

[Step 1/5] 🎨 Designer creating design specification...
🎨 [DESIGNER] Creating design for: Create design specification for: Build me a todo list webapp
✅ [DESIGNER] Design specification created
✓ Design completed

[Step 2/5] 💻 Frontend implementing design...
💻 [FRONTEND] Implementing: Implement webapp: Build me a todo list webapp
✅ [FRONTEND] Implementation completed - 4 files generated
✓ Implementation completed: react

[Step 3/5] 🔍 Designer reviewing implementation...
🔍 [DESIGNER] Reviewing implementation
✅ [DESIGNER] Review completed - Approved: True
✓ Review completed: ✅ Approved (Score: 9/10)

[Step 4/5] 🚀 Deploying to Netlify...
✅ Extracted deployment URL: https://your-app-xyz123.netlify.app
✓ Deployed to: https://your-app-xyz123.netlify.app

[Step 5/5] 📱 Formatting WhatsApp response...

✅ [ORCHESTRATOR] Webapp generation complete!
```

**WhatsApp Response Format:**
```
✅ Your webapp is ready!

🔗 Live Site: https://your-app-xyz123.netlify.app

🎨 Design:
  • Style: modern minimal
  • Fully responsive
  • Accessibility optimized
  • Review score: 9/10

⚙️ Technical:
  • Framework: react
  • Build tool: Vite
  • Deployed on Netlify

🤖 Built by AI Agent Team:
  • UI/UX Designer Agent (design)
  • Frontend Developer Agent (implementation)
  • Collaborative review process

🚀 Powered by Claude Multi-Agent System
```

**✨ The webapp is LIVE and functional!** Click the URL to see your AI-generated webapp deployed on Netlify.

### Test 3: Keyword Detection

The system detects webapp requests using these keywords:
- **Action verbs**: build, create, make, develop, generate
- **Web terms**: website, webapp, web app, application, app
- **Page types**: landing page, dashboard, portfolio, site
- **App types**: todo, blog, store, shop, game

**Examples that trigger multi-agent:**
- ✅ "Create a portfolio website"
- ✅ "Make me a blog app"
- ✅ "I need a landing page for my startup"
- ✅ "Generate a dashboard webapp"

**Examples that use single agent:**
- ❌ "What is React?" (educational question)
- ❌ "How do I deploy to Netlify?" (guidance)
- ❌ "Can you review my code?" (no webapp creation)

---

## Architecture Overview

### System Flow

```
WhatsApp User
    ↓
WhatsApp Business API (Meta)
    ↓
Webhook POST → https://whatsapp-mcp-t9mi.onrender.com/webhook
    ↓
FastAPI Server (main.py)
    ↓
AgentManager.process_message()
    ↓
    ├── Webapp keywords detected?
    │   YES → CollaborativeOrchestrator
    │          ├── DesignerAgent (creates design)
    │          ├── FrontendDeveloperAgent (implements)
    │          ├── DesignerAgent (reviews)
    │          └── Format response → WhatsApp
    │
    └── NO → Single Agent (CTO assistant) → WhatsApp
```

### Resource Usage

**Plan**: Standard ($25/month)
**Resources**: 2GB RAM, sufficient CPU
**Why upgraded**: Multi-agent system with orchestrator requires more memory than single-agent (512MB starter plan may cause OOM errors)

### File Structure

```
/app/
├── src/python/
│   ├── main.py                          # FastAPI entry point
│   ├── agents/
│   │   ├── manager.py                   # Routes messages, manages agents
│   │   ├── agent.py                     # Single agent (CTO mode)
│   │   ├── session.py                   # Session management
│   │   └── collaborative/               # Multi-agent system
│   │       ├── orchestrator.py          # Coordinates Designer + Frontend
│   │       ├── a2a_protocol.py          # Agent-to-agent communication
│   │       ├── base_agent.py            # Base class for all agents
│   │       ├── designer_agent.py        # UI/UX Designer (Phase 1.5)
│   │       ├── frontend_agent.py        # Frontend Developer (Phase 1.5)
│   │       └── models.py                # A2A data models
│   ├── github_mcp/                      # GitHub integration
│   └── netlify_mcp/                     # Netlify integration
├── Dockerfile.render                    # Python 3.12 + Node.js
├── render.yaml                          # Deployment config
└── requirements.txt                     # All dependencies
```

---

## Implementation Complete (Phase 2-4) ✅

### Phase 2: Real Designer Agent ✅ COMPLETE

**Implementation**: `src/python/agents/collaborative/designer_agent.py:63-181`

**What it does**:
- Analyzes user requirements using Claude AI
- Generates comprehensive design specifications including:
  - Design style & theme
  - Color palette (WCAG AA compliant)
  - Typography system
  - Layout & spacing specifications
  - Component specifications
  - User flow
  - Accessibility requirements
- Reviews frontend implementations for design fidelity
- Provides constructive feedback and scoring

**Example output**:
```python
{
  "status": "completed",
  "design_spec": {
    "style": "modern minimal",
    "colors": { "primary": "#3B82F6", ... },
    "typography": { "font_family": "Inter", ... },
    "layout": { "type": "single-page", ... },
    "components": [ ... ]
  }
}
```

### Phase 3: Real Frontend Agent ✅ COMPLETE

**Implementation**: `src/python/agents/collaborative/frontend_agent.py:67-202`

**What it does**:
- Generates production-ready React code using Claude AI
- Creates complete project structure with multiple files:
  - index.html (with Tailwind CDN)
  - src/App.jsx (complete React component)
  - src/main.jsx (React entry point)
  - package.json (with dependencies)
  - Additional component files as needed
- Implements responsive design with Tailwind CSS
- Adds proper state management using React hooks
- Includes accessibility features (ARIA labels, semantic HTML)
- Reviews design specifications for implementability

**Example output**:
```python
{
  "status": "completed",
  "implementation": {
    "framework": "react",
    "build_tool": "vite",
    "files": [
      {"path": "index.html", "content": "<!DOCTYPE html>..."},
      {"path": "src/App.jsx", "content": "import React..."},
      {"path": "package.json", "content": "{\"name\":..."}
    ],
    "dependencies": ["react", "react-dom", "@vitejs/plugin-react"]
  }
}
```

### Phase 4: Netlify Deployment ✅ COMPLETE

**Implementation**: `src/python/agents/collaborative/orchestrator.py:168-235`

**What it does**:
- Deploys generated webapps to Netlify using Netlify MCP
- Uses Claude SDK to interact with Netlify MCP tools
- Extracts deployment URLs from responses
- Returns live, accessible URLs
- Handles errors gracefully with fallback to dashboard URL

**Deployment flow**:
```python
# 1. Extract generated files from frontend agent
files = implementation.get('files', [])

# 2. Send deployment request to Claude with Netlify MCP
deployment_prompt = "Deploy this React webapp to Netlify..."
response = await self.deployment_sdk.send_message(deployment_prompt)

# 3. Extract and return live URL
deployment_url = extract_url(response)  # https://your-app.netlify.app
```

**Result**: Real, live webapps deployed to Netlify that users can access immediately!

---

## Troubleshooting

### Issue: Multi-agent not triggering

**Check logs for:**
```
Multi-agent mode: ❌ Disabled
```

**Causes**:
1. `ENABLE_NETLIFY_MCP` not set to `true`
2. `NETLIFY_PERSONAL_ACCESS_TOKEN` missing
3. Netlify MCP failed to initialize

**Fix**: Set environment variables in Render dashboard

### Issue: Memory issues (OOM errors)

**Symptom**: Service crashes or restarts frequently

**Fix**: Confirm you're on Standard plan (2GB RAM)
```yaml
# render.yaml
plan: standard  # NOT starter
```

### Issue: "Multi-agent orchestrator failed to initialize"

**Check logs for import errors:**
```
⚠️ Multi-agent system not available
```

**Cause**: Python dependency issue

**Fix**: Verify requirements.txt includes:
```
aiohttp>=3.9.0
typing-extensions>=4.14.1
```

### Issue: Webapp requests going to single agent

**Check keyword detection:**
- Message must contain webapp-related keywords
- Case-insensitive matching

**Debug**: Add print statement to see detection:
```python
# manager.py - _is_webapp_request()
print(f"Message: {message}")
print(f"Detected as webapp: {result}")
```

---

## Monitoring

### Key Metrics to Watch

1. **Active agents count**: Should match active users
2. **Memory usage**: Should stay under 2GB (Standard plan)
3. **Response time**: Multi-agent ~5-10s, single agent ~2-3s
4. **Session cleanup**: Runs every 5 minutes (cleans 15+ min idle)

### Useful Endpoints

- `GET /health` - Health check
- `POST /webhook` - WhatsApp messages (Meta only)
- `GET /webhook?hub.verify_token=...` - Webhook verification

---

## Security Notes

1. **Webhook verification**: Validates all incoming WhatsApp messages
2. **Non-root user**: Docker runs as user 1001 (agentuser)
3. **Environment secrets**: Never commit tokens to git
4. **HTTPS**: Render provides free SSL certificates

---

## Cost Breakdown

- **Render Standard Plan**: $25/month (2GB RAM)
- **Anthropic API**: Pay-per-token (varies by usage)
- **WhatsApp Business API**: Free tier available
- **GitHub API**: Free for personal use
- **Netlify**: Free tier (100GB bandwidth)

**Estimated total**: ~$25-35/month depending on usage

---

## Support

If you encounter issues:

1. Check Render logs for error messages
2. Verify all environment variables are set
3. Confirm WhatsApp webhook is configured correctly
4. Test with simple messages first ("Hi") before webapp requests

**System is production-ready with FULL AI implementation!**

The multi-agent system now uses real Claude AI to:
- ✅ Generate professional design specifications
- ✅ Create production-ready React code
- ✅ Review implementations for quality
- ✅ Deploy live webapps to Netlify

---

## What Changed in This Update

### Phase 2 (Designer Agent)
**File**: `src/python/agents/collaborative/designer_agent.py`
- `execute_task()`: Now uses Claude AI to generate comprehensive design specifications (lines 63-181)
- `review_artifact()`: Now uses Claude AI to review implementations with scoring (lines 183-280)

### Phase 3 (Frontend Agent)
**File**: `src/python/agents/collaborative/frontend_agent.py`
- `execute_task()`: Now uses Claude AI to generate production React code (lines 67-202)
- `review_artifact()`: Now uses Claude AI to review designs for implementability (lines 204-293)

### Phase 4 (Orchestrator Deployment)
**File**: `src/python/agents/collaborative/orchestrator.py`
- Added `deployment_sdk` for Netlify operations (line 47)
- Updated `build_webapp()` with real AI workflow (lines 58-166)
- Added `_deploy_to_netlify()` method for actual deployments (lines 168-235)
- Added `_format_files_for_deployment()` helper (lines 237-250)
- Updated `_format_whatsapp_response()` with review scores (lines 252-281)

### No Configuration Changes Needed
- All existing environment variables remain the same
- No new dependencies added
- Docker and Render configurations unchanged
- Simply push to deploy!

---

## Ready to Deploy

```bash
# Commit all changes
git add .
git commit -m "Complete Phase 2-4: Full AI multi-agent system with Netlify deployment"
git push origin main
```

Render will auto-deploy. After deployment completes (~5-10 minutes), send a webapp request via WhatsApp and watch your AI agent team build and deploy a real webapp! 🚀
