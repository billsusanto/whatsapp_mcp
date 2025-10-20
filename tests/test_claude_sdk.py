#!/usr/bin/env python3
"""
Simple test script for Claude Agent SDK with MCP tools
Tests the SDK without any WhatsApp integration
"""

import sys
import os
import asyncio
from typing import Any

# Suppress bytecode generation
sys.dont_write_bytecode = True

# IMPORTANT: Import mcp.types first to avoid import order issues
import mcp.types

# Add src/python to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'python'))

from claude_agent_sdk import tool
from sdk.claude_sdk import ClaudeSDK
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# Define a simple test tool
@tool("get_weather", "Get the weather for a location", {"location": str})
async def get_weather_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Test MCP tool - returns mock weather data"""
    location = args.get('location', 'Unknown')
    print(f"\n🔧 [TOOL CALLED] get_weather(location='{location}')")

    # Mock weather data
    weather_data = {
        "San Francisco": "Sunny, 72°F",
        "New York": "Cloudy, 65°F",
        "London": "Rainy, 58°F",
        "Tokyo": "Clear, 68°F"
    }

    weather = weather_data.get(location, f"Weather data not available for {location}")

    return {
        "content": [{
            "type": "text",
            "text": f"Weather in {location}: {weather}"
        }]
    }


@tool("calculate", "Perform a calculation", {"expression": str})
async def calculate_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Test MCP tool - performs simple calculations"""
    expression = args.get('expression', '')
    print(f"\n🔧 [TOOL CALLED] calculate(expression='{expression}')")

    try:
        # Safe eval for basic math
        result = eval(expression, {"__builtins__": {}}, {})
        return {
            "content": [{
                "type": "text",
                "text": f"Result: {expression} = {result}"
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error calculating '{expression}': {str(e)}"
            }],
            "isError": True
        }


async def test_claude_sdk():
    """Test Claude SDK with MCP tools"""

    print("=" * 70)
    print("🧪 Testing Claude Agent SDK with MCP Tools")
    print("=" * 70)

    # Check environment
    print("\n1. Checking ANTHROPIC_API_KEY...")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        print("   Please set it in .env file")
        return
    print(f"✅ API key configured: {api_key[:8]}...{api_key[-4:]}")

    # Initialize Claude SDK with tools
    print("\n2. Initializing Claude SDK with MCP tools...")
    try:
        claude_sdk = ClaudeSDK(
            system_prompt="You are a helpful assistant with access to weather and calculator tools.",
            available_mcp_servers={"test_tools": [get_weather_tool, calculate_tool]}
        )
        print("✅ Claude SDK initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Claude SDK: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test 1: Simple conversation
    print("\n" + "=" * 70)
    print("TEST 1: Simple Conversation (no tool use)")
    print("=" * 70)

    test_message_1 = "Hello! Can you introduce yourself?"
    print(f"\n👤 User: {test_message_1}")

    try:
        response_1 = await claude_sdk.send_message(test_message_1)
        print(f"\n🤖 Claude: {response_1}")
        print("\n✅ Test 1 passed!")
    except Exception as e:
        print(f"\n❌ Test 1 failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test 2: Tool use - Weather
    print("\n" + "=" * 70)
    print("TEST 2: Tool Use - Weather Query")
    print("=" * 70)

    test_message_2 = "What's the weather like in San Francisco?"
    print(f"\n👤 User: {test_message_2}")

    try:
        response_2 = await claude_sdk.send_message(test_message_2)
        print(f"\n🤖 Claude: {response_2}")
        print("\n✅ Test 2 passed!")
    except Exception as e:
        print(f"\n❌ Test 2 failed: {e}")
        import traceback
        traceback.print_exc()

    # Test 3: Tool use - Calculator
    print("\n" + "=" * 70)
    print("TEST 3: Tool Use - Calculator")
    print("=" * 70)

    test_message_3 = "What is 15 multiplied by 23?"
    print(f"\n👤 User: {test_message_3}")

    try:
        response_3 = await claude_sdk.send_message(test_message_3)
        print(f"\n🤖 Claude: {response_3}")
        print("\n✅ Test 3 passed!")
    except Exception as e:
        print(f"\n❌ Test 3 failed: {e}")
        import traceback
        traceback.print_exc()

    # Test 4: Multiple tool uses
    print("\n" + "=" * 70)
    print("TEST 4: Multiple Tool Uses")
    print("=" * 70)

    test_message_4 = "What's the weather in Tokyo and London? Also calculate 100 + 250."
    print(f"\n👤 User: {test_message_4}")

    try:
        response_4 = await claude_sdk.send_message(test_message_4)
        print(f"\n🤖 Claude: {response_4}")
        print("\n✅ Test 4 passed!")
    except Exception as e:
        print(f"\n❌ Test 4 failed: {e}")
        import traceback
        traceback.print_exc()

    # Cleanup
    print("\n" + "=" * 70)
    print("Cleaning up...")
    try:
        await claude_sdk.close()
        print("✅ Claude SDK closed")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")

    print("\n" + "=" * 70)
    print("✅ All tests completed!")
    print("=" * 70)


async def interactive_mode():
    """Interactive chat mode with Claude SDK"""

    print("=" * 70)
    print("💬 Interactive Mode - Chat with Claude Agent SDK")
    print("=" * 70)
    print("\nAvailable tools:")
    print("  - get_weather(location) - Get weather for a location")
    print("  - calculate(expression) - Perform calculations")
    print("\nType 'exit' or 'quit' to end the conversation")
    print("=" * 70)

    # Check environment
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return

    # Initialize Claude SDK
    try:
        claude_sdk = ClaudeSDK(
            system_prompt="You are a helpful assistant with access to weather and calculator tools.",
            available_mcp_servers={"test_tools": [get_weather_tool, calculate_tool]}
        )
        print("\n✅ Connected to Claude\n")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return

    # Chat loop
    try:
        while True:
            # Get user input
            user_input = input("\n👤 You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye!")
                break

            # Send message to Claude
            try:
                print("\n🤖 Claude: ", end="", flush=True)
                response = await claude_sdk.send_message(user_input)
                print(response)
            except Exception as e:
                print(f"\n❌ Error: {e}")

    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
    finally:
        await claude_sdk.close()
        print("✅ Connection closed\n")


if __name__ == "__main__":
    import sys

    # Check for interactive mode flag
    if len(sys.argv) > 1 and sys.argv[1] in ['-i', '--interactive', 'chat']:
        asyncio.run(interactive_mode())
    else:
        asyncio.run(test_claude_sdk())
