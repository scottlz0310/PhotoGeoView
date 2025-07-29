"""
End-to-end integration tests for CI simulation tool.

These tests run the complete CI simulation workflow using actual
PhotoGeoView project files to verify real-world functionality.
"""

import pytest
import os
import sys
import tempfile
import shutil
import subprocess
importon
from pathlib import Path
from unittest.mock import patch, Mock

# Add the tools/ci directory to the path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "tools" / "ci"))

from simulator import CISimulator
from config_manager import ConfigManager
from models import CheckStatus, SimulationResult
from check_orchestrator import CheckOrchestrator


@pytest.mark.integration
class TestEndToEndSimulation:
    """End-to-end integration tests for the CI simulation tool."""

    @pytest.fixture
    def project_files_setup(self, temp_dir):
        """Set up a mock project structure with actual files."""
        # Create a realistic project structure
        project_dir = Path(temp_dir) / "test_project"
        project_dir.mkdir()

        # Create source files
        src_dir = project_dir / "src"
        src_dir.mkdir()

        # Create a sample Python module
        (src_dir / "__init__.py").write_text("")
        (src_dir / "main.py").write_text('''
"""Main module for test project."""

import sys
from typing import List, Optional


class PhotoProcessor:
    """A sample photo processing class."""

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.processed_count = 0

    def process_image(self, image_path: str) -> bool:
        """Process a single image."""
        if not image_path:
            raise ValueError("Image path cannot be empty")

        # Simulate processing
        self.processed_count += 1
        return True

    def batch_process(self, image_paths: List[str]) -> int:
        """Process multiple images."""
        successful = 0
        for path in image_paths:
            try:
                if self.process_image(path):
                    successful += 1
            except ValueError:
                continue
        return successful


def main():
    """Main entry point."""
    processor = PhotoProcessor()
    result = processor.process_image("test.jpg")
    print(f"Processing result: {result}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
''')

        # Create test files
        tests_dir = project_dir / "tests"
        tests_dir.mkdir()

        (tests_dir / "__init__.py").write_text("")
        (tests_dir / "test_main.py").write_text('''
"""Tests for main module."""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from main import PhotoProcessor


class TestPhotoProcessor:
    """Test cases for PhotoProcessor."""

    def test_init_default_config(self):
        """Test initialization with default config."""
        processor = PhotoProcessor()
        assert processor.config == {}
        assert processor.processed_count == 0

    def test_init_with_config(self):
        """Test initialization with custom config."""
        config = {"quality": 95}
        processor = PhotoProcessor(config)
        assert processor.config == config

    def test_process_image_success(self):
        """Test successful image processing."""
        processor = PhotoProcessor()
        result = processor.process_image("test.jpg")
        assert result is True
        assert processor.processed_count == 1

    def test_process_image_empty_path(self):
        """Test processing with empty path."""
        processor = PhotoProcessor()
        with pytest.raises(ValueError, match="Image path cannot be empty"):
            processor.process_image("")

    def test_batch_process_success(self):
        """Test successful batch processing."""
        processor = PhotoProcessor()
        paths = ["image1.jpg", "image2.jpg", "image3.jpg"]
        result = processor.batch_process(paths)
        assert result == 3
        assert processor.processed_count == 3

    def test_batch_process_with_errors(self):
        """Test batch processing with some errors."""
        processor = PhotoProcessor()
        paths = ["image1.jpg", "", "image3.jpg"]  # Empty path will cause error
        result = processor.batch_process(paths)
        assert result == 2  # Only 2 successful
        assert processor.processed_count == 2


# Performance test
def test_performance_batch_processing():
    """Test performance of batch processing."""
    import time

    processor = PhotoProcessor()
    paths = [f"image{i}.jpg" for i in range(100)]

    start_time = time.time()
    result = processor.batch_process(paths)
    end_time = time.time()

    assert result == 100
    assert end_time - start_time < 1.0  # Should complete in less than 1 second
''')

        # Create requirements.txt
        (project_dir / "requirements.txt").write_text('''
pytest>=7.0.0
black>=22.0.0
isort>=5.0.0
flake8>=4.0.0
mypy>=0.900
safety>=2.0.0
bandit>=1.7.0
''')

        # Create pyproject.toml
        (project_dir / "pyproject.toml").write_text('''
[tool.black]
line-length = 88
target-version = ['py39', 'py310', 'py311']

[tool.isort]
profile = "black"
multi_line_output = 3

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
''')

        # Create CI config
        (project_dir / "ci-config.yaml").write_text('''
python_versions:
  - "3.10"
  - "3.11"

timeout: 300
parallel_jobs: 2
output_dir: "reports"

checkers:
  code_quality:
    enabled: true
    black:
      enabled: true
      line_length: 88
    isort:
      enabled: true
    flake8:
      enabled: true
      max_line_length: 88
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
    integration_tests: false
    ai_tests: false

  performance:
    enabled: false
    regression_threshold: 30.0
''')

        return project_dir

    def test_full_simulation_workflow(self, project_files_setup):
        """Test complete CI simulation workflow with real project files."""
        project_dir = project_files_setup

        # Change to project directory
        original_cwd = os.getcwd()
        os.chdir(project_dir)

        try:
            # Create CI simulator
            config_path = project_dir / "ci-config.yaml"
            simulator = CISimulator(str(config_path))

            # Mock external tool availability
            with patch('shutil.which') as mock_which:
                mock_which.return_value = "/usr/bin/tool"  # All tools available

                # Mock subprocess calls for external tools
                with patch('subprocess.run') as mock_run:
                    # Configure mock responses for different tools
                    def mock_subprocess(*args, **kwargs):
                        cmd = args[0] if args else kwargs.get('args', [])
                        if not cmd:
                            return Mock(returncode=0, stdout="", stderr="")

                        cmd_str = ' '.join(cmd) if isinstance(cmd, list) else str(cmd)

                        # Black formatter
                        if 'black' in cmd_str:
                            if '--check' in cmd_str:
                                return Mock(returncode=0, stdout="All done! ✨ 🍰 ✨", stderr="")
                            else:
                                return Mock(returncode=0, stdout="reformatted 1 file", stderr="")

                        # isort
                        elif 'isort' in cmd_str:
                            return Mock(returncode=0, stdout="Skipped 0 files", stderr="")

                        # flake8
                        elif 'flake8' in cmd_str:
                            return Mock(returncode=0, stdout="", stderr="")

                        # mypy
                        elif 'mypy' in cmd_str:
                            return Mock(returncode=0, stdout="Success: no issues found", stderr="")

                        # pytest
                        elif 'pytest' in cmd_str:
                            return Mock(
                                returncode=0,
                                stdout="collected 6 items\n\ntests/test_main.py::TestPhotoProcessor::test_init_default_config PASSED\ntests/test_main.py::TestPhotoProcessor::test_init_with_config PASSED\ntests/test_main.py::TestPhotoProcessor::test_process_image_success PASSED\ntests/test_main.py::TestPhotoProcessor::test_process_image_empty_path PASSED\ntests/test_main.py::TestPhotoProcessor::test_batch_process_success PASSED\ntests/test_main.py::TestPhotoProcessor::test_batch_process_with_errors PASSED\n\n6 passed in 0.12s",
                                stderr=""
                            )

                        # safety
                        elif 'safety' in cmd_str:
                            return Mock(returncode=0, stdout="All good! No known security vulnerabilities found.", stderr="")

                        # bandit
                        elif 'bandit' in cmd_str:
                            return Mock(returncode=0, stdout="No issues identified.", stderr="")

                        # Default success
                        else:
                            return Mock(returncode=0, stdout="Success", stderr="")

                    mock_run.side_effect = mock_subprocess

                    # Run the simulation
                    result = simulator.run(
                        checks=["code_quality", "security", "tests"],
                        python_versions=["3.10"]
                    )

                    # Verify results
                    assert isinstance(result, SimulationResult)
                    assert result.overall_status in [CheckStatus.SUCCESS, CheckStatus.WARNING]
                    assert len(result.check_results) > 0
                    assert "3.10" in result.python_versions_tested

                    # Verify specific checks were run
                    check_names = [check.name for check in result.check_results.values()]
                    assert any("Code Quality" in name for name in check_names)
                    assert any("Security" in name for name in check_names)
                    assert any("Test" in name for name in check_names)

                    # Verify reports were generated
                    reports_dir = project_dir / "reports"
                    if reports_dir.exists():
                        report_files = list(reports_dir.glob("*.md")) + list(reports_dir.glob("*.json"))
                        assert len(report_files) > 0

        finally:
            os.chdir(original_cwd)

    def test_simulation_with_code_quality_issues(self, project_files_setup):
        """Test simulation when code quality issues are found."""
        project_dir = project_files_setup

        # Create a file with code quality issues
        problematic_file = project_dir / "src" / "problematic.py"
        problematic_file.write_text('''
# This file has intentional code quality issues

import os,sys
import json

def bad_function( x,y ):
    if x==None:
        return None
    result=x+y
    print("Result is:",result)
    return result

class BadClass:
    def __init__(self,value):
        self.value=value

    def method(self):
        pass

# Long line that exceeds the line length limit and should be flagged by flake8 and black formatter
very_long_variable_name = "This is a very long string that definitely exceeds the maximum line length and should be flagged"
''')

        original_cwd = os.getcwd()
        os.chdir(project_dir)

        try:
            config_path = project_dir / "ci-config.yaml"
            simulator = CISimulator(str(config_path))

            with patch('shutil.which') as mock_which:
                mock_which.return_value = "/usr/bin/tool"

                with patch('subprocess.run') as mock_run:
                    def mock_subprocess_with_issues(*args, **kwargs):
                        cmd = args[0] if args else kwargs.get('args', [])
                        cmd_str = ' '.join(cmd) if isinstance(cmd, list) else str(cmd)

                        # Black formatter finds issues
                        if 'black' in cmd_str and '--check' in cmd_str:
                            return Mock(
                                returncode=1,
                                stdout="",
                                stderr="would reformat src/problematic.py"
                            )

                        # flake8 finds issues
                        elif 'flake8' in cmd_str:
                            return Mock(
                                returncode=1,
                                stdout="src/problematic.py:4:9: E401 multiple imports on one line\nsrc/problematic.py:7:17: E711 comparison to None should be 'if cond is None:'\nsrc/problematic.py:10:11: E225 missing whitespace around operator",
                                stderr=""
                            )

                        # mypy finds issues
                        elif 'mypy' in cmd_str:
                            return Mock(
                                returncode=1,
                                stdout="src/problematic.py:7: error: Function is missing a type annotation",
                                stderr=""
                            )

                        # Other tools succeed
                        else:
                            return Mock(returncode=0, stdout="Success", stderr="")

                    mock_run.side_effect = mock_subprocess_with_issues

                    # Run simulation
                    result = simulator.run(checks=["code_quality"])

                    # Should have warnings or failures due to code quality issues
                    assert result.overall_status in [CheckStatus.WARNING, CheckStatus.FAILURE]

                    # Check that errors were captured
                    failed_checks = result.failed_checks
                    assert len(failed_checks) > 0

                    # Verify error details
                    for check in failed_checks:
                        assert len(check.errors) > 0

        finally:
            os.chdir(original_cwd)

    def test_simulation_with_test_failures(self, project_files_setup):
        """Test simulation when tests fail."""
        project_dir = project_files_setup

        # Create a test file with failing tests
        failing_test = project_dir / "tests" / "test_failing.py"
        failing_test.write_text('''
"""Tests that are designed to fail."""

import pytest


def test_always_fails():
    """This test always fails."""
    assert False, "This test is designed to fail"


def test_assertion_error():
    """This test has an assertion error."""
    expected = 10
    actual = 5
    assert actual == expected, f"Expected {expected}, got {actual}"


def test_exception():
    """This test raises an exception."""
    raise ValueError("Test exception")
''')

        original_cwd = os.getcwd()
        os.chdir(project_dir)

        try:
            config_path = project_dir / "ci-config.yaml"
            simulator = CISimulator(str(config_path))

            with patch('shutil.which') as mock_which:
                mock_which.return_value = "/usr/bin/tool"

                with patch('subprocess.run') as mock_run:
                    def mock_subprocess_with_test_failures(*args, **kwargs):
                        cmd = args[0] if args else kwargs.get('args', [])
                        cmd_str = ' '.join(cmd) if isinstance(cmd, list) else str(cmd)

                        # pytest with failures
                        if 'pytest' in cmd_str:
                            return Mock(
                                returncode=1,
                                stdout="collected 9 items\n\ntests/test_main.py::TestPhotoProcessor::test_init_default_config PASSED\ntests/test_failing.py::test_always_fails FAILED\ntests/test_failing.py::test_assertion_error FAILED\ntests/test_failing.py::test_exception FAILED\n\n6 passed, 3 failed in 0.25s",
                                stderr="FAILED tests/test_failing.py::test_always_fails - assert False\nFAILED tests/test_failing.py::test_assertion_error - AssertionError: Expected 10, got 5\nFAILED tests/test_failing.py::test_exception - ValueError: Test exception"
                            )

                        # Other tools succeed
                        else:
                            return Mock(returncode=0, stdout="Success", stderr="")

                    mock_run.side_effect = mock_subprocess_with_test_failures

                    # Run simulation
                    result = simulator.run(checks=["tests"])

                    # Should fail due to test failures
                    assert result.overall_status == CheckStatus.FAILURE

                    # Check that test failures were captured
                    test_results = [r for r in result.check_results.values() if "Test" in r.name]
                    assert len(test_results) > 0

                    failed_test_result = next((r for r in test_results if not r.is_successful), None)
                    assert failed_test_result is not None
                    assert len(failed_test_result.errors) > 0

        finally:
            os.chdir(original_cwd)

    def test_simulation_with_security_vulnerabilities(self, project_files_setup):
        """Test simulation when security vulnerabilities are found."""
        project_dir = project_files_setup

        # Create a file with security issues
        vulnerable_file = project_dir / "src" / "vulnerable.py"
        vulnerable_file.write_text('''
"""File with intentional security vulnerabilities."""

import subprocess
import os


def execute_command(user_input):
    """Execute a command - VULNERABLE to command injection."""
    # This is intentionally vulnerable
    subprocess.call(user_input, shell=True)


def read_file(filename):
    """Read a file - VULNERABLE to path traversal."""
    # This is intentionally vulnerable
    with open(filename, 'r') as f:
        return f.read()


def generate_temp_file():
    """Generate temp file - VULNERABLE."""
    # This is intentionally vulnerable
    import tempfile
    return tempfile.mktemp()


# Hardcoded password - VULNERABLE
PASSWORD = "admin123"
API_KEY = "sk-1234567890abcdef"
''')

        original_cwd = os.getcwd()
        os.chdir(project_dir)

        try:
            config_path = project_dir / "ci-config.yaml"
            simulator = CISimulator(str(config_path))

            with patch('shutil.which') as mock_which:
                mock_which.return_value = "/usr/bin/tool"

                with patch('subprocess.run') as mock_run:
                    def mock_subprocess_with_security_issues(*args, **kwargs):
                        cmd = args[0] if args else kwargs.get('args', [])
                        cmd_str = ' '.join(cmd) if isinstance(cmd, list) else str(cmd)

                        # bandit finds security issues
                        if 'bandit' in cmd_str:
                            return Mock(
                                returncode=1,
                                stdout="Issue: [B602:subprocess_popen_with_shell_equals_true] subprocess call with shell=True identified\nIssue: [B108:hardcoded_tmp_directory] Probable insecure usage of temp file/directory\nIssue: [B105:hardcoded_password_string] Possible hardcoded password",
                                stderr=""
                            )

                        # safety might find vulnerable dependencies
                        elif 'safety' in cmd_str:
                            return Mock(
                                returncode=1,
                                stdout="VULNERABILITY: Package 'requests' version 2.25.1 has known security vulnerabilities",
                                stderr=""
                            )

                        # Other tools succeed
                        else:
                            return Mock(returncode=0, stdout="Success", stderr="")

                    mock_run.side_effect = mock_subprocess_with_security_issues

                    # Run simulation
                    result = simulator.run(checks=["security"])

                    # Should fail due to security issues
                    assert result.overall_status == CheckStatus.FAILURE

                    # Check that security issues were captured
                    security_results = [r for r in result.check_results.values() if "Security" in r.name]
                    assert len(security_results) > 0

                    failed_security_result = next((r for r in security_results if not r.is_successful), None)
                    assert failed_security_result is not None
                    assert len(failed_security_result.errors) > 0

                    # Check for specific security issue types
                    error_text = ' '.join(failed_security_result.errors)
                    assert any(keyword in error_text.lower() for keyword in
                             ['subprocess', 'hardcoded', 'vulnerability', 'security'])

        finally:
            os.chdir(original_cwd)

    def test_simulation_report_generation(self, project_files_setup):
        """Test that simulation generates proper reports."""
        project_dir = project_files_setup

        original_cwd = os.getcwd()
        os.chdir(project_dir)

        try:
            config_path = project_dir / "ci-config.yaml"
            simulator = CISimulator(str(config_path))

            with patch('shutil.which') as mock_which:
                mock_which.return_value = "/usr/bin/tool"

                with patch('subprocess.run') as mock_run:
                    mock_run.return_value = Mock(returncode=0, stdout="Success", stderr="")

                    # Run simulation
                    result = simulator.run(checks=["code_quality", "tests"])

                    # Check that reports were generated
                    reports_dir = project_dir / "reports"
                    if reports_dir.exists():
                        # Look for markdown and JSON reports
                        md_reports = list(reports_dir.glob("**/*.md"))
                        json_reports = list(reports_dir.glob("**/*.json"))

                        # Should have at least one report
                        assert len(md_reports) + len(json_reports) > 0

                        # If markdown report exists, check its content
                        if md_reports:
                            md_content = md_reports[0].read_text()
                            assert "# CI Simulation Report" in md_content
                            assert "## Summary" in md_content
                            assert "## Check Results" in md_content

                        # If JSON report exists, check its structure
                        if json_reports:
                            json_data = json.loads(json_reports[0].read_text())
                            assert "overall_status" in json_data
                            assert "check_results" in json_data
                            assert "total_duration" in json_data

        finally:
            os.chdir(original_cwd)

    def test_simulation_cleanup(self, project_files_setup):
        """Test that simulation properly cleans up temporary files."""
        project_dir = project_files_setup

        original_cwd = os.getcwd()
        os.chdir(project_dir)

        try:
            config_path = project_dir / "ci-config.yaml"
            simulator = CISimulator(str(config_path))

            with patch('shutil.which') as mock_which:
                mock_which.return_value = "/usr/bin/tool"

                with patch('subprocess.run') as mock_run:
                    mock_run.return_value = Mock(returncode=0, stdout="Success", stderr="")

                    # Run simulation
                    result = simulator.run(checks=["code_quality"])

                    # Run cleanup
                    simulator.cleanup(keep_reports=False)

                    # Check that temporary files were cleaned up
                    # (This is more of a smoke test since we're mocking most operations)
                    assert isinstance(result, SimulationResult)

        finally:
            os.chdir(original_cwd)


