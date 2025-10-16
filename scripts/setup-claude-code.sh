#!/bin/bash
# Setup script to install Claude Code and make it accessible

echo "🔧 Installing Claude Code globally..."
npm install -g @anthropic-ai/claude-code

echo "📍 Finding Claude Code executable..."

# Try to find the executable in common locations
if command -v claude-code &> /dev/null; then
    CLAUDE_PATH=$(which claude-code)
    echo "✅ Found claude-code at: $CLAUDE_PATH"
elif [ -f "/usr/local/bin/claude-code" ]; then
    CLAUDE_PATH="/usr/local/bin/claude-code"
    echo "✅ Found claude-code at: $CLAUDE_PATH"
elif [ -f "/vercel/.npm/_npx/*/node_modules/.bin/claude-code" ]; then
    CLAUDE_PATH=$(ls /vercel/.npm/_npx/*/node_modules/.bin/claude-code 2>/dev/null | head -1)
    echo "✅ Found claude-code at: $CLAUDE_PATH"
else
    echo "⚠️  Claude Code not found in standard locations"
    echo "Will fall back to require.resolve() at runtime"
fi

echo "✅ Setup complete!"
