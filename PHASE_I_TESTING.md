# Phase I Testing Guide - GitHub MCP Integration

This guide walks you through testing the GitHub MCP integration locally before deploying to Render.

## Prerequisites

Before testing, make sure you have:

1. **Python 3.11+** installed
2. **Claude Code CLI** installed (`npm install -g @anthropic-ai/claude-code`)
3. **Virtual environment** activated
4. **Required API keys**:
   - Anthropic API Key
   - GitHub Personal Access Token

---

## Step 1: Get GitHub Personal Access Token

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Give it a name: "WhatsApp MCP Integration"
4. Select scopes:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `workflow` (Update GitHub Action workflows)
   - ✅ `read:org` (Read org and team membership)
5. Click "Generate token"
6. **Copy the token** (starts with `ghp_...`)

---

## Step 2: Set Environment Variables

Create or update your `.env` file:

```bash
# Required for Claude Agent SDK
ANTHROPIC_API_KEY=sk-ant-...

# Required for GitHub MCP
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_...

# Enable GitHub MCP feature
ENABLE_GITHUB_MCP=true

# Optional (for WhatsApp testing)
WHATSAPP_ACCESS_TOKEN=EAA...
WHATSAPP_PHONE_NUMBER_ID=...
WHATSAPP_WEBHOOK_VERIFY_TOKEN=...
```

Or export them directly:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export GITHUB_PERSONAL_ACCESS_TOKEN="ghp_..."
export ENABLE_GITHUB_MCP="true"
```

---

## Step 3: Install/Update Dependencies

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify Claude Code CLI is installed
claude --version
```

---

## Step 4: Run Automated Tests

Run the test script:

```bash
python test_github_mcp.py
```

**Expected output:**

```
============================================================
🧪 GITHUB MCP INTEGRATION TESTS - PHASE I
============================================================

============================================================
TEST 1: GitHub MCP Configuration
============================================================
✓ ANTHROPIC_API_KEY: Set
✓ GITHUB_PERSONAL_ACCESS_TOKEN: Set
✓ ENABLE_GITHUB_MCP: True

AgentManager initialized with 1 WhatsApp MCP tools
GitHub MCP: enabled
✅ GitHub MCP enabled and configured

✓ AgentManager initialized
  - GitHub MCP enabled: True
  - GitHub MCP config: ['github']

✅ TEST 1 PASSED: Configuration successful

============================================================
TEST 2: Agent Creation with GitHub MCP
============================================================
...
✅ TEST 2 PASSED: Agent created successfully

============================================================
TEST 3: GitHub MCP Tool Usage
============================================================
...
✅ TEST 3 PASSED: GitHub MCP tool executed

============================================================
TEST SUMMARY
============================================================
Passed: 3/3

✅ ALL TESTS PASSED!
============================================================
```

---

## Step 5: Interactive Testing

Run the interactive mode to chat with the agent:

```bash
python test_github_mcp.py --interactive
```

**Try these commands:**

1. **List repositories:**
   ```
   You: List my GitHub repositories
   Agent: [Lists your repositories]
   ```

2. **Get repository info:**
   ```
   You: Tell me about the whatsapp_mcp repository
   Agent: [Shows repository details]
   ```

3. **Check recent activity:**
   ```
   You: What are my recent GitHub notifications?
   Agent: [Shows notifications]
   ```

4. **Search code:**
   ```
   You: Search for "claude_sdk" in my repositories
   Agent: [Shows search results]
   ```

5. **View pull requests:**
   ```
   You: Show me open pull requests in whatsapp_mcp
   Agent: [Lists PRs]
   ```

Type `exit` or `quit` to stop.

---

## Step 6: Test FastAPI Service Locally

Start the FastAPI service:

```bash
python src/python/main.py
```

**Expected startup logs:**

```
============================================================
🚀 WhatsApp MCP Service Starting...
============================================================
ANTHROPIC_API_KEY configured: True
WHATSAPP_ACCESS_TOKEN configured: True
GITHUB_PERSONAL_ACCESS_TOKEN configured: True
WhatsApp MCP Tools registered: 1
GitHub MCP enabled: True
  Available MCP servers: ['github']
============================================================
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Test the Health Endpoint

In another terminal:

```bash
curl http://localhost:8000/health | jq
```

**Expected response:**

```json
{
  "status": "healthy",
  "service": "whatsapp-mcp",
  "api_key_configured": true,
  "whatsapp_configured": true,
  "github_mcp_enabled": true,
  "github_token_configured": true,
  "active_agents": 0
}
```

### Test the Agent Endpoint

Send a test message:

```bash
curl -X POST http://localhost:8000/agent/process \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "message": "List my GitHub repositories"
  }' | jq
