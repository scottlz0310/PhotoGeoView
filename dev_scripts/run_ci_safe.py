#!/usr/bin/env python3
"""
Safe CI Runner - Prevents hanging and provides timeout protection

This script runs CI checks with proper timeout protection to prevent hanging.
"""

import signal
import subprocess
import sys
from pathlib import Path


class TimeoutError(Exception):
    pass


def timeout_handler(signum, frame):
    raise TimeoutError("Command timed out")


def run_with_timeout(cmd, timeout_seconds=60, cwd=None):
    """Run a command with timeout protection."""
    print(f"Running: {' '.join(cmd)} (timeout: {timeout_seconds}s)")

    try:
        # Set up timeout signal
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)

        # Run the command
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout_seconds
        )

        # Cancel the alarm
        signal.alarm(0)

        return result.returncode == 0, result.stdout, result.stderr

    except (subprocess.TimeoutExpired, TimeoutError):
        print(f"⚠️  Command timed out after {timeout_seconds} seconds")
        return False, "", f"Command timed out after {timeout_seconds} seconds"
    except Exception as e:
        signal.alarm(0)  # Make sure to cancel alarm
        print(f"❌ Command failed: {e}")
        return False, "", str(e)


def main():
    """Run CI checks safely."""
    print("🚀 Starting Safe CI Checks...")
    print("=" * 50)

    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("❌ Please run this script from the project root directory")
        return 1

    checks = [
        {
            "name": "Python Syntax Check",
            "cmd": [sys.executable, "-m", "py_compile", "main.py"],
            "timeout": 30,
        },
        {
            "name": "Import Test",
            "cmd": [sys.executable, "-c", "import main; print('✅ Import successful')"],
            "timeout": 30,
        },
        {
            "name": "Basic Test Discovery",
            "cmd": [sys.executable, "-m", "pytest", "--collect-only", "-q"],
            "timeout": 60,
        },
    ]

    results = []

    for check in checks:
        print(f"\n📋 {check['name']}")
        print("-" * 30)

        success, stdout, stderr = run_with_timeout(check["cmd"], check["timeout"])

        if success:
            print(f"✅ {check['name']}: PASSED")
            if stdout.strip():
                print(f"Output: {stdout.strip()}")
        else:
            print(f"❌ {check['name']}: FAILED")
            if stderr.strip():
                print(f"Error: {stderr.strip()}")

        results.append(
            {
                "name": check["name"],
                "success": success,
                "stdout": stdout,
                "stderr": stderr,
            }
        )

    # Summary
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)

    passed = sum(1 for r in results if r["success"])
    total = len(results)

    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{status} {result['name']}")

    print(f"\nResult: {passed}/{total} checks passed")

    if passed == total:
        print("🎉 All checks passed!")
        return 0
    else:
        print("⚠️  Some checks failed")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
