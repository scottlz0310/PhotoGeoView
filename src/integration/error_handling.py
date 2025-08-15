"""
Unified Error Handling System for AI Integration

Provides centralized error handling that coordinates between:
- GitHub Copilot (CS4Coding): Robust error recovery
- Cursor (CursorBLD): User-friendly error presentation
- Kiro: Integration error management and monitoring

Author: Kiro AI Integration System
"""

import logging
import sys
import traceback
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .models import AIComponent


class ErrorCategory(Enum):
    """Error category enumeration for unified error handling"""

    UI_ERROR = "ui"  # CursorBLD UI-related errors
    CORE_ERROR = "core"  # CS4Coding functionality errors
    INTEGRATION_ERROR = "integration"  # Kiro integration errors
    SYSTEM_ERROR = "system"  # System-level errors
    NETWORK_ERROR = "network"  # Network-related errors
    FILE_ERROR = "file"  # File system errors
    VALIDATION_ERROR = "validation"  # Data validation errors
    PERFORMANCE_ERROR = "performance"  # Performance-related errors
    STATE_ERROR = "state"  # State management errors


class ErrorSeverity(Enum):
    """Error severity levels"""

    CRITICAL = "critical"  # Application cannot continue
    ERROR = "error"  # Feature unavailable but app can continue
    WARNING = "warning"  # Potential issue, degraded functionality
    INFO = "info"  # Informational message


@dataclass
class ErrorContext:
    """Context information for error handling"""

    # Error identification
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    ai_component: Optional[AIComponent] = None

    # Error details
    message: str = ""
    technical_details: str = ""
    user_message: str = ""

    # Context information
    operation: str = ""
    file_path: Optional[Path] = None
    user_action: str = ""

    # System state
    timestamp: datetime = None
    stack_trace: str = ""
    system_info: Dict[str, Any] = None

    # Recovery information
    recovery_suggestions: List[str] = None
    retry_possible: bool = False
    fallback_available: bool = False

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.recovery_suggestions is None:
            self.recovery_suggestions = []
        if self.system_info is None:
            self.system_info = {}


