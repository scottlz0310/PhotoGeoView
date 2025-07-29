#!/usr/bin/env python3
"""
Simple test for PerformanceAnalyzer

Quick test to verify the PerformanceAnalyzer can be imported and instantiated.
"""

import sys
import tempfile
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_import():
    """Test that we can import the PerformanceAnalyzer."""
    try:
        from tools.ci.checkers.performance_analyzer import PerformanceAnalyzer
        from tools.ci.models import CheckStatus
        print("✅ Import successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_instantiation():
    """Test that we can create a PerformanceAnalyzer instance."""
    try:
        from tools.ci.checkers.performance_analyzer import PerformanceAnalyzer

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            config = {
                'benchmark_timeout': 60,
                'regression_threshold': 30.0,
                'baseline_file': temp_path / 'baseline.json',
                'results_dir': temp_path / 'results'
            }

            analyzer = PerformanceAnalyzer(config)
            print(f"✅ Instantiation successful - Name: {analyzer.name}")
            print(f"   Check type: {analyzer.check_type}")
            print(f"   Dependencies: {analyzer.dependencies}")
            print(f"   Available: {analyzer.is_available()}")
            return True

    except Exception as e:
        print(f"❌ Instantiation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("Simple PerformanceAnalyzer Test")
    print("=" * 40)

    success1 = test_import()
    success2 = test_instantiation()

    if success1 and success2:
        print("\n🎉 Basic tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    exit(main())
