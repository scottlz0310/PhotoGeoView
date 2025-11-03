"""
Unit tests for core data models.
"""

from datetime import datetime
from pathlib import Path

import pytest
from models import (
    CheckResult,
    CheckStatus,
    CheckTask,
    RegressionIssue,
    SeverityLevel,
    SimulationResult,
)


class TestCheckResult:
    """Test cases for CheckResult model."""

    def test_check_result_creation(self):
        """Test basic CheckResult creation."""
        result = CheckResult(
            name="test_check", status=CheckStatus.SUCCESS, duration=1.5
        )

        assert result.name == "test_check"
        assert result.status == CheckStatus.SUCCESS
        assert result.duration == 1.5
        assert result.output == ""
        assert result.errors == []
        assert result.warnings == []
        assert result.suggestions == []
        assert isinstance(result.metadata, dict)
        assert isinstance(result.timestamp, datetime)

    def test_check_result_with_all_fields(self):
        """Test CheckResult creation with all fields."""
        result = CheckResult(
            name="comprehensive_check",
            status=CheckStatus.WARNING,
            duration=2.3,
            output="Check completed with warnings",
            errors=["Error 1", "Error 2"],
            warnings=["Warning 1"],
            suggestions=["Suggestion 1", "Suggestion 2"],
            metadata={"test_count": 5, "coverage": 80.0},
            python_version="3.10",
        )

        assert result.name == "comprehensive_check"
        assert result.status == CheckStatus.WARNING
        assert result.duration == 2.3
        assert result.output == "Check completed with warnings"
        assert len(result.errors) == 2
        assert len(result.warnings) == 1
        assert len(result.suggestions) == 2
        assert result.metadata["test_count"] == 5
        assert result.python_version == "3.10"

    def test_is_successful_property(self):
        """Test is_successful property."""
        success_result = CheckResult("test", CheckStatus.SUCCESS, 1.0)
        warning_result = CheckResult("test", CheckStatus.WARNING, 1.0)
        failure_result = CheckResult("test", CheckStatus.FAILURE, 1.0)
        skipped_result = CheckResult("test", CheckStatus.SKIPPED, 1.0)

        assert success_result.is_successful is True
        assert warning_result.is_successful is True
        assert failure_result.is_successful is False
        assert skipped_result.is_successful is False

    def test_has_errors_property(self):
        """Test has_errors property."""
        no_errors = CheckResult("test", CheckStatus.SUCCESS, 1.0)
        with_errors = CheckResult("test", CheckStatus.SUCCESS, 1.0, errors=["Error"])
        failure_status = CheckResult("test", CheckStatus.FAILURE, 1.0)

        assert no_errors.has_errors is False
        assert with_errors.has_errors is True
        assert failure_status.has_errors is True

    def test_to_dict_serialization(self):
        """Test CheckResult serialization to dictionary."""
        result = CheckResult(
            name="test_check",
            status=CheckStatus.SUCCESS,
            duration=1.5,
            output="Test output",
            errors=["Error 1"],
            warnings=["Warning 1"],
            suggestions=["Suggestion 1"],
            metadata={"key": "value"},
            python_version="3.10",
        )

        data = result.to_dict()

        assert data["name"] == "test_check"
        assert data["status"] == "success"
        assert data["duration"] == 1.5
        assert data["output"] == "Test output"
        assert data["errors"] == ["Error 1"]
        assert data["warnings"] == ["Warning 1"]
        assert data["suggestions"] == ["Suggestion 1"]
        assert data["metadata"] == {"key": "value"}
        assert data["python_version"] == "3.10"
        assert "timestamp" in data

    def test_from_dict_deserialization(self):
        """Test CheckResult deserialization from dictionary."""
        timestamp = datetime.now()
        data = {
            "name": "test_check",
            "status": "success",
            "duration": 1.5,
            "output": "Test output",
            "errors": ["Error 1"],
            "warnings": ["Warning 1"],
            "suggestions": ["Suggestion 1"],
            "metadata": {"key": "value"},
            "timestamp": timestamp.isoformat(),
            "python_version": "3.10",
        }

        result = CheckResult.from_dict(data)

        assert result.name == "test_check"
        assert result.status == CheckStatus.SUCCESS
        assert result.duration == 1.5
        assert result.output == "Test output"
        assert result.errors == ["Error 1"]
        assert result.warnings == ["Warning 1"]
        assert result.suggestions == ["Suggestion 1"]
        assert result.metadata == {"key": "value"}
        assert result.python_version == "3.10"
        assert result.timestamp.isoformat() == timestamp.isoformat()


