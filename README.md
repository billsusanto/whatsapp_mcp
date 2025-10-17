# 🤖 WhatsApp AI Agent with Claude SDK

An intelligent WhatsApp bot powered by Claude AI that provides automated, context-aware responses to WhatsApp users. Built with Python, Claude Agent SDK, FastAPI, and deployed on Render.

---

## 📋 Table of Contents

1. [What This Project Does](#what-this-project-does)
2. [Architecture Overview](#architecture-overview)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [How It Works](#how-it-works)
6. [Setup Instructions](#setup-instructions)
7. [Deployment to Render](#deployment-to-render)
8. [Environment Variables](#environment-variables)
9. [Testing](#testing)
10. [Resources](#resources)

---

## 🎯 What This Project Does

This project creates an **AI-powered WhatsApp bot** that automatically responds to user messages using Claude AI:

### Use Case: Intelligent WhatsApp Assistant

Users send messages to your WhatsApp Business number → Your server processes them with Claude → AI responses sent back automatically with context awareness

**Example Conversation:**
```
User: "What's the weather like?"
Bot (Claude): "I'd be happy to help! However, I'll need to know your location to provide weather information..."

User: "Can you help me with Python?"
Bot (Claude): "Absolutely! I can help with Python programming. What specific aspect would you like assistance with?"
```

### Key Features:
- ✅ **Multi-user support** - One agent instance per phone number
- ✅ **Context-aware** - 30-minute conversation sessions with 20-message history
- ✅ **Tool integration** - Claude can use WhatsApp MCP tools to send messages
- ✅ **Async processing** - Non-blocking webhook responses
- ✅ **Production-ready** - Deployed on Render with Docker

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         WhatsApp User                           │
│                              │                                  │
│                              │ Sends message                    │
│                              ▼                                  │
│                    WhatsApp Business API                        │
│                              │                                  │
│                              │ POST webhook                     │
│                              ▼                                  │
│         ┌────────────────────────────────────────────┐         │
│         │         Render (Docker Container)          │         │
│         │  ─────────────────────────────────────────  │         │
│         │                                             │         │
│         │  ┌──────────────────────────────────────┐  │         │
│         │  │   FastAPI Service (main.py)          │  │         │
│         │  │   • Webhook verification (GET)       │  │         │
│         │  │   • Message processing (POST)        │  │         │
│         │  │   • Health check endpoint            │  │         │
│         │  └──────────────────────────────────────┘  │         │
│         │                    │                        │         │
│         │                    ▼                        │         │
│         │  ┌──────────────────────────────────────┐  │         │
│         │  │   Agent Manager                      │  │         │
│         │  │   • One agent per phone number       │  │         │
│         │  │   • Agent spawning & routing         │  │         │
│         │  │   • Session management               │  │         │
│         │  └──────────────────────────────────────┘  │         │
│         │           │              │                  │         │
│         │           ▼              ▼                  │         │
│         │  ┌──────────────┐  ┌──────────────┐       │         │
│         │  │   Agent 1    │  │   Agent 2    │  ...  │         │
│         │  │              │  │              │       │         │
│         │  │ Claude SDK   │  │ Claude SDK   │       │         │
│         │  │ with MCP     │  │ with MCP     │       │         │
│         │  │ tools        │  │ tools        │       │         │
│         │  └──────────────┘  └──────────────┘       │         │
│         │           │              │                  │         │
│         │           └──────┬───────┘                  │         │
│         │                  ▼                          │         │
│         │  ┌──────────────────────────────────────┐  │         │
│         │  │   WhatsApp MCP Tool                  │  │         │
│         │  │   • send_whatsapp(to, text)          │  │         │
│         │  │   • Uses WhatsApp Business API       │  │         │
│         │  └──────────────────────────────────────┘  │         │
│         │                                             │         │
│         └─────────────────────────────────────────────┘         │
│                              │                                  │
│                              │ Send response                    │
│                              ▼                                  │
│                    WhatsApp Business API                        │
│                              │                                  │
│                              ▼                                  │
│                         WhatsApp User                           │
│                      (Receives AI response)                     │
└─────────────────────────────────────────────────────────────────┘
```

### Architecture Highlights:

1. **Single Render Service** - One Docker container runs everything
2. **Agent Manager Pattern** - Spawns one agent per phone number
3. **Claude Agent SDK** - Uses official Python SDK with tool support
4. **MCP Tools** - WhatsApp sending capabilities integrated as tools
5. **Session Management** - 30-minute TTL, 20-message history per user

---

## 🛠️ Technology Stack

### Backend (Python)
- **Framework:** FastAPI (REST API with async support)
- **AI SDK:** `claude-agent-sdk` - Official Python SDK for Claude agents
- **MCP:** `mcp>=1.18.0` - Model Context Protocol for tool integration
- **WhatsApp:** WhatsApp Business Cloud API (Graph API v18.0)
- **Server:** Uvicorn (ASGI server)
- **Python:** 3.11+

### Infrastructure
- **Deployment:** Render (Docker container)
- **Containerization:** Docker with Node.js 20 + Python 3.11
- **Runtime:** Claude Code CLI (installed via npm in container)

### External APIs
- **Anthropic Claude API** - AI agent capabilities
- **WhatsApp Business Cloud API** - Send/receive messages

---

## 📁 Project Structure

```
whatsapp_mcp/
├── src/
│   └── python/                        # 🐍 Python backend
│       ├── main.py                    # 🚀 FastAPI entry point
│       │
│       ├── agents/                    # Agent system
│       │   ├── __init__.py
│       │   ├── manager.py             # Agent manager (one per phone)
│       │   ├── agent.py               # Individual agent instance
│       │   └── session.py             # Session management (30min TTL)
│       │
│       ├── sdk/                       # Claude SDK wrapper
│       │   ├── __init__.py
│       │   └── claude_sdk.py          # SDK client with MCP tools
│       │
│       ├── whatsapp/                  # WhatsApp integration
│       │   ├── __init__.py
│       │   ├── client.py              # WhatsApp API client
│       │   └── parser.py              # Webhook payload parser
│       │
│       └── utils/                     # Utilities
│           ├── __init__.py
│           ├── config.py              # Environment config
│           └── logger.py              # Logging
│
├── test_claude_sdk.py                 # Local SDK testing script
├── test_agent.py                      # Agent integration tests
│
├── requirements.txt                   # Python dependencies
├── Dockerfile.render                  # 🐳 Docker for Render deployment
├── render.yaml                        # Render deployment config
├── .dockerignore                      # Docker build exclusions
│
├── .env                               # Environment variables (gitignored)
├── .gitignore
│
├── README.md                          # This file
│
└── docs/                              # Documentation
    ├── ARCHITECTURE.md                # Architecture deep dive
    ├── IMPLEMENTATION_COMPLETE.md     # Implementation summary
    ├── CLAUDE_SDK_TEST.md             # SDK test results
    └── PRE_DEPLOYMENT_CHECKLIST.md    # Deployment verification
```

---

## 🔄 How It Works

### Message Flow:

1. **User sends message** to WhatsApp Business number

2. **WhatsApp API** → POST webhook to Render: `/webhook`

3. **FastAPI webhook handler** (`main.py`):
   - Validates webhook (GET for verification)
   - Parses message payload (POST)
   - Extracts phone number and text
   - Returns 200 OK immediately (WhatsApp requires fast response)

4. **Async processing** (background task):
   - Agent Manager gets/creates agent for phone number
   - Agent processes message with Claude SDK
   - Claude generates response (may use tools)
   - Response sent back via WhatsApp API

5. **User receives AI response** in WhatsApp

### Agent System:

- **One agent per phone number** - Isolated conversations
- **Session management** - 30-minute TTL, auto-cleanup
- **Conversation history** - Last 20 messages per user
- **MCP tool integration** - `send_whatsapp` tool available to Claude

### Claude Agent SDK:

The project uses the official Claude Agent SDK which:
- Requires **Claude Code CLI** to be installed
- Runs agents with full tool support
- Manages conversation context automatically
- Supports MCP tools via `@tool` decorator

---

## 🚀 Setup Instructions

### Prerequisites

- **Python** 3.11+
- **Docker** (for local testing and deployment)
- **WhatsApp Business Account** with API access
- **Anthropic API Key** for Claude
- **Render Account** (free tier works)

### 1. Clone and Install Dependencies

```bash
# Clone the repository
git clone https://github.com/billsusanto/whatsapp_mcp.git
cd whatsapp_mcp

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create a `.env` file in the root directory:

```env
# Anthropic API
ANTHROPIC_API_KEY=sk-ant-api03-...

# WhatsApp Business API
WHATSAPP_ACCESS_TOKEN=EAA...
WHATSAPP_PHONE_NUMBER_ID=123456789012345
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_secure_random_token

# Optional: Custom system prompt
AGENT_SYSTEM_PROMPT="You are a helpful WhatsApp assistant..."
```

**Where to get these:**
- **ANTHROPIC_API_KEY:** [Anthropic Console](https://console.anthropic.com/)
- **WhatsApp credentials:** [Meta Business Suite](https://business.facebook.com/) → WhatsApp → API Setup
- **WHATSAPP_WEBHOOK_VERIFY_TOKEN:** Create your own secure random string (e.g., `my_secret_token_12345`)

### 3. Test Locally

#### Test the Claude SDK (without Docker):

```bash
# Requires Claude Code CLI to be installed locally
python test_claude_sdk.py

# Interactive mode
python test_claude_sdk.py --interactive
```

#### Test with Docker (Recommended):

```bash
# Build Docker image
docker build -f Dockerfile.render -t whatsapp-mcp .

# Run container
docker run -p 8000:8000 --env-file .env whatsapp-mcp

# Service available at http://localhost:8000
```

#### Test webhook locally with ngrok:

```bash
# Install ngrok: https://ngrok.com/
ngrok http 8000

# Copy HTTPS URL (e.g., https://abc123.ngrok-free.app)
# Configure in WhatsApp Business webhook settings
```

---

## 🚢 Deployment to Render

### Deployment Steps:

#### 1. Prepare Repository

Make sure your code is pushed to GitHub:

```bash
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

#### 2. Create Render Service

**Option A: Using render.yaml (Recommended)**

1. Go to [render.com](https://render.com) and sign up
2. Click "New" → "Blueprint"
3. Connect your GitHub repository
4. Select branch: `main` (or `python-only-branch`)
5. Render will detect `render.yaml` and configure automatically
6. Click "Apply"

**Option B: Manual Setup**

1. Click "New" → "Web Service"
2. Connect GitHub repository
3. Configure:
   - **Language:** Docker
   - **Branch:** main
   - **Dockerfile Path:** `./Dockerfile.render`
   - **Region:** Oregon (or closest to you)
4. Click "Create Web Service"

#### 3. Set Environment Variables

In Render dashboard → Your Service → Environment:

| Variable | Value |
|----------|-------|
| `ANTHROPIC_API_KEY` | Your Claude API key |
| `WHATSAPP_ACCESS_TOKEN` | Your WhatsApp token |
| `WHATSAPP_PHONE_NUMBER_ID` | Your phone number ID |
| `WHATSAPP_WEBHOOK_VERIFY_TOKEN` | Your verify token |

Click "Save Changes" - Render will redeploy.

#### 4. Configure WhatsApp Webhook

Once deployed (service URL: `https://whatsapp-mcp-XXXX.onrender.com`):

1. Go to [Meta Business Suite](https://business.facebook.com/) → WhatsApp → Configuration
2. Click "Edit" on Webhook
3. Set **Callback URL**: `https://whatsapp-mcp-XXXX.onrender.com/webhook`
4. Set **Verify Token**: Same value as `WHATSAPP_WEBHOOK_VERIFY_TOKEN`
5. Click "Verify and Save"
6. Subscribe to "messages" field
7. Test by sending a message to your WhatsApp Business number!

### Expected Build Time:

- **First build:** 8-12 minutes
  - Installing Node.js: ~2 min
  - Installing Claude Code CLI: ~3-5 min
  - Installing Python packages: ~2-3 min
- **Subsequent builds:** 3-5 minutes (with caching)

### Service Health Check:

Check your service is running:
```bash
curl https://your-service.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "whatsapp-mcp",
  "api_key_configured": true,
  "whatsapp_configured": true,
  "active_agents": 0
}
```

---

## 🔐 Environment Variables

### Required Variables

| Variable | Description | Where to Get |
|----------|-------------|--------------|
| `ANTHROPIC_API_KEY` | Claude API key | [console.anthropic.com](https://console.anthropic.com/) |
| `WHATSAPP_ACCESS_TOKEN` | WhatsApp API token | [Meta Business Suite](https://business.facebook.com/) |
| `WHATSAPP_PHONE_NUMBER_ID` | Your WhatsApp phone number ID | Meta Business Suite → WhatsApp API |
| `WHATSAPP_WEBHOOK_VERIFY_TOKEN` | Webhook verification token | Create your own random string |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AGENT_SYSTEM_PROMPT` | Custom system prompt for Claude | "You are a helpful WhatsApp assistant..." |
| `PORT` | Server port (Render sets this) | 8000 |

---

## 🧪 Testing

### Local Testing (Without WhatsApp)

Test the Claude SDK independently:

```bash
# Automated tests (4 test scenarios)
python test_claude_sdk.py

# Interactive chat mode
python test_claude_sdk.py --interactive
```

**Test results documented in:** `CLAUDE_SDK_TEST.md`

### Integration Testing

Test the full agent system:

```bash
python test_agent.py
```

This tests:
- ✅ Agent Manager initialization
- ✅ Agent creation per phone number
- ✅ Message processing with Claude SDK
- ✅ MCP tools registration

### Testing with WhatsApp

1. Deploy to Render
2. Configure WhatsApp webhook
3. Send a message to your WhatsApp Business number
4. Check Render logs for processing
5. Verify response received in WhatsApp

**Tip:** Check Render logs in real-time:
```
Render Dashboard → Your Service → Logs
```

---

## 📚 Key Features

### Multi-User Support
- One agent instance per phone number
- Isolated conversation contexts
- Automatic agent spawning

### Session Management
- 30-minute TTL per conversation
- 20-message history limit
- Automatic cleanup of expired sessions

### Tool Integration
- WhatsApp MCP tool: `send_whatsapp(to, text)`
- Claude can autonomously send messages
- Extensible for additional tools

### Error Handling
- Graceful error messages to users
- Comprehensive logging
- Webhook validation

### Production Ready
- Docker containerization
- Health check endpoints
- Non-blocking async processing
- Security (non-root user in Docker)

---

## 📖 Resources

### Documentation

- [WhatsApp Cloud API](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [Claude Agent SDK](https://docs.claude.com/en/docs/claude-code/sdk)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Render Documentation](https://render.com/docs)

### API References

- [WhatsApp Send Messages](https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-messages)
- [WhatsApp Webhooks](https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/payload-examples)
- [Anthropic Messages API](https://docs.anthropic.com/en/api/messages)

### Tools & Libraries

- [Python Requests](https://requests.readthedocs.io/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Uvicorn](https://www.uvicorn.org/)
- [Docker](https://docs.docker.com/)

---

## 🛠️ Development

### Running Locally

```bash
# Without Docker
source venv/bin/activate
python src/python/main.py

# With Docker
docker build -f Dockerfile.render -t whatsapp-mcp .
docker run -p 8000:8000 --env-file .env whatsapp-mcp
```

### Project Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python test_claude_sdk.py
python test_agent.py

# Format code (if using black)
black src/python/

# Type checking (if using mypy)
mypy src/python/
```

---

## 🏛️ Architecture Files

For detailed architecture documentation:

- **ARCHITECTURE.md** - Full system design and module breakdown
- **IMPLEMENTATION_COMPLETE.md** - Feature implementation summary
- **CLAUDE_SDK_TEST.md** - SDK testing results and examples
- **PRE_DEPLOYMENT_CHECKLIST.md** - Deployment verification checklist

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

- **Anthropic** - Claude AI and Agent SDK
- **Meta** - WhatsApp Business API
- **Render** - Hosting platform

---

**Built with Claude Agent SDK, FastAPI, Python, and Docker**

**Deployment:** Render (https://whatsapp-mcp-p0ti.onrender.com)
