# Vercel Setup Checklist

## System Requirements Compliance

Based on Claude Agent SDK requirements, this project is configured for Vercel deployment.

### ✅ Runtime Dependencies

- **Node.js 18+**: Configured via `NODE_VERSION=20` in vercel.json
- **Claude Code CLI**: Installed via `npm install -g @anthropic-ai/claude-code` during build
- **SDK Package**: `@anthropic-ai/claude-agent-sdk` in dependencies

### ✅ Resource Allocation

Configured in `vercel.json`:
- **Memory**: 1024MB (1GiB RAM) - meets recommended 1GiB requirement
- **Max Duration**: 60 seconds - allows time for AI processing
- **CPU**: Automatically allocated by Vercel based on memory tier

### ✅ Network Access

- **Outbound HTTPS to api.anthropic.com**: Allowed by default on Vercel
- **WhatsApp API access**: Allowed (graph.facebook.com)
- **No MCP servers needed**: Using cloud runtime with `CLAUDE_CODE_USE_REMOTE=1`

## Required Environment Variables in Vercel Dashboard

You must set these in your Vercel project settings:

1. **ANTHROPIC_API_KEY** - Your Anthropic API key
2. **WHATSAPP_ACCESS_TOKEN** - WhatsApp Business API token
3. **WHATSAPP_PHONE_NUMBER_ID** - Your WhatsApp phone number ID
4. **WHATSAPP_WEBHOOK_VERIFY_TOKEN** - Webhook verification token
5. **CLAUDE_CODE_USE_REMOTE** - Set to `1` (enables cloud runtime)
6. **AGENT_SYSTEM_PROMPT** - (Optional) Custom system prompt for the agent

## Deployment Steps

### 1. Connect to Vercel
```bash
# If not already connected
vercel login
vercel link
```

### 2. Set Environment Variables
Go to your Vercel dashboard → Project Settings → Environment Variables

Or use the CLI:
```bash
vercel env add ANTHROPIC_API_KEY
vercel env add WHATSAPP_ACCESS_TOKEN
vercel env add WHATSAPP_PHONE_NUMBER_ID
vercel env add WHATSAPP_WEBHOOK_VERIFY_TOKEN
vercel env add CLAUDE_CODE_USE_REMOTE
vercel env add AGENT_SYSTEM_PROMPT
```

### 3. Deploy
```bash
git push origin main
# Vercel will auto-deploy on push
```

Or manual deploy:
```bash
vercel --prod
```

## Verifying Deployment

### Check Build Logs
1. Go to Vercel Dashboard → Deployments
2. Click on latest deployment
3. Check "Building" logs for:
   - ✅ `npm install -g @anthropic-ai/claude-code` success
   - ✅ `npm install` completed
   - ✅ `npm run build` successful
4. Check "Functions" logs for runtime execution

### Test Webhook
1. Get your deployment URL: `https://your-project.vercel.app`
2. Test verification endpoint:
   ```bash
   curl "https://your-project.vercel.app/api/webhook?hub.mode=subscribe&hub.verify_token=YOUR_TOKEN&hub.challenge=test123"
   # Should return: test123
   ```

### Configure WhatsApp Webhook
1. Go to Meta Developer Console → WhatsApp → Configuration
2. Set webhook URL: `https://your-project.vercel.app/api/webhook`
3. Set verify token: Same as `WHATSAPP_WEBHOOK_VERIFY_TOKEN`
4. Click "Verify and Save"

## Troubleshooting

### "Claude Code executable not found"
- ✅ Fixed by installing `@anthropic-ai/claude-code` as dependency
- ✅ Code now uses `require.resolve('@anthropic-ai/claude-code/cli.js')` to find executable
- ✅ Explicitly sets `pathToClaudeCodeExecutable` option
- ✅ Check vercel.json has `installCommand` with `-g @anthropic-ai/claude-code`
- ✅ Check package.json has `postinstall` script
- 🔧 Optional: Set `CLAUDE_CODE_EXECUTABLE` env var to override path

### "Function timeout"
- Increase `maxDuration` in vercel.json (max 60s on Hobby plan, 300s on Pro)
- Consider using Vercel Pro for longer timeouts if needed

### "Out of memory"
- Increase `memory` in vercel.json functions config
- Maximum: 1024MB (Hobby), 3008MB (Pro)

### API Key Issues
- Verify `ANTHROPIC_API_KEY` is set in Vercel environment variables
- Check it's not prefixed with quotes or has extra whitespace
- Ensure it starts with `sk-ant-api03-`

## Resource Limits by Plan

| Feature | Hobby | Pro |
|---------|-------|-----|
| Memory | Up to 1024MB | Up to 3008MB |
| Duration | Up to 10s (default) | Up to 300s |
| Request Size | 4.5MB | 4.5MB |

Current config uses **1024MB / 60s** which works on both Hobby and Pro plans.

## Additional Notes

- **Node.js 20**: Explicitly set via environment variable
- **No local file system**: Conversation history stored in-memory (will reset on function cold start)
- **Serverless**: Each request may run on a different instance
- **Cold starts**: First request after idle may be slower
- **For production**: Consider using Redis/database for conversation history persistence
