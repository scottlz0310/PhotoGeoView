#!/usr/bin/env python3
"""
Demonstration of the integrated Error Recovery System

This script demonstrates how the ErrorHandler, ResourceManager, and
ErrorRecoverySystem work together to provide comprehensive error
handling and resource management for the CI simulation tool.

Author: Kiro (AI Integration and Quality Assurance)
"""

import os
import sys
import tempfile
import time
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from error_handler import ErrorCategory
from error_recovery_system import ErrorRecoverySystem
from interfaces import ConfigurationError, DependencyError, EnvironmentError


def demonstrate_error_recovery():
    """Demonstrate the complete error recovery system."""

    print("🚀 CI Simulation Error Recovery System Demo")
    print("=" * 50)

    # Initialize the system
    config = {
        "error_handler": {"auto_recovery_enabled": True, "max_retry_attempts": 2},
        "resource_manager": {
            "monitoring_enabled": False,  # Disable for demo
            "max_memory_percent": 80.0,
            "max_disk_percent": 90.0,
        },
    }

    system = ErrorRecoverySystem(config)
    print("✅ Error Recovery System initialized")
    print()

    # Demonstrate different types of errors
    print("📋 Demonstrating Error Handling")
    print("-" * 30)

    # 1. Environment Error
    print("1. Environment Error:")
    try:
        raise EnvironmentError("Python 3.12 not found")
    except Exception as e:
        error_context = system.handle_error_with_resources(
            error=e, component="python_manager", operation="version_check"
        )
        print(f"   ✓ Handled: {error_context.category.value} error")
        print(f"   ✓ Severity: {error_context.severity.value}")
        print(f"   ✓ Recovery attempts: {len(error_context.recovery_attempts)}")

    print()

    # 2. Dependency Error
    print("2. Dependency Error:")
    try:
        raise DependencyError(
            ["missing-package", "another-missing"], "Required packages not found"
        )
    except Exception as e:
        error_context = system.handle_error_with_resources(
            error=e, component="dependency_checker", operation="validate_requirements"
        )
        print(f"   ✓ Handled: {error_context.category.value} error")
        print(f"   ✓ Missing deps: {e.missing_dependencies}")

    print()

    # 3. Resource Error (Memory)
    print("3. Resource Error:")
    try:
        raise MemoryError("Cannot allocate memory")
    except Exception as e:
        error_context = system.handle_error_with_resources(
            error=e, component="test_runner", operation="run_large_test_suite"
        )
        print(f"   ✓ Handled: {error_context.category.value} error")
        print(
            f"   ✓ Resource context included: {'resource_usage' in error_context.environment_info}"
        )

    print()

    # Demonstrate resource management
    print("💾 Demonstrating Resource Management")
    print("-" * 35)

    # Create some temporary resources
    temp_files = []
    with system.resource_manager.temp_directory(prefix="demo_") as temp_dir:
        print(f"1. Created temporary directory: {Path(temp_dir).name}")

        # Create some files in the temp directory
        for i in range(3):
            temp_file = Path(temp_dir) / f"test_file_{i}.txt"
            temp_file.write_text(f"Test content {i}")
            temp_files.append(str(temp_file))

        print(f"   ✓ Created {len(temp_files)} temporary files")

        # Show resource statistics
        stats = system.resource_manager.get_resource_statistics()
        print(f"   ✓ Tracked resources: {stats['tracked_resources']['temp_resources']}")

    print("   ✓ Temporary directory automatically cleaned up")
    print()

    # Demonstrate system health monitoring
    print("🏥 System Health Monitoring")
    print("-" * 25)

    health = system.check_system_health()
    print(f"System Status: {health.system_status.upper()}")
    print(f"Total Errors: {health.error_count}")
    print(f"Resolved Errors: {health.resolved_error_count}")
    print(f"Memory Usage: {health.memory_percent:.1f}%")
    print(f"Disk Usage: {health.disk_percent:.1f}%")
    print(f"Active Temp Resources: {health.active_temp_resources}")

    if health.recommendations:
        print("Recommendations:")
        for rec in health.recommendations:
            print(f"  - {rec}")

    print()

    # Demonstrate recovery suggestions
    print("💡 Recovery Suggestions")
    print("-" * 20)

    for category in [
        ErrorCategory.ENVIRONMENT,
        ErrorCategory.DEPENDENCY,
        ErrorCategory.RESOURCE,
    ]:
        suggestions = system.get_recovery_suggestions(category)
        print(f"{category.value.title()} Errors:")
        for suggestion in suggestions[:2]:  # Show first 2 suggestions
            print(f"  - {suggestion}")
        print()

    # Generate and display reports
    print("📊 Generating Reports")
    print("-" * 18)

    # Create reports directory
    reports_dir = Path("reports/demo")
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Generate health report
    health_report_path = reports_dir / "health_report.md"
    system.save_health_report(str(health_report_path))
    print(f"✅ Health report saved: {health_report_path}")

    # Generate error report
    error_report_path = reports_dir / "error_report.md"
    system.error_handler.save_error_report(str(error_report_path))
    print(f"✅ Error report saved: {error_report_path}")

    # Generate resource report
    resource_report_path = reports_dir / "resource_report.md"
    system.resource_manager.save_resource_report(str(resource_report_path))
    print(f"✅ Resource report saved: {resource_report_path}")

    print()

    # Show a sample of the health report
    print("📄 Sample Health Report")
    print("-" * 20)

    health_report = system.generate_health_report()
    # Show first 15 lines of the report
    report_lines = health_report.split("\n")[:15]
    for line in report_lines:
        print(line)

    if len(health_report.split("\n")) > 15:
        print("... (truncated)")

    print()

    # Demonstrate graceful cleanup
    print("🧹 Graceful Cleanup")
    print("-" * 16)

    print("Performing system cleanup...")
    system.cleanup_and_shutdown()
    print("✅ System cleanup completed")

    print()
    print("🎉 Demo completed successfully!")
    print("=" * 50)

    return system


