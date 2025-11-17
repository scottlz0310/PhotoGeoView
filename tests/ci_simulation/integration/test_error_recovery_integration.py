"""
Integration tests for error recovery and system resilience.

These tests verify that the CI simulation tool can handle various
error conditions gracefully and recover when possible.
"""

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add the tools/ci directory to the path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "tools" / "ci"))

from error_handler import ErrorHandler
from error_recovery_system import ErrorRecoverySystem
from models import CheckStatus
from simulator import CISimulator


@pytest.mark.integration
class TestErrorRecoveryIntegration:
    """Integration tests for error recovery system."""

    @pytest.fixture
    def project_with_issues(self, temp_dir):
        """Set up a project with various types of issues."""
        project_dir = Path(temp_dir) / "problematic_project"
        project_dir.mkdir()

        # Create source files with issues
        src_dir = project_dir / "src"
        src_dir.mkdir()

        (src_dir / "__init__.py").write_text("")

        # File with syntax errors
        (src_dir / "syntax_errors.py").write_text(
            """
# This file has syntax errors
def broken_function(
    print("Missing closing parenthesis"
    return "This will cause syntax error"

class BrokenClass
    def __init__(self):  # Missing colon
        pass
"""
        )

        # File with import errors
        (src_dir / "import_errors.py").write_text(
            '''
"""File with import errors."""

import nonexistent_module
from another_nonexistent import something
import os, sys  # Multiple imports on one line

def function_with_import_issues():
    import yet_another_nonexistent
    return "This will fail"
'''
        )

        # File with type errors
        (src_dir / "type_errors.py").write_text(
            '''
"""File with type errors."""

def add_numbers(a, b):  # Missing type annotations
    return a + b

def process_data(data):
    # Type mismatch
    result = add_numbers("string", 123)
    return result.upper()  # Calling string method on int

class TypeErrorClass:
    def __init__(self, value):
        self.value = value

    def get_value(self):
        return self.value.nonexistent_method()  # Method doesn't exist
'''
        )

        # Create test files with failures
        tests_dir = project_dir / "tests"
        tests_dir.mkdir()

        (tests_dir / "__init__.py").write_text("")

        (tests_dir / "test_failures.py").write_text(
            '''
"""Tests that fail in various ways."""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_import_failure():
    """Test that fails due to import error."""
    try:
        from import_errors import function_with_import_issues
        assert False, "Should have failed to import"
    except ImportError:
        pytest.fail("Import error as expected")


def test_assertion_failure():
    """Test with assertion failure."""
    assert 1 == 2, "One does not equal two"


def test_exception_failure():
    """Test that raises an exception."""
    raise ValueError("This test always fails")


def test_timeout_simulation():
    """Test that simulates a timeout."""
    import time
    time.sleep(10)  # This will timeout in most configurations
    assert True


@pytest.mark.flaky
def test_flaky_test():
    """Test that sometimes passes, sometimes fails."""
    import random
    if random.random() < 0.5:
        assert False, "Random failure"
    assert True
'''
        )

        # Create requirements with vulnerable packages
        (project_dir / "requirements.txt").write_text(
            """
# Intentionally vulnerable packages for testing
requests==2.20.0  # Has known vulnerabilities
django==2.0.0     # Has known vulnerabilities
flask==0.12.0     # Has known vulnerabilities

# Normal packages
pytest>=7.0.0
black>=22.0.0
"""
        )

        # Create CI config
        (project_dir / "ci-config.yaml").write_text(
            """
python_versions:
  - "3.10"

timeout: 30  # Short timeout to trigger timeout errors
parallel_jobs: 1
output_dir: "reports"

checkers:
  code_quality:
    enabled: true
    black:
      enabled: true
    isort:
      enabled: true
    flake8:
      enabled: true
    mypy:
      enabled: true

  security:
    enabled: true
    safety:
      enabled: true
    bandit:
      enabled: true

  tests:
    enabled: true
    unit_tests: true
"""
        )

        return project_dir

    def test_syntax_error_recovery(self, project_with_issues):
        """Test recovery from syntax errors."""
        project_dir = project_with_issues

        original_cwd = os.getcwd()
        os.chdir(project_dir)

        try:
            config_path = project_dir / "ci-config.yaml"
            simulator = CISimulator(str(config_path))

            with patch("shutil.which") as mock_which:
                mock_which.return_value = "/usr/bin/tool"

                with patch("subprocess.run") as mock_run:

                    def mock_subprocess_with_syntax_errors(*args, **kwargs):
                        cmd = args[0] if args else kwargs.get("args", [])
                        cmd_str = " ".join(cmd) if isinstance(cmd, list) else str(cmd)

                        # Black fails due to syntax errors
                        if "black" in cmd_str:
                            return Mock(
                                returncode=123,  # Black's syntax error code
                                stdout="",
                                stderr="error: cannot use --safe with --fast\nCannot parse: syntax_errors.py",
                            )

                        # flake8 finds syntax errors
                        elif "flake8" in cmd_str:
                            return Mock(
                                returncode=1,
                                stdout="src/syntax_errors.py:3:1: E999 SyntaxError: invalid syntax\nsrc/syntax_errors.py:7:1: E999 SyntaxError: invalid syntax",
                                stderr="",
                            )

                        # mypy fails on syntax errors
                        elif "mypy" in cmd_str:
                            return Mock(
                                returncode=2,
                                stdout="src/syntax_errors.py:3: error: invalid syntax",
                                stderr="",
                            )

                        # Other tools succeed
                        else:
                            return Mock(returncode=0, stdout="Success", stderr="")

                    mock_run.side_effect = mock_subprocess_with_syntax_errors

                    # Run simulation
                    result = simulator.run(checks=["code_quality"])

                    # Should handle syntax errors gracefully
                    assert isinstance(result, SimulationResult)
                    assert result.overall_status == CheckStatus.FAILURE

                    # Should have captured syntax error details
                    failed_checks = result.failed_checks
                    assert len(failed_checks) > 0

                    # Check error messages contain syntax error information
                    error_messages = []
                    for check in failed_checks:
                        error_messages.extend(check.errors)

                    error_text = " ".join(error_messages).lower()
                    assert "syntax" in error_text or "parse" in error_text

        finally:
            os.chdir(original_cwd)

    def test_import_error_recovery(self, project_with_issues):
        """Test recovery from import errors."""
        project_dir = project_with_issues

        original_cwd = os.getcwd()
        os.chdir(project_dir)

        try:
            config_path = project_dir / "ci-config.yaml"
            simulator = CISimulator(str(config_path))

            with patch("shutil.which") as mock_which:
                mock_which.return_value = "/usr/bin/tool"

                with patch("subprocess.run") as mock_run:

                    def mock_subprocess_with_import_errors(*args, **kwargs):
                        cmd = args[0] if args else kwargs.get("args", [])
                        cmd_str = " ".join(cmd) if isinstance(cmd, list) else str(cmd)

                        # pytest fails due to import errors
                        if "pytest" in cmd_str:
                            return Mock(
                                returncode=1,
                                stdout="",
                                stderr="ImportError: No module named 'nonexistent_module'\nModuleNotFoundError: No module named 'another_nonexistent'",
                            )

                        # mypy finds import errors
                        elif "mypy" in cmd_str:
                            return Mock(
                                returncode=1,
                                stdout="src/import_errors.py:4: error: Cannot find implementation or library stub for module named 'nonexistent_module'",
                                stderr="",
                            )

                        # flake8 finds import style issues
                        elif "flake8" in cmd_str:
                            return Mock(
                                returncode=1,
                                stdout="src/import_errors.py:6:1: E401 multiple imports on one line",
                                stderr="",
                            )

                        # Other tools succeed
                        else:
                            return Mock(returncode=0, stdout="Success", stderr="")

                    mock_run.side_effect = mock_subprocess_with_import_errors

                    # Run simulation
                    result = simulator.run(checks=["code_quality", "tests"])

                    # Should handle import errors gracefully
                    assert result.overall_status == CheckStatus.FAILURE

                    # Should have captured import error details
                    failed_checks = result.failed_checks
                    assert len(failed_checks) > 0

                    # Check error messages contain import error information
                    error_messages = []
                    for check in failed_checks:
                        error_messages.extend(check.errors)

                    error_text = " ".join(error_messages).lower()
                    assert "import" in error_text or "module" in error_text

        finally:
            os.chdir(original_cwd)

    def test_timeout_error_recovery(self, project_with_issues):
        """Test recovery from timeout errors."""
        project_dir = project_with_issues

        original_cwd = os.getcwd()
        os.chdir(project_dir)

        try:
            config_path = project_dir / "ci-config.yaml"
            simulator = CISimulator(str(config_path))

            with patch("shutil.which") as mock_which:
                mock_which.return_value = "/usr/bin/tool"

                with patch("subprocess.run") as mock_run:

                    def mock_subprocess_with_timeout(*args, **kwargs):
                        cmd = args[0] if args else kwargs.get("args", [])
                        cmd_str = " ".join(cmd) if isinstance(cmd, list) else str(cmd)

                        # Simulate timeout for pytest
                        if "pytest" in cmd_str:
                            raise subprocess.TimeoutExpired(cmd, 30)

                        # Other tools succeed quickly
                        else:
                            return Mock(returncode=0, stdout="Success", stderr="")

                    mock_run.side_effect = mock_subprocess_with_timeout

                    # Run simulation
                    result = simulator.run(checks=["tests"])

                    # Should handle timeout gracefully
                    assert result.overall_status == CheckStatus.FAILURE

                    # Should have captured timeout error
                    failed_checks = result.failed_checks
                    assert len(failed_checks) > 0

                    # Check error messages contain timeout information
                    error_messages = []
                    for check in failed_checks:
                        error_messages.extend(check.errors)

                    error_text = " ".join(error_messages).lower()
                    assert "timeout" in error_text

        finally:
            os.chdir(original_cwd)

    def test_dependency_error_recovery(self, project_with_issues):
        """Test recovery from missing dependency errors."""
        project_dir = project_with_issues

        original_cwd = os.getcwd()
        os.chdir(project_dir)

        try:
            config_path = project_dir / "ci-config.yaml"
            simulator = CISimulator(str(config_path))

            with patch("shutil.which") as mock_which:
                # Simulate missing tools
                def mock_which_missing(*args, **kwargs):
                    tool = args[0] if args else None
                    if tool in ["black", "mypy"]:
                        return None  # Tool not found
                    return "/usr/bin/tool"

                mock_which.side_effect = mock_which_missing

                with patch("subprocess.run") as mock_run:
                    mock_run.return_value = Mock(returncode=0, stdout="Success", stderr="")

                    # Run simulation
                    result = simulator.run(checks=["code_quality"])

                    # Should handle missing dependencies gracefully
                    assert isinstance(result, SimulationResult)

                    # Some checks should be skipped due to missing dependencies
                    skipped_checks = result.get_checks_by_status(CheckStatus.SKIPPED)
                    assert len(skipped_checks) > 0

                    # Check that skipped checks mention missing dependencies
                    for check in skipped_checks:
                        assert "not available" in check.output.lower() or "missing" in check.output.lower()

        finally:
            os.chdir(original_cwd)

    def test_flaky_test_retry_recovery(self, project_with_issues):
        """Test retry recovery for flaky tests."""
        project_dir = project_with_issues

        original_cwd = os.getcwd()
        os.chdir(project_dir)

        try:
            config_path = project_dir / "ci-config.yaml"
            simulator = CISimulator(str(config_path))

            # Enable retry system
            simulator.recovery_system = ErrorRecoverySystem()
            simulator.recovery_system.max_retries = 2
            simulator.recovery_system.retry_delay = 0.1  # Speed up test

            with patch("shutil.which") as mock_which:
                mock_which.return_value = "/usr/bin/tool"

                with patch("subprocess.run") as mock_run:
                    call_count = 0

                    def mock_subprocess_flaky(*args, **kwargs):
                        nonlocal call_count
                        cmd = args[0] if args else kwargs.get("args", [])
                        cmd_str = " ".join(cmd) if isinstance(cmd, list) else str(cmd)

                        if "pytest" in cmd_str:
                            call_count += 1
                            # Fail first time, succeed on retry
                            if call_count == 1:
                                return Mock(
                                    returncode=1,
                                    stdout="test_failures.py::test_flaky_test FAILED",
                                    stderr="Random failure",
                                )
                            else:
                                return Mock(
                                    returncode=0,
                                    stdout="test_failures.py::test_flaky_test PASSED",
                                    stderr="",
                                )

                        return Mock(returncode=0, stdout="Success", stderr="")

                    mock_run.side_effect = mock_subprocess_flaky

                    # Run simulation
                    result = simulator.run(checks=["tests"])

                    # Should succeed after retry
                    assert result.overall_status in [
                        CheckStatus.SUCCESS,
                        CheckStatus.WARNING,
                    ]

                    # Verify retry was attempted
                    assert call_count > 1

        finally:
            os.chdir(original_cwd)

    def test_partial_failure_recovery(self, project_with_issues):
        """Test recovery when some checks fail but others succeed."""
        project_dir = project_with_issues

        original_cwd = os.getcwd()
        os.chdir(project_dir)

        try:
            config_path = project_dir / "ci-config.yaml"
            simulator = CISimulator(str(config_path))

            with patch("shutil.which") as mock_which:
                mock_which.return_value = "/usr/bin/tool"

                with patch("subprocess.run") as mock_run:

                    def mock_subprocess_partial_failure(*args, **kwargs):
                        cmd = args[0] if args else kwargs.get("args", [])
                        cmd_str = " ".join(cmd) if isinstance(cmd, list) else str(cmd)

                        # Some tools fail
                        if "black" in cmd_str:
                            return Mock(
                                returncode=1,
                                stdout="",
                                stderr="Formatting issues found",
                            )
                        elif "pytest" in cmd_str:
                            return Mock(returncode=1, stdout="", stderr="Some tests failed")

                        # Other tools succeed
                        else:
                            return Mock(returncode=0, stdout="Success", stderr="")

                    mock_run.side_effect = mock_subprocess_partial_failure

                    # Run simulation
                    result = simulator.run(checks=["code_quality", "security", "tests"])

                    # Should have mixed results
                    assert result.overall_status in [
                        CheckStatus.WARNING,
                        CheckStatus.FAILURE,
                    ]

                    # Should have both successful and failed checks
                    successful_checks = result.successful_checks
                    failed_checks = result.failed_checks

                    assert len(successful_checks) > 0
                    assert len(failed_checks) > 0

                    # Total checks should equal successful + failed
                    total_checks = len(result.check_results)
                    assert total_checks == len(successful_checks) + len(failed_checks)

        finally:
            os.chdir(original_cwd)

    def test_error_aggregation_and_reporting(self, project_with_issues):
        """Test error aggregation and comprehensive reporting."""
        project_dir = project_with_issues

        original_cwd = os.getcwd()
        os.chdir(project_dir)

        try:
            config_path = project_dir / "ci-config.yaml"
            simulator = CISimulator(str(config_path))

            # Enable error tracking
            simulator.error_handler = ErrorHandler()

            with patch("shutil.which") as mock_which:
                mock_which.return_value = "/usr/bin/tool"

                with patch("subprocess.run") as mock_run:

                    def mock_subprocess_multiple_errors(*args, **kwargs):
                        cmd = args[0] if args else kwargs.get("args", [])
                        cmd_str = " ".join(cmd) if isinstance(cmd, list) else str(cmd)

                        # Different types of errors for different tools
                        if "black" in cmd_str:
                            return Mock(returncode=1, stdout="", stderr="Syntax error in file")
                        elif "flake8" in cmd_str:
                            return Mock(returncode=1, stdout="Style violations found", stderr="")
                        elif "mypy" in cmd_str:
                            return Mock(returncode=1, stdout="Type errors found", stderr="")
                        elif "pytest" in cmd_str:
                            return Mock(returncode=1, stdout="", stderr="Test failures")
                        elif "safety" in cmd_str:
                            return Mock(returncode=1, stdout="Vulnerabilities found", stderr="")
                        elif "bandit" in cmd_str:
                            return Mock(returncode=1, stdout="Security issues found", stderr="")

                        return Mock(returncode=0, stdout="Success", stderr="")

                    mock_run.side_effect = mock_subprocess_multiple_errors

                    # Run simulation
                    result = simulator.run(checks=["code_quality", "security", "tests"])

                    # Should have comprehensive error information
                    assert result.overall_status == CheckStatus.FAILURE

                    # Should have multiple failed checks
                    failed_checks = result.failed_checks
                    assert len(failed_checks) > 0

                    # Should have error summary
                    if hasattr(simulator, "error_handler") and simulator.error_handler:
                        error_summary = simulator.error_handler.get_error_summary()
                        assert isinstance(error_summary, str)
                        assert len(error_summary) > 0

                    # Check that different types of errors were captured
                    all_errors = []
                    for check in failed_checks:
                        all_errors.extend(check.errors)

                    error_text = " ".join(all_errors).lower()

                    # Should contain various error types
                    error_types = [
                        "syntax",
                        "style",
                        "type",
                        "test",
                        "vulnerabilit",
                        "security",
                    ]
                    found_error_types = [error_type for error_type in error_types if error_type in error_text]
                    assert len(found_error_types) > 0

        finally:
            os.chdir(original_cwd)


