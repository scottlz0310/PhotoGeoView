#!/usr/bin/env python3
"""
Integration test for PerformanceAnalyzer with CI system

Tests the integration of PerformanceAnalyzer with the CI simulation system.
"""

import sys
import tempfile
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_checker_registration():
    """Test that PerformanceAnalyzer can be registered with the CheckerFactory."""
    try:
        from tools.ci.checkers.performance_analyzer import PerformanceAnalyzer
        from tools.ci.interfaces import CheckerFactory

        # Register the checker
        CheckerFactory.register_checker("performance", PerformanceAnalyzer)

        # Verify it's registered
        available_checkers = CheckerFactory.get_available_checkers()
        print(f"Available checkers: {available_checkers}")

        if "performance" in available_checkers:
            print("✅ PerformanceAnalyzer successfully registered")

            # Test creating an instance through the factory
            with tempfile.TemporaryDirectory() as temp_dir:
                config = {
                    "baseline_file": Path(temp_dir) / "baseline.json",
                    "results_dir": Path(temp_dir) / "results",
                }

                checker = CheckerFactory.create_checker("performance", config)
                print(f"✅ Factory creation successful - {checker.name}")
                return True
        else:
            print("❌ PerformanceAnalyzer not found in available checkers")
            return False

    except Exception as e:
        print(f"❌ Checker registration failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_package_import():
    """Test importing from the checkers package."""
    try:
        from tools.ci.checkers import PerformanceAnalyzer

        print("✅ Package import successful")
        return True
    except Exception as e:
        print(f"❌ Package import failed: {e}")
        return False


def main():
    """Main test function."""
    print("PerformanceAnalyzer Integration Test")
    print("=" * 45)

    success1 = test_package_import()
    success2 = test_checker_registration()

    if success1 and success2:
        print("\n🎉 Integration tests passed!")
        print("\nPerformanceAnalyzer is ready for use in the CI simulation system!")
        return 0
    else:
        print("\n❌ Some integration tests failed!")
        return 1


if __name__ == "__main__":
    exit(main())
