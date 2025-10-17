"""
Claude Agent SDK Wrapper

Wraps the Claude Agent SDK for easier agent management with tool use and MCP support
"""

import os
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, create_sdk_mcp_server
from typing import List, Dict, Optional, AsyncIterator


class ClaudeSDK:
    """Wrapper around Claude Agent SDK for agent interactions"""

    def __init__(
        self,
        system_prompt: Optional[str] = None,
        available_mcp_servers: Optional[Dict[str, any]] = None
    ):
        """
        Initialize Claude Agent SDK

        Args:
            system_prompt: Optional system prompt (defaults to env var)
            available_mcp_servers: Dict of MCP servers to make available to Claude
                                  Format: {"server_name": server_config or tools_list}
                                  Example: {
                                      "whatsapp": [send_whatsapp_tool],
                                      "github": {"url": "...", "headers": {...}}
                                  }
        """
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.system_prompt = system_prompt or os.getenv(
            "AGENT_SYSTEM_PROMPT",
            "You are a helpful WhatsApp assistant with access to GitHub. Keep responses concise and friendly."
        )

        self.model = "claude-3-5-sonnet-20241022"
        self.available_mcp_servers = available_mcp_servers or {}
        self.client = None

        print(f"Claude SDK initialized with model: {self.model}")
        print(f"Available MCP servers: {list(self.available_mcp_servers.keys())}")

    async def initialize_client(self):
        """Initialize the async Claude SDK client with available MCP servers"""
        if not self.client:
            # Build MCP servers dict and allowed tools list
            mcp_servers = {}
            allowed_tools = []

            # Process each available MCP server
            for server_name, server_config in self.available_mcp_servers.items():
                # Check if it's a list of tools (needs SDK MCP server wrapper)
                if isinstance(server_config, list):
                    # This is a list of @tool decorated functions
                    # Create an SDK MCP server for them
                    mcp_server = create_sdk_mcp_server(
                        name=server_name,
                        version="1.0.0",
                        tools=server_config
                    )
                    mcp_servers[server_name] = mcp_server

                    # Add individual tools to allowed list
                    for tool_func in server_config:
                        tool_name = getattr(tool_func, 'name', 'unknown')
                        allowed_tools.append(f"mcp__{server_name}__{tool_name}")

                    print(f"✓ Registered {server_name} MCP with {len(server_config)} tools")

                else:
                    # This is a server config dict (e.g., HTTP-based like GitHub)
                    mcp_servers[server_name] = server_config

                    # Allow all tools from this server using wildcard
                    allowed_tools.append(f"mcp__{server_name}__*")

                    print(f"✓ Registered {server_name} MCP server (HTTP)")

            # Create options with all MCP servers
            options = None
            if mcp_servers:
                options = ClaudeAgentOptions(
                    mcp_servers=mcp_servers,
                    allowed_tools=allowed_tools,
                    permission_mode='bypassPermissions'  # Auto-approve all tool usage
                )
                print(f"Total MCP servers: {len(mcp_servers)}")
                print(f"Allowed tools: {allowed_tools}")
                print(f"Permission mode: bypassPermissions")

            # Initialize client with options
            self.client = ClaudeSDKClient(options=options)
            await self.client.__aenter__()
            print("✅ Claude SDK client initialized")

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
