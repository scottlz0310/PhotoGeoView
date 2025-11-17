"""
Unified Logging System for AI Integration

Provides centralized logging that coordinates between:
- GitHub Copilot (CS4Coding): Detailed technical logging
- Cursor (CursorBLD): User-friendly operation logging
- Kiro: Integration monitoring and performance logging

Author: Kiro AI Integration System
"""

import json
import logging
import logging.handlers
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from .models import AIComponent, PerformanceMetrics


class LogLevel(Enum):
    """Extended log levels for AI integration"""

    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"
    PERFORMANCE = "PERFORMANCE"  # Custom level for performance metrics
    AI_OPERATION = "AI_OPERATION"  # Custom level for AI operations


class AILogFormatter(logging.Formatter):
    """Custom formatter for AI integration logging"""

    def __init__(self):
        super().__init__()
        self.format_string = "%(asctime)s | %(levelname)-12s | %(ai_component)-8s | %(name)-20s | %(message)s"

    def format(self, record):
        """Format log record with AI component information"""

        # Add AI component if not present
        if not hasattr(record, "ai_component"):
            record.ai_component = "SYSTEM"

        # Add operation context if available
        if hasattr(record, "operation"):
            record.message = f"[{record.operation}] {record.getMessage()}"
        else:
            record.message = record.getMessage()

        # Use custom format
        formatter = logging.Formatter(self.format_string)
        return formatter.format(record)


class PerformanceLogHandler(logging.Handler):
    """Custom handler for performance metrics logging"""

    def __init__(self, metrics_file: Path):
        super().__init__()
        self.metrics_file = metrics_file
        self.metrics_buffer: list[dict[str, Any]] = []
        self.buffer_size = 100

    def emit(self, record):
        """Emit performance log record"""

        if hasattr(record, "performance_data"):
            metric_entry = {
                "timestamp": datetime.now().isoformat(),
                "level": record.levelname,
                "ai_component": getattr(record, "ai_component", "SYSTEM"),
                "operation": getattr(record, "operation", "unknown"),
                "metrics": record.performance_data,
            }

            self.metrics_buffer.append(metric_entry)

            # Flush buffer when full
            if len(self.metrics_buffer) >= self.buffer_size:
                self.flush_metrics()

    def flush_metrics(self):
        """Flush metrics buffer to file"""

        if not self.metrics_buffer:
            return

        try:
            # Ensure directory exists
            self.metrics_file.parent.mkdir(parents=True, exist_ok=True)

            # Append metrics to file
            with open(self.metrics_file, "a", encoding="utf-8") as f:
                for metric in self.metrics_buffer:
                    f.write(json.dumps(metric) + "\n")

            self.metrics_buffer.clear()

        except Exception as e:
            # Fallback to stderr if file writing fails
            print(f"Failed to write performance metrics: {e}", file=sys.stderr)


