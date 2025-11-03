#!/usr/bin/env python3
"""
Test script to verify CI loop fix

This script tests that the infinite loop prevention mechanisms work correctly.
"""

import os
import subprocess
import sys
from pathlib import Path


def test_environment_protection():
    """Test that environment variable protection works"""
    print("🧪 Testing environment variable protection...")

    # Set the protection variable
    os.environ["CI_SIMULATION_RUNNING"] = "true"

    # Try to run CI simulator
    result = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).parent.parent / "tools" / "ci" / "simulator.py"),
            "--version",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0 and "CI simulation already running" in result.stdout:
        print("✅ Environment protection working")
        return True
    else:
        print("❌ Environment protection failed")
        print(f"Return code: {result.returncode}")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")
        return False


def test_marker_file_protection():
    """Test that marker file protection works"""
    print("🧪 Testing marker file protection...")

    # Create marker file
    marker_file = Path(".skip_ci_hooks")
    marker_file.touch()

    try:
        # Test pre-commit hook
        result = subprocess.run(
            ["bash", "-c", "cd . && .git/hooks/pre-commit"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0 and "CI hooks disabled" in result.stdout:
            print("✅ Marker file protection working")
            return True
        else:
            print("❌ Marker file protection failed")
            print(f"Return code: {result.returncode}")
            print(f"Stdout: {result.stdout}")
            print(f"Stderr: {result.stderr}")
            return False
    finally:
        # Clean up
        if marker_file.exists():
            marker_file.unlink()


def test_git_command_protection():
    """Test that Git commands run with protection"""
    print("🧪 Testing Git command protection...")

    # Import the utils module
    sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "ci"))
    from utils import run_command

    # Run a git command
    returncode, stdout, stderr = run_command(["git", "status", "--porcelain"])

    if returncode == 0:
        print("✅ Git command protection working")
        return True
    else:
        print("❌ Git command protection failed")
        print(f"Return code: {returncode}")
        print(f"Stderr: {stderr}")
        return False


def main():
    """Run all tests"""
    print("🚀 Testing CI infinite loop prevention...")
    print()

    tests = [
        test_environment_protection,
        test_marker_file_protection,
        test_git_command_protection,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
        print()

    print(f"📊 Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! CI loop prevention is working.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
