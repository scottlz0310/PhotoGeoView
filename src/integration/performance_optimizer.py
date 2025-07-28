"""
Performance Optimizer for AI Integration

Implements comprehensive performance optimization across all integrated components:
- Memory usage optimization and garbage collection management
- Intelligent caching strategies for shared resources
- Asynchronous processing coordination for heavy operations
- Resource pooling and connection management

Author: Kiro AI Integration System
"""

import asyncio
import gc
import threading
import time
import weakref
from typing import Dict, Any, List, Optional, Callable, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from pathlib import Path
import psutil

from .models import AIComponent, PerformanceMetrics
from .config_manager import ConfigManager
from .unified_cache import UnifiedCacheSystem
from .performance_monitor import KiroPerformanceMonitor
from .logging_system import LoggerSystem
from .error_handling import IntegratedErrorHandler, ErrorCategory


@dataclass
class OptimizationStrategy:
    """Performance optimization strategy configuration"""

    name: str
    enabled: bool = True
    print = 1  # 1=highest, 5=lowest
    target_components: List[AIComponent] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    last_applied: Optional[datetime] = None
    effectiveness_score: float = 0.0


@dataclass
class ResourcePool:
    """Resource pool for managing shared resources"""

    name: str
    resource_type: str
    max_size: int
    current_size: int = 0
    available_resources: deque = field(default_factory=deque)
    in_use_resources: Set = field(default_factory=set)
    creation_count: int = 0
    destruction_count: int = 0
    hit_count: int = 0
    miss_count: int = 0


