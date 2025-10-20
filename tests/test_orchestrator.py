#!/usr/bin/env python3
"""Test collaborative orchestrator"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'python'))

from agents.collaborative.orchestrator import CollaborativeOrchestrator


async def test_orchestrator():
    """Test end-to-end orchestration"""

    print("=" * 60)
    print("🧪 Testing Collaborative Orchestrator")
    print("=" * 60)

    # Create orchestrator (no MCP servers needed for Phase 1 test)
    orchestrator = CollaborativeOrchestrator(mcp_servers={})

    # Test webapp generation
    response = await orchestrator.build_webapp(
        "Build a modern todo list app with dark theme"
    )

    # Print result
    print("\n" + "=" * 60)
    print("📱 WhatsApp Response:")
    print("=" * 60)
    print(response)
    print("=" * 60)

    # Cleanup
    await orchestrator.cleanup()

    print("\n✅ Orchestrator test passed!")


if __name__ == "__main__":
    asyncio.run(test_orchestrator())