def demonstrate_error_patterns():
    """Demonstrate common error patterns and their handling."""

    print("\n🔍 Common Error Patterns Demo")
    print("=" * 30)

    system = ErrorRecoverySystem(
        {
            "error_handler": {"auto_recovery_enabled": True},
            "resource_manager": {"monitoring_enabled": False},
        }
    )

    # Pattern 1: Cascading errors
    print("1. Cascading Errors Pattern:")
    errors = [
        (ConfigurationError("Invalid config file"), "config_manager", "load_config"),
        (
            EnvironmentError("Python version mismatch"),
            "python_manager",
            "setup_environment",
        ),
        (
            DependencyError(["pytest"], "Missing test framework"),
            "test_runner",
            "initialize",
        ),
    ]

    for error, component, operation in errors:
        try:
            raise error
        except Exception as e:
            system.handle_error_with_resources(e, component, operation)

    print(f"   ✓ Handled {len(errors)} cascading errors")

    # Pattern 2: Resource exhaustion
    print("\n2. Resource Exhaustion Pattern:")
    resource_errors = [
        MemoryError("Out of memory during test execution"),
        OSError("No space left on device"),
    ]

    for error in resource_errors:
        try:
            raise error
        except Exception as e:
            system.handle_error_with_resources(e, "resource_intensive_task", "execute")

    print(f"   ✓ Handled {len(resource_errors)} resource errors")

    # Show final statistics
    stats = system.error_handler.get_error_statistics()
    print(f"\n📈 Final Statistics:")
    print(f"   Total Errors: {stats['total_errors']}")
    print(f"   Resolution Rate: {stats['recovery_success_rate']:.1%}")
    print(f"   Categories: {list(stats['by_category'].keys())}")

    return system


if __name__ == "__main__":
    # Run the main demonstration
    main_system = demonstrate_error_recovery()

    # Run error patterns demonstration
    pattern_system = demonstrate_error_patterns()

    print(f"\n✨ All demonstrations completed successfully!")
    print(f"Check the 'reports/demo/' directory for generated reports.")
