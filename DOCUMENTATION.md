# WhatsApp Multi-Agent System - Complete Documentation

**Version:** 2.2.0
**Last Updated:** January 2025
**Status:** Production Ready with Enhanced Observability

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Installation & Setup](#installation--setup)
5. [Configuration](#configuration)
6. [Core Components](#core-components)
7. [Multi-Agent System](#multi-agent-system)
8. [State Management & Persistence](#state-management--persistence)
9. [API Reference](#api-reference)
10. [Workflow Types](#workflow-types)
11. [Message Handling](#message-handling)
12. [Deployment](#deployment)
13. [Observability & Debugging](#observability--debugging)
14. [Troubleshooting](#troubleshooting)
15. [Performance & Optimization](#performance--optimization)
16. [Security](#security)
17. [Testing](#testing)

---

## Overview

### What is This?

A production-ready, platform-agnostic AI assistant system that uses Claude AI (Sonnet 4.5) and a multi-agent architecture to build complete, deployable web applications through conversational interfaces (WhatsApp, GitHub).

### Key Features

**Platform Support:**
- WhatsApp Business Cloud API (v18.0)
- GitHub App webhook integration (@droid mentions)
- Platform-agnostic orchestrator design

**Single-Agent Mode:**
- Personal AI assistant for individual conversations
- Context-aware responses with Redis session management
- 60-minute conversation memory with auto-expiry
- 10-message history limit (token optimization)

**Multi-Agent Mode:**
- Collaborative team of 5 specialized AI agents
- Builds production-ready webapps from natural language
- Real-time notifications on progress (WhatsApp/GitHub comments)
- **Intelligent refinement handling** during development
- **Automatic build verification and error fixing** (up to 10 retries)
- **Quality loops** (iterative improvement until score ≥ 9/10)
- **State persistence** (crash recovery via PostgreSQL)
- **Logfire debugging** (agents query production traces to fix errors)

**Advanced Capabilities:**
- **AI-Powered Message Classification** (no keyword matching)
- **Lazy Agent Initialization** (memory optimization)
- **Dynamic Progress Tracking** (adjusts estimates during retries)
- **A2A Protocol** (Agent-to-Agent communication)
- **Crash Recovery** (resume interrupted tasks from database)
- **Production Telemetry** (Logfire integration for debugging)

**Integrations:**
- Claude AI (Sonnet 4.5 - `claude-sonnet-4-5-20250929`)
- Model Context Protocol (MCP)
- GitHub (repository management via MCP)
- Netlify (automated deployment via MCP)
- PostgreSQL/Neon (state persistence)
- Redis (session storage)
- Logfire (observability & telemetry)

### Use Cases

1. **Personal Assistant** - Ask questions, get technical guidance
2. **Webapp Builder** - "Build me a todo app with React"
3. **Code Review** - AI-powered code reviews with security analysis
4. **Deployment Automation** - Automatic GitHub + Netlify deployment
5. **Bug Fixing** - "Fix the build errors" → AI diagnoses and fixes using Logfire traces
6. **Design Consultation** - Get UI/UX design specifications
7. **GitHub PR Assistance** - @droid mentions in PR comments trigger multi-agent workflows

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              User Interface (Multi-Platform)                    │
│  ┌─────────────────────┐     ┌──────────────────────────────┐  │
│  │  WhatsApp User      │     │  GitHub PR/Issue Comment     │  │
│  │  (Chat messages)    │     │  (@droid mention)            │  │
│  └─────────────────────┘     └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
              ↓                              ↓
┌─────────────────────────┐    ┌────────────────────────────────┐
│ WhatsApp Business API   │    │  GitHub App Webhook            │
│ (v18.0)                 │    │  (Signature verification)      │
└─────────────────────────┘    └────────────────────────────────┘
              ↓ (webhook POST)              ↓ (webhook POST)
┌─────────────────────────────────────────────────────────────────┐
│                FastAPI Application (main.py)                    │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  POST /webhook              POST /github/webhook          │ │
│  │  • WhatsAppWebhookParser    • GitHub signature verify    │ │
│  │  • Extract message          • Parse event                │ │
│  │  • Return 200 OK (<5s)      • Extract @droid mention     │ │
│  │  • Spawn async task         • Background processing      │ │
│  └───────────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Logfire Telemetry Integration                            │ │
│  │  • instrument_fastapi() - Auto-trace HTTP                │ │
│  │  • instrument_anthropic() - Track LLM calls              │ │
│  │  • instrument_httpx() - Monitor external APIs            │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ↓ (async task)
┌─────────────────────────────────────────────────────────────────┐
│         AgentManager / GitHubAgentManager (manager.py)          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │       AI Message Classifier (Claude-powered)            │   │
│  │  Uses Claude to intelligently classify user intent:    │   │
│  │  • webapp_request → Multi-agent orchestrator           │   │
│  │  • refinement → Update active task                     │   │
│  │  • status_query → Show detailed progress               │   │
│  │  • cancellation → Stop and cleanup                     │   │
│  │  • conversation → Single-agent mode                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │   Redis Session Manager - Persistent storage           │   │
│  │   • TTL: 60 minutes (auto-expiry)                       │   │
│  │   • Max history: 10 messages                            │   │
│  │   • Distributed session support                         │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
         ↓                         ↓                    ↓
┌──────────────────┐  ┌─────────────────────────────┐  ┌──────────┐
│  Single Agent    │  │ Multi-Agent Orchestrator    │  │  Single  │
│                  │  │ (orchestrator.py)           │  │  Agent   │
│  ClaudeSDK       │  │  ┌────────────────────────┐ │  │          │
│  + MCP Tools     │  │  │  PostgreSQL/Neon       │ │  │          │
│  (4096 tokens)   │  │  │  State Persistence     │ │  │          │
└──────────────────┘  │  │  • Crash recovery      │ │  └──────────┘
                      │  │  • Resume tasks        │ │
                      │  │  • Audit trail         │ │
                      │  └────────────────────────┘ │
                      │  ┌────────────────────────┐ │
                      │  │  AI Workflow Planner   │ │
                      │  │  (Claude-powered)      │ │
                      │  │  • Analyze request     │ │
                      │  │  • Select workflow     │ │
                      │  │  • Determine agents    │ │
                      │  │  • Estimate complexity │ │
                      │  └────────────────────────┘ │
                      │         ↓                   │
                      │  ┌────────────────────────┐ │
                      │  │ Lazy Agent Init        │ │
                      │  │ (on-demand creation)   │ │
                      │  │                        │ │
                      │  │ • Designer (UI/UX)     │ │
                      │  │ • Frontend (React)     │ │
                      │  │ • Code Reviewer        │ │
                      │  │ • QA Engineer          │ │
                      │  │ • DevOps (Deploy)      │ │
                      │  └────────────────────────┘ │
                      │         ↓                   │
                      │  A2A Protocol               │
                      │  (Agent-to-Agent)           │
                      │  • send_task()              │
                      │  • request_review()         │
                      │  • Telemetry tracking       │
                      └─────────────────────────────┘
                                 ↓
                      ┌─────────────────────────────┐
                      │   Claude AI API             │
                      │   (Sonnet 4.5)              │
                      │   Model: claude-sonnet-     │
                      │   4-5-20250929              │
                      └─────────────────────────────┘
                                 ↓
                      ┌─────────────────────────────┐
                      │   MCP Servers               │
                      │   • WhatsApp (tools)        │
                      │   • GitHub (npx)            │
                      │   • Netlify (npx)           │
                      │   • PostgreSQL (binary)     │
                      └─────────────────────────────┘
```

### Data Flow Architecture

**WhatsApp Message Flow:**
```
1. User sends WhatsApp message
   ↓
2. WhatsApp Business API → POST /webhook (main.py:151)
   ↓
3. WhatsAppWebhookParser.parse_message() extracts data
   ↓
4. log_user_action() → Logfire telemetry (main.py:172)
   ↓
5. asyncio.create_task(process_whatsapp_message) - Background (main.py:187)
   ↓
6. Return 200 OK to WhatsApp (<5s requirement)
   ↓
7. AgentManager.process_message() - AI classification (manager.py:142)
   ↓
   ├─ Webapp request? → CollaborativeOrchestrator.build_webapp()
   │   ↓
   │   ├─ AI planning → Select workflow (orchestrator.py:1027)
   │   ├─ Save state to PostgreSQL (crash recovery)
   │   ├─ Execute workflow (Design → Implement → Review → Deploy)
   │   ├─ Quality loop (min 9/10 score) (orchestrator.py:1308)
   │   ├─ Deploy with retry (max 10 attempts) (orchestrator.py:1867)
   │   │   ├─ DevOps queries Logfire for deployment errors (orchestrator.py:1912)
   │   │   ├─ Frontend queries Logfire for build errors (orchestrator.py:1995)
   │   │   └─ Fix → Retry → Verify
   │   └─ Delete state on completion
   │
   └─ Regular conversation? → Agent.process_message()
       ↓
       └─ ClaudeSDK.send_message() → Claude API + MCP tools
   ↓
8. RedisSessionManager.add_message() - Store with TTL (session_redis.py:102)
   ↓
9. measure_performance() - Telemetry (main.py:213)
   ↓
10. WhatsAppClient.send_message() → WhatsApp API
    ↓
11. User receives response
```

**GitHub Webhook Flow:**
```
1. User posts @droid mention in PR/Issue comment
   ↓
2. GitHub App webhook → POST /github/webhook (webhook_handler.py:48)
   ↓
3. verify_github_signature() - HMAC SHA-256 (webhook_handler.py:84)
   ↓
4. parse_github_event() - Extract context (webhook_handler.py:96)
   ↓
5. extract_droid_mention() - Get command text (webhook_handler.py:119)
   ↓
6. Return 200 OK to GitHub (<10s requirement)
   ↓
7. background_tasks.add_task(process_droid_command) (webhook_handler.py:135)
   ↓
8. GitHubAgentManager.process_command() (github_manager.py)
   ↓
9. CollaborativeOrchestrator.build_webapp()
   ↓
10. Multi-agent workflow execution (same as WhatsApp flow)
    ↓
11. Post result as GitHub comment with live URL
```

### System Components

#### 1. **FastAPI Application** (`main.py` - 358 lines)
**Location:** `/src/python/main.py`

- **Endpoints:**
  - `GET /` (107-114): Health check
  - `GET /health` (117-131): Detailed status
  - `GET /webhook` (134-148): WhatsApp verification
  - `POST /webhook` (151-195): **CRITICAL** - Incoming WhatsApp messages
  - `POST /agent/process` (270-298): Direct messaging (testing)
  - `POST /agent/reset/{phone_number}` (301-317): Session reset
  - GitHub routes via router (github_bot module)

- **Background Tasks:**
  - `periodic_cleanup()` (247-267): Every 60 minutes, cleanup expired sessions
  - `startup_event()` (320-333): Initialize service
  - `shutdown_event()` (336-341): Cleanup all agents

- **Telemetry Integration:**
  - Lines 31-43: Import telemetry functions
  - Line 46: `initialize_logfire()`
  - Line 51: `instrument_fastapi(app)`
  - Line 54: `instrument_anthropic()`
  - Line 57: `instrument_httpx()`

#### 2. **Agent Manager** (`agents/manager.py` - 496 lines)
**Location:** `/src/python/agents/manager.py`

- **Purpose:** Routes messages to single-agent or multi-agent systems
- **Key Features:**
  - AI-powered intent classification (not keyword-based)
  - Per-user orchestrator management
  - Smart refinement handling
  - Session lifecycle management
  - MCP server configuration (WhatsApp, GitHub, Netlify, PostgreSQL)

- **Key Methods:**
  - `__init__()` (27-119): Initialize MCP servers
  - `process_message()` (142-251): **Main router with AI classification**
  - `_is_webapp_request()` (253-342): AI-powered webapp detection
  - `_classify_message()` (344-454): AI classification during active tasks

#### 3. **Redis Session Manager** (`agents/session_redis.py` - 196 lines)
**Location:** `/src/python/agents/session_redis.py`

- **Purpose:** Persistent session storage with TTL
- **Features:**
  - Redis connection with retry
  - 60-minute TTL (auto-expiry)
  - Max 10 messages history
  - JSON serialization
  - Distributed session support

- **Key Methods:**
  - `get_session()` (57-100): Get/create session with TTL refresh
  - `add_message()` (102-132): Append message with history trimming
  - `cleanup_expired_sessions()` (151-166): Report active sessions

- **Redis Key Pattern:** `session:{phone_number}`

#### 4. **PostgreSQL Database Models** (`database/models.py` - 98 lines)
**Location:** `/src/python/database/models.py`

- **OrchestratorState Table:**
  - Primary Key: `phone_number`
  - State: `is_active`, `current_phase`, `current_workflow`
  - Task: `original_prompt`, `accumulated_refinements`, `current_implementation`, `current_design_spec`
  - Progress: `workflow_steps_completed`, `workflow_steps_total`, `current_agent_working`
  - Purpose: Crash recovery, resume interrupted tasks

- **OrchestratorAudit Table:**
  - Event tracking for state changes
  - Audit trail for analytics

#### 5. **Multi-Agent Orchestrator** (`agents/collaborative/orchestrator.py` - 2,239 lines)
**Location:** `/src/python/agents/collaborative/orchestrator.py`

- **Purpose:** Coordinates 5 specialized agents via A2A protocol
- **Key Features:**
  - AI-powered workflow planning
  - Lazy agent initialization (memory optimization)
  - State persistence (crash recovery)
  - Real-time notifications (WhatsApp/GitHub)
  - Quality loops (min 9/10 score)
  - Deployment retry with Logfire debugging (max 10 attempts)
  - Dynamic progress tracking

- **Configuration:**
  - `max_review_iterations`: 10
  - `min_quality_score`: 9/10
  - `max_build_retries`: 10
  - `enable_agent_caching`: False (saves memory)

- **Critical Methods:**
  - `build_webapp()` (1165-1250): Main entry point with AI planning
  - `_ai_plan_workflow()` (1027-1159): AI-powered workflow selection
  - `_workflow_full_build()` (1256-1423): Complete build workflow
  - `_deploy_with_retry()` (1867-2111): Deployment with Logfire debugging
  - `_save_state()` (691-719): Persist to PostgreSQL
  - `_restore_state()` (721-761): Crash recovery
  - `_send_task_to_agent()` (798-915): A2A task with telemetry
  - `_request_review_from_agent()` (917-1021): A2A review with metrics

#### 6. **Specialized Agents**

All agents extend `BaseAgent` and use A2A protocol for communication.

**Designer Agent** (`designer_agent.py`):
- Creates design specifications
- Reviews frontend code vs design
- Ensures design fidelity (score 1-10)
- WCAG 2.1 accessibility guidelines

**Frontend Developer Agent** (`frontend_agent.py`):
- React/Vue/Next.js implementation
- Production-ready code (NO placeholders)
- Fixes build errors using Logfire traces
- GitHub-ready projects

**Code Reviewer Agent** (`code_reviewer_agent.py`):
- Security analysis (OWASP Top 10)
- Performance review
- Best practices validation
- 10 comprehensive review criteria

**QA Engineer Agent** (`qa_agent.py`):
- Functional testing
- Accessibility testing (WCAG 2.1)
- Cross-browser validation
- Performance testing (Core Web Vitals)

**DevOps Engineer Agent** (`devops_agent.py`):
- Netlify deployment
- Build error detection and logging
- Queries Logfire for deployment failures
- netlify.toml generation (NPM_FLAGS fix)
- Post-deployment verification

#### 7. **A2A Protocol** (`agents/collaborative/a2a_protocol.py` - 157 lines)
**Location:** `/src/python/agents/collaborative/a2a_protocol.py`

- **Purpose:** Standardized agent communication
- **Features:**
  - In-memory message queue
  - Task requests/responses
  - Review requests/responses
  - Agent registration/unregistration

#### 8. **Claude SDK Wrapper** (`sdk/claude_sdk.py` - 340 lines)
**Location:** `/src/python/sdk/claude_sdk.py`

- **Configuration:**
  - Model: `claude-sonnet-4-5-20250929` (Sonnet 4.5)
  - Max tokens: 4096
  - Permission mode: `bypassPermissions`

- **Dynamic System Prompt:**
  - Lines 38-145: Enhances prompt based on available MCP servers
  - WhatsApp instructions (44-51)
  - GitHub instructions (54-70)
  - Netlify instructions (73-100)
  - PostgreSQL instructions with schema (103-145)

- **Key Methods:**
  - `initialize_client()` (160-228): Setup with MCP servers
  - `send_message()` (230-275): Send and get response
  - `stream_message()` (277-315): Streaming support
  - `close()` (317-339): Cleanup with error suppression

#### 9. **GitHub Bot** (`github_bot/webhook_handler.py` - 275 lines)
**Location:** `/src/python/github_bot/webhook_handler.py`

- **Endpoints:**
  - `GET /github/webhook` (30-45): Webhook verification
  - `POST /github/webhook` (48-148): **Main webhook receiver**
  - `GET /github/health` (243-257): Health check
  - `GET /github/config` (260-274): Configuration status

- **Key Features:**
  - HMAC SHA-256 signature verification
  - @droid mention extraction
  - Bot comment filtering (avoid loops)
  - Background task processing
  - Error comment posting

#### 10. **Telemetry** (`utils/telemetry.py` - 446+ lines)
**Location:** `/src/python/utils/telemetry.py`

- **Integration:**
  - Logfire (Pydantic's observability platform)
  - Dashboard: https://logfire.pydantic.dev/
  - Project: whatsapp-mcp

- **Key Functions:**
  - `initialize_logfire()`: Setup with token
  - `instrument_fastapi()`: Auto-trace HTTP requests
  - `instrument_anthropic()`: Track LLM calls and tokens
  - `instrument_httpx()`: Monitor external API calls
  - `trace_operation()`: Context manager for tracing
  - `trace_workflow()`: Decorator for workflows
  - `measure_performance()`: Performance metrics
  - `log_event()`, `log_error()`, `log_metric()`: Event logging
  - `set_user_context()`: User-scoped tracing
  - `track_session_event()`: Session event tracking

- **Usage in Code:**
  - All A2A communications traced (orchestrator.py:826-836)
  - Workflow execution traced (orchestrator.py:1256)
  - Agent task execution traced
  - Deployment attempts traced with metadata

- **Debugging Capabilities:**
  - **DevOps agent queries Logfire** (orchestrator.py:1912-1928)
  - **Frontend agent queries Logfire** (orchestrator.py:1995-2020)
  - Query production traces to understand failures
  - Extract exact error messages, file paths, line numbers
  - Reference specific trace IDs in bug fix analysis

---

## Quick Start

### Prerequisites

- Python 3.12+
- WhatsApp Business Account
- Anthropic API key (Claude)
- (Optional) GitHub Personal Access Token
- (Optional) Netlify Personal Access Token
- (Optional) Redis instance
- (Optional) PostgreSQL/Neon database

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

**Expected**: Multi-agent team starts building, sends real-time updates via WhatsApp

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

# GitHub Bot (Optional - for @droid mentions in PRs)
GITHUB_WEBHOOK_SECRET=your_webhook_secret
GITHUB_APP_ID=your_app_id
GITHUB_INSTALLATION_ID=your_installation_id

# Netlify MCP (Optional - required for multi-agent deployments)
NETLIFY_PERSONAL_ACCESS_TOKEN=your_netlify_token
ENABLE_NETLIFY_MCP=true

# Redis (Optional - for session persistence)
REDIS_URL=redis://localhost:6379

# PostgreSQL/Neon (Optional - for state persistence and crash recovery)
DATABASE_URL=postgresql://user:pass@host/db
ENABLE_PGSQL_MCP=true

# Agent Configuration (Optional)
AGENT_SYSTEM_PROMPT="You are a helpful AI assistant."

# Service Configuration (Optional)
PORT=8000

# Telemetry (Optional - Logfire observability)
LOGFIRE_TOKEN=your_logfire_token
ENABLE_LOGFIRE=true
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
- `redis>=5.0.0` - Session storage
- `sqlalchemy[asyncio]>=2.0.0` - ORM for PostgreSQL
- `asyncpg>=0.29.0` - PostgreSQL async driver
- `pgsql-mcp-server>=1.3.2` - PostgreSQL MCP
- `logfire>=0.40.0` - Observability platform
- `requests>=2.31.0` - HTTP client

#### Step 3: Configure WhatsApp Webhook

1. Go to [Meta Business Suite](https://business.facebook.com/)
2. Navigate to **WhatsApp → Configuration**
3. Set webhook URL: `https://your-domain.com/webhook` (use ngrok for local testing)
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
  "available_mcp_servers": ["whatsapp", "github", "netlify", "postgres"]
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
| `GITHUB_WEBHOOK_SECRET` | ❌ Optional | - | GitHub webhook signature secret |
| `GITHUB_APP_ID` | ❌ Optional | - | GitHub App ID |
| `GITHUB_INSTALLATION_ID` | ❌ Optional | - | GitHub App Installation ID |
| `NETLIFY_PERSONAL_ACCESS_TOKEN` | ❌ Optional | - | Netlify API token for MCP |
| `ENABLE_NETLIFY_MCP` | ❌ Optional | `false` | Enable Netlify deployment (required for multi-agent) |
| `REDIS_URL` | ❌ Optional | `redis://localhost:6379` | Redis connection URL |
| `DATABASE_URL` | ❌ Optional | - | PostgreSQL connection URL (Neon) |
| `ENABLE_PGSQL_MCP` | ❌ Optional | `false` | Enable PostgreSQL MCP for agents |
| `AGENT_SYSTEM_PROMPT` | ❌ Optional | Default prompt | Custom system prompt for single-agent mode |
| `PORT` | ❌ Optional | `8000` | Server port |
| `LOGFIRE_TOKEN` | ❌ Optional | - | Logfire observability token |
| `ENABLE_LOGFIRE` | ❌ Optional | `false` | Enable Logfire telemetry |

### System Configuration

**Session Management** (`agents/manager.py:37`):
```python
session_manager = RedisSessionManager(
    ttl_minutes=60,      # 60-minute conversation timeout
    max_history=10       # Keep last 10 messages
)
```

**Claude SDK** (`sdk/claude_sdk.py:149-150`):
```python
model = "claude-sonnet-4-5-20250929"  # Sonnet 4.5
max_tokens = 4096                      # Token limit per response
```

**Orchestrator** (`agents/collaborative/orchestrator.py:163-166`):
```python
max_review_iterations = 10    # Maximum quality improvement iterations
min_quality_score = 9         # Minimum acceptable score (out of 10)
max_build_retries = 10        # Maximum deployment retry attempts
enable_agent_caching = False  # Agent reuse (False = saves memory)
```

**WhatsApp API** (`whatsapp_mcp/client.py`):
```python
api_version = "v18.0"
base_url = f"https://graph.facebook.com/{api_version}/{phone_number_id}"
```

---

## Core Components

### 1. Main Application (`main.py`)

**Entry Point** (344-357):
```python
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")
```

**Key Endpoints**:

| Endpoint | Method | Handler | Line | Purpose |
|----------|--------|---------|------|---------|
| `/` | GET | `root()` | 107-114 | Health check |
| `/health` | GET | `health_check()` | 117-131 | Detailed status |
| `/webhook` | GET | `webhook_verify()` | 134-148 | WhatsApp verification |
| `/webhook` | POST | `webhook_receive()` | 151-195 | **CRITICAL** - Incoming messages |
| `/agent/process` | POST | `process_message()` | 270-298 | Direct messaging (testing) |
| `/agent/reset/{phone}` | POST | `reset_session()` | 301-317 | Clear history |
| `/github/webhook` | POST | GitHub router | - | GitHub webhook receiver |

**Critical Flow** (Lines 151-195):
```python
@app.post("/webhook")
async def webhook_receive(request: Request):
    body = await request.json()
    message_data = WhatsAppWebhookParser.parse_message(body)  # Line 159

    # Log user action with Logfire
    log_user_action("message_received", from_number, ...)  # Line 172

    # Spawn async task (don't block webhook response)
    asyncio.create_task(process_whatsapp_message(from_number, message_text))  # Line 187

    # Return 200 OK immediately (WhatsApp requires <5s)
    return {"status": "ok"}  # Line 190
```

**Background Tasks**:
- `periodic_cleanup()` (247-267): Runs every 60 minutes to clean expired sessions
- `startup_event()` (320-333): Initialize service, start background tasks
- `shutdown_event()` (336-341): Cleanup all agents

### 2. Agent Manager (`agents/manager.py`)

**Purpose**: Routes messages to single-agent or multi-agent systems using AI classification

**Initialization** (27-119):
```python
def __init__(self, whatsapp_mcp_tools, enable_github, enable_netlify):
    # Redis session manager (persistent, with TTL)
    self.session_manager = RedisSessionManager(ttl_minutes=60, max_history=10)

    # Available MCP servers
    self.available_mcp_servers = {}

    # Per-user orchestrators (for concurrent multi-agent tasks)
    self.orchestrators: Dict[str, any] = {}

    # Multi-agent enabled if Netlify MCP available
    self.multi_agent_enabled = MULTI_AGENT_AVAILABLE and enable_netlify
```

**Main Router** (`process_message()` - 142-251):

The heart of the system - intelligently routes messages using AI:

```python
async def process_message(phone_number: str, message: str) -> str:
    # Check if orchestrator active for this user (line 157)
    active_orchestrator = self.orchestrators.get(phone_number)

    if active_orchestrator and active_orchestrator.is_active:
        # User has active multi-agent task
        # Use AI to classify their message (line 166)
        message_type = await self._classify_message(
            message=message,
            active_task=active_orchestrator.original_prompt,
            current_phase=active_orchestrator.current_phase
        )

        # Route based on AI classification (lines 175-213)
        if message_type == "refinement":
            # User wants to modify current task
            return await active_orchestrator.handle_refinement(message)

        elif message_type == "status_query":
            # User asking about progress
            return await active_orchestrator.handle_status_query()

        elif message_type == "cancellation":
            # User wants to stop
            response = await active_orchestrator.handle_cancellation()
            del self.orchestrators[phone_number]
            return response

        elif message_type == "new_task":
            # User wants a different task (ask for confirmation)
            return "⚠️ You have an active task. Send 'cancel' to stop it."

        # ... etc

    # No active orchestrator - check if this is a webapp request (line 216)
    if self.multi_agent_enabled and await self._is_webapp_request(message):
        # Use AI to detect webapp build requests
        orchestrator = CollaborativeOrchestrator(
            mcp_servers=self.available_mcp_servers,
            user_phone_number=phone_number
        )
        self.orchestrators[phone_number] = orchestrator

        # Execute multi-agent build
        response = await orchestrator.build_webapp(message)

        # Clean up if completed
        if not orchestrator.is_active:
            del self.orchestrators[phone_number]

        return response

    # Fallback to single agent (line 250)
    agent = self.get_or_create_agent(phone_number)
    return await agent.process_message(message)
```

**AI-Powered Detection Methods:**

**`_is_webapp_request()`** (253-342):
- Uses Claude to intelligently detect webapp build requests
- No hardcoded keywords
- Returns JSON: `{is_webapp_request: bool, confidence: float, reasoning: str}`
- Fallback to keyword matching on error

**`_classify_message()`** (344-454):
- Classifies message during active task
- Categories: refinement, status_query, cancellation, new_task, conversation
- Considers: active task, current phase, message content
- Returns classification with confidence and reasoning

### 3. Redis Session Manager (`agents/session_redis.py`)

**Purpose**: Persistent, distributed session storage with automatic expiry

**Key Methods**:

**`get_session()`** (57-100):
```python
def get_session(phone_number: str) -> Dict:
    key = f"session:{phone_number}"
    session_json = redis_client.get(key)

    if session_json:
        # Existing session - deserialize and refresh TTL
        session = json.loads(session_json)
        session["last_active"] = datetime.utcnow()
        redis_client.setex(key, ttl_seconds, json.dumps(session))
        return session
    else:
        # Create new session
        session = {
            "phone_number": phone_number,
            "conversation_history": [],
            "created_at": datetime.utcnow().isoformat(),
            "last_active": datetime.utcnow()
        }
        redis_client.setex(key, ttl_seconds, json.dumps(session))
        return session
```

**`add_message()`** (102-132):
```python
def add_message(phone_number: str, role: str, content: str):
    session = self.get_session(phone_number)

    # Add message
    session["conversation_history"].append({
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    })

    # Limit history to prevent token overflow (line 121)
    if len(session["conversation_history"]) > self.max_history:
        session["conversation_history"] = session["conversation_history"][-self.max_history:]

    # Update last active and save to Redis
    session["last_active"] = datetime.utcnow()
    redis_client.setex(key, ttl_seconds, json.dumps(session))
```

**Benefits**:
- Automatic expiry via Redis TTL
- Distributed session support (multiple server instances)
- No manual cleanup needed
- Survives application restarts

---

## Multi-Agent System

### Agent Architecture

**Agent IDs** (`orchestrator.py:59-66`):
```python
ORCHESTRATOR_ID = "orchestrator"
DESIGNER_ID = "designer_001"
FRONTEND_ID = "frontend_001"
CODE_REVIEWER_ID = "code_reviewer_001"
QA_ID = "qa_engineer_001"
DEVOPS_ID = "devops_001"
```

### Lazy Agent Initialization

**Problem**: Creating all 5 agents at startup wastes ~1.5GB memory
**Solution**: Create agents on-demand, cleanup after use

**`_get_agent()`** (201-246):
```python
async def _get_agent(self, agent_type: str):
    # Check if already active
    if agent_type in self._active_agents:
        return self._active_agents[agent_type]

    # Check cache (if caching enabled)
    if self.enable_agent_caching and agent_type in self._agent_cache:
        agent = self._agent_cache[agent_type]
        self._active_agents[agent_type] = agent
        return agent

    # Create new agent on-demand
    print(f"🚀 Spinning up {agent_type} agent...")

    if agent_type == "designer":
        agent = DesignerAgent(self.mcp_servers)
    elif agent_type == "frontend":
        agent = FrontendDeveloperAgent(self.mcp_servers)
    # ... etc

    # Register in active agents
    self._active_agents[agent_type] = agent

    # Optionally cache for reuse
    if self.enable_agent_caching:
        self._agent_cache[agent_type] = agent

    return agent
```

**`_cleanup_agent()`** (248-275):
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
    print(f"🧹 Cleaning up {agent_type} agent...")
    await agent.cleanup()

    # Unregister from A2A protocol
    a2a_protocol.unregister_agent(agent.agent_card.agent_id)

    # Remove from active agents
    del self._active_agents[agent_type]

    print(f"✅ {agent_type} agent cleaned up and resources freed")
```

**Benefits**:
- 70% memory reduction (only active agents consume RAM)
- Faster startup (no agent initialization)
- Automatic cleanup (resources freed after task)
- Optional caching for performance

### Specialized Agents

#### 1. Designer Agent (`designer_agent.py` - 612 lines)

**Capabilities**:
- Design system creation
- Color palette selection (hex codes)
- Typography specification (Google Fonts)
- Component design (wireframes, layouts)
- Accessibility guidelines (WCAG 2.1 AA)
- **Frontend code review** (compares implementation vs design spec)

**Review Scoring** (1-10):
- 10: Perfect adherence to design
- 9: Excellent, minor tweaks
- 8: Good, some improvements needed
- 7: Acceptable, several issues
- 6: Below standard
- 1-5: Poor to critical issues

#### 2. Frontend Developer Agent (`frontend_agent.py` - 872 lines)

**Capabilities**:
- React/Vue/Next.js/Vite development
- TypeScript for type safety
- Production-ready code (NO placeholders, NO TODOs)
- GitHub-ready projects (README, .gitignore, .env.example)
- **Build error fixing using Logfire traces**

**System Prompt Highlights**:
- Write COMPLETE, WORKING code only
- Implement React optimization (React.memo, useCallback, useMemo)
- Add comprehensive error handling
- Ensure WCAG 2.1 AA accessibility
- Follow SOLID principles and DRY
- Include ALL dependencies in package.json (including devDependencies)

**Logfire Debugging** (orchestrator.py:1995-2020):
When build fails, Frontend agent:
1. Queries Logfire for deployment trace
2. Extracts exact error messages, file paths, line numbers
3. References specific trace IDs
4. Uses production telemetry (not assumptions) to identify root cause
5. Applies precise fixes

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

#### 4. QA Engineer Agent (`qa_agent.py` - 751 lines)

**Testing Criteria** (10 comprehensive checks):

1. Functional Testing
2. Usability & UX
3. Accessibility Testing (WCAG 2.1)
4. Responsive Design (mobile/tablet/desktop)
5. Performance Testing (Core Web Vitals)
6. Cross-Browser Testing
7. Edge Cases
8. Security Testing (basic)
9. Code Quality Verification
10. Production Readiness

#### 5. DevOps Engineer Agent (`devops_agent.py` - 1,272 lines)

**Capabilities**:
- GitHub repository setup and file management
- netlify.toml generation with NPM_FLAGS fix
- Netlify deployment
- **Build error detection from logs**
- **Queries Logfire for deployment failures**
- Post-deployment verification

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

**Logfire Debugging** (orchestrator.py:1912-1928):
When deployment fails, DevOps agent:
1. Queries Logfire: `span.name contains "Deploy" AND timestamp > now() - 1h`
2. Extracts deployment trace ID
3. Analyzes build logs from trace
4. Provides structured error data to Frontend agent
5. Returns exact error messages with file paths and line numbers

---

## State Management & Persistence

### PostgreSQL State Persistence

**Purpose**: Crash recovery and task resumption

**OrchestratorState Table** (`database/models.py:20-66`):
```python
class OrchestratorState(Base):
    __tablename__ = "orchestrator_state"

    # Primary Key
    phone_number: str (PK)

    # State tracking
    is_active: bool
    current_phase: str  # planning, design, implementation, review, deployment
    current_workflow: str  # full_build, bug_fix, redeploy, etc.

    # Task details
    original_prompt: str
    accumulated_refinements: JSON  # List of user refinements
    current_implementation: JSON
    current_design_spec: JSON

    # Progress tracking
    workflow_steps_completed: JSON  # List of completed steps
    workflow_steps_total: int
    current_agent_working: str  # Active agent ID
    current_task_description: str

    # Timestamps
    created_at: datetime
    updated_at: datetime
```

**State Lifecycle**:

1. **Save State** (`orchestrator.py:691-719`):
   - Called after every state change
   - Persists entire orchestrator state to PostgreSQL
   - Enables crash recovery

2. **Restore State** (`orchestrator.py:721-761`):
   - Called during orchestrator initialization
   - Checks for active state in database
   - Resumes interrupted task
   - Notifies user: "🔄 Resumed previous task!"

3. **Delete State** (`orchestrator.py:763-777`):
   - Called on task completion or cancellation
   - Cleans up database entry

**Example Recovery Flow**:
```
1. User: "Build me a todo app"
2. Orchestrator starts, saves state to DB
3. Phase: design, saves state
4. Phase: implementation, saves state
5. [Server crashes/restarts]
6. Orchestrator initializes, checks DB
7. Finds active state for user
8. Restores: phase=implementation, original_prompt="Build me a todo app"
9. Sends WhatsApp: "🔄 Resumed previous task! Phase: implementation"
10. Continues from where it left off
```

### Progress Tracking

**Dynamic Progress System** (`orchestrator.py:878-884`):

**Problem**: Progress exceeds 100% when retries/iterations exceed initial estimate

**Solution**: Dynamically adjust total steps

```python
# After completing a step
workflow_steps_completed.append(step_name)

# If approaching estimate, increase total
if len(workflow_steps_completed) >= workflow_steps_total:
    # Add 5 more steps to accommodate retries
    workflow_steps_total += 5
    save_state()  # Persist updated estimate

# Progress percentage always capped at 100%
progress_percent = min(100, (completed / total) * 100)
```

**Status Query Response** (`handle_status_query()` - 537-618):
```
📊 DETAILED TASK STATUS
========================================

🎯 Your Request:
   Build me a todo app with React and Tailwind

🔧 Workflow Details:
   • Type: full_build
   • Phase: 💻 implementation

   • Progress: [████████████░░░░░░░░] 60% (9/15 steps)

🤖 Currently Active Agent:
   👉 Frontend Developer
   📋 Task: Implement webapp using next.js, react, tailwind...
   ⏳ Status: Working...

💼 Agents Currently Deployed:
   • Designer Agent
   • Frontend Developer Agent

✅ Completed Steps:
   ✓ Designer: Create design specification
   ✓ Frontend: Initial implementation
   ✓ Designer: Review completed (Score: 8/10)
   ... and 6 more

📝 Refinements Applied: 1
   Latest: Make it dark themed...

========================================
⏳ Your request is being actively processed!
💡 Send updates anytime - I'll incorporate them!
```

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
  "available_mcp_servers": ["whatsapp", "github", "netlify", "postgres"]
}
```

**Location**: `main.py:117-131`

#### Webhook Verification

```http
GET /webhook?hub.mode=subscribe&hub.verify_token=TOKEN&hub.challenge=CHALLENGE
```

**Response** (200 OK): `CHALLENGE` (plain text)

**Response** (403 Forbidden): `"Forbidden"` (if token doesn't match)

**Location**: `main.py:134-148`

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

**Location**: `main.py:151-195`

**Important**: Returns 200 OK immediately (<5s) and processes message asynchronously (line 187)

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

**Location**: `main.py:270-298`

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

**Location**: `main.py:301-317`

#### GitHub Webhook

```http
POST /github/webhook
X-Hub-Signature-256: sha256=...
X-GitHub-Event: issue_comment
X-GitHub-Delivery: ...
Content-Type: application/json

{
  "action": "created",
  "comment": {
    "body": "@droid build me a dashboard"
  },
  ...
}
```

**Response** (200 OK):
```json
{
  "status": "processing",
  "message": "Command received and processing"
}
```

**Location**: `github_bot/webhook_handler.py:48-148`

---

## Workflow Types

### 1. Full Build Workflow

**Trigger**: "Build me a [webapp description]"

**AI Planning** (orchestrator.py:1027-1159):
- Analyzes user request
- Determines workflow type
- Selects agents needed
- Estimates complexity

**Steps** (orchestrator.py:1256-1423):
1. **Design Phase** (line 1271-1282)
   - Designer creates comprehensive design spec
   - Stores in `current_design_spec`
   - Saves state to database

2. **Implementation Phase** (line 1292-1306)
   - Frontend implements React/Next.js code
   - Uses design spec as metadata
   - Stores in `current_implementation`
   - Saves state to database

3. **Quality Loop** (line 1308-1378)
   - Designer reviews implementation vs design
   - Score 1-10, feedback list
   - If score < 9: Frontend improves, repeat review
   - Max 10 iterations
   - Final score must be ≥ 9/10

4. **Deployment Phase** (line 1382-1393)
   - Deploy with retry (max 10 attempts)
   - Build verification
   - Logfire debugging on failures
   - Frontend fixes errors between retries

5. **Response** (line 1399-1406)
   - Format WhatsApp response
   - Include: URL, design style, framework, scores, attempts
   - Delete state from database (task complete)

**Example Flow**:
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

**Steps** (orchestrator.py:1424-1479):
1. Frontend analyzes error
2. Frontend applies fixes
3. Deploy with build verification (max 10 retries)

### 3. Redeploy Workflow

**Trigger**: "Redeploy the app", "Deploy to Netlify"

**Steps** (orchestrator.py:1481-1535):
1. Direct deployment to Netlify (no code changes)

### 4. Design Only Workflow

**Trigger**: "Create a design for [description]"

**Steps** (orchestrator.py:1537-1577):
1. Designer creates design specification
2. Return design spec to user

### 5. Custom Workflow

**Trigger**: Any request not matching above patterns

**Steps** (orchestrator.py:1666-1861):
- AI-powered workflow planning
- Dynamic step routing
- Agents selected based on needs

---

## Message Handling

### Smart Message Classification

**AI-Powered Classification** (`manager.py:344-454`):

When a user sends a message while a multi-agent task is active, the system uses Claude AI to classify it:

**Classification Prompt**:
```
Context:
- An AI team is currently working on: "Build me a todo app"
- Current phase: implementation

New message from user: "Make it blue"

Your Task: Classify this message into ONE of these categories:
1. refinement - User wants to modify/refine the current task
2. status_query - User is asking about progress/status
3. cancellation - User wants to cancel/stop the current task
4. new_task - User wants to start a completely different task
5. conversation - General conversation, unrelated to the task

Output: JSON with classification, confidence, reasoning
```

**Examples**:
- "Make it blue" → refinement (0.95 confidence)
- "Add a login feature" → refinement (0.90 confidence)
- "How's it going?" → status_query (0.98 confidence)
- "Cancel" → cancellation (0.99 confidence)
- "Build a different app" → new_task (0.95 confidence)
- "Thanks!" → conversation (0.85 confidence)

### Refinement Handling

**Phase-Specific Refinement**:

**During Design Phase** (`_refine_during_design()` - 452-484):
```
User: "Build a todo app"
# Designer is creating design spec...

User: "Make it dark themed"
# System classifies as "refinement"
# Designer updates design spec with dark theme
# Continues with updated design
```

**During Implementation Phase** (`_refine_during_implementation()` - 486-523):
```
User: "Build a booking website"
# Frontend is coding...

User: "Add a calendar widget"
# System classifies as "refinement"
# Frontend adds calendar widget to code
# Continues with updated implementation
```

**During Review Phase** (`_refine_during_review()` - 525-535):
```
User: "Build a dashboard"
# Designer is reviewing code...

User: "Use Material UI instead"
# System notes refinement
# Will be applied in next improvement iteration
```

**During Deployment Phase**:
```
User: "Build a portfolio site"
# DevOps is deploying...

User: "Add a contact form"
# System queues refinement for post-deployment update
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
REDIS_URL=redis://your-redis-instance:6379
DATABASE_URL=postgresql://user:pass@host/db
LOGFIRE_TOKEN=your_logfire_token
ENABLE_LOGFIRE=true
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

6. **Configure GitHub App (Optional)**
- Go to GitHub Settings → Developer settings → GitHub Apps
- Set webhook URL: `https://your-app.onrender.com/github/webhook`
- Set webhook secret: (same as `GITHUB_WEBHOOK_SECRET`)
- Subscribe to: `issue_comment`, `pull_request`, `pull_request_review_comment`

7. **Test**
```bash
# Test health endpoint
curl https://your-app.onrender.com/health

# Send WhatsApp message
Send "Hello!" to your WhatsApp Business number

# Test GitHub bot
Post "@droid hello" in a PR comment
```

---

## Observability & Debugging

### Logfire Integration

**Dashboard**: https://logfire.pydantic.dev/
**Project**: whatsapp-mcp

**Instrumentation Points**:
- All HTTP requests (FastAPI)
- All LLM calls (Anthropic SDK)
- All external API calls (HTTPX)
- Orchestrator workflows
- A2A protocol messages
- Agent task execution
- Deployment attempts

**Key Traces**:

1. **HTTP Requests**:
   - Request method, path, headers
   - Response status, body size
   - Duration

2. **LLM Calls**:
   - Model name
   - Token usage (input/output)
   - Duration
   - Cost

3. **A2A Communications** (orchestrator.py:826-836):
   - From agent, to agent
   - Task description
   - Priority, metadata
   - Task completion status
   - Response data

4. **Deployment Attempts** (orchestrator.py:1912-1928):
   - Attempt number
   - Build errors (structured)
   - File paths, line numbers
   - Error messages

### Debugging with Logfire

**DevOps Agent Queries Logfire** (orchestrator.py:1912-1928):

When deployment fails, DevOps agent receives this in its task:

```
🔥 IMPORTANT - USE LOGFIRE FOR DEBUGGING:
- If this is a retry attempt (attempt 2+), FIRST query Logfire
- Query: span.name contains "Deploy" AND timestamp > now() - 1h
- Look for previous deployment traces to understand what went wrong
- Extract exact error messages, file paths, line numbers from traces
- Use production telemetry data (not assumptions)
- Reference specific trace IDs in your error analysis

Dashboard: https://logfire.pydantic.dev/
Project: whatsapp-mcp

If build fails:
- Query Logfire for the deployment trace
- Extract EXACT error messages from build logs
- Provide structured error data with file paths and line numbers
- Return detailed error report for Frontend to fix
```

**Frontend Agent Queries Logfire** (orchestrator.py:1995-2020):

When asked to fix build errors, Frontend agent receives:

```
🔥 IMPORTANT - USE LOGFIRE FOR DEBUGGING:
- FIRST query Logfire to see the exact error in production
- Query: agent_name = "Frontend Developer" AND result_status = "error"
- Look for your previous implementation attempt traces
- Extract exact error messages, stack traces, component names
- See what actually failed in the build (not assumptions!)
- Reference specific trace IDs in your bug fix analysis

Dashboard: https://logfire.pydantic.dev/
Project: whatsapp-mcp

Example Logfire debugging:
1. Query: span.name contains "execute_task" AND error_message contains "TypeScript"
2. Found trace: abc123 showing build failed with "Property 'title' does not exist"
3. Extract: You used album.title but data has album.name
4. Fix: Update component to use correct property names

Do NOT guess - use Logfire data to see what actually went wrong!
```

**Query Examples**:

```
# Find deployment failures in last hour
span.name contains "Deploy" AND timestamp > now() - 1h

# Find Frontend agent errors
agent_name = "Frontend Developer" AND result_status = "error"

# Find specific task executions
span.name = "A2A: orchestrator → Frontend Developer"

# Find build errors
error_message contains "Cannot find module"

# Find TypeScript errors
error_message contains "TypeScript" OR error_message contains "Property"
```

**Benefits**:
- Agents use production telemetry to debug
- No guessing - exact error messages from traces
- Reference specific trace IDs
- Understand root cause from real data
- Faster error resolution

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

**Check 4: Logfire Traces**
```
Query: span.name = "POST /webhook" AND timestamp > now() - 1h
Check if webhook requests are reaching the server
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

**Check 3: AI Classification**
```
Check Logfire traces:
Query: span.name contains "webapp detection"
See if AI correctly classified the message
```

#### 3. Build Failures on Netlify

**Symptoms**:
- Deployment succeeds but build fails
- "Cannot find module" errors

**Solutions**:

**Check 1: netlify.toml exists with NPM_FLAGS**
```toml
[build]
  command = "npm run build"
  publish = "dist"

[build.environment]
  NODE_VERSION = "18"
  NPM_FLAGS = "--include=dev"  # CRITICAL
```

**Check 2: Query Logfire for Build Errors**
```
Query: agent_name = "DevOps Engineer" AND error_message contains "Cannot find module"
Extract exact error messages from traces
```

**Check 3: All Dependencies in package.json**
```json
{
  "dependencies": {...},
  "devDependencies": {
    "vite": "^4.0.0",
    "@vitejs/plugin-react": "^3.0.0",
    ...all build tools must be here
  }
}
```

#### 4. Session Not Persisting

**Symptoms**:
- Agent forgets previous messages
- Conversation resets

**Solutions**:

**Check 1: Redis Connection**
```bash
# Test Redis connection
redis-cli -u $REDIS_URL ping
# Expected: PONG
```

**Check 2: Session TTL**
```python
# Default: 60 minutes
# Check agents/manager.py:37
session_manager = RedisSessionManager(ttl_minutes=60, max_history=10)
```

**Check 3: Redis Keys**
```bash
redis-cli -u $REDIS_URL
> KEYS session:*
> TTL session:+1234567890
```

#### 5. Orchestrator Crashed During Task

**Symptoms**:
- Task was in progress
- Server restarted/crashed
- User lost their task

**Solutions**:

**Check 1: State Persistence Enabled**
```
DATABASE_URL=postgresql://...  # Must be set
```

**Check 2: Query Database**
```sql
SELECT * FROM orchestrator_state WHERE phone_number = '+1234567890';
-- Check if state was saved
```

**Check 3: Restoration on Startup**
```
Check logs for:
"🔄 Restoring previous orchestrator state for +1234567890"
"✅ State restored (Phase: implementation, Workflow: full_build)"
```

**Check 4: User Notification**
```
User should receive WhatsApp message:
"🔄 Resumed previous task!
📋 Task: Build me a todo app...
⚙️  Phase: implementation
📊 Progress: 5/15 steps
Continuing from where we left off..."
```

#### 6. Logfire Traces Not Showing

**Symptoms**:
- No traces in Logfire dashboard
- Agents can't query Logfire for debugging

**Solutions**:

**Check 1: Logfire Token**
```
LOGFIRE_TOKEN=your_logfire_token
ENABLE_LOGFIRE=true
```

**Check 2: Instrumentation**
```python
# main.py should have:
initialize_logfire()  # Line 46
instrument_fastapi(app)  # Line 51
instrument_anthropic()  # Line 54
instrument_httpx()  # Line 57
```

**Check 3: Test Trace**
```python
from utils.telemetry import log_event
log_event("test_event", test_data="hello")
# Check Logfire dashboard for this event
```

---

## Performance & Optimization

### Current Performance Characteristics

**Latency**:
- Webhook response: <100ms (returns immediately)
- Single-agent response: 2-5 seconds
- Multi-agent webapp build: 2-10 minutes (depends on complexity)
- Quality loop iteration: 30-60 seconds per iteration
- Deployment retry: 2-3 minutes per attempt

**Memory Usage**:
- Base (FastAPI + Redis): ~200MB
- Per single agent: ~50MB
- Per orchestrator (no agents): ~100MB
- Per active agent: ~200-300MB
- Full orchestrator (5 agents): ~1.5-2GB
- With lazy initialization: ~400-600MB (only active agents)

**Throughput**:
- Max concurrent users (Redis sessions): ~100+ (distributed)
- Max concurrent orchestrators (with lazy init): 5-10 (memory limited)
- Max concurrent single agents: 50-100

**Token Usage**:
- Single-agent response: ~500-1000 tokens
- Multi-agent task: ~10,000-50,000 tokens
- AI classification: ~200-500 tokens
- AI workflow planning: ~500-1000 tokens

### Optimization Recommendations

**Implemented**:
✅ Redis for sessions (distributed, auto-expiry)
✅ PostgreSQL for state persistence (crash recovery)
✅ Lazy agent initialization (70% memory reduction)
✅ Dynamic progress tracking (accurate estimates)
✅ AI classification caching (via conversation history)
✅ Logfire telemetry (debugging with production data)

**High Priority**:
1. **Agent connection pooling** - Reuse Claude SDK connections
2. **Parallel agent initialization** - Spin up multiple agents concurrently
3. **Smart context trimming** - Reduce token usage by 30%
4. **Circuit breaker** - Prevent cascading failures

**Medium Priority**:
5. **Response caching** - Cache common queries
6. **Rate limiting** - Per-user rate limits
7. **Queue system** - For high-volume deployments
8. **Monitoring alerts** - Automated issue detection

---

## Security

### Best Practices

**1. API Key Management**
- Never commit API keys to git
- Use environment variables only
- Rotate keys regularly
- Use separate keys for dev/prod

**2. Webhook Verification**

**WhatsApp** (`main.py:134-148`):
```python
if token != os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN'):
    return PlainTextResponse("Forbidden", status_code=403)
```

**GitHub** (`webhook_handler.py:84-86`):
```python
if not verify_github_signature(body, signature, webhook_secret):
    raise HTTPException(status_code=403, detail="Invalid signature")
```

**3. Input Validation**
- Sanitize user input
- Limit message length (WhatsApp max: 4096 chars)
- Validate phone numbers
- Parse JSON safely

**4. HTTPS Only**
- Always use HTTPS in production
- Configure in deployment platform
- WhatsApp webhooks require HTTPS

**5. Rate Limiting**
- Implement per-user rate limits
- Protect against abuse
- Use Redis for distributed rate limiting

**6. Secret Storage**
- Use environment variables
- Never hardcode secrets
- Use secret management service (Render secrets, etc.)

**7. Database Security**
- Use connection pooling
- Parameterized queries (SQLAlchemy ORM)
- Encrypt sensitive data
- Regular backups

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

# Run specific test file
pytest tests/test_orchestrator.py

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

**Test Session Persistence**:
```bash
# Send first message
curl -X POST http://localhost:8000/agent/process \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1234567890", "message": "Remember: my name is Alice"}'

# Send second message (should remember context)
curl -X POST http://localhost:8000/agent/process \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1234567890", "message": "What is my name?"}'
```

**Test Redis Connection**:
```bash
redis-cli -u $REDIS_URL
> KEYS session:*
> GET session:+1234567890
> TTL session:+1234567890
```

**Test Database State**:
```sql
-- Connect to PostgreSQL
psql $DATABASE_URL

-- Check active orchestrators
SELECT phone_number, is_active, current_phase, current_workflow
FROM orchestrator_state
WHERE is_active = true;

-- Check recent events
SELECT * FROM orchestrator_audit
ORDER BY created_at DESC
LIMIT 10;
```

---

## Appendix

### File Locations Reference

| Component | File Path | Lines | Key Sections |
|-----------|-----------|-------|--------------|
| **Entry Point** | `src/python/main.py` | 358 | 344-357 (startup) |
| **Webhook Handler** | `src/python/main.py` | 358 | 151-195 |
| **Agent Manager** | `src/python/agents/manager.py` | 496 | 142-251 (routing) |
| **Redis Session** | `src/python/agents/session_redis.py` | 196 | 57-132 |
| **Database Models** | `src/python/database/models.py` | 98 | 20-97 |
| **Orchestrator** | `src/python/agents/collaborative/orchestrator.py` | 2,239 | 1165-1423 (workflows) |
| **State Manager** | `src/python/agents/collaborative/orchestrator_state.py` | - | State persistence |
| **Designer Agent** | `src/python/agents/collaborative/designer_agent.py` | 612 | Full file |
| **Frontend Agent** | `src/python/agents/collaborative/frontend_agent.py` | 872 | Full file |
| **Code Reviewer** | `src/python/agents/collaborative/code_reviewer_agent.py` | 697 | Full file |
| **QA Agent** | `src/python/agents/collaborative/qa_agent.py` | 751 | Full file |
| **DevOps Agent** | `src/python/agents/collaborative/devops_agent.py` | 1,272 | Full file |
| **A2A Protocol** | `src/python/agents/collaborative/a2a_protocol.py` | 157 | Full file |
| **Models** | `src/python/agents/collaborative/models.py` | 127 | Full file |
| **Claude SDK** | `src/python/sdk/claude_sdk.py` | 340 | 230-275 (send) |
| **WhatsApp Client** | `src/python/whatsapp_mcp/client.py` | 191 | Full file |
| **WhatsApp Parser** | `src/python/whatsapp_mcp/parser.py` | 150 | Full file |
| **GitHub Webhook** | `src/python/github_bot/webhook_handler.py` | 275 | 48-148 |
| **GitHub Manager** | `src/python/agents/github_manager.py` | - | GitHub-specific |
| **GitHub MCP** | `src/python/github_mcp/server.py` | 113 | Full file |
| **Netlify MCP** | `src/python/netlify_mcp/server.py` | 123 | Full file |
| **PostgreSQL Helper** | `src/python/utils/pgsql_mcp_helper.py` | - | MCP config |
| **Telemetry** | `src/python/utils/telemetry.py` | 446+ | Full file |

### Data Model Reference

**Session (Redis)**:
```python
{
    "phone_number": str,
    "conversation_history": [
        {"role": "user" | "assistant", "content": str, "timestamp": ISO}
    ],
    "created_at": ISO datetime,
    "last_active": ISO datetime
}
# Key: session:{phone_number}
# TTL: 60 minutes
```

**OrchestratorState (PostgreSQL)**:
```python
{
    "phone_number": str (PK),
    "is_active": bool,
    "current_phase": str,
    "current_workflow": str,
    "original_prompt": str,
    "accumulated_refinements": List[str],
    "current_implementation": Dict,
    "current_design_spec": Dict,
    "workflow_steps_completed": List[str],
    "workflow_steps_total": int,
    "current_agent_working": str,
    "current_task_description": str,
    "created_at": datetime,
    "updated_at": datetime
}
```

**AgentCard (A2A Protocol)**:
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

**Task (A2A Protocol)**:
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
**Logfire**: Query traces for debugging

### Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Make changes
4. Run tests: `pytest tests/`
5. Commit: `git commit -m "Add my feature"`
6. Push: `git push origin feature/my-feature`
7. Create Pull Request

---

**Last Updated:** January 2025
**Version:** 2.2.0
**Documentation Status:** ✅ Current (matches codebase)

**Key Improvements in v2.2.0:**
- ✅ Added Redis session persistence
- ✅ Added PostgreSQL state persistence (crash recovery)
- ✅ Added GitHub bot webhook integration
- ✅ Added Logfire debugging capabilities (agents query production traces)
- ✅ Added dynamic progress tracking
- ✅ Updated architecture diagrams
- ✅ Enhanced troubleshooting section
- ✅ Added observability & debugging section
- ✅ Corrected all file line numbers
- ✅ Added platform-agnostic design documentation
