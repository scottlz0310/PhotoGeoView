#!/usr/bin/env python3
"""
Test script for CLI Parser functionality

This script tests the command-line argument parsing and validation
functionality of the CI simulation tool.
"""

import os
import sys
from pathlib import Path
from unittest.mock import Mock

# Add the tools directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ci.check_orchestrator import CheckOrchestrator
from ci.cli_parser import CLIParser
from ci.models import CheckTask


def create_mock_orchestrator():
    """Create a mock orchestrator for testing."""
    mock_orchestrator = Mock(spec=CheckOrchestrator)
    mock_orchestrator.get_available_checks.return_value = [
        "code_quality",
        "test_runner",
        "security_scanner",
    ]
    mock_orchestrator.validate_check_selection.return_value = []
    mock_orchestrator.is_check_available.return_value = True
    mock_orchestrator.list_available_checks.return_value = {
        "code_quality": {
            "name": "Code Quality Checker",
            "check_type": "code_quality",
            "is_available": True,
            "dependencies": [],
            "description": "Checks code quality with Black, isort, flake8, mypy",
        },
        "test_runner": {
            "name": "Test Runner",
            "check_type": "test_runner",
            "is_available": True,
            "dependencies": ["code_quality"],
            "description": "Runs unit and integration tests",
        },
        "security_scanner": {
            "name": "Security Scanner",
            "check_type": "security_scanner",
            "is_available": True,
            "dependencies": [],
            "description": "Scans for security vulnerabilities",
        },
    }
    mock_orchestrator.get_check_info.return_value = {
        "name": "Code Quality Checker",
        "check_type": "code_quality",
        "is_available": True,
        "dependencies": [],
        "description": "Checks code quality with Black, isort, flake8, mypy",
    }
    mock_orchestrator.create_execution_plan.return_value = {
        "total_tasks": 2,
        "execution_levels": 2,
        "estimated_duration": 150.0,
        "execution_order": [
            {
                "level": 0,
                "tasks": ["code_quality"],
                "parallel_execution": False,
                "estimated_duration": 30.0,
            },
            {
                "level": 1,
                "tasks": ["test_runner"],
                "parallel_execution": False,
                "estimated_duration": 120.0,
            },
        ],
    }
    mock_orchestrator.suggest_checks_for_files.return_value = [
        "code_quality",
        "test_runner",
    ]

    return mock_orchestrator


def test_basic_argument_parsing():
    """Test basic argument parsing functionality."""
    print("Testing basic argument parsing...")

    orchestrator = create_mock_orchestrator()
    parser = CLIParser(orchestrator)

    try:
        # Test default run command
        args = parser.parse_args([])
        assert args.command == "run"
        print("✓ Default command parsing works")

        # Test explicit run command
        args = parser.parse_args(["run", "code_quality", "test_runner"])
        assert args.command == "run"
        assert args.checks == ["code_quality", "test_runner"]
        print("✓ Explicit run command parsing works")

        # Test list command
        args = parser.parse_args(["list"])
        assert args.command == "list"
        print("✓ List command parsing works")
        # Test info command
        args = parser.parse_args(["info", "code_quality"])
        assert args.command == "info"
        assert args.check_name == "code_quality"
        print("✓ Info command parsing works")

        # Test plan command
        args = parser.parse_args(["plan", "code_quality"])
        assert args.command == "plan"
        assert args.checks == ["code_quality"]
        print("✓ Plan command parsing works")

        print("✓ Basic argument parsing tests passed")
        return True

    except Exception as e:
        print(f"✗ Basic argument parsing tests failed: {e}")
        return False


def test_run_command_options():
    """Test run command with various options."""
    print("Testing run command options...")

    orchestrator = create_mock_orchestrator()
    parser = CLIParser(orchestrator)

    try:
        # Test with all flag
        args = parser.parse_args(["run", "--all"])
        assert args.all is True
        print("✓ --all flag parsing works")

        # Test with exclude
        args = parser.parse_args(["run", "--exclude", "security_scanner"])
        assert args.exclude == ["security_scanner"]
        print("✓ --exclude option parsing works")

        # Test with python versions
        args = parser.parse_args(["run", "--python-versions", "3.9", "3.10"])
        assert args.python_versions == ["3.9", "3.10"]
        print("✓ --python-versions option parsing works")

        # Test with parallel
        args = parser.parse_args(["run", "--parallel", "4"])
        assert args.parallel == 4
        print("✓ --parallel option parsing works")

        # Test with timeout
        args = parser.parse_args(["run", "--timeout", "300"])
        assert args.timeout == 300.0
        print("✓ --timeout option parsing works")

        # Test with output format
        args = parser.parse_args(["run", "--format", "json"])
        assert args.format == "json"
        print("✓ --format option parsing works")

        print("✓ Run command options tests passed")
        return True

    except Exception as e:
        print(f"✗ Run command options tests failed: {e}")
        return False


