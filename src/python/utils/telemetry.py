"""
Logfire Telemetry Configuration
Provides observability for the WhatsApp Multi-Agent System
"""

import os
from typing import Optional, Dict, Any
from functools import wraps

# Try to import logfire, but make it optional
try:
    import logfire
    from logfire import LogfireSpan
    LOGFIRE_AVAILABLE = True
except ImportError:
    LOGFIRE_AVAILABLE = False
    logfire = None
    LogfireSpan = None

# Initialize Logfire (safe to call multiple times)
_initialized = False


def initialize_logfire():
    """
    Initialize Logfire telemetry

    Set LOGFIRE_TOKEN environment variable to enable
    """
    global _initialized

    if _initialized:
        return

    # Check if logfire package is available
    if not LOGFIRE_AVAILABLE:
        print("⚠️  Logfire package not installed (pip install logfire)")
        print("   Continuing without telemetry...")
        return

    # Check if Logfire is enabled
    logfire_token = os.getenv("LOGFIRE_TOKEN")
    enable_logfire = os.getenv("ENABLE_LOGFIRE", "false").lower() == "true"

    if not enable_logfire or not logfire_token:
        print("⚠️  Logfire telemetry disabled (set LOGFIRE_TOKEN and ENABLE_LOGFIRE=true to enable)")
        return

    try:
        # Configure Logfire
        logfire.configure(
            token=logfire_token,
            service_name="whatsapp-mcp",
            service_version="2.0.0",
            environment=os.getenv("ENV", "production"),
            # Send console logs to Logfire
            send_to_logfire="if-token-present",
        )

        print("✅ Logfire telemetry initialized")
        _initialized = True

    except Exception as e:
        print(f"❌ Failed to initialize Logfire: {e}")
        print("   Continuing without telemetry...")


def instrument_fastapi(app):
    """
    Instrument FastAPI application with Logfire

    Args:
        app: FastAPI application instance
    """
    if not LOGFIRE_AVAILABLE or not _initialized:
        return

    try:
        logfire.instrument_fastapi(app)
        print("✅ FastAPI instrumented with Logfire")
    except Exception as e:
        print(f"⚠️  Failed to instrument FastAPI: {e}")


def instrument_anthropic():
    """
    Instrument Anthropic Claude SDK with Logfire
    Tracks LLM calls, tokens, and costs
    """
    if not LOGFIRE_AVAILABLE or not _initialized:
        return

    try:
        logfire.instrument_anthropic()
        print("✅ Anthropic SDK instrumented with Logfire")
    except Exception as e:
        print(f"⚠️  Failed to instrument Anthropic: {e}")


def instrument_httpx():
    """
    Instrument HTTPX for tracking external HTTP calls
    (WhatsApp API, GitHub API, Netlify API)
    """
    if not LOGFIRE_AVAILABLE or not _initialized:
        return

    try:
        logfire.instrument_httpx()
        print("✅ HTTPX instrumented with Logfire")
    except Exception as e:
        print(f"⚠️  Failed to instrument HTTPX: {e}")


def instrument_aiohttp():
    """
    Instrument aiohttp for A2A protocol tracking
    """
    if not LOGFIRE_AVAILABLE or not _initialized:
        return

    try:
        logfire.instrument_aiohttp_client()
        print("✅ aiohttp instrumented with Logfire")
    except Exception as e:
        print(f"⚠️  Failed to instrument aiohttp: {e}")


# ==========================================
# Decorators for Custom Instrumentation
# ==========================================

def trace_agent_task(agent_name: str):
    """
    Decorator to trace agent task execution

    Usage:
        @trace_agent_task("Designer")
        async def execute_task(self, task):
            ...
    """
    def decorator(func):
        if not LOGFIRE_AVAILABLE or not _initialized:
            return func

        @wraps(func)
        async def wrapper(*args, **kwargs):
            with logfire.span(
                f"{agent_name} Task",
                agent=agent_name,
                task_description=kwargs.get('task', {}).get('description', 'N/A') if 'task' in kwargs else 'N/A'
            ) as span:
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("task.status", "success")
                    return result
                except Exception as e:
                    span.set_attribute("task.status", "failed")
                    span.set_attribute("task.error", str(e))
                    span.record_exception(e)
                    raise
        return wrapper
    return decorator


