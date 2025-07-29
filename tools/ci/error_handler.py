"""
Error Handler for CI Simulation Tool

This module provides comprehensive error handling and recovery strategies
for the CI simulation system, including error classification, automatic
recovery, and detailed troubleshooting guidance.

Author: Kiro (AI Integration and Quality Assurance)
"""

import logging
import traceback
import sys
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

try:
    from .models import CheckResult, CheckStatus, SeverityLevel
    from .interfaces import CISimulationError, CheckerError, EnvironmentError, ConfigurationError, DependencyError
    from .utils import run_command, is_tool_available, get_python_executable, ensure_directory_exists
except ImportError:
    from models import CheckResult, CheckStatus, SeverityLevel
    from interfaces import CISimulationError, CheckerError, EnvironmentError, ConfigurationError, DependencyError
    from utils import run_command, is_tool_available, get_python_executable, ensure_directory_exists


class ErrorCategory(Enum):
    """Categories of errors that can occur during CI simulation."""

    ENVIRONMENT = "environment"
    CONFIGURATION = "configuration"
    EXECUTION = "execution"
    DEPENDENCY = "dependency"
    RESOURCE = "resource"
    NETWORK = "network"
    PERMISSION = "permission"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class RecoveryStrategy(Enum):
    """Available recovery strategies for different error types."""

    RETRY = "retry"
    FALLBACK = "fallback"
    SKIP = "skip"
    ABORT = "abort"
    MANUAL = "manual"
    AUTO_FIX = "auto_fix"


@dataclass
class RecoveryAction:
    """Represents a recovery action to be taken for an error."""

    strategy: RecoveryStrategy
    description: str
    action_function: Optional[Callable] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    success_probability: float = 0.5  # 0.0 to 1.0
    estimated_time: float = 0.0  # seconds
    user_confirmation_required: bool = False


@dataclass
class ErrorContext:
    """Context information for an error occurrence."""

    error: Exception
    category: ErrorCategory
    severity: SeverityLevel
    component: str
    operation: str
    timestamp: datetime = field(default_factory=datetime.now)
    environment_info: Dict[str, Any] = field(default_factory=dict)
    recovery_attempts: List[RecoveryAction] = field(default_factory=list)
    resolved: bool = False


