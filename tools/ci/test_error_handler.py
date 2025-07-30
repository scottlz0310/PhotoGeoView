"""
Test suite for ErrorHandler implementation

This module tests the comprehensive error handling and recovery functionality
of the CI simulation tool.

Author: Kiro (AI Integration and Quality Assurance)
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add the tools/ci directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from error_handler import (
    Entext,
    ErrorCategory,
    ErrorHandler,
    RecoveryAction,
    RecoveryStrategy,
)
from interfaces import (
    CheckerError,
    CISimulationError,
    ConfigurationError,
    DependencyError,
    EnvironmentError,
)
from models import CheckStatus, SeverityLevel


class TestErrorHandler:
    """Test cases for ErrorHandler class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            "max_retry_attempts": 2,
            "retry_delay": 0.1,
            "auto_recovery_enabled": True,
        }
        self.handler = ErrorHandler(self.config)

    def test_initialization(self):
        """Test ErrorHandler initialization."""
        assert self.handler.max_retry_attempts == 2
        assert self.handler.retry_delay == 0.1
        assert self.handler.auto_recovery_enabled is True
        assert len(self.handler.recovery_strategies) > 0
        assert ErrorCategory.ENVIRONMENT in self.handler.recovery_strategies

    def test_error_classification(self):
        """Test error classification functionality."""
        # Test environment error
        env_error = EnvironmentError("Python version not found")
        category = self.handler._classify_error(env_error)
        assert category == ErrorCategory.ENVIRONMENT

        # Test configuration error
        config_error = ConfigurationError("Invalid config file")
        category = self.handler._classify_error(config_error)
        assert category == ErrorCategory.CONFIGURATION

        # Test dependency error
        dep_error = DependencyError(["missing-package"], "Package not found")
        category = self.handler._classify_error(dep_error)
        assert category == ErrorCategory.DEPENDENCY

        # Test timeout error
        import subprocess

        timeout_error = subprocess.TimeoutExpired("cmd", 30)
        category = self.handler._classify_error(timeout_error)
        assert category == ErrorCategory.TIMEOUT

        # Test permission error
        perm_error = PermissionError("Access denied")
        category = self.handler._classify_error(perm_error)
        assert category == ErrorCategory.PERMISSION

        # Test unknown error
        unknown_error = ValueError("Some value error")
        category = self.handler._classify_error(unknown_error)
        assert category == ErrorCategory.UNKNOWN

    def test_severity_determination(self):
        """Test error severity determination."""
        # Test critical severity
        critical_error = SystemExit(1)
        severity = self.handler._determine_severity(
            critical_error, ErrorCategory.EXECUTION
        )
        assert severity == SeverityLevel.CRITICAL

        # Test high severity for environment errors
        env_error = EnvironmentError("Missing dependency")
        severity = self.handler._determine_severity(
            env_error, ErrorCategory.ENVIRONMENT
        )
        assert severity == SeverityLevel.HIGH

        # Test medium severity for configuration errors
        config_error = ConfigurationError("Invalid config")
        severity = self.handler._determine_severity(
            config_error, ErrorCategory.CONFIGURATION
        )
        assert severity == SeverityLevel.MEDIUM

        # Test low severity for timeout errors
        timeout_error = Exception("Timeout")
        severity = self.handler._determine_severity(
            timeout_error, ErrorCategory.TIMEOUT
        )
        assert severity == SeverityLevel.LOW

    @patch("tools.ci.error_handler.is_tool_available")
    def test_environment_info_gathering(self, mock_is_tool_available):
        """Test environment information gathering."""
        mock_is_tool_available.return_value = True

        env_info = self.handler._gather_environment_info()

        assert "python_version" in env_info
        assert "platform" in env_info
        assert "cwd" in env_info
        assert "available_tools" in env_info
        assert "timestamp" in env_info

        # Check that tool availability was checked
        assert mock_is_tool_available.called

    def test_handle_error_basic(self):
        """Test basic error handling functionality."""
        test_error = ValueError("Test error")

        error_context = self.handler.handle_error(
            error=test_error, component="test_component", operation="test_operation"
        )

        assert error_context.error == test_error
        assert error_context.component == "test_component"
        assert error_context.operation == "test_operation"
        assert error_context.category == ErrorCategory.UNKNOWN
        assert error_context.severity == SeverityLevel.MEDIUM
        assert len(self.handler.error_history) == 1

    def test_handle_error_with_context(self):
        """Test error handling with additional context."""
        test_error = EnvironmentError("Missing Qt")
        context = {"python_version": "3.9", "test_type": "gui"}

        error_context = self.handler.handle_error(
            error=test_error,
            component="qt_manager",
            operation="setup_display",
            context=context,
        )

        assert error_context.category == ErrorCategory.ENVIRONMENT
        assert error_context.severity == SeverityLevel.HIGH
        assert "python_version" in error_context.environment_info
        assert "test_type" in error_context.environment_info

    @patch("tools.ci.error_handler.ErrorHandler._attempt_recovery")
    def test_auto_recovery_enabled(self, mock_attempt_recovery):
        """Test that auto recovery is attempted when enabled."""
        self.handler.auto_recovery_enabled = True
        test_error = DependencyError(["missing-pkg"], "Missing package")

        self.handler.handle_error(
            error=test_error, component="test_component", operation="test_operation"
        )

        mock_attempt_recovery.assert_called_once()

    @patch("tools.ci.error_handler.ErrorHandler._attempt_recovery")
    def test_auto_recovery_disabled(self, mock_attempt_recovery):
        """Test that auto recovery is not attempted when disabled."""
        self.handler.auto_recovery_enabled = False
        test_error = DependencyError(["missing-pkg"], "Missing package")

        self.handler.handle_error(
            error=test_error, component="test_component", operation="test_operation"
        )

        mock_attempt_recovery.assert_not_called()

    def test_recovery_attempt_limit(self):
        """Test that recovery attempts are limited."""
        # Create a mock error context
        error_context = ErrorContext(
            error=DependencyError(["pkg1", "pkg2"], "Missing packages"),
            category=ErrorCategory.DEPENDENCY,
            severity=SeverityLevel.HIGH,
            component="test_component",
            operation="test_operation",
        )

        # Mock recovery strategies that always fail
        mock_strategy = RecoveryAction(
            strategy=RecoveryStrategy.AUTO_FIX,
            description="Mock strategy",
            action_function=lambda ctx, **kwargs: False,
        )

        self.handler.recovery_strategies[ErrorCategory.DEPENDENCY] = [mock_strategy] * 5

        # Attempt recovery
        self.handler._attempt_recovery(error_context)

        # Should be limited by max_retry_attempts
        assert len(error_context.recovery_attempts) <= self.handler.max_retry_attempts

    @patch("tools.ci.error_handler.run_command")
    def test_install_dependencies_success(self, mock_run_command):
        """Test successful dependency installation."""
        mock_run_command.return_value = (0, "Successfully installed", "")

        error_context = ErrorContext(
            error=DependencyError(["pytest", "black"], "Missing packages"),
            category=ErrorCategory.DEPENDENCY,
            severity=SeverityLevel.HIGH,
            component="test_component",
            operation="test_operation",
        )

        result = self.handler._install_dependencies(error_context)
        assert result is True
        mock_run_command.assert_called_once()

    @patch("tools.ci.error_handler.run_command")
    def test_install_dependencies_failure(self, mock_run_command):
        """Test failed dependency installation."""
        mock_run_command.return_value = (1, "", "Installation failed")

        error_context = ErrorContext(
            error=DependencyError(["nonexistent-package"], "Missing package"),
            category=ErrorCategory.DEPENDENCY,
            severity=SeverityLevel.HIGH,
            component="test_component",
            operation="test_operation",
        )

        result = self.handler._install_dependencies(error_context)
        assert result is False

    @patch("os.path.exists")
    @patch("shutil.rmtree")
    @patch("os.remove")
    @patch("os.listdir")
    def test_cleanup_resources(
        self, mock_listdir, mock_remove, mock_rmtree, mock_exists
    ):
        """Test resource cleanup functionality."""
        mock_exists.return_value = True
        mock_listdir.return_value = ["ci_simulation_temp", "other_file"]

        error_context = ErrorContext(
            error=MemoryError("Out of memory"),
            category=ErrorCategory.RESOURCE,
            severity=SeverityLevel.LOW,
            component="test_component",
            operation="test_operation",
        )

        result = self.handler._cleanup_resources(error_context)
        assert result is True

    def test_skip_and_continue(self):
        """Test skip and continue recovery strategy."""
        error_context = ErrorContext(
            error=Exception("Some error"),
            category=ErrorCategory.EXECUTION,
            severity=SeverityLevel.MEDIUM,
            component="test_component",
            operation="test_operation",
        )

        result = self.handler._skip_and_continue(error_context)
        assert result is True

    def test_error_report_generation(self):
        """Test error report generation."""
        # Add some test errors
        errors = [
            ErrorContext(
                error=EnvironmentError("Missing Qt"),
                category=ErrorCategory.ENVIRONMENT,
                severity=SeverityLevel.HIGH,
                component="qt_manager",
                operation="setup_display",
            ),
            ErrorContext(
                error=DependencyError(["pytest"], "Missing pytest"),
                category=ErrorCategory.DEPENDENCY,
                severity=SeverityLevel.HIGH,
                component="test_runner",
                operation="run_tests",
            ),
        ]

        report = self.handler.generate_error_report(errors)

        assert "CI Simulation Error Report" in report
        assert "Total Errors: 2" in report
        assert "environment: 1" in report
        assert "dependency: 1" in report
        assert "qt_manager.setup_display" in report
        assert "test_runner.run_tests" in report
        assert "Troubleshooting Guidance" in report

    def test_error_report_empty(self):
        """Test error report generation with no errors."""
        report = self.handler.generate_error_report([])
        assert report == "No errors to report."

    def test_troubleshooting_guidance(self):
        """Test troubleshooting guidance generation."""
        # Test environment error guidance
        env_error = ErrorContext(
            error=EnvironmentError("Missing Qt"),
            category=ErrorCategory.ENVIRONMENT,
            severity=SeverityLevel.HIGH,
            component="qt_manager",
            operation="setup_display",
        )

        guidance = self.handler._get_troubleshooting_guidance(env_error)
        assert len(guidance) > 0
        assert any("system dependencies" in g for g in guidance)
        assert any("Python version" in g for g in guidance)

        # Test dependency error guidance
        dep_error = ErrorContext(
            error=DependencyError(["pytest"], "Missing pytest"),
            category=ErrorCategory.DEPENDENCY,
            severity=SeverityLevel.HIGH,
            component="test_runner",
            operation="run_tests",
        )

        guidance = self.handler._get_troubleshooting_guidance(dep_error)
        assert len(guidance) > 0
        assert any("requirements.txt" in g for g in guidance)
        assert any("virtual environment" in g for g in guidance)

    def test_error_statistics(self):
        """Test error statistics generation."""
        # Add test errors to history
        self.handler.error_history = [
            ErrorContext(
                error=EnvironmentError("Error 1"),
                category=ErrorCategory.ENVIRONMENT,
                severity=SeverityLevel.HIGH,
                component="comp1",
                operation="op1",
                resolved=True,
            ),
            ErrorContext(
                error=DependencyError(["pkg"], "Error 2"),
                category=ErrorCategory.DEPENDENCY,
                severity=SeverityLevel.HIGH,
                component="comp2",
                operation="op2",
                resolved=False,
            ),
            ErrorContext(
                error=Exception("Error 3"),
                category=ErrorCategory.EXECUTION,
                severity=SeverityLevel.MEDIUM,
                component="comp1",
                operation="op3",
                resolved=True,
            ),
        ]

        stats = self.handler.get_error_statistics()

        assert stats["total_errors"] == 3
        assert stats["resolved_errors"] == 2
        assert stats["recovery_success_rate"] == 2 / 3
        assert stats["by_category"]["environment"] == 1
        assert stats["by_category"]["dependency"] == 1
        assert stats["by_category"]["execution"] == 1
        assert stats["by_severity"]["high"] == 2
        assert stats["by_severity"]["medium"] == 1
        assert stats["by_component"]["comp1"] == 2
        assert stats["by_component"]["comp2"] == 1

    def test_error_statistics_empty(self):
        """Test error statistics with no errors."""
        stats = self.handler.get_error_statistics()
        assert stats["total_errors"] == 0

    def test_clear_error_history(self):
        """Test clearing error history."""
        # Add a test error
        self.handler.handle_error(
            error=ValueError("Test error"),
            component="test_component",
            operation="test_operation",
        )

        assert len(self.handler.error_history) == 1

        self.handler.clear_error_history()
        assert len(self.handler.error_history) == 0

    def test_save_error_report(self):
        """Test saving error report to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = os.path.join(temp_dir, "error_report.md")

            # Add a test error
            self.handler.handle_error(
                error=ValueError("Test error"),
                component="test_component",
                operation="test_operation",
            )

            self.handler.save_error_report(report_path)

            assert os.path.exists(report_path)

            with open(report_path, "r", encoding="utf-8") as f:
                content = f.read()
                assert "CI Simulation Error Report" in content
                assert "test_component.test_operation" in content


class TestRecoveryAction:
    """Test cases for RecoveryAction class."""

    def test_recovery_action_creation(self):
        """Test RecoveryAction creation."""
        action = RecoveryAction(
            strategy=RecoveryStrategy.RETRY,
            description="Retry with timeout",
            success_probability=0.7,
            estimated_time=10.0,
        )

        assert action.strategy == RecoveryStrategy.RETRY
        assert action.description == "Retry with timeout"
        assert action.success_probability == 0.7
        assert action.estimated_time == 10.0
        assert action.user_confirmation_required is False


class TestErrorContext:
    """Test cases for ErrorContext class."""

    def test_error_context_creation(self):
        """Test ErrorContext creation."""
        error = ValueError("Test error")
        context = ErrorContext(
            error=error,
            category=ErrorCategory.EXECUTION,
            severity=SeverityLevel.MEDIUM,
            component="test_component",
            operation="test_operation",
        )

        assert context.error == error
        assert context.category == ErrorCategory.EXECUTION
        assert context.severity == SeverityLevel.MEDIUM
        assert context.component == "test_component"
        assert context.operation == "test_operation"
        assert context.resolved is False
        assert len(context.recovery_attempts) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
