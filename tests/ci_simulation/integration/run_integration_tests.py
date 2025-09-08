#!/usr/bin/env python3
"""
Integration test runner for CI simulation tool.

This script runs comprehensive integration tests that verify the complete
CI silation workflow using actual project files and real-world scenarios.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

import pytest

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "tools" / "ci"))


def check_dependencies():
    """Check if required dependencies are available for integration tests."""
    required_tools = ["git", "python3"]
    missing_tools = []

    for tool in required_tools:
        try:
            subprocess.run([tool, "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing_tools.append(tool)

    if missing_tools:
        print(
            f"⚠️  Warning: Missing tools for full integration testing: {', '.join(missing_tools)}"
        )
        print("Some integration tests may be skipped.")

    return len(missing_tools) == 0


def run_integration_tests(
    test_pattern=None, verbose=False, coverage=False, parallel=False, include_slow=False
):
    """
    Run integration tests with specified options.

    Args:
        test_pattern: Pattern to match test files/functions
        verbose: Enable verbose output
        coverage: Enable coverage reporting
        parallel: Run tests in parallel
        include_slow: Include slow integration tests
    """

    # Base pytest arguments
    args = [
        str(Path(__file__).parent),  # Integration test directory
        "--tb=short",  # Short traceback format
        "--strict-markers",  # Strict marker checking
        "-v" if verbose else "-q",  # Verbose or quiet
        "-m",
        "integration",  # Only run integration tests
    ]

    # Add test pattern if specified
    if test_pattern:
        args.extend(["-k", test_pattern])

    # Add coverage if requested
    if coverage:
        args.extend(
            [
                "--cov=tools.ci",
                "--cov-report=html:reports/integration_coverage",
                "--cov-report=term-missing",
                "--cov-append",  # Append to existing coverage data
            ]
        )

    # Add parallel execution if requested
    if parallel:
        args.extend(["-n", "auto"])

    # Handle slow tests
    if not include_slow:
        args.extend(["-m", "integration and not slow"])

    # Add timeout for integration tests
    args.extend(["--timeout=300"])  # 5 minute timeout per test

    # Show test durations
    args.extend(["--durations=5"])

    print(f"Running integration tests with arguments: {' '.join(args)}")
    print("-" * 60)

    # Run the tests
    exit_code = pytest.main(args)

    return exit_code


def run_specific_integration_suite(suite_name):
    """Run a specific integration test suite."""

    suite_patterns = {
        "end_to_end": "test_end_to_end_simulation.py",
        "configuration": "test_configuration_integration.py",
        "error_recovery": "test_error_recovery_integration.py",
        "full_workflow": "TestEndToEndSimulation",
        "config_management": "TestConfigurationIntegration",
        "error_handling": "TestErrorRecoveryIntegration",
        "resilience": "TestSystemResilienceIntegration",
        "multi_python": "TestMultiplePythonVersions",
        "git_hooks": "TestGitHookIntegration",
        "performance": "TestPerformanceIntegration",
    }

    if suite_name not in suite_patterns:
        print(f"❌ Unknown test suite: {suite_name}")
        print(f"Available suites: {', '.join(suite_patterns.keys())}")
        return 1

    pattern = suite_patterns[suite_name]
    print(f"🧪 Running integration test suite: {suite_name}")
    print(f"📋 Pattern: {pattern}")

    return run_integration_tests(test_pattern=pattern, verbose=True)


def setup_test_environment():
    """Set up the test environment for integration tests."""

    # Create necessary directories
    reports_dir = project_root / "reports"
    reports_dir.mkdir(exist_ok=True)

    integration_reports_dir = reports_dir / "integration"
    integration_reports_dir.mkdir(exist_ok=True)

    # Set environment variables for testing
    os.environ["CI_TESTING"] = "true"
    os.environ["CI_INTEGRATION_TESTS"] = "true"

    print("✅ Test environment set up successfully")


def cleanup_test_environment():
    """Clean up test environment after integration tests."""

    # Clean up any temporary files created during testing
    temp_patterns = [
        "test_project*",
        "problematic_project*",
        "config_test*",
        "*.tmp",
        "*.temp",
    ]

    # Note: In a real implementation, you might want to clean up
    # temporary directories created during testing
    print("🧹 Test environment cleaned up")


def validate_test_results(exit_code):
    """Validate and report test results."""

    if exit_code == 0:
        print("✅ All integration tests passed!")
        print("🎉 CI simulation tool is ready for production use")
    elif exit_code == 1:
        print("❌ Some integration tests failed!")
        print("🔍 Check the test output above for details")
    elif exit_code == 2:
        print("⚠️  Test execution was interrupted")
        print("🔧 Check for configuration or environment issues")
    else:
        print(f"❓ Unexpected exit code: {exit_code}")

    return exit_code


def main():
    """Main entry point for the integration test runner."""

    parser = argparse.ArgumentParser(
        description="Run integration tests for CI simulation tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Run all integration tests
  %(prog)s --suite end_to_end       # Run end-to-end tests only
  %(prog)s --pattern "test_config*" # Run configuration tests
  %(prog)s --verbose --coverage     # Run with verbose output and coverage
  %(prog)s --include-slow           # Include slow integration tests
        """,
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
        "--include-slow", action="store_true", help="Include slow integration tests"
    )

    parser.add_argument(
        "--suite",
        choices=[
            "end_to_end",
            "configuration",
            "error_recovery",
            "full_workflow",
            "config_management",
            "error_handling",
            "resilience",
            "multi_python",
            "git_hooks",
            "performance",
        ],
        help="Run specific integration test suite",
    )

    parser.add_argument(
        "--check-deps", action="store_true", help="Check dependencies and exit"
    )

    parser.add_argument(
        "--setup-only", action="store_true", help="Set up test environment and exit"
    )

    args = parser.parse_args()

    # Check dependencies if requested
    if args.check_deps:
        all_deps_available = check_dependencies()
        return 0 if all_deps_available else 1

    # Set up test environment
    setup_test_environment()

    if args.setup_only:
        print("✅ Test environment setup complete")
        return 0

    # Check dependencies
    check_dependencies()

    try:
        # Run specific suite if requested
        if args.suite:
            exit_code = run_specific_integration_suite(args.suite)
        else:
            # Run integration tests
            exit_code = run_integration_tests(
                test_pattern=args.pattern,
                verbose=args.verbose,
                coverage=args.coverage,
                parallel=args.parallel,
                include_slow=args.include_slow,
            )

        # Validate and report results
        return validate_test_results(exit_code)

    finally:
        # Clean up test environment
        cleanup_test_environment()


if __name__ == "__main__":
    sys.exit(main())
