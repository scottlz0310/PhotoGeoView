"""
Test Runner for CI Simulation Tool

This module implements comprehensive test execution with pytest integration,
supporting unit tests, integration tests, performance tests, and AI compatibility tests
with detailed result analysis and reporting.
"""

import json
import logging
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from ..interfaces import CheckerInterface
    from ..models import CheckResult, CheckStatus, ConfigDict
except ImportError:
    from interfaces import CheckerInterface
    from models import CheckResult, CheckStatus, ConfigDict


@dataclass
class TestSuite:
    """Represents a test suite with its configuration and metadata."""

    name: str
    path: str
    test_type: str  # unit, integration, performance, ai_compatibility
    markers: List[str]
    timeout: Optional[float] = None
    requires_display: bool = False
    python_version: Optional[str] = None


class TestRunner(CheckerInterface):
    """
    Comprehensive test runner with pytest integration.

    This checker provides:
    - pytest execution wrapper with proper environment setup
    - Test discovery and classification (unit, integration, performance)
    - Test result analysis and detailed reporting
    - Support for AI compatibility testing
    - Multi-Python version testing support
    """

    def __init__(self, config: ConfigDict):
        """
        Initialize the test runner.

        Args:
            config: Configuration dictionary containing test settings
        """
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.project_root = Path.cwd()
        self.test_root = self.project_root / "tests"

        # Load pytest configuration
        self.pytest_config = self._load_pytest_config()

        # Discover test suites
        self.test_suites = self._discover_test_suites()

    @property
    def name(self) -> str:
        """Return the human-readable name of this checker."""
        return "Test Runner"

    @property
    def check_type(self) -> str:
        """Return the type category of this."""
        return "testing"

    @property
    def dependencies(self) -> List[str]:
        """Return list of external dependencies required by this checker."""
        return ["pytest", "pytest-cov", "pytest-xdist", "pytest-benchmark"]

    def is_available(self) -> bool:
        """
        Check if pytest and required plugins are available.

        Returns:
            True if all dependencies are available
        """
        if self._is_available is not None:
            return self._is_available

        missing_tools = []
        for tool in self.dependencies:
            if not self._is_tool_available(tool):
                missing_tools.append(tool)

        if missing_tools:
            self.logger.warning(f"Missing test tools: {missing_tools}")
            self._is_available = False
        else:
            self._is_available = True

        return self._is_available

    def _is_tool_available(self, tool: str) -> bool:
        """Check if a specific tool is available in the environment."""
        try:
            if tool == "pytest":
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
            else:
                # For pytest plugins, try to import them
                import_name = tool.replace("-", "_")
                # Special cases for pytest plugins
                if tool == "pytest-xdist":
                    import_name = "xdist"
                elif tool == "pytest-qt":
                    import_name = "pytestqt"
                elif tool == "pytest-cov":
                    import_name = "pytest_cov"
                elif tool == "pytest-benchmark":
                    import_name = "pytest_benchmark"

                result = subprocess.run(
                    [sys.executable, "-c", f"import {import_name}"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _load_pytest_config(self) -> Dict[str, Any]:
        """Load pytest configuration from pyproject.toml or use defaults."""
        config = self.config.get("pytest", {})

        # Default pytest configuration
        default_config = {
            "testpaths": ["tests"],
            "python_files": ["test_*.py", "*_test.py"],
            "python_classes": ["Test*"],
            "python_functions": ["test_*"],
            "addopts": [
                "-ra",
                "--strict-markers",
                "--strict-config",
                "--tb=short",
            ],
            "markers": [
                "slow: marks tests as slow",
                "integration: marks tests as integration tests",
                "ai_compatibility: marks tests as AI compatibility tests",
                "performance: marks tests as performance tests",
            ],
            "timeout": 300,  # 5 minutes default timeout
        }

        # Merge with provided configuration
        merged_config = {**default_config, **config}

        # Try to load from pyproject.toml if it exists
        pyproject_path = self.project_root / "pyproject.toml"
        if pyproject_path.exists():
            try:
                # Try to use tomllib (Python 3.11+) or fall back to tomli
                try:
                    import tomllib
                except ImportError:
                    try:
                        import tomli as tomllib
                    except ImportError:
                        tomllib = None

                if tomllib:
                    with open(pyproject_path, "rb") as f:
                        pyproject_data = tomllib.load(f)

                    pytest_config = (
                        pyproject_data.get("tool", {})
                        .get("pytest", {})
                        .get("ini_options", {})
                    )
                    merged_config.update(pytest_config)
                else:
                    self.logger.warning(
                        "tomllib/tomli not available, using default pytest config"
                    )

            except Exception as e:
                self.logger.warning(
                    f"Failed to load pytest config from pyproject.toml: {e}"
                )

        return merged_config

    def _discover_test_suites(self) -> List[TestSuite]:
        """
        Discover and classify test suites in the project.

        Returns:
            List of TestSuite objects representing discovered tests
        """
        test_suites = []

        if not self.test_root.exists():
            self.logger.warning(f"Test directory {self.test_root} does not exist")
            return test_suites

        # Define test suite patterns and their classifications
        suite_patterns = {
            "unit": {
                "patterns": ["test_*.py", "unit_tests.py"],
                "markers": ["unit"],
                "timeout": 60,
            },
            "integration": {
                "patterns": ["*integration*.py", "test_*_integration.py"],
                "markers": ["integration"],
                "timeout": 300,
                "requires_display": True,
            },
            "performance": {
                "patterns": ["*performance*.py", "*benchmark*.py"],
                "markers": ["performance", "slow"],
                "timeout": 600,
            },
            "ai_compatibility": {
                "patterns": ["*ai*.py", "*copilot*.py", "*cursor*.py", "*kiro*.py"],
                "markers": ["ai_compatibility"],
                "timeout": 300,
                "requires_display": True,
            },
        }

        # Discover test files
        for test_type, config in suite_patterns.items():
            for pattern in config["patterns"]:
                for test_file in self.test_root.rglob(pattern):
                    if test_file.is_file() and test_file.suffix == ".py":
                        test_suites.append(
                            TestSuite(
                                name=test_file.stem,
                                path=str(test_file.relative_to(self.project_root)),
                                test_type=test_type,
                                markers=config["markers"],
                                timeout=config.get("timeout"),
                                requires_display=config.get("requires_display", False),
                            )
                        )

        # Remove duplicates (files that match multiple patterns)
        unique_suites = {}
        for suite in test_suites:
            if suite.path not in unique_suites:
                unique_suites[suite.path] = suite
            else:
                # Merge markers from duplicate entries
                existing = unique_suites[suite.path]
                existing.markers = list(set(existing.markers + suite.markers))

        return list(unique_suites.values())

    def run_check(self, **kwargs) -> CheckResult:
        """
        Execute comprehensive test suite.

        Args:
            **kwargs: Additional arguments including:
                - test_types: List of test types to run
                - python_version: Specific Python version to use
                - parallel: Whether to run tests in parallel
                - coverage: Whether to collect coverage data

        Returns:
            CheckResult containing the outcome of all tests
        """
        start_time = time.time()
        test_types = kwargs.get(
            "test_types", ["unit", "integration", "performance", "ai_compatibility"]
        )
        python_version = kwargs.get("python_version")
        parallel = kwargs.get("parallel", self.config.get("parallel", True))
        coverage = kwargs.get("coverage", self.config.get("coverage", True))

        self.logger.info(f"Starting test execution for types: {test_types}")

        all_results = {}
        overall_status = CheckStatus.SUCCESS
        all_errors = []
        all_warnings = []
        all_suggestions = []
        combined_output = []

        # Run tests by type
        for test_type in test_types:
            if test_type == "unit":
                result = self.run_unit_tests(parallel=parallel, coverage=coverage)
            elif test_type == "integration":
                result = self.run_integration_tests(parallel=parallel)
            elif test_type == "performance":
                result = self.run_performance_tests()
            elif test_type == "ai_compatibility":
                result = self.run_ai_compatibility_tests()
            else:
                self.logger.warning(f"Unknown test type: {test_type}")
                continue

            all_results[test_type] = result
            combined_output.append(
                f"=== {test_type.title()} Tests ===\n{result.output}"
            )

            if result.status == CheckStatus.FAILURE:
                overall_status = CheckStatus.FAILURE
            elif (
                result.status == CheckStatus.WARNING
                and overall_status == CheckStatus.SUCCESS
            ):
                overall_status = CheckStatus.WARNING

            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
            all_suggestions.extend(result.suggestions)

        duration = time.time() - start_time

        # Generate summary
        total_tests = sum(
            result.metadata.get("tests_collected", 0) for result in all_results.values()
        )
        passed_tests = sum(
            result.metadata.get("tests_passed", 0) for result in all_results.values()
        )
        failed_tests = sum(
            result.metadata.get("tests_failed", 0) for result in all_results.values()
        )

        summary = f"Executed {total_tests} tests: {passed_tests} passed, {failed_tests} failed"

        return CheckResult(
            name=self.name,
            status=overall_status,
            duration=duration,
            output="\n\n".join(combined_output),
            errors=all_errors,
            warnings=all_warnings,
            suggestions=all_suggestions,
            metadata={
                "individual_results": {
                    name: result.to_dict() for name, result in all_results.items()
                },
                "test_types_run": test_types,
                "total_tests": total_tests,
                "tests_passed": passed_tests,
                "tests_failed": failed_tests,
                "python_version": python_version or sys.version,
                "parallel_execution": parallel,
                "coverage_enabled": coverage,
                "test_suites_discovered": len(self.test_suites),
                "configuration": self.pytest_config,
            },
        )

    def run_unit_tests(
        self, parallel: bool = True, coverage: bool = True
    ) -> CheckResult:
        """
        Run unit tests with pytest.

        Args:
            parallel: Whether to run tests in parallel
            coverage: Whether to collect coverage data

        Returns:
            CheckResult containing unit test results
        """
        start_time = time.time()
        self.logger.info("Running unit tests")

        # Build pytest command
        cmd = [sys.executable, "-m", "pytest"]

        # Add basic options
        cmd.extend(["-v", "--tb=short"])

        # Add coverage if requested
        if coverage:
            cmd.extend(["--cov=src", "--cov-report=term-missing"])

        # Add parallel execution if requested and available
        if parallel and self._is_tool_available("pytest-xdist"):
            cmd.extend(["-n", "auto"])

        # Add markers to select unit tests
        cmd.extend(["-m", "not slow and not integration and not ai_compatibility"])

        # Add test paths
        unit_suites = [s for s in self.test_suites if s.test_type == "unit"]
        if unit_suites:
            cmd.extend([s.path for s in unit_suites])
        else:
            # Fallback to general test discovery
            cmd.append("tests/")

        # Add JSON report for parsing
        json_report_path = self.project_root / "reports" / "unit_tests.json"
        json_report_path.parent.mkdir(parents=True, exist_ok=True)
        # JSON report removed - using standard pytest output instead

        return self._execute_pytest(cmd, "Unit Tests", start_time, json_report_path)

    def run_integration_tests(self, parallel: bool = False) -> CheckResult:
        """
        Run integration tests with proper environment setup.

        Args:
            parallel: Whether to run tests in parallel (disabled by default for integration)

        Returns:
            CheckResult containing integration test results
        """
        start_time = time.time()
        self.logger.info("Running integration tests")

        # Setup virtual display if needed
        env = os.environ.copy()
        if self._needs_virtual_display():
            env.update(self._setup_virtual_display())

        # Build pytest command
        cmd = [sys.executable, "-m", "pytest"]

        # Add basic options
        cmd.extend(["-v", "--tb=short"])

        # Add parallel execution if requested (usually not recommended for integration tests)
        if parallel and self._is_tool_available("pytest-xdist"):
            cmd.extend(["-n", "2"])  # Limited parallelism for integration tests

        # Add markers to select integration tests
        cmd.extend(["-m", "integration"])

        # Add test paths
        integration_suites = [
            s for s in self.test_suites if s.test_type == "integration"
        ]
        if integration_suites:
            cmd.extend([s.path for s in integration_suites])
        else:
            # Fallback to pattern matching
            cmd.extend(["tests/", "-k", "integration"])

        # Add JSON report for parsing
        json_report_path = self.project_root / "reports" / "integration_tests.json"
        json_report_path.parent.mkdir(parents=True, exist_ok=True)
        # JSON report removed - using standard pytest output instead

        return self._execute_pytest(
            cmd, "Integration Tests", start_time, json_report_path, env=env
        )

    def run_performance_tests(self) -> CheckResult:
        """
        Run performance tests with benchmarking.

        Returns:
            CheckResult containing performance test results
        """
        start_time = time.time()
        self.logger.info("Running performance tests")

        # Build pytest command
        cmd = [sys.executable, "-m", "pytest"]

        # Add basic options
        cmd.extend(["-v", "--tb=short"])

        # Add benchmark options if available
        if self._is_tool_available("pytest-benchmark"):
            cmd.extend(["--benchmark-only", "--benchmark-json=reports/benchmark.json"])

        # Add markers to select performance tests
        cmd.extend(["-m", "performance or slow"])

        # Add test paths
        performance_suites = [
            s for s in self.test_suites if s.test_type == "performance"
        ]
        if performance_suites:
            cmd.extend([s.path for s in performance_suites])
        else:
            # Fallback to pattern matching
            cmd.extend(["tests/", "-k", "performance or benchmark"])

        # Add JSON report for parsing
        json_report_path = self.project_root / "reports" / "performance_tests.json"
        json_report_path.parent.mkdir(parents=True, exist_ok=True)
        # JSON report removed - using standard pytest output instead

        return self._execute_pytest(
            cmd, "Performance Tests", start_time, json_report_path
        )

    def run_ai_compatibility_tests(self) -> CheckResult:
        """
        Run AI compatibility tests for Copilot, Cursor, and Kiro components.

        Returns:
            CheckResult containing AI compatibility test results
        """
        start_time = time.time()
        self.logger.info("Running AI compatibility tests")

        # Setup virtual display if needed
        env = os.environ.copy()
        if self._needs_virtual_display():
            env.update(self._setup_virtual_display())

        # Build pytest command
        cmd = [sys.executable, "-m", "pytest"]

        # Add basic options
        cmd.extend(["-v", "--tb=short"])

        # Add markers to select AI compatibility tests
        cmd.extend(["-m", "ai_compatibility"])

        # Add test paths
        ai_suites = [s for s in self.test_suites if s.test_type == "ai_compatibility"]
        if ai_suites:
            cmd.extend([s.path for s in ai_suites])
        else:
            # Fallback to pattern matching
            cmd.extend(["tests/", "-k", "ai or copilot or cursor or kiro"])

        # Add JSON report for parsing
        json_report_path = self.project_root / "reports" / "ai_compatibility_tests.json"
        json_report_path.parent.mkdir(parents=True, exist_ok=True)
        # JSON report removed - using standard pytest output instead

        return self._execute_pytest(
            cmd, "AI Compatibility Tests", start_time, json_report_path, env=env
        )

    def _execute_pytest(
        self,
        cmd: List[str],
        test_name: str,
        start_time: float,
        json_report_path: Optional[Path],
        env: Optional[Dict[str, str]] = None,
    ) -> CheckResult:
        """
        Execute pytest command and parse results.

        Args:
            cmd: pytest command to execute
            test_name: Name of the test suite
            start_time: Start time for duration calculation
            json_report_path: Path to JSON report file
            env: Environment variables to use

        Returns:
            CheckResult containing test execution results
        """
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.pytest_config.get("timeout", 300),
                cwd=self.project_root,
                env=env or os.environ,
            )

            duration = time.time() - start_time

            # Parse JSON report if available
            test_data = (
                self._parse_json_report(json_report_path) if json_report_path else {}
            )

            # Parse pytest output
            output_data = self._parse_pytest_output(result.stdout, result.stderr)

            # Determine status based on exit code and results
            if result.returncode == 0:
                status = CheckStatus.SUCCESS
                errors = []
                warnings = output_data.get("warnings", [])
                suggestions = ["All tests passed successfully"]
                output = f"✅ {test_name} completed successfully\n{result.stdout}"

            elif result.returncode == 1:
                # Some tests failed
                status = CheckStatus.FAILURE
                errors = output_data.get("errors", [f"Some {test_name.lower()} failed"])
                warnings = output_data.get("warnings", [])
                suggestions = ["Review failed tests and fix the underlying issues"]
                output = f"❌ {test_name} had failures:\n{result.stdout}"

            elif result.returncode == 2:
                # Test execution was interrupted or had errors
                status = CheckStatus.FAILURE
                errors = [f"{test_name} execution was interrupted"]
                if result.stderr:
                    errors.append(f"Error details: {result.stderr}")
                warnings = []
                suggestions = ["Check test configuration and dependencies"]
                output = f"❌ {test_name} execution failed:\n{result.stderr}"

            else:
                # Other error codes
                status = CheckStatus.FAILURE
                errors = [f"{test_name} failed with exit code {result.returncode}"]
                if result.stderr:
                    errors.append(f"Error output: {result.stderr}")
                warnings = []
                suggestions = ["Check pytest configuration and test environment"]
                output = f"❌ {test_name} execution error:\n{result.stderr}"

            return CheckResult(
                name=test_name,
                status=status,
                duration=duration,
                output=output,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions,
                metadata={
                    "command": " ".join(cmd),
                    "exit_code": result.returncode,
                    "tests_collected": test_data.get("collected", 0),
                    "tests_passed": test_data.get("passed", 0),
                    "tests_failed": test_data.get("failed", 0),
                    "tests_skipped": test_data.get("skipped", 0),
                    "test_duration": test_data.get("duration", duration),
                    "json_report_path": (
                        str(json_report_path) if json_report_path else None
                    ),
                    "configuration": self.pytest_config,
                },
            )

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return CheckResult(
                name=test_name,
                status=CheckStatus.FAILURE,
                duration=duration,
                output=f"❌ {test_name} execution timed out",
                errors=[f"{test_name} execution timed out"],
                warnings=[],
                suggestions=["Increase timeout or optimize slow tests"],
                metadata={"timeout": True, "command": " ".join(cmd)},
            )

        except Exception as e:
            duration = time.time() - start_time
            return CheckResult(
                name=test_name,
                status=CheckStatus.FAILURE,
                duration=duration,
                output=f"❌ {test_name} execution failed: {str(e)}",
                errors=[f"Failed to execute {test_name}: {str(e)}"],
                warnings=[],
                suggestions=["Ensure pytest is properly installed and configured"],
                metadata={"exception": str(e), "command": " ".join(cmd)},
            )

    def _parse_json_report(self, json_report_path: Optional[Path]) -> Dict[str, Any]:
        """
        Parse pytest JSON report if available.

        Args:
            json_report_path: Path to JSON report file

        Returns:
            Dictionary containing parsed test data
        """
        if not json_report_path or not json_report_path.exists():
            return {}

        try:
            with open(json_report_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            return {
                "collected": data.get("summary", {}).get("collected", 0),
                "passed": data.get("summary", {}).get("passed", 0),
                "failed": data.get("summary", {}).get("failed", 0),
                "skipped": data.get("summary", {}).get("skipped", 0),
                "duration": data.get("duration", 0),
                "tests": data.get("tests", []),
            }

        except Exception as e:
            self.logger.warning(f"Failed to parse JSON report: {e}")
            return {}

    def _parse_pytest_output(self, stdout: str, stderr: str) -> Dict[str, List[str]]:
        """
        Parse pytest output to extract errors and warnings.

        Args:
            stdout: Standard output from pytest
            stderr: Standard error from pytest

        Returns:
            Dictionary containing parsed errors and warnings
        """
        errors = []
        warnings = []

        # Parse stdout for test results
        if stdout:
            lines = stdout.split("\n")
            for line in lines:
                if "FAILED" in line:
                    errors.append(line.strip())
                elif "WARNING" in line or "warning" in line.lower():
                    warnings.append(line.strip())

        # Parse stderr for system errors
        if stderr:
            lines = stderr.split("\n")
            for line in lines:
                if line.strip():
                    if "error" in line.lower() or "exception" in line.lower():
                        errors.append(line.strip())
                    else:
                        warnings.append(line.strip())

        return {"errors": errors, "warnings": warnings}

    def _needs_virtual_display(self) -> bool:
        """
        Check if virtual display is needed for GUI tests.

        Returns:
            True if virtual display should be set up
        """
        # Check if we're in a headless environment
        return os.environ.get("DISPLAY") is None and os.environ.get("CI") is not None

    def _setup_virtual_display(self) -> Dict[str, str]:
        """
        Setup virtual display environment variables.

        Returns:
            Dictionary of environment variables for virtual display
        """
        return {
            "QT_QPA_PLATFORM": "offscreen",
            "DISPLAY": ":99",
            "XVFB_RUN": "1",
        }

    def get_test_status(self) -> Dict[str, Any]:
        """
        Get current test configuration and discovered suites.

        Returns:
            Dictionary containing test status information
        """
        return {
            "available": self.is_available(),
            "test_suites_discovered": len(self.test_suites),
            "test_suites": [
                {
                    "name": suite.name,
                    "path": suite.path,
                    "type": suite.test_type,
                    "markers": suite.markers,
                }
                for suite in self.test_suites
            ],
            "configuration": self.pytest_config,
            "dependencies_available": {
                dep: self._is_tool_available(dep) for dep in self.dependencies
            },
        }

    def cleanup(self) -> None:
        """Clean up any temporary files or resources."""
        # Clean up JSON report files if configured to do so
        if self.config.get("cleanup_reports", False):
            reports_dir = self.project_root / "reports"
            if reports_dir.exists():
                for report_file in reports_dir.glob("*_tests.json"):
                    try:
                        report_file.unlink()
                    except Exception as e:
                        self.logger.warning(f"Failed to clean up {report_file}: {e}")

    def run_matrix_tests(
        self,
        test_types: List[str],
        python_versions: List[str],
        parallel: bool = True,
        coverage: bool = True,
    ) -> CheckResult:
        """
        Run tests across multiple Python versions in a matrix configuration.

        Args:
            test_ist of test types to run
            python_versions: List of Python versions to test with
            parallel: Whether to run tests in parallel across versions
            coverage: Whether to collect coverage data

        Returns:
            CheckResult containing matrix test results
        """
        start_time = time.time()
        self.logger.info(
            f"Starting matrix testing across Python versions: {python_versions}"
        )

        # Discover available Python versions
        available_versions = self._discover_python_versions()
        valid_versions = []

        for version in python_versions:
            if version in available_versions:
                valid_versions.append(version)
            else:
                self.logger.warning(f"Python version {version} not available")

        if not valid_versions:
            return CheckResult(
                name="Matrix Tests",
                status=CheckStatus.FAILURE,
                duration=time.time() - start_time,
                output="❌ No valid Python versions found for matrix testing",
                errors=["No valid Python versions available"],
                warnings=[],
                suggestions=[
                    "Install the required Python versions or check your configuration"
                ],
                metadata={
                    "requested_versions": python_versions,
                    "available_versions": list(available_versions.keys()),
                    "valid_versions": valid_versions,
                },
            )

        # Run tests for each Python version
        matrix_results = {}
        overall_status = CheckStatus.SUCCESS
        all_errors = []
        all_warnings = []
        all_suggestions = []
        combined_output = []

        if parallel and len(valid_versions) > 1:
            # Run versions in parallel
            matrix_results = self._run_parallel_matrix_tests(
                test_types, valid_versions, available_versions, coverage
            )
        else:
            # Run versions sequentially
            matrix_results = self._run_sequential_matrix_tests(
                test_types, valid_versions, available_versions, coverage
            )

        # Analyze matrix results
        for version, version_results in matrix_results.items():
            combined_output.append(
                f"=== Python {version} Results ===\n{version_results.output}"
            )

            if version_results.status == CheckStatus.FAILURE:
                overall_status = CheckStatus.FAILURE
            elif (
                version_results.status == CheckStatus.WARNING
                and overall_status == CheckStatus.SUCCESS
            ):
                overall_status = CheckStatus.WARNING

            all_errors.extend(
                [f"Python {version}: {error}" for error in version_results.errors]
            )
            all_warnings.extend(
                [f"Python {version}: {warning}" for warning in version_results.warnings]
            )
            all_suggestions.extend(version_results.suggestions)

        # Generate matrix comparison report
        comparison_report = self._generate_matrix_comparison(matrix_results)
        combined_output.append(f"=== Matrix Comparison ===\n{comparison_report}")

        duration = time.time() - start_time

        # Calculate totals across all versions
        total_tests = sum(
            result.metadata.get("total_tests", 0) for result in matrix_results.values()
        )
        passed_tests = sum(
            result.metadata.get("tests_passed", 0) for result in matrix_results.values()
        )
        failed_tests = sum(
            result.metadata.get("tests_failed", 0) for result in matrix_results.values()
        )

        return CheckResult(
            name="Matrix Tests",
            status=overall_status,
            duration=duration,
            output="\n\n".join(combined_output),
            errors=all_errors,
            warnings=all_warnings,
            suggestions=all_suggestions,
            metadata={
                "matrix_results": {
                    version: result.to_dict()
                    for version, result in matrix_results.items()
                },
                "python_versions_tested": valid_versions,
                "test_types_run": test_types,
                "total_tests": total_tests,
                "tests_passed": passed_tests,
                "tests_failed": failed_tests,
                "parallel_execution": parallel,
                "coverage_enabled": coverage,
                "version_comparison": self._analyze_version_differences(matrix_results),
            },
        )

    def _discover_python_versions(self) -> Dict[str, str]:
        """
        Discover available Python versions on the system.

        Returns:
            Dictionary mapping version strings to executable paths
        """
        available_versions = {}

        # Check current Python version
        current_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        available_versions[current_version] = sys.executable

        # Common Python version patterns to check
        version_patterns = ["3.9", "3.10", "3.11", "3.12"]

        for version in version_patterns:
            if version == current_version:
                continue

            # Try different executable names
            executables_to_try = [
                f"python{version}",
                f"python{version.replace('.', '')}",
                f"py -{version}",  # Windows py launcher
            ]

            for executable in executables_to_try:
                try:
                    result = subprocess.run(
                        [executable, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )

                    if result.returncode == 0 and version in result.stdout:
                        available_versions[version] = executable
                        break

                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue

        # Check for pyenv versions
        try:
            result = subprocess.run(
                ["pyenv", "versions", "--bare"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    version_match = re.match(r"^(\d+\.\d+)", line.strip())
                    if version_match:
                        version = version_match.group(1)
                        if version not in available_versions:
                            available_versions[version] = f"pyenv exec python{version}"

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Check for conda environments
        try:
            result = subprocess.run(
                ["conda", "env", "list"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "python" in line.lower():
                        # This is a simplified check - in practice, you'd want to
                        # activate the environment and check the Python version
                        pass

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return available_versions

    def _run_parallel_matrix_tests(
        self,
        test_types: List[str],
        python_versions: List[str],
        available_versions: Dict[str, str],
        coverage: bool,
    ) -> Dict[str, CheckResult]:
        """
        Run matrix tests in parallel across Python versions.

        Args:
            test_types: List of test types to run
            python_versions: List of Python versions to test
            available_versions: Dictionary of available Python executables
            coverage: Whether to collect coverage data

        Returns:
            Dictionary mapping Python versions to their test results
        """
        matrix_results = {}

        with ThreadPoolExecutor(max_workers=min(len(python_versions), 4)) as executor:
            # Submit test jobs for each Python version
            future_to_version = {
                executor.submit(
                    self._run_tests_for_version,
                    version,
                    available_versions[version],
                    test_types,
                    coverage,
                ): version
                for version in python_versions
            }

            # Collect results as they complete
            for future in as_completed(future_to_version):
                version = future_to_version[future]
                try:
                    result = future.result()
                    matrix_results[version] = result
                except Exception as e:
                    self.logger.error(f"Error running tests for Python {version}: {e}")
                    matrix_results[version] = CheckResult(
                        name=f"Python {version} Tests",
                        status=CheckStatus.FAILURE,
                        duration=0.0,
                        output="",
                        errors=[f"Failed to run tests: {str(e)}"],
                        warnings=[],
                        suggestions=[],
                        metadata={"python_version": version, "error": str(e)},
                    )

        return matrix_results

    def _run_sequential_matrix_tests(
        self,
        test_types: List[str],
        python_versions: List[str],
        available_versions: Dict[str, str],
        coverage: bool,
    ) -> Dict[str, CheckResult]:
        """
        Run matrix tests sequentially across Python versions.

        Args:
            test_types: List of test types to run
            python_versions: List of Python versions to test
            available_versions: Dictionary of available Python executables
            coverage: Whether to collect coverage data

        Returns:
            Dictionary mapping Python versions to their test results
        """
        matrix_results = {}

        for version in python_versions:
            self.logger.info(f"Running tests for Python {version}")

            try:
                result = self._run_tests_for_version(
                    version, available_versions[version], test_types, coverage
                )
                matrix_results[version] = result

            except Exception as e:
                self.logger.error(f"Error running tests for Python {version}: {e}")
                matrix_results[version] = CheckResult(
                    name=f"Python {version} Tests",
                    status=CheckStatus.FAILURE,
                    duration=0.0,
                    output="",
                    errors=[f"Failed to run tests: {str(e)}"],
                    warnings=[],
                    suggestions=[],
                    metadata={"python_version": version, "error": str(e)},
                )

        return matrix_results

    def _run_tests_for_version(
        self,
        python_version: str,
        python_executable: str,
        test_types: List[str],
        coverage: bool,
    ) -> CheckResult:
        """
        Run tests for a specific Python version.

        Args:
            python_version: Python version string (e.g., "3.9")
            python_executable: Path to Python executable
            test_types: List of test types to run
            coverage: Whether to collect coverage data

        Returns:
            CheckResult containing the test results for this Python version
        """
        start_time = time.time()

        all_results = {}
        overall_status = CheckStatus.SUCCESS
        all_errors = []
        all_warnings = []
        all_suggestions = []
        combined_output = []

        # Run each test type with the specified Python version
        for test_type in test_types:
            try:
                if test_type == "unit":
                    result = self._run_unit_tests_with_python(
                        python_executable, coverage=coverage
                    )
                elif test_type == "integration":
                    result = self._run_integration_tests_with_python(python_executable)
                elif test_type == "performance":
                    result = self._run_performance_tests_with_python(python_executable)
                elif test_type == "ai_compatibility":
                    result = self._run_ai_compatibility_tests_with_python(
                        python_executable
                    )
                else:
                    continue

                all_results[test_type] = result
                combined_output.append(
                    f"=== {test_type.title()} Tests ===\n{result.output}"
                )

                if result.status == CheckStatus.FAILURE:
                    overall_status = CheckStatus.FAILURE
                elif (
                    result.status == CheckStatus.WARNING
                    and overall_status == CheckStatus.SUCCESS
                ):
                    overall_status = CheckStatus.WARNING

                all_errors.extend(result.errors)
                all_warnings.extend(result.warnings)
                all_suggestions.extend(result.suggestions)

            except Exception as e:
                error_msg = f"Failed to run {test_type} tests with Python {python_version}: {str(e)}"
                all_errors.append(error_msg)
                overall_status = CheckStatus.FAILURE

        duration = time.time() - start_time

        # Calculate totals for this version
        total_tests = sum(
            result.metadata.get("tests_collected", 0) for result in all_results.values()
        )
        passed_tests = sum(
            result.metadata.get("tests_passed", 0) for result in all_results.values()
        )
        failed_tests = sum(
            result.metadata.get("tests_failed", 0) for result in all_results.values()
        )

        return CheckResult(
            name=f"Python {python_version} Tests",
            status=overall_status,
            duration=duration,
            output="\n\n".join(combined_output),
            errors=all_errors,
            warnings=all_warnings,
            suggestions=all_suggestions,
            metadata={
                "python_version": python_version,
                "python_executable": python_executable,
                "individual_results": {
                    name: result.to_dict() for name, result in all_results.items()
                },
                "test_types_run": test_types,
                "total_tests": total_tests,
                "tests_passed": passed_tests,
                "tests_failed": failed_tests,
            },
        )

    def _run_unit_tests_with_python(
        self, python_executable: str, coverage: bool = True
    ) -> CheckResult:
        """Run unit tests with a specific Python executable."""
        start_time = time.time()

        # Build pytest command with specific Python executable
        cmd = [python_executable, "-m", "pytest"]
        cmd.extend(["-v", "--tb=short"])

        if coverage:
            cmd.extend(["--cov=src", "--cov-report=term-missing"])

        cmd.extend(["-m", "not slow and not integration and not ai_compatibility"])

        # Add test paths
        unit_suites = [s for s in self.test_suites if s.test_type == "unit"]
        if unit_suites:
            cmd.extend([s.path for s in unit_suites])
        else:
            cmd.append("tests/")

        # Add JSON report for parsing
        json_report_path = (
            self.project_root
            / "reports"
            / f"unit_tests_{python_executable.replace('/', '_').replace('.', '_')}.json"
        )
        json_report_path.parent.mkdir(parents=True, exist_ok=True)
        # JSON report removed - using standard pytest output instead

        return self._execute_pytest(cmd, "Unit Tests", start_time, json_report_path)

    def _run_integration_tests_with_python(self, python_executable: str) -> CheckResult:
        """Run integration tests with a specific Python executable."""
        start_time = time.time()

        # Setup virtual display if needed
        env = os.environ.copy()
        if self._needs_virtual_display():
            env.update(self._setup_virtual_display())

        # Build pytest command
        cmd = [python_executable, "-m", "pytest"]
        cmd.extend(["-v", "--tb=short"])
        cmd.extend(["-m", "integration"])

        # Add test paths
        integration_suites = [
            s for s in self.test_suites if s.test_type == "integration"
        ]
        if integration_suites:
            cmd.extend([s.path for s in integration_suites])
        else:
            cmd.extend(["tests/", "-k", "integration"])

        # Add JSON report for parsing
        json_report_path = (
            self.project_root
            / "reports"
            / f"integration_tests_{python_executable.replace('/', '_').replace('.', '_')}.json"
        )
        json_report_path.parent.mkdir(parents=True, exist_ok=True)
        # JSON report removed - using standard pytest output instead

        return self._execute_pytest(
            cmd, "Integration Tests", start_time, json_report_path, env=env
        )

    def _run_performance_tests_with_python(self, python_executable: str) -> CheckResult:
        """Run performance tests with a specific Python executable."""
        start_time = time.time()

        # Build pytest command
        cmd = [python_executable, "-m", "pytest"]
        cmd.extend(["-v", "--tb=short"])

        # Add benchmark options if available
        if self._is_tool_available("pytest-benchmark"):
            cmd.extend(
                [
                    "--benchmark-only",
                    f"--benchmark-json=reports/benchmark_{python_executable.replace('/', '_').replace('.', '_')}.json",
                ]
            )

        cmd.extend(["-m", "performance or slow"])

        # Add test paths
        performance_suites = [
            s for s in self.test_suites if s.test_type == "performance"
        ]
        if performance_suites:
            cmd.extend([s.path for s in performance_suites])
        else:
            cmd.extend(["tests/", "-k", "performance or benchmark"])

        # Add JSON report for parsing
        json_report_path = (
            self.project_root
            / "reports"
            / f"performance_tests_{python_executable.replace('/', '_').replace('.', '_')}.json"
        )
        json_report_path.parent.mkdir(parents=True, exist_ok=True)
        # JSON report removed - using standard pytest output instead

        return self._execute_pytest(
            cmd, "Performance Tests", start_time, json_report_path
        )

    def _run_ai_compatibility_tests_with_python(
        self, python_executable: str
    ) -> CheckResult:
        """Run AI compatibility tests with a specific Python executable."""
        start_time = time.time()

        # Setup virtual display if needed
        env = os.environ.copy()
        if self._needs_virtual_display():
            env.update(self._setup_virtual_display())

        # Build pytest command
        cmd = [python_executable, "-m", "pytest"]
        cmd.extend(["-v", "--tb=short"])
        cmd.extend(["-m", "ai_compatibility"])

        # Add test paths
        ai_suites = [s for s in self.test_suites if s.test_type == "ai_compatibility"]
        if ai_suites:
            cmd.extend([s.path for s in ai_suites])
        else:
            cmd.extend(["tests/", "-k", "ai or copilot or cursor or kiro"])

        # Add JSON report for parsing
        json_report_path = (
            self.project_root
            / "reports"
            / f"ai_compatibility_tests_{python_executable.replace('/', '_').replace('.', '_')}.json"
        )
        json_report_path.parent.mkdir(parents=True, exist_ok=True)
        # JSON report removed - using standard pytest output instead

        return self._execute_pytest(
            cmd, "AI Compatibility Tests", start_time, json_report_path, env=env
        )

    def _generate_matrix_comparison(
        self, matrix_results: Dict[str, CheckResult]
    ) -> str:
        """
        Generate a comparison report across Python versions.

        Args:
            matrix_results: Dictionary of test results by Python version

        Returns:
            String containing the comparison report
        """
        if not matrix_results:
            return "No matrix results to compare"

        lines = ["Python Version Comparison:"]
        lines.append("=" * 50)

        # Create comparison table
        headers = ["Version", "Status", "Tests", "Passed", "Failed", "Duration"]
        lines.append(
            f"{headers[0]:<10} {headers[1]:<10} {headers[2]:<8} {headers[3]:<8} {headers[4]:<8} {headers[5]:<10}"
        )
        lines.append("-" * 60)

        for version, result in sorted(matrix_results.items()):
            status_icon = "✅" if result.status == CheckStatus.SUCCESS else "❌"
            total_tests = result.metadata.get("total_tests", 0)
            passed_tests = result.metadata.get("tests_passed", 0)
            failed_tests = result.metadata.get("tests_failed", 0)
            duration = f"{result.duration:.1f}s"

            lines.append(
                f"{version:<10} {status_icon:<10} {total_tests:<8} {passed_tests:<8} {failed_tests:<8} {duration:<10}"
            )

        # Add version-specific issues
        version_issues = self._analyze_version_differences(matrix_results)
        if version_issues:
            lines.append("\nVersion-Specific Issues:")
            lines.append("-" * 30)
            for issue in version_issues:
                lines.append(f"• {issue}")

        return "\n".join(lines)

    def _analyze_version_differences(
        self, matrix_results: Dict[str, CheckResult]
    ) -> List[str]:
        """
        Analyze differences between Python version test results.

        Args:
            matrix_results: Dictionary of test results by Python version

        Returns:
            List of version-specific issues or differences
        """
        issues = []

        if len(matrix_results) < 2:
            return issues

        # Find versions with different outcomes
        successful_versions = []
        failed_versions = []

        for version, result in matrix_results.items():
            if result.status == CheckStatus.SUCCESS:
                successful_versions.append(version)
            else:
                failed_versions.append(version)

        if successful_versions and failed_versions:
            issues.append(
                f"Inconsistent results: {', '.join(successful_versions)} passed, "
                f"{', '.join(failed_versions)} failed"
            )

        # Check for version-specific errors
        error_patterns = {}
        for version, result in matrix_results.items():
            for error in result.errors:
                if error not in error_patterns:
                    error_patterns[error] = []
                error_patterns[error].append(version)

        for error, versions in error_patterns.items():
            if len(versions) < len(matrix_results):
                missing_versions = set(matrix_results.keys()) - set(versions)
                issues.append(
                    f"Error only in Python {', '.join(versions)}: {error[:100]}..."
                )

        return issues

    # Update existing test methods to accept python_version parameter
    def run_unit_tests(
        self,
        parallel: bool = True,
        coverage: bool = True,
        python_version: Optional[str] = None,
    ) -> CheckResult:
        """
        Run unit tests with pytest.

        Args:
            parallel: Whether to run tests in parallel
            coverage: Whether to collect coverage data
            python_version: Specific Python version to use

        Returns:
            CheckResult containing unit test results
        """
        if python_version:
            available_versions = self._discover_python_versions()
            if python_version in available_versions:
                return self._run_unit_tests_with_python(
                    available_versions[python_version], coverage=coverage
                )
            else:
                return CheckResult(
                    name="Unit Tests",
                    status=CheckStatus.FAILURE,
                    duration=0.0,
                    output=f"❌ Python version {python_version} not available",
                    errors=[f"Python version {python_version} not found"],
                    warnings=[],
                    suggestions=["Install the required Python version"],
                    metadata={"python_version": python_version},
                )

        # Use existing implementation for default Python version
        start_time = time.time()
        self.logger.info("Running unit tests")

        # Build pytest command
        cmd = [sys.executable, "-m", "pytest"]

        # Add basic options
        cmd.extend(["-v", "--tb=short"])

        # Add coverage if requested
        if coverage:
            cmd.extend(["--cov=src", "--cov-report=term-missing"])

        # Add parallel execution if requested and available
        if parallel and self._is_tool_available("pytest-xdist"):
            cmd.extend(["-n", "auto"])

        # Add markers to select unit tests
        cmd.extend(["-m", "not slow and not integration and not ai_compatibility"])

        # Add test paths
        unit_suites = [s for s in self.test_suites if s.test_type == "unit"]
        if unit_suites:
            cmd.extend([s.path for s in unit_suites])
        else:
            # Fallback to general test discovery
            cmd.append("tests/")

        # Add JSON report for parsing
        json_report_path = self.project_root / "reports" / "unit_tests.json"
        json_report_path.parent.mkdir(parents=True, exist_ok=True)
        # JSON report removed - using standard pytest output instead

        return self._execute_pytest(cmd, "Unit Tests", start_time, json_report_path)

    def run_integration_tests(
        self, parallel: bool = False, python_version: Optional[str] = None
    ) -> CheckResult:
        """
        Run integration tests with proper environment setup.

        Args:
            parallel: Whether to run tests in parallel (disabled by default for integration)
            python_version: Specific Python version to use

        Returns:
            CheckResult containing integration test results
        """
        if python_version:
            available_versions = self._discover_python_versions()
            if python_version in available_versions:
                return self._run_integration_tests_with_python(
                    available_versions[python_version]
                )
            else:
                return CheckResult(
                    name="Integration Tests",
                    status=CheckStatus.FAILURE,
                    duration=0.0,
                    output=f"❌ Python version {python_version} not available",
                    errors=[f"Python version {python_version} not found"],
                    warnings=[],
                    suggestions=["Install the required Python version"],
                    metadata={"python_version": python_version},
                )

        # Use existing implementation for default Python version
        start_time = time.time()
        self.logger.info("Running integration tests")

        # Setup virtual display if needed
        env = os.environ.copy()
        if self._needs_virtual_display():
            env.update(self._setup_virtual_display())

        # Build pytest command
        cmd = [sys.executable, "-m", "pytest"]

        # Add basic options
        cmd.extend(["-v", "--tb=short"])

        # Add parallel execution if requested (usually not recommended for integration tests)
        if parallel and self._is_tool_available("pytest-xdist"):
            cmd.extend(["-n", "2"])  # Limited parallelism for integration tests

        # Add markers to select integration tests
        cmd.extend(["-m", "integration"])

        # Add test paths
        integration_suites = [
            s for s in self.test_suites if s.test_type == "integration"
        ]
        if integration_suites:
            cmd.extend([s.path for s in integration_suites])
        else:
            # Fallback to pattern matching
            cmd.extend(["tests/", "-k", "integration"])

        # Add JSON report for parsing
        json_report_path = self.project_root / "reports" / "integration_tests.json"
        json_report_path.parent.mkdir(parents=True, exist_ok=True)
        # JSON report removed - using standard pytest output instead

        return self._execute_pytest(
            cmd, "Integration Tests", start_time, json_report_path, env=env
        )

    def run_performance_tests(
        self, python_version: Optional[str] = None
    ) -> CheckResult:
        """
        Run performance tests with benchmarking.

        Args:
            python_version: Specific Python version to use

        Returns:
            CheckResult containing performance test results
        """
        if python_version:
            available_versions = self._discover_python_versions()
            if python_version in available_versions:
                return self._run_performance_tests_with_python(
                    available_versions[python_version]
                )
            else:
                return CheckResult(
                    name="Performance Tests",
                    status=CheckStatus.FAILURE,
                    duration=0.0,
                    output=f"❌ Python version {python_version} not available",
                    errors=[f"Python version {python_version} not found"],
                    warnings=[],
                    suggestions=["Install the required Python version"],
                    metadata={"python_version": python_version},
                )

        # Use existing implementation for default Python version
        start_time = time.time()
        self.logger.info("Running performance tests")

        # Build pytest command
        cmd = [sys.executable, "-m", "pytest"]

        # Add basic options
        cmd.extend(["-v", "--tb=short"])

        # Add benchmark options if available
        if self._is_tool_available("pytest-benchmark"):
            cmd.extend(["--benchmark-only", "--benchmark-json=reports/benchmark.json"])

        # Add markers to select performance tests
        cmd.extend(["-m", "performance or slow"])

        # Add test paths
        performance_suites = [
            s for s in self.test_suites if s.test_type == "performance"
        ]
        if performance_suites:
            cmd.extend([s.path for s in performance_suites])
        else:
            # Fallback to pattern matching
            cmd.extend(["tests/", "-k", "performance or benchmark"])

        # Add JSON report for parsing
        json_report_path = self.project_root / "reports" / "performance_tests.json"
        json_report_path.parent.mkdir(parents=True, exist_ok=True)
        # JSON report removed - using standard pytest output instead

        return self._execute_pytest(
            cmd, "Performance Tests", start_time, json_report_path
        )

    def run_ai_compatibility_tests(
        self, python_version: Optional[str] = None
    ) -> CheckResult:
        """
        Run AI compatibility tests for Copilot, Cursor, and Kiro components.

        Args:
            python_version: Specific Python version to use

        Returns:
            CheckResult containing AI compatibility test results
        """
        if python_version:
            available_versions = self._discover_python_versions()
            if python_version in available_versions:
                return self._run_ai_compatibility_tests_with_python(
                    available_versions[python_version]
                )
            else:
                return CheckResult(
                    name="AI Compatibility Tests",
                    status=CheckStatus.FAILURE,
                    duration=0.0,
                    output=f"❌ Python version {python_version} not available",
                    errors=[f"Python version {python_version} not found"],
                    warnings=[],
                    suggestions=["Install the required Python version"],
                    metadata={"python_version": python_version},
                )

        # Use existing implementation for default Python version
        start_time = time.time()
        self.logger.info("Running AI compatibility tests")

        # Setup virtual display if needed
        env = os.environ.copy()
        if self._needs_virtual_display():
            env.update(self._setup_virtual_display())

        # Build pytest command
        cmd = [sys.executable, "-m", "pytest"]

        # Add basic options
        cmd.extend(["-v", "--tb=short"])

        # Add markers to select AI compatibility tests
        cmd.extend(["-m", "ai_compatibility"])

        # Add test paths
        ai_suites = [s for s in self.test_suites if s.test_type == "ai_compatibility"]
        if ai_suites:
            cmd.extend([s.path for s in ai_suites])
        else:
            # Fallback to pattern matching
            cmd.extend(["tests/", "-k", "ai or copilot or cursor or kiro"])

        # Add JSON report for parsing
        json_report_path = self.project_root / "reports" / "ai_compatibility_tests.json"
        json_report_path.parent.mkdir(parents=True, exist_ok=True)
        # JSON report removed - using standard pytest output instead

        return self._execute_pytest(
            cmd, "AI Compatibility Tests", start_time, json_report_path, env=env
        )
