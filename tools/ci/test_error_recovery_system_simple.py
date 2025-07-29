#!/usr/bin/env python3
"""
Simple test for ErrorRecoverySystem to verify integration functionality
"""

import sys
import os
import tempfile

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from error_recovery_system import ErrorRecoverySystem, get_error_recovery_system
from interfaces import EnvironmentError, DependencyError

def test_integrated_functionality():
    """Test integrated error recovery system functionality."""
    print("Testing ErrorRecoverySystem integration...")

    # Initialize system
    config = {
        'error_handler': {'auto_recovery_enabled': True},
        'resource_manager': {'monitoring_enabled': False}
    }
    system = ErrorRecoverySystem(config)
    print("✓ ErrorRecoverySystem initialized successfully")

    # Test error handling with resource context
    error_context = system.handle_error_with_resources(
        error=EnvironmentError("Test environment error"),
        component="test_component",
        operation="test_operation"
    )

    assert error_context.component == "test_component"
    assert 'resource_usage' in error_context.environment_info
    assert 'tracked_resources' in error_context.environment_info
    print("✓ Error handling with resource context works")

    # Test system health check
    health = system.check_system_health()
    assert health.system_status in ["healthy", "warning", "critical"]
    assert health.error_count >= 1  # We just added an error
    assert health.memory_percent >= 0
    assert health.disk_percent >= 0
    print("✓ System health check works")

    # Test health report generation
    report = system.generate_health_report()
    assert "CI Simulation System Health Report" in report
    assert "Error Statistics" in report
    assert "Resource Usage" in report
    print("✓ Health report generation works")

    # Test recovery suggestions
    suggestions = system.get_recovery_suggestions(error_context.category)
    assert len(suggestions) > 0
    print("✓ Recovery suggestions work")

    # Test global system access
    global_system = get_error_recovery_system()
    assert global_system is not None
    print("✓ Global error recovery system works")

    print("\nIntegration tests passed! ✅")

def test_resource_related_error_handling():
    """Test handling of resource-related errors."""
    print("\nTesting resource-related error handling...")

    system = ErrorRecoverySystem({
        'error_handler': {'auto_recovery_enabled': True},
        'resource_manager': {'monitoring_enabled': False}
    })

    # Test memory error
    memory_error = MemoryError("Out of memory")
    error_context = system.handle_error_with_resources(
        error=memory_error,
        component="memory_test",
        operation="allocation"
    )

    # Should be classified as resource error
    from error_handler import ErrorCategory
    assert error_context.category == ErrorCategory.RESOURCE
    print("✓ Memory error classified as resource error")

    # Test timeout error (often resource-related)
    import subprocess
    timeout_error = subprocess.TimeoutExpired("test_cmd", 30)
    error_context = system.handle_error_with_resources(
        error=timeout_error,
        component="timeout_test",
        operation="execution"
    )

    assert error_context.category == ErrorCategory.TIMEOUT
    print("✓ Timeout error handled correctly")

    print("Resource-related error handling tests passed! ✅")

if __name__ == "__main__":
    test_integrated_functionality()
    test_resource_related_error_handling()
