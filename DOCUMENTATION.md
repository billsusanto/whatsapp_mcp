# WhatsApp Multi-Agent System - Complete Documentation

**Version:** 2.1.0
**Last Updated:** October 24, 2025
**Status:** Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Installation & Setup](#installation--setup)
5. [Configuration](#configuration)
6. [Core Components](#core-components)
7. [Multi-Agent System](#multi-agent-system)
8. [API Reference](#api-reference)
9. [Workflow Types](#workflow-types)
10. [Message Handling](#message-handling)
11. [Deployment](#deployment)
12. [Troubleshooting](#troubleshooting)
13. [Performance & Optimization](#performance--optimization)
14. [Security](#security)
15. [Testing](#testing)

---

## Overview

### What is This?

A production-ready WhatsApp-integrated AI assistant system that uses Claude AI (Sonnet 4.5) and a multi-agent architecture to build complete, deployable web applications through WhatsApp chat.

### Key Features

**Single-Agent Mode:**
- Personal AI assistant for individual conversations
- Context-aware responses with session management
- 60-minute conversation memory (10 messages max)

**Multi-Agent Mode:**
- Collaborative team of 5 specialized AI agents
- Builds production-ready webapps from natural language
- Real-time WhatsApp notifications on progress
- Intelligent refinement handling during development
- Automatic build verification and error fixing
- Quality loops (iterative improvement until score ≥ 9/10)

**Integrations:**
- WhatsApp Business Cloud API (v18.0)
- Claude AI (Sonnet 4.5 - `claude-sonnet-4-5-20250929`)
- Model Context Protocol (MCP)
- GitHub (repository management via MCP)
- Netlify (automated deployment via MCP)
- Logfire (observability & telemetry)

### Use Cases

1. **Personal Assistant** - Ask questions, get technical guidance
2. **Webapp Builder** - "Build me a todo app with React"
3. **Code Review** - AI-powered code reviews with security analysis
4. **Deployment Automation** - Automatic GitHub + Netlify deployment
5. **Bug Fixing** - "Fix the build errors" → AI diagnoses and fixes
6. **Design Consultation** - Get UI/UX design specifications

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          WhatsApp User                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓ (sends message)
┌─────────────────────────────────────────────────────────────────┐
│                   WhatsApp Business Cloud API                   │
│                         (v18.0)                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓ (webhook POST)
┌─────────────────────────────────────────────────────────────────┐
│                FastAPI Application (main.py)                    │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │          WhatsAppWebhookParser (parser.py)                │ │
│  │  • Parse incoming messages                                │ │
│  │  • Extract phone number, message text, type               │ │
│  └───────────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Spawn async task → Return 200 OK (<5s requirement)       │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ↓ (async task)
┌─────────────────────────────────────────────────────────────────┐
│                      AgentManager (manager.py)                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │       AI Message Classifier (Claude-powered)            │   │
│  │  ┌───────────────┬────────────────┬──────────────────┐ │   │
│  │  │ webapp_request│  refinement    │   conversation   │ │   │
│  │  │  (multi-agent)│  (orchestrator)│  (single-agent)  │ │   │
│  │  └───────────────┴────────────────┴──────────────────┘ │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │   SessionManager - Per-user conversation history       │   │
│  │   • TTL: 60 minutes                                     │   │
│  │   • Max history: 10 messages                            │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
         ↓                              ↓                  ↓
┌──────────────────┐      ┌─────────────────────────┐    ┌──────────┐
│  Single Agent    │      │ Multi-Agent Orchestrator│    │  Single  │
│                  │      │  ┌────────────────────┐ │    │  Agent   │
│  ClaudeSDK       │      │  │  AI Workflow       │ │    │          │
│  + MCP Tools     │      │  │  Planner           │ │    │          │
│  (4096 tokens)   │      │  │  (Claude)          │ │    │          │
└──────────────────┘      │  └────────────────────┘ │    └──────────┘
                          │         ↓               │
                          │  ┌────────────────────┐ │
                          │  │ Lazy Agent Init    │ │
                          │  │ (on-demand)        │ │
                          │  │                    │ │
                          │  │ • Designer         │ │
                          │  │ • Frontend Dev     │ │
                          │  │ • Code Reviewer    │ │
                          │  │ • QA Engineer      │ │
                          │  │ • DevOps           │ │
                          │  └────────────────────┘ │
                          │         ↓               │
                          │  A2A Protocol           │
                          │  (Agent-to-Agent)       │
                          │  • register_agent()     │
                          │  • send_task()          │
                          │  • request_review()     │
                          └─────────────────────────┘
                                     ↓
                          ┌─────────────────────────┐
                          │   Claude AI API         │
                          │   (Sonnet 4.5)          │
                          │   Model: claude-sonnet- │
                          │   4-5-20250929          │
                          └─────────────────────────┘
                                     ↓
                          ┌─────────────────────────┐
                          │   MCP Servers           │
                          │   • WhatsApp            │
                          │   • GitHub              │
                          │   • Netlify             │
                          └─────────────────────────┘
```

### System Components

#### 1. **FastAPI Application** (`main.py` - 353 lines)
- Webhook endpoint for WhatsApp messages
- Health check endpoints
- Background cleanup tasks (every 60 min)
- Async message processing
- Logfire telemetry integration

#### 2. **Agent Manager** (`agents/manager.py` - 481 lines)
- Routes messages to appropriate agents
- Per-user orchestrator management
- AI-powered intent classification
- Smart refinement handling
- Session lifecycle management

#### 3. **Session Manager** (`agents/session.py` - 129 lines)
- 60-minute conversation TTL
- 10-message history limit
- Auto-cleanup of expired sessions
- Per-user context tracking

#### 4. **Multi-Agent Orchestrator** (`agents/collaborative/orchestrator.py` - 2,015 lines)
- Coordinates 5 specialized agents
- AI-powered workflow planning
- Real-time WhatsApp notifications
- Build retry with error detection (max 10 retries)
- Quality loops (max 10 iterations, min score 9/10)
- Lazy agent initialization (memory optimization)

#### 5. **Specialized Agents**

**Designer Agent** (`designer_agent.py` - 612 lines):
- Creates design specifications
- Reviews frontend code vs design
- Ensures design fidelity
- Accessibility guidelines (WCAG 2.1)

**Frontend Developer Agent** (`frontend_agent.py` - 872 lines):
- Writes React/Next.js/Vue code
- Production-ready implementations
- NO placeholders or TODOs
- Fixes build errors
- GitHub-ready projects

**Code Reviewer Agent** (`code_reviewer_agent.py` - 697 lines):
- Security analysis (OWASP Top 10)
- Performance review
- Best practices validation
- Scores code quality (1-10)
- 10 comprehensive review criteria

**QA Engineer Agent** (`qa_agent.py` - 751 lines):
- Functional testing
- Accessibility testing (WCAG 2.1)
- Cross-browser validation
- Performance testing (Core Web Vitals)
- Responsive design testing

**DevOps Engineer Agent** (`devops_agent.py` - 1,272 lines):
- Netlify deployment
- Build error detection
- netlify.toml generation (with NPM_FLAGS fix)
- Post-deployment verification
- Build retry logic

#### 6. **A2A Protocol** (`agents/collaborative/a2a_protocol.py` - 157 lines)
- Standardized agent communication
- Task requests/responses
- Review requests/responses
- Agent discovery and registration

#### 7. **Claude SDK Wrapper** (`sdk/claude_sdk.py` - 294 lines)
- Model: `claude-sonnet-4-5-20250929` (Sonnet 4.5)
- Max tokens: 4096
- MCP server integration
- Tool auto-approval: `bypassPermissions`
- Conversation context management

#### 8. **MCP Integration**
- **WhatsApp MCP** (`whatsapp_mcp/client.py` - 191 lines): Send messages, mark as read, media handling
- **GitHub MCP** (`github_mcp/server.py` - 113 lines): Repository management, file operations
- **Netlify MCP** (`netlify_mcp/server.py` - 123 lines): Site deployment, build management

#### 9. **Telemetry** (`utils/telemetry.py` - 446 lines)
- Logfire integration
- FastAPI instrumentation
- Anthropic SDK instrumentation
- HTTPX instrumentation
- Event logging, metrics, performance tracking

---

## Quick Start

### Prerequisites

- Python 3.12+
- WhatsApp Business Account
- Anthropic API key (Claude)
- (Optional) GitHub Personal Access Token
- (Optional) Netlify Personal Access Token

### 5-Minute Setup

```bash
# 1. Clone repository
git clone <your-repo-url>
cd whatsapp_mcp

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 5. Run locally
python src/python/main.py

# 6. Test webhook
curl http://localhost:8000/health
```

### First Message

Send a WhatsApp message to your business number:

```
Hello!
```

**Expected response**: AI assistant greeting

Try multi-agent mode:

```
Build me a todo app with React and Tailwind
```

**Expected**: Multi-agent team starts building, sends real-time updates

---

## Installation & Setup

### Local Development Setup

#### Step 1: Environment Setup

```bash
# Create .env file
cat > .env << 'EOF'
# Claude AI (REQUIRED)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# WhatsApp Business API (REQUIRED)
WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_custom_verify_token
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id

# GitHub MCP (Optional - required for GitHub integration)
GITHUB_PERSONAL_ACCESS_TOKEN=your_github_token
ENABLE_GITHUB_MCP=true

# Netlify MCP (Optional - required for multi-agent deployments)
NETLIFY_PERSONAL_ACCESS_TOKEN=your_netlify_token
ENABLE_NETLIFY_MCP=true

# Agent Configuration (Optional)
AGENT_SYSTEM_PROMPT="You are a helpful AI assistant."

# Service Configuration (Optional)
PORT=8000

# Telemetry (Optional - Logfire observability)
LOGFIRE_TOKEN=your_logfire_token
EOF
```

#### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

**Key dependencies**:
- `claude-agent-sdk>=0.1.0` - Official Claude SDK
- `anthropic>=0.18.0` - Claude API client
- `fastapi>=0.104.0` - Web framework
- `uvicorn[standard]>=0.24.0` - ASGI server
- `mcp>=1.18.0` - Model Context Protocol
- `logfire>=0.40.0` - Observability platform
- `requests>=2.31.0` - HTTP client
- `pydantic>=2.0.0` - Data validation

#### Step 3: Configure WhatsApp Webhook

1. Go to [Meta Business Suite](https://business.facebook.com/)
2. Navigate to **WhatsApp → Configuration**
3. Set webhook URL: `http://localhost:8000/webhook` (use ngrok for local testing)
4. Set verify token: (same as `WHATSAPP_WEBHOOK_VERIFY_TOKEN`)
5. Subscribe to `messages` events

#### Step 4: Test Locally

```bash
# Start server
python src/python/main.py

# In another terminal, test health endpoint
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "service": "whatsapp-mcp",
  "api_key_configured": true,
  "whatsapp_configured": true,
  "github_mcp_enabled": true,
  "netlify_mcp_enabled": true,
  "active_agents": 0,
  "available_mcp_servers": ["whatsapp", "github", "netlify"]
}

# Send test message via API
curl -X POST http://localhost:8000/agent/process \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1234567890", "message": "Hello!"}'
```

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | ✅ Yes | - | Claude API authentication key |
| `WHATSAPP_ACCESS_TOKEN` | ✅ Yes | - | WhatsApp Business API token |
| `WHATSAPP_PHONE_NUMBER_ID` | ✅ Yes | - | Phone number ID for sending messages |
| `WHATSAPP_WEBHOOK_VERIFY_TOKEN` | ✅ Yes | - | Custom token for webhook verification |
| `WHATSAPP_BUSINESS_ACCOUNT_ID` | ⚠️ Recommended | - | WhatsApp Business Account ID |
| `GITHUB_PERSONAL_ACCESS_TOKEN` | ❌ Optional | - | GitHub API token for MCP |
| `ENABLE_GITHUB_MCP` | ❌ Optional | `false` | Enable GitHub integration |
| `NETLIFY_PERSONAL_ACCESS_TOKEN` | ❌ Optional | - | Netlify API token for MCP |
| `ENABLE_NETLIFY_MCP` | ❌ Optional | `false` | Enable Netlify deployment (required for multi-agent) |
| `AGENT_SYSTEM_PROMPT` | ❌ Optional | Default prompt | Custom system prompt for single-agent mode |
| `PORT` | ❌ Optional | `8000` | Server port |
| `LOGFIRE_TOKEN` | ❌ Optional | - | Logfire observability token |

### System Configuration

**Session Management** (`agents/manager.py:37`):
```python
session_manager = SessionManager(
    ttl_minutes=60,      # 60-minute conversation timeout
    max_history=10       # Keep last 10 messages
)
```

**Claude SDK** (`sdk/claude_sdk.py:104-105`):
```python
model = "claude-sonnet-4-5-20250929"  # Sonnet 4.5
max_tokens = 4096                      # Token limit per response
```

**Orchestrator** (`agents/collaborative/orchestrator.py:131-134`):
```python
max_review_iterations = 10    # Maximum quality improvement iterations
min_quality_score = 9         # Minimum acceptable score (out of 10)
max_build_retries = 10        # Maximum deployment retry attempts
enable_agent_caching = False  # Agent reuse (False = saves memory)
```

**WhatsApp API** (`whatsapp_mcp/client.py:25-26`):
```python
api_version = "v18.0"
base_url = f"https://graph.facebook.com/{api_version}/{phone_number_id}"
```

---

## Core Components

### 1. Main Application (`main.py`)

**Entry Point** (340-353):
```python
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")
```

**Key Endpoints**:

| Endpoint | Method | Handler | Line | Purpose |
|----------|--------|---------|------|---------|
| `/` | GET | `root()` | 103-110 | Health check |
| `/health` | GET | `health_check()` | 113-127 | Detailed status |
| `/webhook` | GET | `webhook_verify()` | 130-144 | WhatsApp verification |
| `/webhook` | POST | `webhook_receive()` | 147-191 | **CRITICAL** - Incoming messages |
| `/agent/process` | POST | `process_message()` | 266-294 | Direct messaging (testing) |
| `/agent/reset/{phone}` | POST | `reset_session()` | 297-313 | Clear history |

**Critical Flow**:
```python
# Line 147: Webhook receives message
@app.post("/webhook")
async def webhook_receive(request: Request):
    body = await request.json()
    message_data = WhatsAppWebhookParser.parse_message(body)  # Line 155

    # Line 183: Spawn async task (don't block webhook response)
    asyncio.create_task(process_whatsapp_message(from_number, message_text))

    # Line 186: Return 200 OK immediately (WhatsApp requires <5s response)
    return {"status": "ok"}
```

**Background Tasks**:
- `periodic_cleanup()` (243-263): Runs every 60 minutes to clean expired sessions
- `startup_event()` (316-329): Initialize service, start background tasks
- `shutdown_event()` (332-337): Cleanup all agents

### 2. Agent Manager (`agents/manager.py`)

**Purpose**: Routes messages to single-agent or multi-agent systems

**Initialization** (27-105):
```python
def __init__(self, whatsapp_mcp_tools, enable_github, enable_netlify):
    # Session TTL: 60 minutes, max history: 10 messages
    self.session_manager = SessionManager(ttl_minutes=60, max_history=10)

    # Available MCP servers
    self.available_mcp_servers = {}

    # Per-user orchestrators
    self.orchestrators: Dict[str, any] = {}

    # Multi-agent enabled if Netlify MCP available
    self.multi_agent_enabled = MULTI_AGENT_AVAILABLE and enable_netlify
```

**Main Router** (`process_message()` - 127-236):
```python
async def process_message(phone_number: str, message: str) -> str:
    # Check if orchestrator active (line 142)
    active_orchestrator = self.orchestrators.get(phone_number)

    if active_orchestrator and active_orchestrator.is_active:
        # Classify message (line 151)
        message_type = await self._classify_message(message, ...)

        # Route based on classification (lines 160-198)
        if message_type == "refinement":
            return await active_orchestrator.handle_refinement(message)
        elif message_type == "status_query":
            return await active_orchestrator.handle_status_query()
        elif message_type == "cancellation":
            return await active_orchestrator.handle_cancellation()
        # ... etc

    # Check if webapp request (line 201)
    if self.multi_agent_enabled and await self._is_webapp_request(message):
        # Create orchestrator (line 207)
        orchestrator = CollaborativeOrchestrator(
            mcp_servers=self.available_mcp_servers,
            user_phone_number=phone_number
        )
        self.orchestrators[phone_number] = orchestrator

        # Execute build (line 214)
        return await orchestrator.build_webapp(message)

    # Fallback to single agent (line 235)
    agent = self.get_or_create_agent(phone_number)
    return await agent.process_message(message)
```

**AI-Powered Detection**:
- `_is_webapp_request()` (238-327): Uses Claude to detect webapp build requests
- `_classify_message()` (329-439): Classifies user intent (refinement/status/cancel/new task)

### 3. Session Manager (`agents/session.py`)

**Key Methods**:

**`get_session()`** (27-47):
```python
def get_session(phone_number: str) -> Dict:
    if phone_number not in self.sessions:
        # Create new session
        self.sessions[phone_number] = {
            "phone_number": phone_number,
            "conversation_history": [],
            "created_at": datetime.utcnow(),
            "last_active": datetime.utcnow()
        }
    else:
        # Update last active time
        self.sessions[phone_number]["last_active"] = datetime.utcnow()
    return self.sessions[phone_number]
```

**`add_message()`** (49-74):
```python
def add_message(phone_number: str, role: str, content: str):
    session = self.get_session(phone_number)

    session["conversation_history"].append({
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    })

    # Limit history to prevent token overflow (line 68)
    if len(session["conversation_history"]) > self.max_history:
        session["conversation_history"] = session["conversation_history"][-self.max_history:]
```

**`cleanup_expired_sessions()`** (92-112):
```python
def cleanup_expired_sessions():
    now = datetime.utcnow()
    expired = []

    for phone_number, session in self.sessions.items():
        time_diff = now - session["last_active"]
        if time_diff > timedelta(minutes=self.ttl_minutes):
            expired.append(phone_number)

    for phone_number in expired:
        del self.sessions[phone_number]

    return len(expired)
```

---

## Multi-Agent System

### Agent Architecture

**Agent IDs** (`orchestrator.py:58-65`):
```python
ORCHESTRATOR_ID = "orchestrator"
DESIGNER_ID = "designer_001"
FRONTEND_ID = "frontend_001"
CODE_REVIEWER_ID = "code_reviewer_001"
QA_ID = "qa_engineer_001"
DEVOPS_ID = "devops_001"
```

### Lazy Agent Initialization

**Problem**: Creating all agents at startup wastes memory
**Solution**: Create agents on-demand, cleanup after use

**`_get_agent()`** (164-209):
```python
async def _get_agent(self, agent_type: str):
    # Check if already active
    if agent_type in self._active_agents:
        return self._active_agents[agent_type]

    # Check cache (if caching enabled)
    if self.enable_agent_caching and agent_type in self._agent_cache:
        return self._agent_cache[agent_type]

    # Create new agent
    print(f"🚀 Spinning up {agent_type} agent...")

    if agent_type == "designer":
        agent = DesignerAgent(self.mcp_servers)
    elif agent_type == "frontend":
        agent = FrontendDeveloperAgent(self.mcp_servers)
    # ... etc

    self._active_agents[agent_type] = agent
    return agent
```

**`_cleanup_agent()`** (211-238):
```python
async def _cleanup_agent(self, agent_type: str):
    if agent_type not in self._active_agents:
        return

    agent = self._active_agents[agent_type]

    # If caching enabled, keep the agent
    if self.enable_agent_caching:
        print(f"💾 Keeping {agent_type} agent in cache")
        return

    # Clean up the agent
    await agent.cleanup()
    a2a_protocol.unregister_agent(agent.agent_card.agent_id)
    del self._active_agents[agent_type]
```

### Specialized Agents

#### 1. Designer Agent (`designer_agent.py` - 612 lines)

**Capabilities**:
- Design system creation
- Color palette selection (hex codes)
- Typography specification
- Component design
- Accessibility guidelines (WCAG 2.1)
- **Frontend code review** (compares code vs design spec)

**Key Methods**:
- `execute_task()`: Create comprehensive design specification
- `review_artifact()`: Review frontend code against design

#### 2. Frontend Developer Agent (`frontend_agent.py` - 872 lines)

**Capabilities**:
- React/Vue/Next.js development
- TypeScript implementation
- Production-ready code (NO placeholders, NO TODOs)
- GitHub-ready projects
- Build error fixing

**System Prompt Highlights**:
- Write COMPLETE, WORKING code
- Use TypeScript for type safety
- Implement React performance optimization (React.memo, useCallback, useMemo)
- Add comprehensive error handling
- Include .gitignore, README.md, .env.example
- Follow SOLID principles and DRY
- Ensure WCAG 2.1 AA accessibility

#### 3. Code Reviewer Agent (`code_reviewer_agent.py` - 697 lines)

**Review Criteria** (10 comprehensive checks):

1. **Security Analysis** (CRITICAL)
   - OWASP Top 10 vulnerabilities
   - XSS, SQL injection, CSRF
   - API key exposure
   - Input validation

2. **Code Quality & Best Practices**
   - SOLID principles
   - DRY (Don't Repeat Yourself)
   - Meaningful names
   - Code organization

3. **React/JavaScript Specific**
   - Hooks usage (useCallback, useMemo)
   - Re-render optimization
   - Memory leak prevention
   - Dependency arrays

4. **Error Handling**
   - Try-catch blocks
   - Error boundaries
   - User-friendly error messages
   - Edge case handling

5. **Performance**
   - Code splitting
   - Lazy loading
   - Bundle size
   - Unnecessary re-renders

6. **Accessibility**
   - WCAG 2.1 compliance
   - ARIA labels
   - Keyboard navigation
   - Color contrast

7. **Documentation & Comments**
   - README completeness
   - Code comments
   - JSDoc for functions
   - API documentation

8. **Git/GitHub Best Practices**
   - .gitignore completeness
   - No secrets in code
   - Environment variables
   - README instructions

9. **Maintainability**
   - Code modularity
   - Component reusability
   - Clear structure
   - Scalability

10. **Dependencies & Build**
    - No unused dependencies
    - Version pinning
    - Build configuration
    - Production-ready

**Scoring**:
```
10/10: Perfect - production-ready, secure, performant
9/10:  Excellent - minor tweaks needed
8/10:  Good - a few improvements needed
7/10:  Acceptable - several issues to fix
6/10:  Below standard - significant issues
5/10:  Poor - major refactoring needed
1-4/10: Critical issues - security flaws, broken functionality
```

#### 4. QA Engineer Agent (`qa_agent.py` - 751 lines)

**Testing Criteria**:

1. **Functional Testing**
   - All features work as intended
   - User flows complete successfully
   - State management correct

2. **Usability & UX**
   - Intuitive navigation
   - Clear feedback
   - Loading states
   - Error messages

3. **Accessibility Testing**
   - WCAG 2.1 compliance
   - Screen reader support
   - Keyboard navigation
   - Color contrast (4.5:1 minimum)

4. **Responsive Design**
   - Mobile (320px+)
   - Tablet (768px+)
   - Desktop (1024px+)
   - No horizontal scroll

5. **Performance Testing**
   - Core Web Vitals
   - LCP < 2.5s
   - FCP < 1.8s
   - CLS < 0.1

6. **Cross-Browser Testing**
   - Chrome
   - Firefox
   - Safari
   - Edge

7. **Edge Cases**
   - Empty states
   - Error states
   - Long text
   - Special characters

8. **Security Testing (Basic)**
   - XSS prevention
   - Input sanitization
   - HTTPS usage

9. **Code Quality Verification**
   - No console errors
   - No warnings
   - Clean code

10. **Production Readiness**
    - Build succeeds
    - No broken links
    - All assets load

#### 5. DevOps Engineer Agent (`devops_agent.py` - 1,272 lines)

**Capabilities**:
- Netlify deployment
- **Build error detection** (critical)
- **netlify.toml generation**
- Post-deployment verification
- Performance optimization

**Critical netlify.toml Template**:
```toml
[build]
  command = "npm run build"
  publish = "dist"

[build.environment]
  NODE_VERSION = "18"
  # CRITICAL: Include devDependencies for build tools
  NPM_FLAGS = "--include=dev"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

**Why Critical**: Most Netlify build failures happen because `devDependencies` (like Vite, @vitejs/plugin-react) aren't installed by default. The `NPM_FLAGS = "--include=dev"` solves this.

**Build Error Detection Flow**:
1. Check Netlify build logs
2. Look for errors:
   - "Cannot find module X" → Missing dependency
   - "devDependencies not installed" → netlify.toml issue
   - Import errors → Wrong paths
   - TypeScript errors → Type mismatches
3. If errors found:
   - Analyze error messages
   - Provide specific fixes to Frontend agent
   - Request code updates
   - Redeploy and verify
4. Return success only if:
   - Build succeeds
   - Site is accessible
   - Page loads without errors

---

## API Reference

### REST Endpoints

#### Health Check

```http
GET /
```

**Response** (200 OK):
```json
{
  "service": "whatsapp-mcp",
  "status": "running",
  "version": "1.0.0"
}
```

#### Detailed Health Check

```http
GET /health
```

**Response** (200 OK):
```json
{
  "status": "healthy",
  "service": "whatsapp-mcp",
  "api_key_configured": true,
  "whatsapp_configured": true,
  "github_mcp_enabled": true,
  "github_token_configured": true,
  "netlify_mcp_enabled": true,
  "netlify_token_configured": true,
  "active_agents": 3,
  "available_mcp_servers": ["whatsapp", "github", "netlify"]
}
```

**Location**: `main.py:113-127`

#### Webhook Verification

```http
GET /webhook?hub.mode=subscribe&hub.verify_token=TOKEN&hub.challenge=CHALLENGE
```

**Response** (200 OK): `CHALLENGE` (plain text)

**Response** (403 Forbidden): `"Forbidden"` (if token doesn't match)

**Location**: `main.py:130-144`

#### Webhook Receiver

```http
POST /webhook
Content-Type: application/json

{
  "object": "whatsapp_business_account",
  "entry": [{
    "changes": [{
      "value": {
        "messages": [{
          "from": "1234567890",
          "type": "text",
          "text": {
            "body": "Hello!"
          }
        }]
      }
    }]
  }]
}
```

**Response** (200 OK):
```json
{
  "status": "ok"
}
```

**Location**: `main.py:147-191`

**Important**: Returns 200 OK immediately (<5s) and processes message asynchronously (line 183)

#### Process Message (Testing)

```http
POST /agent/process
Content-Type: application/json

{
  "phone_number": "+1234567890",
  "message": "Build me a todo app"
}
```

**Response** (200 OK):
```json
{
  "response": "🚀 Request received! Multi-agent team is processing...",
  "status": "success"
}
```

**Location**: `main.py:266-294`

#### Reset Session

```http
POST /agent/reset/+1234567890
```

**Response** (200 OK):
```json
{
  "status": "success",
  "message": "Session reset for +1234567890"
}
```

**Location**: `main.py:297-313`

---

## Workflow Types

### 1. Full Build Workflow

**Trigger**: "Build me a [webapp description]"

**Steps**:
1. **Design Phase** - Designer creates comprehensive design spec
2. **Implementation Phase** - Frontend implements React/Next.js code
3. **Quality Loop** - Designer reviews code vs design (iterative until score ≥ 9/10)
4. **Deployment Phase** - DevOps deploys to Netlify with build verification
5. **Response** - User receives deployment URL

**Example**:
```
User: "Build me a todo app with React and Tailwind"

📱 "🚀 Request received! Multi-agent team processing..."
📱 "🧠 AI Planning Complete - Workflow: full_build"
📱 "🤖 Orchestrator → UI/UX Designer"
📱 "✅ Task Done by: UI/UX Designer"
📱 "🤖 Orchestrator → Frontend Developer"
📱 "✅ Task Done by: Frontend Developer"
📱 "🔍 Orchestrator → UI/UX Designer (Review)"
📱 "✅ Review Done - Score: 8/10 - ⚠️ Needs improvement"
📱 "🤖 Orchestrator → Frontend Developer (Improvements)"
📱 "✅ Task Done by: Frontend Developer"
📱 "🔍 Orchestrator → UI/UX Designer (Review)"
📱 "✅ Review Done - Score: 9/10 - ✅ Approved"
📱 "🚀 Deploying to Netlify..."
📱 "✅ Your webapp is ready! 🔗 https://your-app.netlify.app"
```

### 2. Bug Fix Workflow

**Trigger**: "Fix the [error description]", "The build is failing"

**Steps**:
1. **Analysis** - Frontend analyzes error
2. **Fix** - Frontend applies fixes
3. **Deploy** - DevOps redeploys with build verification

### 3. Redeploy Workflow

**Trigger**: "Redeploy the app", "Deploy to Netlify"

**Steps**:
1. **Deploy** - Direct deployment to Netlify

### 4. Design Only Workflow

**Trigger**: "Create a design for [description]"

**Steps**:
1. **Design** - Designer creates design specification
2. **Response** - User receives design spec

### 5. Custom Workflow

**Trigger**: Any request not matching above patterns

**Steps**: AI-powered workflow planning determines specific steps

---

## Message Handling

### Smart Message Classification

When a user sends a message while a multi-agent task is active, the system intelligently classifies it:

**Classification Types**:

1. **refinement** - User wants to modify current task
2. **status_query** - User asking about progress
3. **cancellation** - User wants to stop
4. **new_task** - User wants a different task
5. **conversation** - General chat

**AI Classification** (`manager.py:329-439`):

Uses Claude to classify user intent based on:
- Current active task
- Current phase (design/implementation/review/deployment)
- User's message content

**Examples**:
- "Make it blue" → refinement
- "Add a login feature" → refinement
- "How's it going?" → status_query
- "Cancel" → cancellation
- "Build a different app" → new_task

### Refinement Handling

**Phase-Specific Refinement**:

**During Design Phase**:
```
User: "Build a todo app"
# Designer is creating design spec...

User: "Make it dark themed"
# System classifies as "refinement"
# Designer updates design spec with dark theme
# Continues with updated design
```

**During Implementation Phase**:
```
User: "Build a booking website"
# Frontend is coding...

User: "Add a calendar widget"
# System classifies as "refinement"
# Frontend adds calendar widget to code
# Continues with updated implementation
```

---

## Deployment

### Render Deployment (Recommended)

**Prerequisites**:
- GitHub account
- Render account
- Environment variables ready

**Step-by-Step**:

1. **Prepare Repository**
```bash
git add .
git commit -m "Deploy to Render"
git push origin main
```

2. **Create Render Service**
- Go to https://render.com
- Click "New" → "Blueprint"
- Connect GitHub repo
- Render detects `render.yaml`

3. **Set Environment Variables**

In Render dashboard, add:
```
ANTHROPIC_API_KEY=sk-ant-...
WHATSAPP_ACCESS_TOKEN=EAA...
WHATSAPP_PHONE_NUMBER_ID=123...
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_custom_token
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_...
NETLIFY_PERSONAL_ACCESS_TOKEN=nfp_...
ENABLE_GITHUB_MCP=true
ENABLE_NETLIFY_MCP=true
```

4. **Deploy**
- Click "Apply"
- Wait for build (~3-5 minutes)
- Get deployment URL: `https://your-app.onrender.com`

5. **Configure WhatsApp**
- Go to Meta Business Suite
- WhatsApp → Configuration
- Webhook URL: `https://your-app.onrender.com/webhook`
- Verify token: (same as `WHATSAPP_WEBHOOK_VERIFY_TOKEN`)
- Subscribe to: `messages`

6. **Test**
```bash
# Test health endpoint
curl https://your-app.onrender.com/health

# Send WhatsApp message
Send "Hello!" to your WhatsApp Business number
```

---

## Troubleshooting

### Common Issues

#### 1. Webhook Not Receiving Messages

**Symptoms**:
- Send WhatsApp message but no response
- Logs show no incoming webhooks

**Solutions**:

**Check 1: Webhook URL**
```bash
curl https://your-app.onrender.com/health
# Expected: {"status": "healthy", ...}
```

**Check 2: WhatsApp Configuration**
```
Meta Business Suite → WhatsApp → Configuration
- Webhook URL: https://your-app.onrender.com/webhook ✓
- Verify token: Matches WHATSAPP_WEBHOOK_VERIFY_TOKEN ✓
- Subscriptions: messages ✓
```

**Check 3: Webhook Verification**
```bash
curl "https://your-app.onrender.com/webhook?hub.mode=subscribe&hub.verify_token=YOUR_TOKEN&hub.challenge=TEST"
# Expected: "TEST"
```

#### 2. Multi-Agent Not Triggering

**Symptoms**:
- Send "Build me a todo app" but single-agent responds

**Solutions**:

**Check 1: Netlify MCP Enabled**
```bash
curl https://your-app.onrender.com/health

# Response should include:
{
  "netlify_mcp_enabled": true,  # Must be true
  "netlify_token_configured": true
}
```

**Check 2: Environment Variables**
```
ENABLE_NETLIFY_MCP=true
NETLIFY_PERSONAL_ACCESS_TOKEN=nfp_...
```

#### 3. Build Failures on Netlify

**Symptoms**:
- Deployment succeeds but build fails
- "Cannot find module" errors

**Solutions**:

**Check 1: netlify.toml exists**
```toml
[build]
  command = "npm run build"
  publish = "dist"

[build.environment]
  NODE_VERSION = "18"
  NPM_FLAGS = "--include=dev"  # CRITICAL
```

#### 4. Session Not Persisting

**Symptoms**:
- Agent forgets previous messages
- Conversation resets

**Solutions**:

**Check 1: Session TTL**
```python
# Default: 60 minutes
# Check agents/manager.py:37
session_manager = SessionManager(ttl_minutes=60, max_history=10)
```

**Note**: Sessions are in-memory and will be lost on restart

---

## Performance & Optimization

### Current Performance Characteristics

**Latency**:
- Webhook response: <100ms (returns immediately)
- Single-agent response: 2-5 seconds
- Multi-agent webapp build: 2-10 minutes (depends on complexity)

**Memory Usage**:
- Base: ~200MB
- Per single agent: ~50MB
- Per orchestrator (with agents): ~300-500MB

**Throughput**:
- Max concurrent users: ~20-30 (single instance, in-memory sessions)
- Max concurrent orchestrators: 3-5 (memory limited)

### Optimization Recommendations

**High Priority**:
1. **Redis for sessions** - Enable horizontal scaling
2. **Database for orchestrator state** - Crash recovery
3. **AI classification caching** - 60% reduction in API calls
4. **Retry logic with backoff** - Improve reliability

**Medium Priority**:
5. **Parallel agent initialization** - 2-3x faster startup
6. **Smart context trimming** - 30% token reduction
7. **Circuit breaker** - Prevent cascading failures
8. **Enhanced metrics** - Better observability

**See full optimization guide in codebase analysis**

---

## Security

### Best Practices

**1. API Key Management**
- Never commit API keys to git
- Use environment variables only
- Rotate keys regularly
- Use separate keys for dev/prod

**2. Webhook Verification** (`main.py:130-144`)
```python
# Always verify webhook token
if token != os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN'):
    return PlainTextResponse("Forbidden", status_code=403)
```

**3. Input Validation**
- Sanitize user input
- Limit message length (WhatsApp max: 4096 chars)
- Validate phone numbers

**4. HTTPS Only**
- Always use HTTPS in production
- Configure in deployment platform

**5. Rate Limiting**
- Implement per-user rate limits
- Protect against abuse

---

## Testing

### Running Tests

```bash
# Install pytest
pip install pytest pytest-asyncio

# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage
pip install pytest-cov
pytest tests/ --cov=src/python --cov-report=html
```

### Manual Testing

**Test Single Agent**:
```bash
curl -X POST http://localhost:8000/agent/process \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "message": "What is Python?"
  }'
```

**Test Multi-Agent**:
```bash
curl -X POST http://localhost:8000/agent/process \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "message": "Build me a todo app with React"
  }'
```

---

## Appendix

### File Locations Reference

| Component | File Path | Lines | Key Sections |
|-----------|-----------|-------|--------------|
| **Entry Point** | `src/python/main.py` | 353 | 340-353 (startup) |
| **Webhook Handler** | `src/python/main.py` | 353 | 147-191 |
| **Agent Manager** | `src/python/agents/manager.py` | 481 | 127-236 (routing) |
| **Session Manager** | `src/python/agents/session.py` | 129 | 27-112 |
| **Orchestrator** | `src/python/agents/collaborative/orchestrator.py` | 2,015 | 164-244 (lifecycle) |
| **Designer Agent** | `src/python/agents/collaborative/designer_agent.py` | 612 | Full file |
| **Frontend Agent** | `src/python/agents/collaborative/frontend_agent.py` | 872 | Full file |
| **Code Reviewer** | `src/python/agents/collaborative/code_reviewer_agent.py` | 697 | Full file |
| **QA Agent** | `src/python/agents/collaborative/qa_agent.py` | 751 | Full file |
| **DevOps Agent** | `src/python/agents/collaborative/devops_agent.py` | 1,272 | Full file |
| **A2A Protocol** | `src/python/agents/collaborative/a2a_protocol.py` | 157 | Full file |
| **Models** | `src/python/agents/collaborative/models.py` | 127 | Full file |
| **Claude SDK** | `src/python/sdk/claude_sdk.py` | 294 | 185-230 (send) |
| **WhatsApp Client** | `src/python/whatsapp_mcp/client.py` | 191 | 51-114 (send) |
| **WhatsApp Parser** | `src/python/whatsapp_mcp/parser.py` | 150 | Full file |
| **GitHub MCP** | `src/python/github_mcp/server.py` | 113 | Full file |
| **Netlify MCP** | `src/python/netlify_mcp/server.py` | 123 | Full file |
| **Telemetry** | `src/python/utils/telemetry.py` | 446 | Full file |

### Data Model Reference

**Session**:
```python
{
    "phone_number": str,
    "conversation_history": [
        {"role": "user" | "assistant", "content": str, "timestamp": str}
    ],
    "created_at": datetime,
    "last_active": datetime
}
```

**AgentCard**:
```python
{
    "agent_id": str,
    "name": str,
    "role": AgentRole,
    "description": str,
    "capabilities": List[str],
    "skills": Dict[str, List[str]]
}
```

**Task**:
```python
{
    "task_id": str,
    "description": str,
    "from_agent": str,
    "to_agent": str,
    "priority": "low" | "medium" | "high",
    "status": TaskStatus,
    "metadata": Optional[Dict]
}
```

---

## Support & Contributing

### Getting Help

**Issues**: Open an issue in the GitHub repository
**Questions**: Check existing documentation first

### Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Make changes
4. Run tests: `pytest tests/`
5. Commit: `git commit -m "Add my feature"`
6. Push: `git push origin feature/my-feature`
7. Create Pull Request

---

**Last Updated:** October 24, 2025
**Version:** 2.1.0
**Documentation Status:** ✅ Current (matches codebase)
