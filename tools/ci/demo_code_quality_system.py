#!/usr/bin/env python3
"""
Demonstration script for the Code Quality Check System

This script demonstrates the comprehensive code quality checking system
with Black, isort, flake8, and mypy integration.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tools.ci.checkers.code_quality import CodeQualityChecker
from tools.ci.models import CheckStatus


def main():
    """Demonstrate the code quality checking system."""
    print("=" * 60)
    print("Code Quality Check System Demonstration")
    print("=" * 60)

    # Configuration for all tools
    config = {
        "tools": {
            "black": {"line_length": 88, "target_version": ["py39", "py310", "py311"]},
            "isort": {
                "profile": "black",
                "line_length": 88,
                "known_first_party": ["src", "tools"],
                "known_third_party": ["PyQt6", "PIL", "folium", "pytest"],
            },
            "flake8": {
                "max_line_length": 88,
                "ignore": ["E203", "W503", "E501"],  # Added E501 for demo
                "exclude": [".git", "__pycache__", "build", "dist", ".venv", ".eggs"],
            },
            "mypy": {
                "python_version": "3.9",
                "warn_return_any": True,
                "disallow_untyped_defs": True,
                "check_untyped_defs": True,
            },
        }
    }

    # Initialize the checker
    print("\n1. Initializing Code Quality Checker...")
    checker = CodeQualityChecker(config)

    # Check availability
    print(f"   Checker available: {checker.is_available()}")
    print(f"   Dependencies: {checker.dependencies}")

    # Test individual tools
    print("\n2. Testing Individual Tools:")

    tools = ["black", "isort", "flake8", "mypy"]
    individual_results = {}

    for tool in tools:
        print(f"\n   Testing {tool}...")
        available = checker._is_tool_available(tool)
        print(f"   - Available: {available}")

        if available:
            if tool == "black":
                result = checker.run_black(auto_fix=False)
            elif tool == "isort":
                result = checker.run_isort(auto_fix=False)
            elif tool == "flake8":
                result = checker.run_flake8()
            elif tool == "mypy":
                result = checker.run_mypy()

            individual_results[tool] = result
            print(f"   - Status: {result.status.value}")
            print(f"   - Duration: {result.duration:.2f}s")
            print(f"   - Errors: {len(result.errors)}")
            print(f"   - Warnings: {len(result.warnings)}")

            # Show sample issues if any
            if hasattr(result, "metadata") and "issues" in result.metadata:
                issues = result.metadata["issues"]
                if issues:
                    print(f"   - Issues found: {len(issues)}")
                    print(f"   - Sample issue: {issues[0]['message'][:50]}...")

    # Test comprehensive check
    print("\n3. Running Comprehensive Code Quality Check...")
    comprehensive_result = checker.run_check(
        check_types=["black", "isort", "flake8", "mypy"], auto_fix=False
    )

    print(f"   Overall Status: {comprehensive_result.status.value}")
    print(f"   Total Duration: {comprehensive_result.duration:.2f}s")
    print(f"   Total Errors: {len(comprehensive_result.errors)}")
    print(f"   Total Warnings: {len(comprehensive_result.warnings)}")
    print(f"   Total Suggestions: {len(comprehensive_result.suggestions)}")

    # Show configuration details
    print("\n4. Configuration Details:")
    metadata = comprehensive_result.metadata
    if "configuration" in metadata:
        for tool, tool_config in metadata["configuration"].items():
            print(f"   {tool}: {len(tool_config)} settings")

    # Show summary
    print("\n5. Summary:")
    success_count = sum(
        1
        for result in individual_results.values()
        if result.status == CheckStatus.SUCCESS
    )
    total_count = len(individual_results)

    print(f"   Tools tested: {total_count}")
    print(f"   Successful: {success_count}")
    print(f"   Failed: {total_count - success_count}")

    if comprehensive_result.status == CheckStatus.SUCCESS:
        print("   ✅ All code quality checks passed!")
    else:
        print("   ❌ Some code quality issues found")
        print("   💡 Run with auto_fix=True to fix formatting issues automatically")

    print("\n" + "=" * 60)
    print("Code Quality Check System Demo Complete")
    print("=" * 60)

    return comprehensive_result


if __name__ == "__main__":
    result = main()
    # Exit with appropriate code
    sys.exit(0 if result.status in [CheckStatus.SUCCESS, CheckStatus.WARNING] else 1)
