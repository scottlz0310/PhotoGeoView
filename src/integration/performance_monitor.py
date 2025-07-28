"""
Kiro Performance Monitor

Real-time system monitoring for AI integration:
- Memory usage and CPU monitoring
- AI component health checks and status tracking
- Performance alerting and threshold management
- Resource usage optimization

Author: Kiro AI Integration System
"""

import asyncio
import threading
import time
import psutil
import os
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque
from pathlib import Path

from .interfaces import IPerformanceMonitor
from .models import AIComponent, PerformanceMetrics
from .config_manager import ConfigManager
from .error_handling import IntegratedErrorHandler, ErrorCategory
from .logging_system import LoggerSystem


@dataclass
class PerformanceAlert:
    """Performance alert data structure"""
    level: str  # info, warning, critical
    message: str
    component: AIComponent
    metric_name: str
    current_value: float
    threshold: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ResourceThresholds:
    """Resource usage thresholds for alerting"""
    memory_warning_mb: float = 400.0
    memory_critical_mb: float = 600.0
    cpu_warning_percent: float = 70.0
    cpu_critical_percent: float = 90.0
    disk_warning_percent: float = 80.0
    disk_critical_percent: float = 95.0
    response_time_warning_ms: float = 1000.0
    response_time_critical_ms: float = 3000.0


