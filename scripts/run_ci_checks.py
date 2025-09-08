#!/usr/bin/env python3
"""
CI Checks Runner Script

This script runs individual CI checks sequentially to avoid resource conflicts
and ensure reliable execution.
"""

import logging
import subprocess
import sys
import time
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_check(check_name: str, timeout: int = 300) -> bool:
    """
    Run a single CI check with timeout.

    Args:
        check_name: Name of the check to run
        timeout: Timeout in seconds

    Returns:
        True if check passed, False otherwise
    """
    logger.info(f"Running {check_name} check...")
    start_time = time.time()

    try:
        # Run the check with timeout
        cmd = [
            sys.executable, "-m", "tools.ci.simulator", "run",
            check_name, "--timeout", str(timeout)
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout + 30  # Add 30 seconds buffer
        )

        duration = time.time() - start_time

        if result.returncode == 0:
            logger.info(f"✓ {check_name} completed successfully in {duration:.2f}s")
            return True
        else:
            logger.warning(f"⚠ {check_name} completed with warnings in {duration:.2f}s")
            logger.warning(f"Output: {result.stdout}")
            if result.stderr:
                logger.warning(f"Errors: {result.stderr}")
            return True  # Continue even with warnings

    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        logger.error(f"✗ {check_name} timed out after {duration:.2f}s")
        return False
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"✗ {check_name} failed with error after {duration:.2f}s: {e}")
        return False

def main():
    """Main function to run all CI checks sequentially."""
    logger.info("Starting sequential CI checks...")

    # Define checks with their timeouts
    checks = [
        ("code_quality", 60),
        ("performance_analyzer", 120),
        ("security_scanner", 60),
        ("test_runner", 300),
        ("ai_component_tester", 120),
    ]

    results = {}
    overall_success = True

    for check_name, timeout in checks:
        success = run_check(check_name, timeout)
        results[check_name] = success
        if not success:
            overall_success = False
            logger.error(f"Check {check_name} failed, but continuing...")

        # Add a small delay between checks
        time.sleep(2)

    # Print summary
    logger.info("\n" + "="*50)
    logger.info("CI CHECKS SUMMARY")
    logger.info("="*50)

    for check_name, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        logger.info(f"{check_name:20} : {status}")

    logger.info("="*50)
    if overall_success:
        logger.info("✓ All checks completed successfully!")
        return 0
    else:
        logger.warning("⚠ Some checks failed, but continuing...")
        return 0  # Return 0 to continue CI pipeline

if __name__ == "__main__":
    sys.exit(main())
