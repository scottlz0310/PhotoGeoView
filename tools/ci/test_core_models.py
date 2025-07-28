#!/usr/bin/env python3
"""
Test script for core data models and interfaces.

This script validates that the core data models and interfaces
are properly implemented and can be used correctly.
"""

import sys
import json
from datetime import datetime
from pathlib import Path

# Add the tools directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ci.models import CheckResult, CheckStatus, SimulationResult, RegressionIssue, SeverityLevel
from ci.interfaces import CheckerFactory, CISimulationError


def test_check_result():
    """Test CheckResult model functionality."""
    print("Testing CheckResult model...")

    # Create a sample check result
    result = CheckResult(
        name="test_check",
        status=CheckStatus.SUCCESS,
        duration=1.5,
        output="Test completed successfully",
        errors=[],
        warnings=["Minor warning"],
        suggestions=["Consider optimization"],
        metadata={"test_count": 10},
        python_version="3.9"
    )

    # Test properties
    assert result.is_successful == True
    assert result.has_errors == False

    # Test serialization
    result_dict = result.to_dict()
    assert result_dict["name"] == "test_check"
    assert result_dict["status"] == "success"

    # Test deserialization
    restored_result = CheckResult.from_dict(result_dict)
    assert restored_result.name == result.name
    assert restored_result.status == result.status

    print("✓ CheckResult model tests passed")


def test_regression_issue():
    """Test RegressionIssue model functionality."""
    print("Testing RegressionIssue model...")

    # Create a sample regression issue
    issue = RegressionIssue(
        test_name="performance_test",
        baseline_value=100.0,
        current_value=150.0,
        regression_percentage=50.0,
        severity=SeverityLevel.HIGH,
        description="Performance degraded significantly",
        metric_type="performance",
        threshold_exceeded=True
    )

    # Test serialization
    issue_dict = issue.to_dict()
    assert issue_dict["test_name"] == "performance_test"
    assert issue_dict["severity"] == "high"

    # Test deserialization
    restored_issue = RegressionIssue.from_dict(issue_dict)
    assert restored_issue.test_name == issue.test_name
    assert restored_issue.severity == issue.severity

    print("✓ RegressionIssue model tests passed")


def test_simulation_result():
    """Test SimulationResult model functionality."""
    print("Testing SimulationResult model...")

    # Create sample check results
    check1 = CheckResult("check1", CheckStatus.SUCCESS, 1.0)
    check2 = CheckResult("check2", CheckStatus.FAILURE, 2.0, errors=["Error occurred"])

    # Create sample regression issue
    regression = RegressionIssue(
        "test", 100.0, 120.0, 20.0, SeverityLevel.MEDIUM, "Minor regression"
    )

    # Create simulation result
    sim_result = SimulationResult(
        overall_status=CheckStatus.WARNING,
        total_duration=3.0,
        check_results={"check1": check1, "check2": check2},
        python_versions_tested=["3.9", "3.10"],
        summary="Mixed results",
        regression_issues=[regression]
    )

    # Test properties
    assert sim_result.is_successful == True  # WARNING is considered successful
    assert len(sim_result.failed_checks) == 1
    assert len(sim_result.successful_checks) == 1

    # Test serialization
    sim_dict = sim_result.to_dict()
    assert sim_dict["overall_status"] == "warning"
    assert len(sim_dict["check_results"]) == 2

    # Test deserialization
    restored_sim = SimulationResult.from_dict(sim_dict)
    assert restored_sim.overall_status == sim_result.overall_status
    assert len(restored_sim.check_results) == 2

    print("✓ SimulationResult model tests passed")


def test_checker_factory():
    """Test CheckerFactory functionality."""
    print("Testing CheckerFactory...")

    # Test initial state
    assert len(CheckerFactory.get_available_checkers()) == 0
    assert not CheckerFactory.is_checker_available("test_checker")

    # Create a mock checker class
    from ci.interfaces import CheckerInterface

    class MockChecker(CheckerInterface):
        @property
        def name(self):
            return "Mock Checker"

        @property
        def check_type(self):
            return "mock"

        @property
        def dependencies(self):
            return []

        def is_available(self):
            return True

        def run_check(self, **kwargs):
            return CheckResult("mock_check", CheckStatus.SUCCESS, 0.1)

    # Register the mock checker
    CheckerFactory.register_checker("mock", MockChecker)

    # Test registration
    assert CheckerFactory.is_checker_available("mock")
    assert "mock" in CheckerFactory.get_available_checkers()

    # Test creation
    checker = CheckerFactory.create_checker("mock", {})
    assert isinstance(checker, MockChecker)
    assert checker.name == "Mock Checker"

    print("✓ CheckerFactory tests passed")


def main():
    """Run all tests."""
    print("Running core models and interfaces tests...\n")

    try:
        test_check_result()
        test_regression_issue()
        test_simulation_result()
        test_checker_factory()

        print("\n✅ All tests passed successfully!")
        print("Core data models and interfaces are working correctly.")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