@pytest.mark.integration
class TestSystemResilienceIntegration:
    """Integration tests for overall system resilience."""

    def test_resource_exhaustion_handling(self, project_with_issues):
        """Test handling of resource exhaustion scenarios."""
        project_dir = project_with_issues

        original_cwd = os.getcwd()
        os.chdir(project_dir)

        try:
            config_path = project_dir / "ci-config.yaml"
            simulator = CISimulator(str(config_path))

            with patch("shutil.which") as mock_which:
                mock_which.return_value = "/usr/bin/tool"

                with patch("subprocess.run") as mock_run:

                    def mock_subprocess_resource_exhaustion(*args, **kwargs):
                        # Simulate memory error
                        raise MemoryError("Not enough memory to complete operation")

                    mock_run.side_effect = mock_subprocess_resource_exhaustion

                    # Run simulation
                    result = simulator.run(checks=["code_quality"])

                    # Should handle resource exhaustion gracefully
                    assert isinstance(result, SimulationResult)
                    assert result.overall_status == CheckStatus.FAILURE

                    # Should have captured resource exhaustion errors
                    failed_checks = result.failed_checks
                    assert len(failed_checks) > 0

                    error_messages = []
                    for check in failed_checks:
                        error_messages.extend(check.errors)

                    error_text = " ".join(error_messages).lower()
                    assert "memory" in error_text or "resource" in error_text

        finally:
            os.chdir(original_cwd)

    def test_filesystem_permission_handling(self, project_with_issues):
        """Test handling of filesystem permission errors."""
        project_dir = project_with_issues

        original_cwd = os.getcwd()
        os.chdir(project_dir)

        try:
            config_path = project_dir / "ci-config.yaml"
            simulator = CISimulator(str(config_path))

            with patch("shutil.which") as mock_which:
                mock_which.return_value = "/usr/bin/tool"

                with patch("subprocess.run") as mock_run:

                    def mock_subprocess_permission_error(*args, **kwargs):
                        # Simulate permission error
                        raise PermissionError("Permission denied: cannot write to directory")

                    mock_run.side_effect = mock_subprocess_permission_error

                    # Run simulation
                    result = simulator.run(checks=["code_quality"])

                    # Should handle permission errors gracefully
                    assert isinstance(result, SimulationResult)
                    assert result.overall_status == CheckStatus.FAILURE

                    # Should have captured permission errors
                    failed_checks = result.failed_checks
                    assert len(failed_checks) > 0

                    error_messages = []
                    for check in failed_checks:
                        error_messages.extend(check.errors)

                    error_text = " ".join(error_messages).lower()
                    assert "permission" in error_text or "denied" in error_text

        finally:
            os.chdir(original_cwd)

    def test_network_connectivity_handling(self, project_with_issues):
        """Test handling of network connectivity issues."""
        project_dir = project_with_issues

        original_cwd = os.getcwd()
        os.chdir(project_dir)

        try:
            config_path = project_dir / "ci-config.yaml"
            simulator = CISimulator(str(config_path))

            with patch("shutil.which") as mock_which:
                mock_which.return_value = "/usr/bin/tool"

                with patch("subprocess.run") as mock_run:

                    def mock_subprocess_network_error(*args, **kwargs):
                        cmd = args[0] if args else kwargs.get("args", [])
                        cmd_str = " ".join(cmd) if isinstance(cmd, list) else str(cmd)

                        # Safety check requires network access
                        if "safety" in cmd_str:
                            return Mock(
                                returncode=1,
                                stdout="",
                                stderr="Network error: Unable to connect to vulnerability database",
                            )

                        # Other tools work offline
                        return Mock(returncode=0, stdout="Success", stderr="")

                    mock_run.side_effect = mock_subprocess_network_error

                    # Run simulation
                    result = simulator.run(checks=["security"])

                    # Should handle network errors gracefully
                    assert isinstance(result, SimulationResult)

                    # Network-dependent checks may fail, others should succeed
                    failed_checks = result.failed_checks

                    if failed_checks:
                        error_messages = []
                        for check in failed_checks:
                            error_messages.extend(check.errors)

                        error_text = " ".join(error_messages).lower()
                        assert "network" in error_text or "connect" in error_text

        finally:
            os.chdir(original_cwd)

    def test_graceful_degradation(self, project_with_issues):
        """Test graceful degradation when some components fail."""
        project_dir = project_with_issues

        original_cwd = os.getcwd()
        os.chdir(project_dir)

        try:
            config_path = project_dir / "ci-config.yaml"
            simulator = CISimulator(str(config_path))

            with patch("shutil.which") as mock_which:
                # Some tools available, some not
                def mock_which_partial(*args, **kwargs):
                    tool = args[0] if args else None
                    if tool in ["black", "pytest"]:
                        return "/usr/bin/tool"  # Available
                    return None  # Not available

                mock_which.side_effect = mock_which_partial

                with patch("subprocess.run") as mock_run:
                    mock_run.return_value = Mock(returncode=0, stdout="Success", stderr="")

                    # Run simulation
                    result = simulator.run(checks=["code_quality", "security", "tests"])

                    # Should complete despite some tools being unavailable
                    assert isinstance(result, SimulationResult)

                    # Should have mix of successful, failed, and skipped checks
                    successful_checks = result.successful_checks
                    failed_checks = result.failed_checks
                    skipped_checks = result.get_checks_by_status(CheckStatus.SKIPPED)

                    # Should have at least some results
                    total_checks = len(successful_checks) + len(failed_checks) + len(skipped_checks)
                    assert total_checks > 0

                    # Should have some skipped checks due to missing tools
                    assert len(skipped_checks) > 0

        finally:
            os.chdir(original_cwd)