class PerformanceOptimizer:
    """
    Comprehensive performance optimizer for AI integration

    Responsibilities:
    - Memory usage optimization across all components
    - Intelligent caching strategy implementation
    - Asynchronous processing coordination
    - Resource pooling and lifecycle management
    - Performance bottleneck identification and resolution
    """

    def __init__(
        self,
        config_manager: ConfigManager,
        cache_system: UnifiedCacheSystem,
        performance_monitor: KiroPerformanceMonitor,
        logger_system: LoggerSystem = None,
    ):
        """
        Initialize performance optimizer

        Args:
            config_manager: Configuration manager
            cache_system: Unified cache system
            performance_monitor: Performance monitor
            logger_system: Logging system
        """
        self.config_manager = config_manager
        self.cache_system = cache_system
        self.performance_monitor = performance_monitor
        self.logger_system = logger_system or LoggerSystem()
        self.error_handler = IntegratedErrorHandler(self.logger_system)

        # Optimization state
        self.is_optimizing = False
        self.optimization_thread: Optional[threading.Thread] = None
        self.optimization_lock = threading.RLock()

        # Optimization strategies
        self.strategies: Dict[str, OptimizationStrategy] = {}
        self.active_optimizations: Set[str] = set()

        # Resource pools
        self.resource_pools: Dict[str, ResourcePool] = {}

        # Thread pools for different types of operations
        self.io_thread_pool = ThreadPoolExecutor(
            max_workers=4, thread_name_prefix="optimizer_io"
        )
        self.cpu_thread_pool = ThreadPoolExecutor(
            max_workers=2, thread_name_prefix="optimizer_cpu"
        )
        self.process_pool = ProcessPoolExecutor(max_workers=2)

        # Performance tracking
        self.optimization_history: deque = deque(maxlen=500)
        self.bottleneck_detection: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=100)
        )

        # Memory management
        self.memory_pressure_threshold = 0.8  # 80% memory usage
        self.gc_frequency = 30  # seconds
        self.last_gc_time = time.time()

        # Async processing coordination
        self.async_tasks: Dict[str, asyncio.Task] = {}
        self.task_priorities: Dict[str, int] = {}

        # Initialize optimization strategies
        self._initialize_strategies()

        # Start optimization monitoring
        self.start_optimization()

        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "performance_optimizer_init",
            "Performance optimizer initialized",
        )

    def _initialize_strategies(self):
        """Initialize optimization strategies"""
        try:
            # Memory optimization strategies
            self.strategies["memory_cleanup"] = OptimizationStrategy(
                name="memory_cleanup",
                priority=1,
                target_components=[AIComponent.KIRO],
                parameters={
                    "gc_threshold": 0.8,
                    "cleanup_interval": 30,
                    "aggressive_mode": False,
                },
            )

            self.strategies["cache_optimization"] = OptimizationStrategy(
                name="cache_optimization",
                priority=2,
                target_components=[AIComponent.KIRO],
                parameters={
                    "max_cache_size": 200 * 1024 * 1024,  # 200MB
                    "eviction_policy": "lru",
                    "compression_enabled": True,
                },
            )

            # UI optimization strategies
            self.strategies["ui_responsiveness"] = OptimizationStrategy(
                name="ui_responsiveness",
                priority=1,
                target_components=[AIComponent.CURSOR],
                parameters={
                    "max_ui_thread_time": 16,  # 16ms for 60fps
                    "background_processing": True,
                    "lazy_loading": True,
                },
            )

            self.strategies["thumbnail_optimization"] = OptimizationStrategy(
                name="thumbnail_optimization",
                priority=2,
                target_components=[AIComponent.CURSOR],
                parameters={
                    "batch_size": 10,
                    "preload_distance": 20,
                    "quality_scaling": True,
                },
            )

            # Core processing optimization strategies
            self.strategies["image_processing"] = OptimizationStrategy(
                name="image_processing",
                priority=2,
                target_components=[AIComponent.COPILOT],
                parameters={
                    "parallel_processing": True,
                    "chunk_size": 1024 * 1024,  # 1MB chunks
                    "use_gpu": False,
                },
            )

            self.strategies["exif_processing"] = OptimizationStrategy(
                name="exif_processing",
                priority=3,
                target_components=[AIComponent.COPILOT],
                parameters={
                    "batch_processing": True,
                    "cache_parsed_data": True,
                    "skip_thumbnails": False,
                },
            )

            # Resource pooling strategies
            self.strategies["connection_pooling"] = OptimizationStrategy(
                name="connection_pooling",
                priority=3,
                target_components=[AIComponent.KIRO],
                parameters={
                    "max_connections": 10,
                    "idle_timeout": 300,
                    "validation_interval": 60,
                },
            )

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "strategies_initialized",
                f"Initialized {len(self.strategies)} optimization strategies",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "initialize_strategies"},
                AIComponent.KIRO,
            )

    def start_optimization(self):
        """Start performance optimization monitoring"""
        try:
            with self.optimization_lock:
                if self.is_optimizing:
                    return

                self.is_optimizing = True
                self.optimization_thread = threading.Thread(
                    target=self._optimization_loop,
                    name="performance_optimizer",
                    daemon=True,
                )
                self.optimization_thread.start()

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "optimization_started",
                "Performance optimization monitoring started",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "start_optimization"},
                AIComponent.KIRO,
            )

    def stop_optimization(self):
        """Stop performance optimization monitoring"""
        try:
            with self.optimization_lock:
                self.is_optimizing = False

            if self.optimization_thread and self.optimization_thread.is_alive():
                self.optimization_thread.join(timeout=5.0)

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "optimization_stopped",
                "Performance optimization monitoring stopped",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "stop_optimization"},
                AIComponent.KIRO,
            )

    def _optimization_loop(self):
        """Main optimization monitoring loop"""
        while self.is_optimizing:
            try:
                # Check system performance
                current_metrics = self._collect_performance_metrics()

                # Detect bottlenecks
                bottlenecks = self._detect_bottlenecks(current_metrics)

                # Apply optimizations based on bottlenecks
                if bottlenecks:
                    self._apply_optimizations(bottlenecks)

                # Perform routine maintenance
                self._perform_maintenance()

                # Sleep before next iteration
                time.sleep(5.0)  # Check every 5 seconds

            except Exception as e:
                self.error_handler.handle_error(
                    e,
                    ErrorCategory.INTEGRATION_ERROR,
                    {"operation": "optimization_loop"},
                    AIComponent.KIRO,
                )
                time.sleep(10.0)  # Longer sleep on error

    def _collect_performance_metrics(self) -> Dict[str, Any]:
        """Collect current performance metrics"""
        try:
            process = psutil.Process()

            metrics = {
                "timestamp": datetime.now(),
                "memory": {
                    "rss": process.memory_info().rss,
                    "vms": process.memory_info().vms,
                    "percent": process.memory_percent(),
                    "available": psutil.virtual_memory().available,
                },
                "cpu": {
                    "percent": process.cpu_percent(),
                    "system_percent": psutil.cpu_percent(),
                    "threads": process.num_threads(),
                },
                "io": {
                    "read_bytes": process.io_counters().read_bytes,
                    "write_bytes": process.io_counters().write_bytes,
                },
                "cache": {
                    "size": self.cache_system.get_cache_size(),
                    "hit_rate": self.cache_system.get_hit_rate(),
                    "entries": self.cache_system.get_entry_count(),
                },
            }

            return metrics

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "collect_performance_metrics"},
                AIComponent.KIRO,
            )
            return {}

    def _detect_bottlenecks(self, metrics: Dict[str, Any]) -> List[str]:
        """Detect performance bottlenecks"""
        bottlenecks = []

        try:
            if not metrics:
                return bottlenecks

            # Memory bottlenecks
            memory_percent = metrics.get("memory", {}).get("percent", 0)
            if memory_percent > 80:
                bottlenecks.append("high_memory_usage")
                self.bottleneck_detection["memory"].append(memory_percent)

            # CPU bottlenecks
            cpu_percent = metrics.get("cpu", {}).get("percent", 0)
            if cpu_percent > 70:
                bottlenecks.append("high_cpu_usage")
                self.bottleneck_detection["cpu"].append(cpu_percent)

            # Cache bottlenecks
            cache_hit_rate = metrics.get("cache", {}).get("hit_rate", 1.0)
            if cache_hit_rate < 0.7:  # Less than 70% hit rate
                bottlenecks.append("low_cache_hit_rate")
                self.bottleneck_detection["cache"].append(cache_hit_rate)

            # I/O bottlenecks (simplified detection)
            io_metrics = metrics.get("io", {})
            if io_metrics:
                # Store for trend analysis
                self.bottleneck_detection["io"].append(
                    io_metrics.get("read_bytes", 0) + io_metrics.get("write_bytes", 0)
                )

            return bottlenecks

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "detect_bottlenecks"},
                AIComponent.KIRO,
            )
            return []

    def _apply_optimizations(self, bottlenecks: List[str]):
        """Apply optimizations based on detected bottlenecks"""
        try:
            for bottleneck in bottlenecks:
                if bottleneck == "high_memory_usage":
                    self._optimize_memory_usage()
                elif bottleneck == "high_cpu_usage":
                    self._optimize_cpu_usage()
                elif bottleneck == "low_cache_hit_rate":
                    self._optimize_cache_performance()

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "apply_optimizations", "bottlenecks": bottlenecks},
                AIComponent.KIRO,
            )

    def _optimize_memory_usage(self):
        """Optimize memory usage"""
        try:
            strategy = self.strategies.get("memory_cleanup")
            if not strategy or not strategy.enabled:
                return

            # Force garbage collection
            collected = gc.collect()

            # Clear cache if memory pressure is high
            memory_percent = psutil.Process().memory_percent()
            if memory_percent > 85:
                self.cache_system.clear_expired()

                # More aggressive cleanup if still high
                if psutil.Process().memory_percent() > 90:
                    self.cache_system.clear_lru(0.3)  # Clear 30% of LRU items

            # Update strategy effectiveness
            strategy.last_applied = datetime.now()
            strategy.effectiveness_score = max(0, 100 - memory_percent) / 100

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "memory_optimized",
                f"Memory optimization applied, collected {collected} objects",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "optimize_memory_usage"},
                AIComponent.KIRO,
            )

    def _optimize_cpu_usage(self):
        """Optimize CPU usage"""
        try:
            strategy = self.strategies.get("ui_responsiveness")
            if not strategy or not strategy.enabled:
                return

            # Reduce thread pool sizes temporarily
            if hasattr(self.io_thread_pool, "_max_workers"):
                original_workers = self.io_thread_pool._max_workers
                if original_workers > 2:
                    # Temporarily reduce workers
                    self.io_thread_pool._max_workers = max(2, original_workers - 1)

            # Increase sleep intervals in background tasks
            self._adjust_background_task_intervals(1.5)  # 50% slower

            strategy.last_applied = datetime.now()

            self.logger_system.log_ai_operation(
                AIComponent.KIRO, "cpu_optimized", "CPU usage optimization applied"
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "optimize_cpu_usage"},
                AIComponent.KIRO,
            )

    def _optimize_cache_performance(self):
        """Optimize cache performance"""
        try:
            strategy = self.strategies.get("cache_optimization")
            if not strategy or not strategy.enabled:
                return

            # Analyze cache usage patterns
            cache_stats = self.cache_system.get_statistics()

            # Adjust cache size if needed
            current_size = cache_stats.get("size", 0)
            max_size = strategy.parameters.get("max_cache_size", 200 * 1024 * 1024)

            if current_size > max_size * 0.9:  # 90% full
                # Increase cache size if memory allows
                memory_percent = psutil.Process().memory_percent()
                if memory_percent < 70:
                    new_max_size = min(max_size * 1.2, 500 * 1024 * 1024)  # Max 500MB
                    self.cache_system.set_max_size(new_max_size)
                    strategy.parameters["max_cache_size"] = new_max_size

            # Optimize eviction policy
            hit_rate = cache_stats.get("hit_rate", 0)
            if hit_rate < 0.6:  # Less than 60%
                # Switch to more aggressive caching
                self.cache_system.set_eviction_policy("lfu")  # Least Frequently Used

            strategy.last_applied = datetime.now()
            strategy.effectiveness_score = hit_rate

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "cache_optimized",
                f"Cache optimization applied, hit rate: {hit_rate:.2f}",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "optimize_cache_performance"},
                AIComponent.KIRO,
            )

    def _adjust_background_task_intervals(self, multiplier: float):
        """Adjust background task intervals"""
        try:
            # This would adjust intervals of background tasks
            # Implementation depends on specific task management system
            pass

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "adjust_background_task_intervals"},
                AIComponent.KIRO,
            )

    def _perform_maintenance(self):
        """Perform routine maintenance tasks"""
        try:
            current_time = time.time()

            # Garbage collection
            if current_time - self.last_gc_time > self.gc_frequency:
                gc.collect()
                self.last_gc_time = current_time

            # Clean up completed async tasks
            completed_tasks = [
                task_id for task_id, task in self.async_tasks.items() if task.done()
            ]

            for task_id in completed_tasks:
                del self.async_tasks[task_id]
                if task_id in self.task_priorities:
                    del self.task_priorities[task_id]

            # Update resource pools
            self._maintain_resource_pools()

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "perform_maintenance"},
                AIComponent.KIRO,
            )

    def _maintain_resource_pools(self):
        """Maintain resource pools"""
        try:
            for pool_name, pool in self.resource_pools.items():
                # Remove expired resources
                current_time = time.time()
                expired_resources = []

                for resource in list(pool.available_resources):
                    if hasattr(resource, "last_used"):
                        if current_time - resource.last_used > 300:  # 5 minutes
                            expired_resources.append(resource)

                for resource in expired_resources:
                    pool.available_resources.remove(resource)
                    pool.current_size -= 1
                    pool.destruction_count += 1

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "maintain_resource_pools"},
                AIComponent.KIRO,
            )

    # Public API methods

    def create_resource_pool(
        self, name: str, resource_type: str, max_size: int
    ) -> bool:
        """Create a new resource pool"""
        try:
            if name in self.resource_pools:
                return False

            self.resource_pools[name] = ResourcePool(
                name=name, resource_type=resource_type, max_size=max_size
            )

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "resource_pool_created",
                f"Resource pool created: {name} ({resource_type}, max_size={max_size})",
            )

            return True

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "create_resource_pool", "name": name},
                AIComponent.KIRO,
            )
            return False

    def get_resource(self, pool_name: str, factory_func: Callable = None):
        """Get resource from pool"""
        try:
            if pool_name not in self.resource_pools:
                return None

            pool = self.resource_pools[pool_name]

            # Try to get from available resources
            if pool.available_resources:
                resource = pool.available_resources.popleft()
                pool.in_use_resources.add(resource)
                pool.hit_count += 1
                return resource

            # Create new resource if under limit
            if pool.current_size < pool.max_size and factory_func:
                resource = factory_func()
                pool.in_use_resources.add(resource)
                pool.current_size += 1
                pool.creation_count += 1
                pool.miss_count += 1
                return resource

            # Pool is full and no available resources
            pool.miss_count += 1
            return None

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "get_resource", "pool": pool_name},
                AIComponent.KIRO,
            )
            return None

    def return_resource(self, pool_name: str, resource):
        """Return resource to pool"""
        try:
            if pool_name not in self.resource_pools:
                return False

            pool = self.resource_pools[pool_name]

            if resource in pool.in_use_resources:
                pool.in_use_resources.remove(resource)

                # Mark last used time
                if hasattr(resource, "last_used"):
                    resource.last_used = time.time()
                else:
                    setattr(resource, "last_used", time.time())

                pool.available_resources.append(resource)
                return True

            return False

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "return_resource", "pool": pool_name},
                AIComponent.KIRO,
            )
            return False

    def submit_async_task(self, task_id: str, coro, priority: int = 3) -> bool:
        """Submit asynchronous task with priority"""
        try:
            if task_id in self.async_tasks:
                return False  # Task already exists

            # Create task
            task = asyncio.create_task(coro)
            self.async_tasks[task_id] = task
            self.task_priorities[task_id] = priority

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "async_task_submitted",
                f"Async task submitted: {task_id} (priority={priority})",
            )

            return True

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "submit_async_task", "task_id": task_id},
                AIComponent.KIRO,
            )
            return False

    def cancel_async_task(self, task_id: str) -> bool:
        """Cancel asynchronous task"""
        try:
            if task_id not in self.async_tasks:
                return False

            task = self.async_tasks[task_id]
            task.cancel()

            del self.async_tasks[task_id]
            if task_id in self.task_priorities:
                del self.task_priorities[task_id]

            return True

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "cancel_async_task", "task_id": task_id},
                AIComponent.KIRO,
            )
            return False

    def get_optimization_status(self) -> Dict[str, Any]:
        """Get current optimization status"""
        try:
            return {
                "is_optimizing": self.is_optimizing,
                "active_strategies": len(
                    [s for s in self.strategies.values() if s.enabled]
                ),
                "resource_pools": {
                    name: {
                        "size": pool.current_size,
                        "max_size": pool.max_size,
                        "hit_rate": (
                            pool.hit_count / (pool.hit_count + pool.miss_count)
                            if (pool.hit_count + pool.miss_count) > 0
                            else 0
                        ),
                        "utilization": (
                            pool.current_size / pool.max_size
                            if pool.max_size > 0
                            else 0
                        ),
                    }
                    for name, pool in self.resource_pools.items()
                },
                "async_tasks": len(self.async_tasks),
                "recent_bottlenecks": {
                    name: list(deque_data)[-5:] if deque_data else []
                    for name, deque_data in self.bottleneck_detection.items()
                },
            }

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "get_optimization_status"},
                AIComponent.KIRO,
            )
            return {}

    def enable_strategy(self, strategy_name: str) -> bool:
        """Enable optimization strategy"""
        try:
            if strategy_name in self.strategies:
                self.strategies[strategy_name].enabled = True
                return True
            return False

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "enable_strategy", "strategy": strategy_name},
                AIComponent.KIRO,
            )
            return False

    def disable_strategy(self, strategy_name: str) -> bool:
        """Disable optimization strategy"""
        try:
            if strategy_name in self.strategies:
                self.strategies[strategy_name].enabled = False
                return True
            return False

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "disable_strategy", "strategy": strategy_name},
                AIComponent.KIRO,
            )
            return False

    def cleanup(self):
        """Cleanup optimizer resources"""
        try:
            # Stop optimization
            self.stop_optimization()

            # Shutdown thread pools
            self.io_thread_pool.shutdown(wait=False)
            self.cpu_thread_pool.shutdown(wait=False)
            self.process_pool.shutdown(wait=False)

            # Cancel async tasks
            for task_id in list(self.async_tasks.keys()):
                self.cancel_async_task(task_id)

            # Clear resource pools
            self.resource_pools.clear()

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "performance_optimizer_cleanup",
                "Performance optimizer cleaned up",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "cleanup"},
                AIComponent.KIRO,
            )
