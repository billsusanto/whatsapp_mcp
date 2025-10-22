# WhatsApp MCP - Codebase Map & Analysis

**Generated:** 2025-10-22
**Last Updated:** 2025-10-22 (Added WhatsApp notifications & enhanced Designer agent)
**Purpose:** Comprehensive documentation of the WhatsApp Multi-Agent System codebase

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Directory Structure](#directory-structure)
3. [Core Architecture](#core-architecture)
4. [Key Files & Components](#key-files--components)
5. [Data Flow](#data-flow)
6. [Dependencies](#dependencies)
7. [Important Data Structures](#important-data-structures)
8. [Entry Points](#entry-points)
9. [Configuration](#configuration)

---

## Project Overview

### What This System Does
A WhatsApp-integrated AI assistant system that uses:
- **Claude Agent SDK** for AI capabilities
- **Model Context Protocol (MCP)** for extensible tool integration
- **Multi-agent collaborative system** for complex webapp building tasks
- **Agent-to-Agent (A2A) Protocol** for standardized inter-agent communication

### Key Capabilities
1. **Single-Agent Mode**: Personal assistant for individual WhatsApp users
2. **Multi-Agent Mode**: Collaborative team of specialized AI agents for webapp development
3. **Real-Time WhatsApp Notifications**: Live updates on agent activities and task progress
4. **MCP Integration**: WhatsApp, GitHub, and Netlify tools
5. **Session Management**: Conversation history per user with auto-cleanup
6. **Deployment**: Automated Netlify deployment with build verification
7. **Enhanced Design Review**: Designer agent reviews both design specs AND frontend code

---

## Directory Structure

```
whatsapp_mcp/
├── src/python/                      # Main source code
│   ├── main.py                      # FastAPI application entry point
│   ├── agents/                      # Agent system
│   │   ├── manager.py               # Agent lifecycle management
│   │   ├── agent.py                 # Individual agent wrapper
│   │   ├── session.py               # Session management
│   │   └── collaborative/           # Multi-agent system
│   │       ├── orchestrator.py      # Workflow coordination
│   │       ├── base_agent.py        # Base agent class
│   │       ├── a2a_protocol.py      # A2A communication
│   │       ├── models.py            # Data models
│   │       ├── designer_agent.py    # UI/UX design
│   │       ├── frontend_agent.py    # Frontend development
│   │       ├── code_reviewer_agent.py
│   │       ├── qa_agent.py
│   │       └── devops_agent.py
│   ├── sdk/                         # SDK wrappers
│   │   └── claude_sdk.py            # Claude Agent SDK wrapper
│   ├── whatsapp_mcp/                # WhatsApp integration
│   │   ├── client.py                # WhatsApp Business API client
│   │   └── parser.py                # Webhook parser
│   ├── github_mcp/                  # GitHub MCP server
│   │   └── server.py
│   ├── netlify_mcp/                 # Netlify MCP server
│   │   └── server.py
│   └── utils/                       # Utilities
│       ├── config.py
│       └── logger.py
├── tests/                           # Test suite
│   ├── test_a2a_protocol.py
│   ├── test_claude_sdk.py
│   ├── test_orchestrator.py
│   └── ...
├── requirements.txt                 # Python dependencies
├── docker-compose.yml               # Docker configuration
├── render.yaml                      # Render deployment config
└── .env                             # Environment variables
```

---

## Core Architecture

### High-Level Flow

```
WhatsApp User
     ↓
  Webhook → main.py (FastAPI)
     ↓
  AgentManager
     ↓
  ┌──────────────────┐
  │ Single Agent?    │ → Agent → ClaudeSDK → Claude API
  │ Multi-Agent?     │ → Orchestrator → Multiple Specialized Agents
  └──────────────────┘
     ↓
  WhatsApp Response
```

### Agent Hierarchy

```
AgentManager (manager.py:24)
    ├─→ Agent (agent.py:16) - Single-user conversations
    │     └─→ ClaudeSDK (claude_sdk.py:12)
    │           └─→ ClaudeAgentOptions + MCP Servers
    │
    └─→ CollaborativeOrchestrator (orchestrator.py:23) - Multi-agent workflows
          ├─→ DesignerAgent (lazy initialization)
          ├─→ FrontendDeveloperAgent
          ├─→ CodeReviewerAgent
          ├─→ QAEngineerAgent
          └─→ DevOpsEngineerAgent

          All communicate via A2A Protocol (a2a_protocol.py:14)
```

---

## Key Files & Components

### 1. Entry Point: `src/python/main.py`

**Purpose:** FastAPI application handling WhatsApp webhooks

**Key Functions:**

| Line | Function | Purpose |
|------|----------|---------|
| 76-83 | `root()` | Health check endpoint for Render |
| 86-100 | `health_check()` | Detailed service status |
| 103-117 | `webhook_verify()` | WhatsApp webhook verification (GET) |
| 120-155 | `webhook_receive()` | Incoming message handler (POST) |
| 158-181 | `process_whatsapp_message()` | Async message processing |
| 184-204 | `periodic_cleanup()` | Background cleanup task |
| 207-235 | `process_message()` | Direct message endpoint (testing) |
| 257-270 | `startup_event()` | Initialize service and background tasks |

**Key Variables:**
- Line 32: `whatsapp_client` - WhatsApp Business API client
- Line 35: `whatsapp_send_tool` - MCP tool decorator
- Line 60: `agent_manager` - Central agent coordinator

**Dependencies:**
- FastAPI, Pydantic
- WhatsAppClient, WhatsAppWebhookParser
- AgentManager
- claude_agent_sdk tools

---

### 2. Agent Management: `src/python/agents/manager.py`

**Purpose:** Manages lifecycle of multiple Claude agents (one per user)

**Key Classes & Methods:**

| Line | Component | Purpose |
|------|-----------|---------|
| 24-108 | `AgentManager.__init__()` | Initialize manager with MCP servers |
| 109-128 | `get_or_create_agent()` | Lazy agent creation per user |
| 130-162 | `process_message()` | Route to single/multi-agent |
| 164-253 | `_is_webapp_request()` | AI-powered intent detection |
| 255-268 | `stream_response()` | Streaming support |
| 275-280 | `cleanup_agent()` | Agent resource cleanup |
| 288-294 | `get_active_agents_count()` | Active agent count |

**Key Features:**
- **Multi-Agent Detection**: Uses Claude to intelligently detect webapp build requests (line 164-253)
- **MCP Server Configuration**: Dynamically loads WhatsApp, GitHub, Netlify MCPs (lines 42-88)
- **Orchestrator Integration**: Routes complex tasks to multi-agent system (lines 94-103)

---

### 3. Individual Agent: `src/python/agents/agent.py`

**Purpose:** Single agent instance for individual user conversations

**Key Methods:**

| Line | Function | Purpose |
|------|----------|---------|
| 19-49 | `__init__()` | Initialize agent with MCP servers |
| 51-78 | `process_message()` | Process user message with history |
| 80-108 | `stream_response()` | Stream response chunks |
| 110-113 | `reset_conversation()` | Clear conversation history |
| 115-118 | `cleanup()` | Release resources |

**Key Features:**
- Session management integration (lines 62-72)
- Conversation history tracking
- Claude SDK wrapper usage

---

### 4. Session Management: `src/python/agents/session.py`

**Purpose:** Track conversation history per WhatsApp user

**Key Classes & Methods:**

| Line | Component | Purpose |
|------|-----------|---------|
| 11-25 | `SessionManager.__init__()` | Initialize with TTL and max history |
| 27-47 | `get_session()` | Get or create user session |
| 49-74 | `add_message()` | Add message to history with auto-trim |
| 76-84 | `get_conversation_history()` | Retrieve message history |
| 86-90 | `clear_session()` | Delete session |
| 92-112 | `cleanup_expired_sessions()` | Remove inactive sessions |

**Configuration:**
- TTL: 60 minutes (configurable in manager.py:37)
- Max history: 10 messages (prevents token overflow)

---

### 5. Claude SDK Wrapper: `src/python/sdk/claude_sdk.py`

**Purpose:** Wrapper around Claude Agent SDK with MCP support

**Key Methods:**

| Line | Function | Purpose |
|------|----------|---------|
| 15-111 | `__init__()` | Initialize SDK with MCP servers and system prompt |
| 113-180 | `initialize_client()` | Setup async client with MCP configuration |
| 182-227 | `send_message()` | Send message and get response |
| 229-267 | `stream_message()` | Stream response chunks |
| 269-276 | `close()` | Cleanup client |

**MCP Integration:**
- Lines 44-51: WhatsApp MCP prompt enhancement
- Lines 54-69: GitHub MCP prompt enhancement
- Lines 73-100: Netlify MCP prompt enhancement
- Lines 122-147: Dynamic MCP server registration

**Configuration:**
- Model: `claude-sonnet-4-5-20250929` (line 104)
- Max tokens: 4096 (line 105)
- Permission mode: `bypassPermissions` (line 156)

---

### 6. Multi-Agent Orchestrator: `src/python/agents/collaborative/orchestrator.py`

**Purpose:** Coordinates multi-agent webapp development team with real-time WhatsApp notifications

**Key Methods:**

| Line | Function | Purpose |
|------|-----------|---------|
| 58-118 | `__init__(user_phone_number)` | Initialize orchestrator with WhatsApp notifications |
| 124-169 | `_get_agent()` | Lazy agent instantiation on-demand |
| 171-198 | `_cleanup_agent()` | Free agent resources |
| 226-238 | `_send_whatsapp_notification()` | Send WhatsApp updates to user |
| 240-255 | `_get_agent_type_name()` | Map agent IDs to human-readable names |
| 276-339 | `_send_task_to_agent()` | A2A task delegation **with notifications** |
| 341-395 | `_request_review_from_agent()` | A2A review request **with notifications** |
| 401-533 | `_ai_plan_workflow()` | AI-powered workflow planning |
| 539-598 | `build_webapp()` | Main entry point **with initial acknowledgment** |
| 600-738 | `_workflow_full_build()` | Complete webapp build workflow |
| 740-788 | `_workflow_bug_fix()` | Bug fix workflow |
| 790-839 | `_workflow_redeploy()` | Redeploy existing code |
| 841-878 | `_workflow_design_only()` | Design specification only |
| 967-1158 | `_workflow_custom()` | AI-planned custom workflow |
| 1172-1241 | `_deploy_with_retry()` | Deploy with build verification |

**Workflow Types:**
1. **full_build** (line 600): Designer → Frontend → Review Loop → Deploy
2. **bug_fix** (line 740): Frontend fixes → Deploy
3. **redeploy** (line 790): Direct deployment
4. **design_only** (line 841): Designer only
5. **custom** (line 967): AI-planned steps

**Key Features:**
- **Lazy Initialization**: Agents created on-demand (line 124)
- **WhatsApp Notifications**: Real-time updates to user on agent activities (lines 226-255)
  - Initial acknowledgment when workflow starts
  - Agent-to-Agent communication notifications
  - Task completion notifications
  - Review score notifications
- **Quality Loop**: Iterative improvement until score ≥ 9/10 (lines 643-709)
- **Build Retry**: Auto-fix build errors up to 5 attempts (lines 1172-1241)
- **AI Planning**: Claude decides workflow and steps (lines 401-533)
- **Agent Access Fix**: All agent references use constant IDs (DESIGNER_ID, FRONTEND_ID, etc.)

**Agent IDs:**
- `ORCHESTRATOR_ID = "orchestrator"` (line 49)
- `DESIGNER_ID = "designer_001"` (line 52)
- `FRONTEND_ID = "frontend_001"` (line 53)
- `CODE_REVIEWER_ID = "code_reviewer_001"` (line 54)
- `QA_ID = "qa_engineer_001"` (line 55)
- `DEVOPS_ID = "devops_001"` (line 56)

---

### 7. Base Agent Class: `src/python/agents/collaborative/base_agent.py`

**Purpose:** Abstract base for all specialized agents

**Key Methods:**

| Line | Function | Purpose |
|------|-----------|---------|
| 27-55 | `__init__()` | Initialize base agent with A2A registration |
| 57-82 | `receive_message()` | Route incoming A2A messages |
| 84-100 | `handle_task_request()` | Handle task execution requests |
| 102-111 | `handle_review_request()` | Handle review requests |
| 113-122 | `handle_question()` | Handle questions |
| 124-135 | `execute_task()` | **Abstract** - Must be implemented by subclass |
| 137-148 | `review_artifact()` | **Abstract** - Must be implemented by subclass |
| 150-180 | `send_task_to()` | Send task to another agent |
| 182-201 | `request_review_from()` | Request review from another agent |
| 203-207 | `cleanup()` | Release resources |

**Specializations:**
All inherit from BaseAgent and implement `execute_task()` and `review_artifact()`:
- `DesignerAgent` (designer_agent.py)
- `FrontendDeveloperAgent` (frontend_agent.py)
- `CodeReviewerAgent` (code_reviewer_agent.py)
- `QAEngineerAgent` (qa_agent.py)
- `DevOpsEngineerAgent` (devops_agent.py)

---

### 7.1. Designer Agent: `src/python/agents/collaborative/designer_agent.py`

**Purpose:** UI/UX Designer that creates design specifications AND reviews frontend code implementation

**Key Methods:**

| Line | Function | Purpose |
|------|----------|---------|
| 14-61 | `__init__()` | Initialize designer with dual-role system prompt |
| 63-181 | `execute_task()` | Create comprehensive design specifications |
| 183-281 | `review_artifact()` | Review frontend code against design spec |

**Enhanced Capabilities (Updated):**
```python
capabilities=[
    "Design system creation",
    "Wireframing",
    "Color scheme design",
    "Typography specification",
    "Component design",
    "Accessibility review",
    "Responsive design",
    "Frontend code review",           # ✅ NEW
    "Design fidelity verification"    # ✅ NEW
]
```

**System Prompt Enhancement (Lines 36-68):**
The Designer agent now has a **dual role**:
1. **Design Creation**: Create comprehensive design specifications with exact values
2. **Code Review**: Review frontend implementations to ensure they match design specs

**Review Process (Lines 195-260):**
When reviewing implementation, the Designer agent:
1. **Compares Design Spec vs Code**:
   - Checks if hex color codes in design match CSS/Tailwind values
   - Verifies typography (fonts, sizes, weights) are correctly implemented
   - Validates spacing values (margins, padding) match design system
   - Ensures components match specifications

2. **Validates Code Quality**:
   - CSS/Tailwind classes correctly implement design
   - Design tokens/variables properly defined
   - Font families correctly imported and applied
   - Responsive breakpoints match design spec

3. **Checks Accessibility in Code**:
   - ARIA labels present in JSX/HTML
   - Color contrast values from design spec
   - Keyboard navigation support
   - Semantic HTML elements

4. **Provides Detailed Feedback**:
   - Specific file names and line numbers
   - Code-level suggestions
   - Critical issues that don't match design spec

**Scoring Criteria (Line 244-250):**
- 10: Perfect implementation, matches design spec exactly
- 9: Excellent, minor tweaks needed
- 8: Good, a few improvements needed
- 7: Acceptable, several issues to fix
- 6: Below standard, significant changes required
- 5 or below: Major redesign/reimplementation needed

**Example Review Output:**
```json
{
  "approved": false,
  "score": 7,
  "feedback": [
    "Primary color in App.jsx line 25 uses #4287F5 instead of spec's #3B82F6",
    "Font family not imported - missing Google Fonts link for 'Inter'",
    "Spacing inconsistent - using p-3 instead of design system's p-4"
  ],
  "critical_issues": [
    "Color mismatch breaks brand consistency",
    "Missing font import will cause fallback to system fonts"
  ],
  "suggestions": [
    "Add hover states to buttons for better UX",
    "Consider adding dark mode variants"
  ],
  "iteration": 1
}
```

---

### 8. A2A Protocol: `src/python/agents/collaborative/a2a_protocol.py`

**Purpose:** Agent-to-Agent communication protocol implementation

**Key Classes & Methods:**

| Line | Component | Purpose |
|------|-----------|---------|
| 14-26 | `A2AProtocol.__init__()` | Initialize protocol |
| 27-30 | `register_agent()` | Register agent for communication |
| 32-36 | `unregister_agent()` | Unregister agent |
| 38-82 | `send_message()` | Send A2A message between agents |
| 84-112 | `send_task()` | Send task and wait for completion |
| 114-140 | `request_review()` | Request artifact review |
| 142-145 | `get_agent_card()` | Agent discovery |
| 147-153 | `discover_agents_by_role()` | Find agents by role |

**Singleton Instance:**
- Line 157: `a2a_protocol = A2AProtocol()` - Global instance for in-memory communication

---

### 9. Data Models: `src/python/agents/collaborative/models.py`

**Purpose:** Pydantic models for A2A protocol and domain objects

**Key Models:**

| Line | Model | Purpose |
|------|-------|---------|
| 12-20 | `AgentRole` | Agent role enumeration |
| 22-30 | `MessageType` | A2A message types |
| 33-39 | `TaskStatus` | Task execution status |
| 43-56 | `AgentCard` | Agent capabilities (discovery) |
| 59-71 | `A2AMessage` | Standardized agent message |
| 74-86 | `Task` | Task request model |
| 88-99 | `TaskResponse` | Task response model |
| 102-111 | `DesignSpecification` | Design spec from designer |
| 113-120 | `WebappImplementation` | Frontend implementation |
| 122-128 | `DesignReview` | Design review feedback |

---

### 10. WhatsApp Client: `src/python/whatsapp_mcp/client.py`

**Purpose:** WhatsApp Business Cloud API integration

**Key Methods:**

| Line | Function | Purpose |
|------|----------|---------|
| 15-29 | `__init__()` | Initialize with credentials from env |
| 31-70 | `send_message()` | Send text message to user |
| 72-100 | `mark_as_read()` | Mark message as read |
| 102-124 | `get_media()` | Get media file info |
| 126-147 | `download_media()` | Download media file |

**API Configuration:**
- API version: v18.0 (line 25)
- Base URL: `https://graph.facebook.com/v18.0/{phone_number_id}` (line 26)

---

### 11. WhatsApp Parser: `src/python/whatsapp_mcp/parser.py`

**Purpose:** Parse incoming WhatsApp webhook payloads

**Key Methods:**

| Line | Function | Purpose |
|------|----------|---------|
| 14-110 | `parse_message()` | Extract message data from webhook |
| 113-136 | `is_status_update()` | Check if webhook is status update |
| 139-151 | `extract_sender()` | Get sender phone number |

**Supported Message Types:**
- Text (lines 66-68)
- Image (lines 70-77)
- Video (lines 79-86)
- Audio (lines 88-94)
- Document (lines 96-104)

---

## Data Flow

### 1. WhatsApp Message → Agent Response

```
1. WhatsApp User sends message
   ↓
2. WhatsApp Cloud API sends webhook to /webhook (POST)
   ↓ main.py:120 webhook_receive()
3. WhatsAppWebhookParser.parse_message() extracts data
   ↓ parser.py:14
4. process_whatsapp_message() spawned async
   ↓ main.py:158
5. AgentManager.process_message()
   ↓ manager.py:130
6. Decision: Single agent or Multi-agent?
   ├─→ Single: Agent.process_message()
   │      ↓ agent.py:51
   │   ClaudeSDK.send_message()
   │      ↓ claude_sdk.py:182
   │   Claude API response
   │
   └─→ Multi: Orchestrator.build_webapp()
          ↓ orchestrator.py:452
       AI Planning (workflow decision)
          ↓ orchestrator.py:314
       Execute workflow (Designer → Frontend → Review → Deploy)
          ↓ A2A Protocol communication
       Deployment via Netlify MCP

7. Response sent back via WhatsApp
   ↓ whatsapp_client.send_message()
```

### 2. Multi-Agent Workflow (Full Build) with Real-Time Notifications

```
Orchestrator
   ↓ _ai_plan_workflow() - Decide workflow type
   ↓
   ↓ 📱 WhatsApp: "🚀 Request received! Multi-agent team processing..."
   ↓ 📱 WhatsApp: "🧠 AI Planning Complete - Workflow: full_build"
   ↓
   ↓ _workflow_full_build()
   ↓
   ├─→ Step 1: Designer creates design spec
   │      ↓ 📱 WhatsApp: "🤖 Orchestrator → UI/UX Designer"
   │      ↓              "📋 Task: Create design specification..."
   │      ↓ _send_task_to_agent(DESIGNER_ID)
   │      ↓ A2A Protocol → DesignerAgent.execute_task()
   │      ↓ Claude generates design specification
   │      ↓ 📱 WhatsApp: "✅ Task Done by: UI/UX Designer"
   │
   ├─→ Step 2: Frontend implements design
   │      ↓ 📱 WhatsApp: "🤖 Orchestrator → Frontend Developer"
   │      ↓              "📋 Task: Implement webapp using next.js..."
   │      ↓ _send_task_to_agent(FRONTEND_ID)
   │      ↓ A2A Protocol → FrontendAgent.execute_task()
   │      ↓ Claude generates React/Vue code
   │      ↓ 📱 WhatsApp: "✅ Task Done by: Frontend Developer"
   │
   ├─→ Step 3: Quality loop (iterative improvement)
   │      ↓ While score < 9/10 and iterations < 10:
   │      ↓   📱 WhatsApp: "🔍 Orchestrator → UI/UX Designer"
   │      ↓                "📋 Requesting review of implementation..."
   │      ↓   Designer reviews implementation (compares code vs design spec)
   │      ↓   _request_review_from_agent(DESIGNER_ID)
   │      ↓   📱 WhatsApp: "✅ Review Done by: UI/UX Designer"
   │      ↓                "📊 Score: 7/10 - ⚠️ Needs improvement"
   │      ↓   If not approved:
   │      ↓     📱 WhatsApp: "🤖 Orchestrator → Frontend Developer"
   │      ↓                  "📋 Task: Improve implementation..."
   │      ↓     Frontend improves code
   │      ↓     _send_task_to_agent(FRONTEND_ID, improvements)
   │      ↓     📱 WhatsApp: "✅ Task Done by: Frontend Developer"
   │
   ├─→ Step 4: Deploy with retry
   │      ↓ _deploy_with_retry()
   │      ↓ While attempts < 5:
   │      ↓   Try deploy via Netlify MCP
   │      ↓   Check build logs for errors
   │      ↓   If build failed:
   │      ↓     📱 WhatsApp: "🤖 Orchestrator → Frontend Developer"
   │      ↓                  "📋 Task: Fix build errors..."
   │      ↓     Frontend fixes errors
   │      ↓     _send_task_to_agent(FRONTEND_ID, fix errors)
   │      ↓     📱 WhatsApp: "✅ Task Done by: Frontend Developer"
   │      ↓   If build succeeds: break
   │
   └─→ Step 5: Format and return response
          ↓ _format_whatsapp_response()
          ↓ 📱 WhatsApp: "✅ Your webapp is ready!"
          ↓              "🔗 Live Site: https://..."
          ↓ Return deployment URL + metadata
```

### 3. Session Management Flow

```
User sends message
   ↓
SessionManager.get_session(phone_number)
   ↓
If session exists:
   └─→ Update last_active timestamp

If session doesn't exist:
   └─→ Create new session with empty history

SessionManager.add_message(phone_number, role, content)
   ↓
Append to conversation_history
   ↓
If history.length > max_history (10):
   └─→ Trim to most recent 10 messages

SessionManager.get_conversation_history(phone_number)
   ↓
Return list of messages
   ↓
Pass to Claude SDK for context

Background cleanup (every 60 minutes):
   ↓
SessionManager.cleanup_expired_sessions()
   ↓
For each session:
   If (now - last_active) > TTL (60 minutes):
      └─→ Delete session
```

---

## Dependencies

### Python Dependencies (requirements.txt)

| Package | Version | Purpose |
|---------|---------|---------|
| claude-agent-sdk | ≥0.1.0 | Official Claude Agent SDK |
| anthropic | ≥0.18.0 | Anthropic Claude API |
| requests | ≥2.31.0 | HTTP requests (WhatsApp API) |
| python-dotenv | ≥1.0.0 | Environment variables |
| pydantic | ≥2.0.0 | Data validation |
| fastapi | ≥0.104.0 | REST API framework |
| uvicorn[standard] | ≥0.24.0 | ASGI server |
| mcp | ≥1.18.0 | Model Context Protocol SDK |
| aiohttp | ≥3.9.0 | Async HTTP (A2A protocol) |
| typing-extensions | ≥4.14.1 | Type hints |

### Internal Module Dependencies

```
main.py
  ├─→ agents.manager (AgentManager)
  ├─→ whatsapp_mcp.client (WhatsAppClient)
  ├─→ whatsapp_mcp.parser (WhatsAppWebhookParser)
  └─→ claude_agent_sdk (tool decorator)

agents/manager.py
  ├─→ agents.agent (Agent)
  ├─→ agents.session (SessionManager)
  ├─→ agents.collaborative.orchestrator (CollaborativeOrchestrator)
  ├─→ github_mcp.server
  └─→ netlify_mcp.server

agents/agent.py
  ├─→ sdk.claude_sdk (ClaudeSDK)
  └─→ agents.session (SessionManager)

agents/collaborative/orchestrator.py
  ├─→ sdk.claude_sdk (ClaudeSDK)
  ├─→ agents.collaborative.designer_agent (DesignerAgent)
  ├─→ agents.collaborative.frontend_agent (FrontendDeveloperAgent)
  ├─→ agents.collaborative.code_reviewer_agent (CodeReviewerAgent)
  ├─→ agents.collaborative.qa_agent (QAEngineerAgent)
  ├─→ agents.collaborative.devops_agent (DevOpsEngineerAgent)
  ├─→ agents.collaborative.models (Task, TaskResponse, etc.)
  └─→ agents.collaborative.a2a_protocol (a2a_protocol)

agents/collaborative/base_agent.py
  ├─→ sdk.claude_sdk (ClaudeSDK)
  ├─→ agents.collaborative.models (AgentCard, A2AMessage, Task, TaskResponse)
  └─→ agents.collaborative.a2a_protocol (a2a_protocol)

sdk/claude_sdk.py
  └─→ claude_agent_sdk (ClaudeSDKClient, ClaudeAgentOptions, create_sdk_mcp_server)
```

---

## Important Data Structures

### 1. Session Structure

```python
{
    "phone_number": str,              # User's WhatsApp number
    "conversation_history": [         # List of messages
        {
            "role": "user" | "assistant",
            "content": str,
            "timestamp": str (ISO format)
        }
    ],
    "created_at": datetime,
    "last_active": datetime
}
```

### 2. Agent Card (A2A Discovery)

```python
{
    "agent_id": str,                  # Unique agent identifier
    "name": str,                      # Human-readable name
    "role": AgentRole,                # DESIGNER, FRONTEND, etc.
    "description": str,               # Agent capabilities
    "version": str,                   # Agent version
    "capabilities": List[str],        # List of capabilities
    "skills": Dict[str, List[str]],  # Categorized skills
    "endpoint": Optional[str]         # API endpoint (if HTTP-based)
}
```

### 3. A2A Message

```python
{
    "message_id": str,                # Unique message ID
    "from_agent": str,                # Sender agent ID
    "to_agent": str,                  # Recipient agent ID
    "message_type": MessageType,      # TASK_REQUEST, REVIEW_REQUEST, etc.
    "content": Dict[str, Any],        # Message payload
    "timestamp": str,                 # ISO format
    "metadata": Optional[Dict]        # Optional metadata
}
```

### 4. Task Model

```python
{
    "task_id": str,                   # Unique task ID
    "description": str,               # What needs to be done
    "from_agent": str,                # Requesting agent
    "to_agent": str,                  # Executing agent
    "priority": str,                  # low, medium, high
    "status": TaskStatus,             # PENDING, IN_PROGRESS, COMPLETED, FAILED
    "metadata": Optional[Dict]        # Additional context
}
```

### 5. Design Specification

```python
{
    "style": str,                     # modern, minimal, bold, playful
    "colors": Dict[str, str],         # Color palette (hex codes)
    "typography": Dict[str, Any],     # Font families, scales
    "components": List[Dict],         # Component specifications
    "layout_description": str,        # Layout structure
    "design_tokens": Dict[str, str], # CSS custom properties
    "accessibility_notes": List[str]  # Accessibility requirements
}
```

### 6. Webapp Implementation

```python
{
    "framework": str,                 # react, vue, next.js
    "files": [                        # List of code files
        {
            "path": str,              # File path (e.g., "src/App.jsx")
            "content": str            # File content
        }
    ],
    "dependencies": Dict[str, str],   # package.json dependencies
    "build_command": str,             # Build command (e.g., "npm run build")
    "output_directory": str           # Build output directory
}
```

### 7. MCP Server Configuration

```python
# For SDK tools (e.g., WhatsApp)
{
    "whatsapp": [tool_function_1, tool_function_2, ...]
}

# For HTTP-based MCP (e.g., GitHub, Netlify)
{
    "github": {
        "command": "npx",
        "args": ["@modelcontextprotocol/server-github"],
        "env": {
            "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_..."
        }
    }
}
```

---

## Entry Points

### 1. Production Entry Point

**File:** `src/python/main.py`
**Line:** 281-294

```python
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")
```

**Environment Variable:** `PORT` (defaults to 8000)

### 2. API Endpoints

| Endpoint | Method | Handler | Purpose |
|----------|--------|---------|---------|
| `/` | GET | `root()` | Health check |
| `/health` | GET | `health_check()` | Detailed status |
| `/webhook` | GET | `webhook_verify()` | WhatsApp webhook verification |
| `/webhook` | POST | `webhook_receive()` | Incoming messages |
| `/agent/process` | POST | `process_message()` | Direct message (testing) |
| `/agent/reset/{phone_number}` | POST | `reset_session()` | Reset conversation |

### 3. Background Tasks

**Startup Tasks** (main.py:257-270):
- Initialize MCP servers
- Start periodic cleanup task (runs every 60 minutes)

**Cleanup Task** (main.py:184-204):
- Runs every 60 minutes
- Cleans up expired sessions (TTL > 60 minutes)
- Logs cleanup statistics

### 4. Workflow Entry Points

**Single Agent Workflow:**
- Entry: `AgentManager.process_message()` (manager.py:130)
- Condition: Regular conversation (not webapp request)
- Handler: `Agent.process_message()` (agent.py:51)

**Multi-Agent Workflow:**
- Entry: `AgentManager.process_message()` (manager.py:130)
- Condition: Webapp build request detected by AI (manager.py:145)
- Handler: `CollaborativeOrchestrator.build_webapp()` (orchestrator.py:452)

---

## Configuration

### Environment Variables (.env)

| Variable | Required | Purpose |
|----------|----------|---------|
| `ANTHROPIC_API_KEY` | ✅ Yes | Claude API authentication |
| `WHATSAPP_ACCESS_TOKEN` | ✅ Yes | WhatsApp Business API token |
| `WHATSAPP_PERMANENT_TOKEN` | ⚠️ Optional | Permanent WhatsApp token |
| `WHATSAPP_BUSINESS_ACCOUNT_ID` | ✅ Yes | WhatsApp Business Account ID |
| `WHATSAPP_PHONE_NUMBER_ID` | ✅ Yes | Phone number for sending/receiving |
| `WHATSAPP_WEBHOOK_VERIFY_TOKEN` | ✅ Yes | Webhook verification token |
| `AGENT_SYSTEM_PROMPT` | ⚠️ Optional | Custom system prompt for agents |
| `GITHUB_PERSONAL_ACCESS_TOKEN` | ⚠️ Optional | GitHub MCP integration |
| `ENABLE_GITHUB_MCP` | ⚠️ Optional | Enable GitHub MCP (true/false) |
| `NETLIFY_PERSONAL_ACCESS_TOKEN` | ⚠️ Optional | Netlify MCP integration |
| `ENABLE_NETLIFY_MCP` | ⚠️ Optional | Enable Netlify MCP (true/false) |
| `PORT` | ⚠️ Optional | Server port (default: 8000) |

### System Configuration

**Session Manager** (session.py:14):
- TTL: 60 minutes (set in manager.py:37)
- Max history: 10 messages (prevents token overflow)

**Claude SDK** (claude_sdk.py):
- Model: `claude-sonnet-4-5-20250929` (line 104)
- Max tokens: 4096 (line 105)
- Permission mode: `bypassPermissions` (auto-approve tools)

**Orchestrator** (orchestrator.py):
- Max review iterations: 10 (line 106)
- Min quality score: 9/10 (line 107)
- Max build retries: 5 (line 108)
- Agent caching: Disabled by default (line 109)

**WhatsApp API** (whatsapp_mcp/client.py):
- API version: v18.0 (line 25)
- Base URL: `https://graph.facebook.com/v18.0/{phone_number_id}`

### Deployment Configuration

**Render** (render.yaml):
- Service type: Web Service
- Build command: `pip install -r requirements.txt`
- Start command: `python src/python/main.py`

**Docker** (docker-compose.yml):
- Container orchestration for local development
- Port mapping: 8000:8000

---

## Key Relationships & Dependencies

### 1. Agent Lifecycle

```
AgentManager (manager.py)
    creates → Agent (agent.py) - one per phone number
    creates → CollaborativeOrchestrator (orchestrator.py) - one singleton

Agent
    uses → SessionManager (session.py) - shared across all agents
    uses → ClaudeSDK (claude_sdk.py) - one per agent

CollaborativeOrchestrator
    creates → Specialized Agents (lazy initialization)
        - DesignerAgent
        - FrontendDeveloperAgent
        - CodeReviewerAgent
        - QAEngineerAgent
        - DevOpsEngineerAgent

    All agents inherit from → BaseAgent (base_agent.py)
    All agents communicate via → A2A Protocol (a2a_protocol.py)
```

### 2. MCP Integration Points

```
main.py
    ├─→ Creates @tool decorated functions (line 35)
    └─→ Passes to AgentManager

AgentManager
    ├─→ Collects MCP tools from various sources
    │     - WhatsApp tools (from main.py)
    │     - GitHub MCP config (from github_mcp.server)
    │     - Netlify MCP config (from netlify_mcp.server)
    └─→ Passes to Agent and Orchestrator

ClaudeSDK
    ├─→ Receives MCP servers dict
    ├─→ Enhances system prompt with tool descriptions
    └─→ Registers with ClaudeAgentOptions
```

### 3. Communication Patterns

**Single Agent:**
```
User → WhatsApp → main.py → AgentManager → Agent → ClaudeSDK → Claude API
                                                                    ↓
User ← WhatsApp ← main.py ←─────────────────────────────────── Response
```

**Multi-Agent (A2A):**
```
Orchestrator
    ↓ send_task_to_agent()
A2A Protocol.send_task()
    ↓ create A2AMessage
Target Agent.receive_message()
    ↓ handle_task_request()
Target Agent.execute_task()
    ↓ use ClaudeSDK
Claude API generates result
    ↓
TaskResponse returned to Orchestrator
```

---

## Areas Related to Potential Bugs/Features

### 1. Session Management
- **File:** `src/python/agents/session.py`
- **Key Lines:** 68-71 (history trimming), 92-112 (cleanup logic)
- **Potential Issues:**
  - Race conditions in cleanup
  - Memory leaks if cleanup fails
  - Context loss when history trimmed

### 2. Webhook Processing
- **File:** `src/python/main.py`
- **Key Lines:** 120-155 (webhook_receive), 158-181 (process_whatsapp_message)
- **Potential Issues:**
  - Async task spawning without error handling
  - WhatsApp expects quick 200 OK (must return within 5 seconds)
  - Parser failures silently ignored

### 3. Multi-Agent Coordination
- **File:** `src/python/agents/collaborative/orchestrator.py`
- **Key Lines:** 643-709 (quality loop), 1172-1241 (build retry)
- **Fixed Issues (2025-10-22):**
  - ✅ **Agent Access Errors**: Fixed by using constant IDs (DESIGNER_ID, FRONTEND_ID, etc.) instead of accessing `.agent_card.agent_id` on lazy-initialized agents
  - ✅ **User Visibility**: Added real-time WhatsApp notifications for all agent activities
- **Potential Issues:**
  - Infinite loops if quality never improves
  - Build retry exhaustion
  - Agent cleanup failures causing memory leaks
  - WhatsApp notification failures (non-blocking, logged)

### 4. MCP Server Initialization
- **File:** `src/python/agents/manager.py`
- **Key Lines:** 49-88 (GitHub/Netlify MCP setup)
- **Potential Issues:**
  - Silent failures if tokens invalid
  - MCP server unavailability
  - Tool registration conflicts

### 5. A2A Protocol
- **File:** `src/python/agents/collaborative/a2a_protocol.py`
- **Key Lines:** 38-82 (send_message)
- **Potential Issues:**
  - In-memory only (not distributed)
  - No message persistence
  - Agent unregistration edge cases

### 6. Claude SDK Integration
- **File:** `src/python/sdk/claude_sdk.py`
- **Key Lines:** 113-180 (initialize_client), 182-227 (send_message)
- **Potential Issues:**
  - Client initialization failures
  - MCP tool conflicts
  - Response parsing errors

---

## Testing

### Test Files

| File | Purpose |
|------|---------|
| `tests/test_a2a_protocol.py` | A2A communication testing |
| `tests/test_claude_sdk.py` | Claude SDK wrapper testing |
| `tests/test_docker_sdk.py` | Docker integration testing |
| `tests/test_netlify_mcp.py` | Netlify MCP testing |
| `tests/test_orchestrator.py` | Multi-agent workflow testing |
| `tests/test_github_mcp.py` | GitHub MCP testing |

---

## Summary

### Architecture Strengths
1. **Modular Design**: Clear separation of concerns
2. **MCP Integration**: Extensible tool system
3. **A2A Protocol**: Standardized agent communication
4. **Lazy Initialization**: Resource-efficient agent creation
5. **Quality Loop**: Iterative improvement until standards met
6. **Build Retry**: Automatic error fixing
7. **Real-Time Notifications**: WhatsApp updates on agent activities (Added 2025-10-22)
8. **Enhanced Code Review**: Designer agent validates code against design spec (Added 2025-10-22)

### Potential Improvement Areas
1. **Distributed A2A**: Current implementation is in-memory only
2. **Persistent Sessions**: Sessions lost on restart
3. **Error Handling**: Some error cases silently ignored
4. **Rate Limiting**: No rate limiting on WhatsApp/Claude API calls
5. **Monitoring**: Limited observability and logging
6. **Testing Coverage**: Needs more comprehensive tests

### Key Design Patterns
- **Factory Pattern**: AgentManager creates agents on-demand
- **Strategy Pattern**: Different workflows based on AI decision
- **Observer Pattern**: A2A Protocol for agent communication
- **Singleton Pattern**: A2A Protocol, Orchestrator
- **Decorator Pattern**: MCP tools using @tool decorator

---

## Quick Reference

### Most Important Files to Understand
1. `main.py` - Entry point and API endpoints
2. `agents/manager.py` - Agent lifecycle and routing
3. `agents/collaborative/orchestrator.py` - Multi-agent workflows
4. `sdk/claude_sdk.py` - Claude API integration
5. `agents/collaborative/a2a_protocol.py` - Agent communication

### Common Operations

**Add new MCP server:**
1. Create server in `src/python/{name}_mcp/server.py`
2. Add configuration function
3. Register in `agents/manager.py` __init__()

**Add new agent type:**
1. Create agent in `agents/collaborative/{name}_agent.py`
2. Inherit from `BaseAgent`
3. Implement `execute_task()` and `review_artifact()`
4. Register in `orchestrator.py` __init__()

**Add new workflow:**
1. Add workflow type to AI planning prompt (orchestrator.py:338-360)
2. Create `_workflow_{name}()` method in orchestrator
3. Add routing in `build_webapp()` (orchestrator.py:473-483)

---

## Recent Changes & Improvements (2025-10-22)

### 1. Fixed Agent Access Errors in Orchestrator

**Problem:**
- Orchestrator was trying to access `self.frontend.agent_card.agent_id`, `self.designer.agent_card.agent_id`, etc.
- These attributes didn't exist due to lazy initialization
- Error: `'CollaborativeOrchestrator' object has no attribute 'frontend'`

**Solution:**
- Replaced all agent attribute accesses with constant agent IDs:
  - `self.frontend.agent_card.agent_id` → `self.FRONTEND_ID`
  - `self.designer.agent_card.agent_id` → `self.DESIGNER_ID`
  - `self.code_reviewer.agent_card.agent_id` → `self.CODE_REVIEWER_ID`
  - `self.qa_engineer.agent_card.agent_id` → `self.QA_ID`
  - `self.devops.agent_card.agent_id` → `self.DEVOPS_ID`

**Files Modified:**
- `src/python/agents/collaborative/orchestrator.py` (9 locations updated)

---

### 2. Added Real-Time WhatsApp Notifications

**Feature:**
Users now receive live WhatsApp updates on multi-agent workflow progress.

**Implementation:**

**A. Orchestrator Enhancements** (`orchestrator.py`):
- **Line 58**: Added `user_phone_number` parameter to `__init__()`
- **Lines 75-86**: Initialize WhatsApp client for notifications
- **Lines 226-238**: `_send_whatsapp_notification()` method
- **Lines 240-255**: `_get_agent_type_name()` helper method
- **Lines 276-339**: Enhanced `_send_task_to_agent()` with pre/post notifications
- **Lines 341-395**: Enhanced `_request_review_from_agent()` with review score notifications
- **Lines 553-569**: Added initial acknowledgment and AI planning notifications in `build_webapp()`

**B. AgentManager Integration** (`manager.py`):
- **Lines 94-103**: Changed orchestrator to lazy initialization per user
- **Lines 145-175**: Pass user phone number when creating orchestrator
- Dynamic orchestrator creation with user's WhatsApp number

**Notification Types:**
1. **Initial Acknowledgment**: "🚀 Request received! Multi-agent team processing..."
2. **AI Planning**: "🧠 AI Planning Complete - Workflow: full_build"
3. **A2A Communication**: "🤖 Orchestrator → Frontend Developer"
4. **Task Completion**: "✅ Task Done by: Frontend Developer"
5. **Review Results**: "✅ Review Done by: UI/UX Designer - Score: 7/10"

**Example Flow:**
```
User sends: "Build me a todo app"
  ↓
📱 "🚀 Request received! Multi-agent team processing..."
📱 "🧠 AI Planning Complete - Workflow: full_build"
📱 "🤖 Orchestrator → UI/UX Designer"
📱 "✅ Task Done by: UI/UX Designer"
📱 "🤖 Orchestrator → Frontend Developer"
📱 "✅ Task Done by: Frontend Developer"
📱 "🔍 Orchestrator → UI/UX Designer (Review)"
📱 "✅ Review Done by: UI/UX Designer - Score: 9/10 - ✅ Approved"
📱 "✅ Your webapp is ready! 🔗 https://..."
```

---

### 3. Enhanced Designer Agent Code Review

**Feature:**
Designer agent now comprehensively reviews frontend code against design specifications.

**Implementation:**

**A. Updated Agent Capabilities** (`designer_agent.py` lines 20-30):
```python
capabilities=[
    "Design system creation",
    "Wireframing",
    "Color scheme design",
    "Typography specification",
    "Component design",
    "Accessibility review",
    "Responsive design",
    "Frontend code review",           # NEW
    "Design fidelity verification"    # NEW
]
```

**B. Enhanced System Prompt** (lines 36-68):
- Added dual-role description: Design Creation + Code Review
- Emphasized comparing actual code vs design spec
- Added scoring guidance (be critical, 9-10 only for near-perfect)

**C. Comprehensive Review Prompt** (lines 195-260):
Designer agent now checks:
1. **Design Fidelity**: Hex codes, typography, spacing in code
2. **Code Quality**: CSS/Tailwind classes, design tokens, fonts
3. **Accessibility**: ARIA labels in JSX/HTML, color contrast
4. **Responsiveness**: Breakpoint classes (md:, lg:) in code
5. **Specific Feedback**: File names, line numbers, code references

**Review Criteria:**
- 10: Perfect implementation, matches design spec exactly
- 9: Excellent, minor tweaks needed
- 8: Good, a few improvements needed
- 7: Acceptable, several issues to fix
- 6: Below standard, significant changes required
- 5 or below: Major redesign/reimplementation needed

**Example Review:**
```json
{
  "approved": false,
  "score": 7,
  "feedback": [
    "Primary color in App.jsx line 25 uses #4287F5 instead of spec's #3B82F6",
    "Font family not imported - missing Google Fonts link for 'Inter'"
  ],
  "critical_issues": [
    "Color mismatch breaks brand consistency"
  ]
}
```

---

### 4. Files Modified Summary

| File | Lines Changed | Changes |
|------|--------------|---------|
| `orchestrator.py` | ~200 lines | Agent access fix, WhatsApp notifications |
| `manager.py` | ~30 lines | Dynamic orchestrator with phone number |
| `designer_agent.py` | ~70 lines | Enhanced code review capabilities |

### 5. Testing & Validation

**Syntax Validation:**
```bash
✅ python3 -m py_compile src/python/agents/collaborative/orchestrator.py
✅ python3 -m py_compile src/python/agents/manager.py
✅ python3 -m py_compile src/python/agents/collaborative/designer_agent.py
```

**All files compile without errors.**

---

**End of Codebase Map**
