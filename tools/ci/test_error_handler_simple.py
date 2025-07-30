#!/usr/bin/env python3
"""
Simple test for ErrorHandler to verify basic functionality
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from error_handler import ErrorCategory, ErrorHandler, RecoveryStrategy
from interfaces import DependencyError, EnvironmentError


def test_basic_functionality():
    """Test basic error handler functionality."""
    print("Testing ErrorHandler basic functionality...")

    # Initialize handler
    handler = ErrorHandler()
    print("✓ ErrorHandler initialized successfully")

    # Test error classification
    env_error = EnvironmentError("Python version not found")
    category = handler._classify_error(env_error)
    assert category == ErrorCategory.ENVIRONMENT
    print("✓ Environment error classified correctly")

    dep_error = DependencyError(["missing-package"], "Package not found")
    category = handler._classify_error(dep_error)
    assert category == ErrorCategory.DEPENDENCY
    print("✓ Dependency error classified correctly")

    # Test error handling
    error_context = handler.handle_error(
        error=ValueError("Test error"),
        component="test_component",
        operation="test_operation",
    )

    assert error_context.component == "test_component"
    assert error_context.operation == "test_operation"
    print("✓ Error handling works correctly")

    # Test error report generation
    report = handler.generate_error_report()
    assert "CI Simulation Error Report" in report
    assert "test_component.test_operation" in report
    print("✓ Error report generation works")

    # Test error statistics
    stats = handler.get_error_statistics()
    assert stats["total_errors"] == 1
    print("✓ Error statistics work correctly")

    print("\nAll tests passed! ✅")


if __name__ == "__main__":
    test_basic_functionality()