class KiroPerformanceMonitor(IPerformanceMonitor):
    """
    Kiro Performance Monitor for real-time system monitoring

    Features:
    - Real-time memory and CPU monitoring
    - AI component health tracking
    - Performance alerting with configurable thresholds
    - Resource usage optimization recommendations
    - Historical performance data collection
    """

    def __init__(self,
                 config_manager: ConfigManager = None,
                 logger_system: LoggerSystem = None):
        """
        Initialize the performance monitor

        Args:
            config_manager: Configuration manager instance
            logger_system: Logging system instance
        """

        self.config_manager = config_manager
        self.logger_system = logger_system or LoggerSystem()
        self.error_handler = IntegratedErrorHandler(self.logger_system)

        # Monitoring state
        self.is_monitoring = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self.monitoring_lock = threading.RLock()

        # Performance data storage
        self.metrics_history: deque = deque(maxlen=1000)  # Last 1000 measurements
        self.current_metrics: Optional[PerformanceMetrics] = None

        # AI component tracking
        self.ai_components: Dict[AIComponent, Dict[str, Any]] = {
            AIComponent.COPILOT: {"status": "unknown", "last_check": None, "response_times": deque(maxlen=100)},
            AIComponent.CURSOR: {"status": "unknown", "last_check": None, "response_times": deque(maxlen=100)},
            AIComponent.KIRO: {"status": "active", "last_check": datetime.now(), "response_times": deque(maxlen=100)}
        }

        # Alert system
        self.alert_handlers: List[Callable[[PerformanceAlert], None]] = []
        self.alert_history: deque = deque(maxlen=200)
        self.alert_suppression: Dict[str, datetime] = {}  # Suppress duplicate alerts

        # Thresholds
        self.thresholds = ResourceThresholds()
        self._load_thresholds_from_config()

        # Real-time monitoring
        self.monitoring_interval = 2.0  # seconds
        self.alert_cooldown_duration = 60.0  # seconds between same alerts

        # Performance optimization integration
        self.optimizer: Optional['PerformanceOptimizer'] = None
        self.recent_alerts: deque = deque(maxlen=100)
        self.alert_cooldown: Dict[str, datetime] = {}  # Prevent alert spam

        # System info
        self.process = psutil.Process(os.getpid())
        self.system_info = self._get_system_info()

        # Monitoring intervals
        self.health_check_interval = 10.0  # seconds
        self.last_health_check = datetime.now()

        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "performance_monitor_init",
            "Kiro Performance Monitor initialized"
        )

    def _load_thresholds_from_config(self):
        """Load performance thresholds from configuration"""

        if not self.config_manager:
            return

        try:
            # Load thresholds from config
            perf_config = self.config_manager.get_setting("performance", {})

            # Ensure we have a dict and not some other type
            if not isinstance(perf_config, dict):
                perf_config = {}

            # Set thresholds with type checking
            memory_warning = perf_config.get("memory_warning_mb", 400.0)
            if isinstance(memory_warning, (int, float)):
                self.thresholds.memory_warning_mb = float(memory_warning)

            memory_critical = perf_config.get("memory_critical_mb", 600.0)
            if isinstance(memory_critical, (int, float)):
                self.thresholds.memory_critical_mb = float(memory_critical)

            cpu_warning = perf_config.get("cpu_warning_percent", 70.0)
            if isinstance(cpu_warning, (int, float)):
                self.thresholds.cpu_warning_percent = float(cpu_warning)

            cpu_critical = perf_config.get("cpu_critical_percent", 90.0)
            if isinstance(cpu_critical, (int, float)):
                self.thresholds.cpu_critical_percent = float(cpu_critical)

            # Load monitoring intervals with type checking
            monitoring_interval = perf_config.get("monitoring_interval", 2.0)
            if isinstance(monitoring_interval, (int, float)):
                self.monitoring_interval = float(monitoring_interval)

            health_check_interval = perf_config.get("health_check_interval", 10.0)
            if isinstance(health_check_interval, (int, float)):
                self.health_check_interval = float(health_check_interval)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "load_thresholds"},
                AIComponent.KIRO
            )

    def _get_system_info(self) -> Dict[str, Any]:
        """Get basic system information"""

        try:
            return {
                "cpu_count": psutil.cpu_count(),
                "cpu_count_logical": psutil.cpu_count(logical=True),
                "memory_total": psutil.virtual_memory().total,
                "platform": os.name,
                "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
                "process_id": os.getpid()
            }
        except Exception as e:
            self.logger_system.log_error(
                AIComponent.KIRO,
                e,
                "system_info_collection",
                {}
            )
            return {}

    # IPerformanceMonitor implementation

    def start_monitoring(self) -> None:
        """Start performance monitoring"""

        with self.monitoring_lock:
            if self.is_monitoring:
                return

            self.is_monitoring = True

            # Start monitoring thread
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                name="KiroPerformanceMonitor",
                daemon=True
            )
            self.monitoring_thread.start()

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "monitoring_start",
                "Performance monitoring started"
            )

    def stop_monitoring(self) -> None:
        """Stop performance monitoring"""

        with self.monitoring_lock:
            if not self.is_monitoring:
                return

            self.is_monitoring = False

            # Wait for monitoring thread to finish
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5.0)

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "monitoring_stop",
                "Performance monitoring stopped"
            )

    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage statistics"""

        try:
            # Process memory
            process_memory = self.process.memory_info()

            # System memory
            system_memory = psutil.virtual_memory()

            return {
                "process_rss_mb": process_memory.rss / 1024 / 1024,
                "process_vms_mb": process_memory.vms / 1024 / 1024,
                "system_total_mb": system_memory.total / 1024 / 1024,
                "system_available_mb": system_memory.available / 1024 / 1024,
                "system_used_percent": system_memory.percent,
                "process_percent": self.process.memory_percent()
            }

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "memory_usage_collection"},
                AIComponent.KIRO
            )
            return {}

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""

        try:
            # Current metrics
            if self.current_metrics:
                metrics_dict = {
                    "timestamp": self.current_metrics.timestamp.isoformat(),
                    "memory_usage_mb": self.current_metrics.memory_usage_mb,
                    "memory_peak_mb": self.current_metrics.memory_peak_mb,
                    "memory_available_mb": self.current_metrics.memory_available_mb,
                    "cpu_usage_percent": self.current_metrics.cpu_usage_percent,
                    "cpu_cores": self.current_metrics.cpu_cores,
                    "images_loaded": self.current_metrics.images_loaded,
                    "thumbnails_generated": self.current_metrics.thumbnails_generated,
                    "maps_rendered": self.current_metrics.maps_rendered,
                    "cache_hits": self.current_metrics.cache_hits,
                    "cache_misses": self.current_metrics.cache_misses,
                    "cache_hit_ratio": self.current_metrics.cache_hit_ratio,
                    "copilot_operations": self.current_metrics.copilot_operations,
                    "cursor_operations": self.current_metrics.cursor_operations,
                    "kiro_operations": self.current_metrics.kiro_operations,
                    "total_operations": self.current_metrics.total_operations,
                    "avg_image_load_time": self.current_metrics.avg_image_load_time,
                    "avg_thumbnail_time": self.current_metrics.avg_thumbnail_time,
                    "avg_exif_parse_time": self.current_metrics.avg_exif_parse_time,
                    "avg_map_render_time": self.current_metrics.avg_map_render_time
                }
            else:
                metrics_dict = {"status": "no_data"}

            # Add system info
            metrics_dict.update({
                "system_info": self.system_info,
                "monitoring_active": self.is_monitoring,
                "metrics_history_count": len(self.metrics_history),
                "recent_alerts_count": len(self.recent_alerts)
            })

            return metrics_dict

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "performance_metrics_collection"},
                AIComponent.KIRO
            )
            return {"status": "error"}

    def log_operation_time(self, operation: str, duration: float) -> None:
        """Log the duration of an operation"""

        try:
            # Determine which AI component performed the operation
            component = AIComponent.KIRO  # Default

            if "image" in operation.lower() or "exif" in operation.lower():
                component = AIComponent.COPILOT
            elif "ui" in operation.lower() or "theme" in operation.lower():
                component = AIComponent.CURSOR

            # Update component response times
            if component in self.ai_components:
                self.ai_components[component]["response_times"].append(duration)
                self.ai_components[component]["last_check"] = datetime.now()

            # Log performance
            self.logger_system.log_performance(
                component,
                operation,
                {
                    "duration": duration,
                    "timestamp": datetime.now().isoformat()
                }
            )

            # Check for performance alerts
            self._check_response_time_alert(operation, duration, component)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "operation_time_logging", "op_name": operation},
                AIComponent.KIRO
            )

    def get_ai_component_status(self) -> Dict[str, str]:
        """Get status of all AI components"""

        try:
            status_dict = {}

            for component, info in self.ai_components.items():
                last_check = info.get("last_check")

                if last_check:
                    time_since_check = datetime.now() - last_check

                    if time_since_check < timedelta(seconds=30):
                        status = "active"
                    elif time_since_check < timedelta(minutes=5):
                        status = "idle"
                    else:
                        status = "inactive"
                else:
                    status = "unknown"

                status_dict[component.value] = status

            return status_dict

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "ai_component_status"},
                AIComponent.KIRO
            )
            return {}

    # Monitoring loop

    def _monitoring_loop(self):
        """Main monitoring loop (runs in separate thread)"""

        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "monitoring_loop_start",
            "Performance monitoring loop started"
        )

        while self.is_monitoring:
            try:
                # Collect current metrics
                self._collect_metrics()

                # Perform health checks periodically
                if (datetime.now() - self.last_health_check).total_seconds() >= self.health_check_interval:
                    self._perform_health_checks()
                    self.last_health_check = datetime.now()

                # Sleep until next monitoring cycle
                time.sleep(self.monitoring_interval)

            except Exception as e:
                self.error_handler.handle_error(
                    e, ErrorCategory.INTEGRATION_ERROR,
                    {"operation": "monitoring_loop"},
                    AIComponent.KIRO
                )
                time.sleep(self.monitoring_interval)  # Continue monitoring despite errors

        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "monitoring_loop_end",
            "Performance monitoring loop ended"
        )

    def _collect_metrics(self):
        """Collect current performance metrics"""

        try:
            # Memory metrics
            memory_info = self.get_memory_usage()

            # CPU metrics
            cpu_percent = self.process.cpu_percent()

            # Create performance metrics object
            metrics = PerformanceMetrics(
                timestamp=datetime.now(),
                memory_usage_mb=memory_info.get("process_rss_mb", 0.0),
                memory_peak_mb=memory_info.get("process_rss_mb", 0.0),  # TODO: Track actual peak
                memory_available_mb=memory_info.get("system_available_mb", 0.0),
                cpu_usage_percent=cpu_percent,
                cpu_cores=self.system_info.get("cpu_count", 1)
            )

            # Calculate average response times
            for component, info in self.ai_components.items():
                response_times = info.get("response_times", deque())
                if response_times:
                    avg_time = sum(response_times) / len(response_times) * 1000  # Convert to ms

                    if component == AIComponent.COPILOT:
                        metrics.avg_image_load_time = avg_time
                        metrics.avg_exif_parse_time = avg_time
                    elif component == AIComponent.CURSOR:
                        metrics.avg_thumbnail_time = avg_time

            # Store current metrics
            self.current_metrics = metrics
            self.metrics_history.append(metrics)

            # Check for alerts
            self._check_resource_alerts(metrics)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "metrics_collection"},
                AIComponent.KIRO
            )

    def _perform_health_checks(self):
        """Perform health checks on AI components"""

        try:
            for component in self.ai_components:
                # Update component status based on recent activity
                last_check = self.ai_components[component].get("last_check")

                if last_check:
                    time_since_check = datetime.now() - last_check

                    if time_since_check < timedelta(seconds=30):
                        self.ai_components[component]["status"] = "active"
                    elif time_since_check < timedelta(minutes=5):
                        self.ai_components[component]["status"] = "idle"
                    else:
                        self.ai_components[component]["status"] = "inactive"
                else:
                    self.ai_components[component]["status"] = "unknown"

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "health_check",
                f"Health check completed: {self.get_ai_component_status()}"
            )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "health_checks"},
                AIComponent.KIRO
            )

    # Alert system

    def _check_resource_alerts(self, metrics: PerformanceMetrics):
        """Check for resource usage alerts"""

        # Memory alerts
        if metrics.memory_usage_mb > self.thresholds.memory_critical_mb:
            self._create_alert("critical", "High memory usage", AIComponent.KIRO,
                             "memory_usage", metrics.memory_usage_mb, self.thresholds.memory_critical_mb)
        elif metrics.memory_usage_mb > self.thresholds.memory_warning_mb:
            self._create_alert("warning", "Elevated memory usage", AIComponent.KIRO,
                             "memory_usage", metrics.memory_usage_mb, self.thresholds.memory_warning_mb)

        # CPU alerts
        if metrics.cpu_usage_percent > self.thresholds.cpu_critical_percent:
            self._create_alert("critical", "High CPU usage", AIComponent.KIRO,
                             "cpu_usage", metrics.cpu_usage_percent, self.thresholds.cpu_critical_percent)
        elif metrics.cpu_usage_percent > self.thresholds.cpu_warning_percent:
            self._create_alert("warning", "Elevated CPU usage", AIComponent.KIRO,
                             "cpu_usage", metrics.cpu_usage_percent, self.thresholds.cpu_warning_percent)

    def _check_response_time_alert(self, operation: str, duration: float, component: AIComponent):
        """Check for response time alerts"""

        duration_ms = duration * 1000  # Convert to milliseconds

        if duration_ms > self.thresholds.response_time_critical_ms:
            self._create_alert("critical", f"Slow operation: {operation}", component,
                             "response_time", duration_ms, self.thresholds.response_time_critical_ms)
        elif duration_ms > self.thresholds.response_time_warning_ms:
            self._create_alert("warning", f"Slow operation: {operation}", component,
                             "response_time", duration_ms, self.thresholds.response_time_warning_ms)

    def _create_alert(self, level: str, message: str, component: AIComponent,
                     metric_name: str, current_value: float, threshold: float):
        """Create and process a performance alert"""

        try:
            # Check cooldown to prevent alert spam
            alert_key = f"{component.value}_{metric_name}_{level}"
            now = datetime.now()

            if alert_key in self.alert_cooldown:
                if (now - self.alert_cooldown[alert_key]).total_seconds() < 60:  # 1 minute cooldown
                    return

            # Create alert
            alert = PerformanceAlert(
                level=level,
                message=message,
                component=component,
                metric_name=metric_name,
                current_value=current_value,
                threshold=threshold,
                timestamp=now
            )

            # Store alert
            self.recent_alerts.append(alert)
            self.alert_cooldown[alert_key] = now

            # Log alert
            self.logger_system.log_ai_operation(
                component,
                f"performance_alert_{level}",
                f"{message}: {current_value:.2f} (threshold: {threshold:.2f})"
            )

            # Notify alert handlers
            for handler in self.alert_handlers:
                try:
                    handler(alert)
                except Exception as e:
                    self.logger_system.log_error(
                        AIComponent.KIRO,
                        e,
                        "alert_handler_error",
                        {"alert_level": level, "message": message}
                    )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "alert_creation", "level": level},
                AIComponent.KIRO
            )

    # Alert handler management

    def add_alert_handler(self, handler: Callable[[PerformanceAlert], None]):
        """Add an alert handler"""
        if handler not in self.alert_handlers:
            self.alert_handlers.append(handler)

    def remove_alert_handler(self, handler: Callable[[PerformanceAlert], None]):
        """Remove an alert handler"""
        if handler in self.alert_handlers:
            self.alert_handlers.remove(handler)

    # Utility methods

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of performance data"""

        try:
            if not self.metrics_history:
                return {"status": "no_data"}

            # Calculate averages from recent history
            recent_metrics = list(self.metrics_history)[-10:]  # Last 10 measurements

            avg_memory = sum(m.memory_usage_mb for m in recent_metrics) / len(recent_metrics)
            avg_cpu = sum(m.cpu_usage_percent for m in recent_metrics) / len(recent_metrics)

            # Component status
            component_status = self.get_ai_component_status()

            return {
                "status": "active" if self.is_monitoring else "inactive",
                "average_memory_mb": avg_memory,
                "average_cpu_percent": avg_cpu,
                "component_status": component_status,
                "recent_alerts": len([a for a in self.recent_alerts if (datetime.now() - a.timestamp).total_seconds() < 300]),  # Last 5 minutes
                "metrics_collected": len(self.metrics_history),
                "system_info": self.system_info
            }

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "performance_summary"},
                AIComponent.KIRO
            )
            return {"status": "error"}

    def get_recent_alerts(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """Get recent alerts within specified time window"""

        try:
            cutoff_time = datetime.now() - timedelta(minutes=minutes)

            recent_alerts = [
                {
                    "level": alert.level,
                    "message": alert.message,
                    "component": alert.component.value,
                    "metric_name": alert.metric_name,
                    "current_value": alert.current_value,
                    "threshold": alert.threshold,
                    "timestamp": alert.timestamp.isoformat()
                }
                for alert in self.recent_alerts
                if alert.timestamp >= cutoff_time
            ]

            return recent_alerts

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "recent_alerts", "minutes": minutes},
                AIComponent.KIRO
            )
            return []

    def clear_alerts(self):
        """Clear all stored alerts"""
        self.recent_alerts.clear()
        self.alert_cooldown.clear()

    def update_thresholds(self, new_thresholds: Dict[str, float]):
        """Update performance thresholds"""

        try:
            for key, value in new_thresholds.items():
                if hasattr(self.thresholds, key):
                    setattr(self.thresholds, key, value)

            # Save to configuration
            if self.config_manager:
                threshold_dict = {
                    "memory_warning_mb": self.thresholds.memory_warning_mb,
                    "memory_critical_mb": self.thresholds.memory_critical_mb,
                    "cpu_warning_percent": self.thresholds.cpu_warning_percent,
                    "cpu_critical_percent": self.thresholds.cpu_critical_percent,
                    "response_time_warning_ms": self.thresholds.response_time_warning_ms,
                    "response_time_critical_ms": self.thresholds.response_time_critical_ms
                }

                self.config_manager.set_setting("performance.thresholds", threshold_dict)

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "thresholds_update",
                f"Performance thresholds updated: {new_thresholds}"
            )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.CONFIGURATION_ERROR,
                {"operation": "threshold_update", "thresholds": str(new_thresholds)},
                AIComponent.KIRO
            )

    def shutdown(self):
        """Shutdown the performance monitor"""

        try:
            # Stop monitoring
            self.stop_monitoring()

            # Clear data
            self.metrics_history.clear()
            self.recent_alerts.clear()
            self.alert_cooldown.clear()
            self.alert_handlers.clear()

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "performance_monitor_shutdown",
                "Performance monitor shutdown complete"
            )

        except Exception as e:
            self.logger_system.log_error(
                AIComponent.KIRO,
                e,
                "performance_monitor_shutdown",
                {}
            )
    def _load_thresholds_from_config(self):
        """Load performance thresholds from configuration"""
        try:
            if self.config_manager:
                self.thresholds.memory_warning_mb = self.config_manager.get_setting(
                    "performance.memory_warning_mb", 400.0
                )
                self.thresholds.memory_critical_mb = self.config_manager.get_setting(
                    "performance.memory_critical_mb", 600.0
                )
                self.thresholds.cpu_warning_percent = self.config_manager.get_setting(
                    "performance.cpu_warning_percent", 70.0
                )
                self.thresholds.cpu_critical_percent = self.config_manager.get_setting(
                    "performance.cpu_critical_percent", 90.0
                )
                self.thresholds.response_time_warning_ms = self.config_manager.get_setting(
                    "performance.response_time_warning_ms", 1000.0
                )
                self.thresholds.response_time_critical_ms = self.config_manager.get_setting(
                    "performance.response_time_critical_ms", 3000.0
 )
        except Exception as e:
            self.logger_system.error(f"Failed to load thresholds from config: {e}")

    def set_optimizer(self, optimizer: 'PerformanceOptimizer'):
        """Set performance optimizer for integration"""
        self.optimizer = optimizer

    def start_monitoring(self):
        """Start performance monitoring"""
        try:
            with self.monitoring_lock:
                if self.is_monitoring:
                    return

                self.is_monitoring = True
                self.monitoring_thread = threading.Thread(
                    target=self._monitoring_loop,
                    name="performance_monitor",
                    daemon=True
                )
                self.monitoring_thread.start()

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "monitoring_started",
                "Performance monitoring started"
            )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "start_monitoring"},
                AIComponent.KIRO
            )

    def stop_monitoring(self):
        """Stop performance monitoring"""
        try:
            with self.monitoring_lock:
                self.is_monitoring = False

            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5.0)

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "monitoring_stopped",
                "Performance monitoring stopped"
            )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "stop_monitoring"},
                AIComponent.KIRO
            )

    def _monitoring_loop(self):
        """Enhanced monitoring loop with real-time alerting"""
        while self.is_monitoring:
            try:
                # Collect current metrics
                metrics = self._collect_enhanced_metrics()

                if metrics:
                    # Store metrics
                    self.current_metrics = metrics
                    self.metrics_history.append(metrics)

                    # Check for alerts
                    self._check_performance_alerts(metrics)

                    # Update AI component status
                    self._update_ai_component_status()

                # Sleep until next check
                time.sleep(self.monitoring_interval)

            except Exception as e:
                self.error_handler.handle_error(
                    e, ErrorCategory.INTEGRATION_ERROR,
                    {"operation": "monitoring_loop"},
                    AIComponent.KIRO
                )
                time.sleep(5.0)  # Longer sleep on error

    def _collect_enhanced_metrics(self) -> Optional[PerformanceMetrics]:
        """Collect enhanced performance metrics"""
        try:
            process = psutil.Process()
            system_memory = psutil.virtual_memory()

            # Memory metrics
            memory_info = process.memory_info()
            memory_usage_mb = memory_info.rss / 1024 / 1024
            memory_peak_mb = getattr(memory_info, 'peak_wset', memory_info.rss) / 1024 / 1024
            memory_available_mb = system_memory.available / 1024 / 1024

            # CPU metrics
            cpu_usage_percent = process.cpu_percent()
            cpu_cores = psutil.cpu_count()

            # Application metrics (would be updated by other components)
            images_loaded = 0
            thumbnails_generated = 0
            maps_rendered = 0
            cache_hits = 0
            cache_misses = 0

            # AI component metrics
            copilot_operations = len(self.ai_components[AIComponent.COPILOT]["response_times"])
            cursor_operations = len(self.ai_components[AIComponent.CURSOR]["response_times"])
            kiro_operations = len(self.ai_components[AIComponent.KIRO]["response_times"])

            # Response times (averages)
            avg_image_load_time = self._calculate_average_response_time(AIComponent.COPILOT)
            avg_thumbnail_time = self._calculate_average_response_time(AIComponent.CURSOR)
            avg_exif_parse_time = self._calculate_average_response_time(AIComponent.COPILOT)
            avg_map_render_time = self._calculate_average_response_time(AIComponent.COPILOT)

            return PerformanceMetrics(
                memory_usage_mb=memory_usage_mb,
                memory_peak_mb=memory_peak_mb,
                memory_available_mb=memory_available_mb,
                cpu_usage_percent=cpu_usage_percent,
                cpu_cores=cpu_cores,
                images_loaded=images_loaded,
                thumbnails_generated=thumbnails_generated,
                maps_rendered=maps_rendered,
                cache_hits=cache_hits,
                cache_misses=cache_misses,
                copilot_operations=copilot_operations,
                cursor_operations=cursor_operations,
                kiro_operations=kiro_operations,
                avg_image_load_time=avg_image_load_time,
                avg_thumbnail_time=avg_thumbnail_time,
                avg_exif_parse_time=avg_exif_parse_time,
                avg_map_render_time=avg_map_render_time
            )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "collect_enhanced_metrics"},
                AIComponent.KIRO
            )
            return None

    def _calculate_average_response_time(self, component: AIComponent) -> float:
        """Calculate average response time for AI component"""
        try:
            response_times = self.ai_components[component]["response_times"]
            if response_times:
                return sum(response_times) / len(response_times)
            return 0.0
        except Exception:
            return 0.0

    def _check_performance_alerts(self, metrics: PerformanceMetrics):
        """Check for performance alerts with enhanced logic"""
        try:
            current_time = datetime.now()

            # Memory alerts
            if metrics.memory_usage_mb > self.thresholds.memory_critical_mb:
                self._emit_performance_alert("critical", "Memory usage critical", AIComponent.KIRO,
                               "memory_usage", metrics.memory_usage_mb, self.thresholds.memory_critical_mb)
            elif metrics.memory_usage_mb > self.thresholds.memory_warning_mb:
                self._emit_performance_alert("warning", "Memory usage high", AIComponent.KIRO,
                               "memory_usage", metrics.memory_usage_mb, self.thresholds.memory_warning_mb)

            # CPU alerts
            if metrics.cpu_usage_percent > self.thresholds.cpu_critical_percent:
                self._emit_performance_alert("critical", "CPU usage critical", AIComponent.KIRO,
                               "cpu_usage", metrics.cpu_usage_percent, self.thresholds.cpu_critical_percent)
            elif metrics.cpu_usage_percent > self.thresholds.cpu_warning_percent:
                self._emit_performance_alert("warning", "CPU usage high", AIComponent.KIRO,
                               "cpu_usage", metrics.cpu_usage_percent, self.thresholds.cpu_warning_percent)

            # Response time alerts
            if metrics.avg_image_load_time > self.thresholds.response_time_critical_ms:
                self._emit_performance_alert("critical", "Image loading very slow", AIComponent.COPILOT,
                               "response_time", metrics.avg_image_load_time, self.thresholds.response_time_critical_ms)
            elif metrics.avg_image_load_time > self.thresholds.response_time_warning_ms:
                self._emit_performance_alert("warning", "Image loading slow", AIComponent.COPILOT,
                               "response_time", metrics.avg_image_load_time, self.thresholds.response_time_warning_ms)

            # Cache performance alerts
            cache_hit_ratio = metrics.cache_hit_ratio
            if cache_hit_ratio < 0.5:  # Less than 50%
                self._emit_performance_alert("warning", "Low cache hit ratio", AIComponent.KIRO,
                               "cache_hit_ratio", cache_hit_ratio, 0.5)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "check_performance_alerts"},
                AIComponent.KIRO
            )

    def _emit_performance_alert(self, level: str, message: str, component: AIComponent,
                   metric_name: str, current_value: float, threshold: float):
        """Emit performance alert with enhanced suppression and optimization triggers"""
        try:
            # Create alert key for suppression
            alert_key = f"{component.value}_{metric_name}_{level}"
            current_time = datetime.now()

            # Check if alert is suppressed
            if alert_key in self.alert_cooldown:
                last_alert_time = self.alert_cooldown[alert_key]
                if (current_time - last_alert_time).total_seconds() < 60.0:  # 60 second cooldown
                    return  # Suppress duplicate alert

            # Create alert
            alert = PerformanceAlert(
                level=level,
                message=message,
                component=component,
                metric_name=metric_name,
                current_value=current_value,
                threshold=threshold,
                timestamp=current_time
            )

            # Store alert
            self.recent_alerts.append(alert)
            self.alert_cooldown[alert_key] = current_time

            # Notify handlers
            for handler in self.alert_handlers:
                try:
                    handler(alert)
                except Exception as e:
                    self.logger_system.error(f"Alert handler failed: {e}")

            # Log alert
            self.logger_system.log_ai_operation(
                component,
                "performance_alert",
                f"[{level.upper()}] {message}: {current_value:.2f} (threshold: {threshold:.2f})"
            )

            # Trigger optimization if available
            if self.optimizer and level == "critical":
                self._trigger_emergency_optimization(metric_name, current_value)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "emit_performance_alert", "level": level, "message": message},
                AIComponent.KIRO
            )

    def _trigger_emergency_optimization(self, metric_name: str, current_value: float):
        """Trigger emergency optimization for critical alerts"""
        try:
            if not self.optimizer:
                return

            if metric_name == "memory_usage":
                # Force aggressive memory cleanup
                self.optimizer._optimize_memory_usage()

                # Clear more cache if still critical
                if current_value > self.thresholds.memory_critical_mb * 1.1:
                    self.optimizer.cache_system.clear_lru(0.5)  # Clear 50%

            elif metric_name == "cpu_usage":
                # Reduce processing load
                self.optimizer._optimize_cpu_usage()

            elif metric_name == "response_time":
                # Optimize processing pipeline
                self.optimizer._optimize_cache_performance()

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "trigger_emergency_optimization", "metric": metric_name},
                AIComponent.KIRO
            )

    def _update_ai_component_status(self):
        """Update AI component status based on performance"""
        try:
            current_time = datetime.now()

            for component in self.ai_components:
                component_data = self.ai_components[component]

                # Update last check time
                component_data["last_check"] = current_time

                # Determine status based on response times and alerts
                response_times = component_data["response_times"]
                if response_times:
                    avg_response = sum(response_times) / len(response_times)

                    if avg_response > self.thresholds.response_time_critical_ms:
                        component_data["status"] = "critical"
                    elif avg_response > self.thresholds.response_time_warning_ms:
                        component_data["status"] = "warning"
                    else:
                        component_data["status"] = "active"
                else:
                    component_data["status"] = "idle"

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "update_ai_component_status"},
                AIComponent.KIRO
            )

    # Enhanced public API methods

    def add_alert_handler(self, handler: Callable[[PerformanceAlert], None]):
        """Add alert handler"""
        if handler not in self.alert_handlers:
            self.alert_handlers.append(handler)

    def remove_alert_handler(self, handler: Callable[[PerformanceAlert], None]):
        """Remove alert handler"""
        if handler in self.alert_handlers:
            self.alert_handlers.remove(handler)

    def record_operation_time(self, component: AIComponent, operation_time_ms: float):
        """Record operation time for AI component"""
        try:
            if component in self.ai_components:
                self.ai_components[component]["response_times"].append(operation_time_ms)
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "record_operation_time", "component": component.value},
                AIComponent.KIRO
            )

    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """Get current performance metrics"""
        return self.current_metrics

    def get_metrics_history(self, limit: int = 100) -> List[PerformanceMetrics]:
        """Get performance metrics history"""
        return list(self.metrics_history)[-limit:]

    def get_ai_component_status(self) -> Dict[AIComponent, Dict[str, Any]]:
        """Get AI component status"""
        return self.ai_components.copy()

    def update_thresholds(self, **kwargs):
        """Update performance thresholds"""
        try:
            for key, value in kwargs.items():
                if hasattr(self.thresholds, key):
                    setattr(self.thresholds, key, value)

                    # Save to configuration
                    if self.config_manager:
                        self.config_manager.set_setting(f"performance.{key}", value)

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "thresholds_updated",
                f"Performance thresholds updated: {list(kwargs.keys())}"
            )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "update_thresholds"},
                AIComponent.KIRO
            )

    def cleanup(self):
        """Cleanup monitor resources"""
        try:
            # Stop monitoring
            self.stop_monitoring()

            # Clear data
            self.metrics_history.clear()
            self.recent_alerts.clear()
            self.alert_handlers.clear()

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "performance_monitor_cleanup",
                "Performance monitor cleaned up"
            )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "cleanup"},
                AIComponent.KIRO
            )
