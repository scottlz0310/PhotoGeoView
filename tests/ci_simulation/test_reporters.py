"""
Unit tests for report generation components.
"""

import json
import os

# Import reporters
import sys
from datetime import datetime

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools", "ci"))

from models import (
    CheckResult,
    CheckStatus,
    RegressionIssue,
    SeverityLevel,
    SimulationResult,
)
from reporters.history_tracker import HistoryTracker
from reporters.json_reporter import JSONReporter
from reporters.markdown_reporter import MarkdownReporter


class TestMarkdownReporter:
    """Test cases for MarkdownReporter."""

    def test_markdown_reporter_creation(self):
        """Test MarkdownReporter creation."""
        reporter = MarkdownReporter()

        assert reporter.format_name == "markdown"
        assert reporter.file_extension == ".md"

    def test_generate_report_basic(self, sample_simulation_result, temp_dir):
        """Test basic markdown report generation."""
        reporter = MarkdownReporter()
        output_path = os.path.join(temp_dir, "test_report.md")

        result_path = reporter.generate_report(sample_simulation_result, output_path)

        assert result_path == output_path
        assert os.path.exists(output_path)

        # Check report content
        with open(output_path) as f:
            content = f.read()

        assert "# CI Simulation Report" in content
        assert "## Summary" in content
        assert "## Check Results" in content
        assert sample_simulation_result.summary in content

    def test_generate_report_with_errors(self, sample_failed_check_result, temp_dir):
        """Test markdown report generation with errors."""
        simulation_result = SimulationResult(
            overall_status=CheckStatus.FAILURE,
            total_duration=3.0,
            check_results={"failed_check": sample_failed_check_result},
            python_versions_tested=["3.10"],
            summary="Test failed",
        )

        reporter = MarkdownReporter()
        output_path = os.path.join(temp_dir, "error_report.md")

        result_path = reporter.generate_report(simulation_result, output_path)

        assert os.path.exists(result_path)

        with open(result_path) as f:
            content = f.read()

        assert "❌ FAILURE" in content
        assert "Syntax error in line 42" in content
        assert "Import error" in content

    def test_generate_report_with_regressions(self, sample_check_result, temp_dir):
        """Test markdown report generation with performance regressions."""
        regression = RegressionIssue(
            test_name="performance_test",
            baseline_value=100.0,
            current_value=150.0,
            regression_percentage=50.0,
            severity=SeverityLevel.HIGH,
            description="Performance degraded by 50%",
        )

        simulation_result = SimulationResult(
            overall_status=CheckStatus.WARNING,
            total_duration=5.0,
            check_results={"test": sample_check_result},
            python_versions_tested=["3.10"],
            summary="Test completed with regressions",
            regression_issues=[regression],
        )

        reporter = MarkdownReporter()
        output_path = os.path.join(temp_dir, "regression_report.md")

        result_path = reporter.generate_report(simulation_result, output_path)

        with open(result_path) as f:
            content = f.read()

        assert "## Performance Regressions" in content
        assert "performance_test" in content
        assert "50.0%" in content
        assert "HIGH" in content

    def test_format_check_result_success(self, sample_check_result):
        """Test formatting successful check result."""
        reporter = MarkdownReporter()
        formatted = reporter._format_check_result(sample_check_result)

        assert "✅ SUCCESS" in formatted
        assert sample_check_result.name in formatted
        assert f"{sample_check_result.duration:.2f}s" in formatted
        assert "Test completed successfully" in formatted

    def test_format_check_result_failure(self, sample_failed_check_result):
        """Test formatting failed check result."""
        reporter = MarkdownReporter()
        formatted = reporter._format_check_result(sample_failed_check_result)

        assert "❌ FAILURE" in formatted
        assert sample_failed_check_result.name in formatted
        assert "Syntax error in line 42" in formatted
        assert "Import error" in formatted

    def test_format_check_result_with_suggestions(self):
        """Test formatting check result with suggestions."""
        check_result = CheckResult(
            name="test_with_suggestions",
            status=CheckStatus.WARNING,
            duration=1.0,
            suggestions=["Fix indentation", "Add type hints"],
        )

        reporter = MarkdownReporter()
        formatted = reporter._format_check_result(check_result)

        assert "⚠️ WARNING" in formatted
        assert "**Suggestions:**" in formatted
        assert "Fix indentation" in formatted
        assert "Add type hints" in formatted

    def test_format_regression_issue(self):
        """Test formatting regression issue."""
        regression = RegressionIssue(
            test_name="memory_test",
            baseline_value=50.0,
            current_value=80.0,
            regression_percentage=60.0,
            severity=SeverityLevel.CRITICAL,
            description="Memory usage increased significantly",
        )

        reporter = MarkdownReporter()
        formatted = reporter._format_regression_issue(regression)

        assert "memory_test" in formatted
        assert "50.0" in formatted
        assert "80.0" in formatted
        assert "60.0%" in formatted
        assert "CRITICAL" in formatted
        assert "Memory usage increased significantly" in formatted

    def test_validate_output_path(self):
        """Test output path validation."""
        reporter = MarkdownReporter()

        assert reporter.validate_output_path("report.md") is True
        assert reporter.validate_output_path("path/to/report.md") is True
        assert reporter.validate_output_path("report.txt") is False
        assert reporter.validate_output_path("report.json") is False

    def test_generate_summary_section(self, sample_simulation_result):
        """Test generating summary section."""
        reporter = MarkdownReporter()
        summary = reporter._generate_summary_section(sample_simulation_result)

        assert "## Summary" in summary
        assert f"**Overall Status:** {sample_simulation_result.overall_status.value.upper()}" in summary
        assert f"**Total Duration:** {sample_simulation_result.total_duration:.2f}s" in summary
        assert f"**Python Versions:** {', '.join(sample_simulation_result.python_versions_tested)}" in summary

    def test_generate_check_results_section(self, sample_simulation_result):
        """Test generating check results section."""
        reporter = MarkdownReporter()
        section = reporter._generate_check_results_section(sample_simulation_result)

        assert "## Check Results" in section
        assert "test_check" in section
        assert "failed_check" in section