def trace_workflow(workflow_type: str):
    """
    Decorator to trace multi-agent workflows

    Usage:
        @trace_workflow("full_build")
        async def _workflow_full_build(self, user_prompt, plan):
            ...
    """
    def decorator(func):
        if not LOGFIRE_AVAILABLE or not _initialized:
            return func

        @wraps(func)
        async def wrapper(self, user_prompt: str, plan: Dict = None, *args, **kwargs):
            with logfire.span(
                f"Workflow: {workflow_type}",
                workflow_type=workflow_type,
                user_prompt=user_prompt[:100],  # Truncate for privacy
                agents_planned=plan.get('agents_needed', []) if plan else [],
                complexity=plan.get('estimated_complexity', 'unknown') if plan else 'unknown'
            ) as span:
                try:
                    result = await func(self, user_prompt, plan, *args, **kwargs)
                    span.set_attribute("workflow.status", "success")
                    span.set_attribute("workflow.result_length", len(result))
                    return result
                except Exception as e:
                    span.set_attribute("workflow.status", "failed")
                    span.set_attribute("workflow.error", str(e))
                    span.record_exception(e)
                    raise
        return wrapper
    return decorator


def trace_a2a_communication():
    """
    Decorator to trace Agent-to-Agent communication

    Usage:
        @trace_a2a_communication()
        async def send_task(from_agent_id, to_agent_id, task):
            ...
    """
    def decorator(func):
        if not LOGFIRE_AVAILABLE or not _initialized:
            return func

        @wraps(func)
        async def wrapper(from_agent_id: str, to_agent_id: str, *args, **kwargs):
            with logfire.span(
                "A2A Communication",
                from_agent=from_agent_id,
                to_agent=to_agent_id,
                message_type=kwargs.get('message_type', 'task') if kwargs else 'task'
            ) as span:
                try:
                    result = await func(from_agent_id, to_agent_id, *args, **kwargs)
                    span.set_attribute("a2a.status", "success")
                    return result
                except Exception as e:
                    span.set_attribute("a2a.status", "failed")
                    span.set_attribute("a2a.error", str(e))
                    span.record_exception(e)
                    raise
        return wrapper
    return decorator


# ==========================================
# Context Managers for Manual Instrumentation
# ==========================================

class trace_operation:
    """
    Context manager for tracing custom operations

    Usage:
        with trace_operation("Deploy to Netlify", deployment_url=url):
            result = deploy()
    """
    def __init__(self, operation_name: str, **attributes):
        self.operation_name = operation_name
        self.attributes = attributes
        self.span: Optional[LogfireSpan] = None

    def __enter__(self):
        if LOGFIRE_AVAILABLE and _initialized:
            self.span = logfire.span(self.operation_name, **self.attributes)
            return self.span.__enter__()
        return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            if exc_type:
                self.span.set_attribute("error", str(exc_val))
                self.span.record_exception(exc_val)
            self.span.__exit__(exc_type, exc_val, exc_tb)


# ==========================================
# Helper Functions
# ==========================================

def log_metric(metric_name: str, value: float, **attributes):
    """
    Log a custom metric

    Usage:
        log_metric("agent.response_time", 1.234, agent="designer")
    """
    if not LOGFIRE_AVAILABLE or not _initialized:
        return

    try:
        logfire.info(
            f"metric: {metric_name}",
            metric_name=metric_name,
            metric_value=value,
            **attributes
        )
    except Exception:
        pass  # Don't break on telemetry errors


def log_event(event_name: str, **attributes):
    """
    Log a custom event

    Usage:
        log_event("user.message_received", phone_number=phone, message_type="text")
    """
    if not LOGFIRE_AVAILABLE or not _initialized:
        return

    try:
        logfire.info(
            event_name,
            event_type=event_name,
            **attributes
        )
    except Exception:
        pass  # Don't break on telemetry errors


def log_user_action(action: str, phone_number: str, **attributes):
    """
    Log user action (sanitized phone number for privacy)

    Usage:
        log_user_action("message_sent", phone_number, message_length=123)
    """
    if not LOGFIRE_AVAILABLE or not _initialized:
        return

    # Hash phone number for privacy
    import hashlib
    user_hash = hashlib.sha256(phone_number.encode()).hexdigest()[:16]

    try:
        logfire.info(
            f"user_action: {action}",
            action=action,
            user_hash=user_hash,  # Privacy-friendly
            **attributes
        )
    except Exception:
        pass


def set_user_context(phone_number: str):
    """
    Set user context for all subsequent traces

    Usage:
        set_user_context("+1234567890")
    """
    if not LOGFIRE_AVAILABLE or not _initialized:
        return

    import hashlib
    user_hash = hashlib.sha256(phone_number.encode()).hexdigest()[:16]

    try:
        logfire.set_user(user_hash)
    except Exception:
        pass