class TestRegressionIssue:
    """Test cases for RegressionIssue model."""

    def test_regression_issue_creation(self):
        """Test basic RegressionIssue creation."""
        issue = RegressionIssue(
            test_name="performance_test",
            baseline_value=100.0,
            current_value=150.0,
            regression_percentage=50.0,
            severity=SeverityLevel.HIGH,
            description="Performance degraded by 50%",
        )

        assert issue.test_name == "performance_test"
        assert issue.baseline_value == 100.0
        assert issue.current_value == 150.0
        assert issue.regression_percentage == 50.0
        assert issue.severity == SeverityLevel.HIGH
        assert issue.description == "Performance degraded by 50%"
        assert issue.metric_type == "performance"
        assert issue.threshold_exceeded is False

    def test_regression_issue_with_all_fields(self):
        """Test RegressionIssue creation with all fields."""
        issue = RegressionIssue(
            test_name="memory_test",
            baseline_value=50.0,
            current_value=80.0,
            regression_percentage=60.0,
            severity=SeverityLevel.CRITICAL,
            description="Memory usage increased significantly",
            metric_type="memory",
            threshold_exceeded=True,
        )

        assert issue.test_name == "memory_test"
        assert issue.metric_type == "memory"
        assert issue.threshold_exceeded is True

    def test_regression_issue_serialization(self):
        """Test RegressionIssue serialization."""
        issue = RegressionIssue(
            test_name="test",
            baseline_value=100.0,
            current_value=150.0,
            regression_percentage=50.0,
            severity=SeverityLevel.HIGH,
            description="Test regression",
        )

        data = issue.to_dict()

        assert data["test_name"] == "test"
        assert data["baseline_value"] == 100.0
        assert data["current_value"] == 150.0
        assert data["regression_percentage"] == 50.0
        assert data["severity"] == "high"
        assert data["description"] == "Test regression"
        assert data["metric_type"] == "performance"
        assert data["threshold_exceeded"] is False

    def test_regression_issue_deserialization(self):
        """Test RegressionIssue deserialization."""
        data = {
            "test_name": "test",
            "baseline_value": 100.0,
            "current_value": 150.0,
            "regression_percentage": 50.0,
            "severity": "high",
            "description": "Test regression",
            "metric_type": "memory",
            "threshold_exceeded": True,
        }

        issue = RegressionIssue.from_dict(data)

        assert issue.test_name == "test"
        assert issue.baseline_value == 100.0
        assert issue.current_value == 150.0
        assert issue.regression_percentage == 50.0
        assert issue.severity == SeverityLevel.HIGH
        assert issue.description == "Test regression"
        assert issue.metric_type == "memory"
        assert issue.threshold_exceeded is True


class TestSimulationResult:
    """Test cases for SimulationResult model."""

    def test_simulation_result_creation(self, sample_check_result):
        """Test basic SimulationResult creation."""
        result = SimulationResult(
            overall_status=CheckStatus.SUCCESS,
            total_duration=5.0,
            check_results={"test": sample_check_result},
            python_versions_tested=["3.10"],
            summary="All checks passed",
        )

        assert result.overall_status == CheckStatus.SUCCESS
        assert result.total_duration == 5.0
        assert len(result.check_results) == 1
        assert result.python_versions_tested == ["3.10"]
        assert result.summary == "All checks passed"
        assert isinstance(result.report_paths, dict)
        assert isinstance(result.regression_issues, list)
        assert isinstance(result.timestamp, datetime)
        assert isinstance(result.configuration, dict)

    def test_is_successful_property(self):
        """Test is_successful property."""
        success_result = SimulationResult(CheckStatus.SUCCESS, 1.0, {}, [], "Success")
        warning_result = SimulationResult(CheckStatus.WARNING, 1.0, {}, [], "Warning")
        failure_result = SimulationResult(CheckStatus.FAILURE, 1.0, {}, [], "Failure")

        assert success_result.is_successful is True
        assert warning_result.is_successful is True
        assert failure_result.is_successful is False

    def test_failed_checks_property(
        self, sample_check_result, sample_failed_check_result
    ):
        """Test failed_checks property."""
        result = SimulationResult(
            CheckStatus.WARNING,
            5.0,
            {"success": sample_check_result, "failure": sample_failed_check_result},
            ["3.10"],
            "Mixed results",
        )

        failed = result.failed_checks
        assert len(failed) == 1
        assert failed[0].name == "failed_check"

    def test_successful_checks_property(
        self, sample_check_result, sample_failed_check_result
    ):
        """Test successful_checks property."""
        result = SimulationResult(
            CheckStatus.WARNING,
            5.0,
            {"success": sample_check_result, "failure": sample_failed_check_result},
            ["3.10"],
            "Mixed results",
        )

        successful = result.successful_checks
        assert len(successful) == 1
        assert successful[0].name == "test_check"

    def test_get_checks_by_status(
        self, sample_check_result, sample_failed_check_result
    ):
        """Test get_checks_by_status method."""
        result = SimulationResult(
            CheckStatus.WARNING,
            5.0,
            {"success": sample_check_result, "failure": sample_failed_check_result},
            ["3.10"],
            "Mixed results",
        )

        success_checks = result.get_checks_by_status(CheckStatus.SUCCESS)
        failure_checks = result.get_checks_by_status(CheckStatus.FAILURE)

        assert len(success_checks) == 1
        assert len(failure_checks) == 1
        assert success_checks[0].name == "test_check"
        assert failure_checks[0].name == "failed_check"

    def test_simulation_result_serialization(self, sample_simulation_result):
        """Test SimulationResult serialization."""
        data = sample_simulation_result.to_dict()

        assert data["overall_status"] == "warning"
        assert data["total_duration"] == 5.3
        assert "check_results" in data
        assert len(data["check_results"]) == 2
        assert data["python_versions_tested"] == ["3.10", "3.11"]
        assert data["summary"] == "2 checks completed: 1 success, 1 failure"
        assert "timestamp" in data

    def test_simulation_result_deserialization(self, sample_simulation_result):
        """Test SimulationResult deserialization."""
        data = sample_simulation_result.to_dict()
        restored = SimulationResult.from_dict(data)

        assert restored.overall_status == sample_simulation_result.overall_status
        assert restored.total_duration == sample_simulation_result.total_duration
        assert len(restored.check_results) == len(
            sample_simulation_result.check_results
        )
        assert (
            restored.python_versions_tested
            == sample_simulation_result.python_versions_tested
        )
        assert restored.summary == sample_simulation_result.summary

    def test_save_and_load_from_file(self, sample_simulation_result, temp_dir):
        """Test saving and loading SimulationResult from file."""
        file_path = Path(temp_dir) / "test_result.json"

        # Save to file
        sample_simulation_result.save_to_file(str(file_path))
        assert file_path.exists()

        # Load from file
        loaded_result = SimulationResult.load_from_file(str(file_path))

        assert loaded_result.overall_status == sample_simulation_result.overall_status
        assert loaded_result.total_duration == sample_simulation_result.total_duration
        assert len(loaded_result.check_results) == len(
            sample_simulation_result.check_results
        )


