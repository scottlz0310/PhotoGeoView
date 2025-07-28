#!/usr/bin/env python3
"""
Test script for environment managers.

This script tests the Python version manager, Qt manager, and display manager
to ensure they work correctly.

Author: Kiro (AI Integration and Quality Assurance)
"""

import sys
import os
import logging

# Add the tools/ci directory to the path
ci_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ci_dir)

# Import with absolute path handling
try:
    from environment import PythonVersionManager, QtEnvironmentManager, DisplayManager
    from models import CheckStatus
except ImportError:
    # Fallback to direct imports
    sys.path.insert(0, os.path.join(ci_dir, "environment"))
    sys.path.insert(0, os.path.join(ci_dir, ".."))

    from python_manager import PythonVersionManager
    from qt_manager import QtEnvironmentManager
    from display_manager import DisplayManager
    from models import CheckStatus

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def test_python_version_manager():
    """Test Python version manager functionality."""
    print("\n=== Testing Python Version Manager ===")

    manager = PythonVersionManager()

    # Test version discovery
    print("Discovering Python versions...")
    versions = manager.discover_python_versions()
    print(f"Discovered versions: {list(versions.keys())}")

    for version, info in versions.items():
        print(f"  {info}")

    # Test compatibility check
    print("\nChecking version compatibility...")
    result = manager.check_version_compatibility()
    print(f"Status: {result.status.name}")
    print(f"Output: {result.output}")

    if result.errors:
        print("Errors:")
        for error in result.errors:
            print(f"  - {error}")

    if result.warnings:
        print("Warnings:")
        for warning in result.warnings:
            print(f"  - {warning}")

    if result.suggestions:
        print("Suggestions:")
        for suggestion in result.suggestions:
            print(f"  - {suggestion}")

    return result.status == CheckStatus.SUCCESS


def test_qt_environment_manager():
    """Test Qt environment manager functionality."""
    print("\n=== Testing Qt Environment Manager ===")

    manager = QtEnvironmentManager()

    # Test Qt environment setup
    print("Setting up Qt environment...")
    result = manager.setup_qt_environment()
    print(f"Status: {result.status.name}")
    print(f"Output: {result.output}")

    if result.errors:
        print("Errors:")
        for error in result.errors:
            print(f"  - {error}")

    if result.warnings:
        print("Warnings:")
        for warning in result.warnings:
            print(f"  - {warning}")

    if result.suggestions:
        print("Suggestions:")
        for suggestion in result.suggestions:
            print(f"  - {suggestion}")

    # Test environment variables
    print("\nQt test environment variables:")
    env_vars = manager.get_qt_test_environment()
    for key, value in env_vars.items():
        print(f"  {key}={value}")

    # Cleanup
    cleanup_result = manager.cleanup_qt_environment()
    print(f"Cleanup status: {cleanup_result.status.name}")

    return result.status != CheckStatus.FAILURE


def test_display_manager():
    """Test display manager functionality."""
    print("\n=== Testing Display Manager ===")

    manager = DisplayManager()

    # Check if virtual display is needed
    print(f"Virtual display needed: {manager.is_virtual_display_needed()}")

    # Check Xvfb availability
    print("Checking Xvfb availability...")
    xvfb_result = manager.check_xvfb_availability()
    print(f"Xvfb status: {xvfb_result.status.name}")
    print(f"Output: {xvfb_result.output}")

    if xvfb_result.errors:
        print("Errors:")
        for error in xvfb_result.errors:
            print(f"  - {error}")

    if xvfb_result.suggestions:
        print("Suggestions:")
        for suggestion in xvfb_result.suggestions:
            print(f"  - {suggestion}")

    # Test display environment
    print("\nDisplay environment variables:")
    env_vars = manager.get_display_environment()
    for key, value in env_vars.items():
        print(f"  {key}={value}")

    return xvfb_result.status != CheckStatus.FAILURE


def main():
    """Run all tests."""
    print("Testing CI Environment Managers")
    print("=" * 50)

    results = []

    # Test Python version manager
    try:
        results.append(test_python_version_manager())
    except Exception as e:
        print(f"Python version manager test failed: {e}")
        results.append(False)

    # Test Qt environment manager
    try:
        results.append(test_qt_environment_manager())
    except Exception as e:
        print(f"Qt environment manager test failed: {e}")
        results.append(False)

    # Test display manager
    try:
        results.append(test_display_manager())
    except Exception as e:
        print(f"Display manager test failed: {e}")
        results.append(False)

    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    print(f"Python Version Manager: {'PASS' if results[0] else 'FAIL'}")
    print(f"Qt Environment Manager: {'PASS' if results[1] else 'FAIL'}")
    print(f"Display Manager: {'PASS' if results[2] else 'FAIL'}")

    overall_success = all(results)
    print(f"\nOverall: {'PASS' if overall_success else 'FAIL'}")

    return 0 if overall_success else 1


if __name__ == "__main__":
    sys.exit(main())
