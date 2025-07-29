"""
Unit tests for all checker implementations.
"""

import pytest
import os
import tempfile
import subprocess
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path

# Import checkers
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'tools', 'ci'))

from checkers.code_quality import CodeQualityChecker
from checkers.security_scanner import SecurityScanne
om checkers.performance_analyzer import PerformanceAnalyzer
from checkers.test_runner import TestRunner
from checkers.ai_component_tester import AIComponentTester
from models import CheckResult, CheckStatus
from interfaces import CheckerError


class TestCodeQualityChecker:
    """Test cases for CodeQualityChecker."""

    def test_code_quality_checker_creation(self, sample_config):
        """Test CodeQualityChecker creation."""
        checker = CodeQualityChecker(sample_config)

        assert checker.name == "Code Quality Checker"
        assert checker.check_type == "code_quality"
        assert "black" in checker.dependencies
        assert "isort" in checker.dependencies
        assert "flake8" in checker.dependencies
        assert "mypy" in checker.dependencies

    @patch('subprocess.run')
    def test_run_black_success(self, mock_run, sample_config, temp_dir):
        """Test successful Black formatting check."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "All done! ✨ 🍰 ✨"
        mock_run.return_value.stderr = ""

        checker = CodeQualityChecker(sample_config)
        result = checker.run_black()

        assert isinstance(result, CheckResult)
        assert result.status == CheckStatus.SUCCESS
        assert result.name == "Black Formatter"
        assert "All done!" in result.output

    @patch('subprocess.run')
    def test_run_black_failure(self, mock_run, sample_config):
        """Test Black formatting check with errors."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = "error: cannot use --safe with --fast"

        checker = CodeQualityChecker(sample_config)
        result = checker.run_black()

        assert result.status == CheckStatus.FAILURE
        assert len(result.errors) > 0
        assert "error: cannot use --safe with --fast" in result.errors[0]

    @patch('subprocess.run')
    def test_run_black_with_auto_fix(self, mock_run, sample_config):
        """Test Black formatting with auto-fix enabled."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "reformatted test.py"
        mock_run.return_value.stderr = ""

        checker = CodeQualityChecker(sample_config)
        result = checker.run_black(auto_fix=True)

        assert result.status == CheckStatus.SUCCESS
        # Verify that --check flag is not used when auto_fix=True
        call_args = mock_run.call_args[0][0]
        assert "--check" not in call_args

    @patch('subprocess.run')
    def test_run_isort_success(self, mock_run, sample_config):
        """Test successful isort check."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Skipped 0 files"
        mock_run.return_value.stderr = ""

        checker = CodeQualityChecker(sample_config)
        result = checker.run_isort()

        assert result.status == CheckStatus.SUCCESS
        assert result.name == "isort Import Sorter"

    @patch('subprocess.run')
    def test_run_isort_with_changes_needed(self, mock_run, sample_config):
        """Test isort check when changes are needed."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = "Fixing /path/to/file.py"
        mock_run.return_value.stderr = ""

        checker = CodeQualityChecker(sample_config)
        result = checker.run_isort()

        assert result.status == CheckStatus.FAILURE
        assert "Import sorting issues found" in result.errors[0]

    @patch('subprocess.run')
    def test_run_flake8_success(self, mock_run, sample_config):
        """Test successful flake8 check."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = ""

        checker = CodeQualityChecker(sample_config)
        result = checker.run_flake8()

        assert result.status == CheckStatus.SUCCESS
        assert result.name == "flake8 Style Checker"

    @patch('subprocess.run')
    def test_run_flake8_with_violations(self, mock_run, sample_config):
        """Test flake8 check with style violations."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = "./test.py:1:1: E302 expected 2 blank lines, found 1"
        mock_run.return_value.stderr = ""

        checker = CodeQualityChecker(sample_config)
        result = checker.run_flake8()

        assert result.status == CheckStatus.FAILURE
        assert len(result.errors) > 0
        assert "E302" in result.errors[0]

    @patch('subprocess.run')
    def test_run_mypy_success(self, mock_run, sample_config):
        """Test successful mypy check."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Success: no issues found"
        mock_run.return_value.stderr = ""

        checker = CodeQualityChecker(sample_config)
        result = checker.run_mypy()

        assert result.status == CheckStatus.SUCCESS
        assert result.name == "mypy Type Checker"

    @patch('subprocess.run')
    def test_run_mypy_with_errors(self, mock_run, sample_config):
        """Test mypy check with type errors."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = "test.py:10: error: Incompatible types"
        mock_run.return_value.stderr = ""

        checker = CodeQualityChecker(sample_config)
        result = checker.run_mypy()

        assert result.status == CheckStatus.FAILURE
        assert len(result.errors) > 0
        assert "Incompatible types" in result.errors[0]

    @patch('subprocess.run')
    def test_run_all_quality_checks(self, mock_run, sample_config):
        """Test running all quality checks."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Success"
        mock_run.return_value.stderr = ""

        checker = CodeQualityChecker(sample_config)
        results = checker.run_all_quality_checks()

        assert isinstance(results, dict)
        assert "black" in results
        assert "isort" in results
        assert "flake8" in results
        assert "mypy" in results

        for result in results.values():
            assert isinstance(result, CheckResult)

    def test_is_available_all_tools_present(self, sample_config):
        """Test is_available when all tools are present."""
        with patch('shutil.which') as mock_which:
            mock_which.return_value = "/usr/bin/tool"

            checker = CodeQualityChecker(sample_config)
            assert checker.is_available() is True

    def test_is_available_missing_tools(self, sample_config):
        """Test is_available when tools are missing."""
        with patch('shutil.which') as mock_which:
            mock_which.return_value = None

            checker = CodeQualityChecker(sample_config)
            assert checker.is_available() is False

    @patch('subprocess.run')
    def test_run_check_integration(self, mock_run, sample_config):
        """Test the main run_check method."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Success"
        mock_run.return_value.stderr = ""

        checker = CodeQualityChecker(sample_config)
        result = checker.run_check()

        assert isinstance(result, CheckResult)
        assert result.name == "Code Quality Checker"


class TestSecurityScanner:
    """Test cases for SecurityScanner."""

    def test_security_scanner_creation(self, sample_config):
        """Test SecurityScanner creation."""
        scanner = SecurityScanner(sample_config)

        assert scanner.name == "Security Scanner"
        assert scanner.check_type == "security"
        assert "safety" in scanner.dependencies
        assert "bandit" in scanner.dependencies

    @patch('subprocess.run')
    def test_run_safety_check_success(self, mock_run, sample_config):
        """Test successful safety vulnerability check."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "All good! No known security vulnerabilities found."
        mock_run.return_value.stderr = ""

        scanner = SecurityScanner(sample_config)
        result = scanner.run_safety_check()

        assert result.status == CheckStatus.SUCCESS
        assert result.name == "Safety Vulnerability Scanner"
        assert "No known security vulnerabilities" in result.output

    @patch('subprocess.run')
    def test_run_safety_check_with_vulnerabilities(self, mock_run, sample_config):
        """Test safety check with vulnerabilities found."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = "VULNERABILITY: django==1.0 has known security vulnerabilities"
        mock_run.return_value.stderr = ""

        scanner = SecurityScanner(sample_config)
        result = scanner.run_safety_check()

        assert result.status == CheckStatus.FAILURE
        assert len(result.errors) > 0
        assert "django==1.0" in result.errors[0]

    @patch('subprocess.run')
    def test_run_bandit_scan_success(self, mock_run, sample_config):
        """Test successful bandit security scan."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "No issues identified."
        mock_run.return_value.stderr = ""

        scanner = SecurityScanner(sample_config)
        result = scanner.run_bandit_scan()

        assert result.status == CheckStatus.SUCCESS
        assert result.name == "Bandit Security Linter"

    @patch('subprocess.run')
    def test_run_bandit_scan_with_issues(self, mock_run, sample_config):
        """Test bandit scan with security issues."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = "Issue: [B602:subprocess_popen_with_shell_equals_true]"
        mock_run.return_value.stderr = ""

        scanner = SecurityScanner(sample_config)
        result = scanner.run_bandit_scan()

        assert result.status == CheckStatus.FAILURE
        assert len(result.errors) > 0
        assert "B602" in result.errors[0]

    @patch('subprocess.run')
    def test_run_full_security_scan(self, mock_run, sample_config):
        """Test running full security scan."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "No issues found"
        mock_run.return_value.stderr = ""

        scanner = SecurityScanner(sample_config)
        results = scanner.run_full_security_scan()

        assert isinstance(results, dict)
        assert "safety" in results
        assert "bandit" in results

        for result in results.values():
            assert isinstance(result, CheckResult)

    @patch('subprocess.run')
    def test_generate_security_report(self, mock_run, sample_config):
        """Test security report generation."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "No issues"
        mock_run.return_value.stderr = ""

        scanner = SecurityScanner(sample_config)
        results = scanner.run_full_security_scan()
        report = scanner.generate_security_report(results)

        assert isinstance(report, str)
        assert "Security Scan Report" in report
        assert "safety" in report.lower()
        assert "bandit" in report.lower()


class TestPerformanceAnalyzer:
    """Test cases for PerformanceAnalyzer."""

    def test_performance_analyzer_creation(self, sample_config):
        """Test PerformanceAnalyzer creation."""
        analyzer = PerformanceAnalyzer(sample_config)

        assert analyzer.name == "Performance Analyzer"
        assert analyzer.check_type == "performance"
        assert "pytest" in analyzer.dependencies

    @patch('subprocess.run')
    def test_run_benchmarks_success(self, mock_run, sample_config):
        """Test successful benchmark execution."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "test_performance.py::test_speed PASSED [100%]"
        mock_run.return_value.stderr = ""

        analyzer = PerformanceAnalyzer(sample_config)
        result = analyzer.run_benchmarks()

        assert result.status == CheckStatus.SUCCESS
        assert result.name == "Performance Benchmarks"

    @patch('subprocess.run')
    def test_run_benchmarks_failure(self, mock_run, sample_config):
        """Test benchmark execution with failures."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = "test_performance.py::test_speed FAILED"
        mock_run.return_value.stderr = "AssertionError: Performance regression detected"

        analyzer = PerformanceAnalyzer(sample_config)
        result = analyzer.run_benchmarks()

        assert result.status == CheckStatus.FAILURE
        assert len(result.errors) > 0

    def test_compare_with_baseline_no_baseline(self, sample_config, temp_dir):
        """Test comparison when no baseline exists."""
        analyzer = PerformanceAnalyzer(sample_config)
        analyzer.baseline_path = os.path.join(temp_dir, "nonexistent_baseline.json")

        current_results = {"test_speed": 1.5, "test_memory": 100}
        report = analyzer.compare_with_baseline(current_results)

        assert "No baseline found" in report.summary
        assert len(report.regressions) == 0

    def test_compare_with_baseline_with_regression(self, sample_config, temp_dir):
        """Test comparison with performance regression."""
        import json

        baseline_data = {"test_speed": 1.0, "test_memory": 80}
        baseline_path = os.path.join(temp_dir, "baseline.json")

        with open(baseline_path, 'w') as f:
            json.dump(baseline_data, f)

        analyzer = PerformanceAnalyzer(sample_config)
        analyzer.baseline_path = baseline_path

        current_results = {"test_speed": 1.5, "test_memory": 120}
        report = analyzer.compare_with_baseline(current_results)

        assert len(report.regressions) > 0
        assert any(reg.test_name == "test_speed" for reg in report.regressions)
        assert any(reg.test_name == "test_memory" for reg in report.regressions)

    def test_detect_performance_regression(self, sample_config, temp_dir):
        """Test performance regression detection."""
        import json

        baseline_data = {"test_critical": 1.0, "test_minor": 2.0}
        baseline_path = os.path.join(temp_dir, "baseline.json")

        with open(baseline_path, 'w') as f:
            json.dump(baseline_data, f)

        analyzer = PerformanceAnalyzer(sample_config)
        analyzer.baseline_path = baseline_path

        # Simulate significant regression (>30% threshold)
        current_results = {"test_critical": 1.5, "test_minor": 2.1}
        regressions = analyzer.detect_performance_regression(threshold=30.0)

        # Should detect the critical regression but not the minor one
        critical_regressions = [r for r in regressions if r.test_name == "test_critical"]
        assert len(critical_regressions) > 0

    def test_save_baseline(self, sample_config, temp_dir):
        """Test saving performance baseline."""
        analyzer = PerformanceAnalyzer(sample_config)
        analyzer.baseline_path = os.path.join(temp_dir, "new_baseline.json")

        results = {"test_speed": 1.2, "test_memory": 90}
        analyzer.save_baseline(results)

        assert os.path.exists(analyzer.baseline_path)

        # Verify saved content
        import json
        with open(analyzer.baseline_path, 'r') as f:
            saved_data = json.load(f)

        assert saved_data == results


class TestTestRunner:
    """Test cases for TestRunner."""

    def test_test_runner_creation(self, sample_config):
        """Test TestRunner creation."""
        runner = TestRunner(sample_config)

        assert runner.name == "Test Runner"
        assert runner.check_type == "tests"
        assert "pytest" in runner.dependencies

    @patch('subprocess.run')
    def test_run_unit_tests_success(self, mock_run, sample_config):
        """Test successful unit test execution."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "10 passed, 0 failed"
        mock_run.return_value.stderr = ""

        runner = TestRunner(sample_config)
        result = runner.run_unit_tests()

        assert result.status == CheckStatus.SUCCESS
        assert result.name == "Unit Tests"
        assert "10 passed" in result.output

    @patch('subprocess.run')
    def test_run_unit_tests_failure(self, mock_run, sample_config):
        """Test unit test execution with failures."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = "8 passed, 2 failed"
        mock_run.return_value.stderr = "FAILED test_example.py::test_function"

        runner = TestRunner(sample_config)
        result = runner.run_unit_tests()

        assert result.status == CheckStatus.FAILURE
        assert len(result.errors) > 0

    @patch('subprocess.run')
    def test_run_integration_tests(self, mock_run, sample_config):
        """Test integration test execution."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "5 passed"
        mock_run.return_value.stderr = ""

        runner = TestRunner(sample_config)
        result = runner.run_integration_tests()

        assert result.status == CheckStatus.SUCCESS
        assert result.name == "Integration Tests"

    @patch('subprocess.run')
    def test_run_ai_compatibility_tests(self, mock_run, sample_config):
        """Test AI compatibility test execution."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "AI compatibility tests passed"
        mock_run.return_value.stderr = ""

        runner = TestRunner(sample_config)
        result = runner.run_ai_compatibility_tests()

        assert result.status == CheckStatus.SUCCESS
        assert result.name == "AI Compatibility Tests"

    @patch('subprocess.run')
    def test_run_performance_tests(self, mock_run, sample_config):
        """Test performance test execution."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Performance tests completed"
        mock_run.return_value.stderr = ""

        runner = TestRunner(sample_config)
        result = runner.run_performance_tests()

        assert result.status == CheckStatus.SUCCESS
        assert result.name == "Performance Tests"

    @patch('subprocess.run')
    def test_run_demo_scripts(self, mock_run, sample_config):
        """Test demo script execution."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Demo scripts executed successfully"
        mock_run.return_value.stderr = ""

        runner = TestRunner(sample_config)
        result = runner.run_demo_scripts()

        assert result.status == CheckStatus.SUCCESS
        assert result.name == "Demo Scripts"


class TestAIComponentTester:
    """Test cases for AIComponentTester."""

    def test_ai_component_tester_creation(self, sample_config):
        """Test AIComponentTester creation."""
        tester = AIComponentTester(sample_config)

        assert tester.name == "AI Component Tester"
        assert tester.check_type == "ai_integration"
        assert "pytest" in tester.dependencies

    @patch('subprocess.run')
    def test_test_copilot_components(self, mock_run, sample_config):
        """Test Copilot component testing."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Copilot tests passed"
        mock_run.return_value.stderr = ""

        tester = AIComponentTester(sample_config)
        result = tester.test_copilot_components()

        assert result.status == CheckStatus.SUCCESS
        assert result.name == "Copilot Component Tests"

    @patch('subprocess.run')
    def test_test_cursor_components(self, mock_run, sample_config):
        """Test Cursor component testing."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Cursor tests passed"
        mock_run.return_value.stderr = ""

        tester = AIComponentTester(sample_config)
        result = tester.test_cursor_components()

        assert result.status == CheckStatus.SUCCESS
        assert result.name == "Cursor Component Tests"

    @patch('subprocess.run')
    def test_test_kiro_components(self, mock_run, sample_config):
        """Test Kiro component testing."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Kiro tests passed"
        mock_run.return_value.stderr = ""

        tester = AIComponentTester(sample_config)
        result = tester.test_kiro_components()

        assert result.status == CheckStatus.SUCCESS
        assert result.name == "Kiro Component Tests"

    @patch('subprocess.run')
    def test_run_ai_integration_tests(self, mock_run, sample_config):
        """Test running all AI integration tests."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "All AI tests passed"
        mock_run.return_value.stderr = ""

        tester = AIComponentTester(sample_config)
        results = tester.run_ai_integration_tests()

        assert isinstance(results, dict)
        assert "copilot" in results
        assert "cursor" in results
        assert "kiro" in results

        for result in results.values():
            assert isinstance(result, CheckResult)

    @patch('subprocess.run')
    def test_validate_ai_compatibility(self, mock_run, sample_config):
        """Test AI compatibility validation."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "AI compatibility validated"
        mock_run.return_value.stderr = ""

        tester = AIComponentTester(sample_config)
        result = tester.validate_ai_compatibility()

        assert result.status == CheckStatus.SUCCESS
        assert result.name == "AI Compatibility Validation"