```

**Expected response:**

```json
{
  "response": "Here are your GitHub repositories:\n1. whatsapp_mcp - ...\n2. another-repo - ...",
  "status": "success"
}
```

---

## Step 7: Verify GitHub MCP Integration

### Check Logs

Look for these log messages in the FastAPI output:

```
✅ GitHub MCP enabled and configured
AgentManager initialized with 1 WhatsApp MCP tools
GitHub MCP: enabled
```

When an agent is created:

```
Agent created for +1234567890 with 1 MCP tools
  Additional MCP servers: ['github']
Claude SDK initialized with model: claude-3-5-sonnet-20241022
WhatsApp tools to register: 1
Additional MCP servers: ['github']
Registered WhatsApp MCP tools: ['send_whatsapp']
Registered MCP server: github
Total MCP servers configured: 2
Allowed tools: ['mcp__whatsapp_tools__send_whatsapp', 'mcp__github__*']
```

### Verify Claude Can Access GitHub

The agent should be able to:

- ✅ List your repositories
- ✅ Read repository content
- ✅ View pull requests
- ✅ Check workflow status
- ✅ Search code

---

## Troubleshooting

### Issue 1: "GITHUB_PERSONAL_ACCESS_TOKEN not set"

**Solution:**
```bash
export GITHUB_PERSONAL_ACCESS_TOKEN="ghp_..."
```

### Issue 2: "GitHub MCP not available"

**Cause:** Token validation failed

**Solution:**
1. Check token is valid: https://github.com/settings/tokens
2. Verify token hasn't expired
3. Ensure token has `repo` scope

### Issue 3: "Claude SDK client initialization failed"

**Cause:** Claude Code CLI not installed

**Solution:**
```bash
npm install -g @anthropic-ai/claude-code
claude --version
```

### Issue 4: Agent returns "I don't have access to GitHub"

**Cause:** GitHub MCP not enabled

**Solution:**
```bash
export ENABLE_GITHUB_MCP="true"
```

Restart the service.

### Issue 5: "HTTP 401 Unauthorized" from GitHub API

**Cause:** Invalid GitHub token

**Solution:**
1. Regenerate token at: https://github.com/settings/tokens
2. Update environment variable
3. Restart service

---

## Success Criteria for Phase I

Before moving to Phase II (Render deployment), verify:

- ✅ All automated tests pass (`python test_github_mcp.py`)
- ✅ Interactive mode works with GitHub commands
- ✅ Health endpoint shows `github_mcp_enabled: true`
- ✅ Agent can list your GitHub repositories
- ✅ No errors in service logs
- ✅ Agent logs show "Additional MCP servers: ['github']"

---

## Next Steps

Once Phase I testing is complete:

1. **Commit changes:**
   ```bash
   git add .
   git commit -m "Add GitHub MCP integration (Phase I)"
   ```

2. **Move to Phase II:** Deploy to Render with GitHub MCP

3. **Phase III:** Add per-user GitHub credentials

---

## Quick Test Commands

```bash
# Run all tests
python test_github_mcp.py

# Interactive mode
python test_github_mcp.py --interactive

# Start service
python src/python/main.py

# Health check
curl http://localhost:8000/health | jq

# Test agent
curl -X POST http://localhost:8000/agent/process \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1234567890", "message": "List my repos"}' | jq
```

---

## Files Modified in Phase I

- ✅ `src/python/github_mcp/__init__.py` (new)
- ✅ `src/python/github_mcp/server.py` (new)
- ✅ `src/python/sdk/claude_sdk.py` (updated)
- ✅ `src/python/agents/agent.py` (updated)
- ✅ `src/python/agents/manager.py` (updated)
- ✅ `src/python/main.py` (updated)
- ✅ `test_github_mcp.py` (new)
- ✅ `requirements.txt` (updated)
- ✅ `PHASE_I_TESTING.md` (new)

---

**Questions or issues?** Check the logs carefully and verify all environment variables are set correctly.
