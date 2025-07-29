#!/usr/bin/env python3
"""
Test script for PerformanceAnalyzer implementation

This script tests the basic functionality of the PerformanceAnalyzer
to ensure it works correctly with the CI simulation system.
"""

import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tools.ci.checkers.performance_analyzer import PerformanceAnalyzer
from tools.ci.models import CheckStatus


def test_performance_analyzer():
    """Test the PerformanceAnalyzer implementation."""
    print("Testing PerformanceAnalyzer implementation...")

    # Create temporary directories for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Configure the analyzer
        config = {
            'benchmark_timeout': 60,
            'memory_sample_interval': 0.1,
            'regression_threshold': 30.0,
            'baseline_file': temp_path / 'baseline.json',
            'results_dir': temp_path / 'results'
        }

        analyzer = PerformanceAnalyzer(config)

        # Test 1: Check availability
        print("1. Testing availability check...")
        is_available = analyzer.is_available()
        print(f"   Analyzer available: {is_available}")

        if not is_available:
            print("   Skipping further tests - dependencies not available")
            return True

        # Test 2: Run performance check
        print("2. Running performance analysis...")
        result = analyzer.run_check()

        print(f"   Status: {result.status}")
        print(f"   Duration: {result.duration:.2f}s")
        print(f"   Benchmark count: {result.metadata.get('benchmark_count', 0)}")
        print(f"   Peak memory: {result.metadata.get('peak_memory', 0):.1f}MB")

        # Test 3: Check if results were saved
        print("3. Checking result persistence...")
        results_dir = temp_path / 'results'
        if results_dir.exists():
            result_files = list(results_dir.glob("performance_results_*.json"))
            print(f"   Result files created: {len(result_files)}")

            if result_files:
                # Load and verify a result file
                with open(result_files[0], 'r') as f:
                    data = json.load(f)
                print(f"   Benchmarks in result: {len(data.get('benchmarks', {}))}")
                print(f"   Metrics in result: {len(data.get('metrics', []))}")

        # Test 4: Test regression detection (should be empty on first run)
        print("4. Testing regression detection...")
        regressions = analyzer.detect_performance_regression(threshold=20.0)
        print(f"   Regressions detected: {len(regressions)}")

        # Test 5: Test trend analysis (should have insufficient data)
        print("5. Testing trend analysis...")
        trends = analyzer.analyze_performance_trends(history_days=7)
        print(f"   Trend analysis status: {trends.get('status', 'unknown')}")

        print("✅ PerformanceAnalyzer test completed successfully!")
        return True


def test_benchmark_simulation():
    """Test individual benchmark simulations."""
    print("\nTesting individual benchmark simulations...")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        config = {
            'baseline_file': temp_path / 'baseline.json',
            'results_dir': temp_path / 'results'
        }

        analyzer = PerformanceAnalyzer(config)

        if not analyzer.is_available():
            print("   Skipping benchmark tests - dependencies not available")
            return True

        # Test individual benchmarks
        benchmarks = [
            ("file_discovery", analyzer._benchmark_file_discovery),
            ("image_processing", analyzer._benchmark_image_processing),
            ("ui_responsiveness", analyzer._benchmark_ui_responsiveness),
            ("memory_efficiency", analyzer._benchmark_memory_efficiency),
            ("concurrent_operations", analyzer._benchmark_concurrent_operations)
        ]

        for name, benchmark_func in benchmarks:
            print(f"   Testing {name}...")
            try:
                result = benchmark_func()
                print(f"     Duration: {result.duration:.3f}s")
                print(f"     Memory peak: {result.memory_peak:.1f}MB")
                print(f"     CPU peak: {result.cpu_peak:.1f}%")
                if result.throughput:
                    print(f"     Throughput: {result.throughput:.2f} ops/sec")
            except Exception as e:
                print(f"     Error: {e}")
                return False

        print("✅ Benchmark simulation tests completed successfully!")
        return True


def main():
    """Main test function."""
    print("=" * 60)
    print("PerformanceAnalyzer Implementation Test")
    print("=" * 60)

    try:
        # Run tests
        success1 = test_performance_analyzer()
        success2 = test_benchmark_simulation()

        if success1 and success2:
            print("\n🎉 All tests passed!")
            return 0
        else:
            print("\n❌ Some tests failed!")
            return 1

    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