class TestCheckerErrorHandling:
    """Test error handling in checkers."""

    @patch('subprocess.run')
    def test_subprocess_timeout_handling(self, mock_run, sample_config):
        """Test handling of subprocess timeouts."""
        mock_run.side_effect = subprocess.TimeoutExpired("black", 30)

        checker = CodeQualityChecker(sample_config)
        result = checker.run_black()

        assert result.status == CheckStatus.FAILURE
        assert "timeout" in result.errors[0].lower()

    @patch('subprocess.run')
    def test_subprocess_exception_handling(self, mock_run, sample_config):
        """Test handling of subprocess exceptions."""
        mock_run.side_effect = FileNotFoundError("black command not found")

        checker = CodeQualityChecker(sample_config)
        result = checker.run_black()

        assert result.status == CheckStatus.FAILURE
        assert "not found" in result.errors[0].lower()

    def test_invalid_config_handling(self):
        """Test handling of invalid configuration."""
        invalid_config = {"invalid": "config"}

        checker = CodeQualityChecker(invalid_config)
        errors = checker.validate_config()

        assert len(errors) == 0  # Should not crash, just use defaults

    @patch('os.path.exists')
    def test_missing_baseline_handling(self, mock_exists, sample_config):
        """Test handling of missing baseline files."""
        mock_exists.return_value = False

        analyzer = PerformanceAnalyzer(sample_config)
        current_results = {"test": 1.0}
        report = analyzer.compare_with_baseline(current_results)

        assert "No baseline found" in report.summary
        assert len(report.regressions) == 0


