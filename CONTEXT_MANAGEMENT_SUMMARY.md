# Context Window Management System - Executive Summary

**Date:** 2025-10-27
**Status:** ✅ Research & Planning Complete
**Next Phase:** Implementation

---

## Overview

This document summarizes the research and planning for implementing **Context Window Management** in the multi-agent orchestration system. The system prevents context rot by monitoring agent token usage and performing seamless handoffs when approaching the 200K token limit.

---

## Problem Statement

**Current Issue:**
- Multi-agent system uses Claude Sonnet 4.5 with 200K token context window
- Long-running agents (especially Frontend, Backend) can approach or exceed this limit
- Context rot occurs when agents lose track of earlier decisions
- No mechanism exists to preserve work when agents hit the limit

**Business Impact:**
- Tasks fail when context window is exhausted
- Users must restart from scratch, losing all progress
- Poor user experience for complex webapp builds

---

## Proposed Solution

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         AgentLifecycleManager                          │ │
│  │  - Monitors all active agents                          │ │
│  │  - Tracks token usage per agent                        │ │
│  │  - Triggers handoffs at 90% threshold                  │ │
│  │  - Spawns new agents with continuity                   │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ monitors
                            ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Frontend v1  │  │ Backend v1   │  │ Designer v1  │
│ 145K tokens  │  │ 87K tokens   │  │ 32K tokens   │
│ ⚠️  WARNING  │  │ ✅ OK        │  │ ✅ OK        │
└──────────────┘  └──────────────┘  └──────────────┘
       │
       │ handoff triggered @ 180K tokens
       ▼
┌──────────────────────────────────────────┐
│    HandoffDocument.md                    │
│  - Original request & context            │
│  - Decisions made (with reasoning)       │
│  - Rejected alternatives                 │
│  - Work completed (files, code)          │
│  - TODO list (prioritized)               │
│  - Token usage history                   │
│  - Tool state (DB connections, etc.)     │
└──────────────────────────────────────────┘
       │
       │ loaded by
       ▼
┌──────────────┐
│ Frontend v2  │  ← Continues work seamlessly
│ 0K tokens    │
│ ✅ ACTIVE    │
└──────────────┘
```

### Core Components

1. **Token Tracking System**
   - Monitors real-time token usage via Anthropic API response objects
   - Maintains cumulative count across all operations
   - Triggers warnings at 75% (150K tokens) and critical at 90% (180K tokens)

2. **Handoff Document Schema**
   - JSON metadata + Markdown body for human/machine readability
   - Preserves: decisions, rejected alternatives, work completed, TODOs
   - Versioned schema (1.0.0) with forward compatibility

3. **Agent Lifecycle Manager**
   - Manages agent spawn/terminate lifecycle
   - Monitors token usage via background task (every 30s)
   - Triggers automatic handoffs at critical threshold
   - Maintains agent registry and state

4. **State Transfer Protocol**
   - Queries outgoing agent for comprehensive state
   - Writes structured handoff document to disk
   - Spawns new agent with handoff context injected into system prompt
   - Ensures zero knowledge loss during transition

5. **Orchestrator Integration**
   - Orchestrator uses lifecycle manager for all agent operations
   - Pauses task routing during handoffs
   - Notifies users of continuity events
   - Resumes seamlessly with new agent instance

---

## Key Features

### ✅ Automatic Handoff Triggering
- Monitors token usage in real-time after every API call
- Automatically triggers handoff when usage exceeds 90% (180K/200K tokens)
- No manual intervention required

### ✅ Comprehensive State Preservation
Handoff documents capture 17 critical categories:
1. Original user request
2. Task description & status (% complete)
3. Decisions made (with reasoning & confidence)
4. Rejected alternatives (to avoid repeating mistakes)
5. Work completed (files created, code written)
6. Current work in progress
7. Prioritized TODO list
8. Tool state (DB connections, API sessions)
9. Token usage history
10. Quality metrics & validation rules
11. Assumptions & constraints
12. Dependencies (upstream/downstream)
13. Error history & recovery attempts
14. References & documentation
15. Code quality checklist
16. Performance metrics
17. Testing notes

### ✅ Zero Knowledge Loss
- Decisions and reasoning preserved → no repeat research
- Rejected alternatives documented → no wasted retries
- Work completed tracked → no duplicate effort
- TODOs prioritized → immediate continuation

### ✅ Human-Readable Handoffs
- Markdown format for easy human review
- YAML front matter for machine parsing
- Structured sections for quick navigation
- Can be manually edited if needed

### ✅ Seamless Continuity
- New agent receives full context via enhanced system prompt
- Inherits cumulative token count from previous instance
- Continues work from exact stopping point
- Users unaware of internal handoff (transparent)

---

## Token Counting Implementation

### Method 1: Real-Time from API Responses (Chosen)
```python
message = client.messages.create(...)
print(message.usage)
# Usage(input_tokens=25, output_tokens=13)

