#!/usr/bin/env python3
"""
Test runner for CI simulation unit tests.

This script runs all unit tests for the CI simulation tool components
and provides detailed reporting of test results.
"""

import argparse
import os
import sys
from pathlib import Path

import pytest

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "tools" / "ci"))


def run_tests(test_pattern=None, verbose=False, coverage=False, parallel=False):
    """
    Run the unit tests with specified options.

    Args:
        test_pattern: Pattern to match test files/functions
        verbose: Enable verbose output
        coverage: Enable coverage reporting
        parallel: Run tests in parallel
    """

    # Base pytest arguments
    args = [
        str(Path(__file__).parent),  # Test directory
        "--tb=short",  # Short traceback format
        "--strict-markers",  # Strict marker checking
        "-v" if verbose else "-q",  # Verbose or quiet
    ]

    # Add test pattern if specified
    if test_pattern:
        args.extend(["-k", test_pattern])

    # Add coverage if requested
    if coverage:
        args.extend(
            [
                "--cov=tools.ci",
                "--cov-report=html:reports/coverage",
                "--cov-report=term-missing",
                "--cov-fail-under=80",
            ]
        )

    # Add parallel execution if requested
    if parallel:
        args.extend(["-n", "auto"])

    # Add markers for different test types
    args.extend(
        [
            "-m",
            "not integration",  # Skip integration tests by default
            "--durations=10",  # Show 10 slowest tests
        ]
    )

    print(f"Running tests with arguments: {' '.join(args)}")
    print("-" * 60)

    # Run the tests
    exit_code = pytest.main(args)

    return exit_code


def main():
    """Main entry point for the test runner."""

    parser = argparse.ArgumentParser(
        description="Run unit tests for CI simulation tool"
    )

    parser.add_argument("-k", "--pattern", help="Pattern to match test files/functions")

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )

    parser.add_argument(
        "-c", "--coverage", action="store_true", help="Enable coverage reporting"
    )

    parser.add_argument(
        "-p", "--parallel", action="store_true", help="Run tests in parallel"
    )

    parser.add_argument(
        "--integration", action="store_true", help="Include integration tests"
    )

    parser.add_argument(
        "--component",
        choices=[
            "models",
            "interfaces",
            "config",
            "checkers",
            "environment",
            "reporters",
            "orchestrator",
            "error_handling",
        ],
        help="Run tests for specific component only",
    )

    args = parser.parse_args()

    # Adjust pattern based on component selection
    if args.component:
        component_patterns = {
            "models": "test_models",
            "interfaces": "test_interfaces",
            "config": "test_config_manager",
            "checkers": "test_checkers",
            "environment": "test_environment_managers",
            "reporters": "test_reporters",
            "orchestrator": "test_orchestrator",
            "error_handling": "test_orchestrator_and_error_handling",
        }
        args.pattern = component_patterns.get(args.component, args.pattern)

    # Create reports directory if coverage is enabled
    if args.coverage:
        reports_dir = project_root / "reports"
        reports_dir.mkdir(exist_ok=True)

    # Run the tests
    exit_code = run_tests(
        test_pattern=args.pattern,
        verbose=args.verbose,
        coverage=args.coverage,
        parallel=args.parallel,
    )

    # Print summary
    print("-" * 60)
    if exit_code == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")

    if args.coverage:
        print(f"📊 Coverage report generated in: reports/coverage/index.html")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