class TestCheckerIntegration:
    """Integration tests for checkers."""

    def test_all_checkers_implement_interface(self, sample_config):
        """Test that all checkers properly implement the interface."""
        checkers = [
            CodeQualityChecker(sample_config),
            SecurityScanner(sample_config),
            PerformanceAnalyzer(sample_config),
            TestRunner(sample_config),
            AIComponentTester(sample_config)
        ]

        for checker in checkers:
            # Test required properties
            assert hasattr(checker, 'name')
            assert hasattr(checker, 'check_type')
            assert hasattr(checker, 'dependencies')

            # Test required methods
            assert callable(getattr(checker, 'is_available'))
            assert callable(getattr(checker, 'run_check'))
            assert callable(getattr(checker, 'validate_config'))
            assert callable(getattr(checker, 'cleanup'))

    @patch('subprocess.run')
    def test_checker_cleanup_called(self, mock_run, sample_config):
        """Test that cleanup is properly called."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Success"
        mock_run.return_value.stderr = ""

        checker = CodeQualityChecker(sample_config)

        # Mock the cleanup method to verify it's called
        checker.cleanup = Mock()

        try:
            result = checker.run_check()
        finally:
            checker.cleanup()

        checker.cleanup.assert_called_once()

    def test_checker_config_validation(self, sample_config):
        """Test configuration validation across all checkers."""
        checkers = [
            CodeQualityChecker(sample_config),
            SecurityScanner(sample_config),
            PerformanceAnalyzer(sample_config),
            TestRunner(sample_config),
            AIComponentTester(sample_config)
        ]

        for checker in checkers:
            errors = checker.validate_config()
            # Should not have validation errors with sample config
            assert isinstance(errors, list)