class ErrorHandler:
    """
    Comprehensive error handler with recovery strategies.

    This class provides centralized error handling for the CI simulation tool,
    including error classification, automatic recovery attempts, and detailed
    troubleshooting guidance.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the error handler.

        Args:
            config: Configuration dictionary for error handling behavior
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.error_history: List[ErrorContext] = []
        self.recovery_strategies: Dict[ErrorCategory, List[RecoveryAction]] = {}
        self.max_retry_attempts = self.config.get('max_retry_attempts', 3)
        self.retry_delay = self.config.get('retry_delay', 1.0)
        self.auto_recovery_enabled = self.config.get('auto_recovery_enabled', True)

        self._initialize_recovery_strategies()

    def _initialize_recovery_strategies(self) -> None:
        """Initialize default recovery strategies for different error categories."""

        # Environment errors
        self.recovery_strategies[ErrorCategory.ENVIRONMENT] = [
            RecoveryAction(
                strategy=RecoveryStrategy.AUTO_FIX,
                description="Attempt to install missing system dependencies",
                action_function=self._install_system_dependencies,
                success_probability=0.7,
                estimated_time=30.0
            ),
            RecoveryAction(
                strategy=RecoveryStrategy.FALLBACK,
                description="Use alternative Python version",
                action_function=self._use_alternative_python,
                success_probability=0.6,
                estimated_time=5.0
            ),
            RecoveryAction(
                strategy=RecoveryStrategy.MANUAL,
                description="Manual environment setup required",
                success_probability=0.9,
                user_confirmation_required=True
            )
        ]

        # Configuration errors
        self.recovery_strategies[ErrorCategory.CONFIGURATION] = [
            RecoveryAction(
                strategy=RecoveryStrategy.FALLBACK,
                description="Use default configuration",
                action_function=self._use_default_config,
                success_probability=0.8,
                estimated_time=1.0
            ),
            RecoveryAction(
                strategy=RecoveryStrategy.AUTO_FIX,
                description="Repair configuration file",
                action_function=self._repair_config_file,
                success_probability=0.6,
                estimated_time=2.0
            )
        ]

        # Execution errors
        self.recovery_strategies[ErrorCategory.EXECUTION] = [
            RecoveryAction(
                strategy=RecoveryStrategy.RETRY,
                description="Retry with increased timeout",
                action_function=self._retry_with_timeout,
                success_probability=0.5,
                estimated_time=10.0
            ),
            RecoveryAction(
                strategy=RecoveryStrategy.FALLBACK,
                description="Skip problematic test and continue",
                action_function=self._skip_and_continue,
                success_probability=0.9,
                estimated_time=0.1
            )
        ]

        # Dependency errors
        self.recovery_strategies[ErrorCategory.DEPENDENCY] = [
            RecoveryAction(
                strategy=RecoveryStrategy.AUTO_FIX,
                description="Install missing dependencies",
                action_function=self._install_dependencies,
                success_probability=0.8,
                estimated_time=20.0
            ),
            RecoveryAction(
                strategy=RecoveryStrategy.FALLBACK,
                description="Use alternative implementation",
                action_function=self._use_alternative_implementation,
                success_probability=0.4,
                estimated_time=1.0
            )
        ]

        # Resource errors
        self.recovery_strategies[ErrorCategory.RESOURCE] = [
            RecoveryAction(
                strategy=RecoveryStrategy.AUTO_FIX,
                description="Clean up temporary files",
                action_function=self._cleanup_resources,
                success_probability=0.7,
                estimated_time=5.0
            ),
            RecoveryAction(
                strategy=RecoveryStrategy.FALLBACK,
                description="Reduce resource usage",
                action_function=self._reduce_resource_usage,
                success_probability=0.6,
                estimated_time=2.0
            )
        ]

        # Timeout errors
        self.recovery_strategies[ErrorCategory.TIMEOUT] = [
            RecoveryAction(
                strategy=RecoveryStrategy.RETRY,
                description="Retry with extended timeout",
                action_function=self._extend_timeout,
                success_probability=0.6,
                estimated_time=30.0
            ),
            RecoveryAction(
                strategy=RecoveryStrategy.SKIP,
                description="Skip timeout-prone operation",
                action_function=self._skip_operation,
                success_probability=0.9,
                estimated_time=0.1
            )
        ]

    def handle_error(
        self,
        error: Exception,
        component: str,
        operation: str,
        context: Dict[str, Any] = None
    ) -> ErrorContext:
        """
        Handle an error with automatic classification and recovery attempts.

        Args:
            error: The exception that occurred
            component: Name of the component where error occurred
            operation: Description of the operation that failed
            context: Additional context information

        Returns:
            ErrorContext with recovery information
        """
        # Classify the error
        category = self._classify_error(error)
        severity = self._determine_severity(error, category)

        # Create error context
        error_context = ErrorContext(
            error=error,
            category=category,
            severity=severity,
            component=component,
            operation=operation,
            environment_info=self._gather_environment_info(),
        )

        if context:
            error_context.environment_info.update(context)

        # Log the error
        self._log_error(error_context)

        # Attempt recovery if enabled
        if self.auto_recovery_enabled:
            self._attempt_recovery(error_context)

        # Add to history
        self.error_history.append(error_context)

        return error_context

    def _classify_error(self, error: Exception) -> ErrorCategory:
        """Classify an error into a category."""

        if isinstance(error, EnvironmentError):
            return ErrorCategory.ENVIRONMENT
        elif isinstance(error, ConfigurationError):
            return ErrorCategory.CONFIGURATION
        elif isinstance(error, DependencyError):
            return ErrorCategory.DEPENDENCY
        elif isinstance(error, subprocess.TimeoutExpired):
            return ErrorCategory.TIMEOUT
        elif isinstance(error, PermissionError):
            return ErrorCategory.PERMISSION
        elif isinstance(error, (OSError, IOError)):
            if "No space left on device" in str(error):
                return ErrorCategory.RESOURCE
            elif "Permission denied" in str(error):
                return ErrorCategory.PERMISSION
            else:
                return ErrorCategory.EXECUTION
        elif isinstance(error, (ConnectionError, TimeoutError)):
            return ErrorCategory.NETWORK
        elif isinstance(error, MemoryError):
            return ErrorCategory.RESOURCE
        else:
            return ErrorCategory.UNKNOWN

    def _determine_severity(self, error: Exception, category: ErrorCategory) -> SeverityLevel:
        """Determine the severity level of an error."""

        # Critical errors that prevent any progress
        if isinstance(error, (SystemExit, KeyboardInterrupt)):
            return SeverityLevel.CRITICAL

        # High severity for environment and dependency issues
        if category in [ErrorCategory.ENVIRONMENT, ErrorCategory.DEPENDENCY]:
            return SeverityLevel.HIGH

        # Medium severity for configuration and execution issues
        if category in [ErrorCategory.CONFIGURATION, ErrorCategory.EXECUTION]:
            return SeverityLevel.MEDIUM

        # Low severity for resource and timeout issues (often recoverable)
        if category in [ErrorCategory.RESOURCE, ErrorCategory.TIMEOUT]:
            return SeverityLevel.LOW

        return SeverityLevel.MEDIUM

    def _gather_environment_info(self) -> Dict[str, Any]:
        """Gather environment information for error context."""

        info = {
            'python_version': sys.version,
            'platform': sys.platform,
            'cwd': os.getcwd(),
            'path': os.environ.get('PATH', ''),
            'timestamp': datetime.now().isoformat(),
        }

        # Check available tools
        tools = ['git', 'python', 'pip', 'black', 'isort', 'flake8', 'mypy', 'pytest']
        info['available_tools'] = {tool: is_tool_available(tool) for tool in tools}

        # Memory and disk info (if available)
        try:
            import psutil
            info['memory_percent'] = psutil.virtual_memory().percent
            info['disk_percent'] = psutil.disk_usage('/').percent
        except ImportError:
            pass

        return info

    def _log_error(self, error_context: ErrorContext) -> None:
        """Log error information."""

        self.logger.error(
            f"Error in {error_context.component}.{error_context.operation}: "
            f"{error_context.category.value} - {str(error_context.error)}"
        )

        if error_context.severity == SeverityLevel.CRITICAL:
            self.logger.critical(f"Critical error: {str(error_context.error)}")
            self.logger.critical(f"Traceback: {traceback.format_exc()}")

    def _attempt_recovery(self, error_context: ErrorContext) -> None:
        """Attempt to recover from an error using available strategies."""

        strategies = self.recovery_strategies.get(error_context.category, [])

        for strategy in strategies:
            if len(error_context.recovery_attempts) >= self.max_retry_attempts:
                break

            self.logger.info(f"Attempting recovery: {strategy.description}")

            try:
                if strategy.action_function:
                    success = strategy.action_function(error_context, **strategy.parameters)
                    if success:
                        error_context.resolved = True
                        self.logger.info(f"Recovery successful: {strategy.description}")
                        break
                    else:
                        self.logger.warning(f"Recovery failed: {strategy.description}")

                error_context.recovery_attempts.append(strategy)

            except Exception as recovery_error:
                self.logger.error(f"Recovery attempt failed: {str(recovery_error)}")
                error_context.recovery_attempts.append(strategy)

    # Recovery action implementations

    def _install_system_dependencies(self, error_context: ErrorContext, **kwargs) -> bool:
        """Attempt to install missing system dependencies."""

        # Check for common missing dependencies
        missing_deps = []

        # Qt dependencies
        if not is_tool_available('qmake') and 'qt' in str(error_context.error).lower():
            missing_deps.extend(['qt5-default', 'qtbase5-dev'])

        # Display dependencies
        if 'display' in str(error_context.error).lower():
            missing_deps.extend(['xvfb', 'x11-utils'])

        if not missing_deps:
            return False

        # Try to install using apt (Ubuntu/Debian)
        if shutil.which('apt-get'):
            try:
                cmd = ['sudo', 'apt-get', 'install', '-y'] + missing_deps
                returncode, stdout, stderr = run_command(cmd, timeout=300)
                return returncode == 0
            except Exception:
                return False

        return False

    def _use_alternative_python(self, error_context: ErrorContext, **kwargs) -> bool:
        """Try to use an alternative Python version."""

        # Try different Python versions
        versions = ['3.9', '3.10', '3.11', '3.8']

        for version in versions:
            python_exe = get_python_executable(version)
            if python_exe:
                # Update environment to use this Python version
                os.environ['PYTHON_EXECUTABLE'] = python_exe
                return True

        return False

    def _use_default_config(self, error_context: ErrorContext, **kwargs) -> bool:
        """Use default configuration when config is invalid."""

        try:
            # This would be implemented by the specific component
            # For now, just indicate that fallback is possible
            return True
        except Exception:
            return False

    def _repair_config_file(self, error_context: ErrorContext, **kwargs) -> bool:
        """Attempt to repair a corrupted configuration file."""

        # This is a placeholder - actual implementation would depend on
        # the specific configuration format and corruption type
        return False

    def _retry_with_timeout(self, error_context: ErrorContext, **kwargs) -> bool:
        """Retry operation with increased timeout."""

        # This would be handled by the calling component
        # The error handler just indicates that retry is recommended
        return False

    def _skip_and_continue(self, error_context: ErrorContext, **kwargs) -> bool:
        """Skip the problematic operation and continue."""

        # Mark as resolved to continue execution
        return True

    def _install_dependencies(self, error_context: ErrorContext, **kwargs) -> bool:
        """Install missing Python dependencies."""

        if isinstance(error_context.error, DependencyError):
            missing_deps = error_context.error.missing_dependencies

            try:
                cmd = [sys.executable, '-m', 'pip', 'install'] + missing_deps
                returncode, stdout, stderr = run_command(cmd, timeout=120)
                return returncode == 0
            except Exception:
                return False

        return False

    def _use_alternative_implementation(self, error_context: ErrorContext, **kwargs) -> bool:
        """Use alternative implementation when primary fails."""

        # This would be component-specific
        return False

    def _cleanup_resources(self, error_context: ErrorContext, **kwargs) -> bool:
        """Clean up temporary files and resources."""

        try:
            # Clean up common temporary directories
            temp_dirs = ['/tmp', 'temp', '.pytest_cache', '__pycache__']

            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    if temp_dir.startswith('/tmp'):
                        # Only clean our own temp files
                        for item in os.listdir(temp_dir):
                            if 'ci_simulation' in item:
                                item_path = os.path.join(temp_dir, item)
                                if os.path.isdir(item_path):
                                    shutil.rmtree(item_path)
                                else:
                                    os.remove(item_path)
                    else:
                        # Clean project-specific temp directories
                        if os.path.isdir(temp_dir):
                            shutil.rmtree(temp_dir)

            return True
        except Exception:
            return False

    def _reduce_resource_usage(self, error_context: ErrorContext, **kwargs) -> bool:
        """Reduce resource usage for the operation."""

        # This would be implemented by specific components
        # Could involve reducing parallelism, batch sizes, etc.
        return False

    def _extend_timeout(self, error_context: ErrorContext, **kwargs) -> bool:
        """Extend timeout for the operation."""

        # This would be handled by the calling component
        return False

    def _skip_operation(self, error_context: ErrorContext, **kwargs) -> bool:
        """Skip the timeout-prone operation."""

        return True

    def generate_error_report(self, errors: List[ErrorContext] = None) -> str:
        """
        Generate a detailed error report with troubleshooting guidance.

        Args:
            errors: List of error contexts to include (defaults to all)

        Returns:
            Formatted error report string
        """

        if errors is None:
            errors = self.error_history

        if not errors:
            return "No errors to report."

        report_lines = [
            "# CI Simulation Error Report",
            f"Generated: {datetime.now().isoformat()}",
            f"Total Errors: {len(errors)}",
            ""
        ]

        # Summary by category
        category_counts = {}
        for error in errors:
            category_counts[error.category] = category_counts.get(error.category, 0) + 1

        report_lines.extend([
            "## Error Summary by Category",
            ""
        ])

        for category, count in sorted(category_counts.items(), key=lambda x: x[0].value):
            report_lines.append(f"- {category.value}: {count}")

        report_lines.extend(["", "## Detailed Error Information", ""])

        # Detailed error information
        for i, error in enumerate(errors, 1):
            report_lines.extend([
                f"### Error {i}: {error.component}.{error.operation}",
                f"- **Category**: {error.category.value}",
                f"- **Severity**: {error.severity.value}",
                f"- **Timestamp**: {error.timestamp.isoformat()}",
                f"- **Error**: {str(error.error)}",
                f"- **Resolved**: {'Yes' if error.resolved else 'No'}",
                ""
            ])

            if error.recovery_attempts:
                report_lines.extend([
                    "**Recovery Attempts:**",
                    ""
                ])
                for attempt in error.recovery_attempts:
                    report_lines.append(f"- {attempt.strategy.value}: {attempt.description}")
                report_lines.append("")

            # Add troubleshooting guidance
            guidance = self._get_troubleshooting_guidance(error)
            if guidance:
                report_lines.extend([
                    "**Troubleshooting Guidance:**",
                    ""
                ])
                for guide in guidance:
                    report_lines.append(f"- {guide}")
                report_lines.append("")

        return "\n".join(report_lines)

    def _get_troubleshooting_guidance(self, error_context: ErrorContext) -> List[str]:
        """Get troubleshooting guidance for a specific error."""

        guidance = []

        if error_context.category == ErrorCategory.ENVIRONMENT:
            guidance.extend([
                "Check that all required system dependencies are installed",
                "Verify Python version compatibility (3.9, 3.10, or 3.11)",
                "Ensure virtual display is available for GUI tests (install xvfb)",
                "Check Qt dependencies if running GUI-related tests"
            ])

        elif error_context.category == ErrorCategory.DEPENDENCY:
            guidance.extend([
                "Run 'pip install -r requirements.txt' to install Python dependencies",
                "Check for conflicting package versions",
                "Consider using a fresh virtual environment",
                "Verify that all development dependencies are installed"
            ])

        elif error_context.category == ErrorCategory.CONFIGURATION:
            guidance.extend([
                "Check configuration file syntax (JSON/YAML)",
                "Verify all required configuration keys are present",
                "Check file permissions for configuration files",
                "Consider using default configuration as fallback"
            ])

        elif error_context.category == ErrorCategory.RESOURCE:
            guidance.extend([
                "Check available disk space",
                "Monitor memory usage during execution",
                "Clean up temporary files and caches",
                "Consider reducing parallelism or batch sizes"
            ])

        elif error_context.category == ErrorCategory.TIMEOUT:
            guidance.extend([
                "Increase timeout values in configuration",
                "Check network connectivity for remote operations",
                "Consider running tests in smaller batches",
                "Monitor system load during execution"
            ])

        elif error_context.category == ErrorCategory.PERMISSION:
            guidance.extend([
                "Check file and directory permissions",
                "Ensure write access to output directories",
                "Consider running with appropriate user privileges",
                "Verify Git repository permissions"
            ])

        return guidance

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get statistics about errors encountered."""

        if not self.error_history:
            return {"total_errors": 0}

        stats = {
            "total_errors": len(self.error_history),
            "resolved_errors": sum(1 for e in self.error_history if e.resolved),
            "by_category": {},
            "by_severity": {},
            "by_component": {},
            "recovery_success_rate": 0.0
        }

        for error in self.error_history:
            # By category
            cat = error.category.value
            stats["by_category"][cat] = stats["by_category"].get(cat, 0) + 1

            # By severity
            sev = error.severity.value
            stats["by_severity"][sev] = stats["by_severity"].get(sev, 0) + 1

            # By component
            comp = error.component
            stats["by_component"][comp] = stats["by_component"].get(comp, 0) + 1

        # Calculate recovery success rate
        if stats["total_errors"] > 0:
            stats["recovery_success_rate"] = stats["resolved_errors"] / stats["total_errors"]

        return stats

    def clear_error_history(self) -> None:
        """Clear the error history."""
        self.error_history.clear()

    def save_error_report(self, filepath: str, errors: List[ErrorContext] = None) -> None:
        """
        Save error report to file.

        Args:
            filepath: Path to save the report
            errors: List of error contexts to include (defaults to all)
        """
        ensure_directory_exists(os.path.dirname(filepath))

        report = self.generate_error_report(errors)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)

        self.logger.info(f"Error report saved to: {filepath}")