class IntegratedErrorHandler:
    """
    Unified error handling system that coordinates error management
    across all AI implementations
    """

    def __init__(self, logger=None):
        """
        Initialize the integrated erroAI intler

        Args:
            logger: Logger instance for error logging
        """
        self.logger = logger
        self.error_strategies: Dict[ErrorCategory, Callable] = {
            ErrorCategory.UI_ERROR: self._handle_ui_error,
            ErrorCategory.CORE_ERROR: self._handle_core_error,
            ErrorCategory.INTEGRATION_ERROR: self._handle_integration_error,
            ErrorCategory.SYSTEM_ERROR: self._handle_system_error,
            ErrorCategory.NETWORK_ERROR: self._handle_network_error,
            ErrorCategory.FILE_ERROR: self._handle_file_error,
            ErrorCategory.VALIDATION_ERROR: self._handle_validation_error,
            ErrorCategory.PERFORMANCE_ERROR: self._handle_performance_error,
        }

        # Error statistics
        self.error_counts: Dict[ErrorCategory, int] = {cat: 0 for cat in ErrorCategory}
        self.recent_errors: List[ErrorContext] = []
        self.max_recent_errors = 100

        # Recovery strategies
        self.recovery_handlers: Dict[str, Callable] = {}
        self.fallback_handlers: Dict[str, Callable] = {}

    def handle_error(
        self,
        error: Exception,
        category: ErrorCategory,
        context: Dict[str, Any] = None,
        ai_component: Optional[AIComponent] = None,
    ) -> ErrorContext:
        """
        Handle an error with unified error management

        Args:
            error: The exception that occurred
            category: Category of the error
            context: Additional context information
            ai_component: AI component that generated the error

        Returns:
            ErrorContext with error details and recovery information
        """

        # Create error context
        error_context = self._create_error_context(
            error, category, context, ai_component
        )

        # Log the error
        self._log_error(error_context)

        # Update statistics
        self.error_counts[category] += 1
        self.recent_errors.insert(0, error_context)
        self.recent_errors = self.recent_errors[: self.max_recent_errors]

        # Apply error handling strategy
        strategy = self.error_strategies.get(category, self._default_error_handling)
        try:
            strategy(error_context)
        except Exception as handler_error:
            # Error in error handler - use fallback
            self._fallback_error_handling(error_context, handler_error)

        return error_context

    def _create_error_context(
        self,
        error: Exception,
        category: ErrorCategory,
        context: Dict[str, Any] = None,
        ai_component: Optional[AIComponent] = None,
    ) -> ErrorContext:
        """Create comprehensive error context"""

        context = context or {}

        # 型チェック: categoryがErrorCategory型であることを確認
        if not isinstance(category, ErrorCategory):
            # 文字列が渡された場合は、デフォルトのErrorCategoryを使用
            category = ErrorCategory.CORE_ERROR

        # Determine severity based on error type and category
        severity = self._determine_severity(error, category)

        # Generate error ID
        error_id = f"{category.value}_{int(datetime.now().timestamp())}_{id(error)}"

        # Extract technical details
        technical_details = f"{type(error).__name__}: {str(error)}"
        stack_trace = traceback.format_exc()

        # Generate user-friendly message
        user_message = self._generate_user_message(error, category, ai_component)

        # Collect system information
        system_info = {
            "python_version": sys.version,
            "platform": sys.platform,
            "ai_component": ai_component.value if ai_component else None,
        }

        # Determine recovery options
        recovery_suggestions = self._get_recovery_suggestions(error, category)
        retry_possible = self._is_retry_possible(error, category)
        fallback_available = self._is_fallback_available(error, category)

        return ErrorContext(
            error_id=error_id,
            category=category,
            severity=severity,
            ai_component=ai_component,
            message=str(error),
            technical_details=technical_details,
            user_message=user_message,
            operation=context.get("operation", ""),
            file_path=context.get("file_path"),
            user_action=context.get("user_action", ""),
            stack_trace=stack_trace,
            system_info=system_info,
            recovery_suggestions=recovery_suggestions,
            retry_possible=retry_possible,
            fallback_available=fallback_available,
        )

    def _determine_severity(
        self, error: Exception, category: ErrorCategory
    ) -> ErrorSeverity:
        """Determine error severity based on error type and category"""

        # Critical errors that prevent application from continuing
        critical_errors = (SystemExit, KeyboardInterrupt, MemoryError)
        if isinstance(error, critical_errors):
            return ErrorSeverity.CRITICAL

        # Category-based severity
        if category == ErrorCategory.SYSTEM_ERROR:
            return ErrorSeverity.ERROR
        elif category == ErrorCategory.INTEGRATION_ERROR:
            return ErrorSeverity.ERROR
        elif category == ErrorCategory.UI_ERROR:
            return ErrorSeverity.WARNING
        elif category == ErrorCategory.VALIDATION_ERROR:
            return ErrorSeverity.WARNING
        elif category == ErrorCategory.PERFORMANCE_ERROR:
            return ErrorSeverity.INFO

        # Default to ERROR for unknown cases
        return ErrorSeverity.ERROR

    def _generate_user_message(
        self,
        error: Exception,
        category: ErrorCategory,
        ai_component: Optional[AIComponent],
    ) -> str:
        """Generate user-friendly error message"""

        component_name = ai_component.value.title() if ai_component else "System"

        if category == ErrorCategory.UI_ERROR:
            return f"Interface issue in {component_name}. The display may not update correctly."
        elif category == ErrorCategory.CORE_ERROR:
            return f"Feature unavailable in {component_name}. Some functionality may be limited."
        elif category == ErrorCategory.FILE_ERROR:
            return f"File access problem. Please check file permissions and try again."
        elif category == ErrorCategory.NETWORK_ERROR:
            return f"Network connection issue. Please check your internet connection."
        elif category == ErrorCategory.VALIDATION_ERROR:
            return f"Invalid data detected. Please verify your input and try again."
        elif category == ErrorCategory.PERFORMANCE_ERROR:
            return f"Performance issue detected. The application may respond slowly."
        else:
            return (
                f"An unexpected error occurred in {component_name}. Please try again."
            )

    def _get_recovery_suggestions(
        self, error: Exception, category: ErrorCategory
    ) -> List[str]:
        """Get recovery suggestions based on error type and category"""

        suggestions = []

        if category == ErrorCategory.FILE_ERROR:
            suggestions.extend(
                [
                    "Check if the file exists and is accessible",
                    "Verify file permissions",
                    "Try selecting a different file",
                    "Restart the application if the problem persists",
                ]
            )
        elif category == ErrorCategory.NETWORK_ERROR:
            suggestions.extend(
                [
                    "Check your internet connection",
                    "Try again in a few moments",
                    "Check firewall settings",
                    "Use offline features if available",
                ]
            )
        elif category == ErrorCategory.UI_ERROR:
            suggestions.extend(
                [
                    "Try refreshing the display",
                    "Switch to a different theme",
                    "Restart the application",
                    "Check display settings",
                ]
            )
        elif category == ErrorCategory.PERFORMANCE_ERROR:
            suggestions.extend(
                [
                    "Close other applications to free memory",
                    "Reduce image quality settings",
                    "Clear application cache",
                    "Restart the application",
                ]
            )
        else:
            suggestions.extend(
                [
                    "Try the operation again",
                    "Restart the application",
                    "Check the application logs for more details",
                ]
            )

        return suggestions

    def _is_retry_possible(self, error: Exception, category: ErrorCategory) -> bool:
        """Determine if the operation can be retried"""

        # Generally, temporary errors can be retried
        retry_categories = {
            ErrorCategory.NETWORK_ERROR,
            ErrorCategory.PERFORMANCE_ERROR,
            ErrorCategory.FILE_ERROR,
        }

        # Permanent errors that shouldn't be retried
        permanent_errors = (KeyboardInterrupt, SystemExit, NotImplementedError)

        return category in retry_categories and not isinstance(error, permanent_errors)

    def _is_fallback_available(self, error: Exception, category: ErrorCategory) -> bool:
        """Determine if fallback handling is available"""

        # Categories that typically have fallback options
        fallback_categories = {
            ErrorCategory.UI_ERROR,
            ErrorCategory.CORE_ERROR,
            ErrorCategory.INTEGRATION_ERROR,
        }

        return category in fallback_categories

    def _log_error(self, error_context: ErrorContext):
        """Log error with appropriate level"""

        if self.logger:
            log_message = f"[{error_context.ai_component.value if error_context.ai_component else 'SYSTEM'}] {error_context.message}"

            if error_context.severity == ErrorSeverity.CRITICAL:
                self.logger.critical(
                    log_message, extra={"error_context": error_context}
                )
            elif error_context.severity == ErrorSeverity.ERROR:
                self.logger.error(log_message, extra={"error_context": error_context})
            elif error_context.severity == ErrorSeverity.WARNING:
                self.logger.warning(log_message, extra={"error_context": error_context})
            else:
                self.logger.info(log_message, extra={"error_context": error_context})

    # AI-specific error handling strategies

    def _handle_ui_error(self, error_context: ErrorContext):
        """Handle CursorBLD UI-related errors"""

        # UI error recovery strategies
        if "theme" in error_context.operation.lower():
            # Theme-related error - try default theme
            error_context.recovery_suggestions.insert(0, "Switching to default theme")

        if "thumbnail" in error_context.operation.lower():
            # Thumbnail error - disable thumbnails temporarily
            error_context.recovery_suggestions.insert(
                0, "Disabling thumbnail generation temporarily"
            )

        # UI errors are generally non-critical
        pass

    def _handle_core_error(self, error_context: ErrorContext):
        """Handle CS4Coding core functionality errors"""

        # Core functionality error recovery
        if "exif" in error_context.operation.lower():
            # EXIF parsing error - use basic file info
            error_context.recovery_suggestions.insert(
                0, "Using basic file information instead of EXIF data"
            )

        if "map" in error_context.operation.lower():
            # Map error - disable map features
            error_context.recovery_suggestions.insert(
                0, "Map features temporarily unavailable"
            )

    def _handle_integration_error(self, error_context: ErrorContext):
        """Handle Kiro integration errors"""

        # Integration error recovery
        if "cache" in error_context.operation.lower():
            # Cache error - clear cache and continue
            error_context.recovery_suggestions.insert(0, "Clearing cache and retrying")

        if "config" in error_context.operation.lower():
            # Configuration error - use defaults
            error_context.recovery_suggestions.insert(0, "Using default configuration")

    def _handle_system_error(self, error_context: ErrorContext):
        """Handle system-level errors"""

        # System errors are typically more serious
        if (
            isinstance(error_context.message, str)
            and "memory" in error_context.message.lower()
        ):
            error_context.recovery_suggestions.insert(
                0, "Close other applications to free memory"
            )

        if "permission" in error_context.message.lower():
            error_context.recovery_suggestions.insert(
                0, "Check file and folder permissions"
            )

    def _handle_network_error(self, error_context: ErrorContext):
        """Handle network-related errors"""

        error_context.recovery_suggestions.extend(
            [
                "Check internet connection",
                "Try again in a few moments",
                "Use offline features if available",
            ]
        )

    def _handle_file_error(self, error_context: ErrorContext):
        """Handle file system errors"""

        if error_context.file_path:
            error_context.recovery_suggestions.insert(
                0, f"Check if file exists: {error_context.file_path}"
            )

    def _handle_validation_error(self, error_context: ErrorContext):
        """Handle data validation errors"""

        error_context.recovery_suggestions.extend(
            [
                "Verify input data format",
                "Check for corrupted files",
                "Try with a different file",
            ]
        )

    def _handle_performance_error(self, error_context: ErrorContext):
        """Handle performance-related errors"""

        error_context.recovery_suggestions.extend(
            [
                "Reduce image quality settings",
                "Close other applications",
                "Clear application cache",
            ]
        )

    def _default_error_handling(self, error_context: ErrorContext):
        """Default error handling for unknown error types"""

        error_context.recovery_suggestions.extend(
            [
                "Try the operation again",
                "Restart the application if the problem persists",
            ]
        )

    def _fallback_error_handling(
        self, error_context: ErrorContext, handler_error: Exception
    ):
        """Fallback error handling when primary handler fails"""

        if self.logger:
            self.logger.critical(f"Error handler failed: {handler_error}")

        # Minimal error handling - 最終手段として標準エラー出力とコンソールの両方に出力
        fallback_logger = logging.getLogger(__name__)
        handler_error_msg = f"Critical error in error handler: {handler_error}"
        original_error_msg = f"Original error: {error_context.message}"

        fallback_logger.critical(handler_error_msg)
        fallback_logger.critical(original_error_msg)

        print(handler_error_msg)
        print(original_error_msg)

    # Utility methods

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics"""

        return {
            "error_counts": {
                cat.value: count for cat, count in self.error_counts.items()
            },
            "total_errors": sum(self.error_counts.values()),
            "recent_error_count": len(self.recent_errors),
            "most_common_category": max(
                self.error_counts, key=self.error_counts.get
            ).value,
        }

    def clear_error_history(self):
        """Clear error history and statistics"""

        self.error_counts = {cat: 0 for cat in ErrorCategory}
        self.recent_errors.clear()

    def register_recovery_handler(self, operation: str, handler: Callable):
        """Register a custom recovery handler for specific operations"""

        self.recovery_handlers[operation] = handler

    def register_fallback_handler(self, operation: str, handler: Callable):
        """Register a custom fallback handler for specific operations"""

        self.fallback_handlers[operation] = handler
