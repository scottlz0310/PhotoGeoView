"""
Integrated Logging System for AI Integration

Provides unified logging across all AI components:
- CursorBLD: UI event logging
- CS4Coding: Core functionality logging
- Kiro: Integration and performance logging

Author: Kiro AI Integration System
"""

import logging
import logging.handlers
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import json
import threading

from .interfaces import ILogger


class IntegratedLogger(ILogger):
    """
    Unified logging implementation that coordinates logging across AI components
    """

    def __init__(self,
                 name: str = "PhotoGeoView_AI_Integration",
                 log_dir: Path = Path("logs"),
                 log_level: int = logging.INFO):
        """
        Initialize integrated logger

        Args:
            name: Logger name
            log_dir: Directory for log files
            log_level: Minimum logging level
        """
        self.name = name
        self.log_dir = log_dir
        self.log_level = log_level

        # Ensure log directory exists
        self.log_dir.mkdir(exist_ok=True)

        # Initialize loggers for different components
        self.main_logger = self._setup_main_logger()
        self.component_loggers = {
            'cursorbld': self._setup_component_logger('cursorbld'),
            'cs4coding': self._setup_component_logger('cs4coding'),
            'kiro': self._setup_component_logger('kiro')
        }

        # Performance logging
        self.performance_logger = self._setup_performance_logger()

        # Error tracking
        self.error_counts = {}
        self._lock = threading.RLock()

        self.info("IntegratedLogger initialized successfully")

    def _setup_main_logger(self) -> logging.Logger:
        """Setup main application logger"""
        logger = logging.getLogger(f"{self.name}.main")
        logger.setLevel(self.log_level)

        # Clear existing handlers
        logger.handlers.clear()

        # File handler for main log
        main_log_file = self.log_dir / "main.log"
        file_handler = logging.handlers.RotatingFileHandler(
            main_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )

        # Console handler
        console_handler = logging.StreamHandler()

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def _setup_component_logger(self, component: str) -> logging.Logger:
        """Setup logger for specific AI component"""
        logger = logging.getLogger(f"{self.name}.{component}")
        logger.setLevel(self.log_level)

        # Clear existing handlers
        logger.handlers.clear()

        # Component-specific log file
        log_file = self.log_dir / f"{component}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )

        # Component-specific formatter
        formatter = logging.Formatter(
            f'%(asctime)s - {component.upper()} - %(levelname)s - %(message)s'
        )

        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger

    def _setup_performance_logger(self) -> logging.Logger:
        """Setup performance metrics logger"""
        logger = logging.getLogger(f"{self.name}.performance")
        logger.setLevel(logging.DEBUG)

        # Clear existing handlers
        logger.handlers.clear()

        # Performance log file
        perf_log_file = self.log_dir / "performance.log"
        file_handler = logging.handlers.RotatingFileHandler(
            perf_log_file,
            maxBytes=20*1024*1024,  # 20MB
            backupCount=3
        )

        # JSON formatter for structured performance data
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

        return logger

    def _get_component_from_extra(self, extra: Optional[Dict[str, Any]]) -> str:
        """Extract component name from extra data"""
        if not e
           return 'main'

        component = extra.get('component', '')

        if 'cursorbld' in component.lower() or 'cursor' in component.lower():
            return 'cursorbld'
        elif 'cs4coding' in component.lower() or 'copilot' in component.lower():
            return 'cs4coding'
        elif 'kiro' in component.lower():
            return 'kiro'
        else:
            return 'main'

    def _log_with_component(self, level: int, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log message with appropriate component logger"""
        with self._lock:
            # Determine component
            component = self._get_component_from_extra(extra)

            # Get appropriate logger
            if component in self.component_loggers:
                logger = self.component_loggers[component]
            else:
                logger = self.main_logger

            # Add session info to extra data
            if extra is None:
                extra = {}

            extra.update({
                'timestamp': datetime.now().isoformat(),
                'component': component,
                'thread': threading.current_thread().name
            })

            # Log the message
            logger.log(level, message, extra=extra)

            # Also log to main logger for centralized view
            if component != 'main':
                self.main_logger.log(level, f"[{component.upper()}] {message}", extra=extra)

    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log debug message"""
        self._log_with_component(logging.DEBUG, message, extra)

    def info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log info message"""
        self._log_with_component(logging.INFO, message, extra)

    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log warning message"""
        self._log_with_component(logging.WARNING, message, extra)

    def error(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log error message"""
        with self._lock:
            # Track error counts
            component = self._get_component_from_extra(extra)
            error_key = f"{component}_errors"
            self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1

        self._log_with_component(logging.ERROR, message, extra)

    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log critical message"""
        with self._lock:
            # Track critical errors
            component = self._get_component_from_extra(extra)
            critical_key = f"{component}_critical"
            self.error_counts[critical_key] = self.error_counts.get(critical_key, 0) + 1

        self._log_with_component(logging.CRITICAL, message, extra)

    def log_performance(self, component: str, operation: str, duration_ms: float,
                       success: bool = True, additional_data: Optional[Dict[str, Any]] = None):
        """
        Log performance metrics

        Args:
            component: AI component name
            operation: Operation performed
            duration_ms: Duration in milliseconds
            success: Whether operation succeeded
            additional_data: Additional performance data
        """
        perf_data = {
            'timestamp': datetime.now().isoformat(),
            'component': component,
            'operation': operation,
            'duration_ms': duration_ms,
            'success': success
        }

        if additional_data:
            perf_data.update(additional_data)

        # Log as JSON for easy parsing
        self.performance_logger.info(json.dumps(perf_data))

    def log_user_action(self, action: str, context: Optional[Dict[str, Any]] = None):
        """
        Log user actions for UX analysis

        Args:
            action: User action performed
            context: Additional context information
        """
        action_data = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'type': 'user_action'
        }

        if context:
            action_data.update(context)

        self.info(f"User action: {action}", extra=action_data)

    def log_ai_integration_event(self, event_type: str, source_ai: str, target_ai: str,
                                details: Optional[Dict[str, Any]] = None):
        """
        Log AI integration events

        Args:
            event_type: Type of integration event
            source_ai: Source AI component
            target_ai: Target AI component
            details: Additional event details
        """
        event_data = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'source_ai': source_ai,
            'target_ai': target_ai,
            'type': 'ai_integration'
        }

        if details:
            event_data.update(details)

        self.info(f"AI Integration: {event_type} ({source_ai} -> {target_ai})", extra=event_data)

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics across all components"""
        with self._lock:
            return {
                'error_counts': self.error_counts.copy(),
                'total_errors': sum(
                    count for key, count in self.error_counts.items()
                    if 'error' in key
                ),
                'total_critical': sum(
                    count for key, count in self.error_counts.items()
                    if 'critical' in key
                )
            }

    def set_log_level(self, level: int):
        """Set logging level for all loggers"""
        self.log_level = level
        self.main_logger.setLevel(level)

        for logger in self.component_loggers.values():
            logger.setLevel(level)

    def flush_logs(self):
        """Flush all log handlers"""
        for handler in self.main_logger.handlers:
            handler.flush()

        for logger in self.component_loggers.values():
            for handler in logger.handlers:
                handler.flush()

        for handler in self.performance_logger.handlers:
            handler.flush()

    def cleanup(self):
        """Cleanup logging resources"""
        self.info("IntegratedLogger cleanup initiated")

        # Flush all logs
        self.flush_logs()

        # Close all handlers
        for handler in self.main_logger.handlers:
            handler.close()

        for logger in self.component_loggers.values():
            for handler in logger.handlers:
                handler.close()

        for handler in self.performance_logger.handlers:
            handler.close()


def create_integrated_logger(log_dir: Path = Path("logs"),
                           log_level: int = logging.INFO) -> IntegratedLogger:
    """
    Factory function to create integrated logger

    Args:
        log_dir: Directory for log files
        log_level: Minimum logging level

    Returns:
        Configured IntegratedLogger instance
    """
    return IntegratedLogger(log_dir=log_dir, log_level=log_level)
