"""
Unit tests for check orchestrator and error handling components.
"""

import pytest
import os
import time
import threading
from unittest.mock import Mock, patch, MagicMock, call
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

# Import components
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'tools', 'ci'))

from check_orchestrator import CheckOrchestrator
from error_handler import ErrorHandler
from error_recovery_system import ErrorRecoverySystem
from models import CheckResult, CheckStatus, CheckTask, SimulationResult
from interfaces import CheckerInterface, CheckerError, EnvironmentError, DependencyError


class MockChecker(CheckerInterface):
    """Mock checker for testing."""

    def __init__(self, config, name="mock_checker", check_type="test",
                 dependencies=None, available=True, duration=1.0, status=CheckStatus.SUCCESS):
        super().__init__(config)
        self._name = name
        self._check_type = check_type
        self._dependencies = dependencies or []
        self._available = available
        self._duration = duration
        self._status = status
        self.run_count = 0

    @property
    def name(self):
        return self._name

    @property
    def check_type(self):
        return self._check_type

    @property
    def dependencies(self):
        return self._dependencies

    def is_available(self):
        return self._available

    def run_check(self, **kwargs):
        self.run_count += 1
        time.sleep(self._duration)  # Simulate work

        if self._status == CheckStatus.FAILURE:
            raise CheckerError(self.name, "Mock check failed")

        return CheckResult(
            name=self.name,
            status=self._status,
            duration=self._duration,
            output=f"Mock check {self.name} completed"
        )


