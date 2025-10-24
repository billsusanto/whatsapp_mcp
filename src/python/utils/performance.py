"""
Performance optimization utilities

Provides:
- Response caching
- Connection pooling
- Parallel execution helpers
- Performance monitoring
"""

import os
import json
import hashlib
import asyncio
from typing import Optional, Dict, Any, Callable, TypeVar, List
from datetime import datetime, timedelta
from functools import wraps
import redis.asyncio as aioredis
from contextlib import asynccontextmanager

# Type variables for generic functions
T = TypeVar('T')


class CacheManager:
    """
    Redis-based cache manager with TTL support

    Provides intelligent caching for:
    - AI classification results
    - Design specifications
    - Build error patterns
    """

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize cache manager

        Args:
            redis_url: Redis connection URL (defaults to env var)
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL")
        self.redis_client: Optional[aioredis.Redis] = None
        self.enabled = bool(self.redis_url)

        # TTL configuration (in seconds)
        self.ttl_classification = int(os.getenv("CACHE_TTL_CLASSIFICATION", "3600"))  # 1 hour
        self.ttl_design_spec = int(os.getenv("CACHE_TTL_DESIGN_SPEC", "7200"))  # 2 hours
        self.ttl_build_error = int(os.getenv("CACHE_TTL_BUILD_ERROR", "1800"))  # 30 minutes

    async def initialize(self):
        """Initialize Redis connection"""
        if not self.enabled:
            print("⚠️  Cache disabled: REDIS_URL not configured")
            return

        try:
            self.redis_client = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.redis_client.ping()
            print("✅ Cache initialized (Redis)")
        except Exception as e:
            print(f"⚠️  Cache initialization failed: {e}")
            self.enabled = False
            self.redis_client = None

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()

    def _generate_key(self, prefix: str, data: str) -> str:
        """
        Generate cache key with hash

        Args:
            prefix: Key prefix (e.g., "classification")
            data: Data to hash

        Returns:
            Cache key
        """
        data_hash = hashlib.md5(data.encode()).hexdigest()
        return f"{prefix}:{data_hash}"

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if not self.enabled or not self.redis_client:
            return None

        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"⚠️  Cache get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache with TTL

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        if not self.enabled or not self.redis_client:
            return

        try:
            serialized = json.dumps(value)
            if ttl:
                await self.redis_client.setex(key, ttl, serialized)
            else:
                await self.redis_client.set(key, serialized)
        except Exception as e:
            print(f"⚠️  Cache set error: {e}")

    async def delete(self, key: str):
        """Delete key from cache"""
        if not self.enabled or not self.redis_client:
            return

        try:
            await self.redis_client.delete(key)
        except Exception as e:
            print(f"⚠️  Cache delete error: {e}")

    async def get_classification(self, message: str) -> Optional[Dict]:
        """
        Get cached webapp classification result

        Args:
            message: User message

        Returns:
            Cached classification or None
        """
        key = self._generate_key("classification", message)
        return await self.get(key)

    async def set_classification(self, message: str, result: Dict):
        """
        Cache webapp classification result

        Args:
            message: User message
            result: Classification result
        """
        key = self._generate_key("classification", message)
        await self.set(key, result, ttl=self.ttl_classification)

    async def get_design_spec(self, prompt: str) -> Optional[Dict]:
        """
        Get cached design specification

        Args:
            prompt: User prompt

        Returns:
            Cached design spec or None
        """
        key = self._generate_key("design", prompt)
        return await self.get(key)

    async def set_design_spec(self, prompt: str, design_spec: Dict):
        """
        Cache design specification

        Args:
            prompt: User prompt
            design_spec: Design specification
        """
        key = self._generate_key("design", prompt)
        await self.set(key, design_spec, ttl=self.ttl_design_spec)


# Global cache instance
cache_manager = CacheManager()


