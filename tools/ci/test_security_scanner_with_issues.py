#!/usr/bin/env python3
"""
Test SecurityScanner with a file that contains security issues.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.ci.checkers.security_scanner import SecurityScanner
from tools.ci.models import CheckStatus


def test_security_scanner_with_issues():
    """Test the SecurityScanner with a file containing security issues."""
    print("Testing SecurityScanner with security issues...")

    # Test configuration
    config = {
        'timeout': 60,
        'safety': {
            'ignore_ids': [],
            'full_report': True
        },
        'bandit': {
            'exclude_dirs': ['venv', 'env', '.venv', 'node_modules', '__pycache__', 'build', 'dist'],
            'skip_tests': False,  # Don't skip tests so we can see B101
            'confidence_level': 'LOW'
        }
    }

    # Create scanner instance
    scanner = SecurityScanner(config)

    if not scanner.is_available():
        print("Security scanner dependencies not available")
        return False

    # Test bandit scan specifically
    print("\n--- Testing Bandit Scan with Security Issues ---")
    bandit_result = scanner.run_bandit_scan()
    print(f"Bandit status: {bandit_result.status.value}")
    print(f"Bandit duration: {bandit_result.duration:.2f}s")
    print(f"Bandit output: {bandit_result.output}")

    if bandit_result.errors:
        print(f"\nErrors found ({len(bandit_result.errors)}):")
        for i, error in enumerate(bandit_result.errors, 1):
            print(f"  {i}. {error}")

    if bandit_result.warnings:
        print(f"\nWarnings found ({len(bandit_result.warnings)}):")
        for i, warning in enumerate(bandit_result.warnings, 1):
            print(f"  {i}. {warning}")

    if bandit_result.suggestions:
        print(f"\nSuggestions ({len(bandit_result.suggestions)}):")
        for i, suggestion in enumerate(bandit_result.suggestions, 1):
            print(f"  {i}. {suggestion}")

    # Check metadata
    if bandit_result.metadata and 'issues' in bandit_result.metadata:
        issues = bandit_result.metadata['issues']
        print(f"\nDetailed Issues ({len(issues)}):")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue['file_path']}:{issue.get('line_number', '?')} - {issue['rule_code']}")
            print(f"     Severity: {issue['severity']} - {issue['message']}")

    # Test full security scan
    print("\n--- Testing Full Security Scan ---")
    full_results = scanner.run_full_security_scan()

    # Generate and display report
    print("\n--- Testing Security Report Generation ---")
    report = scanner.generate_security_report(full_results)
    print("Security report:")
    print("=" * 50)
    print(report)
    print("=" * 50)

    # Save detailed report
    report_path = Path("detailed_security_scan_report.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\nDetailed report saved to: {report_path}")

    print("\nSecurityScanner test with issues completed successfully!")
    return True


if __name__ == "__main__":
    try:
        success = test_security_scanner_with_issues()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