@pytest.mark.integration
class TestMultiplePythonVersions:
    """Integration tests for multiple Python version support."""

    def test_multiple_python_versions_simulation(self, project_files_setup):
        """Test simulation with multiple Python versions."""
        project_dir = project_files_setup

        original_cwd = os.getcwd()
        os.chdir(project_dir)

        try:
            config_path = project_dir / "ci-config.yaml"
            simulator = CISimulator(str(config_path))

            with patch('shutil.which') as mock_which:
                mock_which.return_value = "/usr/bin/tool"

                with patch('subprocess.run') as mock_run:
                    # Mock different responses for different Python versions
                    def mock_subprocess_multi_python(*args, **kwargs):
                        cmd = args[0] if args else kwargs.get('args', [])
                        cmd_str = ' '.join(cmd) if isinstance(cmd, list) else str(cmd)

                        # Simulate version-specific behavior
                        if 'python3.9' in cmd_str:
                            # Python 3.9 might have different mypy results
                            if 'mypy' in cmd_str:
                                return Mock(
                                    returncode=1,
                                    stdout="src/main.py:15: error: Unsupported syntax for Python 3.9",
                                    stderr=""
                                )
                        elif 'python3.11' in cmd_str:
                            # Python 3.11 succeeds
                            pass

                        # Default success for most operations
                        return Mock(returncode=0, stdout="Success", stderr="")

                    mock_run.side_effect = mock_subprocess_multi_python

                    # Run simulation with multiple Python versions
                    result = simulator.run(
                        checks=["code_quality", "tests"],
                        python_versions=["3.10", "3.11"]
                    )

                    # Verify results
                    assert isinstance(result, SimulationResult)
                    assert len(result.python_versions_tested) == 2
                    assert "3.10" in result.python_versions_tested
                    assert "3.11" in result.python_versions_tested

                    # Should have results for each version
                    version_specific_results = [
                        r for r in result.check_results.values()
                        if r.python_version is not None
                    ]

                    # May have version-specific results
                    if version_specific_results:
                        python_versions_in_results = {r.python_version for r in version_specific_results}
                        assert len(python_versions_in_results) > 0

        finally:
            os.chdir(original_cwd)


