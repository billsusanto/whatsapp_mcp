#!/bin/bash

# Start the FastAPI server for local testing

echo "=================================================="
echo "🚀 Starting WhatsApp MCP Server (GitHub Bot Enabled)"
echo "=================================================="
echo ""
echo "Server will start on: http://localhost:8000"
echo "GitHub webhook endpoint: http://localhost:8000/github/webhook"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=================================================="
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
fi

# Start the server with reload for development
cd /Users/billsusanto/Documents/Projects/whatsapp_mcp
python3 -m uvicorn src.python.main:app --reload --port 8000 --host 0.0.0.0