class TestCheckOrchestrator:
    """Test cases for CheckOrchestrator."""

    def test_orchestrator_creation(self, sample_config):
        """Test CheckOrchestrator creation."""
        orchestrator = CheckOrchestrator(sample_config)

        assert orchestrator.config == sample_config
        assert orchestrator.max_parallel_jobs > 0
        assert orchestrator.timeout > 0
        assert isinstance(orchestrator.checkers, dict)

    def test_register_checker(self, sample_config):
        """Test registering a checker."""
        orchestrator = CheckOrchestrator(sample_config)
        checker = MockChecker(sample_config, "test_checker", "test")

        orchestrator.register_checker("test", checker)

        assert "test" in orchestrator.checkers
        assert orchestrator.checkers["test"] == checker

    def test_execute_single_check(self, sample_config):
        """Test executing a single check."""
        orchestrator = CheckOrchestrator(sample_config)
        checker = MockChecker(sample_config, "single_check", "test")
        orchestrator.register_checker("test", checker)

        task = CheckTask("single_task", "test")
        results = orchestrator.execute_checks([task])

        assert len(results) == 1
        assert "single_task" in results
        assert results["single_task"].status == CheckStatus.SUCCESS
        assert checker.run_count == 1

    def test_execute_multiple_checks_sequential(self, sample_config):
        """Test executing multiple checks sequentially."""
        orchestrator = CheckOrchestrator(sample_config)
        orchestrator.max_parallel_jobs = 1  # Force sequential execution

        checker1 = MockChecker(sample_config, "check1", "test1")
        checker2 = MockChecker(sample_config, "check2", "test2")

        orchestrator.register_checker("test1", checker1)
        orchestrator.register_checker("test2", checker2)

        tasks = [
            CheckTask("task1", "test1"),
            CheckTask("task2", "test2")
        ]

        start_time = time.time()
        results = orchestrator.execute_checks(tasks)
        end_time = time.time()

        assert len(results) == 2
        assert "task1" in results
        assert "task2" in results
        assert results["task1"].status == CheckStatus.SUCCESS
        assert results["task2"].status == CheckStatus.SUCCESS

        # Should take at least 2 seconds (1 second each, sequential)
        assert end_time - start_time >= 2.0

    def test_execute_multiple_checks_parallel(self, sample_config):
        """Test executing multiple checks in parallel."""
        orchestrator = CheckOrchestrator(sample_config)
        orchestrator.max_parallel_jobs = 2  # Allow parallel execution

        checker1 = MockChecker(sample_config, "check1", "test1", duration=1.0)
        checker2 = MockChecker(sample_config, "check2", "test2", duration=1.0)

        orchestrator.register_checker("test1", checker1)
        orchestrator.register_checker("test2", checker2)

        tasks = [
            CheckTask("task1", "test1"),
            CheckTask("task2", "test2")
        ]

        start_time = time.time()
        results = orchestrator.execute_checks(tasks)
        end_time = time.time()

        assert len(results) == 2
        assert results["task1"].status == CheckStatus.SUCCESS
        assert results["task2"].status == CheckStatus.SUCCESS

        # Should take less than 2 seconds (parallel execution)
        assert end_time - start_time < 1.5

    def test_resolve_dependencies_simple(self, sample_config):
        """Test simple dependency resolution."""
        orchestrator = CheckOrchestrator(sample_config)

        # Create checkers with dependencies
        checker1 = MockChecker(sample_config, "check1", "test1", dependencies=[])
        checker2 = MockChecker(sample_config, "check2", "test2", dependencies=["test1"])
        checker3 = MockChecker(sample_config, "check3", "test3", dependencies=["test2"])

        orchestrator.register_checker("test1", checker1)
        orchestrator.register_checker("test2", checker2)
        orchestrator.register_checker("test3", checker3)

        task_names = ["test3", "tetest2"]  # Intentionally out of order
        resolved = orchestrator.resolve_dependencies(task_names)

        # Should be in dependency order: test1, test2, test3
        assert resolved == ["test1", "test2", "test3"]

    def test_resolve_dependencies_complex(self, sample_config):
        """Test complex dependency resolution."""
        orchestrator = CheckOrchestrator(sample_config)

        # Create a more complex dependency graph
        checkers = {
            "a": MockChecker(sample_config, "a", "a", dependencies=[]),
            "b": MockChecker(sample_config, "b", "b", dependencies=["a"]),
            "c": MockChecker(sample_config, "c", "c", dependencies=["a"]),
            "d": MockChecker(sample_config, "d", "d", dependencies=["b", "c"]),
            "e": MockChecker(sample_config, "e", "e", dependencies=["d"])
        }

        for check_type, checker in checkers.items():
            orchestrator.register_checker(check_type, checker)

        task_names = ["e", "d", "c", "b", "a"]  # Reverse order
        resolved = orchestrator.resolve_dependencies(task_names)

        # Verify dependency order is respected
        a_index = resolved.index("a")
        b_index = resolved.index("b")
        c_index = resolved.index("c")
        d_index = resolved.index("d")
        e_index = resolved.index("e")

        assert a_index < b_index  # a before b
        assert a_index < c_index  # a before c
        assert b_index < d_index  # b before d
        assert c_index < d_index  # c before d
        assert d_index < e_index  # d before e

    def test_resolve_dependencies_circular(self, sample_config):
        """Test circular dependency detection."""
        orchestrator = CheckOrchestrator(sample_config)

        # Create circular dependency
        checker1 = MockChecker(sample_config, "check1", "test1", dependencies=["test2"])
        checker2 = MockChecker(sample_config, "check2", "test2", dependencies=["test1"])

        orchestrator.register_checker("test1", checker1)
        orchestrator.register_checker("test2", checker2)

        with pytest.raises(ValueError, match="Circular dependency detected"):
            orchestrator.resolve_dependencies(["test1", "test2"])

    def test_execute_checks_with_dependencies(self, sample_config):
        """Test executing checks with dependencies."""
        orchestrator = CheckOrchestrator(sample_config)

        checker1 = MockChecker(sample_config, "base", "base", dependencies=[])
        checker2 = MockChecker(sample_config, "dependent", "dependent", dependencies=["base"])

        orchestrator.register_checker("base", checker1)
        orchestrator.register_checker("dependent", checker2)

        tasks = [
            CheckTask("dependent_task", "dependent"),
            CheckTask("base_task", "base")  # Intentionally out of order
        ]

        results = orchestrator.execute_checks(tasks)

        assert len(results) == 2
        assert results["base_task"].status == CheckStatus.SUCCESS
        assert results["dependent_task"].status == CheckStatus.SUCCESS

        # Base should have run before dependent
        assert checker1.run_count == 1
        assert checker2.run_count == 1

    def test_execute_checks_with_failure(self, sample_config):
        """Test executing checks when one fails."""
        orchestrator = CheckOrchestrator(sample_config)

        checker1 = MockChecker(sample_config, "success", "success", status=CheckStatus.SUCCESS)
        checker2 = MockChecker(sample_config, "failure", "failure", status=CheckStatus.FAILURE)

        orchestrator.register_checker("success", checker1)
        orchestrator.register_checker("failure", checker2)

        tasks = [
            CheckTask("success_task", "success"),
            CheckTask("failure_task", "failure")
        ]

        results = orchestrator.execute_checks(tasks)

        assert len(results) == 2
        assert results["success_task"].status == CheckStatus.SUCCESS
        assert results["failure_task"].status == CheckStatus.FAILURE

    def test_execute_checks_with_timeout(self, sample_config):
        """Test executing checks with timeout."""
        orchestrator = CheckOrchestrator(sample_config)
        orchestrator.timeout = 0.5  # Very short timeout

        # Create a slow checker
        slow_checker = MockChecker(sample_config, "slow", "slow", duration=2.0)
        orchestrator.register_checker("slow", slow_checker)

        task = CheckTask("slow_task", "slow", timeout=0.5)
        results = orchestrator.execute_checks([task])

        assert len(results) == 1
        assert results["slow_task"].status == CheckStatus.FAILURE
        assert "timeout" in results["slow_task"].errors[0].lower()

    def test_execute_checks_unavailable_checker(self, sample_config):
        """Test executing checks with unavailable checker."""
        orchestrator = CheckOrchestrator(sample_config)

        unavailable_checker = MockChecker(
            sample_config, "unavailable", "unavailable", available=False
        )
        orchestrator.register_checker("unavailable", unavailable_checker)

        task = CheckTask("unavailable_task", "unavailable")
        results = orchestrator.execute_checks([task])

        assert len(results) == 1
        assert results["unavailable_task"].status == CheckStatus.SKIPPED
        assert "not available" in results["unavailable_task"].output.lower()

    def test_execute_checks_priority_ordering(self, sample_config):
        """Test that checks are executed in priority order."""
        orchestrator = CheckOrchestrator(sample_config)
        orchestrator.max_parallel_jobs = 1  # Force sequential execution

        execution_order = []

        def create_tracking_checker(name, priority):
            checker = MockChecker(sample_config, name, name, duration=0.1)
            original_run = checker.run_check

            def tracked_run(**kwargs):
                execution_order.append(name)
                return original_run(**kwargs)

            checker.run_check = tracked_run
            return checker

        # Create checkers
        low_priority = create_tracking_checker("low", 1)
        high_priority = create_tracking_checker("high", 10)
        medium_priority = create_tracking_checker("medium", 5)

        orchestrator.register_checker("low", low_priority)
        orchestrator.register_checker("high", high_priority)
        orchestrator.register_checker("medium", medium_priority)

        tasks = [
            CheckTask("low_task", "low", priority=1),
            CheckTask("high_task", "high", priority=10),
            CheckTask("medium_task", "medium", priority=5)
        ]

        orchestrator.execute_checks(tasks)

        # Should execute in priority order: high, medium, low
        assert execution_order == ["high", "medium", "low"]