class TestJSONReporter:
    """Test cases for JSONReporter."""

    def test_json_reporter_creation(self):
        """Test JSONReporter creation."""
        reporter = JSONReporter()

        assert reporter.format_name == "json"
        assert reporter.file_extension == ".json"

    def test_generate_report_basic(self, sample_simulation_result, temp_dir):
        """Test basic JSON report generation."""
        reporter = JSONReporter()
        output_path = os.path.join(temp_dir, "test_report.json")

        result_path = reporter.generate_report(sample_simulation_result, output_path)

        assert result_path == output_path
        assert os.path.exists(output_path)

        # Check report content
        with open(output_path) as f:
            data = json.load(f)

        assert data["overall_status"] == sample_simulation_result.overall_status.value
        assert data["total_duration"] == sample_simulation_result.total_duration
        assert "check_results" in data
        assert "metadata" in data

    def test_generate_report_with_metadata(self, sample_simulation_result, temp_dir):
        """Test JSON report generation with metadata."""
        # Add some configuration metadata
        sample_simulation_result.configuration = {
            "python_versions": ["3.10", "3.11"],
            "timeout": 300,
            "parallel_jobs": 2,
        }

        reporter = JSONReporter()
        output_path = os.path.join(temp_dir, "metadata_report.json")

        result_path = reporter.generate_report(sample_simulation_result, output_path)

        with open(result_path) as f:
            data = json.load(f)

        assert "configuration" in data["metadata"]
        assert data["metadata"]["configuration"]["timeout"] == 300
        assert data["metadata"]["configuration"]["parallel_jobs"] == 2

    def test_generate_report_with_regressions(self, sample_check_result, temp_dir):
        """Test JSON report generation with regressions."""
        regression = RegressionIssue(
            test_name="performance_test",
            baseline_value=100.0,
            current_value=150.0,
            regression_percentage=50.0,
            severity=SeverityLevel.HIGH,
            description="Performance degraded",
        )

        simulation_result = SimulationResult(
            overall_status=CheckStatus.WARNING,
            total_duration=5.0,
            check_results={"test": sample_check_result},
            python_versions_tested=["3.10"],
            summary="Test with regressions",
            regression_issues=[regression],
        )

        reporter = JSONReporter()
        output_path = os.path.join(temp_dir, "regression_report.json")

        result_path = reporter.generate_report(simulation_result, output_path)

        with open(result_path) as f:
            data = json.load(f)

        assert "regression_issues" in data
        assert len(data["regression_issues"]) == 1
        assert data["regression_issues"][0]["test_name"] == "performance_test"
        assert data["regression_issues"][0]["severity"] == "high"

    def test_validate_output_path(self):
        """Test output path validation."""
        reporter = JSONReporter()

        assert reporter.validate_output_path("report.json") is True
        assert reporter.validate_output_path("path/to/report.json") is True
        assert reporter.validate_output_path("report.md") is False
        assert reporter.validate_output_path("report.txt") is False

    def test_generate_metadata(self, sample_simulation_result):
        """Test metadata generation."""
        reporter = JSONReporter()
        metadata = reporter._generate_metadata(sample_simulation_result)

        assert "generation_time" in metadata
        assert "report_version" in metadata
        assert "configuration" in metadata
        assert isinstance(metadata["generation_time"], str)

    def test_serialize_check_results(self, sample_simulation_result):
        """Test check results serialization."""
        reporter = JSONReporter()
        serialized = reporter._serialize_check_results(sample_simulation_result.check_results)

        assert isinstance(serialized, dict)
        assert "test_check" in serialized
        assert "failed_check" in serialized

        # Check that CheckResult objects are properly serialized
        test_result = serialized["test_check"]
        assert test_result["status"] == "success"
        assert test_result["duration"] == 1.5


