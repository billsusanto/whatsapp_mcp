#!/usr/bin/env python3
"""
Simple test script for Claude Agent SDK in Docker
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

# Define test tools
@tool("get_weather", "Get the weather for a location", {"location": str})
async def get_weather_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Test MCP tool - returns mock weather data"""
    location = args.get('location', 'Unknown')
    print(f"\n🔧 [TOOL CALLED] get_weather(location='{location}')")

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


async def test_in_docker():
    """Test Claude SDK in Docker environment"""

    print("=" * 70)
    print("🐳 Testing Claude Agent SDK in Docker")
    print("=" * 70)

    # Check environment
    print("\n1. Checking ANTHROPIC_API_KEY...")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return
    print(f"✅ API key configured: {api_key[:8]}...{api_key[-4:]}")

    # Initialize Claude SDK
    print("\n2. Initializing Claude SDK with MCP tools...")
    try:
        claude_sdk = ClaudeSDK(
            system_prompt="You are a helpful assistant with access to tools.",
            available_mcp_servers={"test_tools": [get_weather_tool, calculate_tool]}
        )
        print("✅ Claude SDK initialized")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test 1: Weather query
    print("\n" + "=" * 70)
    print("TEST 1: Weather Query")
    print("=" * 70)

    test_message = "What's the weather in Tokyo?"
    print(f"\n👤 User: {test_message}")

    try:
        response = await claude_sdk.send_message(test_message)
        print(f"\n🤖 Claude: {response}")
        print("\n✅ Test 1 passed!")
    except Exception as e:
        print(f"\n❌ Test 1 failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test 2: Calculator
    print("\n" + "=" * 70)
    print("TEST 2: Calculator")
    print("=" * 70)

    test_message_2 = "What is 50 multiplied by 75?"
    print(f"\n👤 User: {test_message_2}")

    try:
        response_2 = await claude_sdk.send_message(test_message_2)
        print(f"\n🤖 Claude: {response_2}")
        print("\n✅ Test 2 passed!")
    except Exception as e:
        print(f"\n❌ Test 2 failed: {e}")
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
    print("✅ Docker tests completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_in_docker())