def test_argument_validation():
    """Test argument validation functionality."""
    print("Testing argument validation...")

    orchestrator = create_mock_orchestrator()
    parser = CLIParser(orchestrator)

    try:
        # Test valid arguments
        args = parser.parse_args(["run", "code_quality"])
        errors = parser.validate_args(args)
        assert len(errors) == 0
        print("✓ Valid arguments pass validation")

        # Test invalid check name validation
        orchestrator.validate_check_selection.return_value = [
            "Invalid check names: ['invalid_check']"
        ]
        args = parser.parse_args(["run", "invalid_check"])
        errors = parser.validate_args(args)
        assert len(errors) > 0
        print("✓ Invalid check names are caught")

        # Reset mock for other tests
        orchestrator.validate_check_selection.return_value = []

        # Test invalid parallel value
        args = parser.parse_args(["run", "--parallel", "0"])
        errors = parser.validate_args(args)
        assert any("Parallel tasks must be at least 1" in error for error in errors)
        print("✓ Invalid parallel value is caught")

        # Test invalid timeout value
        args = parser.parse_args(["run", "--timeout", "-10"])
        errors = parser.validate_args(args)
        assert any("Timeout must be positive" in error for error in errors)
        print("✓ Invalid timeout value is caught")

        print("✓ Argument validation tests passed")
        return True

    except Exception as e:
        print(f"✗ Argument validation tests failed: {e}")
        return False


def test_task_creation():
    """Test task creation from arguments."""
    print("Testing task creation from arguments...")

    orchestrator = create_mock_orchestrator()
    parser = CLIParser(orchestrator)

    try:
        # Test basic task creation
        args = parser.parse_args(["run", "code_quality"])
        tasks = parser.create_tasks_from_args(args)
        assert len(tasks) == 1
        assert tasks[0].name == "code_quality"
        assert tasks[0].check_type == "code_quality"
        print("✓ Basic task creation works")

        # Test multiple checks
        args = parser.parse_args(["run", "code_quality", "test_runner"])
        tasks = parser.create_tasks_from_args(args)
        assert len(tasks) == 2
        print("✓ Multiple check task creation works")

        # Test with Python versions
        args = parser.parse_args(
            ["run", "code_quality", "--python-versions", "3.9", "3.10"]
        )
        tasks = parser.create_tasks_from_args(args)
        assert len(tasks) == 2  # 1 check × 2 Python versions
        assert any(task.python_version == "3.9" for task in tasks)
        assert any(task.python_version == "3.10" for task in tasks)
        print("✓ Python version task creation works")

        # Test with exclusions
        args = parser.parse_args(["run", "--all", "--exclude", "security_scanner"])
        tasks = parser.create_tasks_from_args(args)
        task_types = [task.check_type for task in tasks]
        assert "security_scanner" not in task_types
        assert "code_quality" in task_types
        assert "test_runner" in task_types
        print("✓ Exclusion task creation works")

        print("✓ Task creation tests passed")
        return True

    except Exception as e:
        print(f"✗ Task creation tests failed: {e}")
        return False


def test_configuration_creation():
    """Test configuration creation from arguments."""
    print("Testing configuration creation...")

    orchestrator = create_mock_orchestrator()
    parser = CLIParser(orchestrator)

    try:
        # Test basic configuration
        args = parser.parse_args(["run"])
        config = parser.get_execution_config(args)
        assert isinstance(config, dict)
        print("✓ Basic configuration creation works")

        # Test with parallel option
        args = parser.parse_args(["run", "--parallel", "4"])
        config = parser.get_execution_config(args)
        assert config.get("max_parallel_tasks") == 4
        print("✓ Parallel configuration works")

        # Test with fail-fast option
        args = parser.parse_args(["run", "--fail-fast"])
        config = parser.get_execution_config(args)
        assert config.get("fail_fast") is True
        print("✓ Fail-fast configuration works")

        # Test with format option
        args = parser.parse_args(["run", "--format", "json"])
        config = parser.get_execution_config(args)
        assert config.get("report_format") == "json"
        print("✓ Format configuration works")

        print("✓ Configuration creation tests passed")
        return True

    except Exception as e:
        print(f"✗ Configuration creation tests failed: {e}")
        return False


def test_output_functions():
    """Test output functions (without actually printing)."""
    print("Testing output functions...")

    orchestrator = create_mock_orchestrator()
    parser = CLIParser(orchestrator)

    try:
        # Test that functions don't crash
        # We can't easily test the actual output without capturing stdout

        # These should not raise exceptions
        parser.print_available_checks(detailed=False, format_type="table")
        parser.print_available_checks(detailed=True, format_type="json")
        parser.print_check_info("code_quality")

        # Test execution plan
        args = parser.parse_args(["run", "code_quality"])
        tasks = parser.create_tasks_from_args(args)
        parser.print_execution_plan(tasks, format_type="table")
        parser.print_execution_plan(tasks, format_type="json")

        print("✓ Output functions work without errors")
        return True

    except Exception as e:
        print(f"✗ Output functions tests failed: {e}")
        return False


def main():
    """Run all tests."""
    print("Starting CLI Parser tests...\n")

    tests = [
        test_basic_argument_parsing,
        test_run_command_options,
        test_argument_validation,
        test_task_creation,
        test_configuration_creation,
        test_output_functions,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
            print()  # Add spacing between tests
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}\n")

    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
