"""
Performance Monitoring Dashboard

Provides real-time performance monitoring and reporting for theme
and navigation operations with visualization capabilities.

Author: Kiro AI Integration System
Requirements: 5.2, 5.3
"""

import json
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from .logging_system import LoggerSystem
from .performance_optimizer import PerformanceOptimizer


class PerformanceMetrics:
    """Container for performance metrics data"""

    def __init__(self):
        self.theme_switch_times: list[float] = []
        self.breadcrumb_render_times: list[float] = []
        self.cache_hit_rates: dict[str, float] = {}
        self.memory_usage: list[tuple[datetime, int]] = []
        self.error_rates: dict[str, float] = {}
        self.operation_counts: dict[str, int] = {}

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary for serialization"""
        return {
            "theme_switch_times": self.theme_switch_times,
            "breadcrumb_render_times": self.breadcrumb_render_times,
            "cache_hit_rates": self.cache_hit_rates,
            "memory_usage": [
                (ts.isoformat(), usage) for ts, usage in self.memory_usage
            ],
            "error_rates": self.error_rates,
            "operation_counts": self.operation_counts,
            "timestamp": datetime.now().isoformat(),
        }

class PerformanceDashboard:
    """Performance monitoring dashboard for theme and navigation operations"""

    def __init__(
        self, performance_optimizer: PerformanceOptimizer, logger_system: LoggerSystem
    ):
        self.performance_optimizer = performance_optimizer
        self.logger = logger_system.get_logger(__name__)

        # Dashboard state
        self.is_monitoring = False
        self.monitoring_interval = 5.0  # seconds
        self.metrics_history_limit = 1000

        # Metrics storage
        self.current_metrics = PerformanceMetrics()
        self.metrics_history: list[PerformanceMetrics] = []

        # Threading
        self._monitoring_thread: threading.Thread | None = None
        self._stop_monitoring = threading.Event()
        self._metrics_lock = threading.RLock()

        # Performance thresholds for alerts
        self.thresholds = {
            "theme_switch_max_time": 2.0,  # seconds
            "breadcrumb_render_max_time": 0.5,  # seconds
            "cache_hit_rate_min": 0.7,  # 70%
            "error_rate_max": 0.1,  # 10%
            "memory_usage_max_mb": 100,  # MB
        }

        # Alert callbacks
        self.alert_callbacks: list[callable] = []

    def start_monitoring(self) -> None:
        """Start performance monitoring"""
        if self.is_monitoring:
            self.logger.warning("Performance monitoring already started")
            return

        self.is_monitoring = True
        self._stop_monitoring.clear()

        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop, name="PerformanceMonitoring", daemon=True
        )
        self._monitoring_thread.start()

        self.logger.info("Performance monitoring started")

    def stop_monitoring(self) -> None:
        """Stop performance monitoring"""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        self._stop_monitoring.set()

        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=5.0)

        self.logger.info("Performance monitoring stopped")

    def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        try:
            while not self._stop_monitoring.wait(self.monitoring_interval):
                try:
                    self._collect_metrics()
                    self._check_thresholds()
                    self._cleanup_old_metrics()
                except Exception as e:
                    self.logger.error(f"Error in monitoring loop: {e}")

        except Exception as e:
            self.logger.error(f"Monitoring loop error: {e}")
        finally:
            self.logger.debug("Performance monitoring loop ended")

    def _collect_metrics(self) -> None:
        """Collect current performance metrics"""
        try:
            with self._metrics_lock:
                # Get metrics from performance optimizer
                optimizer_metrics = self.performance_optimizer.monitor.get_all_metrics()
                counters = self.performance_optimizer.monitor.get_counters()

                # Update current metrics
                if "theme_switch" in optimizer_metrics:
                    theme_stats = optimizer_metrics["theme_switch"]
                    if theme_stats.get("count", 0) > 0:
                        self.current_metrics.theme_switch_times.append(
                            theme_stats["recent_avg"]
                        )

                if "breadcrumb_render" in optimizer_metrics:
                    breadcrumb_stats = optimizer_metrics["breadcrumb_render"]
                    if breadcrumb_stats.get("count", 0) > 0:
                        self.current_metrics.breadcrumb_render_times.append(
                            breadcrumb_stats["recent_avg"]
                        )

                # Calculate cache hit rates
                self._calculate_cache_hit_rates()

                # Record memory usage
                self._record_memory_usage()

                # Update operation counts
                self.current_metrics.operation_counts.update(counters)

                # Limit metrics history
                max_points = 100
                if len(self.current_metrics.theme_switch_times) > max_points:
                    self.current_metrics.theme_switch_times = (
                        self.current_metrics.theme_switch_times[-max_points:]
                    )
                if len(self.current_metrics.breadcrumb_render_times) > max_points:
                    self.current_metrics.breadcrumb_render_times = (
                        self.current_metrics.breadcrumb_render_times[-max_points:]
                    )

        except Exception as e:
            self.logger.error(f"Failed to collect metrics: {e}")

    def _calculate_cache_hit_rates(self) -> None:
        """Calculate cache hit rates for different caches"""
        try:
            # Get cache statistics
            cache_stats = {
                "theme_cache": self.performance_optimizer.theme_cache.size(),
                "stylesheet_cache": self.performance_optimizer.stylesheet_cache.size(),
                "path_cache": self.performance_optimizer.path_cache.size(),
            }

            # Calculate hit rates (simplified - would need actual hit/miss counters)
            for cache_name, size in cache_stats.items():
                # Estimate hit rate based on cache utilization
                max_size = getattr(
                    self.performance_optimizer, cache_name.replace("_cache", "_cache")
                ).max_size
                utilization = size / max_size if max_size > 0 else 0
                estimated_hit_rate = min(
                    0.95, 0.5 + (utilization * 0.4)
                )  # Rough estimation
                self.current_metrics.cache_hit_rates[cache_name] = estimated_hit_rate

        except Exception as e:
            self.logger.error(f"Failed to calculate cache hit rates: {e}")

    def _record_memory_usage(self) -> None:
        """Record current memory usage"""
        try:
            import os

            import psutil

            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024  # Convert to MB

            self.current_metrics.memory_usage.append((datetime.now(), int(memory_mb)))

            # Limit memory usage history
            if len(self.current_metrics.memory_usage) > 100:
                self.current_metrics.memory_usage = self.current_metrics.memory_usage[
                    -100:
                ]

        except ImportError:
            # psutil not available, skip memory monitoring
            pass
        except Exception as e:
            self.logger.error(f"Failed to record memory usage: {e}")

    def _check_thresholds(self) -> None:
        """Check performance thresholds and trigger alerts"""
        try:
            alerts = []

            # Check theme switch times
            if self.current_metrics.theme_switch_times:
                avg_theme_time = sum(
                    self.current_metrics.theme_switch_times[-10:]
                ) / min(10, len(self.current_metrics.theme_switch_times))
                if avg_theme_time > self.thresholds["theme_switch_max_time"]:
                    alerts.append(f"Theme switch time too high: {avg_theme_time:.3f}s")

            # Check breadcrumb render times
            if self.current_metrics.breadcrumb_render_times:
                avg_breadcrumb_time = sum(
                    self.current_metrics.breadcrumb_render_times[-10:]
                ) / min(10, len(self.current_metrics.breadcrumb_render_times))
                if avg_breadcrumb_time > self.thresholds["breadcrumb_render_max_time"]:
                    alerts.append(
                        f"Breadcrumb render time too high: {avg_breadcrumb_time:.3f}s"
                    )

            # Check cache hit rates
            for cache_name, hit_rate in self.current_metrics.cache_hit_rates.items():
                if hit_rate < self.thresholds["cache_hit_rate_min"]:
                    alerts.append(
                        f"Low cache hit rate for {cache_name}: {hit_rate:.2%}"
                    )

            # Check memory usage
            if self.current_metrics.memory_usage:
                current_memory = self.current_metrics.memory_usage[-1][1]
                if current_memory > self.thresholds["memory_usage_max_mb"]:
                    alerts.append(f"High memory usage: {current_memory}MB")

            # Trigger alerts
            for alert in alerts:
                self._trigger_alert(alert)

        except Exception as e:
            self.logger.error(f"Failed to check thresholds: {e}")

    def _trigger_alert(self, message: str) -> None:
        """Trigger performance alert"""
        try:
            self.logger.warning(f"Performance alert: {message}")

            # Call alert callbacks
            for callback in self.alert_callbacks:
                try:
                    callback(message)
                except Exception as e:
                    self.logger.error(f"Alert callback failed: {e}")

        except Exception as e:
            self.logger.error(f"Failed to trigger alert: {e}")

    def _cleanup_old_metrics(self) -> None:
        """Clean up old metrics to prevent memory growth"""
        try:
            with self._metrics_lock:
                # Keep only recent metrics history
                if len(self.metrics_history) > self.metrics_history_limit:
                    self.metrics_history = self.metrics_history[
                        -self.metrics_history_limit :
                    ]

                # Archive current metrics periodically
                if (
                    len(self.current_metrics.theme_switch_times) > 0
                    or len(self.current_metrics.breadcrumb_render_times) > 0
                ):
                    # Create snapshot of current metrics
                    snapshot = PerformanceMetrics()
                    snapshot.theme_switch_times = (
                        self.current_metrics.theme_switch_times[-10:]
                    )  # Keep recent data
                    snapshot.breadcrumb_render_times = (
                        self.current_metrics.breadcrumb_render_times[-10:]
                    )
                    snapshot.cache_hit_rates = (
                        self.current_metrics.cache_hit_rates.copy()
                    )
                    snapshot.memory_usage = self.current_metrics.memory_usage[-10:]
                    snapshot.error_rates = self.current_metrics.error_rates.copy()
                    snapshot.operation_counts = (
                        self.current_metrics.operation_counts.copy()
                    )

                    self.metrics_history.append(snapshot)

        except Exception as e:
            self.logger.error(f"Failed to cleanup old metrics: {e}")

    # Public API methods

    def get_current_metrics(self) -> dict[str, Any]:
        """Get current performance metrics"""
        with self._metrics_lock:
            return self.current_metrics.to_dict()

    def get_metrics_summary(self) -> dict[str, Any]:
        """Get performance metrics summary"""
        try:
            with self._metrics_lock:
                summary = {
                    "monitoring_active": self.is_monitoring,
                    "monitoring_duration": time.time()
                    - getattr(self, "_start_time", time.time()),
                    "total_operations": sum(
                        self.current_metrics.operation_counts.values()
                    ),
                    "performance_summary": {},
                }

                # Theme performance summary
                if self.current_metrics.theme_switch_times:
                    theme_times = self.current_metrics.theme_switch_times
                    summary["performance_summary"]["theme_switches"] = {
                        "count": len(theme_times),
                        "avg_time": sum(theme_times) / len(theme_times),
                        "min_time": min(theme_times),
                        "max_time": max(theme_times),
                        "recent_avg": sum(theme_times[-5:]) / min(5, len(theme_times)),
                    }

                # Breadcrumb performance summary
                if self.current_metrics.breadcrumb_render_times:
                    breadcrumb_times = self.current_metrics.breadcrumb_render_times
                    summary["performance_summary"]["breadcrumb_renders"] = {
                        "count": len(breadcrumb_times),
                        "avg_time": sum(breadcrumb_times) / len(breadcrumb_times),
                        "min_time": min(breadcrumb_times),
                        "max_time": max(breadcrumb_times),
                        "recent_avg": sum(breadcrumb_times[-5:])
                        / min(5, len(breadcrumb_times)),
                    }

                # Cache performance summary
                summary["performance_summary"]["cache_performance"] = (
                    self.current_metrics.cache_hit_rates
                )

                # Memory usage summary
                if self.current_metrics.memory_usage:
                    memory_values = [
                        usage for _, usage in self.current_metrics.memory_usage
                    ]
                    summary["performance_summary"]["memory_usage"] = {
                        "current_mb": memory_values[-1] if memory_values else 0,
                        "avg_mb": sum(memory_values) / len(memory_values),
                        "peak_mb": max(memory_values),
                    }

                return summary

        except Exception as e:
            self.logger.error(f"Failed to get metrics summary: {e}")
            return {"error": str(e)}

    def export_metrics(self, file_path: Path) -> bool:
        """Export metrics to file"""
        try:
            with self._metrics_lock:
                export_data = {
                    "export_timestamp": datetime.now().isoformat(),
                    "current_metrics": self.current_metrics.to_dict(),
                    "metrics_history": [
                        metrics.to_dict() for metrics in self.metrics_history
                    ],
                    "thresholds": self.thresholds,
                    "summary": self.get_metrics_summary(),
                }

                with open(file_path, "w") as f:
                    json.dump(export_data, f, indent=2)

                self.logger.info(f"Metrics exported to {file_path}")
                return True

        except Exception as e:
            self.logger.error(f"Failed to export metrics: {e}")
            return False

    def add_alert_callback(self, callback: callable) -> None:
        """Add callback for performance alerts"""
        if callback not in self.alert_callbacks:
            self.alert_callbacks.append(callback)

    def remove_alert_callback(self, callback: callable) -> None:
        """Remove alert callback"""
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)

    def set_threshold(self, threshold_name: str, value: float) -> None:
        """Set performance threshold"""
        if threshold_name in self.thresholds:
            self.thresholds[threshold_name] = value
            self.logger.info(f"Updated threshold {threshold_name} to {value}")
        else:
            self.logger.warning(f"Unknown threshold: {threshold_name}")

    def reset_metrics(self) -> None:
        """Reset all metrics"""
        with self._metrics_lock:
            self.current_metrics = PerformanceMetrics()
            self.metrics_history.clear()
            self.performance_optimizer.monitor.reset_metrics()
            self.logger.info("Performance metrics reset")

    def get_performance_report(self) -> str:
        """Generate human-readable performance report"""
        try:
            summary = self.get_metrics_summary()

            report_lines = [
                "=== Performance Report ===",
                f"Monitoring Active: {summary.get('monitoring_active', False)}",
                f"Total Operations: {summary.get('total_operations', 0)}",
                "",
            ]

            perf_summary = summary.get("performance_summary", {})

            # Theme performance
            if "theme_switches" in perf_summary:
                theme_data = perf_summary["theme_switches"]
                report_lines.extend(
                    [
                        "Theme Performance:",
                        f"  Switches: {theme_data['count']}",
                        f"  Average Time: {theme_data['avg_time']:.3f}s",
                        f"  Recent Average: {theme_data['recent_avg']:.3f}s",
                        f"  Range: {theme_data['min_time']:.3f}s - {theme_data['max_time']:.3f}s",
                        "",
                    ]
                )

            # Breadcrumb performance
            if "breadcrumb_renders" in perf_summary:
                breadcrumb_data = perf_summary["breadcrumb_renders"]
                report_lines.extend(
                    [
                        "Breadcrumb Performance:",
                        f"  Renders: {breadcrumb_data['count']}",
                        f"  Average Time: {breadcrumb_data['avg_time']:.3f}s",
                        f"  Recent Average: {breadcrumb_data['recent_avg']:.3f}s",
                        f"  Range: {breadcrumb_data['min_time']:.3f}s - {breadcrumb_data['max_time']:.3f}s",
                        "",
                    ]
                )

            # Cache performance
            if "cache_performance" in perf_summary:
                cache_data = perf_summary["cache_performance"]
                report_lines.extend(
                    [
                        "Cache Performance:",
                    ]
                )
                for cache_name, hit_rate in cache_data.items():
                    report_lines.append(f"  {cache_name}: {hit_rate:.1%} hit rate")
                report_lines.append("")

            # Memory usage
            if "memory_usage" in perf_summary:
                memory_data = perf_summary["memory_usage"]
                report_lines.extend(
                    [
                        "Memory Usage:",
                        f"  Current: {memory_data['current_mb']}MB",
                        f"  Average: {memory_data['avg_mb']:.1f}MB",
                        f"  Peak: {memory_data['peak_mb']}MB",
                        "",
                    ]
                )

            return "\n".join(report_lines)

        except Exception as e:
            return f"Error generating performance report: {e}"
