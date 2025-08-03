"""
Performance Optimizer for Theme and Navigation Components

Implements performance optimizations including lazy loading, caching,
and monitoring for theme and navigation operations.

Author: Kiro AI Integration System
Requirements: 5.2, 5.3
"""

import asyncio
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from weakref import WeakSet

from .logging_system import LoggerSystem


class ResourceCache:
    """Generic resource cache with TTL and size limits"""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._access_times: Dict[str, float] = {}
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired"""
        with self._lock:
            if key not in self._cache:
                return None

            value, timestamp = self._cache[key]
            current_time = time.time()

            # Check if expired
            if current_time - timestamp > self.ttl_seconds:
                del self._cache[key]
                if key in self._access_times:
                    del self._access_times[key]
                return None

            # Update access time
            self._access_times[key] = current_time
            return value

    def set(self, key: str, value: Any) -> None:
        """Set cached value with current timestamp"""
        with self._lock:
            current_time = time.time()

            # Evict old entries if cache is full
            if len(self._cache) >= self.max_size:
                self._evict_lru()

            self._cache[key] = (value, current_time)
            self._access_times[key] = current_time

    def _evict_lru(self) -> None:
        """Evict least recently used entries"""
        if not self._access_times:
            return

        # Remove 20% of entries (LRU)
        entries_to_remove = max(1, len(self._access_times) // 5)
        sorted_entries = sorted(self._access_times.items(), key=lambda x: x[1])

        for key, _ in sorted_entries[:entries_to_remove]:
            if key in self._cache:
                del self._cache[key]
            del self._access_times[key]

    def clear(self) -> None:
        """Clear all cached entries"""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()

    def size(self) -> int:
        """Get current cache size"""
        return len(self._cache)


class LazyResourceLoader:
    """Lazy loading manager for theme resources"""

    def __init__(self, logger_system: LoggerSystem):
        self.logger = logger_system.get_logger(__name__)
        self._loaded_resources: Set[str] = set()
        self._loading_tasks: Dict[str, asyncio.Task] = {}
        self._resource_callbacks: Dict[str, List[callable]] = {}
        self._lock = threading.RLock()

    def is_loaded(self, resource_id: str) -> bool:
        """Check if resource is already loaded"""
        return resource_id in self._loaded_resources

    async def load_resource(self, resource_id: str, loader_func: callable, *args, **kwargs) -> Any:
        """Load resource lazily with deduplication"""
        with self._lock:
            # Return immediately if already loaded
            if resource_id in self._loaded_resources:
                return True

            # If already loading, wait for existing task
            if resource_id in self._loading_tasks:
                try:
                    return await self._loading_tasks[resource_id]
                except Exception as e:
                    self.logger.error(f"Failed to wait for loading task {resource_id}: {e}")
                    return False

            # Start new loading task
            task = asyncio.create_task(self._load_resource_impl(resource_id, loader_func, *args, **kwargs))
            self._loading_tasks[resource_id] = task

            try:
                result = await task
                return result
            finally:
                # Clean up task
                if resource_id in self._loading_tasks:
                    del self._loading_tasks[resource_id]

    async def _load_resource_impl(self, resource_id: str, loader_func: callable, *args, **kwargs) -> Any:
        """Internal resource loading implementation"""
        try:
            start_time = time.time()

            # Call the loader function
            if asyncio.iscoroutinefunction(loader_func):
                result = await loader_func(*args, **kwargs)
            else:
                result = await asyncio.to_thread(loader_func, *args, **kwargs)

            # Mark as loaded
            self._loaded_resources.add(resource_id)

            # Execute callbacks
            if resource_id in self._resource_callbacks:
                for callback in self._resource_callbacks[resource_id]:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(resource_id, result)
                        else:
                            callback(resource_id, result)
                    except Exception as e:
                        self.logger.error(f"Resource callback failed for {resource_id}: {e}")

                # Clean up callbacks
                del self._resource_callbacks[resource_id]

            load_time = time.time() - start_time
            self.logger.debug(f"Resource loaded: {resource_id} (took {load_time:.3f}s)")

            return result

        except Exception as e:
            self.logger.error(f"Failed to load resource {resource_id}: {e}")
            return False

    def add_load_callback(self, resource_id: str, callback: callable) -> None:
        """Add callback to be executed when resource is loaded"""
        with self._lock:
            if resource_id not in self._resource_callbacks:
                self._resource_callbacks[resource_id] = []
            self._resource_callbacks[resource_id].append(callback)

    def unload_resource(self, resource_id: str) -> None:
        """Mark resource as unloaded"""
        with self._lock:
            self._loaded_resources.discard(resource_id)
            if resource_id in self._loading_tasks:
                self._loading_tasks[resource_id].cancel()
                del self._loading_tasks[resource_id]


class PerformanceMonitor:
    """Performance monitoring for theme and navigation operations"""

    def __init__(self, logger_system: LoggerSystem):
        self.logger = logger_system.get_logger(__name__)
        self._metrics: Dict[str, List[float]] = {}
        self._counters: Dict[str, int] = {}
        self._start_times: Dict[str, float] = {}
        self._lock = threading.RLock()
        self.max_metric_history = 1000

    def start_operation(self, operation_id: str) -> None:
        """Start timing an operation"""
        with self._lock:
            self._start_times[operation_id] = time.time()

    def end_operation(self, operation_id: str, operation_type: str = "general") -> float:
        """End timing an operation and record the duration"""
        with self._lock:
            if operation_id not in self._start_times:
                self.logger.warning(f"No start time found for operation: {operation_id}")
                return 0.0

            duration = time.time() - self._start_times[operation_id]
            del self._start_times[operation_id]

            # Record metric
            if operation_type not in self._metrics:
                self._metrics[operation_type] = []

            self._metrics[operation_type].append(duration)

            # Limit history size
            if len(self._metrics[operation_type]) > self.max_metric_history:
                self._metrics[operation_type] = self._metrics[operation_type][-self.max_metric_history:]

            # Update counter
            self._counters[operation_type] = self._counters.get(operation_type, 0) + 1

            return duration

    def record_metric(self, metric_name: str, value: float) -> None:
        """Record a custom metric value"""
        with self._lock:
            if metric_name not in self._metrics:
                self._metrics[metric_name] = []

            self._metrics[metric_name].append(value)

            # Limit history size
            if len(self._metrics[metric_name]) > self.max_metric_history:
                self._metrics[metric_name] = self._metrics[metric_name][-self.max_metric_history:]

    def increment_counter(self, counter_name: str, amount: int = 1) -> None:
        """Increment a counter"""
        with self._lock:
            self._counters[counter_name] = self._counters.get(counter_name, 0) + amount

    def get_metrics_summary(self, metric_name: str) -> Dict[str, float]:
        """Get summary statistics for a metric"""
        with self._lock:
            if metric_name not in self._metrics or not self._metrics[metric_name]:
                return {}

            values = self._metrics[metric_name]
            return {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "recent_avg": sum(values[-10:]) / min(len(values), 10)
            }

    def get_all_metrics(self) -> Dict[str, Dict[str, float]]:
        """Get summary for all metrics"""
        with self._lock:
            result = {}
            for metric_name in self._metrics:
                result[metric_name] = self.get_metrics_summary(metric_name)
            return result

    def get_counters(self) -> Dict[str, int]:
        """Get all counter values"""
        with self._lock:
            return self._counters.copy()

    def reset_metrics(self) -> None:
        """Reset all metrics and counters"""
        with self._lock:
            self._metrics.clear()
            self._counters.clear()
            self._start_times.clear()


class PerformanceOptimizer:
    """Main performance optimizer coordinating all optimization strategies"""

    def __init__(self, logger_system: LoggerSystem):
        self.logger = logger_system.get_logger(__name__)

        # Initialize optimization components
        self.theme_cache = ResourceCache(max_size=100, ttl_seconds=600)  # 10 minutes
        self.stylesheet_cache = ResourceCache(max_size=50, ttl_seconds=300)  # 5 minutes
        self.path_cache = ResourceCache(max_size=500, ttl_seconds=120)  # 2 minutes

        self.lazy_loader = LazyResourceLoader(logger_system)
        self.monitor = PerformanceMonitor(logger_system)

        # Optimization settings
        self.enable_lazy_loading = True
        self.enable_caching = True
        self.enable_monitoring = True

        # Background optimization task
        self._optimization_task: Optional[asyncio.Task] = None
        self._running = False

    def start_optimization(self) -> None:
        """Start background optimization processes"""
        if self._running:
            return

        self._running = True
        self._optimization_task = asyncio.create_task(self._optimization_loop())
        self.logger.info("Performance optimization started")

    def stop_optimization(self) -> None:
        """Stop background optimization processes"""
        self._running = False
        if self._optimization_task:
            self._optimization_task.cancel()
            self._optimization_task = None
        self.logger.info("Performance optimization stopped")

    async def _optimization_loop(self) -> None:
        """Background optimization loop"""
        try:
            while self._running:
                await asyncio.sleep(30)  # Run every 30 seconds

                try:
                    await self._cleanup_caches()
                    await self._log_performance_summary()
                except Exception as e:
                    self.logger.error(f"Error in optimization loop: {e}")

        except asyncio.CancelledError:
            self.logger.debug("Optimization loop cancelled")
        except Exception as e:
            self.logger.error(f"Optimization loop error: {e}")

    async def _cleanup_caches(self) -> None:
        """Clean up expired cache entries"""
        try:
            # Force cleanup of expired entries
            for cache in [self.theme_cache, self.stylesheet_cache, self.path_cache]:
                # Trigger cleanup by accessing a non-existent key
                cache.get("__cleanup_trigger__")

        except Exception as e:
            self.logger.error(f"Cache cleanup error: {e}")

    async def _log_performance_summary(self) -> None:
        """Log performance summary"""
        try:
            metrics = self.monitor.get_all_metrics()
            counters = self.monitor.get_counters()

            if metrics or counters:
                summary = []

                # Add key metrics
                for metric_name in ["theme_switch", "breadcrumb_render", "path_validation"]:
                    if metric_name in metrics:
                        stats = metrics[metric_name]
                        summary.append(f"{metric_name}: {stats['avg']:.3f}s avg ({stats['count']} ops)")

                # Add cache stats
                summary.append(f"Caches: theme={self.theme_cache.size()}, "
                             f"stylesheet={self.stylesheet_cache.size()}, "
                             f"path={self.path_cache.size()}")

                if summary:
                    self.logger.debug(f"Performance summary: {', '.join(summary)}")

        except Exception as e:
            self.logger.error(f"Performance summary error: {e}")

    # Theme optimization methods

    async def optimize_theme_loading(self, theme_name: str, loader_func: callable) -> Any:
        """Optimize theme loading with caching and lazy loading"""
        if not self.enable_lazy_loading:
            return await asyncio.to_thread(loader_func)

        resource_id = f"theme_{theme_name}"
        return await self.lazy_loader.load_resource(resource_id, loader_func)

    def cache_stylesheet(self, theme_name: str, stylesheet: str) -> None:
        """Cache compiled stylesheet"""
        if self.enable_caching:
            cache_key = f"stylesheet_{theme_name}"
            self.stylesheet_cache.set(cache_key, stylesheet)

    def get_cached_stylesheet(self, theme_name: str) -> Optional[str]:
        """Get cached stylesheet"""
        if not self.enable_caching:
            return None

        cache_key = f"stylesheet_{theme_name}"
        return self.stylesheet_cache.get(cache_key)

    # Breadcrumb optimization methods

    def cache_path_info(self, path: Path, path_info: Dict[str, Any]) -> None:
        """Cache path information for breadcrumb rendering"""
        if self.enable_caching:
            cache_key = f"path_{str(path)}"
            self.path_cache.set(cache_key, path_info)

    def get_cached_path_info(self, path: Path) -> Optional[Dict[str, Any]]:
        """Get cached path information"""
        if not self.enable_caching:
            return None

        cache_key = f"path_{str(path)}"
        return self.path_cache.get(cache_key)

    async def optimize_breadcrumb_rendering(self, path: Path, segments: List[Any]) -> List[Any]:
        """Optimize breadcrumb rendering for long paths"""
        if len(segments) <= 5:  # Short paths don't need optimization
            return segments

        # Use cached truncation if available
        cache_key = f"truncated_{str(path)}_{len(segments)}"
        cached_result = self.path_cache.get(cache_key)
        if cached_result:
            return cached_result

        # Apply smart truncation
        optimized_segments = await self._apply_smart_truncation(segments)

        # Cache result
        self.path_cache.set(cache_key, optimized_segments)

        return optimized_segments

    async def _apply_smart_truncation(self, segments: List[Any]) -> List[Any]:
        """Apply smart truncation to breadcrumb segments"""
        if len(segments) <= 7:
            return segments

        # Keep first 2, last 3, and add ellipsis in between
        truncated = segments[:2] + ["..."] + segments[-3:]
        return truncated

    # Monitoring methods

    def start_theme_operation(self, operation_name: str) -> str:
        """Start monitoring a theme operation"""
        if not self.enable_monitoring:
            return ""

        operation_id = f"theme_{operation_name}_{time.time()}"
        self.monitor.start_operation(operation_id)
        return operation_id

    def end_theme_operation(self, operation_id: str) -> float:
        """End monitoring a theme operation"""
        if not self.enable_monitoring or not operation_id:
            return 0.0

        return self.monitor.end_operation(operation_id, "theme_switch")

    def start_navigation_operation(self, operation_name: str) -> str:
        """Start monitoring a navigation operation"""
        if not self.enable_monitoring:
            return ""

        operation_id = f"nav_{operation_name}_{time.time()}"
        self.monitor.start_operation(operation_id)
        return operation_id

    def end_navigation_operation(self, operation_id: str) -> float:
        """End monitoring a navigation operation"""
        if not self.enable_monitoring or not operation_id:
            return 0.0

        return self.monitor.end_operation(operation_id, "breadcrumb_render")

    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        return {
            "metrics": self.monitor.get_all_metrics(),
            "counters": self.monitor.get_counters(),
            "cache_stats": {
                "theme_cache_size": self.theme_cache.size(),
                "stylesheet_cache_size": self.stylesheet_cache.size(),
                "path_cache_size": self.path_cache.size()
            },
            "optimization_settings": {
                "lazy_loading_enabled": self.enable_lazy_loading,
                "caching_enabled": self.enable_caching,
                "monitoring_enabled": self.enable_monitoring
            }
        }
