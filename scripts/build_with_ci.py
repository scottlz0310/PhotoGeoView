#!/usr/bin/env python3
"""
Build script with integrated CI checks.
"""

import sys
import subprocess
from pathlib import Path

def main():
    project_root = Path(__file__).parent.parent

    print("Running pre-build CI checks...")

    # Run CI simulator
    result = subprocess.run([
        sys.executable, "-m", "tools.ci.simulator",
        "run", "--checks", "code_quality", "test_runner",
        "--format", "both", "--fail-fast"
    ], cwd=project_root)

    if result.returncode != 0:
        print("❌ CI checks failed. Build aborted.")
        return 1

    print("✅ CI checks passed. Proceeding with build...")

    # Run actual build
    build_result = subprocess.run([
        sys.executable, "-m", "build"
    ], cwd=project_root)

    return build_result.returncode

if __name__ == "__main__":
    sys.exit(main())
