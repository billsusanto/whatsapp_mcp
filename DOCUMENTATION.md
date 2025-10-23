# WhatsApp Multi-Agent System - Complete Documentation

**Version:** 2.0.0
**Last Updated:** October 22, 2025
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
13. [Development Guide](#development-guide)
14. [Security](#security)
15. [Performance](#performance)
16. [Testing](#testing)

---

## Overview

### What is This?

A production-ready WhatsApp-integrated AI assistant system that uses Claude AI and a multi-agent architecture to build complete, deployable web applications through WhatsApp chat.

### Key Features

**Single-Agent Mode:**
- Personal AI assistant for individual conversations
- Context-aware responses with session management
- 60-minute conversation memory

**Multi-Agent Mode:**
- Collaborative team of specialized AI agents
- Builds production-ready webapps from natural language
- Real-time WhatsApp notifications on progress
- Intelligent refinement handling during development
- Automatic build verification and error fixing

**Integrations:**
- WhatsApp Business Cloud API
- Claude AI (Sonnet 4.5)
- Model Context Protocol (MCP)
- GitHub (repository management)
- Netlify (automated deployment)

### Use Cases

1. **Personal Assistant** - Ask questions, get technical guidance
2. **Webapp Builder** - "Build me a todo app with React"
3. **Code Review** - Get AI-powered code reviews with security analysis
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
└─────────────────────────────────────────────────────────────────┘
                              ↓ (webhook POST)
┌─────────────────────────────────────────────────────────────────┐
│                FastAPI Application (main.py)                    │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │               WhatsAppWebhookParser                       │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ↓ (async task)
┌─────────────────────────────────────────────────────────────────┐
│                      AgentManager                               │
│  ┌─────────────────────────────────────────────────────┐       │
│  │       AI Message Classifier                         │       │
│  │  ┌───────────────┬────────────────┬──────────────┐ │       │
│  │  │ webapp_request│  refinement    │ conversation │ │       │
│  │  └───────────────┴────────────────┴──────────────┘ │       │
│  └─────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
         ↓                              ↓                  ↓
┌──────────────────┐      ┌─────────────────────────┐    ┌──────────┐
│  Single Agent    │      │ Multi-Agent Orchestrator│    │  Single  │
│                  │      │  ┌────────────────────┐ │    │  Agent   │
│  ClaudeSDK       │      │  │  AI Workflow       │ │    │          │
│  + MCP Tools     │      │  │  Planner           │ │    │          │
│                  │      │  └────────────────────┘ │    │          │
└──────────────────┘      │         ↓               │    └──────────┘
                          │  ┌────────────────────┐ │
                          │  │ Specialized Agents │ │
                          │  │  • Designer        │ │
                          │  │  • Frontend Dev    │ │
                          │  │  • Code Reviewer   │ │
                          │  │  • QA Engineer     │ │
                          │  │  • DevOps          │ │
                          │  └────────────────────┘ │
                          │         ↓               │
                          │  A2A Protocol           │
                          │  (Agent-to-Agent)       │
                          └─────────────────────────┘
                                     ↓
                          ┌─────────────────────────┐
                          │   Claude AI API         │
                          │   (Sonnet 4.5)          │
                          └─────────────────────────┘
                                     ↓
                          ┌─────────────────────────┐
                          │   MCP Servers           │
                          │   • GitHub              │
                          │   • Netlify             │
                          │   • WhatsApp            │
                          └─────────────────────────┘
```

### System Components

#### 1. **FastAPI Application** (`main.py`)
- Webhook endpoint for WhatsApp messages
- Health check endpoints
- Background cleanup tasks
- Async message processing

#### 2. **Agent Manager** (`agents/manager.py`)
- Routes messages to appropriate agents
- Per-user orchestrator management
- AI-powered intent classification
- Smart refinement handling

#### 3. **Session Manager** (`agents/session.py`)
- 60-minute conversation TTL
- 10-message history limit
- Auto-cleanup of expired sessions
- Per-user context tracking

#### 4. **Multi-Agent Orchestrator** (`agents/collaborative/orchestrator.py`)
- Coordinates 5 specialized agents
- AI-powered workflow planning
- Real-time WhatsApp notifications
- Build retry with error detection
- Quality loops (iterative improvement)

#### 5. **Specialized Agents**

**Designer Agent:**
- Creates design specifications
- Reviews frontend code vs design
- Ensures design fidelity

**Frontend Developer Agent:**
- Writes React/Next.js/Vue code
- Production-ready implementations
- Fixes build errors
- GitHub-ready projects

**Code Reviewer Agent:**
- Security analysis (OWASP Top 10)
- Performance review
- Best practices validation
- Scores code quality (1-10)

**QA Engineer Agent:**
- Functional testing
- Accessibility testing (WCAG 2.1)
- Cross-browser validation
- Performance testing

**DevOps Engineer Agent:**
- Netlify deployment
- Build error detection
- netlify.toml generation
- Post-deployment verification

#### 6. **A2A Protocol** (`agents/collaborative/a2a_protocol.py`)
- Standardized agent communication
- Task requests/responses
- Review requests/responses
- Agent discovery

#### 7. **MCP Integration**
- WhatsApp MCP: Send messages
- GitHub MCP: Repository management
- Netlify MCP: Deployment automation

---

## Quick Start

### Prerequisites

- Python 3.12+
- WhatsApp Business Account
- Anthropic API key
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

Expected response: AI assistant greeting

Try multi-agent mode:

```
Build me a todo app with React and Tailwind
```

Expected: Multi-agent team starts building, sends real-time updates

---

## Installation & Setup

### Local Development Setup

#### Step 1: Environment Setup

```bash
# Create .env file
cat > .env << 'EOF'
# Claude AI
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# WhatsApp Business API
WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_custom_verify_token
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id

# GitHub MCP (Optional)
GITHUB_PERSONAL_ACCESS_TOKEN=your_github_token
ENABLE_GITHUB_MCP=true

# Netlify MCP (Optional)
NETLIFY_PERSONAL_ACCESS_TOKEN=your_netlify_token
ENABLE_NETLIFY_MCP=true

# Agent Configuration
AGENT_SYSTEM_PROMPT="You are a helpful AI assistant."

# Service Configuration
PORT=8000
EOF
```

#### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

#### Step 3: Configure WhatsApp Webhook

1. Go to Meta Business Suite
2. Navigate to WhatsApp → Configuration
3. Set webhook URL: `http://localhost:8000/webhook` (use ngrok for local testing)
4. Set verify token: (same as `WHATSAPP_WEBHOOK_VERIFY_TOKEN`)
5. Subscribe to `messages` events

#### Step 4: Test Locally

```bash
# Start server
python src/python/main.py

# In another terminal, test health endpoint
curl http://localhost:8000/health

# Send test message via API
curl -X POST http://localhost:8000/agent/process \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1234567890", "message": "Hello!"}'
```

### Production Deployment (Render)

#### Step 1: Prepare Repository

```bash
# Ensure render.yaml exists
git add render.yaml Dockerfile.render requirements.txt
git commit -m "Prepare for Render deployment"
git push origin main
```

#### Step 2: Deploy to Render

1. Go to [render.com](https://render.com)
2. Click "New" → "Blueprint"
3. Connect your GitHub repository
4. Render will detect `render.yaml`
5. Set environment variables in dashboard:
   - `ANTHROPIC_API_KEY`
   - `WHATSAPP_ACCESS_TOKEN`
   - `WHATSAPP_PHONE_NUMBER_ID`
   - `WHATSAPP_WEBHOOK_VERIFY_TOKEN`
   - `GITHUB_PERSONAL_ACCESS_TOKEN` (optional)
   - `NETLIFY_PERSONAL_ACCESS_TOKEN` (optional)
6. Click "Apply"

#### Step 3: Configure WhatsApp Webhook

1. Get your Render URL: `https://your-app.onrender.com`
2. Update WhatsApp webhook URL: `https://your-app.onrender.com/webhook`
3. Verify webhook in Meta dashboard

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
| `ENABLE_NETLIFY_MCP` | ❌ Optional | `false` | Enable Netlify deployment |
| `AGENT_SYSTEM_PROMPT` | ❌ Optional | Default prompt | Custom system prompt for single-agent mode |
| `PORT` | ❌ Optional | `8000` | Server port |

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
model = "claude-sonnet-4-5-20250929"
max_tokens = 4096
```

**Orchestrator** (`agents/collaborative/orchestrator.py:122-125`):
```python
max_review_iterations = 10    # Maximum quality improvement iterations
min_quality_score = 9         # Minimum acceptable score (out of 10)
max_build_retries = 5         # Maximum deployment retry attempts
enable_agent_caching = False  # Agent reuse (set True for speed, uses more memory)
```

### WhatsApp API Configuration

**API Version:** v18.0
**Base URL:** `https://graph.facebook.com/v18.0/{phone_number_id}`

**Supported Message Types:**
- Text messages
- Image messages
- Video messages
- Audio messages
- Document messages

---

## Core Components

### 1. Main Application (`main.py`)

**Entry Point:** Line 281-294

```python
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")
```

**Key Endpoints:**

| Endpoint | Method | Handler | Purpose |
|----------|--------|---------|---------|
| `/` | GET | `root()` | Health check (line 76) |
| `/health` | GET | `health_check()` | Detailed status (line 86) |
| `/webhook` | GET | `webhook_verify()` | WhatsApp verification (line 103) |
| `/webhook` | POST | `webhook_receive()` | Incoming messages (line 120) |
| `/agent/process` | POST | `process_message()` | Direct messaging (line 207) |
| `/agent/reset/{phone}` | POST | `reset_session()` | Clear history (line 238) |

**Critical Flow:**

```python
# Line 120: Webhook receives message
@app.post("/webhook")
async def webhook_receive(request: Request):
    body = await request.json()
    message_data = WhatsAppWebhookParser.parse_message(body)

    # Line 148: Spawn async task (don't block webhook response)
    asyncio.create_task(process_whatsapp_message(from_number, message_text))

    # Line 151: Return 200 OK immediately (WhatsApp requires <5s response)
    return {"status": "ok"}
```

### 2. Agent Manager (`agents/manager.py`)

**Purpose:** Routes messages to single-agent or multi-agent systems

**Key Methods:**

**`__init__()`** (Line 27-105):
```python
def __init__(self, whatsapp_mcp_tools, enable_github, enable_netlify):
    # Initialize MCP servers
    self.available_mcp_servers = {}

    # WhatsApp MCP
    if whatsapp_mcp_tools:
        self.available_mcp_servers["whatsapp"] = whatsapp_mcp_tools

    # GitHub MCP (optional)
    if enable_github:
        github_config = create_github_mcp_config()
        self.available_mcp_servers["github"] = github_config

    # Netlify MCP (optional)
    if enable_netlify:
        netlify_config = create_netlify_mcp_config()
        self.available_mcp_servers["netlify"] = netlify_config

    # Per-user orchestrators
    self.orchestrators = {}
```

**`process_message()`** (Line 127-236) - Smart Message Routing:

```python
async def process_message(phone_number: str, message: str) -> str:
    # Check for active orchestrator
    active_orchestrator = self.orchestrators.get(phone_number)

    if active_orchestrator and active_orchestrator.is_active:
        # Classify incoming message
        message_type = await self._classify_message(
            message=message,
            active_task=active_orchestrator.original_prompt,
            current_phase=active_orchestrator.current_phase
        )

        # Route based on classification
        if message_type == "refinement":
            return await active_orchestrator.handle_refinement(message)
        elif message_type == "status_query":
            return await active_orchestrator.handle_status_query()
        elif message_type == "cancellation":
            return await active_orchestrator.handle_cancellation()
        elif message_type == "new_task":
            return "⚠️ Current task active. Send 'cancel' to stop."

    # Check if webapp request
    if await self._is_webapp_request(message):
        orchestrator = CollaborativeOrchestrator(
            mcp_servers=self.available_mcp_servers,
            user_phone_number=phone_number
        )
        self.orchestrators[phone_number] = orchestrator
        return await orchestrator.build_webapp(message)

    # Regular conversation
    agent = self.get_or_create_agent(phone_number)
    return await agent.process_message(message)
```

**`_classify_message()`** (Line 329-439) - AI-Powered Classification:

```python
async def _classify_message(message, active_task, current_phase):
    """
    Uses Claude to classify user intent:
    - refinement: Modify current task
    - status_query: Ask about progress
    - cancellation: Stop current task
    - new_task: Start different task
    - conversation: General chat
    """

    classification_prompt = f"""
    Context:
    - Currently working on: "{active_task}"
    - Current phase: {current_phase}

    New message: "{message}"

    Classify as: refinement | status_query | cancellation | new_task | conversation
    """

    # Use Claude to classify
    response = await self.claude_sdk.send_message(classification_prompt)

    # Extract classification from response
    # ... (with fallback to keyword matching)
```

### 3. Session Manager (`agents/session.py`)

**Purpose:** Track conversation history per user

**Key Methods:**

**`get_session()`** (Line 27-47):
```python
def get_session(phone_number: str):
    if phone_number not in sessions:
        sessions[phone_number] = {
            "phone_number": phone_number,
            "conversation_history": [],
            "created_at": datetime.now(),
            "last_active": datetime.now()
        }
    else:
        sessions[phone_number]["last_active"] = datetime.now()
    return sessions[phone_number]
```

**`add_message()`** (Line 49-74):
```python
def add_message(phone_number: str, role: str, content: str):
    session = get_session(phone_number)

    session["conversation_history"].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })

    # Trim to max_history (default: 10)
    if len(session["conversation_history"]) > self.max_history:
        session["conversation_history"] = session["conversation_history"][-self.max_history:]
```

**`cleanup_expired_sessions()`** (Line 92-112):
```python
def cleanup_expired_sessions():
    expired = []
    for phone_number, session in sessions.items():
        if (datetime.now() - session["last_active"]).seconds > (ttl_minutes * 60):
            expired.append(phone_number)

    for phone_number in expired:
        del sessions[phone_number]

    return len(expired)
```

---

## Multi-Agent System

### Overview

The multi-agent system coordinates 5 specialized AI agents to build production-ready webapps.

### Agent Types

#### 1. **Designer Agent** (`designer_agent.py`)

**Capabilities:**
- Design system creation
- Color palette selection
- Typography specification
- Component design
- Accessibility guidelines
- **Frontend code review** (compares code vs design spec)

**Key Methods:**

**`execute_task()`** (Line 63-181):
```python
async def execute_task(task: Task) -> Dict:
    """Create comprehensive design specification"""

    prompt = f"""Create a design specification for: {task.description}

    Include:
    1. Style (modern, minimal, bold, playful)
    2. Color palette (hex codes)
    3. Typography (font families, sizes, weights)
    4. Component designs
    5. Layout structure
    6. Design tokens (CSS custom properties)
    7. Accessibility requirements (WCAG 2.1 AA)

    Be SPECIFIC with exact values (e.g., #3B82F6, not "blue")
    """

    response = await self.claude_sdk.send_message(prompt)
    return {"design_spec": parse_design_spec(response)}
```

**`review_artifact()`** (Line 183-281):
```python
async def review_artifact(artifact: Dict) -> Dict:
    """Review frontend code against design specification"""

    design_spec = artifact["original_design"]
    implementation = artifact["implementation"]

    prompt = f"""Review this frontend implementation against the design spec.

    DESIGN SPECIFICATION:
    {design_spec}

    IMPLEMENTATION:
    {implementation}

    Check:
    1. Do hex color codes in code match design spec exactly?
    2. Are font families correctly imported and applied?
    3. Do spacing values (margins, padding) match design system?
    4. Are components implemented as specified?
    5. Is the code accessible (ARIA labels, semantic HTML)?

    Be CRITICAL - score 9-10 only for near-perfect implementations.
    Give specific file names and line numbers for issues.

    Respond with JSON:
    {
      "approved": true/false,
      "score": 1-10,
      "feedback": ["specific issue 1", "specific issue 2"],
      "critical_issues": ["blocking issue 1"],
      "suggestions": ["improvement 1"]
    }
    """

    review = await self.claude_sdk.send_message(prompt)
    return parse_review(review)
```

#### 2. **Frontend Developer Agent** (`frontend_agent.py`)

**Capabilities:**
- React/Vue/Next.js development
- TypeScript implementation
- Production-ready code
- GitHub-ready projects
- Build error fixing

**System Prompt Highlights** (Line 38-122):
```
- Write COMPLETE, WORKING code (NO placeholders, NO TODOs)
- Use TypeScript for type safety
- Implement React performance optimization (React.memo, useCallback, useMemo)
- Add comprehensive error handling
- Include .gitignore, README.md, .env.example
- Follow SOLID principles and DRY
- Ensure WCAG 2.1 AA accessibility
```

**`execute_task()`** generates complete project structure:
```
project/
├── src/
│   ├── components/
│   ├── hooks/
│   ├── utils/
│   ├── App.jsx
│   └── index.js
├── public/
├── package.json
├── .gitignore
├── README.md
├── .env.example
└── netlify.toml (if deploying)
```

#### 3. **Code Reviewer Agent** (`code_reviewer_agent.py`)

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

**Scoring** (Line 160-170):
```
10/10: Perfect - production-ready, secure, performant
9/10:  Excellent - minor tweaks needed
8/10:  Good - a few improvements needed
7/10:  Acceptable - several issues to fix
6/10:  Below standard - significant issues
5/10:  Poor - major refactoring needed
1-4/10: Critical issues - security flaws, broken functionality
```

#### 4. **QA Engineer Agent** (`qa_agent.py`)

**Testing Criteria:**

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

#### 5. **DevOps Engineer Agent** (`devops_agent.py`)

**Capabilities:**
- Netlify deployment
- **Build error detection**
- **netlify.toml generation**
- Post-deployment verification
- Performance optimization

**Critical netlify.toml Template** (Line 160-184):
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

**Why Critical:** Most Netlify build failures happen because `devDependencies` (like Vite, @vitejs/plugin-react) aren't installed by default. The `NPM_FLAGS = "--include=dev"` solves this.

**Build Error Detection** (Line 359-414):
```python
# After deployment, DevOps agent:
1. Checks Netlify build logs
2. Looks for errors:
   - "Cannot find module X" → Missing dependency
   - "devDependencies not installed" → netlify.toml issue
   - Import errors → Wrong paths
   - TypeScript errors → Type mismatches
3. If errors found:
   - Analyzes error messages
   - Provides specific fixes to Frontend agent
   - Requests code updates
   - Redeploys and verifies
4. Returns success only if:
   - Build succeeds
   - Site is accessible
   - Page loads without errors
```

### Orchestrator (`orchestrator.py`)

**Purpose:** Coordinates all agents, manages workflows

**Key Features:**

1. **Lazy Agent Initialization** (Line 155-200)
2. **Real-Time WhatsApp Notifications** (Line 241-270)
3. **AI-Powered Workflow Planning** (Line 740-872)
4. **Smart Refinement Handling** (Line 312-451)
5. **Quality Loops** (Line 1022-1077)
6. **Build Retry Logic** (Line 1559-1633)

**State Management** (Line 127-140):
```python
self.is_active = False              # Currently processing?
self.current_phase = None            # design | implementation | review | deployment
self.current_workflow = None         # full_build | bug_fix | etc.
self.original_prompt = None          # User's request
self.accumulated_refinements = []    # All refinements
self.current_implementation = None   # Current code
self.current_design_spec = None      # Current design
```

**Agent IDs** (Line 49-56):
```python
ORCHESTRATOR_ID = "orchestrator"
DESIGNER_ID = "designer_001"
FRONTEND_ID = "frontend_001"
CODE_REVIEWER_ID = "code_reviewer_001"
QA_ID = "qa_engineer_001"
DEVOPS_ID = "devops_001"
```

### A2A Protocol (`a2a_protocol.py`)

**Purpose:** Standardized agent-to-agent communication

**Key Methods:**

**`register_agent()`** (Line 27-30):
```python
def register_agent(agent):
    agents[agent.agent_card.agent_id] = agent
```

**`send_task()`** (Line 84-112):
```python
async def send_task(from_agent_id, to_agent_id, task):
    # Find target agent
    target_agent = agents.get(to_agent_id)

    # Create A2A message
    message = A2AMessage(
        from_agent=from_agent_id,
        to_agent=to_agent_id,
        message_type=MessageType.TASK_REQUEST,
        content=task.dict()
    )

    # Send to agent
    response = await target_agent.receive_message(message)

    return TaskResponse(**response)
```

**`request_review()`** (Line 114-140):
```python
async def request_review(from_agent_id, to_agent_id, artifact):
    target_agent = agents.get(to_agent_id)

    message = A2AMessage(
        from_agent=from_agent_id,
        to_agent=to_agent_id,
        message_type=MessageType.REVIEW_REQUEST,
        content={"artifact": artifact}
    )

    review = await target_agent.receive_message(message)
    return review
```

---

## API Reference

### REST Endpoints

#### Health Check

```http
GET /
```

**Response:**
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

**Response:**
```json
{
  "status": "healthy",
  "service": "whatsapp-mcp",
  "api_key_configured": true,
  "whatsapp_configured": true,
  "github_mcp_enabled": true,
  "netlify_mcp_enabled": true,
  "active_agents": 3,
  "available_mcp_servers": ["whatsapp", "github", "netlify"]
}
```

#### Webhook Verification

```http
GET /webhook?hub.mode=subscribe&hub.verify_token=TOKEN&hub.challenge=CHALLENGE
```

**Response:** `CHALLENGE` (plain text)

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

**Response:**
```json
{
  "status": "ok"
}
```

#### Process Message (Testing)

```http
POST /agent/process
Content-Type: application/json

{
  "phone_number": "+1234567890",
  "message": "Build me a todo app"
}
```

**Response:**
```json
{
  "response": "🚀 Request received! Multi-agent team is processing...",
  "status": "success"
}
```

#### Reset Session

```http
POST /agent/reset/+1234567890
```

**Response:**
```json
{
  "status": "success",
  "message": "Session reset for +1234567890"
}
```

---

## Workflow Types

### 1. Full Build Workflow

**Trigger:** "Build me a [webapp description]"

**Steps:**
1. **Design Phase** - Designer creates comprehensive design spec
2. **Implementation Phase** - Frontend implements React/Next.js code
3. **Quality Loop** - Designer reviews code vs design (iterative until score ≥ 9/10)
4. **Deployment Phase** - DevOps deploys to Netlify with build verification
5. **Response** - User receives deployment URL

**Example:**
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

**Quality Loop** (`orchestrator.py:1022-1077`):
```python
while review_iteration < max_review_iterations:
    review = await request_review_from_agent(DESIGNER_ID, implementation)
    score = review['score']

    if score >= min_quality_score:  # 9/10
        break

    # Request improvements
    improved = await send_task_to_agent(
        FRONTEND_ID,
        f"Improve based on feedback: {review['feedback']}"
    )
    implementation = improved
```

### 2. Bug Fix Workflow

**Trigger:** "Fix the [error description]", "The build is failing"

**Steps:**
1. **Analysis** - Frontend analyzes error
2. **Fix** - Frontend applies fixes
3. **Deploy** - DevOps redeploys with build verification

**Example:**
```
User: "Fix the build errors"

📱 "🚀 Request received!"
📱 "🧠 AI Planning - Workflow: bug_fix"
📱 "🤖 Orchestrator → Frontend Developer"
📱 "✅ Build errors fixed"
📱 "🚀 Redeploying..."
📱 "✅ Bug fix complete! 🔗 https://your-app.netlify.app"
```

### 3. Redeploy Workflow

**Trigger:** "Redeploy the app", "Deploy to Netlify"

**Steps:**
1. **Deploy** - Direct deployment to Netlify

**Example:**
```
User: "Redeploy the app"

📱 "🚀 Redeploying to Netlify..."
📱 "✅ Site redeployed! 🔗 https://your-app.netlify.app"
```

### 4. Design Only Workflow

**Trigger:** "Create a design for [description]"

**Steps:**
1. **Design** - Designer creates design specification
2. **Response** - User receives design spec

**Example:**
```
User: "Create a design for a booking website"

📱 "🎨 UI/UX Designer creating design..."
📱 "✅ Design complete! Includes: color palette, typography, components, layout"
```

### 5. Custom Workflow

**Trigger:** Any request not matching above patterns

**Steps:** AI-powered workflow planning determines specific steps

**Example:**
```
User: "Review this code and deploy it"

📱 "🧠 AI Planning - Workflow: custom"
📱 "🤖 Orchestrator → Code Reviewer"
📱 "✅ Code review complete - Score: 8/10"
📱 "🤖 Orchestrator → DevOps Engineer"
📱 "✅ Deployed! 🔗 https://your-app.netlify.app"
```

---

## Message Handling

### Smart Message Classification

When a user sends a message while a multi-agent task is active, the system intelligently classifies it:

**Classification Types:**

1. **Refinement** - User wants to modify current task
2. **Status Query** - User asking about progress
3. **Cancellation** - User wants to stop
4. **New Task** - User wants a different task
5. **Conversation** - General chat

**AI Classification** (`manager.py:329-439`):

```python
async def _classify_message(message, active_task, current_phase):
    prompt = f"""
    Context:
    - Currently working on: "{active_task}"
    - Current phase: {current_phase}

    New message: "{message}"

    Classify this message:
    - "refinement" if user wants to modify/refine current task
    - "status_query" if asking about progress
    - "cancellation" if wants to stop/cancel
    - "new_task" if requesting completely different task
    - "conversation" if general chat

    Examples:
    - "Make it blue" → refinement
    - "Add a login feature" → refinement
    - "How's it going?" → status_query
    - "Cancel" → cancellation
    - "Build a different app" → new_task
    """

    response = await claude.send_message(prompt)
    return extract_classification(response)
```

### Refinement Handling

**Phase-Specific Refinement** (`orchestrator.py:312-451`):

**During Design Phase:**
```python
User: "Build a todo app"
# Designer is creating design spec...

User: "Make it dark themed"

# System:
→ Classifies as "refinement"
→ Routes to handle_refinement()
→ Calls _refine_during_design()
→ Designer updates design spec with dark theme
→ Continues with updated design
```

**During Implementation Phase:**
```python
User: "Build a booking website"
# Frontend is coding...

User: "Add a calendar widget"

# System:
→ Classifies as "refinement"
→ Routes to handle_refinement()
→ Calls _refine_during_implementation()
→ Frontend adds calendar widget to code
→ Continues with updated implementation
```

**During Review Phase:**
```python
User: "Build a dashboard"
# Designer is reviewing code...

User: "Change the header color to blue"

# System:
→ Classifies as "refinement"
→ Notes refinement for next iteration
→ Will be applied when Frontend improves code
```

### Status Queries

**Detailed Status Response** (`orchestrator.py:453-527`):

```
User: "How's it going?"

Response:
📊 DETAILED TASK STATUS
========================================

🎯 Your Request:
   Build a todo app with React and Tailwind

🔧 Workflow Details:
   • Type: full_build
   • Phase: 💻 implementation
   • Progress: [████████████░░░░░░░░] 60% (3/5 steps)

🤖 Currently Active Agent:
   👉 Frontend Developer
   📋 Task: Implement webapp using React, Tailwind...
   ⏳ Status: Working...

💼 Agents Currently Deployed:
   • UI/UX Designer
   • Frontend Developer

✅ Completed Steps:
   ✓ UI/UX Designer: Create design specification
   ✓ Frontend Developer: Implement webapp
   ✓ UI/UX Designer: Review completed (Score: 8/10)

========================================
⏳ Your request is being actively processed!
💡 Send updates anytime - I'll incorporate them!
```

### Cancellation

```
User: "Cancel"

Response:
🛑 Task cancelled. The multi-agent team has stopped working on the previous request.
```

---

## Deployment

### Render Deployment (Recommended)

**Prerequisites:**
- GitHub account
- Render account
- Environment variables ready

**Step-by-Step:**

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

### Docker Deployment

**Build Image:**
```bash
docker build -f Dockerfile.render -t whatsapp-mcp .
```

**Run Container:**
```bash
docker run -d \
  -p 8000:8000 \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  -e WHATSAPP_ACCESS_TOKEN=EAA... \
  -e WHATSAPP_PHONE_NUMBER_ID=123... \
  -e WHATSAPP_WEBHOOK_VERIFY_TOKEN=token \
  -e GITHUB_PERSONAL_ACCESS_TOKEN=ghp_... \
  -e NETLIFY_PERSONAL_ACCESS_TOKEN=nfp_... \
  -e ENABLE_GITHUB_MCP=true \
  -e ENABLE_NETLIFY_MCP=true \
  --name whatsapp-mcp \
  whatsapp-mcp
```

**Check Logs:**
```bash
docker logs -f whatsapp-mcp
```

### Local Development with ngrok

**Setup ngrok:**
```bash
# Install ngrok
brew install ngrok  # macOS
# or download from https://ngrok.com

# Start server
python src/python/main.py

# In another terminal, start ngrok
ngrok http 8000
```

**Configure WhatsApp:**
- Copy ngrok URL: `https://abc123.ngrok.io`
- Set WhatsApp webhook: `https://abc123.ngrok.io/webhook`
- Test by sending message

---

## Troubleshooting

### Common Issues

#### 1. Webhook Not Receiving Messages

**Symptoms:**
- Send WhatsApp message but no response
- Logs show no incoming webhooks

**Solutions:**

**Check 1: Webhook URL**
```bash
# Test health endpoint
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

**Check 3: Logs**
```bash
# Render dashboard → Logs
# Look for: "Received webhook: {...}"
```

**Check 4: Webhook Verification**
```bash
curl "https://your-app.onrender.com/webhook?hub.mode=subscribe&hub.verify_token=YOUR_TOKEN&hub.challenge=TEST"

# Expected: "TEST"
```

#### 2. Multi-Agent Not Triggering

**Symptoms:**
- Send "Build me a todo app" but single-agent responds

**Solutions:**

**Check 1: Netlify MCP Enabled**
```bash
# Check /health endpoint
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

**Check 3: Intent Detection**
```bash
# Try explicit request
Send: "Build me a webapp for managing todos"

# Should trigger multi-agent mode
```

#### 3. Build Failures on Netlify

**Symptoms:**
- Deployment succeeds but build fails
- "Cannot find module" errors

**Solutions:**

**Check 1: netlify.toml exists**
```toml
[build]
  command = "npm run build"
  publish = "dist"

[build.environment]
  NODE_VERSION = "18"
  NPM_FLAGS = "--include=dev"  # CRITICAL
```

**Check 2: DevOps Agent Review**
```
DevOps agent should:
1. Check build logs
2. Detect missing devDependencies
3. Generate netlify.toml with NPM_FLAGS
4. Redeploy
```

**Check 3: Manual Fix**
```bash
# If DevOps doesn't fix, manually add netlify.toml to repo
# Commit and push
git add netlify.toml
git commit -m "Add netlify config"
git push
```

#### 4. Session Not Persisting

**Symptoms:**
- Agent forgets previous messages
- Conversation resets

**Solutions:**

**Check 1: Session TTL**
```python
# Default: 60 minutes
# Check agents/manager.py:37
session_manager = SessionManager(ttl_minutes=60, max_history=10)
```

**Check 2: Cleanup Logs**
```bash
# Look for: "🧹 Running periodic cleanup..."
# Shows: "Expired sessions: X"
```

**Check 3: Max History**
```python
# Default: 10 messages
# Older messages are trimmed
# To increase: Change max_history in manager.py:37
```

#### 5. API Rate Limits

**Symptoms:**
- "Rate limit exceeded" errors
- Slow responses

**Solutions:**

**Check 1: Claude API Limits**
```
Claude Sonnet 4.5:
- 50 requests/minute (per API key)
- 40,000 tokens/minute
```

**Check 2: Implement Backoff**
```python
# In claude_sdk.py, add retry logic
async def send_message_with_retry(prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await send_message(prompt)
        except RateLimitError:
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
    raise
```

#### 6. Memory Issues (Render)

**Symptoms:**
- Service crashes
- "Out of memory" errors

**Solutions:**

**Check 1: Render Plan**
```
Starter (512MB): Not enough for multi-agent
Standard (2GB): Recommended for multi-agent
Pro (4GB+): For high traffic
```

**Check 2: Agent Caching**
```python
# In orchestrator.py:125
enable_agent_caching = False  # Saves memory

# If set to True, agents stay in memory
# More memory but faster for repeat builds
```

**Check 3: Cleanup**
```python
# Ensure agents are cleaned up after use
# orchestrator.py:1115-1119
finally:
    await self._cleanup_all_active_agents()
```

### Debugging Tips

**Enable Verbose Logging:**
```python
# In main.py:293
uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="debug")
```

**Check Agent States:**
```bash
# Send status query via WhatsApp
"How's it going?"

# Or via API
curl -X POST https://your-app.onrender.com/agent/process \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1234567890", "message": "status"}'
```

**Monitor Background Tasks:**
```python
# Check periodic_cleanup logs (every 60 min)
# main.py:184-204

# Output:
# "🧹 Running periodic cleanup..."
# "✓ Cleanup complete - Expired sessions: X, Active agents: Y"
```

---

## Development Guide

### Project Structure

```
whatsapp_mcp/
├── src/python/
│   ├── main.py                      # Entry point
│   ├── agents/
│   │   ├── manager.py               # Agent lifecycle
│   │   ├── agent.py                 # Single agent
│   │   ├── session.py               # Session management
│   │   └── collaborative/
│   │       ├── orchestrator.py      # Multi-agent coordinator
│   │       ├── base_agent.py        # Base class
│   │       ├── a2a_protocol.py      # Agent communication
│   │       ├── models.py            # Data models
│   │       ├── research_mixin.py    # Research feature
│   │       ├── designer_agent.py    # Specialized agents
│   │       ├── frontend_agent.py
│   │       ├── code_reviewer_agent.py
│   │       ├── qa_agent.py
│   │       └── devops_agent.py
│   ├── sdk/
│   │   └── claude_sdk.py            # Claude SDK wrapper
│   ├── whatsapp_mcp/
│   │   ├── client.py                # WhatsApp API
│   │   └── parser.py                # Webhook parser
│   ├── github_mcp/
│   │   └── server.py                # GitHub MCP
│   ├── netlify_mcp/
│   │   └── server.py                # Netlify MCP
│   └── utils/
│       ├── config.py
│       └── logger.py
├── tests/                           # Test suite
├── requirements.txt
├── render.yaml
├── Dockerfile.render
└── .env
```

### Adding a New Workflow

**Step 1: Define Workflow Type**

Edit `orchestrator.py:754-823` (AI planning prompt):
```python
# Add to workflow list
"""
6. **my_workflow**: Custom workflow for specific task
   - Steps: Step 1 → Step 2 → Step 3
   - Agents: Agent1 + Agent2
   - Use when: User requests [specific condition]
"""
```

**Step 2: Implement Workflow Method**

Add to `orchestrator.py`:
```python
async def _workflow_my_workflow(self, user_prompt: str, plan: Dict) -> str:
    """My custom workflow"""
    print(f"\n🔥 Starting MY WORKFLOW")

    # Step 1
    result1 = await self._send_task_to_agent(
        agent_id=self.DESIGNER_ID,
        task_description="Do something"
    )

    # Step 2
    result2 = await self._send_task_to_agent(
        agent_id=self.FRONTEND_ID,
        task_description="Do something else",
        metadata={"data": result1}
    )

    # Return response
    return f"""✅ My workflow complete!

    Result: {result2}
    """
```

**Step 3: Add Routing**

Edit `orchestrator.py:925-936`:
```python
# Route to appropriate workflow
if workflow_type == "my_workflow":
    result = await self._workflow_my_workflow(user_prompt, plan)
elif workflow_type == "bug_fix":
    result = await self._workflow_bug_fix(user_prompt, plan)
# ... rest
```

**Step 4: Test**

```bash
# Send WhatsApp message that should trigger your workflow
"Do my custom workflow thing"

# Check logs for: "🔥 Starting MY WORKFLOW"
```

### Adding a New Agent

**Step 1: Create Agent File**

Create `src/python/agents/collaborative/my_agent.py`:
```python
from typing import Dict, Any
from .base_agent import BaseAgent
from .models import AgentCard, AgentRole, Task

class MyCustomAgent(BaseAgent):
    """My custom agent for specific tasks"""

    def __init__(self, mcp_servers: Dict = None):
        agent_card = AgentCard(
            agent_id="my_agent_001",
            name="My Custom Agent",
            role=AgentRole.BACKEND,  # Or create new role in models.py
            description="Expert in doing X, Y, Z",
            capabilities=[
                "Capability 1",
                "Capability 2",
                "Capability 3"
            ],
            skills={
                "languages": ["Python", "JavaScript"],
                "frameworks": ["FastAPI", "React"],
                "tools": ["Docker", "Git"]
            }
        )

        system_prompt = """
        You are an expert in [domain].

        Your expertise includes:
        - Skill 1
        - Skill 2
        - Skill 3

        When executing tasks:
        1. Do X
        2. Do Y
        3. Do Z
        """

        super().__init__(
            agent_card=agent_card,
            system_prompt=system_prompt,
            mcp_servers=mcp_servers
        )

    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute assigned task"""
        prompt = f"""
        Task: {task.description}

        Please do X, Y, Z...

        Respond with JSON: {{
            "result": "...",
            "status": "success"
        }}
        """

        response = await self.claude_sdk.send_message(prompt)

        # Parse and return result
        return {
            "result": parse_result(response),
            "status": "success"
        }

    async def review_artifact(self, artifact: Any) -> Dict[str, Any]:
        """Review work product"""
        prompt = f"""
        Review this artifact: {artifact}

        Provide feedback...

        Respond with JSON: {{
            "approved": true/false,
            "score": 1-10,
            "feedback": ["issue 1", "issue 2"]
        }}
        """

        review = await self.claude_sdk.send_message(prompt)
        return parse_review(review)
```

**Step 2: Register in Orchestrator**

Edit `orchestrator.py`:

Add agent ID constant (line 49-56):
```python
MY_AGENT_ID = "my_agent_001"
```

Add to `_get_agent()` (line 155-200):
```python
elif agent_type == "my_agent":
    from .my_agent import MyCustomAgent
    agent = MyCustomAgent(self.mcp_servers)
```

Add to `_get_agent_type_from_id()` (line 576-589):
```python
elif "my_agent" in agent_id:
    return "my_agent"
```

Add to `_get_agent_type_name()` (line 255-270):
```python
elif "my_agent" in agent_id:
    return "My Custom Agent"
```

**Step 3: Use in Workflows**

```python
# In any workflow method
result = await self._send_task_to_agent(
    agent_id=self.MY_AGENT_ID,
    task_description="Do custom task"
)
```

**Step 4: Test**

```python
# Create test script
import asyncio
from agents.collaborative.my_agent import MyCustomAgent
from agents.collaborative.models import Task

async def test():
    agent = MyCustomAgent()

    task = Task(
        description="Test task",
        from_agent="test",
        to_agent="my_agent_001"
    )

    result = await agent.execute_task(task)
    print(f"Result: {result}")

asyncio.run(test())
```

### Extending MCP Servers

**Add New MCP Server:**

**Step 1: Create MCP Server File**

Create `src/python/my_service_mcp/server.py`:
```python
import os

def create_my_service_mcp_config():
    """Create MCP configuration for My Service"""

    token = os.getenv("MY_SERVICE_TOKEN")
    if not token:
        raise ValueError("MY_SERVICE_TOKEN not set")

    return {
        "command": "npx",
        "args": ["@modelcontextprotocol/server-myservice"],
        "env": {
            "MY_SERVICE_TOKEN": token
        }
    }
```

**Step 2: Register in AgentManager**

Edit `agents/manager.py:27-105`:
```python
# 4. Add My Service MCP if enabled
self.enable_my_service = enable_my_service
if self.enable_my_service:
    try:
        from my_service_mcp.server import create_my_service_mcp_config

        my_service_config = create_my_service_mcp_config()
        self.available_mcp_servers["my_service"] = my_service_config
        print("✅ My Service MCP configured")
    except ValueError as e:
        print(f"⚠️  My Service MCP not available: {e}")
        self.enable_my_service = False
```

**Step 3: Update main.py**

```python
# Line 58-64
enable_my_service = os.getenv("ENABLE_MY_SERVICE_MCP", "false").lower() == "true"

agent_manager = AgentManager(
    whatsapp_mcp_tools=[whatsapp_send_tool],
    enable_github=enable_github,
    enable_netlify=enable_netlify,
    enable_my_service=enable_my_service  # Add parameter
)
```

**Step 4: Add Environment Variable**

```bash
# .env
ENABLE_MY_SERVICE_MCP=true
MY_SERVICE_TOKEN=your_token_here
```

**Step 5: Update render.yaml**

```yaml
- key: MY_SERVICE_TOKEN
  sync: false

- key: ENABLE_MY_SERVICE_MCP
  value: true
```

---

## Security

### Best Practices

**1. API Key Management**
- Never commit API keys to git
- Use environment variables only
- Rotate keys regularly
- Use separate keys for dev/prod

**2. Webhook Verification**
```python
# main.py:103-117
# Always verify webhook token
if token != os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN'):
    return PlainTextResponse("Forbidden", status_code=403)
```

**3. Input Validation**
```python
# Validate phone numbers
import re
def is_valid_phone(phone: str) -> bool:
    return bool(re.match(r'^\+\d{10,15}$', phone))

# Sanitize user input
def sanitize_input(text: str) -> str:
    # Remove potentially harmful characters
    return text.strip()[:1000]  # Limit length
```

**4. Rate Limiting**
```python
# Add to main.py
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/webhook")
@limiter.limit("10/minute")  # 10 requests per minute
async def webhook_receive(request: Request):
    # ... existing code
```

**5. HTTPS Only**
```python
# Enforce HTTPS in production
if os.getenv("ENV") == "production":
    from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
    app.add_middleware(HTTPSRedirectMiddleware)
```

### Security Checklist

- [ ] API keys in environment variables only
- [ ] Webhook token verification enabled
- [ ] HTTPS enforced in production
- [ ] Input validation on all endpoints
- [ ] Rate limiting configured
- [ ] Error messages don't leak sensitive info
- [ ] Dependencies regularly updated
- [ ] .gitignore includes .env
- [ ] No secrets in logs
- [ ] Session cleanup working (prevents memory leaks)

---

## Performance

### Optimization Tips

**1. Agent Caching**

```python
# orchestrator.py:125
enable_agent_caching = True  # Reuse agents (faster but more memory)

# Trade-off:
# False: Slower but uses less memory (default)
# True: Faster but uses more memory
```

**2. Session Cleanup**

```python
# manager.py:37
session_manager = SessionManager(
    ttl_minutes=30,      # Shorter TTL = less memory
    max_history=5        # Fewer messages = less tokens
)
```

**3. Parallel Agent Tasks**

```python
# Instead of sequential:
design = await send_task_to_agent(DESIGNER_ID, "design")
review = await request_review_from_agent(CODE_REVIEWER_ID, design)

# Use parallel when possible:
import asyncio
design_task = send_task_to_agent(DESIGNER_ID, "design")
review_task = send_task_to_agent(CODE_REVIEWER_ID, "review")
design, review = await asyncio.gather(design_task, review_task)
```

**4. Response Streaming**

```python
# For long responses, use streaming
async def stream_response(phone_number, message):
    async for chunk in agent.stream_message(message):
        whatsapp_client.send_message(phone_number, chunk)
```

**5. Database for Sessions**

```python
# Replace in-memory sessions with Redis for production

from redis import Redis
redis = Redis(host='localhost', port=6379)

def get_session(phone_number):
    session = redis.get(f"session:{phone_number}")
    return json.loads(session) if session else create_new_session()

def save_session(phone_number, session):
    redis.setex(f"session:{phone_number}", 3600, json.dumps(session))
```

### Performance Monitoring

**Add Metrics:**

```python
import time
from collections import defaultdict

metrics = defaultdict(list)

@app.middleware("http")
async def track_timing(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    metrics[request.url.path].append(duration)
    print(f"{request.url.path}: {duration:.2f}s")

    return response

@app.get("/metrics")
async def get_metrics():
    return {
        path: {
            "avg": sum(times) / len(times),
            "max": max(times),
            "min": min(times),
            "count": len(times)
        }
        for path, times in metrics.items()
    }
```

---

## Testing

### Running Tests

```bash
# Install pytest
pip install pytest pytest-asyncio

# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_orchestrator.py

# Run with verbose output
pytest tests/ -v

# Run with coverage
pip install pytest-cov
pytest tests/ --cov=src/python --cov-report=html
```

### Test Structure

**Unit Tests:**
```python
# tests/test_agent.py
import pytest
from agents.agent import Agent

@pytest.mark.asyncio
async def test_agent_creation():
    agent = Agent(
        phone_number="+1234567890",
        session_manager=mock_session_manager,
        available_mcp_servers={}
    )
    assert agent.phone_number == "+1234567890"

@pytest.mark.asyncio
async def test_message_processing():
    agent = Agent(...)
    response = await agent.process_message("Hello!")
    assert response is not None
    assert len(response) > 0
```

**Integration Tests:**
```python
# tests/test_orchestrator.py
import pytest
from agents.collaborative.orchestrator import CollaborativeOrchestrator

@pytest.mark.asyncio
async def test_full_build_workflow():
    orchestrator = CollaborativeOrchestrator(mcp_servers={})

    # Mock user request
    response = await orchestrator.build_webapp("Build a todo app")

    # Verify response contains deployment URL
    assert "netlify.app" in response or "app.netlify.com" in response

@pytest.mark.asyncio
async def test_refinement_handling():
    orchestrator = CollaborativeOrchestrator(mcp_servers={})

    # Start task
    await orchestrator.build_webapp("Build a todo app")

    # Send refinement
    response = await orchestrator.handle_refinement("Make it blue")

    # Verify refinement applied
    assert orchestrator.accumulated_refinements == ["Make it blue"]
```

**API Tests:**
```python
# tests/test_api.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_webhook_verification():
    response = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "test_token",
            "hub.challenge": "challenge_string"
        }
    )
    assert response.status_code == 200
    assert response.text == "challenge_string"
```

### Manual Testing

**Test Single Agent:**
```bash
curl -X POST http://localhost:8000/agent/process \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "message": "What is Python?"
  }'
```

**Test Multi-Agent:**
```bash
curl -X POST http://localhost:8000/agent/process \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "message": "Build me a todo app with React"
  }'
```

**Test Status Query:**
```bash
# Start a build first, then:
curl -X POST http://localhost:8000/agent/process \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "message": "How is it going?"
  }'
```

---

## Appendix

### Environment Variables Reference

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-api03-xxx
WHATSAPP_ACCESS_TOKEN=EAAxxx
WHATSAPP_PHONE_NUMBER_ID=123xxx
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_custom_token_here

# Optional - GitHub Integration
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxx
ENABLE_GITHUB_MCP=true

# Optional - Netlify Integration (Required for multi-agent)
NETLIFY_PERSONAL_ACCESS_TOKEN=nfp_xxx
ENABLE_NETLIFY_MCP=true

# Optional - Configuration
AGENT_SYSTEM_PROMPT="Custom prompt for single-agent mode"
PORT=8000
```

### Useful Commands

```bash
# Start server
python src/python/main.py

# Check syntax
python3 -m py_compile src/python/**/*.py

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# View logs (Render)
# Dashboard → Your Service → Logs

# Reset session via API
curl -X POST http://localhost:8000/agent/reset/+1234567890

# Health check
curl http://localhost:8000/health
```

### File Locations Reference

| Component | File Path | Key Lines |
|-----------|-----------|-----------|
| **Entry Point** | `src/python/main.py` | 281-294 |
| **Webhook Handler** | `src/python/main.py` | 120-155 |
| **Agent Manager** | `src/python/agents/manager.py` | 127-236 (routing) |
| **Orchestrator** | `src/python/agents/collaborative/orchestrator.py` | 878-959 (main) |
| **Designer Agent** | `src/python/agents/collaborative/designer_agent.py` | 63-281 |
| **Frontend Agent** | `src/python/agents/collaborative/frontend_agent.py` | Full file |
| **DevOps Agent** | `src/python/agents/collaborative/devops_agent.py` | Full file |
| **A2A Protocol** | `src/python/agents/collaborative/a2a_protocol.py` | 38-140 |
| **Models** | `src/python/agents/collaborative/models.py` | Full file |
| **Session Manager** | `src/python/agents/session.py` | 27-112 |
| **WhatsApp Client** | `src/python/whatsapp_mcp/client.py` | 31-70 (send) |
| **Claude SDK** | `src/python/sdk/claude_sdk.py` | 182-227 (send) |

### Data Model Reference

**AgentCard:**
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

**Task:**
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

**TaskResponse:**
```python
{
    "task_id": str,
    "status": TaskStatus,
    "result": Any,
    "agent_id": str,
    "timestamp": str
}
```

**Session:**
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

---

## Support & Contributing

### Getting Help

**Issues:** https://github.com/your-repo/issues
**Discussions:** https://github.com/your-repo/discussions

### Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Make changes
4. Run tests: `pytest tests/`
5. Commit: `git commit -m "Add my feature"`
6. Push: `git push origin feature/my-feature`
7. Create Pull Request

### License

[Your License Here]

---

**Last Updated:** October 22, 2025
**Version:** 2.0.0
**Maintained by:** [Your Name/Team]
