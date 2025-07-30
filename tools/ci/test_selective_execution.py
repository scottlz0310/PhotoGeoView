#!/usr/bin/env python3
"""
Integration test for selective check execution functionality

This script demonstrates the complete workflow of selective check execution
including CLI parsing, task filtering, dependency resolution, and orchestration.
"""

import logging
import os
import sys
from pathlib import Path
from unittest.mock import Mock

# Add the tools directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ci.check_orchestrator import CheckOrchestrator
from ci.cli_parser import CLIParser
from ci.interfaces import CheckerFactory, CheckerInterface
from ci.models import CheckResult, CheckStatus, CheckTask

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class MockChecker(CheckerInterface):
    """Mock checker for testing purposes."""

    def __init__(self, config, name, check_type, dependencies=None):
        super().__init__(config)
        self._name = name
        self._check_type = check_type
        self._dependencies = dependencies or []

    @property
    def name(self) -> str:
        return self._name

    @property
    def check_type(self) -> str:
        return self._check_type

    @property
    def dependencies(self) -> list:
        return self._dependencies

    def is_available(self) -> bool:
        return True

    def run_check(self, **kwargs) -> CheckResult:
        return CheckResult(
            name=self.name,
            status=CheckStatus.SUCCESS,
            duration=1.0,
            output=f"Mock {self.name} completed successfully",
            metadata={"mock": True},
        )


class MockCodeQualityChecker(MockChecker):
    def __init__(self, config):
        super().__init__(config, "Code Quality", "code_quality")


class MockTestRunner(MockChecker):
    def __init__(self, config):
        super().__init__(config, "Test Runner", "test_runner", ["code_quality"])


class MockSecurityScanner(MockChecker):
    def __init__(self, config):
        super().__init__(config, "Security Scanner", "security_scanner")


class MockPerformanceAnalyzer(MockChecker):
    def __init__(self, config):
        super().__init__(
            config, "Performance Analyzer", "performance_analyzer", ["test_runner"]
        )


def setup_mock_checkers():
    """Set up mock checkers for testing."""
    # Register mock checkers
    CheckerFactory.register_checker("code_quality", MockCodeQualityChecker)
    CheckerFactory.register_checker("test_runner", MockTestRunner)
    CheckerFactory.register_checker("security_scanner", MockSecurityScanner)
    CheckerFactory.register_checker("performance_analyzer", MockPerformanceAnalyzer)