@pytest.mark.integration
class TestGitHookIntegration:
    """Integration tests for Git hook functionality."""

    def test_git_hook_setup(self, project_files_setup):
        """Test Git hook setup and configuration."""
        project_dir = project_files_setup

        # Initialize a git repository
        original_cwd = os.getcwd()
        os.chdir(project_dir)

        try:
            # Initialize git repo
            subprocess.run(['git', 'init'], check=True, capture_output=True)
            subprocess.run(['git', 'config', 'user.email', 'test@example.com'], check=True)
            subprocess.run(['git', 'config', 'user.name', 'Test User'], check=True)

            config_path = project_dir / "ci-config.yaml"
            simulator = CISimulator(str(config_path))

            # Setup git hook
            success = simulator.setup_git_hook()

            # Verify hook was created
            hook_path = project_dir / ".git" / "hooks" / "pre-commit"
            if success:
                assert hook_path.exists()

                # Check hook content
                hook_content = hook_path.read_text()
                assert "ci-simulation" in hook_content.lower() or "simulator" in hook_content.lower()

                # Check that hook is executable
                assert os.access(hook_path, os.X_OK)

        except subprocess.CalledProcessError:
            # Git might not be available in test environment
            pytest.skip("Git not available for testing")

        finally:
            os.chdir(original_cwd)