class TestHistoryTracker:
    """Test cases for HistoryTracker."""

    def test_history_tracker_creation(self, temp_dir):
        """Test HistoryTracker creation."""
        history_dir = os.path.join(temp_dir, "history")
        tracker = HistoryTracker(history_dir)

        assert tracker.history_dir == history_dir
        assert tracker.trends_file == os.path.join(history_dir, "trends.json")

    def test_save_simulation_result(self, sample_simulation_result, temp_dir):
        """Test saving simulation result to history."""
        history_dir = os.path.join(temp_dir, "history")
        tracker = HistoryTracker(history_dir)

        saved_path = tracker.save_simulation_result(sample_simulation_result)

        assert os.path.exists(saved_path)
        assert saved_path.endswith(".json")

        # Verify saved content
        with open(saved_path) as f:
            data = json.load(f)

        assert data["overall_status"] == sample_simulation_result.overall_status.value
        assert data["total_duration"] == sample_simulation_result.total_duration

    def test_load_simulation_result(self, sample_simulation_result, temp_dir):
        """Test loading simulation result from history."""
        history_dir = os.path.join(temp_dir, "history")
        tracker = HistoryTracker(history_dir)

        # Save first
        saved_path = tracker.save_simulation_result(sample_simulation_result)

        # Load back
        loaded_result = tracker.load_simulation_result(os.path.basename(saved_path))

        assert loaded_result.overall_status == sample_simulation_result.overall_status
        assert loaded_result.total_duration == sample_simulation_result.total_duration
        assert len(loaded_result.check_results) == len(sample_simulation_result.check_results)

    def test_get_recent_results(self, sample_simulation_result, temp_dir):
        """Test getting recent simulation results."""
        history_dir = os.path.join(temp_dir, "history")
        tracker = HistoryTracker(history_dir)

        # Save multiple results
        for i in range(5):
            result = SimulationResult(
                overall_status=CheckStatus.SUCCESS,
                total_duration=float(i + 1),
                check_results={},
                python_versions_tested=["3.10"],
                summary=f"Test {i}",
            )
            tracker.save_simulation_result(result)

        recent = tracker.get_recent_results(limit=3)

        assert len(recent) == 3
        # Should be in reverse chronological order (most recent first)
        assert recent[0].total_duration > recent[1].total_duration

    def test_get_recent_results_empty_history(self, temp_dir):
        """Test getting recent results when history is empty."""
        history_dir = os.path.join(temp_dir, "empty_history")
        tracker = HistoryTracker(history_dir)

        recent = tracker.get_recent_results()

        assert recent == []

    def test_analyze_trends(self, temp_dir):
        """Test trend analysis."""
        history_dir = os.path.join(temp_dir, "history")
        tracker = HistoryTracker(history_dir)

        # Create results with trend (increasing duration)
        for i in range(10):
            result = SimulationResult(
                overall_status=CheckStatus.SUCCESS if i < 8 else CheckStatus.FAILURE,
                total_duration=float(i * 10 + 100),  # 100, 110, 120, ...
                check_results={},
                python_versions_tested=["3.10"],
                summary=f"Test {i}",
            )
            tracker.save_simulation_result(result)

        trends = tracker.analyze_trends()

        assert "duration_trend" in trends
        assert "success_rate" in trends
        assert "recent_failures" in trends

        # Duration should be increasing
        assert trends["duration_trend"]["direction"] == "increasing"

        # Success rate should be less than 100% due to recent failures
        assert trends["success_rate"] < 1.0

    def test_generate_trend_report(self, temp_dir):
        """Test trend report generation."""
        history_dir = os.path.join(temp_dir, "history")
        tracker = HistoryTracker(history_dir)

        # Save some results
        for i in range(5):
            result = SimulationResult(
                overall_status=CheckStatus.SUCCESS,
                total_duration=float(i + 1),
                check_results={},
                python_versions_tested=["3.10"],
                summary=f"Test {i}",
            )
            tracker.save_simulation_result(result)

        report = tracker.generate_trend_report()

        assert isinstance(report, str)
        assert "Trend Analysis Report" in report
        assert "Duration Trend" in report
        assert "Success Rate" in report

    def test_cleanup_old_results(self, temp_dir):
        """Test cleaning up old results."""
        history_dir = os.path.join(temp_dir, "history")
        tracker = HistoryTracker(history_dir)

        # Save many results
        for i in range(20):
            result = SimulationResult(
                overall_status=CheckStatus.SUCCESS,
                total_duration=float(i + 1),
                check_results={},
                python_versions_tested=["3.10"],
                summary=f"Test {i}",
            )
            tracker.save_simulation_result(result)

        # Cleanup, keeping only 10 most recent
        tracker.cleanup_old_results(keep_count=10)

        remaining = tracker.get_recent_results()
        assert len(remaining) == 10

    def test_get_performance_baseline(self, temp_dir):
        """Test getting performance baseline from history."""
        history_dir = os.path.join(temp_dir, "history")
        tracker = HistoryTracker(history_dir)

        # Save results with performance data
        for i in range(5):
            check_result = CheckResult(
                name="performance_test",
                status=CheckStatus.SUCCESS,
                duration=1.0,
                metadata={"benchmark_results": {"test_speed": float(100 + i * 10)}},
            )

            result = SimulationResult(
                overall_status=CheckStatus.SUCCESS,
                total_duration=float(i + 1),
                check_results={"performance": check_result},
                python_versions_tested=["3.10"],
                summary=f"Test {i}",
            )
            tracker.save_simulation_result(result)

        baseline = tracker.get_performance_baseline()

        assert isinstance(baseline, dict)
        assert "test_speed" in baseline
        # Should be average of the values
        expected_avg = sum(100 + i * 10 for i in range(5)) / 5
        assert baseline["test_speed"] == expected_avg

    def test_update_trends_file(self, temp_dir):
        """Test updating trends file."""
        history_dir = os.path.join(temp_dir, "history")
        tracker = HistoryTracker(history_dir)

        trends_data = {
            "last_updated": datetime.now().isoformat(),
            "success_rate": 0.85,
            "average_duration": 120.5,
        }

        tracker._update_trends_file(trends_data)

        assert os.path.exists(tracker.trends_file)

        with open(tracker.trends_file) as f:
            saved_data = json.load(f)

        assert saved_data["success_rate"] == 0.85
        assert saved_data["average_duration"] == 120.5

    def test_load_trends_file(self, temp_dir):
        """Test loading trends file."""
        history_dir = os.path.join(temp_dir, "history")
        tracker = HistoryTracker(history_dir)

        # Create trends file
        trends_data = {"success_rate": 0.9, "average_duration": 100.0}
        os.makedirs(history_dir, exist_ok=True)

        with open(tracker.trends_file, "w") as f:
            json.dump(trends_data, f)

        loaded_trends = tracker._load_trends_file()

        assert loaded_trends["success_rate"] == 0.9
        assert loaded_trends["average_duration"] == 100.0

    def test_load_trends_file_nonexistent(self, temp_dir):
        """Test loading non-existent trends file."""
        history_dir = os.path.join(temp_dir, "history")
        tracker = HistoryTracker(history_dir)

        trends = tracker._load_trends_file()

        assert trends == {}


