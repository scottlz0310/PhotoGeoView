"""
Qt Theme Breadcrumb Integration Test Runner

Comprehensive test runner for all qt-theme-breadcrumb integration tests.
Executes tests with proper reporting and coverage analysis.

Author: Kiro AI Integration System
Requirements: 1.2, 1.3, 2.1, 4.1, 4.3
"""

import argparse
import sys
import time
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_integration_tests(
    test_pattern=None, verbose=False, coverage=False, platform_only=False
):
    """
    Run qt-theme-breadcrumb integration tests

    Args:
        test_pattern: Pattern to match specific tests
        verbose: Enable verbose output
        coverage: Enable coverage reporting
        platform_only: Run only platform-specific tests
    """
    print("🚀 Starting Qt Theme Breadcrumb Integration Tests")
    print("=" * 60)

    # Test files to run
    test_files = [
        "tests/test_qt_theme_breadcrumb_integration.py",
        "tests/test_theme_persistence_integration.py",
        "tests/test_file_system_watcher_integration.py",
        "tests/test_cross_platform_compatibility.py",
    ]

    if platform_only:
        test_files = ["tests/test_cross_platform_compatibility.py"]

    if test_pattern:
        test_files = [f for f in test_files if test_pattern in f]

    # Build pytest arguments
    pytest_args = []

    # Add test files
    pytest_args.extend(test_files)

    # Add common options
    pytest_args.extend(
        [
            "-v" if verbose else "-q",
            "--tb=short",
            "--strict-markers",
            "--disable-warnings",
        ]
    )

    # Add coverage options
    if coverage:
        pytest_args.extend(
            [
                "--cov=src/integration",
                "--cov=src/ui",
                "--cov-report=html:tests/reports/coverage_html",
                "--cov-report=xml:tests/reports/coverage.xml",
                "--cov-report=term-missing",
            ]
        )

    # Add output options
    pytest_args.extend(
        [
            "--junit-xml=tests/reports/junit_results.xml",
            "--html=tests/reports/test.html",
            "--self-contained-html",
        ]
    )

    # Create reports directory
    reports_dir = Path("tests/reports")
    reports_dir.mkdir(exist_ok=True)

    print(f"📋 Running tests: {', '.join(Path(f).name for f in test_files)}")
    print(f"🔧 Pytest args: {' '.join(pytest_args)}")
    print("-" * 60)

    # Record start time
    start_time = time.time()

    # Run tests
    try:
        exit_code = pytest.main(pytest_args)
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1

    # Record end time
    end_time = time.time()
    duration = end_time - start_time

    print("-" * 60)
    print(f"⏱️  Test execution completed in {duration:.2f} seconds")

    # Report results
    if exit_code == 0:
        print("✅ All integration tests passed!")
    else:
        print(f"❌ Tests failed with exit code: {exit_code}")

    # Show report locations
    print("\n📊 Test Reports:")
    if coverage:
        print(f"   Coverage HTML: {reports_dir}/coverage_html/index.html")
        print(f"   Coverage XML:  {reports_dir}/coverage.xml")
    print(f"   Test Report:   {reports_dir}/test_report.html")
    print(f"   JUnit XML:     {reports_dir}/junit_results.xml")

    return exit_code


def run_specific_test_categories():
    """Run specific categories of integration tests"""

    categories = {
        "theme": {
            "description": "Theme integration tests",
            "files": [
                "tests/test_qt_theme_breadcrumb_integration.py::TestQtThemeBreadcrumbIntegration::test_theme_changes_across_components",
                "tests/test_theme_persistence_integration.py",
            ],
        },
        "breadcrumb": {
            "description": "Breadcrumb synchronization tests",
            "files": [
                "tests/test_qt_theme_breadcrumb_integration.py::TestQtThemeBreadcrumbIntegration::test_breadcrumb_folder_navigator_sync",
                "tests/test_qt_theme_breadcrumb_integration.py::TestQtThemeBreadcrumbIntegration::test_breadcrumb_segment_navigation",
            ],
        },
        "filesystem": {
            "description": "File system watcher integration tests",
            "files": ["tests/test_file_system_watcher_integration.py"],
        },
        "persistence": {
            "description": "Theme persistence tests",
            "files": ["tests/test_theme_persistence_integration.py"],
        },
        "platform": {
            "description": "Cross-platform compatibility tests",
            "files": ["tests/test_cross_platform_compatibility.py"],
        },
        "workflow": {
            "description": "Complete workflow integration tests",
            "files": [
                "tests/test_qt_theme_breadcrumb_integration.py::TestQtThemeBreadcrumbIntegration::test_complete_theme_breadcrumb_workflow",
                "tests/test_qt_theme_breadcrumb_integration.py::TestQtThemeBreadcrumbIntegration::test_error_recovery_integration",
            ],
        },
    }

    print("🎯 Available Test Categories:")
    print("=" * 40)

    for category, info in categories.items():
        print(f"  {category:12} - {info['description']}")

    print("\nTo run a specific category:")
    print(
        "  python tests/run_qt_theme_breadcrumb_integration_tests.py --category <name>"
    )

    return categories


