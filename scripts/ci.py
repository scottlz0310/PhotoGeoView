#!/usr/bin/env python3
"""
Convenient CI runner script for PhotoGeoView.
"""

import sys
import subprocess
from pathlib import Path

def main():
    project_root = Path(__file__).parent.parent

    # Default to quick CI if no arguments provided
    if len(sys.argv) == 1:
        args = ["run", "--checks", "code_quality", "test_runner", "--format", "both"]
    else:
        args = sys.argv[1:]

    # Run CI simulator
    cmd = [sys.executable, "-m", "tools.ci.simulator"] + args

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=project_root)

    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