# ==========================================
# Session Tracking
# ==========================================

def track_session_event(event_type: str, phone_number: str, **data):
    """
    Track session events (creation, expiration, cleanup)

    Usage:
        track_session_event("session_created", phone_number)
        track_session_event("session_expired", phone_number, ttl_minutes=60)
    """
    if not LOGFIRE_AVAILABLE or not _initialized:
        return

    import hashlib
    user_hash = hashlib.sha256(phone_number.encode()).hexdigest()[:16]

    try:
        logfire.info(
            f"session: {event_type}",
            event_type=event_type,
            user_hash=user_hash,
            **data
        )
    except Exception:
        pass


# ==========================================
# Error Tracking
# ==========================================

def log_error(error: Exception, context: str = "", **attributes):
    """
    Log an error with context

    Usage:
        try:
            ...
        except Exception as e:
            log_error(e, "webhook_processing", phone_number=phone)
    """
    if not LOGFIRE_AVAILABLE or not _initialized:
        return

    try:
        logfire.error(
            f"Error in {context}" if context else "Error",
            error=str(error),
            error_type=type(error).__name__,
            context=context,
            **attributes
        )
    except Exception:
        pass  # Don't break on telemetry errors


# ==========================================
# Performance Tracking
# ==========================================

class measure_performance:
    """
    Context manager to measure operation performance

    Usage:
        with measure_performance("claude_api_call") as perf:
            response = await claude.send_message(prompt)
            perf.set_metadata(tokens=response.usage.total_tokens)
    """
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.metadata = {}

    def __enter__(self):
        import time
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        duration = time.time() - self.start_time

        log_metric(
            f"{self.operation_name}.duration",
            duration,
            operation=self.operation_name,
            **self.metadata
        )

    def set_metadata(self, **kwargs):
        """Add metadata to the performance measurement"""
        self.metadata.update(kwargs)


# ==========================================
# AGENT-SPECIFIC INSTRUMENTATION
# ==========================================

class trace_user_request:
    """
    Context manager for top-level user request tracing

    Usage:
        with trace_user_request(user_id, platform, request_type, user_prompt):
            # All workflow operations
            ...
    """
    def __init__(
        self,
        user_id: str,
        platform: str,
        request_type: str,
        user_prompt: str
    ):
        import hashlib
        self.user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:16]
        self.platform = platform
        self.request_type = request_type
        self.request_preview = user_prompt[:100] if user_prompt else ""
        self.request_length = len(user_prompt) if user_prompt else 0
        self.span = None

    def __enter__(self):
        if LOGFIRE_AVAILABLE and _initialized:
            self.span = logfire.span(
                'user_request',
                user_id=self.user_hash,
                platform=self.platform,
                request_type=self.request_type,
                request_length=self.request_length,
                request_preview=self.request_preview
            )
            return self.span.__enter__()
        return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            if exc_type:
                self.span.set_attribute("request_status", "failed")
                self.span.set_attribute("error_type", exc_type.__name__)
            else:
                self.span.set_attribute("request_status", "success")
            self.span.__exit__(exc_type, exc_val, exc_tb)


class trace_agent_lifecycle:
    """
    Context manager for agent lifecycle tracking

    Usage:
        with trace_agent_lifecycle(agent_id, agent_type, agent_version, user_id, project_id):
            # All agent operations from spawn to cleanup
            ...
    """
    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        agent_version: int,
        user_id: str,
        project_id: str,
        lifecycle_state: str = "ACTIVE"
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.agent_version = agent_version
        self.user_id = user_id
        self.project_id = project_id
        self.lifecycle_state = lifecycle_state
        self.span = None

    def __enter__(self):
        if LOGFIRE_AVAILABLE and _initialized:
            self.span = logfire.span(
                f'agent_lifecycle:{self.agent_type}',
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                agent_version=self.agent_version,
                lifecycle_state=self.lifecycle_state,
                user_id=self.user_id,
                project_id=self.project_id
            )
            return self.span.__enter__()
        return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            if exc_type:
                self.span.set_attribute("lifecycle_status", "failed")
            else:
                self.span.set_attribute("lifecycle_status", "completed")
            self.span.__exit__(exc_type, exc_val, exc_tb)


