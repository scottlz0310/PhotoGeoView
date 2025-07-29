"""
Integrated Error Recovery System for CI Simulation Tool

This module integrates the ErrorHandler and ResourceManager to provide
a comprehensive error handling and recovery system with resource management.

Author: Kiro (AI Integration and Quality Assurance)
"""

import logging
import os
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime

try:
    from .error_handler import ErrorHandler, ErrorContext, ErrorCategory, RecoveryStrategy, RecoveryAction
    from .resource_manager import ResourceManager, get_resource_manager
    from .models import CheckResult, CheckStatus, SeverityLevel
    from .utils import ensure_directory_exists
except ImportError:
    from error_handler import ErrorHandler, ErrorContext, ErrorCategory, RecoveryStrategy, RecoveryAction
    from resource_manager import ResourceManager, get_resource_manager
    from models import CheckResult, CheckStatus, SeverityLevel
    from utils import ensure_directory_exists


@dataclass
class SystemHealth:
    """Represents the overall health of the CI simulation system."""

    error_count: int
    resolved_error_count: int
    resource_usage_ok: bool
    memory_percent: float
    disk_percent: float
    active_temp_resources: int
    system_status: str  # "healthy", "warning", "critical"
    recommendations: List[str]
    timestamp: datetime


class ErrorRecoverySystem:
    """
    Integrated error recovery system combining error handling and resource management.

    This class provides a unified interface for handling errors, managing resources,
    and maintaining system health during CI simulation execution.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the error recovery system.

        Args:
            config: Configuration dictionary for the system
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Initialize components
        error_config = self.config.get('error_handler', {})
        resource_config = self.config.get('resource_manager', {})

        self.error_handler = ErrorHandler(error_config)
        self.resource_manager = get_resource_manager(resource_config)

        # System health monitoring
        self.health_check_interval = self.config.get('health_check_interval', 60)
        self.last_health_check = datetime.now()

        # Recovery strategies that involve resource management
        self._register_resource_recovery_strategies()

    def _register_resource_recovery_strategies(self) -> None:
        """Register recovery strategies that involve resource management."""

        # Add resource-aware recovery strategies to error handler
        resource_recovery_strategies = {
            ErrorCategory.RESOURCE: [
                self.error_handler.recovery_strategies[ErrorCategory.RESOURCE][0],  # Keep existing cleanup
                self.error_handler.recovery_strategies[ErrorCategory.RESOURCE][1],  # Keep existing reduce usage
                # Add new resource-aware strategies
                RecoveryAction(
                    strategy=RecoveryStrategy.AUTO_FIX,
                    description="Force garbage collection and resource cleanup",
                    action_function=self._force_resource_cleanup,
                    success_probability=0.8,
                    estimated_time=10.0
                ),
                RecoveryAction(
                    strategy=RecoveryStrategy.FALLBACK,
                    description="Reduce parallelism and batch sizes",
                    action_function=self._reduce_system_load,
                    success_probability=0.7,
                    estimated_time=5.0
                )
            ]
        }

        # Update error handler strategies
        self.error_handler.recovery_strategies.update(resource_recovery_strategies)

    def handle_error_with_resources(
        self,
        error: Exception,
        component: str,
        operation: str,
        context: Dict[str, Any] = None
    ) -> ErrorContext:
        """
        Handle an error with integrated resource management.

        Args:
            error: The exception that occurred
            component: Name of the component where error occurred
            operation: Description of the operation that failed
            context: Additional context information

        Returns:
            ErrorContext with recovery information
        """
        # Add resource information to context
        if context is None:
            context = {}

        resource_stats = self.resource_manager.get_resource_statistics()
        context.update({
            'resource_usage': resource_stats['current_usage'],
            'tracked_resources': resource_stats['tracked_resources']
        })

        # Handle the error
        error_context = self.error_handler.handle_error(
            error=error,
            component=component,
            operation=operation,
            context=context
        )

        # Check if resource issues contributed to the error
        if self._is_resource_related_error(error_context):
            self._handle_resource_related_error(error_context)

        return error_context

    def _is_resource_related_error(self, error_context: ErrorContext) -> bool:
        """Check if an error is related to resource issues."""

        # Check error category
        if error_context.category in [ErrorCategory.RESOURCE, ErrorCategory.TIMEOUT]:
            return True

        # Check error message for resource-related keywords
        error_msg = str(error_context.error).lower()
        resource_keywords = [
            'memory', 'disk', 'space', 'timeout', 'resource',
            'out of memory', 'no space left', 'cannot allocate'
        ]

        return any(keyword in error_msg for keyword in resource_keywords)

    def _handle_resource_related_error(self, error_context: ErrorContext) -> None:
        """Handle errors that are related to resource issues."""

        self.logger.info(f"Handling resource-related error: {error_context.component}")

        # Get current resource usage
        usage = self.resource_manager.get_resource_usage()

        # Take appropriate action based on resource usage
        if usage.memory_percent > 80:
            self.logger.warning("High memory usage detected, initiating cleanup")
            self.resource_manager._handle_high_memory_usage()

        if usage.disk_percent > 90:
            self.logger.warning("High disk usage detected, initiating cleanup")
            self.resource_manager._handle_high_disk_usage()

        # Clean up old temporary files
        cleaned_files = self.resource_manager.cleanup_temp_files(max_age_seconds=300)
        if cleaned_files > 0:
            self.logger.info(f"Cleaned up {cleaned_files} temporary files")

    def _force_resource_cleanup(self, error_context: ErrorContext, **kwargs) -> bool:
        """Force comprehensive resource cleanup."""

        try:
            # Force garbage collection
            import gc
            gc.collect()

            # Clean up temporary files
            cleaned_files = self.resource_manager.cleanup_temp_files(max_age_seconds=60)

            # Get updated resource usage
            usage = self.resource_manager.get_resource_usage()

            self.logger.info(
                f"Force cleanup completed: {cleaned_files} files cleaned, "
                f"memory: {usage.memory_percent:.1f}%, disk: {usage.disk_percent:.1f}%"
            )

            return True

        except Exception as e:
            self.logger.error(f"Force resource cleanup failed: {e}")
            return False

    def _reduce_system_load(self, error_context: ErrorContext, **kwargs) -> bool:
        """Reduce system load by adjusting operational parameters."""

        try:
            # This would be implemented by specific components
            # For now, just indicate that load reduction is recommended
            self.logger.info("Recommending system load reduction")

            # Add recommendation to error context
            if 'load_reduction_recommended' not in error_context.metadata:
                error_context.metadata['load_reduction_recommended'] = True
                error_context.metadata['recommended_actions'] = [
                    'Reduce parallel execution',
                    'Decrease batch sizes',
                    'Increase timeout values'
                ]

            return True

        except Exception as e:
            self.logger.error(f"System load reduction failed: {e}")
            return False

    def check_system_health(self) -> SystemHealth:
        """
        Check the overall health of the CI simulation system.

        Returns:
            SystemHealth object with current status
        """
        # Get error statistics
        error_stats = self.error_handler.get_error_statistics()

        # Get resource statistics
        resource_stats = self.resource_manager.get_resource_statistics()
        current_usage = resource_stats['current_usage']
        tracked = resource_stats['tracked_resources']

        # Determine system status
        status = "healthy"
        recommendations = []

        # Check error rate
        error_count = error_stats.get('total_errors', 0)
        resolved_count = error_stats.get('resolved_errors', 0)

        if error_count > 10:
            status = "warning"
            recommendations.append("High error count detected - review error patterns")

        if error_count > 0 and resolved_count / error_count < 0.5:
            status = "critical"
            recommendations.append("Low error resolution rate - check recovery strategies")

        # Check resource usage
        memory_ok = current_usage['memory_percent'] < 80
        disk_ok = current_usage['disk_percent'] < 90
        resource_usage_ok = memory_ok and disk_ok

        if not memory_ok:
            if status == "healthy":
                status = "warning"
            recommendations.append(f"High memory usage: {current_usage['memory_percent']:.1f}%")

        if not disk_ok:
            status = "critical"
            recommendations.append(f"High disk usage: {current_usage['disk_percent']:.1f}%")

        # Check temporary resources
        if tracked['temp_resources'] > 100:
            if status == "healthy":
                status = "warning"
            recommendations.append(f"Many temporary resources: {tracked['temp_resources']}")

        if tracked['total_temp_size_mb'] > 1000:  # 1GB
            if status == "healthy":
                status = "warning"
            recommendations.append(f"Large temporary files: {tracked['total_temp_size_mb']:.1f} MB")

        return SystemHealth(
            error_count=error_count,
            resolved_error_count=resolved_count,
            resource_usage_ok=resource_usage_ok,
            memory_percent=current_usage['memory_percent'],
            disk_percent=current_usage['disk_percent'],
            active_temp_resources=tracked['temp_resources'],
            system_status=status,
            recommendations=recommendations,
            timestamp=datetime.now()
        )

    def generate_health_report(self) -> str:
        """Generate a comprehensive system health report."""

        health = self.check_system_health()
        error_stats = self.error_handler.get_error_statistics()

        # Status emoji
        status_emoji = {
            "healthy": "✅",
            "warning": "⚠️",
            "critical": "❌"
        }

        report_lines = [
            "# CI Simulation System Health Report",
            f"Generated: {health.timestamp.isoformat()}",
            f"Status: {status_emoji.get(health.system_status, '❓')} {health.system_status.upper()}",
            "",
            "## Error Statistics",
            f"- Total Errors: {health.error_count}",
            f"- Resolved Errors: {health.resolved_error_count}",
        ]

        if health.error_count > 0:
            resolution_rate = (health.resolved_error_count / health.error_count) * 100
            report_lines.append(f"- Resolution Rate: {resolution_rate:.1f}%")

        report_lines.extend([
            "",
            "## Resource Usage",
            f"- Memory: {health.memory_percent:.1f}%",
            f"- Disk: {health.disk_percent:.1f}%",
            f"- Temporary Resources: {health.active_temp_resources}",
            f"- Resource Usage OK: {'Yes' if health.resource_usage_ok else 'No'}",
        ])

        # Add error breakdown if there are errors
        if error_stats.get('by_category'):
            report_lines.extend([
                "",
                "## Error Breakdown by Category",
            ])
            for category, count in error_stats['by_category'].items():
                report_lines.append(f"- {category}: {count}")

        # Add recommendations
        if health.recommendations:
            report_lines.extend([
                "",
                "## Recommendations",
            ])
            for rec in health.recommendations:
                report_lines.append(f"- {rec}")

        # Add resource details
        resource_report = self.resource_manager.generate_resource_report()
        report_lines.extend([
            "",
            "## Detailed Resource Information",
            "",
            resource_report.split('\n', 2)[2]  # Skip the header
        ])

        return "\n".join(report_lines)

    def save_health_report(self, filepath: str) -> None:
        """Save system health report to file."""
        ensure_directory_exists(os.path.dirname(filepath))

        report = self.generate_health_report()

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)

        self.logger.info(f"System health report saved to: {filepath}")

    def cleanup_and_shutdown(self) -> None:
        """Perform complete cleanup and shutdown."""
        self.logger.info("Initiating system cleanup and shutdown...")

        # Generate final reports
        try:
            reports_dir = "reports/ci-simulation/shutdown"
            ensure_directory_exists(reports_dir)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Save error report
            error_report_path = f"{reports_dir}/error_report_{timestamp}.md"
            self.error_handler.save_error_report(error_report_path)

            # Save health report
            health_report_path = f"{reports_dir}/health_report_{timestamp}.md"
            self.save_health_report(health_report_path)

            # Save resource report
            resource_report_path = f"{reports_dir}/resource_report_{timestamp}.md"
            self.resource_manager.save_resource_report(resource_report_path)

        except Exception as e:
            self.logger.error(f"Error saving shutdown reports: {e}")

        # Perform cleanup
        self.resource_manager.cleanup_all()

        self.logger.info("System cleanup and shutdown completed")

    def get_recovery_suggestions(self, error_category: ErrorCategory) -> List[str]:
        """Get recovery suggestions for a specific error category."""

        suggestions = []

        if error_category == ErrorCategory.RESOURCE:
            usage = self.resource_manager.get_resource_usage()

            if usage.memory_percent > 70:
                suggestions.append("Consider reducing memory usage or increasing available memory")

            if usage.disk_percent > 80:
                suggestions.append("Clean up temporary files or increase available disk space")

            suggestions.extend([
                "Run resource cleanup: cleanup_temp_files()",
                "Monitor resource usage during execution",
                "Consider reducing parallelism or batch sizes"
            ])

        elif error_category == ErrorCategory.ENVIRONMENT:
            suggestions.extend([
                "Check system dependencies installation",
                "Verify Python version compatibility",
                "Ensure virtual environment is properly activated",
                "Check environment variables configuration"
            ])

        elif error_category == ErrorCategory.DEPENDENCY:
            suggestions.extend([
                "Run: pip install -r requirements.txt",
                "Check for package version conflicts",
                "Consider using a fresh virtual environment",
                "Verify package availability in current environment"
            ])

        return suggestions


# Global error recovery system instance
_error_recovery_system: Optional[ErrorRecoverySystem] = None


def get_error_recovery_system(config: Dict[str, Any] = None) -> ErrorRecoverySystem:
    """Get or create the global error recovery system instance."""
    global _error_recovery_system

    if _error_recovery_system is None:
        _error_recovery_system = ErrorRecoverySystem(config)

    return _error_recovery_system