class TestErrorHandler:
    """Test cases for ErrorHandler."""

    def test_error_handler_creation(self):
        """Test ErrorHandler creation."""
        handler = ErrorHandler()

        assert handler.error_counts == {}
        assert handler.recovery_strategies == {}

    def test_handle_checker_error(self):
        """Test handling checker errors."""
        handler = ErrorHandler()

        error = CheckerError("test_checker", "Test error message")
        result = handler.handle_checker_error(error)

        assert isinstance(result, CheckResult)
        assert result.status == CheckStatus.FAILURE
        assert result.name == "test_checker"
        assert "Test error message" in result.errors[0]

    def test_handle_environment_error(self):
        """Test handling environment errors."""
        handler = ErrorHandler()

        error = EnvironmentError("Environment setup failed")
        result = handler.handle_environment_error(error)

        assert isinstance(result, CheckResult)
        assert result.status == CheckStatus.FAILURE
        assert "Environment setup failed" in result.errors[0]

    def test_handle_dependency_error(self):
        """Test handling dependency errors."""
        handler = ErrorHandler()

        error = DependencyError(["pytest", "black"], "Missing dependencies")
        result = handler.handle_dependency_error(error)

        assert isinstance(result, CheckResult)
        assert result.status == CheckStatus.FAILURE
        assert "pytest" in result.errors[0]
        assert "black" in result.errors[0]
        assert len(result.suggestions) > 0

    def test_handle_timeout_error(self):
        """Test handling timeout errors."""
        handler = ErrorHandler()

        result = handler.handle_timeout_error("slow_check", 30.0)

        assert isinstance(result, CheckResult)
        assert result.status == CheckStatus.FAILURE
        assert result.name == "slow_check"
        assert "timeout" in result.errors[0].lower()
        assert "30.0" in result.errors[0]

    def test_handle_generic_exception(self):
        """Test handling generic exceptions."""
        handler = ErrorHandler()

        exception = ValueError("Generic error")
        result = handler.handle_generic_exception("test_check", exception)

        assert isinstance(result, CheckResult)
        assert result.status == CheckStatus.FAILURE
        assert result.name == "test_check"
        assert "Generic error" in result.errors[0]

    def test_error_count_tracking(self):
        """Test error count tracking."""
        handler = ErrorHandler()

        # Handle multiple errors for the same checker
        error1 = CheckerError("test_checker", "Error 1")
        error2 = CheckerError("test_checker", "Error 2")

        handler.handle_checker_error(error1)
        handler.handle_checker_error(error2)

        assert handler.error_counts["test_checker"] == 2

    def test_get_error_summary(self):
        """Test getting error summary."""
        handler = ErrorHandler()

        # Generate some errors
        handler.handle_checker_error(CheckerError("checker1", "Error 1"))
        handler.handle_checker_error(CheckerError("checker1", "Error 2"))
        handler.handle_checker_error(CheckerError("checker2", "Error 3"))

        summary = handler.get_error_summary()

        assert "checker1" in summary
        assert "checker2" in summary
        assert "2" in summary  # checker1 error count
        assert "1" in summary  # checker2 error count

    def test_register_recovery_strategy(self):
        """Test registering recovery strategies."""
        handler = ErrorHandler()

        def custom_recovery(error):
            return CheckResult("recovered", CheckStatus.SUCCESS, 0.0)

        handler.register_recovery_strategy(CheckerError, custom_recovery)

        assert CheckerError in handler.recovery_strategies
        assert handler.recovery_strategies[CheckerError] == custom_recovery

    def test_apply_recovery_strategy(self):
        """Test applying recovery strategies."""
        handler = ErrorHandler()

        def recovery_strategy(error):
            return CheckResult("recovered", CheckStatus.WARNING, 0.0,
                             output="Recovered from error")

        handler.register_recovery_strategy(CheckerError, recovery_strategy)

        error = CheckerError("test_checker", "Test error")
        result = handler.handle_checker_error(error)

        assert result.status == CheckStatus.WARNING
        assert result.name == "recovered"
        assert "Recovered from error" in result.output


