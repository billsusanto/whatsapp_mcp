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
                                      "github": {"command": "npx", "args": [...], "env": {...}},
                                      "netlify": {"command": "npx", "args": [...], "env": {...}}
                                  }
        """
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        # Build system prompt with MCP server info
        base_prompt = system_prompt or os.getenv(
            "AGENT_SYSTEM_PROMPT",
            "You are a professional and helpful assistant. Keep responses concise and friendly."
        )

        # If WhatsApp MCP is available, enhance prompt
        if available_mcp_servers and "whatsapp" in available_mcp_servers:
            base_prompt += """

You have access to WhatsApp MCP tools for messaging. Available operations include:
- send_whatsapp: Send WhatsApp messages to users

IMPORTANT: Use WhatsApp MCP tools (mcp__whatsapp__*) when you need to send messages to users.
"""

        # If GitHub MCP is available, enhance prompt
        if available_mcp_servers and "github" in available_mcp_servers:
            base_prompt += """

You have access to GitHub MCP tools for repository management. Available operations include:
- list_repositories: List user's repositories
- get_repository: Get details about a specific repository
- create_repository: Create a new repository
- search_repositories: Search for repositories
- create_or_update_file: Create or update files in a repository
- search_code: Search for code across repositories
- create_issue: Create issues
- create_pull_request: Create pull requests
- fork_repository: Fork a repository
- create_branch: Create branches

IMPORTANT: Always use the GitHub MCP tools (mcp__github__*) for GitHub operations instead of bash/curl/gh CLI.
"""

        # If Netlify MCP is available, enhance prompt
        if available_mcp_servers and "netlify" in available_mcp_servers:
            base_prompt += """

You have access to Netlify MCP tools for site deployment and management. Available operations include:
- create-site: Create new Netlify sites
- deploy-site: Deploy sites to production or preview
- list-sites: View all user's Netlify sites
- get-site-info: Get detailed information about a site
- delete-site: Remove Netlify sites
- trigger-build: Start new builds
- list-deploys: View deployment history for a site
- get-deploy-info: Get details about a specific deployment
- cancel-deploy: Stop running deployments
- restore-deploy: Rollback to a previous deployment
- set-env-vars: Configure environment variables
- get-env-var: Retrieve environment variables
- link-site: Link a local directory to a Netlify site
- unlink-site: Disconnect a site linkage

IMPORTANT:
1. Always use Netlify MCP tools (mcp__netlify__*) for deployment operations
2. When deploying from GitHub repos, you may need to ask the user for:
   - Github account (https://github.com/billsusanto)
   - Build command (always npm run build), Build directory is root, Add netlify.toml which must also include devDependencies from package.json
   - Publish directory (check netlify for similar or same name as github repo)
3. After successful deployment, always provide the live URL to the user
4. Monitor deployment progress and report the status
"""

        self.system_prompt = base_prompt

        self.model = "claude-sonnet-4-5-20250929"
        self.max_tokens = 4096
        self.available_mcp_servers = available_mcp_servers or {}
        self.client = None
        self._is_initialized = False
        self._is_closed = False

        print(f"Claude SDK initialized with model: {self.model} (Sonnet 4.5)")
        print(f"Max tokens: {self.max_tokens} (memory optimized)")
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
                    model=self.model,  # Use Claude Sonnet 4.5
                    mcp_servers=mcp_servers,
                    allowed_tools=allowed_tools,
                    permission_mode='bypassPermissions',  # Auto-approve all tool usage
                    system_prompt=self.system_prompt  # Pass enhanced system prompt
                )
                print(f"Total MCP servers: {len(mcp_servers)}")
                print(f"Allowed tools: {allowed_tools}")
                print(f"Permission mode: bypassPermissions")
            else:
                # No MCP servers, but still need to specify model
                options = ClaudeAgentOptions(
                    model=self.model,  # Use Claude Sonnet 4.5
                    system_prompt=self.system_prompt
                )

            # Initialize client with options
            try:
                self.client = ClaudeSDKClient(options=options)
                await self.client.__aenter__()
                self._is_initialized = True
                print("✅ Claude SDK client initialized successfully")
                print(f"   Model: {self.model} (Sonnet 4.5)")
                print(f"   Active MCP servers: {list(mcp_servers.keys()) if mcp_servers else 'None'}")
            except Exception as e:
                print(f"❌ Error initializing Claude SDK client: {e}")
                import traceback
                traceback.print_exc()
                raise

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
        # Guard against double-close
        if self._is_closed:
            return

        if self.client and self._is_initialized:
            try:
                await self.client.__aexit__(None, None, None)
                self._is_closed = True
                print("Claude SDK client closed")
            except RuntimeError as e:
                # Suppress cancel scope errors - these are expected during shutdown
                if "cancel scope" in str(e).lower():
                    self._is_closed = True
                    print("Claude SDK client closed (suppressed cancel scope cleanup)")
                else:
                    print(f"Error closing Claude SDK client: {str(e)}")
                    raise
            except Exception as e:
                print(f"Error closing Claude SDK client: {str(e)}")
                # Still mark as closed to prevent retry
                self._is_closed = True
