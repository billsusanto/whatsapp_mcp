# Manager Refactoring Plan

## Executive Summary

We currently have **two separate manager classes** (`AgentManager` and `GitHubAgentManager`) with ~70% duplicated code. This document proposes a refactoring to create a **unified, platform-agnostic manager** that eliminates duplication and makes the codebase more maintainable.

## Current Architecture Problems

### 1. Code Duplication

**AgentManager** (manager.py - 538 lines) and **GitHubAgentManager** (github_manager.py - 376 lines) duplicate:

- ✅ AI-powered request classification (`_is_webapp_request()`) - **~80 lines duplicated**
- ✅ Message type classification (`_classify_message()`) - **~70 lines duplicated**
- ✅ Agent creation and lifecycle management
- ✅ Orchestrator creation and configuration
- ✅ Session management logic (3 different implementations!)

### 2. Multiple Session Manager Implementations

We have **3 different session managers** doing the same thing:

1. **SessionManager** (session.py) - In-memory, used for testing
2. **RedisSessionManager** (session_redis.py) - Redis-backed, used by WhatsApp
3. **InMemorySessionManager** (github_manager.py) - Duplicate of SessionManager

### 3. Platform-Specific Coupling

Current managers are tightly coupled to their platforms:

```python
# AgentManager (WhatsApp-specific)
self.whatsapp_client = WhatsAppClient()
self.whatsapp_client.send_message(phone_number, message)

# GitHubAgentManager (GitHub-specific)
self.github_client = get_github_client()
self.github_client.post_comment(repo, issue_number, message)
```

## Proposed Unified Architecture

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    UnifiedAgentManager                       │
│  (Platform-agnostic routing and agent lifecycle management) │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ uses
                           ▼
            ┌──────────────────────────────┐
            │   Platform Adapter Pattern   │
            └──────────────────────────────┘
                    │              │
        ┌───────────┴──────────┐   │
        ▼                      ▼   ▼
┌───────────────┐      ┌──────────────────┐
│ WhatsAppAdapter│      │  GitHubAdapter   │
│ - send_message│      │ - post_comment   │
│ - Redis session│      │ - add_reaction   │
└───────────────┘      │ - InMem session  │
                        └──────────────────┘
```

### Core Components

#### 1. UnifiedAgentManager (New)

**Location:** `src/python/agents/unified_manager.py`

**Responsibilities:**
- Platform-agnostic request routing (AI classification)
- Agent and Orchestrator lifecycle management
- Message processing coordination
- Session management (via injected session manager)

**Interface:**
```python
class UnifiedAgentManager:
    def __init__(
        self,
        platform: str,  # "whatsapp" or "github"
        session_manager: BaseSessionManager,
        notification_adapter: NotificationAdapter,
        mcp_config: Dict[str, Any]
    ):
        """
        Initialize unified manager with platform-specific dependencies.

        Args:
            platform: Platform identifier
            session_manager: Session storage (Redis or InMemory)
            notification_adapter: Platform notification interface
            mcp_config: MCP server configuration
        """

    async def process_message(
        self,
        user_id: str,  # phone_number or repo#issue
        message: str,
        context: Optional[Dict] = None  # Platform-specific context
    ) -> str:
        """
        Process a user message - routes to Agent or Orchestrator.

        Returns:
            Response message
        """
```

#### 2. NotificationAdapter (Abstract Interface)

**Location:** `src/python/agents/adapters/notification.py`

```python
from abc import ABC, abstractmethod

class NotificationAdapter(ABC):
    """Abstract interface for platform notifications"""

    @abstractmethod
    async def send_message(self, recipient: str, message: str):
        """Send a message to a user"""
        pass

    @abstractmethod
    async def send_reaction(self, message_id: str, reaction: str):
        """React to a message (optional)"""
        pass
```

#### 3. Platform Adapters

**WhatsAppAdapter** (`src/python/agents/adapters/whatsapp_adapter.py`):
```python
class WhatsAppAdapter(NotificationAdapter):
    def __init__(self, client: WhatsAppClient):
        self.client = client

    async def send_message(self, phone_number: str, message: str):
        self.client.send_message(phone_number, message)

    async def send_reaction(self, message_id: str, reaction: str):
        # WhatsApp reactions (if supported)
        pass
```

**GitHubAdapter** (`src/python/agents/adapters/github_adapter.py`):
```python
class GitHubAdapter(NotificationAdapter):
    def __init__(self, client: GitHubClient, context: Dict):
        self.client = client
        self.context = context

    async def send_message(self, _: str, message: str):
        # GitHub uses comment posting
        repo = self.context["repository"]["full_name"]
        number = self._get_issue_number()
        self.client.post_comment(repo, number, message)

    async def send_reaction(self, comment_id: str, reaction: str):
        repo = self.context["repository"]["full_name"]
        self.client.react_to_comment(repo, int(comment_id), reaction)
```

#### 4. Session Manager Interface

**BaseSessionManager** (`src/python/agents/session/base.py`):
```python
from abc import ABC, abstractmethod