tracker.record_usage("operation_name", message.usage)
```

**Advantages:**
- 100% accurate (from Anthropic's own tracking)
- No pre-flight API calls needed
- Works with streaming and non-streaming

### Cumulative Tracking
```python
class AgentTokenTracker:
    total_input_tokens: int = 0
    total_output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.total_input_tokens + self.total_output_tokens

    @property
    def usage_percentage(self) -> float:
        return (self.total_tokens / 200_000) * 100

    def should_handoff(self) -> bool:
        return self.usage_percentage >= 90.0
```

---

## Handoff Document Structure

### File Naming
```
handoffs/{project_id}/{agent_type}/{timestamp}_v{version}_handoff.md
```

Example:
```
handoffs/proj_abc123/frontend_agent/20251027_143052_v1_handoff.md
```

### Document Format
```markdown
---
# YAML metadata (machine-readable)
schema_version: "1.0.0"
trace_id: "f3b9e2f4-91d1..."
task_id: "build_webapp_todo_app"
source_agent:
  agent_id: "frontend_001"
  version: 1
  termination_reason: "context_window_exhausted"
token_usage:
  total_tokens: 182050
  usage_percentage: 91.03
---

# AGENT HANDOFF DOCUMENT

## 1. ORIGINAL REQUEST & CONTEXT
{User's original request}

## 2. TASK DESCRIPTION & STATUS
{What was being accomplished, % complete}

## 3. DECISIONS MADE
{Key decisions with reasoning}

... (14 more sections) ...

**END OF HANDOFF DOCUMENT**
```

---

## Implementation Phases

### Phase 1: Token Tracking (Week 1) - 40 hours
**Deliverables:**
- `AgentTokenTracker` class with cumulative tracking
- Integration with `ClaudeSDK` to extract usage from API responses
- Telemetry metrics for token usage monitoring
- Unit tests (>90% coverage)

**Key Files:**
- `src/python/agents/collaborative/token_tracker.py` (NEW)
- `src/python/sdk/claude_sdk.py` (MODIFIED)

### Phase 2: Handoff Documents (Week 2) - 40 hours
**Deliverables:**
- `HandoffDocument` Pydantic models with validation
- `HandoffManager` class for creating/writing/loading handoffs
- Markdown generation with YAML front matter
- Agent query system to extract state

**Key Files:**
- `src/python/agents/collaborative/handoff_manager.py` (NEW)
- `src/python/agents/collaborative/models.py` (MODIFIED)

### Phase 3: Lifecycle Management (Week 3) - 40 hours
**Deliverables:**
- `AgentLifecycleManager` for spawn/terminate/handoff
- Agent registry and state tracking
- Background monitoring loop (30s intervals)
- Handoff triggering logic

**Key Files:**
- `src/python/agents/collaborative/agent_lifecycle_manager.py` (NEW)

### Phase 4: Orchestrator Integration (Week 4) - 40 hours
**Deliverables:**
- Orchestrator integration with lifecycle manager
- Event handling for lifecycle events
- Task routing pause/resume during handoffs
- User notifications

**Key Files:**
- `src/python/agents/collaborative/orchestrator.py` (MODIFIED)
- `src/python/agents/collaborative/base_agent.py` (MODIFIED)

### Phase 5: Testing & Hardening (Week 5) - 40 hours
**Deliverables:**
- Comprehensive unit tests (all components)
- Integration tests (handoff flows)
- End-to-end tests (full webapp builds with handoffs)
- Error handling and recovery
- Performance optimization
- Documentation

**Test Coverage Goal:** >85%

---

## Risk Assessment

### High Risk
❌ **Token Count Inaccuracy**
- **Mitigation:** Use official Anthropic API usage objects (100% accurate)
- **Fallback:** Add 10% safety margin to thresholds

### Medium Risk
⚠️ **Handoff Document Incompleteness**
- **Mitigation:** Structured JSON schema with validation
- **Fallback:** Retry with clarifying prompts, use fallback content

### Low Risk
✅ **Performance Impact of Monitoring**
- **Mitigation:** 30-second polling interval (minimal overhead)
- **Monitoring:** Track monitoring loop performance

### Low Risk
✅ **Storage Growth (Handoff Documents)**
- **Mitigation:** Compress old handoffs, delete after 30 days
- **Monitoring:** Track handoff directory size

---

## Success Metrics

### Functional Metrics
- ✅ 100% of agents successfully handoff when reaching 180K tokens
- ✅ 0 tasks fail due to context window exhaustion
- ✅ New agent instances resume within 30 seconds of handoff

### Quality Metrics
- ✅ >90% of handoff documents pass validation
- ✅ <5% of resumed agents need to re-ask questions (knowledge loss)
- ✅ Average completion time unchanged (no slowdown from handoffs)

### User Experience Metrics
- ✅ Users unaware of handoffs (seamless continuity)
- ✅ Zero data loss during handoffs
- ✅ Tasks >200K tokens complete successfully

---

## Future Enhancements

### Phase 6 (Future)
- **Multi-Instance Handoffs:** Support handoff to different agent types (e.g., Frontend → Backend)
- **Predictive Handoffs:** ML model to predict when handoff will be needed and pre-trigger
- **Handoff Compression:** Summarize old handoff sections to reduce size
- **Handoff Chaining:** Support multiple generations (v1 → v2 → v3 → ... → vN)
- **Human Review:** Optional human approval for critical handoffs
- **Distributed Handoffs:** Support handoffs across multiple orchestrator instances

---

## Documentation Deliverables

### For Developers
- ✅ `CONTEXT_WINDOW_MANAGEMENT_PLAN.md` - Detailed technical specification
- ✅ `CONTEXT_MANAGEMENT_IMPLEMENTATION.md` - Implementation guide with code examples
- ✅ `CONTEXT_MANAGEMENT_SUMMARY.md` - This executive summary
- 🔲 API documentation for lifecycle manager classes
- 🔲 Integration guide for adding new agent types

### For Users
- 🔲 User-facing documentation explaining continuity feature
- 🔲 FAQ on handoff behavior
- 🔲 Troubleshooting guide

### For Operations
- 🔲 Monitoring playbook (Logfire dashboards)
- 🔲 Runbook for handoff failures
- 🔲 Storage management guide

---

## Estimated Effort

| Phase | Duration | Effort | Dependencies |
|-------|----------|--------|--------------|
| Phase 1: Token Tracking | 1 week | 40 hours | None |
| Phase 2: Handoff Docs | 1 week | 40 hours | Phase 1 |
| Phase 3: Lifecycle Mgmt | 1 week | 40 hours | Phase 2 |
| Phase 4: Orchestrator | 1 week | 40 hours | Phase 3 |
| Phase 5: Testing | 1 week | 40 hours | Phase 4 |
| **Total** | **5 weeks** | **200 hours** | |

**Recommended Team:**
- 1 Senior Backend Engineer (Python, async)
- 1 Mid-level Engineer (testing, documentation)

**Timeline:** 5 weeks (1 phase per week)

---

## References

### Research Sources
1. **Anthropic SDK Documentation** - Token counting API
2. **Claude API Usage Tracking** - Real-time usage objects
3. **Multi-Agent Orchestration Best Practices** (Skywork.ai)
4. **Agent Handoff Protocols** (OpenAI Cookbook)
5. **Context Window Management** (Academic papers on LLM memory)

### Related Documentation
- `CONTEXT_WINDOW_MANAGEMENT_PLAN.md` - Full technical specification
- `CONTEXT_MANAGEMENT_IMPLEMENTATION.md` - Implementation details
- Current system docs: `CODEBASE_MAP.md` (this analysis)

---

## Approval & Sign-off

**Research Completed By:** Claude (AI Planning Agent)
**Date:** 2025-10-27
**Status:** ✅ Ready for Implementation

**Next Steps:**
1. Review this plan with engineering team
2. Approve technical approach and timelines
3. Begin Phase 1 implementation (Token Tracking)
4. Schedule weekly check-ins during 5-week implementation

---

## Appendix: Quick Reference

### Key Classes

| Class | Purpose | Location |
|-------|---------|----------|
| `AgentTokenTracker` | Track cumulative token usage | `token_tracker.py` |
| `HandoffDocument` | Pydantic model for handoffs | `handoff_manager.py` |
| `HandoffManager` | Create/write/load handoffs | `handoff_manager.py` |
| `AgentLifecycleManager` | Manage agent lifecycle | `agent_lifecycle_manager.py` |
| `AgentInstance` | Wrapper for agent + metadata | `agent_lifecycle_manager.py` |

### Key Thresholds

| Threshold | Token Count | Percentage | Action |
|-----------|-------------|------------|--------|
| Warning | 150,000 | 75% | Log warning, monitor closely |
| Critical | 180,000 | 90% | Trigger handoff immediately |
| Maximum | 200,000 | 100% | Hard limit (never reach) |

### Handoff Document Sections (17 Total)

1. Original Request & Context
2. Task Description & Status
3. Decisions Made
4. Rejected Alternatives
5. Work Completed
6. Current Work in Progress
7. TODO List
8. Tool State & Session Info
9. Quality Metrics
10. Dependencies
11. Assumptions & Constraints
12. Error History
13. Performance Notes
14. Testing Notes
15. References
16. Metadata (JSON)
17. Signature & Validity

---

**END OF SUMMARY**

For detailed technical specifications, see:
- `CONTEXT_WINDOW_MANAGEMENT_PLAN.md`
- `CONTEXT_MANAGEMENT_IMPLEMENTATION.md`
