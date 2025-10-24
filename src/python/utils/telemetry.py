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
# Initialization
# ==========================================

# Auto-initialize when module is imported
initialize_logfire()
