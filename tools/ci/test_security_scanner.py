#!/usr/bin/env python3
"""
Test script for SecurityScanner implementation

This script tests the SecurityScanner functionality including
safety vulnerability scanning and bandit security linting.
"""

import sys
import os
import json
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.ci.checkers.security_scanner import SecurityScanner
from tools.ci.models import CheckStatus


def test_security_scanner():
    """Test the SecurityScanner implementation."""
    print("Testing SecurityScanner implementation...")

    # Test configuration
    config = {
        'timeout': 60,
        'safety': {
            'ignore_ids': [],
            'full_report': True
        },
        'bandit': {
            'exclude_dirs': ['venv', 'env', '.venv', 'node_modules', '__pycache__', 'build', 'dist'],
            'skip_tests': True,
            'confidence_level': 'LOW'
        }
    }

    # Create scanner instance
    scanner = SecurityScanner(config)

    # Test basic properties
    print(f"Scanner name: {scanner.name}")
    print(f"Scanner type: {scanner.check_type}")
    print(f"Dependencies: {scanner.dependencies}")

    # Test availability
    is_available = scanner.is_available()
    print(f"Scanner available: {is_available}")

    if not is_available:
        print("Security scanner dependencies not available. Install with:")
        print("pip install safety bandit")
        return False

    # Test individual scans
    print("\n--- Testing Safety Check ---")
    safety_result = scanner.run_safety_check()
    print(f"Safety status: {safety_result.status.value}")
    print(f"Safety duration: {safety_result.duration:.2f}s")
    print(f"Safety output: {safety_result.output}")
    if safety_result.errors:
        print(f"Safety errors: {len(safety_result.errors)}")
    if safety_result.warnings:
        print(f"Safety warnings: {len(safety_result.warnings)}")

    print("\n--- Testing Bandit Scan ---")
    bandit_result = scanner.run_bandit_scan()
    print(f"Bandit status: {bandit_result.status.value}")
    print(f"Bandit duration: {bandit_result.duration:.2f}s")
    print(f"Bandit output: {bandit_result.output}")
    if bandit_result.errors:
        print(f"Bandit errors: {len(bandit_result.errors)}")
    if bandit_result.warnings:
        print(f"Bandit warnings: {len(bandit_result.warnings)}")

    # Test combined scan
    print("\n--- Testing Combined Security Scan ---")
    combined_result = scanner.run_check()
    print(f"Combined status: {combined_result.status.value}")
    print(f"Combined duration: {combined_result.duration:.2f}s")
    print(f"Combined output: {combined_result.output}")

    # Test full scan with individual results
    print("\n--- Testing Full Security Scan ---")
    full_results = scanner.run_full_security_scan()
    for scan_name, result in full_results.items():
        print(f"{scan_name}: {result.status.value} ({result.duration:.2f}s)")

    # Test report generation
    print("\n--- Testing Security Report Generation ---")
    report = scanner.generate_security_report(full_results)
    print("Security report generated successfully")
    print(f"Report length: {len(report)} characters")

    # Save report to file for inspection
    report_path = Path("security_scan_report.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"Report saved to: {report_path}")

    # Test configuration
    print("\n--- Testing Configuration ---")
    default_config = scanner.get_default_config()
    print(f"Default config keys: {list(default_config.keys())}")

    validation_errors = scanner.validate_config()
    print(f"Config validation errors: {len(validation_errors)}")

    print("\nSecurityScanner test completed successfully!")
    return True


if __name__ == "__main__":
    try:
        success = test_security_scanner()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