def run_performance_tests():
    """Run performance-focused integration tests"""

    performance_tests = [
        "tests/test_qt_theme_breadcrumb_integration.py::TestQtThemeBreadcrumbIntegration::test_performance_under_load",
        "tests/test_file_system_watcher_integration.py::TestFileSystemWatcherIntegration::test_watcher_performance_under_load",
    ]

    print("🏃 Running Performance Integration Tests")
    print("=" * 50)

    pytest_args = performance_tests + [
        "-v",
        "--tb=short",
        "--benchmark-only",
        "--benchmark-sort=mean",
        "--benchmark-html=tests/reports/benchmark_report.html",
    ]

    return pytest.main(pytest_args)


def validate_test_environment():
    """Validate that the test environment is properly set up"""

    print("🔍 Validating Test Environment")
    print("-" * 30)

    # Check Python version
    python_version = sys.version_info
    print(
        f"Python Version: {python_version.major}.{python_version.minor}.{python_version.micro}"
    )

    if python_version < (3, 8):
        print("❌ Python 3.8+ required")
        return False

    # Check required packages
    required_packages = [
        "pytest",
        "pytest-cov",
        "pytest-html",
        "pytest-asyncio",
        "PySide6",
    ]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (missing)")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False

    # Check project structure
    required_paths = ["src/integration", "src/ui", "tests"]

    for path in required_paths:
        if Path(path).exists():
            print(f"✅ {path}")
        else:
            print(f"❌ {path} (missing)")
            return False

    print("\n✅ Test environment validation passed")
    return True


def main():
    """Main entry point for test runner"""

    parser = argparse.ArgumentParser(
        description="Qt Theme Breadcrumb Integration Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all integration tests
  python tests/run_qt_theme_breadcrumb_integration_tests.py

  # Run with coverage
  python tests/run_qt_theme_breadcrumb_integration_tests.py --coverage

  # Run specific test pattern
  python tests/run_qt_theme_breadcrumb_integration_tests.py --pattern theme

  # Run platform-specific tests only
  python tests/run_qt_theme_breadcrumb_integration_tests.py --platform-only

  # Run specific category
  python tests/run_qt_theme_breadcrumb_integration_tests.py --category theme

  # Validate environment
  python tests/run_qt_theme_breadcrumb_integration_tests.py --validate
        """,
    )

    parser.add_argument("--pattern", help="Pattern to match specific test files")

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    parser.add_argument(
        "--coverage", "-c", action="store_true", help="Enable coverage reporting"
    )

    parser.add_argument(
        "--platform-only",
        "-p",
        action="store_true",
        help="Run only platform-specific tests",
    )

    parser.add_argument(
        "--category",
        choices=[
            "theme",
            "breadcrumb",
            "filesystem",
            "persistence",
            "platform",
            "workflow",
        ],
        help="Run specific test category",
    )

    parser.add_argument(
        "--performance", action="store_true", help="Run performance tests only"
    )

    parser.add_argument(
        "--validate", action="store_true", help="Validate test environment setup"
    )

    parser.add_argument(
        "--list-categories", action="store_true", help="List available test categories"
    )

    args = parser.parse_args()

    # Handle special commands
    if args.validate:
        return 0 if validate_test_environment() else 1

    if args.list_categories:
        run_specific_test_categories()
        return 0

    if args.performance:
        return run_performance_tests()

    # Validate environment before running tests
    if not validate_test_environment():
        return 1

    # Handle category-specific tests
    if args.category:
        categories = run_specific_test_categories()
        if args.category in categories:
            category_files = categories[args.category]["files"]
            pytest_args = category_files + ["-v", "--tb=short"]
            if args.coverage:
                pytest_args.extend(
                    [
                        "--cov=src/integration",
                        "--cov=src/ui",
                        "--cov-report=term-missing",
                    ]
                )
            return pytest.main(pytest_args)
        else:
            print(f"❌ Unknown category: {args.category}")
            return 1

    # Run main integration tests
    return run_integration_tests(
        test_pattern=args.pattern,
        verbose=args.verbose,
        coverage=args.coverage,
        platform_only=args.platform_only,
    )


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
