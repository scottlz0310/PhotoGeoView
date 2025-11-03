#!/usr/bin/env python3
"""
Pre-commit script for PhotoGeoView.
"""

import subprocess
import sys
from pathlib import Path


def main():
    project_root = Path(__file__).parent.parent

    print("Running pre-commit checks...")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.ci.simulator",
            "run",
            "code_quality",
            "test_runner",
            "--fail-fast",
            "--format",
            "markdown",
        ],
        cwd=project_root,
    )

    if result.returncode == 0:
        print("✅ Pre-commit checks passed")
    else:
        print("❌ Pre-commit checks failed")

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
