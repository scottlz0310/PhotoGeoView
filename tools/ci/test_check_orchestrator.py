#!/usr/bin/env python3
"""
Test script for CheckOrchestrator functionality

This script tests the basic functionality of the CheckOrchestrator
including dependency resolution, task filtering, and resource management.
"""

import logging
import os
import sys
from pathlib import Path

# Add the tools directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ci.check_orchestrator import CheckOrchestrator, DependencyResolver
from ci.interfaces import CheckerFactory
from ci.models import CheckStatus, CheckTask

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def test_dependency_resolver():
    """Test the dependency resolution functionality."""
    print("Testing DependencyResolver...")

    resolver = DependencyResolver()

    # Create test tasks with dependencies
    tasks = [
        CheckTask(name="task_a", check_type="code_quality", dependencies=[]),
        CheckTask(name="task_b", check_type="test_runner", dependencies=["task_a"]),
        CheckTask(
            name="task_c", check_type="security_scanner", dependencies=["task_a"]
        ),
        CheckTask(
            name="task_d",
            check_type="performance_analyzer",
            dependencies=["task_b", "task_c"],
        ),
    ]

    try:
        # Test dependency resolution
        resolved_order = resolver.resolve_dependencies(tasks)
        print(f"Resolved order: {resolved_order}")

        # Test dependency levels
        levels = resolver.get_dependency_levels(tasks)
        print(f"Dependency levels: {levels}")

        # Verify correct ordering
        assert resolved_order.index("task_a") < resolved_order.index("task_b")
        assert resolved_order.index("task_a") < resolved_order.index("task_c")
        assert resolved_order.index("task_b") < resolved_order.index("task_d")
        assert resolved_order.index("task_c") < resolved_order.index("task_d")

        print("✓ DependencyResolver tests passed")

    except Exception as e:
        print(f"✗ DependencyResolver tests failed: {e}")
        return False

    return True


def test_circular_dependency_detection():
    """Test circular dependency detection."""
    print("Testing circular dependency detection...")

    resolver = DependencyResolver()

    # Create tasks with circular dependency
    tasks = [
        CheckTask(name="task_a", check_type="code_quality", dependencies=["task_b"]),
        CheckTask(name="task_b", check_type="test_runner", dependencies=["task_a"]),
    ]

    try:
        resolver.resolve_dependencies(tasks)
        print("✗ Circular dependency detection failed - should have raised ValueError")
        return False
    except ValueError as e:
        print(f"✓ Circular dependency correctly detected: {e}")
        return True
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def test_orchestrator_initialization():
    """Test CheckOrchestrator initialization."""
    print("Testing CheckOrchestrator initialization...")

    config = {
        "max_parallel_tasks": 2,
        "memory_threshold_percent": 80,
        "cpu_threshold_percent": 90,
        "checkers": {},
    }

    try:
        orchestrator = CheckOrchestrator(config)

        # Test basic properties
        available_checks = orchestrator.get_available_checks()
        print(f"Available checks: {available_checks}")

        # Test resource usage
        resource_usage = orchestrator.get_resource_usage()
        print(f"Resource usage: {resource_usage}")

        print("✓ CheckOrchestrator initialization tests passed")
        return True

    except Exception as e:
        print(f"✗ CheckOrchestrator initialization failed: {e}")
        return False


def test_task_filtering():
    """Test task filtering functionality."""
    print("Testing task filtering...")

    config = {"max_parallel_tasks": 2, "checkers": {}}

    try:
        orchestrator = CheckOrchestrator(config)

        # Create test tasks
        tasks = [
            CheckTask(name="quality_check", check_type="code_quality", dependencies=[]),
            CheckTask(
                name="test_check",
                check_type="test_runner",
                dependencies=["quality_check"],
            ),
            CheckTask(
                name="security_check", check_type="security_scanner", dependencies=[]
            ),
        ]

        # Test validation
        errors = orchestrator.validate_tasks(tasks)
        if errors:
            print(f"Task validation errors: {errors}")

        # Test check selection validation
        selection_errors = orchestrator.validate_check_selection(["invalid_check"])
        if selection_errors:
            print(f"Selection validation correctly caught errors: {selection_errors}")

        # Test available checks listing
        checks_info = orchestrator.list_available_checks()
        print(f"Available checks info: {list(checks_info.keys())}")

        print("✓ Task filtering tests passed")
        return True

    except Exception as e:
        print(f"✗ Task filtering tests failed: {e}")
        return False


def test_execution_plan():
    """Test execution plan creation."""
    print("Testing execution plan creation...")

    config = {"max_parallel_tasks": 2, "checkers": {}}

    try:
        orchestrator = CheckOrchestrator(config)

        # Create test tasks
        tasks = [
            CheckTask(name="quality_check", check_type="code_quality", dependencies=[]),
            CheckTask(
                name="test_check",
                check_type="test_runner",
                dependencies=["quality_check"],
            ),
        ]

        # Create execution plan
        plan = orchestrator.create_execution_plan(tasks)
        print(f"Execution plan: {plan}")

        # Verify plan structure
        assert "total_tasks" in plan
        assert "execution_levels" in plan
        assert "execution_order" in plan

        print("✓ Execution plan tests passed")
        return True

    except Exception as e:
        print(f"✗ Execution plan tests failed: {e}")
        return False


def main():
    """Run all tests."""
    print("Starting CheckOrchestrator tests...\n")

    tests = [
        test_dependency_resolver,
        test_circular_dependency_detection,
        test_orchestrator_initialization,
        test_task_filtering,
        test_execution_plan,
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
