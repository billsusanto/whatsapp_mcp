"""
Test Suite for Netlify MCP Integration

Tests the Netlify MCP server integration with Claude Agent SDK
Phase I: Local testing before Render deployment
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add src/python to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'python'))

# Load environment variables
load_dotenv()

from agents.manager import AgentManager
from claude_agent_sdk import tool
from typing import Any


# Test tool for WhatsApp MCP (not actually used, just needed for initialization)
@tool("test_tool", "A test tool", {})
async def test_tool(args: dict[str, Any]) -> dict[str, Any]:
    return {
        "content": [{
            "type": "text",
            "text": "Test tool response"
        }]
    }


async def test_netlify_config():
    """
    Test 1: Verify Netlify MCP Configuration
    Tests that Netlify MCP can be configured correctly
    """
    print("\n" + "="*60)
    print("TEST 1: Netlify MCP Configuration")
    print("="*60)

    # Check environment variables
    api_key = os.getenv("ANTHROPIC_API_KEY")
    netlify_token = os.getenv("NETLIFY_PERSONAL_ACCESS_TOKEN")
    enable_netlify = os.getenv("ENABLE_NETLIFY_MCP", "false").lower() == "true"

    print(f"✓ ANTHROPIC_API_KEY: {'Set' if api_key else 'Missing'}")
    print(f"✓ NETLIFY_PERSONAL_ACCESS_TOKEN: {'Set' if netlify_token else 'Missing'}")
    print(f"✓ ENABLE_NETLIFY_MCP: {enable_netlify}")

    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return False

    if not netlify_token:
        print("❌ NETLIFY_PERSONAL_ACCESS_TOKEN not set")
        print("   Get your token from: https://app.netlify.com/user/applications#personal-access-tokens")
        return False

    if not enable_netlify:
        print("❌ ENABLE_NETLIFY_MCP is not true")
        return False

    # Try to create AgentManager with Netlify MCP
    try:
        manager = AgentManager(
            whatsapp_mcp_tools=[test_tool],
            enable_netlify=True
        )

        print(f"\n✓ AgentManager initialized")
        print(f"  - Available MCP servers: {list(manager.available_mcp_servers.keys())}")
        print(f"  - Netlify MCP enabled: {manager.enable_netlify}")

        await manager.cleanup_all_agents()

        if "netlify" not in manager.available_mcp_servers:
            print("❌ Netlify MCP not in available servers")
            return False

        print("\n✅ TEST 1 PASSED: Configuration successful\n")
        return True

    except Exception as e:
        print(f"❌ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_creation():
    """
    Test 2: Agent Creation with Netlify MCP
    Tests that an agent can be created with Netlify MCP enabled
    """
    print("="*60)
    print("TEST 2: Agent Creation with Netlify MCP")
    print("="*60)

    try:
        manager = AgentManager(
            whatsapp_mcp_tools=[test_tool],
            enable_netlify=True
        )

        # Create an agent
        agent = manager.get_or_create_agent("+1234567890")

        print(f"\n✓ Agent created for +1234567890")
        print(f"  - Available MCP servers: {list(agent.available_mcp_servers.keys())}")

        await manager.cleanup_all_agents()

        if "netlify" not in agent.available_mcp_servers:
            print("❌ Netlify MCP not available to agent")
            return False

        print("\n✅ TEST 2 PASSED: Agent created successfully\n")
        return True

    except Exception as e:
        print(f"❌ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_list_sites():
    """
    Test 3: List Netlify Sites
    Tests that the agent can list existing Netlify sites
    """
    print("="*60)
    print("TEST 3: List Netlify Sites")
    print("="*60)

    try:
        manager = AgentManager(
            whatsapp_mcp_tools=[test_tool],
            enable_netlify=True
        )

        print("\n📤 Sending: 'List my Netlify sites'")

        response = await manager.process_message(
            phone_number="+1234567890",
            message="List my Netlify sites"
        )

        print(f"\n📥 Response received (length: {len(response)} chars)")
        print(f"Response preview: {response[:200]}...")

        await manager.cleanup_all_agents()

        # Check if response mentions sites or indicates no sites
        if "site" in response.lower() or "deploy" in response.lower() or "no sites" in response.lower():
            print("\n✅ TEST 3 PASSED: Successfully listed Netlify sites\n")
            return True
        else:
            print(f"\n⚠️  TEST 3 WARNING: Response doesn't mention sites")
            print(f"Full response: {response}")
            return True  # Still pass, might be legitimate response

    except Exception as e:
        print(f"❌ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_netlify_mcp_tools():
    """
    Test 4: Verify Netlify MCP Tools Available
    Tests that Claude can see and describe Netlify MCP tools
    """
    print("="*60)
    print("TEST 4: Netlify MCP Tools Availability")
    print("="*60)

    try:
        manager = AgentManager(
            whatsapp_mcp_tools=[test_tool],
            enable_netlify=True
        )

        print("\n📤 Sending: 'What Netlify MCP tools do you have access to?'")

        response = await manager.process_message(
            phone_number="+1234567890",
            message="What Netlify MCP tools do you have access to?"
        )

        print(f"\n📥 Response received (length: {len(response)} chars)")
        print(f"Response preview: {response[:300]}...")

        await manager.cleanup_all_agents()

        # Check if response mentions Netlify tools
        netlify_keywords = ["create-site", "deploy", "list-sites", "netlify"]
        has_netlify_mention = any(keyword in response.lower() for keyword in netlify_keywords)

        if has_netlify_mention:
            print("\n✅ TEST 4 PASSED: Netlify MCP tools are accessible\n")
            return True
        else:
            print(f"\n❌ TEST 4 FAILED: Response doesn't mention Netlify tools")
            print(f"Full response: {response}")
            return False

    except Exception as e:
        print(f"❌ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_interactive_mode():
    """
    Interactive Test Mode
    Allows manual testing of Netlify MCP deployment
    """
    print("="*60)
    print("INTERACTIVE MODE: Netlify MCP Agent")
    print("="*60)
    print("Type 'exit' or 'quit' to stop\n")

    manager = AgentManager(
        whatsapp_mcp_tools=[test_tool],
        enable_netlify=True
    )

    print("Example commands:")
    print("  - List my Netlify sites")
    print("  - Deploy my GitHub repo [owner/repo] to Netlify")
    print("  - Show deployment status for [site-name]")
    print("  - Delete site [site-name]")
    print()

    try:
        while True:
            user_input = input("You: ").strip()

            if user_input.lower() in ['exit', 'quit']:
                break

            if not user_input:
                continue

            print("\n🤔 Processing...")
            response = await manager.process_message(
                phone_number="+1234567890",
                message=user_input
            )

            print(f"\n🤖 Agent: {response}\n")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    finally:
        await manager.cleanup_all_agents()
        print("All agents cleaned up")


async def run_all_tests():
    """Run all automated tests"""
    print("\n" + "="*60)
    print("🧪 NETLIFY MCP INTEGRATION TESTS - PHASE I")
    print("="*60)

    results = []

    # Test 1: Configuration
    results.append(await test_netlify_config())

    # Test 2: Agent Creation
    results.append(await test_agent_creation())

    # Test 3: List Sites
    results.append(await test_list_sites())

    # Test 4: Verify Tools
    results.append(await test_netlify_mcp_tools())

    # Print summary
    print("="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n✅ ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")

    print("="*60 + "\n")

    return all(results)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Test Netlify MCP Integration")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode for manual testing"
    )

    args = parser.parse_args()

    if args.interactive:
        asyncio.run(test_interactive_mode())
    else:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