class TestErrorRecoverySystem:
    """Test cases for ErrorRecoverySystem."""

    def test_error_recovery_system_creation(self):
        """Test ErrorRecoverySystem creation."""
        recovery_system = ErrorRecoverySystem()

        assert recovery_system.max_retries == 3
        assert recovery_system.retry_delay == 1.0
        assert recovery_system.retry_counts == {}

    def test_should_retry_first_attempt(self):
        """Test retry decision for first attempt."""
        recovery_system = ErrorRecoverySystem()

        error = CheckerError("test_checker", "Temporary error")
        should_retry = recovery_system.should_retry("test_task", error)

        assert should_retry is True

    def test_should_retry_max_attempts_reached(self):
        """Test retry decision when max attempts reached."""
        recovery_system = ErrorRecoverySystem()
        recovery_system.max_retries = 2

        # Simulate multiple failures
        recovery_system.retry_counts["test_task"] = 2

        error = CheckerError("test_checker", "Persistent error")
        should_retry = recovery_system.should_retry("test_task", error)

        assert should_retry is False

    def test_should_retry_non_retryable_error(self):
        """Test retry decision for non-retryable errors."""
        recovery_system = ErrorRecoverySystem()

        # Configuration errors are typically not retryable
        error = ValueError("Invalid configuration")
        should_retry = recovery_system.should_retry("test_task", error)

        assert should_retry is False

    def test_execute_with_retry_success_first_attempt(self, sample_config):
        """Test retry execution with success on first attempt."""
        recovery_system = ErrorRecoverySystem()

        checker = MockChecker(sample_config, "success_checker", "test")
        task = CheckTask("test_task", "test")

        result = recovery_system.execute_with_retry(task, checker)

        assert result.status == CheckStatus.SUCCESS
        assert checker.run_count == 1
        assert recovery_system.retry_counts.get("test_task", 0) == 0

    def test_execute_with_retry_success_after_failure(self, sample_config):
        """Test retry execution with success after initial failure."""
        recovery_system = ErrorRecoverySystem()
        recovery_system.retry_delay = 0.1  # Speed up test

        # Create a checker that fails first time, succeeds second time
        checker = MockChecker(sample_config, "flaky_checker", "test")
        original_run = checker.run_check

        def flaky_run(**kwargs):
            if checker.run_count == 0:
                checker.run_count += 1
                raise CheckerError("flaky_checker", "Temporary failure")
            else:
                return original_run(**kwargs)

        checker.run_check = flaky_run
        checker.run_count = 0  # Reset count

        task = CheckTask("flaky_task", "test")
        result = recovery_system.execute_with_retry(task, checker)

        assert result.status == CheckStatus.SUCCESS
        assert recovery_system.retry_counts["flaky_task"] == 1

    def test_execute_with_retry_max_attempts_exceeded(self, sample_config):
        """Test retry execution when max attempts are exceeded."""
        recovery_system = ErrorRecoverySystem()
        recovery_system.max_retries = 2
        recovery_system.retry_delay = 0.1  # Speed up test

        # Create a checker that always fails
        checker = MockChecker(sample_config, "failing_checker", "test",
                            status=CheckStatus.FAILURE)

        task = CheckTask("failing_task", "test")
        result = recovery_system.execute_with_retry(task, checker)

        assert result.status == CheckStatus.FAILURE
        assert checker.run_count == 3  # Initial attempt + 2 retries
        assert recovery_system.retry_counts["failing_task"] == 2

    def test_reset_retry_count(self):
        """Test resetting retry count."""
        recovery_system = ErrorRecoverySystem()

        recovery_system.retry_counts["test_task"] = 5
        recovery_system.reset_retry_count("test_task")

        assert recovery_system.retry_counts["test_task"] == 0

    def test_get_retry_statistics(self):
        """Test getting retry statistics."""
        recovery_system = ErrorRecoverySystem()

        recovery_system.retry_counts = {
            "task1": 2,
            "task2": 0,
            "task3": 1
        }

        stats = recovery_system.get_retry_statistics()

        assert stats["total_tasks"] == 3
        assert stats["tasks_with_retries"] == 2
        assert stats["total_retries"] == 3
        assert stats["average_retries"] == 1.0

    def test_is_retryable_error(self):
        """Test error retryability classification."""
        recovery_system = ErrorRecoverySystem()

        # Retryable errors
        assert recovery_system.is_retryable_error(CheckerError("test", "Network error"))
        assert recovery_system.is_retryable_error(EnvironmentError("Temporary failure"))

        # Non-retryable errors
        assert not recovery_system.is_retryable_error(ValueError("Invalid config"))
        assert not recovery_system.is_retryable_error(TypeError("Type mismatch"))

    def test_apply_backoff_strategy(self):
        """Test backoff strategy application."""
        recovery_system = ErrorRecoverySystem()
        recovery_system.retry_delay = 1.0

        # Test exponential backoff
        delay1 = recovery_system._calculate_retry_delay(1)
        delay2 = recovery_system._calculate_retry_delay(2)
        delay3 = recovery_system._calculate_retry_delay(3)

        assert delay1 == 1.0
        assert delay2 == 2.0
        assert delay3 == 4.0