class TestCheckTask:
    """Test cases for CheckTask model."""

    def test_check_task_creation(self):
        """Test basic CheckTask creation."""
        task = CheckTask(name="test_task", check_type="code_quality")

        assert task.name == "test_task"
        assert task.check_type == "code_quality"
        assert task.python_version is None
        assert task.dependencies == []
        assert task.timeout is None
        assert task.priority == 0
        assert isinstance(task.metadata, dict)

    def test_check_task_with_all_fields(self):
        """Test CheckTask creation with all fields."""
        task = CheckTask(
            name="comprehensive_task",
            check_type="security",
            python_version="3.10",
            dependencies=["code_quality", "tests"],
            timeout=300.0,
            priority=5,
            metadata={"config": "custom"},
        )

        assert task.name == "comprehensive_task"
        assert task.check_type == "security"
        assert task.python_version == "3.10"
        assert task.dependencies == ["code_quality", "tests"]
        assert task.timeout == 300.0
        assert task.priority == 5
        assert task.metadata == {"config": "custom"}

    def test_check_task_validation(self):
        """Test CheckTask validation."""
        # Valid task should not raise
        CheckTask("valid_task", "code_quality")

        # Empty name should raise
        with pytest.raises(ValueError, match="Task name cannot be empty"):
            CheckTask("", "code_quality")

        # Empty check_type should raise
        with pytest.raises(ValueError, match="Check type cannot be empty"):
            CheckTask("valid_task", "")


class TestEnumValues:
    """Test enum values and behavior."""

    def test_check_status_values(self):
        """Test CheckStatus enum values."""
        assert CheckStatus.SUCCESS.value == "success"
        assert CheckStatus.FAILURE.value == "failure"
        assert CheckStatus.WARNING.value == "warning"
        assert CheckStatus.SKIPPED.value == "skipped"
        assert CheckStatus.IN_PROGRESS.value == "in_progress"

    def test_severity_level_values(self):
        """Test SeverityLevel enum values."""
        assert SeverityLevel.CRITICAL.value == "critical"
        assert SeverityLevel.HIGH.value == "high"
        assert SeverityLevel.MEDIUM.value == "medium"
        assert SeverityLevel.LOW.value == "low"
        assert SeverityLevel.INFO.value == "info"

    def test_enum_comparison(self):
        """Test enum comparison behavior."""
        assert CheckStatus.SUCCESS == CheckStatus.SUCCESS
        assert CheckStatus.SUCCESS != CheckStatus.FAILURE

        assert SeverityLevel.CRITICAL != SeverityLevel.HIGH
        assert SeverityLevel.LOW == SeverityLevel.LOW
