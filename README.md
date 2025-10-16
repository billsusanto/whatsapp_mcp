# WhatsApp Claude Agent SDK

A hybrid TypeScript/Python project that enables AI-powered WhatsApp messaging through two distinct interfaces:

1. **WhatsApp Webhook** - Receive messages from WhatsApp users and respond automatically with Claude AI
2. **MCP Server** - Expose WhatsApp messaging capabilities to Claude Desktop as a tool

---

## Table of Contents

1. [What This Project Does](#what-this-project-does)
2. [Architecture Overview](#architecture-overview)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [How It Works](#how-it-works)
6. [Setup Instructions](#setup-instructions)
7. [Implementation Guide](#implementation-guide)
8. [Deployment](#deployment)
9. [Environment Variables](#environment-variables)
10. [Resources](#resources)

---

## What This Project Does

This project creates a bridge between WhatsApp Business API and Claude AI in two ways:

### Use Case 1: AI-Powered WhatsApp Bot
Users send messages to your WhatsApp Business number → Your server processes with Claude → Automated AI responses sent back

**Example:**
- User: "What's the weather today?"
- Bot (Claude): "I'd be happy to help! However, I'll need to know your location to provide weather information..."

### Use Case 2: WhatsApp Tool for Claude Desktop
Claude Desktop users can send WhatsApp messages directly through Claude's interface using MCP (Model Context Protocol)

**Example:**
- You (in Claude Desktop): "Send a WhatsApp message to +1234567890 saying hello"
- Claude: *Uses WhatsApp MCP tool to send message*
- Confirmation: "Message sent successfully!"

---

## Architecture Overview

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
│         ┌───────────────────────────────────────┐              │
│         │   Vercel (Next.js Serverless)         │              │
│         │   ─────────────────────────────────   │              │
│         │   src/app/api/webhook/route.ts        │              │
│         │   • GET: Webhook verification         │              │
│         │   • POST: Process incoming messages   │              │
│         │   • Use Claude Agent SDK              │              │
│         │   • Generate AI responses             │              │
│         │   • Send via WhatsApp API             │              │
│         └───────────────────────────────────────┘              │
│                              │                                  │
│                              │ Response                         │
│                              ▼                                  │
│                    WhatsApp Business API                        │
│                              │                                  │
│                              ▼                                  │
│                         WhatsApp User                           │
│                      (Receives AI response)                     │
└─────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│                     Claude Desktop User                         │
│                              │                                  │
│                              │ "Send WhatsApp to..."            │
│                              ▼                                  │
│         ┌───────────────────────────────────────┐              │
│         │   Render (Python MCP Server)          │              │
│         │   ─────────────────────────────────   │              │
│         │   src/python/mcp/server.py            │              │
│         │   • MCP Server with SSE transport     │              │
│         │   • Expose WhatsApp tools:            │              │
│         │     - send_message(to, text)          │              │
│         │     - get_conversation(phone)         │              │
│         │   • Uses Python WhatsApp client       │              │
│         └───────────────────────────────────────┘              │
│                              │                                  │
│                              │ API call                         │
│                              ▼                                  │
│                    WhatsApp Business API                        │
│                              │                                  │
│                              ▼                                  │
│                         WhatsApp User                           │
│                      (Receives message)                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Next.js Webhook (TypeScript)
- **Framework:** Next.js 15.5+ (App Router)
- **Runtime:** Node.js serverless functions on Vercel
- **AI SDK:** `@anthropic-ai/claude-agent-sdk` - Agent framework with tool use
- **Docker:** Multi-stage builds with Node 20 Alpine
- **Purpose:** Handle WhatsApp webhooks, process messages, respond with AI

### MCP Server (Python)
- **Language:** Python 3.11+
- **AI SDK:** `claude-agent-sdk` - Python agent framework
- **MCP:** `mcp` - Model Context Protocol SDK
- **Web Server:** `uvicorn` + `starlette` - ASGI server for SSE transport
- **Docker:** Python 3.11 slim with optimized layers
- **Purpose:** Expose WhatsApp as a tool for Claude Desktop via MCP

### External APIs
- **WhatsApp Business Cloud API** - Send/receive messages
- **Anthropic Claude API** - AI agent capabilities

### Containerization
- **Docker:** Both services containerized for consistency
- **docker-compose:** Local development orchestration
- **Production:** Vercel (Next.js) + Render (Python) with Docker support

---

## Project Structure

```
monorepo/
├── src/
│   ├── app/                           # Next.js App Router
│   │   ├── api/
│   │   │   └── webhook/
│   │   │       └── route.ts           # 🔷 WhatsApp webhook handler
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── globals.css
│   │
│   └── python/                        # 🐍 Python MCP Server
│       ├── whatsapp/
│       │   ├── __init__.py
│       │   ├── client.py              # WhatsApp Business API client
│       │   └── parser.py              # Webhook payload parser
│       │
│       ├── sdk/
│       │   ├── __init__.py
│       │   └── claude_sdk.py          # Claude Agent SDK wrapper
│       │
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── agent.py               # Individual agent instance
│       │   ├── manager.py             # Multi-agent management
│       │   └── session.py             # Conversation session tracking
│       │
│       ├── mcp/
│       │   ├── __init__.py
│       │   └── server.py              # 🔌 MCP server entry point
│       │
│       └── utils/
│           ├── __init__.py
│           ├── config.py              # Environment configuration
│           └── logger.py              # Logging utilities
│
├── public/                            # Static assets
├── node_modules/                      # Node dependencies (gitignored)
│
├── package.json                       # Node dependencies
├── requirements.txt                   # Python dependencies
│
├── Dockerfile.vercel                  # 🐳 Docker for Next.js/Agent Server
├── Dockerfile.render                  # 🐳 Docker for Python MCP Server
├── docker-compose.yml                 # 🐳 Local development orchestration
├── .dockerignore                      # Docker build exclusions
│
├── vercel.json                        # Vercel deployment config
├── render.yaml                        # Render deployment config
├── .env                               # Environment variables (gitignored)
├── .gitignore
│
├── next.config.ts
├── tsconfig.json
├── tailwind.config.ts
└── README.md                          # This file
```

---

## How It Works

### Workflow 1: WhatsApp User → AI Response

1. **User sends message** to your WhatsApp Business number
2. **WhatsApp API** sends webhook POST to `https://your-app.vercel.app/api/webhook`
3. **Next.js webhook handler** (`src/app/api/webhook/route.ts`):
   - Parses webhook payload
   - Extracts phone number and message text
   - Calls Claude Agent SDK with message
   - Receives AI-generated response
4. **Webhook handler sends response** via WhatsApp Business API
5. **User receives AI response** in WhatsApp

### Workflow 2: Claude Desktop → WhatsApp Message

1. **User asks Claude Desktop** to send a WhatsApp message
2. **Claude identifies** it needs the WhatsApp tool
3. **Claude connects** to MCP server at `https://whatsapp-mcp.onrender.com/sse`
4. **MCP server** exposes tools:
   - `send_message(to, text)`
   - `get_conversation(phone_number)`
5. **Claude calls** `send_message` tool
6. **MCP server** uses Python WhatsApp client to send message
7. **Message delivered** via WhatsApp Business API
8. **Claude confirms** to user: "Message sent!"

---

## Setup Instructions

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.11+
- **WhatsApp Business Account** with API access
- **Anthropic API Key** for Claude
- **Vercel Account** (free tier works)
- **Render Account** (free tier works)

### 1. Clone and Install Dependencies

```bash
# Clone the repository
git clone <your-repo-url>
cd monorepo

# Install Node.js dependencies
npm install

# Install Python dependencies
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create a `.env` file in the root directory:

```env
# Anthropic API
ANTHROPIC_API_KEY=sk-ant-api03-...

# WhatsApp Business API
WHATSAPP_ACCESS_TOKEN=EAHUle7WZCIeQBPvvh2w...
WHATSAPP_PHONE_NUMBER_ID=855776727613754
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_secure_token_123

# Agent Configuration
AGENT_SYSTEM_PROMPT="You are a helpful WhatsApp assistant..."
```

**Where to get these:**
- **ANTHROPIC_API_KEY:** [Anthropic Console](https://console.anthropic.com/)
- **WhatsApp credentials:** [Meta Business Suite](https://business.facebook.com/) → WhatsApp → API Setup
- **WHATSAPP_WEBHOOK_VERIFY_TOKEN:** Create your own secure random string

### 3. Test Locally

#### Option A: With Docker (Recommended)

```bash
# Build and start both services
docker-compose up --build

# Services will be available at:
# - Webhook: http://localhost:3000/api/webhook
# - MCP Server: http://localhost:10000

# Stop services
docker-compose down
```

#### Option B: Without Docker

**Next.js Webhook:**
```bash
npm run dev
# Open http://localhost:3000

# Test webhook verification
curl "http://localhost:3000/api/webhook?hub.mode=subscribe&hub.verify_token=your_secure_token_123&hub.challenge=test123"
# Should return: test123
```

**Python MCP Server:**
```bash
source venv/bin/activate
python src/python/mcp/server.py
# MCP server starts on port 8080
```

### 4. Test with ngrok (for WhatsApp webhook)

```bash
# Install ngrok: https://ngrok.com/
ngrok http 3000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
# Add to WhatsApp Business API webhook configuration:
# URL: https://abc123.ngrok.io/api/webhook
# Verify Token: your_secure_token_123
```

---

## Implementation Guide

All files contain detailed TODO comments and pseudocode. Implement in this order:

### Priority 1: Next.js Webhook (TypeScript)

**File:** `src/app/api/webhook/route.ts`

**What to implement:**

1. **GET handler** (Webhook verification):
   ```typescript
   export async function GET(request: NextRequest) {
     const searchParams = request.nextUrl.searchParams;
     const mode = searchParams.get('hub.mode');
     const token = searchParams.get('hub.verify_token');
     const challenge = searchParams.get('hub.challenge');

     if (mode === 'subscribe' && token === process.env.WHATSAPP_WEBHOOK_VERIFY_TOKEN) {
       return new NextResponse(challenge, { status: 200 });
     }
     return new NextResponse('Forbidden', { status: 403 });
   }
   ```

2. **POST handler** (Message processing):
   ```typescript
   import { ClaudeAgent } from '@anthropic-ai/claude-agent-sdk';

   export async function POST(request: NextRequest) {
     const body = await request.json();

     // Parse WhatsApp webhook
     // Extract phone number and message text
     // Call Claude Agent SDK
     // Send response via WhatsApp API

     return NextResponse.json({ status: 'ok' });
   }
   ```

**Resources:**
- [WhatsApp Webhook Docs](https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/payload-examples)
- [Next.js Route Handlers](https://nextjs.org/docs/app/building-your-application/routing/route-handlers)
- [Claude Agent SDK](https://docs.claude.com/en/docs/claude-code/sdk/migration-guide)

### Priority 2: Python Utilities (for MCP)

**Files to implement:**
1. `src/python/utils/config.py` - Environment variable loading
2. `src/python/whatsapp/client.py` - WhatsApp API client
3. `src/python/whatsapp/parser.py` - Webhook parser (optional for MCP)

**Example: WhatsApp Client**
```python
import os
import requests

class WhatsAppClient:
    def __init__(self):
        self.access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.api_url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}/messages"

    def send_message(self, to: str, text: str):
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text}
        }
        response = requests.post(self.api_url, headers=headers, json=payload)
        return response.json()
```

### Priority 3: Python MCP Server

**File:** `src/python/mcp/server.py`

**What to implement:**
- MCP server with SSE transport
- Tools: `send_message`, `get_conversation`
- Health check endpoint for Render

**Resources:**
- [MCP Python SDK Guide](https://modelcontextprotocol.io/quickstart/server)
- [MCP Tools Documentation](https://modelcontextprotocol.io/docs/concepts/tools)

---

## Deployment

### Deploy Next.js to Vercel (with Docker)

**Option 1: Automatic Deployment (Vercel's Native Build)**
```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
vercel --prod
```

**Option 2: Docker Deployment (Using Dockerfile.vercel)**
1. Push code to GitHub
2. In Vercel dashboard → Project Settings → Build & Development Settings
3. Set **Build Command**: `docker build -f Dockerfile.vercel -t next-app .`
4. Vercel will use your Dockerfile for deployment

**Set environment variables in Vercel dashboard:**
- Go to your project → Settings → Environment Variables
- Add all variables from `.env`

**Configure WhatsApp webhook:**
- Webhook URL: `https://your-app.vercel.app/api/webhook`
- Verify Token: Your `WHATSAPP_WEBHOOK_VERIFY_TOKEN`

### Deploy MCP Server to Render (with Docker)

**Using Dockerfile.render:**

1. Push code to GitHub
2. Go to [render.com](https://render.com) and sign up
3. Click "New" → "Web Service"
4. Connect your GitHub repository
5. **Configure service:**
   - **Environment:** Docker
   - **Dockerfile Path:** `Dockerfile.render`
   - **Region:** Choose closest to your users
6. Set environment variables in Render dashboard:
   - `ANTHROPIC_API_KEY`
   - `WHATSAPP_ACCESS_TOKEN`
   - `WHATSAPP_PHONE_NUMBER_ID`
7. Deploy!

**Alternative: Using render.yaml Blueprint:**
- Render auto-detects `render.yaml`
- Modify `render.yaml` to specify `dockerfilePath: Dockerfile.render`

**Your MCP server URL:** `https://whatsapp-mcp-server.onrender.com/sse`

**Connect to Claude Desktop:**

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac) or equivalent:

```json
{
  "mcpServers": {
    "whatsapp": {
      "url": "https://whatsapp-mcp-server.onrender.com/sse",
      "transport": "sse"
    }
  }
}
```

### Local Docker Testing Before Deployment

```bash
# Test Vercel Dockerfile locally
docker build -f Dockerfile.vercel -t whatsapp-webhook .
docker run -p 3000:3000 --env-file .env whatsapp-webhook

# Test Render Dockerfile locally
docker build -f Dockerfile.render -t whatsapp-mcp .
docker run -p 10000:10000 --env-file .env whatsapp-mcp

# Test both with docker-compose
docker-compose up --build
```

---

## Environment Variables

### Required for Both Services

| Variable | Description | Where to Get |
|----------|-------------|--------------|
| `ANTHROPIC_API_KEY` | Claude API key | [console.anthropic.com](https://console.anthropic.com/) |
| `WHATSAPP_ACCESS_TOKEN` | WhatsApp API token | [Meta Business Suite](https://business.facebook.com/) |
| `WHATSAPP_PHONE_NUMBER_ID` | Your WhatsApp phone number ID | Meta Business Suite → WhatsApp API |
| `AGENT_SYSTEM_PROMPT` | Custom system prompt for Claude | Your custom prompt |

### Required for Webhook Only

| Variable | Description |
|----------|-------------|
| `WHATSAPP_WEBHOOK_VERIFY_TOKEN` | Webhook verification token (create your own) |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Server port (Render sets this) | 8080 |

---

## Key Features

### Claude Agent SDK Benefits

- **Tool Use:** Built-in support for custom tools and MCP
- **State Management:** Better conversation history handling
- **Agent-Focused:** Designed specifically for autonomous agents
- **Preset Configurations:** Includes pre-built agent templates

### WhatsApp Integration

- **Business API:** Cloud-based, scalable
- **Webhook Support:** Real-time message delivery
- **Rich Messages:** Supports text, images, videos, documents

### MCP Integration

- **SSE Transport:** Real-time streaming for Claude Desktop
- **Tool Exposure:** WhatsApp capabilities as Claude tools
- **Extensible:** Easy to add more tools

---

## Resources

### Documentation

- [WhatsApp Cloud API Documentation](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [Anthropic Claude API Documentation](https://docs.anthropic.com/)
- [Claude Agent SDK Migration Guide](https://docs.claude.com/en/docs/claude-code/sdk/migration-guide)
- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Vercel Deployment](https://vercel.com/docs)
- [Render Deployment](https://render.com/docs)

### API References

- [WhatsApp Send Messages](https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-messages)
- [WhatsApp Webhooks](https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/payload-examples)
- [Anthropic Messages API](https://docs.anthropic.com/en/api/messages)
- [MCP Server Implementation](https://modelcontextprotocol.io/quickstart/server)

### Tools & Libraries

- [Python Requests](https://requests.readthedocs.io/)
- [Next.js API Routes](https://nextjs.org/docs/app/building-your-application/routing/route-handlers)
- [Uvicorn ASGI Server](https://www.uvicorn.org/)

---

## Development Commands

### Docker Commands

```bash
# Start all services with Docker Compose
docker-compose up --build

# Start in detached mode
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild specific service
docker-compose up --build webhook
docker-compose up --build mcp-server

# Clean up (remove volumes)
docker-compose down -v
```

### Local Development (Without Docker)

```bash
# Next.js development server
npm run dev

# Next.js production build
npm run build
npm start

# Python MCP server (local)
source venv/bin/activate
python src/python/mcp/server.py

# Install dependencies
npm install
pip install -r requirements.txt

# Lint TypeScript
npm run lint

# Test (add pytest later)
pytest
```

---

## Project Philosophy

**Simple, Focused, Maintainable**

- **One language per platform:** TypeScript for Vercel, Python for Render
- **No Flask:** Next.js API Routes handle webhooks natively
- **Claude Agent SDK:** Purpose-built for AI agents, not generic API clients
- **MCP Protocol:** Standard interface for Claude Desktop integration
- **Serverless-first:** Vercel functions scale automatically
- **Dockerized:** Consistent environments from dev to production
- **Pseudocode everywhere:** All files have detailed TODO comments for learning

---

**Built with Claude Agent SDK, Next.js, Python, and Docker**
