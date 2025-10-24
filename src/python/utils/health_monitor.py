"""
System Health Monitoring
Tracks system-wide metrics, workflow outcomes, and overall health
"""

import time
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict
from utils.telemetry import log_event, log_metric, log_error


class SystemHealthMonitor:
    """
    Monitors system health across all workflows and agents

    Tracks:
    - Workflow success/failure rates
    - Workflow durations and performance
    - Agent usage patterns
    - Error rates and types
    - System uptime and availability
    """

    def __init__(self):
        self.system_start_time = time.time()

        # In-memory metrics (for quick access, also logged to Logfire)
        self.workflow_stats = defaultdict(lambda: {
            'total': 0,
            'success': 0,
            'failure': 0,
            'error': 0,
            'total_duration_ms': 0
        })

        self.agent_stats = defaultdict(lambda: {
            'total_tasks': 0,
            'active_count': 0,
            'total_duration_ms': 0,
            'errors': 0
        })

        self.error_stats = defaultdict(int)  # error_type -> count
        self.hourly_requests = defaultdict(int)  # hour -> count

        # Log system startup
        log_event("system.started",
                 start_time=datetime.now().isoformat(),
                 timestamp=time.time())

    # ============================================
    # Workflow Tracking
    # ============================================

    def track_workflow_start(self, workflow_type: str, workflow_id: str, metadata: Dict = None):
        """Track when a workflow starts"""
        log_event("system.workflow_started",
                 workflow_type=workflow_type,
                 workflow_id=workflow_id,
                 start_time=time.time(),
                 metadata=metadata or {})

        self.workflow_stats[workflow_type]['total'] += 1
        log_metric("system.workflows_total", 1)
        log_metric(f"system.workflow_{workflow_type}_started", 1)

    def track_workflow_success(
        self,
        workflow_type: str,
        workflow_id: str,
        duration_ms: float,
        metadata: Dict = None
    ):
        """Track successful workflow completion"""
        log_event("system.workflow_succeeded",
                 workflow_type=workflow_type,
                 workflow_id=workflow_id,
                 duration_ms=duration_ms,
                 metadata=metadata or {})

        self.workflow_stats[workflow_type]['success'] += 1
        self.workflow_stats[workflow_type]['total_duration_ms'] += duration_ms

        log_metric("system.workflows_succeeded", 1)
        log_metric(f"system.workflow_{workflow_type}_success", 1)
        log_metric(f"system.workflow_{workflow_type}_duration_ms", duration_ms)

        # Calculate and log success rate
        stats = self.workflow_stats[workflow_type]
        success_rate = (stats['success'] / stats['total']) * 100 if stats['total'] > 0 else 0
        log_metric(f"system.workflow_{workflow_type}_success_rate", success_rate)

    def track_workflow_failure(
        self,
        workflow_type: str,
        workflow_id: str,
        duration_ms: float,
        reason: str,
        metadata: Dict = None
    ):
        """Track workflow failure (expected failure, not error)"""
        log_event("system.workflow_failed",
                 workflow_type=workflow_type,
                 workflow_id=workflow_id,
                 duration_ms=duration_ms,
                 reason=reason,
                 metadata=metadata or {})

        self.workflow_stats[workflow_type]['failure'] += 1
        self.workflow_stats[workflow_type]['total_duration_ms'] += duration_ms

        log_metric("system.workflows_failed", 1)
        log_metric(f"system.workflow_{workflow_type}_failure", 1)

        # Calculate and log failure rate
        stats = self.workflow_stats[workflow_type]
        failure_rate = (stats['failure'] / stats['total']) * 100 if stats['total'] > 0 else 0
        log_metric(f"system.workflow_{workflow_type}_failure_rate", failure_rate)

    def track_workflow_error(
        self,
        workflow_type: str,
        workflow_id: str,
        error: Exception,
        duration_ms: float,
        metadata: Dict = None
    ):
        """Track workflow error (unexpected failure)"""
        error_type = type(error).__name__

        log_error(error, "system_workflow_error",
                 workflow_type=workflow_type,
                 workflow_id=workflow_id,
                 duration_ms=duration_ms,
                 metadata=metadata or {})

        log_event("system.workflow_errored",
                 workflow_type=workflow_type,
                 workflow_id=workflow_id,
                 error_type=error_type,
                 error_message=str(error),
                 duration_ms=duration_ms,
                 metadata=metadata or {})

        self.workflow_stats[workflow_type]['error'] += 1
        self.workflow_stats[workflow_type]['total_duration_ms'] += duration_ms
        self.error_stats[error_type] += 1

        log_metric("system.workflows_errored", 1)
        log_metric(f"system.workflow_{workflow_type}_error", 1)
        log_metric(f"system.error_{error_type}", 1)

        # Calculate and log error rate
        stats = self.workflow_stats[workflow_type]
        error_rate = (stats['error'] / stats['total']) * 100 if stats['total'] > 0 else 0
        log_metric(f"system.workflow_{workflow_type}_error_rate", error_rate)

    # ============================================
    # Agent Tracking
    # ============================================

    def track_agent_task_start(self, agent_id: str, agent_type: str, task_id: str):
        """Track when an agent starts a task"""
        log_event("system.agent_task_started",
                 agent_id=agent_id,
                 agent_type=agent_type,
                 task_id=task_id)

        self.agent_stats[agent_type]['total_tasks'] += 1
        self.agent_stats[agent_type]['active_count'] += 1

        log_metric(f"system.agent_{agent_type}_tasks_total", 1)
        log_metric(f"system.agent_{agent_type}_active", self.agent_stats[agent_type]['active_count'])

    def track_agent_task_complete(
        self,
        agent_id: str,
        agent_type: str,
        task_id: str,
        duration_ms: float,
        success: bool = True
    ):
        """Track agent task completion"""
        log_event("system.agent_task_completed",
                 agent_id=agent_id,
                 agent_type=agent_type,
                 task_id=task_id,
                 duration_ms=duration_ms,
                 success=success)

        self.agent_stats[agent_type]['active_count'] -= 1
        self.agent_stats[agent_type]['total_duration_ms'] += duration_ms

        log_metric(f"system.agent_{agent_type}_active", self.agent_stats[agent_type]['active_count'])
        log_metric(f"system.agent_{agent_type}_duration_ms", duration_ms)

        if success:
            log_metric(f"system.agent_{agent_type}_success", 1)
        else:
            log_metric(f"system.agent_{agent_type}_failure", 1)

    def track_agent_error(self, agent_id: str, agent_type: str, error: Exception):
        """Track agent errors"""
        error_type = type(error).__name__

        log_error(error, "system_agent_error",
                 agent_id=agent_id,
                 agent_type=agent_type)

        self.agent_stats[agent_type]['errors'] += 1

        log_metric(f"system.agent_{agent_type}_errors", 1)
        log_metric(f"system.error_{error_type}", 1)

    # ============================================
    # System-Wide Metrics
    # ============================================

    def get_system_uptime_seconds(self) -> float:
        """Get system uptime in seconds"""
        return time.time() - self.system_start_time

    def get_system_health(self) -> Dict:
        """
        Get comprehensive system health metrics

        Returns:
            Dict with system health data including:
            - uptime
            - workflow stats
            - agent stats
            - error rates
            - performance metrics
        """
        uptime_seconds = self.get_system_uptime_seconds()

        # Calculate overall metrics
        total_workflows = sum(stats['total'] for stats in self.workflow_stats.values())
        total_success = sum(stats['success'] for stats in self.workflow_stats.values())
        total_failure = sum(stats['failure'] for stats in self.workflow_stats.values())
        total_error = sum(stats['error'] for stats in self.workflow_stats.values())

        overall_success_rate = (total_success / total_workflows * 100) if total_workflows > 0 else 0
        overall_error_rate = (total_error / total_workflows * 100) if total_workflows > 0 else 0

        # Calculate average workflow duration
        total_duration_ms = sum(stats['total_duration_ms'] for stats in self.workflow_stats.values())
        avg_workflow_duration_ms = total_duration_ms / total_workflows if total_workflows > 0 else 0

        # Calculate agent utilization
        total_agent_tasks = sum(stats['total_tasks'] for stats in self.agent_stats.values())
        total_agent_errors = sum(stats['errors'] for stats in self.agent_stats.values())
        agent_error_rate = (total_agent_errors / total_agent_tasks * 100) if total_agent_tasks > 0 else 0

        health_data = {
            "status": "healthy" if overall_error_rate < 10 else "degraded" if overall_error_rate < 25 else "unhealthy",
            "uptime_seconds": uptime_seconds,
            "uptime_human": self._format_duration(uptime_seconds),
            "timestamp": datetime.now().isoformat(),

            "workflows": {
                "total": total_workflows,
                "success": total_success,
                "failure": total_failure,
                "error": total_error,
                "success_rate": round(overall_success_rate, 2),
                "error_rate": round(overall_error_rate, 2),
                "avg_duration_ms": round(avg_workflow_duration_ms, 2),
                "by_type": {
                    wf_type: {
                        "total": stats['total'],
                        "success": stats['success'],
                        "failure": stats['failure'],
                        "error": stats['error'],
                        "success_rate": round((stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0, 2),
                        "avg_duration_ms": round(stats['total_duration_ms'] / stats['total'] if stats['total'] > 0 else 0, 2)
                    }
                    for wf_type, stats in self.workflow_stats.items()
                }
            },

            "agents": {
                "total_tasks": total_agent_tasks,
                "total_errors": total_agent_errors,
                "error_rate": round(agent_error_rate, 2),
                "by_type": {
                    agent_type: {
                        "total_tasks": stats['total_tasks'],
                        "active_count": stats['active_count'],
                        "errors": stats['errors'],
                        "avg_duration_ms": round(stats['total_duration_ms'] / stats['total_tasks'] if stats['total_tasks'] > 0 else 0, 2)
                    }
                    for agent_type, stats in self.agent_stats.items()
                }
            },

            "errors": {
                "total": sum(self.error_stats.values()),
                "by_type": dict(self.error_stats)
            }
        }

        # Log system health snapshot
        log_event("system.health_check",
                 status=health_data["status"],
                 uptime_seconds=uptime_seconds,
                 total_workflows=total_workflows,
                 success_rate=overall_success_rate,
                 error_rate=overall_error_rate,
                 total_agent_tasks=total_agent_tasks)

        log_metric("system.uptime_seconds", uptime_seconds)
        log_metric("system.overall_success_rate", overall_success_rate)
        log_metric("system.overall_error_rate", overall_error_rate)
        log_metric("system.avg_workflow_duration_ms", avg_workflow_duration_ms)

        return health_data

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds / 60)}m {int(seconds % 60)}s"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"
        else:
            days = int(seconds / 86400)
            hours = int((seconds % 86400) / 3600)
            return f"{days}d {hours}h"

    def log_periodic_health_check(self):
        """
        Log periodic health check (call this periodically, e.g., every 5 minutes)
        """
        health_data = self.get_system_health()

        log_event("system.periodic_health_check",
                 status=health_data["status"],
                 uptime_seconds=health_data["uptime_seconds"],
                 total_workflows=health_data["workflows"]["total"],
                 success_rate=health_data["workflows"]["success_rate"],
                 error_rate=health_data["workflows"]["error_rate"])

        return health_data


# Global system health monitor instance
system_health_monitor = SystemHealthMonitor()
