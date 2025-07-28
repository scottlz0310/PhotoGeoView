#!/usr/bin/env python3
"""
Demonstration of Black formatter integration in CI simulation tool.

This script shows how to use the Black formatter functionality
with the CodeQualityChecker.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tools.ci.checkers.code_quality import CodeQualityChecker
from tools.ci.models import CheckStatus


def main():
    """Demonstrate Black formatter integration."""
    print("🔧 Black Formatter Integration Demo")
    print("=" * 50)

    # Create configuration
    config = {
        "tools": {
            "black": {
                "line_length": 88,
                "target_version": ["py39", "py310", "py311"]
            }
        }
    }

    # Initialize the checker
    checker = CodeQualityChecker(config)

    # Show Black status
    print("\n📋 Black Configuration:")
    black_status = checker.get_black_status()
    print(f"  Available: {black_status['available']}")
    print(f"  Line length: {checker.black_config['line_length']}")
    print(f"  Target versions: {checker.black_config['target_version']}")
    print(f"  Config source: {black_status['config_source']}")

    # Run Black check (without auto-fix)
    print("\n🔍 Running Black check (no auto-fix)...")
    check_result = checker.run_black(auto_fix=False)

    print(f"  Status: {check_result.status.value}")
    print(f"  Duration: {check_result.duration:.2f}s")
    print(f"  Issues found: {check_result.metadata.get('issues_found', 0)}")

    if check_result.errors:
        print(f"  Errors: {len(check_result.errors)}")
        for error in check_result.errors[:2]:  # Show first 2 errors
            print(f"    - {error}")

    if check_result.warnings:
        print(f"  Warnings: {len(check_result.warnings)}")
        for warning in check_result.warnings[:2]:  # Show first 2 warnings
            print(f"    - {warning}")

    if check_result.suggestions:
        print(f"  Suggestions: {len(check_result.suggestions)}")
        for suggestion in check_result.suggestions[:2]:  # Show first 2 suggestions
            print(f"    - {suggestion}")

    # Run full code quality check with Black
    print("\n🎯 Running full code quality check (Black only)...")
    full_result = checker.run_check(check_types=["black"], auto_fix=False)

    print(f"  Overall status: {full_result.status.value}")
    print(f"  Duration: {full_result.duration:.2f}s")
    print(f"  Checks run: {full_result.metadata.get('checks_run', [])}")

    # Show configuration used
    config_used = full_result.metadata.get('configuration', {})
    if 'black' in config_used:
        print(f"  Black config: {config_used['black']}")

    print("\n✅ Black formatter integration demo completed!")
    print("\nTo use Black formatter in your CI simulation:")
    print("1. Configure Black settings in your config file")
    print("2. Run: checker.run_black(auto_fix=True) to fix issues")
    print("3. Run: checker.run_black(auto_fix=False) to check only")
    print("4. Use: checker.run_check(check_types=['black']) for integration")


if __name__ == "__main__":
    main()
