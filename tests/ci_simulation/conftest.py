"""
Pytest configuration and fixtures for CI simulation tests.
"""

import pytest
import tempfile
import shutil
import os
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, MagicMock

# Add the tools/ci directory to the path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'tools', 'ci'))

from models import CheckResult, CheckStatus, SimulationResult, CheckTask
from interfaces import CheckerInterface


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_config():
    """Provide a sample configuration for testing."""
    return {
        'python_versions': ['3.9', '3.10', '3.11'],
        'timeout': 300,
        'parallel_jobs': 2,
        'output_dir': 'reports',
        'checkers': {
            'code_quality': {
                'enabled': True,
                'black': {'enabled': True, 'lgth': 88},
                'isort': {'enabled': True},
                'flake8': {'enabled': True, 'max_line_length': 88},
                'mypy': {'enabled': True}
            },
            'security': {
                'enabled': True,
                'safety': {'enabled': True},
                'bandit': {'enabled': True}
            },
            'performance': {
                'enabled': True,
                'regression_threshold': 30.0
            },
            'tests': {
                'enabled': True,
                'unit_tests': True,
                'integration_tests': True,
                'ai_tests': True
            }
        }
    }


@pytest.fixture
def sample_check_result():
    """Provide a sample CheckResult for testing."""
    return CheckResult(
        name="test_check",
        status=CheckStatus.SUCCESS,
        duration=1.5,
        output="Test completed successfully",
        errors=[],
        warnings=["Minor warning"],
        suggestions=["Consider optimization"],
        metadata={"test_count": 10, "coverage": 85.5}
    )


@pytest.fixture
def sample_failed_check_result():
    """Provide a sample failed CheckResult for testing."""
    return CheckResult(
        name="failed_check",
        status=CheckStatus.FAILURE,
        duration=0.8,
        output="Test failed with errors",
        errors=["Syntax error in line 42", "Import error"],
        warnings=[],
        suggestions=["Fix syntax errors", "Check imports"],
        metadata={"error_count": 2}
    )


@pytest.fixture
def sample_simulation_result(sample_check_result, sample_failed_check_result):
    """Provide a sample SimulationResult for testing."""
    return SimulationResult(
        overall_status=CheckStatus.WARNING,
        total_duration=5.3,
        check_results={
            "test_check": sample_check_result,
            "failed_check": sample_failed_check_result
        },
        python_versions_tested=["3.10", "3.11"],
        summary="2 checks completed: 1 success, 1 failure",
        report_paths={"markdown": "reports/test_report.md", "json": "reports/test_report.json"}
    )


@pytest.fixture
def mock_checker():
    """Create a mock checker for testing."""
    checker = Mock(spec=CheckerInterface)
    checker.name = "mock_checker"
    checker.check_type = "test"
    checker.dependencies = ["pytest"]
    checker.is_available.return_value = True
    checker.run_check.return_value = CheckResult(
        name="mock_check",
        status=CheckStatus.SUCCESS,
        duration=1.0,
        output="Mock check completed"
    )
    return checker


@pytest.fixture
def sample_check_tasks():
    """Provide sample CheckTask objects for testing."""
    return [
        CheckTask(
            name="code_quality",
            check_type="code_quality",
            dependencies=[],
            priority=1
        ),
        CheckTask(
            name="security_scan",
            check_type="security",
            dependencies=["code_quality"],
            priority=2
        ),
        CheckTask(
            name="unit_tests",
            check_type="tests",
            dependencies=["code_quality"],
            priority=3
        )
    ]


@pytest.fixture
def mock_subprocess():
    """Mock subprocess for testing external command execution."""
    with pytest.mock.patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Command executed successfully"
        mock_run.return_value.stderr = ""
        yield mock_run


@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def ci_tools_dir(project_root):
    """Get the CI tools directory."""
    return project_root / "tools" / "ci"


@pytest.fixture
def sample_python_file(temp_dir):
    """Create a sample Python file for testing."""
    file_path = os.path.join(temp_dir, "sample.py")
    with open(file_path, 'w') as f:
        f.write('''
def hello_world():
    """A simple hello world function."""
    print("Hello, World!")
    return "Hello, World!"

if __name__ == "__main__":
    hello_world()
''')
    return file_path


@pytest.fixture
def sample_requirements_file(temp_dir):
    """Create a sample requirements.txt file for testing."""
    file_path = os.path.join(temp_dir, "requirements.txt")
    with open(file_path, 'w') as f:
        f.write('''
pytest>=7.0.0
black>=22.0.0
isort>=5.0.0
flake8>=4.0.0
mypy>=0.900
safety>=2.0.0
bandit>=1.7.0
''')
    return file_path


@pytest.fixture
def mock_git_repo(temp_dir):
    """Create a mock git repository for testing."""
    git_dir = os.path.join(temp_dir, ".git")
    os.makedirs(git_dir)

    # Create a simple .gitignore file
    gitignore_path = os.path.join(temp_dir, ".gitignore")
    with open(gitignore_path, 'w') as f:
        f.write('''
__pycache__/
*.pyc
.pytest_cache/
.coverage
''')

    return temp_dir


@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Automatically cleanup test files after each test."""
    yield
    # Cleanup any test files that might have been created
    test_files = [
        "test_report.md",
        "test_report.json",
        "test_config.yaml",
        "test_results.json"
    ]

    for file in test_files:
        if os.path.exists(file):
            os.remove(file)


class MockEnvironment:
    """Mock environment for testing environment managers."""

    def __init__(self):
        self.python_versions = ["3.9", "3.10", "3.11"]
        self.qt_available = True
        self.display_available = True

    def get_python_version(self):
        return "3.10.0"

    def has_qt_dependencies(self):
        return self.qt_available

    def has_virtual_display(self):
        return self.display_available


@pytest.fixture
def mock_environment():
    """Provide a mock environment for testing."""
    return MockEnvironment()