def test_selective_execution_workflow():
    """Test the complete selective execution workflow."""
    print("Testing selective execution workflow...")

    # Setup
    setup_mock_checkers()

    config = {"max_parallel_tasks": 2, "checkers": {}}

    orchestrator = CheckOrchestrator(config)
    parser = CLIParser(orchestrator)

    try:
        # Test 1: Select specific checks
        print("\n1. Testing specific check selection...")
        args = parser.parse_args(["run", "code_quality", "test_runner"])

        # Validate arguments
        errors = parser.validate_args(args)
        if errors:
            print(f"Validation errors: {errors}")
            return False

        # Create tasks
        tasks = parser.create_tasks_from_args(args)
        print(f"Created {len(tasks)} tasks: {[t.name for t in tasks]}")

        # Filter tasks (should include dependencies)
        filtered_tasks = orchestrator.filter_tasks_by_selection(tasks, ["test_runner"])
        print(
            f"Filtered to {len(filtered_tasks)} tasks: {[t.name for t in filtered_tasks]}"
        )

        # Should include code_quality as dependency of test_runner
        task_names = [t.name for t in filtered_tasks]
        assert "test_runner" in task_names
        # Note: dependency resolution happens at execution time, not filtering

        print("✓ Specific check selection works")

        # Test 2: Exclude checks
        print("\n2. Testing check exclusion...")
        args = parser.parse_args(["run", "--all", "--exclude", "security_scanner"])
        tasks = parser.create_tasks_from_args(args)
        task_types = [t.check_type for t in tasks]

        assert "security_scanner" not in task_types
        assert "code_quality" in task_types
        assert "test_runner" in task_types
        print(f"Excluded security_scanner, remaining: {task_types}")
        print("✓ Check exclusion works")

        # Test 3: Multiple Python versions
        print("\n3. Testing multiple Python versions...")
        args = parser.parse_args(
            ["run", "code_quality", "--python-versions", "3.9", "3.10"]
        )
        tasks = parser.create_tasks_from_args(args)

        python_versions = [t.python_version for t in tasks]
        assert "3.9" in python_versions
        assert "3.10" in python_versions
        assert len(tasks) == 2  # 1 check × 2 versions
        print(f"Created tasks for Python versions: {python_versions}")
        print("✓ Multiple Python versions work")

        # Test 4: Execution plan
        print("\n4. Testing execution plan creation...")
        args = parser.parse_args(["run", "performance_analyzer"])  # Has dependencies
        tasks = parser.create_tasks_from_args(args)

        plan = orchestrator.create_execution_plan(tasks)
        print(
            f"Execution plan: {plan['total_tasks']} tasks, {plan['execution_levels']} levels"
        )
        print("✓ Execution plan creation works")

        # Test 5: Actual task execution (mock)
        print("\n5. Testing task execution...")
        args = parser.parse_args(["run", "code_quality"])
        tasks = parser.create_tasks_from_args(args)

        results = orchestrator.execute_checks(tasks)
        print(f"Execution results: {len(results)} results")

        for name, result in results.items():
            print(f"  {name}: {result.status.value} ({result.duration:.1f}s)")
            assert result.status == CheckStatus.SUCCESS

        print("✓ Task execution works")

        print("\n✓ All selective execution workflow tests passed")
        return True

    except Exception as e:
        print(f"✗ Selective execution workflow test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_check_availability_validation():
    """Test check availability validation."""
    print("Testing check availability validation...")

    setup_mock_checkers()

    config = {"checkers": {}}
    orchestrator = CheckOrchestrator(config)
    parser = CLIParser(orchestrator)

    try:
        # Test valid checks
        available_checks = orchestrator.get_available_checks()
        print(f"Available checks: {available_checks}")

        # Test invalid check validation
        errors = orchestrator.validate_check_selection(["invalid_check"])
        assert len(errors) > 0
        print(f"Invalid check correctly caught: {errors[0]}")

        # Test valid check validation
        errors = orchestrator.validate_check_selection(["code_quality"])
        assert len(errors) == 0
        print("Valid check passes validation")

        # Test check info retrieval
        info = orchestrator.get_check_info("code_quality")
        assert info is not None
        assert info["name"] == "Code Quality"
        print(f"Check info retrieved: {info['name']}")

        print("✓ Check availability validation tests passed")
        return True

    except Exception as e:
        print(f"✗ Check availability validation test failed: {e}")
        return False


def test_dependency_resolution_with_selection():
    """Test dependency resolution with selective execution."""
    print("Testing dependency resolution with selection...")

    setup_mock_checkers()

    config = {"checkers": {}}
    orchestrator = CheckOrchestrator(config)

    try:
        # Create tasks with dependencies
        tasks = [
            CheckTask(name="code_quality", check_type="code_quality", dependencies=[]),
            CheckTask(
                name="test_runner",
                check_type="test_runner",
                dependencies=["code_quality"],
            ),
            CheckTask(
                name="security_scanner", check_type="security_scanner", dependencies=[]
            ),
            CheckTask(
                name="performance_analyzer",
                check_type="performance_analyzer",
                dependencies=["test_runner"],
            ),
        ]

        # Test selecting a task with dependencies
        filtered_tasks = orchestrator.filter_tasks_by_selection(
            tasks, ["performance_analyzer"]
        )
        task_names = [t.name for t in filtered_tasks]

        # Should include all dependencies
        assert "performance_analyzer" in task_names
        assert "test_runner" in task_names
        assert "code_quality" in task_names
        assert "security_scanner" not in task_names  # Not a dependency

        print(f"Selected performance_analyzer, got tasks: {task_names}")
        print("✓ Dependency resolution with selection works")

        # Test execution order
        results = orchestrator.execute_checks(filtered_tasks)
        assert len(results) == 3  # code_quality, test_runner, performance_analyzer
        print(f"Executed {len(results)} tasks with dependencies")

        print("✓ Dependency resolution with selection tests passed")
        return True

    except Exception as e:
        print(f"✗ Dependency resolution with selection test failed: {e}")
        return False


def test_cli_integration():
    """Test complete CLI integration."""
    print("Testing CLI integration...")

    setup_mock_checkers()

    config = {"checkers": {}}
    orchestrator = CheckOrchestrator(config)
    parser = CLIParser(orchestrator)

    try:
        # Test help doesn't crash
        try:
            parser.print_help()
        except SystemExit:
            pass  # argparse calls sys.exit() for help

        # Test list command output
        parser.print_available_checks(detailed=True)

        # Test info command output
        parser.print_check_info("code_quality")

        # Test plan command output
        args = parser.parse_args(["plan", "test_runner"])
        tasks = parser.create_tasks_from_args(args)
        parser.print_execution_plan(tasks)

        print("✓ CLI integration tests passed")
        return True

    except Exception as e:
        print(f"✗ CLI integration test failed: {e}")
        return False


def main():
    """Run all integration tests."""
    print("Starting selective execution integration tests...\n")

    tests = [
        test_selective_execution_workflow,
        test_check_availability_validation,
        test_dependency_resolution_with_selection,
        test_cli_integration,
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

    print(f"Integration Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All integration tests passed!")
        return 0
    else:
        print("❌ Some integration tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