class LoggerSystem:
    """
    Unified logging system that coordinates logging across all AI implementations
    """

    def __init__(
        self,
        log_dir: Path | None = None,
        log_level: str = "INFO",
        enable_performance_logging: bool = True,
        enable_ai_operation_logging: bool = True,
    ):
        """
        Initialize the unified logging system

        Args:
            log_dir: Directory for log files
            log_level: Default logging level
            enable_performance_logging: Enable performance metrics logging
            enable_ai_operation_logging: Enable AI operation logging
        """

        self.log_dir = log_dir or Path("logs")
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.enable_performance_logging = enable_performance_logging
        self.enable_ai_operation_logging = enable_ai_operation_logging

        # Create log directory
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Initialize loggers
        self.loggers: dict[str, logging.Logger] = {}
        self.performance_handler: PerformanceLogHandler | None = None

        # Setup logging system
        self._setup_logging()

        # Performance tracking
        self.operation_counts: dict[str, int] = {}
        self.performance_history: list[PerformanceMetrics] = []

        # AI component loggers
        self.ai_loggers = {
            AIComponent.COPILOT: self.get_logger("copilot"),
            AIComponent.CURSOR: self.get_logger("cursor"),
            AIComponent.KIRO: self.get_logger("kiro"),
        }

    def _setup_logging(self):
        """Setup the logging configuration"""

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)

        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Create formatters
        self.formatter = AILogFormatter()

        # Setup console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(self.formatter)
        root_logger.addHandler(console_handler)

        # Setup file handlers
        self._setup_file_handlers()

        # Setup performance logging
        if self.enable_performance_logging:
            self._setup_performance_logging()

    def _setup_file_handlers(self):
        """Setup file-based logging handlers"""

        # Main application log
        main_log_file = self.log_dir / "photogeoview.log"
        main_handler = logging.handlers.RotatingFileHandler(
            main_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        main_handler.setLevel(self.log_level)
        main_handler.setFormatter(self.formatter)
        logging.getLogger().addHandler(main_handler)

        # Error log
        error_log_file = self.log_dir / "errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(self.formatter)
        logging.getLogger().addHandler(error_handler)

        # AI-specific log files
        for ai_component in AIComponent:
            ai_log_file = self.log_dir / f"{ai_component.value}.log"
            ai_handler = logging.handlers.RotatingFileHandler(
                ai_log_file,
                maxBytes=5 * 1024 * 1024,  # 5MB
                backupCount=3,
                encoding="utf-8",
            )
            ai_handler.setLevel(self.log_level)
            ai_handler.setFormatter(self.formatter)

            # Add filter for AI-specific logs
            ai_handler.addFilter(
                lambda record, component=ai_component: getattr(record, "ai_component", None) == component.value.upper()
            )

            logging.getLogger().addHandler(ai_handler)

    def _setup_performance_logging(self):
        """Setup performance metrics logging"""

        metrics_file = self.log_dir / "performance_metrics.jsonl"
        self.performance_handler = PerformanceLogHandler(metrics_file)
        self.performance_handler.setLevel(logging.INFO)

        # Create performance logger
        perf_logger = logging.getLogger("performance")
        perf_logger.addHandler(self.performance_handler)
        perf_logger.setLevel(logging.INFO)

    def get_logger(self, name: str) -> logging.Logger:
        """
        Get or create a logger with the specified name

        Args:
            name: Logger name

        Returns:
            Logger instance
        """

        if name not in self.loggers:
            logger = logging.getLogger(name)
            logger.setLevel(self.log_level)
            self.loggers[name] = logger

        return self.loggers[name]

    def log_ai_operation(
        self,
        ai_component: AIComponent,
        operation: str,
        message: str,
        level: str = "INFO",
        **kwargs,
    ):
        """
        Log an AI operation with component attribution

        Args:
            ai_component: AI component performing the operation
            operation: Operation being performed
            message: Log message
            level: Log level
            **kwargs: Additional context
        """

        if not self.enable_ai_operation_logging:
            return

        logger = self.ai_loggers[ai_component]
        log_level = getattr(logging, level.upper(), logging.INFO)

        # Create log record with AI context
        extra = {
            "ai_component": ai_component.value.upper(),
            "operation": operation,
            **kwargs,
        }

        logger.log(log_level, message, extra=extra)

        # Update operation counts
        op_key = f"{ai_component.value}_{operation}"
        self.operation_counts[op_key] = self.operation_counts.get(op_key, 0) + 1

    def log_performance(self, ai_component: AIComponent, operation: str, metrics: dict[str, Any]):
        """
        Log performance metrics

        Args:
            ai_component: AI component
            operation: Operation being measured
            metrics: Performance metrics dictionary
        """

        if not self.enable_performance_logging or not self.performance_handler:
            return

        perf_logger = logging.getLogger("performance")

        extra = {
            "ai_component": ai_component.value.upper(),
            "operation": operation,
            "performance_data": metrics,
        }

        perf_logger.info(f"Performance metrics for {operation=}", extra=extra)

    def log_error(
        self,
        ai_component: AIComponent,
        error: Exception,
        operation: str = "",
        context: dict[str, Any] | None = None,
    ):
        """
        Log an error with AI component context

        Args:
            ai_component: AI component where error occurred
            error: Exception that occurred
            operation: Operation during which error occurred
            context: Additional context information
        """

        logger = self.ai_loggers[ai_component]

        extra = {
            "ai_component": ai_component.value.upper(),
            "operation": operation,
            "error_type": type(error).__name__,
            **(context or {}),
        }

        logger.error(f"Error in {operation}: {error!s}", extra=extra, exc_info=True)

    def log_integration_event(self, event: str, components: list[AIComponent], details: dict[str, Any] | None = None):
        """
        Log an integration event involving multiple AI components

        Args:
            event: Integration event description
            components: List of AI components involved
            details: Additional event details
        """

        kiro_logger = self.ai_loggers[AIComponent.KIRO]

        component_names = [comp.value for comp in components]

        extra = {
            "ai_component": "KIRO",
            "operation": "integration",
            "involved_components": component_names,
            **(details or {}),
        }

        kiro_logger.info(
            f"Integration event: {event} (Components: {', '.join(component_names)})",
            extra=extra,
        )

    def create_performance_metrics(self) -> PerformanceMetrics:
        """
        Create current performance metrics snapshot

        Returns:
            PerformanceMetrics instance
        """

        import os

        import psutil

        # Get system metrics
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()

        metrics = PerformanceMetrics(
            memory_usage_mb=memory_info.rss / 1024 / 1024,
            memory_peak_mb=(memory_info.peak_wss / 1024 / 1024 if hasattr(memory_info, "peak_wss") else 0),
            memory_available_mb=psutil.virtual_memory().available / 1024 / 1024,
            cpu_usage_percent=process.cpu_percent(),
            cpu_cores=psutil.cpu_count(),
            copilot_operations=self.operation_counts.get("copilot_total", 0),
            cursor_operations=self.operation_counts.get("cursor_total", 0),
            kiro_operations=self.operation_counts.get("kiro_total", 0),
        )

        self.performance_history.append(metrics)

        # Keep only last 1000 metrics
        self.performance_history = self.performance_history[-1000:]

        return metrics

    def get_operation_statistics(self) -> dict[str, Any]:
        """
        Get operation statistics

        Returns:
            Dictionary with operation statistics
        """

        total_operations = sum(self.operation_counts.values())

        ai_totals = {
            "copilot": sum(count for op, count in self.operation_counts.items() if op.startswith("copilot_")),
            "cursor": sum(count for op, count in self.operation_counts.items() if op.startswith("cursor_")),
            "kiro": sum(count for op, count in self.operation_counts.items() if op.startswith("kiro_")),
        }

        return {
            "total_operations": total_operations,
            "ai_totals": ai_totals,
            "operation_breakdown": dict(self.operation_counts),
            "most_active_ai": max(ai_totals, key=ai_totals.get) if ai_totals else None,
        }

    def flush_all(self):
        """Flush all log handlers"""

        for handler in logging.getLogger().handlers:
            handler.flush()

        if self.performance_handler:
            self.performance_handler.flush_metrics()

    def info(self, message: str, **kwargs):
        """Log info message"""
        logger = self.get_logger("system")
        logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        logger = self.get_logger("system")
        logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs):
        """Log error message"""
        logger = self.get_logger("system")
        logger.error(message, extra=kwargs)

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        logger = self.get_logger("system")
        logger.debug(message, extra=kwargs)

    def shutdown(self):
        """Shutdown logging system"""

        self.flush_all()

        # Close all handlers
        for handler in logging.getLogger().handlers[:]:
            handler.close()
            logging.getLogger().removeHandler(handler)

        logging.shutdown()

    # Context managers for operation logging

    def operation_context(self, ai_component: AIComponent, operation: str):
        """
        Context manager for logging operation start/end

        Args:
            ai_component: AI component performing operation
            operation: Operation name
        """

        return OperationContext(self, ai_component, operation)


class OperationContext:
    """Context manager for operation logging"""

    def __init__(self, logger_system: LoggerSystem, ai_component: AIComponent, operation: str):
        self.logger_system = logger_system
        self.ai_component = ai_component
        self.operation = operation
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        self.logger_system.log_ai_operation(
            self.ai_component,
            self.operation,
            f"Starting {self.operation}",
            level="DEBUG",
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        if exc_type is None:
            # Operation completed successfully
            self.logger_system.log_ai_operation(
                self.ai_component,
                self.operation,
                f"Completed {self.operation} in {duration:.3f}s",
                level="DEBUG",
            )

            # Log performance metrics
            self.logger_system.log_performance(
                self.ai_component,
                self.operation,
                {"duration_seconds": duration, "status": "success"},
            )
        else:
            # Operation failed
            self.logger_system.log_error(
                self.ai_component,
                exc_val,
                self.operation,
                {"duration_seconds": duration},
            )
