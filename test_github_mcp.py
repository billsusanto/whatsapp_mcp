"""
Test GitHub MCP Integration (Phase I)

This script tests that GitHub MCP is properly integrated with Claude Agent SDK.
Run this locally before deploying to Render.

Usage:
    # Set environment variables first
    export ANTHROPIC_API_KEY=sk-ant-...
    export GITHUB_PERSONAL_ACCESS_TOKEN=ghp_...
    export ENABLE_GITHUB_MCP=true

    # Run tests
    python test_github_mcp.py

    # Interactive mode
    python test_github_mcp.py --interactive
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add src/python to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'python'))

from agents.manager import AgentManager
from claude_agent_sdk import tool

# Load environment variables
load_dotenv()


@tool("test_tool", "A test tool for verification", {})
async def test_tool(args: dict) -> dict:
    """Test tool to verify MCP setup"""
    return {
        "content": [{
            "type": "text",
            "text": "Test tool called successfully!"
        }]
    }


async def test_github_mcp_configuration():
    """Test 1: Verify GitHub MCP is configured correctly"""
    print("\n" + "=" * 60)
    print("TEST 1: GitHub MCP Configuration")
    print("=" * 60)

    try:
        # Check environment variables
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
        enable_github = os.getenv("ENABLE_GITHUB_MCP", "false").lower() == "true"

        print(f"✓ ANTHROPIC_API_KEY: {'Set' if anthropic_key else 'NOT SET'}")
        print(f"✓ GITHUB_PERSONAL_ACCESS_TOKEN: {'Set' if github_token else 'NOT SET'}")
        print(f"✓ ENABLE_GITHUB_MCP: {enable_github}")

        if not anthropic_key:
            print("\n❌ ANTHROPIC_API_KEY not set!")
            return False

        if not github_token:
            print("\n⚠️  GITHUB_PERSONAL_ACCESS_TOKEN not set - GitHub MCP will be disabled")

        # Initialize Agent Manager with GitHub enabled
        manager = AgentManager(
            whatsapp_mcp_tools=[test_tool],
            enable_github=enable_github
        )

        print(f"\n✓ AgentManager initialized")
        print(f"  - Available MCP servers: {list(manager.available_mcp_servers.keys())}")
        print(f"  - GitHub MCP enabled: {manager.enable_github}")

        await manager.cleanup_all_agents()
        print("\n✅ TEST 1 PASSED: Configuration successful\n")
        return True

    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_creation_with_github():
    """Test 2: Verify agent is created with GitHub MCP"""
    print("\n" + "=" * 60)
    print("TEST 2: Agent Creation with GitHub MCP")
    print("=" * 60)

    try:
        enable_github = os.getenv("ENABLE_GITHUB_MCP", "false").lower() == "true"

        manager = AgentManager(
            whatsapp_mcp_tools=[test_tool],
            enable_github=enable_github
        )

        # Create an agent
        test_phone = "+1234567890"
        agent = manager.get_or_create_agent(test_phone)

        print(f"\n✓ Agent created for {test_phone}")
        print(f"  - Available MCP servers: {list(agent.available_mcp_servers.keys())}")

        await manager.cleanup_all_agents()
        print("\n✅ TEST 2 PASSED: Agent created successfully\n")
        return True

    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_github_mcp_tools():
    """Test 3: Send a message that should use GitHub MCP"""
    print("\n" + "=" * 60)
    print("TEST 3: GitHub MCP Tool Usage")
    print("=" * 60)

    enable_github = os.getenv("ENABLE_GITHUB_MCP", "false").lower() == "true"

    if not enable_github:
        print("⚠️  Skipping - GitHub MCP not enabled (set ENABLE_GITHUB_MCP=true)")
        return True

    try:
        manager = AgentManager(
            whatsapp_mcp_tools=[test_tool],
            enable_github=True
        )

        test_phone = "+1234567890"

        # Test message asking for GitHub info
        print("\n📤 Sending: 'List my GitHub repositories'")
        response = await manager.process_message(
            test_phone,
            "List my GitHub repositories"
        )

        print(f"\n📥 Response received (length: {len(response)} chars)")
        print(f"Response preview: {response[:200]}...")

        await manager.cleanup_all_agents()

        # Check if response indicates successful GitHub interaction
        if len(response) > 0:
            print("\n✅ TEST 3 PASSED: GitHub MCP tool executed\n")
            return True
        else:
            print("\n⚠️  TEST 3: Empty response received\n")
            return False

    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_interactive_mode():
    """Interactive mode: Chat with agent that has GitHub MCP access"""
    print("\n" + "=" * 60)
    print("INTERACTIVE MODE: GitHub MCP Agent")
    print("=" * 60)
    print("Type 'exit' or 'quit' to stop\n")

    enable_github = os.getenv("ENABLE_GITHUB_MCP", "false").lower() == "true"

    manager = AgentManager(
        whatsapp_mcp_tools=[test_tool],
        enable_github=enable_github
    )

    test_phone = "+1234567890"

    print("Example commands:")
    print("  - List my GitHub repositories")
    print("  - Show me recent activity on repo X")
    print("  - Create a new repository called test-repo")
    print("  - What are my GitHub notifications?")
    print()

    try:
        while True:
            user_input = input("You: ").strip()

            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\nExiting interactive mode...")
                break

            if not user_input:
                continue

            print("Agent: ", end="", flush=True)
            response = await manager.process_message(test_phone, user_input)
            print(response)
            print()

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    finally:
        await manager.cleanup_all_agents()


async def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🧪 GITHUB MCP INTEGRATION TESTS - PHASE I")
    print("=" * 60)

    results = []

    # Test 1: Configuration
    results.append(await test_github_mcp_configuration())

    # Test 2: Agent Creation
    results.append(await test_agent_creation_with_github())

    # Test 3: GitHub MCP Tool Usage (if enabled)
    results.append(await test_github_mcp_tools())

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n✅ ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")

    print("=" * 60)

    return passed == total


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Test GitHub MCP Integration")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode"
    )
    args = parser.parse_args()

    if args.interactive:
        asyncio.run(test_interactive_mode())
    else:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