def cached(ttl: int, key_prefix: str):
    """
    Decorator for caching async function results

    Args:
        ttl: Time to live in seconds
        key_prefix: Cache key prefix

    Usage:
        @cached(ttl=3600, key_prefix="user_data")
        async def get_user_data(user_id: str):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"

            # Try to get from cache
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                print(f"📦 Cache hit: {key_prefix}")
                return cached_result

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            await cache_manager.set(cache_key, result, ttl=ttl)

            return result

        return wrapper
    return decorator


class ConnectionPool:
    """
    Database connection pool configuration

    Provides optimized settings for high-concurrency scenarios
    """

    @staticmethod
    def get_pool_config() -> Dict[str, Any]:
        """
        Get database connection pool configuration

        Returns:
            SQLAlchemy pool configuration
        """
        return {
            "pool_size": int(os.getenv("DB_POOL_SIZE", "20")),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
            "pool_pre_ping": True,  # Verify connections before use
            "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),  # 1 hour
            "pool_timeout": 30,  # 30 seconds timeout
        }


class ParallelExecutor:
    """
    Helper for parallel task execution with error handling

    Executes multiple async tasks concurrently with proper exception handling
    """

    @staticmethod
    async def execute_parallel(
        tasks: List[Callable],
        max_concurrent: int = 5,
        timeout: Optional[float] = None
    ) -> List[tuple[bool, Any]]:
        """
        Execute tasks in parallel with concurrency limit

        Args:
            tasks: List of async functions to execute
            max_concurrent: Maximum concurrent tasks
            timeout: Timeout per task in seconds

        Returns:
            List of (success, result) tuples
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        results = []

        async def execute_with_semaphore(task):
            async with semaphore:
                try:
                    if timeout:
                        result = await asyncio.wait_for(task(), timeout=timeout)
                    else:
                        result = await task()
                    return True, result
                except asyncio.TimeoutError:
                    return False, "Task timeout"
                except Exception as e:
                    return False, str(e)

        # Execute all tasks
        task_results = await asyncio.gather(
            *[execute_with_semaphore(task) for task in tasks],
            return_exceptions=True
        )

        return task_results

    @staticmethod
    async def execute_with_fallback(
        primary_task: Callable,
        fallback_task: Callable,
        timeout: float = 30.0
    ) -> tuple[bool, Any, str]:
        """
        Execute primary task with fallback on failure

        Args:
            primary_task: Primary async function
            fallback_task: Fallback async function
            timeout: Timeout for primary task

        Returns:
            (success, result, source)
            source is "primary" or "fallback"
        """
        try:
            result = await asyncio.wait_for(primary_task(), timeout=timeout)
            return True, result, "primary"
        except Exception as e:
            print(f"⚠️  Primary task failed: {e}, using fallback")
            try:
                result = await fallback_task()
                return True, result, "fallback"
            except Exception as fallback_error:
                print(f"❌ Fallback also failed: {fallback_error}")
                return False, None, "none"


class PerformanceMonitor:
    """
    Performance monitoring and metrics collection

    Tracks performance metrics for optimization
    """

    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
        self._lock = asyncio.Lock()

    async def record_metric(self, name: str, value: float):
        """
        Record a performance metric

        Args:
            name: Metric name
            value: Metric value (e.g., duration in seconds)
        """
        async with self._lock:
            if name not in self.metrics:
                self.metrics[name] = []

            self.metrics[name].append(value)

            # Keep only last 1000 measurements
            if len(self.metrics[name]) > 1000:
                self.metrics[name] = self.metrics[name][-1000:]

    async def get_stats(self, name: str) -> Optional[Dict[str, float]]:
        """
        Get statistics for a metric

        Args:
            name: Metric name

        Returns:
            Statistics dict with avg, min, max, p95
        """
        async with self._lock:
            if name not in self.metrics or not self.metrics[name]:
                return None

            values = sorted(self.metrics[name])
            n = len(values)

            return {
                "count": n,
                "avg": sum(values) / n,
                "min": values[0],
                "max": values[-1],
                "p50": values[int(n * 0.5)],
                "p95": values[int(n * 0.95)],
                "p99": values[int(n * 0.99)] if n >= 100 else values[-1],
            }

    async def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """Get all performance statistics"""
        stats = {}
        for metric_name in list(self.metrics.keys()):
            metric_stats = await self.get_stats(metric_name)
            if metric_stats:
                stats[metric_name] = metric_stats
        return stats


# Global performance monitor
perf_monitor = PerformanceMonitor()


@asynccontextmanager
async def measure_time(metric_name: str):
    """
    Context manager to measure execution time

    Usage:
        async with measure_time("api_call"):
            await some_async_function()
    """
    start = datetime.utcnow()
    try:
        yield
    finally:
        duration = (datetime.utcnow() - start).total_seconds()
        await perf_monitor.record_metric(metric_name, duration)


# Optimization helpers
async def batch_process(
    items: List[T],
    process_func: Callable[[T], Any],
    batch_size: int = 10
) -> List[Any]:
    """
    Process items in batches to avoid overwhelming resources

    Args:
        items: Items to process
        process_func: Async function to process each item
        batch_size: Items per batch

    Returns:
        List of results
    """
    results = []

    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = await asyncio.gather(
            *[process_func(item) for item in batch],
            return_exceptions=True
        )
        results.extend(batch_results)

    return results


def get_performance_config() -> Dict[str, Any]:
    """
    Get performance configuration from environment

    Returns:
        Performance configuration dict
    """
    return {
        # Agent configuration
        "min_quality_score": int(os.getenv("MIN_QUALITY_SCORE", "9")),
        "max_build_retries": int(os.getenv("MAX_BUILD_RETRIES", "10")),
        "enable_agent_caching": os.getenv("ENABLE_AGENT_CACHING", "false").lower() == "true",
        "max_cached_agents": int(os.getenv("MAX_CACHED_AGENTS", "3")),

        # Database
        "db_pool_size": int(os.getenv("DB_POOL_SIZE", "20")),
        "db_max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
        "db_pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),

        # Cache
        "cache_ttl_classification": int(os.getenv("CACHE_TTL_CLASSIFICATION", "3600")),
        "cache_ttl_design_spec": int(os.getenv("CACHE_TTL_DESIGN_SPEC", "7200")),

        # Concurrency
        "max_concurrent_agents": int(os.getenv("MAX_CONCURRENT_AGENTS", "5")),
        "max_concurrent_requests": int(os.getenv("MAX_CONCURRENT_REQUESTS", "20")),
    }