class trace_agent_spawn:
    """
    Context manager for agent spawn tracking

    Usage:
        with trace_agent_spawn(agent_id, agent_type, version, handoff_id):
            # Spawn agent
            ...
    """
    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        version: int,
        handoff_id: Optional[str] = None,
        predecessor_agent_id: Optional[str] = None
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.version = version
        self.continuation_mode = "handoff" if handoff_id else "fresh"
        self.handoff_id = handoff_id
        self.predecessor_agent_id = predecessor_agent_id
        self.span = None

    def __enter__(self):
        if LOGFIRE_AVAILABLE and _initialized:
            attributes = {
                'agent_id': self.agent_id,
                'agent_type': self.agent_type,
                'version': self.version,
                'continuation_mode': self.continuation_mode
            }
            if self.handoff_id:
                attributes['handoff_id'] = self.handoff_id
            if self.predecessor_agent_id:
                attributes['predecessor_agent_id'] = self.predecessor_agent_id

            self.span = logfire.span('agent_spawn', **attributes)
            return self.span.__enter__()
        return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            if exc_type:
                self.span.set_attribute("spawn_status", "failed")
            else:
                self.span.set_attribute("spawn_status", "success")
            self.span.__exit__(exc_type, exc_val, exc_tb)


class trace_agent_task_execution:
    """
    Context manager for agent task execution

    Usage:
        with trace_agent_task_execution(agent_id, task_type, task_description):
            # Execute task
            ...
    """
    def __init__(
        self,
        agent_id: str,
        task_type: str,
        task_description: str,
        task_id: Optional[str] = None,
        task_source: str = "orchestrator",
        priority: str = "medium"
    ):
        self.agent_id = agent_id
        self.task_type = task_type
        self.task_description = task_description[:200]  # Truncate
        self.task_id = task_id
        self.task_source = task_source
        self.priority = priority
        self.span = None

    def __enter__(self):
        if LOGFIRE_AVAILABLE and _initialized:
            attributes = {
                'agent_id': self.agent_id,
                'task_description': self.task_description,
                'task_source': self.task_source,
                'priority': self.priority
            }
            if self.task_id:
                attributes['task_id'] = self.task_id

            self.span = logfire.span(f'agent_task:{self.task_type}', **attributes)
            return self.span.__enter__()
        return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            if exc_type:
                self.span.set_attribute("task_status", "failed")
                self.span.set_attribute("error_type", exc_type.__name__)
            else:
                self.span.set_attribute("task_status", "success")
            self.span.__exit__(exc_type, exc_val, exc_tb)


class trace_token_usage:
    """
    Context manager for token usage tracking

    Usage:
        with trace_token_usage(agent_id, operation) as span:
            # Record token usage
            span.set_attribute('tokens_used', 1500)
    """
    def __init__(
        self,
        agent_id: str,
        operation: str,
        cumulative_total: int = 0
    ):
        self.agent_id = agent_id
        self.operation = operation
        self.cumulative_total = cumulative_total
        self.span = None

    def __enter__(self):
        if LOGFIRE_AVAILABLE and _initialized:
            self.span = logfire.span(
                'token_usage_recorded',
                agent_id=self.agent_id,
                operation=self.operation,
                cumulative_total=self.cumulative_total
            )
            return self.span.__enter__()
        return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            self.span.__exit__(exc_type, exc_val, exc_tb)


class trace_agent_handoff:
    """
    Context manager for agent handoff tracking

    Usage:
        with trace_agent_handoff(source_agent_id, target_agent_id, handoff_id):
            # Create and save handoff
            ...
    """
    def __init__(
        self,
        source_agent_id: str,
        target_agent_id: str,
        handoff_id: str,
        trace_id: str,
        termination_reason: str,
        completion_percentage: int,
        tokens_used: int
    ):
        self.source_agent_id = source_agent_id
        self.target_agent_id = target_agent_id
        self.handoff_id = handoff_id
        self.trace_id = trace_id
        self.termination_reason = termination_reason
        self.completion_percentage = completion_percentage
        self.tokens_used = tokens_used
        self.span = None

    def __enter__(self):
        if LOGFIRE_AVAILABLE and _initialized:
            self.span = logfire.span(
                'agent_handoff',
                source_agent_id=self.source_agent_id,
                target_agent_id=self.target_agent_id,
                handoff_id=self.handoff_id,
                trace_id=self.trace_id,
                termination_reason=self.termination_reason,
                completion_percentage=self.completion_percentage,
                tokens_used=self.tokens_used
            )
            return self.span.__enter__()
        return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            if exc_type:
                self.span.set_attribute("handoff_status", "failed")
            else:
                self.span.set_attribute("handoff_status", "success")
            self.span.__exit__(exc_type, exc_val, exc_tb)