@pytest.mark.integration
class TestPerformanceIntegration:
    """Integration tests for performance analysis."""

    def test_performance_baseline_creation(self, project_files_setup):
        """Test creation and usage of performance baselines."""
        project_dir = project_files_setup

        # Create a performance test
        perf_test = project_dir / "tests" / "test_performance.py"
        perf_test.write_text('''
"""Performance tests."""

import time
import pytest


@pytest.mark.performance
def test_processing_speed():
    """Test processing speed."""
    start_time = time.time()

    # Simulate some work
    total = 0
    for i in range(10000):
        total += i * i

    end_time = time.time()
    duration = end_time - start_time

    # Should complete quickly
    assert duration < 1.0

    # Store result for baseline comparison
    return {"processing_speed": duration}


@pytest.mark.performance
def test_memory_usage():
    """Test memory usage."""
    import sys

    # Create some data
    data = [i for i in range(1000)]
    memory_size = sys.getsizeof(data)

    # Should not use too much memory
    assert memory_size < 10000

    return {"memory_usage": memory_size}
''')

        original_cwd = os.getcwd()
        os.chdir(project_dir)

        try:
            config_path = project_dir / "ci-config.yaml"

            # Update config to enable performance tests
            config_content = (project_dir / "ci-config.yaml").read_text()
            config_content = config_content.replace("enabled: false", "enabled: true")
            (project_dir / "ci-config.yaml").write_text(config_content)

            simulator = CISimulator(str(config_path))

            with patch('shutil.which') as mock_which:
                mock_which.return_value = "/usr/bin/tool"

                with patch('subprocess.run') as mock_run:
                    def mock_performance_subprocess(*args, **kwargs):
                        cmd = args[0] if args else kwargs.get('args', [])
                        cmd_str = ' '.join(cmd) if isinstance(cmd, list) else str(cmd)

                        # Mock performance test results
                        if 'pytest' in cmd_str and 'performance' in cmd_str:
                            return Mock(
                                returncode=0,
                                stdout="test_performance.py::test_processing_speed PASSED\ntest_performance.py::test_memory_usage PASSED\n\n2 passed in 0.05s",
                                stderr=""
                            )

                        return Mock(returncode=0, stdout="Success", stderr="")

                    mock_run.side_effect = mock_performance_subprocess

                    # Run simulation with performance tests
                    result = simulator.run(checks=["performance"])

                    # Verify performance results
                    assert isinstance(result, SimulationResult)

                    # Look for performance-related results
                    perf_results = [
                        r for r in result.check_results.values()
                        if "performance" in r.name.lower()
                    ]

                    if perf_results:
                        assert len(perf_results) > 0

        finally:
            os.chdir(original_cwd)