class BaseSessionManager(ABC):
    """Abstract base for session management"""

    @abstractmethod
    def add_message(self, session_id: str, role: str, content: str):
        pass

    @abstractmethod
    def get_conversation_history(self, session_id: str) -> List[Dict]:
        pass

    @abstractmethod
    def clear_session(self, session_id: str):
        pass
```

**Implementations:**
- `InMemorySessionManager` (session.py) - for GitHub
- `RedisSessionManager` (session_redis.py) - for WhatsApp

## Refactoring Plan

### Phase 1: Create Core Abstractions ✅

**Files to create:**
1. `src/python/agents/adapters/__init__.py`
2. `src/python/agents/adapters/notification.py` (NotificationAdapter)
3. `src/python/agents/adapters/whatsapp_adapter.py`
4. `src/python/agents/adapters/github_adapter.py`
5. `src/python/agents/session/base.py` (BaseSessionManager)

**Updates:**
- Make `SessionManager` and `RedisSessionManager` inherit from `BaseSessionManager`

### Phase 2: Create UnifiedAgentManager ✅

**Files to create:**
1. `src/python/agents/unified_manager.py`

**What to migrate:**

From **both managers**, extract shared logic:

| Functionality | Current Location | New Location |
|---------------|------------------|--------------|
| AI request classification | manager.py:295, github_manager.py:217 | unified_manager.py:_is_webapp_request() |
| Message classification | manager.py:386 | unified_manager.py:_classify_message() |
| Agent creation | manager.py:157, github_manager.py:220 | unified_manager.py:_get_or_create_agent() |
| Orchestrator creation | manager.py:262, github_manager.py:254 | unified_manager.py:_create_orchestrator() |
| Message routing | manager.py:178, github_manager.py:110 | unified_manager.py:process_message() |

**Extracted methods:**

```python
class UnifiedAgentManager:
    # Shared AI classification (extracted from both managers)
    async def _is_webapp_request(self, message: str) -> bool:
        """AI-powered webapp request detection"""

    async def _classify_message(
        self,
        message: str,
        active_task: str,
        current_phase: str
    ) -> str:
        """Classify message as refinement/status/cancellation/new/conversation"""

    # Agent lifecycle (extracted from both managers)
    async def _get_or_create_agent(self, user_id: str) -> Agent:
        """Get or create conversational agent"""

    async def _create_orchestrator(self, user_id: str) -> CollaborativeOrchestrator:
        """Create multi-agent orchestrator"""

    # Routing (extracted from both managers)
    async def process_message(
        self,
        user_id: str,
        message: str,
        context: Optional[Dict] = None
    ) -> str:
        """Route message to Agent or Orchestrator"""
```

### Phase 3: Update Entry Points ✅

**WhatsApp Integration** (main.py):

```python
# OLD
from agents.manager import AgentManager
agent_manager = AgentManager(
    whatsapp_mcp_tools=[whatsapp_send_tool],
    enable_github=True,
    enable_netlify=True
)

# NEW
from agents.unified_manager import UnifiedAgentManager
from agents.adapters.whatsapp_adapter import WhatsAppAdapter
from agents.session_redis import RedisSessionManager

whatsapp_adapter = WhatsAppAdapter(whatsapp_client)
session_manager = RedisSessionManager(ttl_minutes=60, max_history=10)

agent_manager = UnifiedAgentManager(
    platform="whatsapp",
    session_manager=session_manager,
    notification_adapter=whatsapp_adapter,
    mcp_config={
        "whatsapp": [whatsapp_send_tool],
        "github": github_mcp_config,
        "netlify": netlify_mcp_config
    }
)
```

**GitHub Integration** (webhook_handler.py):

```python
# OLD
from agents.github_manager import GitHubAgentManager
manager = GitHubAgentManager(session_key, context)
await manager.process_command(command)

# NEW
from agents.unified_manager import UnifiedAgentManager
from agents.adapters.github_adapter import GitHubAdapter
from agents.session import InMemorySessionManager

# Create adapter for this request
github_adapter = GitHubAdapter(get_github_client(), context)
session_manager = get_or_create_github_session_manager()  # Singleton

manager = UnifiedAgentManager(
    platform="github",
    session_manager=session_manager,
    notification_adapter=github_adapter,
    mcp_config=get_github_mcp_config(context)
)

await manager.process_message(session_key, command, context)
```

### Phase 4: Remove Old Managers ✅

**Files to delete:**
1. `src/python/agents/manager.py` (AgentManager)
2. `src/python/agents/github_manager.py` (GitHubAgentManager - except InMemorySessionManager)

**Files to keep and refactor:**
- Move `InMemorySessionManager` from github_manager.py to session.py

### Phase 5: Testing & Validation ✅

**Test Cases:**

1. **WhatsApp Flow:**
   - Greeting → Routes to Agent
   - "Build a webapp" → Routes to Orchestrator
   - Multi-turn conversation → Maintains session history

2. **GitHub Flow:**
   - "@Supernova-Droid hello" → Routes to Agent
   - "@Supernova-Droid build X" → Routes to Orchestrator
   - Adds 👀 reaction
   - Silent mode (no intermediate updates)

3. **Session Management:**
   - WhatsApp uses Redis
   - GitHub uses InMemory
   - Both maintain conversation history

4. **Error Handling:**
   - Both platforms handle errors gracefully
   - Error messages formatted correctly for each platform

## Benefits

### 1. Code Reduction
- **Before:** 914 lines (538 + 376)
- **After:** ~600 lines (unified_manager + adapters)
- **Savings:** ~35% reduction

### 2. Maintainability
- ✅ Single source of truth for routing logic
- ✅ Add new platforms by creating an adapter
- ✅ Fix bugs in one place, benefits all platforms

### 3. Extensibility

Adding a new platform (e.g., Slack, Discord):

```python
# Just create an adapter!
class SlackAdapter(NotificationAdapter):
    async def send_message(self, channel: str, message: str):
        self.slack_client.post_message(channel, message)