class TestIntegratedErrorHandling:
    """Integration tests for error handling components."""

    def test_orchestrator_with_error_handler(self, sample_config):
        """Test orchestrator integration with error handler."""
        orchestrator = CheckOrchestrator(sample_config)
        error_handler = ErrorHandler()

        # Register error handler with orchestrator
        orchestrator.error_handler = error_handler

        # Create a failing checker
        failing_checker = MockChecker(sample_config, "failing", "failing",
                                    status=CheckStatus.FAILURE)
        orchestrator.register_checker("failing", failing_checker)

        task = CheckTask("failing_task", "failing")
        results = orchestrator.execute_checks([task])

        assert len(results) == 1
        assert results["failing_task"].status == CheckStatus.FAILURE
        assert error_handler.error_counts.get("failing", 0) > 0

    def test_orchestrator_with_recovery_system(self, sample_config):
        """Test orchestrator integration with recovery system."""
        orchestrator = CheckOrchestrator(sample_config)
        recovery_system = ErrorRecoverySystem()
        recovery_system.retry_delay = 0.1  # Speed up test

        # Register recovery system with orchestrator
        orchestrator.recovery_system = recovery_system

        # Create a flaky checker that succeeds on retry
        flaky_checker = MockChecker(sample_config, "flaky", "flaky")
        original_run = flaky_checker.run_check

        def flaky_run(**kwargs):
            if flaky_checker.run_count == 1:  # Fail first time
                raise CheckerError("flaky", "Temporary failure")
            else:
                return original_run(**kwargs)

        flaky_checker.run_check = flaky_run
        orchestrator.register_checker("flaky", flaky_checker)

        task = CheckTask("flaky_task", "flaky")
        results = orchestrator.execute_checks([task])

        assert len(results) == 1
        assert results["flaky_task"].status == CheckStatus.SUCCESS
        assert recovery_system.retry_counts["flaky_task"] > 0

    def test_complete_error_handling_workflow(self, sample_config):
        """Test complete error handling workflow."""
        orchestrator = CheckOrchestrator(sample_config)
        error_handler = ErrorHandler()
        recovery_system = ErrorRecoverySystem()
        recovery_system.retry_delay = 0.1

        # Wire components together
        orchestrator.error_handler = error_handler
        orchestrator.recovery_system = recovery_system

        # Create various types of checkers
        success_checker = MockChecker(sample_config, "success", "success")
        failing_checker = MockChecker(sample_config, "failing", "failing",
                                    status=CheckStatus.FAILURE)

        # Flaky checker that succeeds on second attempt
        flaky_checker = MockChecker(sample_config, "flaky", "flaky")
        original_run = flaky_checker.run_check

        def flaky_run(**kwargs):
            if flaky_checker.run_count == 1:
                raise CheckerError("flaky", "Temporary failure")
            else:
                return original_run(**kwargs)

        flaky_checker.run_check = flaky_run

        # Register all checkers
        orchestrator.register_checker("success", success_checker)
        orchestrator.register_checker("failing", failing_checker)
        orchestrator.register_checker("flaky", flaky_checker)

        tasks = [
            CheckTask("success_task", "success"),
            CheckTask("failing_task", "failing"),
            CheckTask("flaky_task", "flaky")
        ]

        results = orchestrator.execute_checks(tasks)

        # Verify results
        assert len(results) == 3
        assert results["success_task"].status == CheckStatus.SUCCESS
        assert results["failing_task"].status == CheckStatus.FAILURE
        assert results["flaky_task"].status == CheckStatus.SUCCESS

        # Verify error handling
        assert error_handler.error_counts.get("failing", 0) > 0
        assert recovery_system.retry_counts.get("flaky_task", 0) > 0

        # Verify statistics
        error_summary = error_handler.get_error_summary()
        retry_stats = recovery_system.get_retry_statistics()

        assert "failing" in error_summary
        assert retry_stats["tasks_with_retries"] >= 1