class trace_handoff_document:
    """
    Context manager for handoff document creation

    Usage:
        with trace_handoff_document(handoff_id) as span:
            # Create handoff document
            span.set_attribute('document_size_kb', 5.2)
    """
    def __init__(self, handoff_id: str):
        self.handoff_id = handoff_id
        self.span = None

    def __enter__(self):
        if LOGFIRE_AVAILABLE and _initialized:
            self.span = logfire.span(
                'handoff_document_created',
                handoff_id=self.handoff_id
            )
            return self.span.__enter__()
        return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            self.span.__exit__(exc_type, exc_val, exc_tb)


class trace_database_operation:
    """
    Context manager for database operations

    Usage:
        with trace_database_operation('agent_handoff', 'insert', record_id):
            # Database operation
            ...
    """
    def __init__(
        self,
        table_name: str,
        operation: str,
        record_id: Optional[Any] = None
    ):
        self.table_name = table_name
        self.operation = operation
        self.record_id = record_id
        self.span = None

    def __enter__(self):
        if LOGFIRE_AVAILABLE and _initialized:
            attributes = {
                'table_name': self.table_name,
                'operation': self.operation
            }
            if self.record_id:
                attributes['record_id'] = str(self.record_id)

            self.span = logfire.span(
                f'database_save:{self.table_name}',
                **attributes
            )
            return self.span.__enter__()
        return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            if exc_type:
                self.span.set_attribute("db_status", "failed")
            else:
                self.span.set_attribute("db_status", "success")
            self.span.__exit__(exc_type, exc_val, exc_tb)


class trace_phase_transition:
    """
    Context manager for workflow phase transitions

    Usage:
        with trace_phase_transition('design', 'implementation', 'design_approved'):
            # Transition phase
            ...
    """
    def __init__(
        self,
        from_phase: str,
        to_phase: str,
        reason: str,
        completion_percentage: int = 0
    ):
        self.from_phase = from_phase
        self.to_phase = to_phase
        self.reason = reason
        self.completion_percentage = completion_percentage
        self.span = None

    def __enter__(self):
        if LOGFIRE_AVAILABLE and _initialized:
            self.span = logfire.span(
                'phase_transition',
                from_phase=self.from_phase,
                to_phase=self.to_phase,
                reason=self.reason,
                completion_percentage=self.completion_percentage
            )
            return self.span.__enter__()
        return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            self.span.__exit__(exc_type, exc_val, exc_tb)


class trace_mcp_tool:
    """
    Context manager for MCP tool execution

    Usage:
        with trace_mcp_tool(agent_id, 'github_create_repo', 'github') as span:
            # Call MCP tool
            span.set_attribute('repo_name', 'my-app')
    """
    def __init__(
        self,
        agent_id: str,
        tool_name: str,
        server: str
    ):
        self.agent_id = agent_id
        self.tool_name = tool_name
        self.server = server
        self.span = None

    def __enter__(self):
        if LOGFIRE_AVAILABLE and _initialized:
            self.span = logfire.span(
                f'mcp_tool:{self.tool_name}',
                agent_id=self.agent_id,
                tool_name=self.tool_name,
                server=self.server
            )
            return self.span.__enter__()
        return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            if exc_type:
                self.span.set_attribute("tool_status", "failed")
            else:
                self.span.set_attribute("tool_status", "success")
            self.span.__exit__(exc_type, exc_val, exc_tb)


class trace_threshold_event:
    """
    Context manager for token threshold events

    Usage:
        with trace_threshold_event(agent_id, 'warning', token_usage, usage_percentage):
            # Send notification
            ...
    """
    def __init__(
        self,
        agent_id: str,
        threshold_type: str,  # 'warning' or 'critical'
        token_usage: int,
        usage_percentage: float,
        tokens_remaining: int
    ):
        self.agent_id = agent_id
        self.threshold_type = threshold_type
        self.token_usage = token_usage
        self.usage_percentage = usage_percentage
        self.tokens_remaining = tokens_remaining
        self.span = None

    def __enter__(self):
        if LOGFIRE_AVAILABLE and _initialized:
            self.span = logfire.span(
                f'agent_threshold:{self.threshold_type}',
                agent_id=self.agent_id,
                threshold_type=self.threshold_type,
                token_usage=self.token_usage,
                usage_percentage=round(self.usage_percentage, 2),
                tokens_remaining=self.tokens_remaining
            )
            return self.span.__enter__()
        return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            self.span.__exit__(exc_type, exc_val, exc_tb)


# ==========================================
# Initialization
# ==========================================

# Auto-initialize when module is imported
initialize_logfire()