```

Then use it:
```python
slack_manager = UnifiedAgentManager(
    platform="slack",
    session_manager=RedisSessionManager(),
    notification_adapter=SlackAdapter(slack_client),
    mcp_config=slack_mcp_config
)
```

### 4. Testability

```python
# Mock notification adapter for testing
class MockNotificationAdapter(NotificationAdapter):
    def __init__(self):
        self.messages = []

    async def send_message(self, recipient: str, message: str):
        self.messages.append((recipient, message))

# Use in tests
mock_adapter = MockNotificationAdapter()
manager = UnifiedAgentManager(
    platform="test",
    session_manager=InMemorySessionManager(),
    notification_adapter=mock_adapter,
    mcp_config={}
)

await manager.process_message("user123", "hello")
assert len(mock_adapter.messages) == 1
```

## Migration Strategy

### Option 1: Big Bang (Risky)
Replace both managers at once. Fast but risky.

### Option 2: Incremental (Recommended)

**Week 1:** Create abstractions
- Create adapter interfaces
- Create UnifiedAgentManager skeleton
- Write unit tests

**Week 2:** Migrate WhatsApp
- Switch WhatsApp to UnifiedAgentManager
- Keep GitHubAgentManager as-is
- Monitor production

**Week 3:** Migrate GitHub
- Switch GitHub to UnifiedAgentManager
- Delete old managers
- Full integration testing

**Week 4:** Cleanup
- Remove deprecated code
- Update documentation
- Performance optimization

## Implementation Checklist

### Phase 1: Abstractions
- [ ] Create `agents/adapters/__init__.py`
- [ ] Create `NotificationAdapter` interface
- [ ] Create `WhatsAppAdapter`
- [ ] Create `GitHubAdapter`
- [ ] Create `BaseSessionManager` interface
- [ ] Update existing session managers to inherit from base

### Phase 2: UnifiedAgentManager
- [ ] Create `unified_manager.py`
- [ ] Extract `_is_webapp_request()` from both managers
- [ ] Extract `_classify_message()` from manager.py
- [ ] Extract agent creation logic
- [ ] Extract orchestrator creation logic
- [ ] Implement platform-agnostic `process_message()`
- [ ] Write unit tests

### Phase 3: WhatsApp Migration
- [ ] Update `main.py` to use UnifiedAgentManager
- [ ] Test greeting flow
- [ ] Test webapp build flow
- [ ] Test multi-turn conversations
- [ ] Deploy to staging
- [ ] Monitor for 24h

### Phase 4: GitHub Migration
- [ ] Update `webhook_handler.py` to use UnifiedAgentManager
- [ ] Test @droid mentions
- [ ] Test 👀 reactions
- [ ] Test silent mode
- [ ] Deploy to staging
- [ ] Monitor for 24h

### Phase 5: Cleanup
- [ ] Delete `agents/manager.py`
- [ ] Delete `agents/github_manager.py`
- [ ] Move `InMemorySessionManager` to `session.py`
- [ ] Update all imports
- [ ] Update documentation
- [ ] Deploy to production

## Risk Mitigation

### Risks

1. **Breaking existing functionality** - Solution: Comprehensive testing
2. **Performance regression** - Solution: Benchmark before/after
3. **Session data loss** - Solution: Gradual migration, backup Redis

### Rollback Plan

If issues arise:
1. Revert to previous commit
2. Both old managers still exist until Phase 5
3. Database schemas unchanged
4. No data migration required

## Success Metrics

- ✅ All existing tests pass
- ✅ No increase in response time
- ✅ 35% code reduction achieved
- ✅ Zero production incidents during migration
- ✅ Both platforms work identically

## Future Enhancements

After refactoring:
1. **Slack integration** - Just add SlackAdapter
2. **Discord integration** - Just add DiscordAdapter
3. **Email integration** - Just add EmailAdapter
4. **Shared session across platforms** - User can switch between WhatsApp/GitHub mid-conversation

## Conclusion

This refactoring will:
- ✅ Eliminate 300+ lines of duplicated code
- ✅ Make adding new platforms trivial (just create an adapter)
- ✅ Improve maintainability and testability
- ✅ Set foundation for multi-platform AI agents

**Recommendation:** Proceed with incremental migration (Option 2) starting with abstractions and WhatsApp.