class TestReporterIntegration:
    """Integration tests for reporters."""

    def test_all_reporters_implement_interface(self):
        """Test that all reporters implement the interface correctly."""
        reporters = [MarkdownReporter(), JSONReporter()]

        for reporter in reporters:
            # Test required properties
            assert hasattr(reporter, "format_name")
            assert hasattr(reporter, "file_extension")

            # Test required methods
            assert callable(reporter.generate_report)
            assert callable(reporter.validate_output_path)

    def test_multiple_report_formats(self, sample_simulation_result, temp_dir):
        """Test generating reports in multiple formats."""
        reporters = {"markdown": MarkdownReporter(), "json": JSONReporter()}

        report_paths = {}

        for format_name, reporter in reporters.items():
            output_path = os.path.join(temp_dir, f"test_report{reporter.file_extension}")

            result_path = reporter.generate_report(sample_simulation_result, output_path)
            report_paths[format_name] = result_path

            assert os.path.exists(result_path)

        # Verify both files were created
        assert os.path.exists(report_paths["markdown"])
        assert os.path.exists(report_paths["json"])

        # Verify content is different but related
        with open(report_paths["markdown"]) as f:
            md_content = f.read()

        with open(report_paths["json"]) as f:
            json_content = json.load(f)

        assert "# CI Simulation Report" in md_content
        assert json_content["overall_status"] == sample_simulation_result.overall_status.value

    def test_history_tracking_with_reports(self, sample_simulation_result, temp_dir):
        """Test history tracking integration with report generation."""
        history_dir = os.path.join(temp_dir, "history")
        tracker = HistoryTracker(history_dir)

        # Save result to history
        saved_path = tracker.save_simulation_result(sample_simulation_result)

        # Generate reports for the saved result
        md_reporter = MarkdownReporter()
        json_reporter = JSONReporter()

        md_path = os.path.join(temp_dir, "history_report.md")
        json_path = os.path.join(temp_dir, "history_report.json")

        md_reporter.generate_report(sample_simulation_result, md_path)
        json_reporter.generate_report(sample_simulation_result, json_path)

        # Verify all files exist
        assert os.path.exists(saved_path)
        assert os.path.exists(md_path)
        assert os.path.exists(json_path)

        # Load from history and verify consistency
        loaded_result = tracker.load_simulation_result(os.path.basename(saved_path))
        assert loaded_result.overall_status == sample_simulation_result.overall_status

    def test_reporter_error_handling(self, sample_simulation_result):
        """Test error handling in reporters."""
        reporter = MarkdownReporter()

        # Test with invalid output path (directory doesn't exist)
        invalid_path = "/nonexistent/directory/report.md"

        with pytest.raises((OSError, IOError)):
            reporter.generate_report(sample_simulation_result, invalid_path)

    def test_history_tracker_concurrent_access(self, sample_simulation_result, temp_dir):
        """Test history tracker with concurrent access simulation."""
        history_dir = os.path.join(temp_dir, "concurrent_history")

        # Simulate multiple trackers (as if from different processes)
        tracker1 = HistoryTracker(history_dir)
        tracker2 = HistoryTracker(history_dir)

        # Save from both trackers
        path1 = tracker1.save_simulation_result(sample_simulation_result)
        path2 = tracker2.save_simulation_result(sample_simulation_result)

        # Both should succeed and create different files
        assert os.path.exists(path1)
        assert os.path.exists(path2)
        assert path1 != path2

        # Both trackers should see both results
        recent1 = tracker1.get_recent_results()
        recent2 = tracker2.get_recent_results()

        assert len(recent1) == 2
        assert len(recent2) == 2
