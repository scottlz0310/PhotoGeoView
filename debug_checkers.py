#!/usr/bin/env python3
"""
Debug script to test checker imports and registration
"""

import sys
import traceback
from pathlib import Path

# Add the tools/ci directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "tools" / "ci"))

def test_checker_imports():
    """Test importing all checkers"""
    checkers = [
        ('code_quality', 'CodeQualityChecker'),
        ('test_runner', 'TestRunner'),
        ('security_scanner', 'SecurityScanner'),
        ('performance_analyzer', 'PerformanceAnalyzer'),
        ('ai_component_tester', 'AIComponentTester')
    ]

    successful_imports = []
    failed_imports = []

    for module_name, class_name in checkers:
        try:
            # Try importing from checkers package
            module = __import__(f'checkers.{module_name}', fromlist=[class_name])
            checker_class = getattr(module, class_name)
            successful_imports.append((module_name, class_name, checker_class))
            print(f"✅ Successfully imported {class_name} from checkers.{module_name}")
        except Exception as e:
            failed_imports.append((module_name, class_name, str(e)))
            print(f"❌ Failed to import {class_name} from checkers.{module_name}: {e}")
            traceback.print_exc()

    return successful_imports, failed_imports

def test_checker_factory():
    """Test CheckerFactory registration"""
    try:
        from interfaces import CheckerFactory
        print(f"✅ CheckerFactory imported successfully")

        # Test registration
        successful_imports, _ = test_checker_imports()

        for module_name, class_name, checker_class in successful_imports:
            try:
                CheckerFactory.register_checker(module_name, checker_class)
                print(f"✅ Registered {class_name} as {module_name}")
            except Exception as e:
                print(f"❌ Failed to register {class_name}: {e}")
                traceback.print_exc()

        # Check available checkers
        available = CheckerFactory.get_available_checkers()
        print(f"Available checkers: {available}")

        return available

    except Exception as e:
        print(f"❌ CheckerFactory test failed: {e}")
        traceback.print_exc()
        return []

def test_simulator_initialization():
    """Test CISimulator initialization"""
    try:
        from simulator import CISimulator
        print(f"✅ CISimulator imported successfully")

        simulator = CISimulator()
        print(f"✅ CISimulator initialized successfully")

        available_checks = simulator.orchestrator.get_available_checks()
        print(f"Available checks from orchestrator: {available_checks}")

        return available_checks

    except Exception as e:
        print(f"❌ CISimulator test failed: {e}")
        traceback.print_exc()
        return []

if __name__ == "__main__":
    print("=" * 60)
    print("CI Checker Debug Script")
    print("=" * 60)

    print("\n1. Testing checker imports...")
    print("-" * 40)
    test_checker_imports()

    print("\n2. Testing CheckerFactory...")
    print("-" * 40)
    available_from_factory = test_checker_factory()

    print("\n3. Testing CISimulator initialization...")
    print("-" * 40)
    available_from_simulator = test_simulator_initialization()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Available from CheckerFactory: {available_from_factory}")
    print(f"Available from CISimulator: {available_from_simulator}")
