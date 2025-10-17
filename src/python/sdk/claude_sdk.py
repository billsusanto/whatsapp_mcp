"""
Claude Agent SDK Wrapper

Wraps the Claude Agent SDK for easier agent management with tool use and MCP support
"""

import os
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, create_sdk_mcp_server
from typing import List, Dict, Optional, AsyncIterator


class ClaudeSDK:
    """Wrapper around Claude Agent SDK for agent interactions"""

    def __init__(self, system_prompt: Optional[str] = None, tools: Optional[List] = None):
        """
        Initialize Claude Agent SDK

        Args:
            system_prompt: Optional system prompt (defaults to env var)
            tools: Optional list of MCP tools (decorated with @tool)
        """
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.system_prompt = system_prompt or os.getenv(
            "AGENT_SYSTEM_PROMPT",
            "You are a helpful WhatsApp assistant. Keep responses concise and friendly."
        )

        self.model = "claude-3-5-sonnet-20241022"
        self.tools = tools or []
        self.client = None
        self.mcp_server = None

        print(f"Claude SDK initialized with model: {self.model}")
        print(f"Tools to register: {len(self.tools)}")

    async def initialize_client(self):
        """Initialize the async Claude SDK client"""
        if not self.client:
            # Create MCP server if tools are provided
            options = None
            if self.tools:
                self.mcp_server = create_sdk_mcp_server(
                    name="whatsapp_tools",
                    version="1.0.0",
                    tools=self.tools
                )

                # Build allowed tools list (format: mcp__servername__toolname)
                allowed_tools = []
                for tool_func in self.tools:
                    # SdkMcpTool objects have a .name attribute
                    tool_name = getattr(tool_func, 'name', 'unknown')
                    allowed_tools.append(f"mcp__whatsapp_tools__{tool_name}")

                options = ClaudeAgentOptions(
                    mcp_servers={"whatsapp_tools": self.mcp_server},
                    allowed_tools=allowed_tools
                )
                print(f"Created MCP server with {len(self.tools)} tools: {allowed_tools}")

            # Initialize client with options
            self.client = ClaudeSDKClient(options=options)
            await self.client.__aenter__()
            print("Claude SDK client initialized")

    async def send_message(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Send a message to Claude and get response

        Args:
            user_message: The user's message text
            conversation_history: List of previous messages (ClaudeSDKClient maintains conversation context)

        Returns:
            Claude's response text
        """
        if not self.client:
            await self.initialize_client()

        try:
            # Send query to agent
            await self.client.query(user_message)

            # Collect response from assistant
            response_text = ""
            async for message in self.client.receive_response():
                # Check if this is an AssistantMessage
                if type(message).__name__ == 'AssistantMessage':
                    # Extract text from content blocks
                    content = getattr(message, 'content', [])
                    for block in content:
                        # TextBlock has a 'text' attribute
                        if type(block).__name__ == 'TextBlock':
                            text_content = getattr(block, 'text', '')
                            response_text += text_content

            if not response_text:
                response_text = "I apologize, but I couldn't generate a response. Please try again."

            return response_text.strip()

        except Exception as e:
            error_msg = f"Error in Claude SDK send_message: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            raise Exception(error_msg)

    async def stream_message(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> AsyncIterator[str]:
        """
        Stream Claude's response (for long messages)

        Args:
            user_message: The user's message
            conversation_history: Not used (client maintains context)

        Yields:
            Text chunks as they arrive
        """
        if not self.client:
            await self.initialize_client()

        try:
            await self.client.query(user_message)

            async for message in self.client.receive_response():
                # Check if this is an AssistantMessage
                if type(message).__name__ == 'AssistantMessage':
                    # Extract text from content blocks
                    content = getattr(message, 'content', [])
                    for block in content:
                        # TextBlock has a 'text' attribute
                        if type(block).__name__ == 'TextBlock':
                            text_content = getattr(block, 'text', '')
                            if text_content:
                                yield text_content

        except Exception as e:
            error_msg = f"Error in Claude SDK stream_message: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            raise Exception(error_msg)

    async def close(self):
        """Clean up the client"""
        if self.client:
            try:
                await self.client.__aexit__(None, None, None)
                print("Claude SDK client closed")
            except Exception as e:
                print(f"Error closing Claude SDK client: {str(e)}")
