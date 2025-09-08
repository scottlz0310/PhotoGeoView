#!/usr/bin/env python3
"""
Final Integration Test for CI/CD Simulation System

This test verifies that all components of the CI/CD simulation system
are properly integrated and working together.
"""

import sys
import json
from pathlib import Path
import subprocess
import tempfile
import shutil

def test_production_config():
    """Test production configuration system"""
    print("Testing production configuration...")

    result = subprocess.run([
        sys.executable, "tools/ci/production_config.py",
        "--project-root", ".", "--validate"
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ Production configuration validation passed")
        return True
    else:
        print(f"❌ Production configuration validation failed: {result.stderr}")
        return False

def test_ci_simulator_availability():
    """Test CI simulator availability"""
    print("Testing CI simulator availability...")

    result = subprocess.run([
        sys.executable, "-m", "tools.ci.simulator", "--version"
    ], capture_output=True, text=True)

    if result.returncode == 0 and "CI Simulator" in result.stdout:
        print("✅ CI Simulator is available")
        return True
    else:
        print(f"❌ CI Simulator not available: {result.stderr}")
        return False

def test_project_structure():
    """Test project structure integrity"""
    print("Testing project structure...")

    required_paths = [
        "tools/ci/simulator.py",
        "tools/ci/production_config.py",
        "tools/ci/production_monitor.py",
        "tools/create_deployment_package.py",
        ".kiro/settings/production_config.json",
        ".kiro/settings/ci_simulator.json",
        "pyproject.toml",
        "requirements.txt"
    ]

    missing_paths = []
    for path_str in required_paths:
        path = Path(path_str)
        if not path.exists():
            missing_paths.append(path_str)

    if not missing_paths:
        print("✅ All required project structure components exist")
        return True
    else:
        print(f"❌ Missing required paths: {missing_paths}")
        return False

def test_pyproject_integration():
    """Test pyproject.toml integration"""
    print("Testing pyproject.toml integration...")

    try:
        with open("pyproject.toml", "r", encoding="utf-8") as f:
            content = f.read()

        # Check for CI simulator script entry
        if "ci-simulator" in content and "tools.ci.simulator:main" in content:
            print("✅ CI simulator is properly integrated in pyproject.toml")
            return True
        else:
            print("❌ CI simulator not found in pyproject.toml scripts")
            return False

    except Exception as e:
        print(f"❌ Error reading pyproject.toml: {e}")
        return False

def test_deployment_package_creation():
    """Test deployment package creation (dry run)"""
    print("Testing deployment package creation...")

    try:
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test the deployment package creator import
            result = subprocess.run([
                sys.executable, "-c",
                "from tools.create_deployment_package import DeploymentPackageCreator; print('Import successful')"
            ], capture_output=True, text=True)

            if result.returncode == 0:
                print("✅ Deployment package creator is importable")
                return True
            else:
                print(f"❌ Deployment package creator import failed: {result.stderr}")
                return False

    except Exception as e:
        print(f"❌ Error testing deployment package creation: {e}")
        return False

def test_monitoring_system():
    """Test monitoring system"""
    print("Testing monitoring system...")

    try:
        result = subprocess.run([
            sys.executable, "-c",
            "from tools.ci.production_monitor import ProductionMonitor; print('Import successful')"
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Production monitoring system is importable")
            return True
        else:
            print(f"❌ Production monitoring system import failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Error testing monitoring system: {e}")
        return False

def main():
    """Run all integration tests"""
    print("=" * 60)
    print("Final Integration Test for CI/CD Simulation System")
    print("=" * 60)

    tests = [
        test_project_structure,
        test_pyproject_integration,
        test_production_config,
        test_ci_simulator_availability,
        test_deployment_package_creation,
        test_monitoring_system
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            print()

    print("=" * 60)
    print(f"Integration Test Results: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("🎉 All integration tests passed! The CI/CD simulation system is ready for production.")
        return True
    else:
        print("⚠️ Some integration tests failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
